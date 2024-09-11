from modelscope import snapshot_download

def download_funasr_model():
    print("开始下载FunASR模型...")
    model_dir = snapshot_download('iic/SenseVoiceSmall')
    print(f"模型下载完成。模型路径: {model_dir}")
    return model_dir

if __name__ == "__main__":
    download_funasr_model()