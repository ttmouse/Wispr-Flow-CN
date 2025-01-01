from funasr import AutoModel
import numpy as np
import os
import sys
import logging
import re
from contextlib import redirect_stdout, redirect_stderr
import io

# 设置 modelscope 日志级别为 WARNING，减少不必要的信息
logging.getLogger('modelscope').setLevel(logging.WARNING)

class FunASREngine:
    def __init__(self):
        try:
            # 使用 redirect_stdout 来捕获输出
            f = io.StringIO()
            with redirect_stdout(f), redirect_stderr(f):
                # 初始化语音识别模型
                self.model = AutoModel(
                    model="damo/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch",
                    model_revision="v2.0.4",
                    disable_update=True
                )
                # 初始化标点模型
                self.punc_model = AutoModel(
                    model="damo/punc_ct-transformer_zh-cn-common-vocab272727-pytorch", ## 这个不要改，是正确的
                    model_revision="v2.0.4"
                )
                
        except Exception as e:
            print(f"❌ 模型加载失败: {e}")
            raise

    def transcribe(self, audio_data):
        """转写音频数据"""
        try:
            if audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)
            # 使用 redirect_stdout 来捕获输出
            f = io.StringIO()
            with redirect_stdout(f), redirect_stderr(f):
                # 1. 语音识别
                result = self.model.generate(
                    input=audio_data,
                    batch_size_s=300,
                    use_itn=True,     # 启用逆文本正则化
                    mode='offline',    # 使用离线模式以获得更好的标点效果
                    decode_method='greedy_search',  # 使用贪婪搜索解码
                    disable_progress_bar=True  # 禁用进度条
                )
            
            # 处理结果
            if isinstance(result, list) and len(result) > 0:
                text = result[0].get('text', '')
            elif isinstance(result, dict):
                text = result.get('text', '')
            else:
                text = str(result)
            
            # 输出原始转写结果
            print(f"🎯 语音识别: {text}")
            
            # 2. 添加标点
            with redirect_stdout(f), redirect_stderr(f):
                punc_result = self.punc_model.generate(
                    input=text,
                    disable_progress_bar=True,  # 禁用进度条
                    batch_size=1,               # 批处理大小
                    mode='offline',             # 离线模式，更准确的标点
                    cache_size=0,               # 不使用缓存，每次都重新预测
                    hotword_score=0.8,          # 提高热词权重，使标点更丰富
                    min_sentence_length=3       # 最小句子长度，小于这个长度的不会加句号
                )
            if isinstance(punc_result, list) and len(punc_result) > 0:
                text = punc_result[0].get('text', text)
            elif isinstance(punc_result, dict):
                text = punc_result.get('text', text)
            
            print(f"🎯 添加标点: {text}")
            
            # 3. 处理英文单词间的空格
            processed_text = self._process_text(text)
            print(f"✨ 处理后文本: {processed_text}")
            
            return [{"text": processed_text}]
            
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