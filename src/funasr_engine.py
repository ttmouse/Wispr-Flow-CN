from funasr import AutoModel
import numpy as np
import os
import sys
import logging

# 设置 modelscope 日志级别为 WARNING，减少不必要的信息
logging.getLogger('modelscope').setLevel(logging.WARNING)

class FunASREngine:
    def __init__(self):
        try:
            self.model = AutoModel(
                model="damo/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch",
                model_revision="v2.0.4",
                disable_update=True,  # 禁用更新检查
                batch_size_s=300,
                use_itn=True,     # 启用逆文本正则化
                add_punc=True,    # 启用标点
                mode='offline'    # 使用离线模式以获得更好的标点效果
            )
        except Exception as e:
            print(f"❌ 模型加载失败: {e}")
            raise

    def transcribe(self, audio_data):
        """转写音频数据"""
        try:
            if audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)
            result = self.model.generate(input=audio_data)
            return result
        except Exception as e:
            print(f"❌ 转写失败: {e}")
            raise

    def get_model_path(self):
        return "使用预训练模型"