from funasr import AutoModel
import numpy as np
import os
import sys

class FunASREngine:
    def __init__(self, model_dir=None):
        print(f"初始化 FunASREngine，模型路径: {model_dir if model_dir else '使用预训练模型'}")
        try:
            # 使用预定义的模型名称
            model_name = "paraformer-zh"
            
            print(f"使用模型名称: {model_name}")
            
            self.model = AutoModel(model=model_name,
                                   model_revision="v2.0.4",
                                   vad_model="fsmn-vad",
                                   punc_model="ct-punc")
            print("成功初始化 AutoModel")
        except Exception as e:
            print(f"初始化 AutoModel 时出错: {e}")
            raise

    def transcribe(self, audio_data):
        print(f"开始转写，音频数据长度：{len(audio_data)}")
        if audio_data.dtype != np.float32:
            audio_data = audio_data.astype(np.float32)
        result = self.model.generate(input=audio_data, 
                                     batch_size_s=300,
                                     hotword='魔搭')
        print(f"转写完成，结果：{result}")
        return result[0]["text"]

    def get_model_path(self):
        return "使用预训练模型"  # 因为我们现在使用预训练模型，所以返回一个描述性字符串