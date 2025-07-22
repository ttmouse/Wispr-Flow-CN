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
    def __init__(self, settings_manager=None):
        try:
            # 保存设置管理器引用
            self.settings_manager = settings_manager
            # 初始化状态标志
            self.is_ready = False
            # 获取应用程序的基础路径
            if getattr(sys, 'frozen', False):
                application_path = sys._MEIPASS
            else:
                application_path = os.path.dirname(os.path.abspath(__file__))
            
            # 设置 MODELSCOPE_CACHE 环境变量
            cache_dir = os.path.join(application_path, 'modelscope', 'hub')
            os.environ['MODELSCOPE_CACHE'] = cache_dir
            
            # 初始化热词列表
            self.hotwords = []
            hotwords_file = os.path.join(os.path.dirname(application_path), "resources", "hotwords.txt")
            if os.path.exists(hotwords_file):
                with open(hotwords_file, 'r', encoding='utf-8') as f:
                    self.hotwords = [line.strip() for line in f 
                                   if line.strip() and not line.strip().startswith('#')]
                print(f"✅ 热词加载成功: 共加载 {len(self.hotwords)} 个热词")
                print(f"📝 热词列表: {', '.join(self.hotwords[:10])}{'...' if len(self.hotwords) > 10 else ''}")
            else:
                print(f"⚠️ 热词文件不存在: {hotwords_file}")
            
            # 检查模型文件是否存在
            asr_model_dir = os.path.join(cache_dir, 'damo', 'speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch')
            punc_model_dir = os.path.join(cache_dir, 'damo', 'punc_ct-transformer_zh-cn-common-vocab272727-pytorch')
            
            # 检查模型路径
            
            # ASR模型是必需的
            if not os.path.exists(asr_model_dir):
                raise Exception(f"ASR模型文件不存在: {asr_model_dir}")
            
            # 标点模型是可选的
            self.has_punc_model = os.path.exists(punc_model_dir)
            if not self.has_punc_model:
                print("⚠️ 标点模型不存在，将跳过标点处理")
            
            # 使用 redirect_stdout 来捕获输出
            f = io.StringIO()
            with redirect_stdout(f), redirect_stderr(f):
                # 初始化语音识别模型
                self.model = AutoModel(
                    model=asr_model_dir,
                    model_revision="v2.0.4",
                    disable_update=True
                )
                
                # 只在标点模型存在时才加载
                if self.has_punc_model:
                    self.punc_model = AutoModel(
                        model=punc_model_dir,
                        model_revision="v2.0.4",
                        disable_update=True
                    )
                else:
                    self.punc_model = None
                
            # 设置引擎就绪状态
            self.is_ready = True
            pass  # FunASR引擎初始化完成
                
        except Exception as e:
            self.is_ready = False
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
            try:
                audio_max = float(np.max(np.abs(audio_data)))
                # 使用Python标量进行比较，避免NumPy数组比较错误
                if float(audio_max) > 0.0:
                    audio_data = audio_data / audio_max
            except Exception as e:
                print(f"音频归一化处理时出错: {e}")
                # 如果处理失败，跳过归一化步骤
                pass

            # 3. 条件性预加重 - 只在高频信号较弱时进行
            try:
                diff_mean = float(np.mean(np.abs(np.diff(audio_data))))
                # 使用Python标量进行比较，避免NumPy数组比较错误
                if float(diff_mean) < 0.04:
                    preemphasis_coef = 0.97
                    audio_data = np.append(audio_data[0], audio_data[1:] - preemphasis_coef * audio_data[:-1])
            except Exception as e:
                print(f"预加重处理时出错: {e}")
                # 如果处理失败，跳过预加重步骤
                pass

            # 4. 静音检测和去除
            chunk_size = 3200  # 200ms at 16kHz
            chunks = np.array_split(audio_data, max(1, len(audio_data) // chunk_size))
            
            # 计算能量
            energies = np.array([np.mean(np.abs(chunk)) for chunk in chunks])
            
            # 自适应阈值
            threshold = float(np.mean(energies)) * 0.1
            # 确保使用标量值进行比较，避免NumPy数组比较错误
            try:
                # 使用np.greater_equal避免直接数组比较
                non_silent_mask = np.greater_equal(energies, threshold)
                
                # 如果静音比例过高才进行去除
                # 使用.mean()和float()确保标量比较
                silent_ratio = float(np.mean(non_silent_mask.astype(np.float32)))
                # 使用Python标量进行比较，避免NumPy数组比较错误
                if silent_ratio < 0.8:
                    # 确保布尔数组索引转换为Python布尔值
                    non_silent_indices = np.where(non_silent_mask)[0]
                    non_silent_chunks = [chunks[i] for i in non_silent_indices]
                    if len(non_silent_chunks) > 0:  # 使用len()而不是直接判断列表
                        audio_data = np.concatenate(non_silent_chunks)
            except Exception as e:
                print(f"静音检测处理时出错: {e}")
                # 如果处理失败，保持原始音频数据
                pass

            # 记录处理结果
            process_time = (time.time() - start_time) * 1000
            compression_ratio = len(audio_data) / original_length * 100
            
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
                    batch_size_s=200,          # 恢复到原来的值
                    use_itn=True,
                    mode='offline',
                    decode_method='greedy_search',  # 改回greedy_search
                    disable_progress_bar=True,
                    hotwords=[(word, self._get_hotword_weight()) for word in self.hotwords] if self.hotwords else None,  # 热词权重
                    cache_size=2000,           # 恢复原来的缓存大小
                    beam_size=5                # 恢复原来的beam size
                )
                
                # 添加热词使用日志
                if self.hotwords:
                    print(f"🎯 单块处理使用热词: {len(self.hotwords)} 个热词，权重: {self._get_hotword_weight()}")
            
            if isinstance(result, list) and len(result) > 0:
                text = result[0].get('text', '')
                return text
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
                    hotwords=[(word, self._get_hotword_weight()) for word in self.hotwords] if self.hotwords else None  # 热词权重
                )
                
                # 添加热词使用日志
                if self.hotwords:
                    print(f"🎯 标点模型使用热词: {len(self.hotwords)} 个热词，权重: {self._get_hotword_weight()}")
            
            if isinstance(result, list) and len(result) > 0:
                return result[0].get('text', text)
            return text
        except Exception as e:
            print(f"❌ 标点处理失败: {e}")
            return text

    def transcribe(self, audio_data):
        """转写音频数据"""
        try:
            # 安全地检查数据类型，避免NumPy数组比较错误
            if hasattr(audio_data, 'dtype') and audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)
            elif not hasattr(audio_data, 'dtype'):
                # 如果不是NumPy数组，转换为NumPy数组
                audio_data = np.array(audio_data, dtype=np.float32)
            
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                # 1. 语音识别
                result = self.model.generate(
                    input=audio_data,
                    batch_size_s=100,     # 减小批处理大小
                    use_itn=True,         # 启用逆文本正则化
                    mode='offline',      # 使用离线模式以提高准确率
                    decode_method='greedy_search',  # 使用贪婪搜索解码
                    disable_progress_bar=True,  # 禁用进度条
                    hotwords=[(word, self._get_hotword_weight()) for word in self.hotwords] if self.hotwords else None  # 热词权重
                )
                
                # 添加热词使用日志
                if self.hotwords:
                    print(f"🎯 主转写使用热词: {len(self.hotwords)} 个热词，权重: {self._get_hotword_weight()}")
            
            if isinstance(result, list) and len(result) > 0:
                text = result[0].get('text', '')
                
            # 2. 添加标点
            text = self._add_punctuation(text)
            
            # 3. 处理英文单词间的空格
            processed_text = self._process_text(text)
            
            # 4. 发音相似词纠错
            corrected_text = self._correct_similar_pronunciation(processed_text)
            
            # 5. 不再在引擎层添加HTML标签，保持纯文本
            final_text = corrected_text
            
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
            # 使用绝对路径，与初始化时保持一致
            if getattr(sys, 'frozen', False):
                application_path = sys._MEIPASS
            else:
                application_path = os.path.dirname(os.path.abspath(__file__))
            
            hotwords_file = os.path.join(os.path.dirname(application_path), "resources", "hotwords.txt")
            if os.path.exists(hotwords_file):
                with open(hotwords_file, "r", encoding="utf-8") as f:
                    self.hotwords = [line.strip() for line in f if line.strip() and not line.startswith("#")]
                print(f"🔄 热词重新加载成功: 共加载 {len(self.hotwords)} 个热词")
                print(f"📝 热词列表: {', '.join(self.hotwords[:10])}{'...' if len(self.hotwords) > 10 else ''}")
            else:
                print(f"⚠️ 热词文件不存在: {hotwords_file}")
                self.hotwords = []
        except Exception as e:
            print(f"❌ 重新加载热词失败: {e}")
            self.hotwords = []
    
    def _get_hotword_weight(self):
        """获取热词权重"""
        if self.settings_manager:
            return self.settings_manager.get_hotword_weight()
        return 80.0  # 默认权重
    
    def _is_pronunciation_correction_enabled(self):
        """检查是否启用发音纠错"""
        if self.settings_manager:
            return self.settings_manager.get_pronunciation_correction_enabled()
        return True  # 默认启用

    def _correct_similar_pronunciation(self, text):
        """纠正发音相似的词"""
        if not text or not self._is_pronunciation_correction_enabled():
            return text
        
        # 定义发音相似词映射表
        pronunciation_map = {
            '浮沉': '浮层',
            '浮尘': '浮层',
            '浮城': '浮层',
            '胡成': '浮层',  # 根据用户需求添加
            '含高': '行高',  # 添加含高到行高的映射
            '韩高': '行高',  # 可能的其他发音变体
            '汉高': '行高',  # 可能的其他发音变体
            '梵高': '行高',  # 修复梵高被错误识别为行高的问题
        }
        
        corrected_text = text
        
        # 只有当目标热词在热词列表中时才进行纠错
        for similar_word, correct_word in pronunciation_map.items():
            if similar_word in corrected_text and correct_word in self.hotwords:
                corrected_text = corrected_text.replace(similar_word, correct_word)
                print(f"🔧 发音纠错: '{similar_word}' -> '{correct_word}'")
        
        return corrected_text
    
    def _highlight_hotwords(self, text):
        """不再在引擎层添加HTML标签，直接返回原文本"""
        # 引擎层不再处理HTML标签，保持纯文本
        return text
    
    def _post_process_text(self, text):
        """文本后处理"""
        # 1. 修复常见的错误模式
        fixes = {
            "有可能是也有可能": "有可能",
            "的的": "的",
            "了了": "了",
            "吗吗": "吗",
            "啊啊": "啊",
            "嗯嗯": "嗯",
            "问题的问题": "问题",
        }
        
        for wrong, correct in fixes.items():
            text = text.replace(wrong, correct)
        
        # 2. 修复重复的标点
        text = re.sub(r'([。，！？；：、])\1+', r'\1', text)
        
        # 3. 修复不合理的词组搭配
        text = re.sub(r'解决了(\w+)问题的问题', r'解决了\1问题', text)
        
        return text

    def get_model_paths(self):
        """获取当前使用的模型路径"""
        cache_dir = os.environ.get('MODELSCOPE_CACHE', '')
        asr_model_dir = os.path.join(cache_dir, 'damo', 'speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch')
        punc_model_dir = os.path.join(cache_dir, 'damo', 'punc_ct-transformer_zh-cn-common-vocab272727-pytorch')
        
        return {
            'asr_model_path': asr_model_dir if os.path.exists(asr_model_dir) else '未找到ASR模型',
            'punc_model_path': punc_model_dir if os.path.exists(punc_model_dir) else '未找到标点模型'
        }
    
    def cleanup(self):
        """清理FunASR引擎资源"""
        try:
            # 重置就绪状态
            self.is_ready = False
            
            # 清理模型资源
            if hasattr(self, 'model') and self.model:
                # 尝试释放模型资源
                del self.model
                self.model = None
                
            if hasattr(self, 'punc_model') and self.punc_model:
                # 尝试释放标点模型资源
                del self.punc_model
                self.punc_model = None
                
            # 清理热词列表
            if hasattr(self, 'hotwords'):
                self.hotwords.clear()
                
            pass
            
        except Exception as e:
            print(f"❌ 清理FunASR引擎资源失败: {e}")
    
    def __del__(self):
        """析构函数，确保资源被释放"""
        self.cleanup()