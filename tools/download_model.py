import os
import requests
import tarfile
import logging
from tqdm import tqdm

MODEL_CONFIGS = {
    "asr": {
        "name": "ASR语音识别模型",
        "url": "https://isv-data.oss-cn-hangzhou.aliyuncs.com/ics/MaaS/ASR/models/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch.tar.gz",
        "dir_name": "paraformer-zh"
    },
    "punc": {
        "name": "标点符号模型",
        "url": "https://isv-data.oss-cn-hangzhou.aliyuncs.com/ics/MaaS/ASR/models/ct-transformer_zh-cn-common-vocab272727-pytorch.tar.gz",
        "dir_name": "ct-transformer"
    }
}

def download_with_progress(url: str, file_path: str, desc: str):
    """带进度条的下载函数"""
    response = requests.get(url, stream=True)
    response.raise_for_status()
    total_size = int(response.headers.get('content-length', 0))
    
    with open(file_path, 'wb') as f, tqdm(
        desc=desc,
        total=total_size,
        unit='iB',
        unit_scale=True,
        unit_divisor=1024,
    ) as pbar:
        for data in response.iter_content(chunk_size=1024):
            size = f.write(data)
            pbar.update(size)

def download_model(model_type: str):
    """下载指定类型的模型"""
    if model_type not in MODEL_CONFIGS:
        raise ValueError(f"不支持的模型类型: {model_type}")
    
    config = MODEL_CONFIGS[model_type]
    model_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models', config['dir_name'])
    
    if os.path.exists(model_dir):
        logging.info(f"{config['name']}已存在于 {model_dir}")
        return model_dir

    logging.info(f"开始下载{config['name']}...")
    try:
        os.makedirs(os.path.dirname(model_dir), exist_ok=True)
        tar_file = f"{model_type}_model.tar.gz"
        
        # 下载模型文件
        download_with_progress(config['url'], tar_file, f"下载{config['name']}")
        
        # 解压模型文件
        logging.info(f"正在解压{config['name']}...")
        try:
            with tarfile.open(tar_file, 'r:gz') as tar:
                tar.extractall(path=model_dir)
        except tarfile.TarError as e:
            logging.error(f"解压{config['name']}失败: {e}")
            raise
        finally:
            if os.path.exists(tar_file):
                os.remove(tar_file)

        logging.info(f"{config['name']}已下载并解压到 {model_dir}")
        return model_dir
        
    except requests.exceptions.RequestException as e:
        logging.error(f"下载{config['name']}失败: {e}")
        raise
    except Exception as e:
        logging.error(f"处理{config['name']}时发生错误: {e}")
        raise

def ensure_models():
    """确保所有必需的模型都已下载"""
    results = {}
    for model_type in MODEL_CONFIGS:
        try:
            model_dir = download_model(model_type)
            results[model_type] = {"success": True, "path": model_dir}
        except Exception as e:
            results[model_type] = {"success": False, "error": str(e)}
    return results

if __name__ == "__main__":
    # 设置日志格式
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # 下载所有模型
    results = ensure_models()
    
    # 打印结果
    for model_type, result in results.items():
        if result["success"]:
            print(f"✓ {MODEL_CONFIGS[model_type]['name']}下载成功: {result['path']}")
        else:
            print(f"❌ {MODEL_CONFIGS[model_type]['name']}下载失败: {result['error']}")