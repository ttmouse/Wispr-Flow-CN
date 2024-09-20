import numpy as np
from funasr import AutoModel
import logging
import traceback

class FunASREngine:
    def __init__(self, model_dir=None):
        self.model = None
        self.load_model(model_dir)

    def load_model(self, model_dir=None):
        try:
            logging.info(f"正在加载模型，模型目录: {'使用预训练模型' if model_dir is None else model_dir}")
            self.model = AutoModel(model="paraformer-zh",
                                   model_revision="v2.0.4",
                                   device="cpu",
                                   use_decoder=False,
                                   use_itn=True)
            logging.info("模型加载成功")
        except Exception as e:
            logging.error(f"加载模型时出错: {e}")
            logging.error(traceback.format_exc())
            raise

    def transcribe(self, audio_data):
        if self.model is None:
            raise ValueError("模型未加载")
        try:
            result = self.model.generate(input=audio_data)
            return result[0]['text']
        except Exception as e:
            logging.error(f"转录音频时出错: {e}")
            logging.error(traceback.format_exc())
            raise