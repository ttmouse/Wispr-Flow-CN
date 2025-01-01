from funasr import AutoModel
import numpy as np
import os
import sys

class FunASREngine:
    def __init__(self, model_dir=None):
        print(f"初始化 FunASREngine，模型路径: {model_dir if model_dir else '使用预训练模型'}")
        try:
            # 使用预定义的模型名称
            model_name = "damo/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch"
            model_revision = "v2.0.4"
            
            print(f"使用模型名称: {model_name}")
            print(f"模型版本: {model_revision}")
            
            # 初始化 ASR 模型
            self.model = AutoModel(
                model=model_name,
                model_revision=model_revision
            )
            print("成功初始化 AutoModel")
        except Exception as e:
            print(f"初始化 AutoModel 时出错: {e}")
            raise

    def transcribe(self, audio_data):
        print(f"开始转写，音频数据长度：{len(audio_data)}")
        if audio_data.dtype != np.float32:
            audio_data = audio_data.astype(np.float32)
            
        # 语音识别
        result = self.model.generate(
            input=audio_data, 
            batch_size_s=300,
            use_itn=True,     # 启用逆文本正则化
            add_punc=True,    # 启用标点
            mode='offline'    # 使用离线模式以获得更好的标点效果
        )
        print(f"转写完成，结果：{result}")
        
        # 处理结果文本：移除多余的空格
        text = result[0]["text"]
        text = text.replace(" ", "")
        
        return text

    def get_model_path(self):
        return "使用预训练模型"  # 因为我们现在使用预训练模型，所以返回一个描述性字符串