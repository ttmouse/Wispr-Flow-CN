from funasr import AutoModel
import numpy as np
import os
import sys
import logging
import re
from contextlib import redirect_stdout, redirect_stderr
import io
import time
from concurrent.futures import ThreadPoolExecutor
import math

# 设置 modelscope 日志级别为 WARNING，减少不必要的信息
logging.getLogger('modelscope').setLevel(logging.WARNING)

class FunASREngine:
    def __init__(self):
        try:
            # 获取应用程序的基础路径
            if getattr(sys, 'frozen', False):
                application_path = sys._MEIPASS
            else:
                application_path = os.path.dirname(os.path.abspath(__file__))
            
            print(f"应用程序路径: {application_path}")
            
            # 设置 MODELSCOPE_CACHE 环境变量
            cache_dir = os.path.join(application_path, 'modelscope', 'hub')
            os.environ['MODELSCOPE_CACHE'] = cache_dir
            print(f"模型缓存路径: {cache_dir}")
            
            # 初始化热词列表
            self.hotwords = []
            hotwords_file = os.path.join(os.path.dirname(application_path), "resources", "hotwords.txt")
            if os.path.exists(hotwords_file):
                with open(hotwords_file, 'r', encoding='utf-8') as f:
                    self.hotwords = [line.strip() for line in f 
                                   if line.strip() and not line.strip().startswith('#')]
                print(f"✓ 加载了 {len(self.hotwords)} 个热词")
            
            # 检查模型文件是否存在
            asr_model_dir = os.path.join(cache_dir, 'damo', 'speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch')
            punc_model_dir = os.path.join(cache_dir, 'damo', 'punc_ct-transformer_zh-cn-common-vocab272727-pytorch')
            
            print(f"ASR模型路径: {asr_model_dir}")
            print(f"标点模型路径: {punc_model_dir}")
            
            if not os.path.exists(asr_model_dir) or not os.path.exists(punc_model_dir):
                raise Exception(f"模型文件不存在: ASR模型: {os.path.exists(asr_model_dir)}, 标点模型: {os.path.exists(punc_model_dir)}")
            
            # 使用 redirect_stdout 来捕获输出
            f = io.StringIO()
            with redirect_stdout(f), redirect_stderr(f):
                print("开始加载ASR模型...")
                # 初始化语音识别模型
                self.model = AutoModel(
                    model=asr_model_dir,
                    model_revision="v2.0.4",
                    disable_update=True
                )
                print("ASR模型加载完成")
                
                print("开始加载标点模型...")
                # 初始化标点模型
                self.punc_model = AutoModel(
                    model=punc_model_dir,
                    model_revision="v2.0.4",
                    disable_update=True
                )
                print("标点模型加载完成")
                
        except Exception as e:
            error_msg = f"❌ 模型加载失败: {str(e)}\n"
            error_msg += f"系统路径: {sys.path}\n"
            error_msg += f"当前目录: {os.getcwd()}\n"
            error_msg += f"环境变量: MODELSCOPE_CACHE={os.environ.get('MODELSCOPE_CACHE', '未设置')}\n"
            print(error_msg)
            raise

    def preprocess_audio(self, audio_data):
        """音频预处理
        1. 音频归一化
        2. 预加重（提升高频部分）
        3. 静音检测和去除
        """
        try:
            start_time = time.time()
            original_length = len(audio_data)

            # 1. 快速检查是否需要预处理
            if len(audio_data) < 1600:  # 小于100ms的音频直接跳过
                return audio_data

            # 2. 音频归一化
            audio_max = np.max(np.abs(audio_data))
            if audio_max > 0:
                audio_data = audio_data / audio_max

            # 3. 条件性预加重 - 只在高频信号较弱时进行
            if np.mean(np.abs(np.diff(audio_data))) < 0.04:
                preemphasis_coef = 0.97
                audio_data = np.append(audio_data[0], audio_data[1:] - preemphasis_coef * audio_data[:-1])

            # 4. 静音检测和去除
            chunk_size = 3200  # 200ms at 16kHz
            chunks = np.array_split(audio_data, max(1, len(audio_data) // chunk_size))
            
            # 计算能量
            energies = np.array([np.mean(np.abs(chunk)) for chunk in chunks])
            
            # 自适应阈值
            threshold = np.mean(energies) * 0.1
            non_silent_mask = energies >= threshold
            
            # 如果静音比例过高才进行去除
            if np.mean(non_silent_mask) < 0.8:
                non_silent_chunks = [chunk for i, chunk in enumerate(chunks) if non_silent_mask[i]]
                if non_silent_chunks:
                    audio_data = np.concatenate(non_silent_chunks)

            # 记录处理结果
            process_time = (time.time() - start_time) * 1000
            compression_ratio = len(audio_data) / original_length * 100
            
            print(f"音频预处理完成:")
            print(f"处理耗时: {process_time:.2f}ms")
            print(f"压缩比例: {compression_ratio:.1f}%")
            
            return audio_data
            
        except Exception as e:
            print(f"❌ 音频预处理失败: {e}")
            return audio_data  # 如果处理失败，返回原始音频

    def _transcribe_single(self, audio_chunk):
        """处理单个音频块"""
        try:
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                result = self.model.generate(
                    input=audio_chunk,
                    batch_size_s=200,
                    use_itn=True,
                    mode='offline',
                    decode_method='greedy_search',
                    disable_progress_bar=True,
                    hotwords=[(word, 50.0) for word in self.hotwords] if self.hotwords else None,
                    cache_size=2000,
                    beam_size=5
                )
            
            if isinstance(result, list) and len(result) > 0:
                return result[0].get('text', '')
            return ''
        except Exception as e:
            print(f"❌ 单块处理失败: {e}")
            return ''

    def _merge_results(self, chunk_results):
        """智能合并分块结果"""
        # 移除空结果
        texts = [text for text in chunk_results if text.strip()]
        if not texts:
            return ""
        
        # 简单的重复检测和移除
        merged = texts[0]
        for i in range(1, len(texts)):
            current = texts[i]
            # 检查重叠部分
            overlap_size = min(len(merged), len(current))
            for size in range(min(overlap_size, 10), 0, -1):  # 最多检查10个字的重叠
                if merged[-size:] == current[:size]:
                    current = current[size:]
                    break
            merged += current
        
        return merged

    def _add_punctuation(self, text):
        """添加标点符号"""
        try:
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                result = self.punc_model.generate(
                    input=text,
                    disable_progress_bar=True,
                    batch_size=1,
                    mode='offline',
                    cache_size=1000,
                    hotword_score=2.0,
                    min_sentence_length=2,
                    hotwords=[(word, 50.0) for word in self.hotwords] if self.hotwords else None
                )
            
            if isinstance(result, list) and len(result) > 0:
                return result[0].get('text', text)
            return text
        except Exception as e:
            print(f"❌ 标点处理失败: {e}")
            return text

    def transcribe(self, audio_data):
        """并行处理音频转写"""
        try:
            start_time = time.time()
            
            if audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)
            
            # 1. 预处理
            audio_data = self.preprocess_audio(audio_data)
            
            # 2. 计算合适的分块大小（每块2秒音频）
            sample_rate = 16000  # 采样率
            chunk_duration = 2   # 每块2秒
            chunk_size = sample_rate * chunk_duration
            
            # 3. 分块，确保有重叠（避免语音在边界处被切断）
            overlap = sample_rate // 2  # 0.5秒重叠
            chunks = []
            start = 0
            while start < len(audio_data):
                end = min(start + chunk_size, len(audio_data))
                chunk = audio_data[start:end]
                if len(chunk) >= sample_rate:  # 只处理长度超过1秒的块
                    chunks.append(chunk)
                start += chunk_size - overlap
            
            # 4. 如果音频太短，直接处理
            if len(chunks) <= 1:
                return self._transcribe_single(audio_data)
            
            # 5. 并行处理每个块
            chunk_start_time = time.time()
            with ThreadPoolExecutor(max_workers=min(len(chunks), 3)) as executor:
                chunk_results = list(executor.map(self._transcribe_single, chunks))
            chunk_time = (time.time() - chunk_start_time) * 1000
            
            # 6. 合并结果
            merge_start_time = time.time()
            merged_text = self._merge_results(chunk_results)
            merge_time = (time.time() - merge_start_time) * 1000
            
            # 7. 添加标点符号
            punc_start_time = time.time()
            final_text = self._add_punctuation(merged_text)
            punc_time = (time.time() - punc_start_time) * 1000
            
            # 8. 处理英文单词间的空格
            final_text = self._process_text(final_text)
            
            # 9. 输出性能统计
            total_time = (time.time() - start_time) * 1000
            print(f"\n并行处理性能统计:")
            print(f"音频长度: {len(audio_data)/sample_rate:.1f}秒")
            print(f"处理块数: {len(chunks)}")
            print(f"分块识别耗时: {chunk_time:.2f}ms")
            print(f"合并耗时: {merge_time:.2f}ms")
            print(f"标点处理耗时: {punc_time:.2f}ms")
            print(f"总耗时: {total_time:.2f}ms")
            print(f"平均每秒处理时间: {total_time/(len(audio_data)/sample_rate):.2f}ms")
            
            return [{"text": final_text}]
            
        except Exception as e:
            print(f"❌ 转写失败: {e}")
            raise

    def _process_text(self, text):
        """处理文本，添加英文单词间的空格"""
        # 1. 使用正则表达式分离英文单词
        def split_english_words(text):
            # 匹配连续的英文字母
            words = re.finditer(r'[a-zA-Z]+', text)
            result = []
            last_end = 0
            
            for match in words:
                start, end = match.span()
                # 添加非英文部分
                if start > last_end:
                    result.append(text[last_end:start])
                # 添加英文单词
                word = match.group()
                # 使用简单的规则分割英文单词
                # 比如 "whatareyou" -> "what are you"
                sub_words = []
                current_word = ""
                for i, char in enumerate(word.lower()):
                    current_word += char
                    # 常见的英文单词
                    common_words = {'what', 'are', 'you', 'doing', 'how', 'is', 'the', 'this', 'that', 'have', 'has', 'had', 'will', 'would', 'can', 'could', 'should', 'must', 'may', 'might', 'shall'}
                    # 如果当前积累的字母构成了一个常见单词，并且剩余的字母也可能构成单词
                    if current_word in common_words and i < len(word) - 1:
                        sub_words.append(current_word)
                        current_word = ""
                if current_word:
                    sub_words.append(current_word)
                result.append(' '.join(sub_words))
                last_end = end
            
            # 添加剩余的文本
            if last_end < len(text):
                result.append(text[last_end:])
            
            return ''.join(result)
        
        # 2. 处理文本
        processed_text = split_english_words(text)
        
        return processed_text

    def get_model_path(self):
        return "使用预训练模型"

    def reload_hotwords(self):
        """重新加载热词"""
        try:
            hotwords_file = os.path.join("resources", "hotwords.txt")
            if os.path.exists(hotwords_file):
                with open(hotwords_file, "r", encoding="utf-8") as f:
                    self.hotwords = [line.strip() for line in f if line.strip() and not line.startswith("#")]
                print(f"重新加载热词成功，共 {len(self.hotwords)} 个")
            else:
                self.hotwords = []
        except Exception as e:
            print(f"重新加载热词失败: {e}")
            self.hotwords = []