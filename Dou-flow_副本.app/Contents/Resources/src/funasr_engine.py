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
from PyQt6.QtCore import QThread, pyqtSignal, QObject

# 设置 modelscope 日志级别为 WARNING，减少不必要的信息
logging.getLogger('modelscope').setLevel(logging.WARNING)

class ModelLoadThread(QThread):
    """模型加载线程"""
    model_loaded = pyqtSignal(object, object)  # ASR模型, 标点模型
    loading_progress = pyqtSignal(str)  # 加载进度信息
    loading_error = pyqtSignal(str)  # 加载错误信息
    
    def __init__(self, application_path, cache_dir, asr_model_dir, punc_model_dir):
        super().__init__()
        self.application_path = application_path
        self.cache_dir = cache_dir
        self.asr_model_dir = asr_model_dir
        self.punc_model_dir = punc_model_dir
    
    def run(self):
        try:
            # 检查模型文件是否存在
            self.loading_progress.emit("检查模型文件...")
            if not os.path.exists(self.asr_model_dir) or not os.path.exists(self.punc_model_dir):
                error_msg = f"模型文件不存在: ASR模型: {os.path.exists(self.asr_model_dir)}, 标点模型: {os.path.exists(self.punc_model_dir)}"
                self.loading_error.emit(error_msg)
                return
            
            # 使用 redirect_stdout 来捕获输出
            f = io.StringIO()
            with redirect_stdout(f), redirect_stderr(f):
                self.loading_progress.emit("正在加载ASR模型...")
                # 初始化语音识别模型
                model = AutoModel(
                    model=self.asr_model_dir,
                    model_revision="v2.0.4",
                    disable_update=True
                )
                self.loading_progress.emit("ASR模型加载完成，正在加载标点模型...")
                
                # 初始化标点模型
                punc_model = AutoModel(
                    model=self.punc_model_dir,
                    model_revision="v2.0.4",
                    disable_update=True
                )
                self.loading_progress.emit("标点模型加载完成")
                
                # 发送加载完成的信号
                self.model_loaded.emit(model, punc_model)
                
        except Exception as e:
            error_msg = f"❌ 模型加载失败: {str(e)}\n"
            error_msg += f"系统路径: {sys.path}\n"
            error_msg += f"当前目录: {os.getcwd()}\n"
            error_msg += f"环境变量: MODELSCOPE_CACHE={os.environ.get('MODELSCOPE_CACHE', '未设置')}\n"
            self.loading_error.emit(error_msg)

class FunASREngine(QObject):
    """支持异步加载的FunASR引擎"""
    model_ready = pyqtSignal()  # 模型准备就绪信号
    loading_progress = pyqtSignal(str)  # 加载进度信号
    loading_error = pyqtSignal(str)  # 加载错误信号
    
    def __init__(self):
        super().__init__()
        self.model = None
        self.punc_model = None
        self.hotwords = []
        self.is_ready = False
        self.load_thread = None
        
        # 快速初始化，只设置基本路径
        try:
            # 获取应用程序的基础路径
            if getattr(sys, 'frozen', False):
                application_path = sys._MEIPASS
            else:
                application_path = os.path.dirname(os.path.abspath(__file__))
            
            # 设置 MODELSCOPE_CACHE 环境变量
            cache_dir = os.path.join(application_path, 'modelscope', 'hub')
            os.environ['MODELSCOPE_CACHE'] = cache_dir
            
            # 构建模型路径
            asr_model_dir = os.path.join(cache_dir, 'damo', 'speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch')
            punc_model_dir = os.path.join(cache_dir, 'damo', 'punc_ct-transformer_zh-cn-common-vocab272727-pytorch')
            
            # 存储路径信息，用于异步加载
            self.application_path = application_path
            self.cache_dir = cache_dir
            self.asr_model_dir = asr_model_dir
            self.punc_model_dir = punc_model_dir
            
            print(f"FunASR引擎快速初始化完成")
                
        except Exception as e:
            error_msg = f"❌ 初始化失败: {str(e)}\n"
            print(error_msg)
            raise
    
    def start_async_loading(self):
        """开始异步加载模型"""
        if self.load_thread is not None and self.load_thread.isRunning():
            return  # 已经在加载中
        
        self.load_thread = ModelLoadThread(
            self.application_path, 
            self.cache_dir, 
            self.asr_model_dir, 
            self.punc_model_dir
        )
        
        # 连接信号
        self.load_thread.model_loaded.connect(self._on_models_loaded)
        self.load_thread.loading_progress.connect(self.loading_progress.emit)
        self.load_thread.loading_error.connect(self.loading_error.emit)
        
        # 开始加载
        self.load_thread.start()
        print("开始异步加载模型...")
    
    def _on_models_loaded(self, model, punc_model):
        """模型加载完成的回调"""
        self.model = model
        self.punc_model = punc_model
        
        # 异步加载热词
        try:
            hotwords_file = os.path.join(os.path.dirname(self.application_path), "resources", "hotwords.txt")
            if os.path.exists(hotwords_file):
                with open(hotwords_file, 'r', encoding='utf-8') as f:
                    self.hotwords = [line.strip() for line in f 
                                   if line.strip() and not line.strip().startswith('#')]
                print(f"✓ 加载了 {len(self.hotwords)} 个热词")
        except Exception as e:
            print(f"⚠️ 热词加载失败: {e}")
        
        self.is_ready = True
        print("✓ 语音识别模型异步加载完成")
        self.model_ready.emit()
    
    def is_model_ready(self):
        """检查模型是否准备就绪"""
        return self.is_ready
    
    def wait_for_model(self, timeout_ms=30000):
        """等待模型加载完成"""
        if self.is_ready:
            return True
        
        if self.load_thread is not None:
            return self.load_thread.wait(timeout_ms)
        
        return False
    
    def get_model_paths(self):
        """获取模型路径信息"""
        return {
            'asr_model': self.asr_model_dir,
            'punc_model': self.punc_model_dir
        }
 
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
                    batch_size_s=200,          # 恢复到原来的值
                    use_itn=True,
                    mode='offline',
                    decode_method='greedy_search',  # 改回greedy_search
                    disable_progress_bar=True,
                    hotwords=[(word, 50.0) for word in self.hotwords] if self.hotwords else None,  # 恢复原来的热词权重
                    cache_size=2000,           # 恢复原来的缓存大小
                    beam_size=5                # 恢复原来的beam size
                )
            
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
                    hotwords=[(word, 50.0) for word in self.hotwords] if self.hotwords else None
                )
            
            if isinstance(result, list) and len(result) > 0:
                return result[0].get('text', text)
            return text
        except Exception as e:
            print(f"❌ 标点处理失败: {e}")
            return text

    def transcribe(self, audio_data):
        """转写音频数据"""
        # 检查模型是否准备就绪
        if not self.is_ready:
            return [{"text": "模型正在加载中，请稍后重试..."}]
        
        try:
            if audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)
            
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                # 1. 语音识别
                result = self.model.generate(
                    input=audio_data,
                    batch_size_s=100,     # 减小批处理大小
                    use_itn=True,         # 启用逆文本正则化
                    mode='offline',      # 使用离线模式以提高准确率
                    decode_method='greedy_search',  # 使用贪婪搜索解码
                    disable_progress_bar=True,  # 禁用进度条
                    hotwords=[(word, 50.0) for word in self.hotwords] if self.hotwords else None
                )
            
            if isinstance(result, list) and len(result) > 0:
                text = result[0].get('text', '')
                
            # 2. 添加标点
            text = self._add_punctuation(text)
            
            # 3. 处理英文单词间的空格
            final_text = self._process_text(text)
            
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