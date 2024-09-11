from funasr import AutoModel
import numpy as np

class FunASREngine:
    def __init__(self, model_dir):
        self.model = AutoModel(model=model_dir, 
                               model_revision="v2.0.4",
                               vad_model="fsmn-vad",
                               punc_model="ct-punc")

    def transcribe(self, audio_data):
        print(f"开始转写，音频数据长度：{len(audio_data)}")
        # 确保音频数据是float32类型
        if audio_data.dtype != np.float32:
            audio_data = audio_data.astype(np.float32)
        result = self.model.generate(input=audio_data, 
                                     batch_size_s=300,
                                     hotword='魔搭')  # 可以根据需要添加热词
        print(f"转写完成，结果：{result}")
        return result[0]["text"]

    def load_model(self, model_dir):
        self.model = AutoModel(model=model_dir, 
                               model_revision="v2.0.4",
                               vad_model="fsmn-vad",
                               punc_model="ct-punc")