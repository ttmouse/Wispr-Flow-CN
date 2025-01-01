import funasr
import gc
import torch

class FunASREngine:
    def __init__(self):
        self.model = funasr.AutoModel(
            model="paraformer-zh",
            model_revision="v2.0.4",
            device="cpu",
            disable_update=True,  # 禁用更新检查
            use_quantization=True  # 使用量化以减少内存使用
        )

    def transcribe(self, audio_data):
        result = self.model.generate(input=audio_data)
        return result

    def set_hotwords(self, hotwords):
        self.model.set_hotwords(hotwords)

    def close(self):
        # 确保所有资源都被释放
        if hasattr(self, 'model'):
            # 尝试更彻底地清理模型
            if hasattr(self.model, 'close'):
                self.model.close()
            elif hasattr(self.model, 'cleanup'):
                self.model.cleanup()
            del self.model
        
        # 清理 CUDA 缓存（如果使用了 GPU）
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        # 强制进行垃圾回收
        gc.collect()

    def __del__(self):
        self.close()