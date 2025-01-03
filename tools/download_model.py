import os
import requests
import tarfile
import logging

def download_funasr_model():
    model_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models', 'paraformer-zh')
    if os.path.exists(model_dir):
        logging.info(f"模型已存在于 {model_dir}")
        return model_dir

    logging.info("开始下载FunASR模型...")
    url = "https://isv-data.oss-cn-hangzhou.aliyuncs.com/ics/MaaS/ASR/models/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch.tar.gz"
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error(f"下载模型失败: {e}")
        raise

    os.makedirs(os.path.dirname(model_dir), exist_ok=True)
    tar_file = "model.tar.gz"
    with open(tar_file, "wb") as f:
        f.write(response.content)
    
    logging.info("解压模型文件...")
    try:
        with tarfile.open(tar_file, 'r:gz') as tar:
            tar.extractall(path=model_dir)
    except tarfile.TarError as e:
        logging.error(f"解压模型文件失败: {e}")
        raise
    finally:
        os.remove(tar_file)

    logging.info(f"模型已下载并解压到 {model_dir}")
    return model_dir

if __name__ == "__main__":
    print(download_funasr_model())