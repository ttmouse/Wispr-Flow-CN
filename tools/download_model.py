import os
import logging
import shutil
import subprocess
from tqdm import tqdm
import sys
import time
import threading

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# 预估的模型大小（字节）
MODEL_SIZES = {
    'asr': 1024 * 1024 * 1024,  # 约1GB
    'punc': 300 * 1024 * 1024    # 约300MB
}

MODELS = {
    'asr': {
        'name': 'speech_paraformer-large-vad-punc_asr_nat-zh-cn-16k-common-vocab8404-pytorch',
        'url': 'https://www.modelscope.cn/iic/speech_paraformer-large-vad-punc_asr_nat-zh-cn-16k-common-vocab8404-pytorch.git'
    },
    'punc': {
        'name': 'punc_ct-transformer_zh-cn-common-vocab272727-pytorch',
        'url': 'https://www.modelscope.cn/iic/punc_ct-transformer_zh-cn-common-vocab272727-pytorch.git'
    }
}

def get_dir_size(path):
    """获取目录大小"""
    total_size = 0
    if os.path.exists(path):
        for dirpath, dirnames, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if not os.path.islink(fp):  # 跳过符号链接
                    total_size += os.path.getsize(fp)
    return total_size

def show_download_progress(model_dir: str, model_type: str, pbar: tqdm):
    """显示下载进度"""
    last_size = 0
    while True:
        current_size = get_dir_size(model_dir)
        if current_size > last_size:
            pbar.update(current_size - last_size)
            last_size = current_size
        time.sleep(0.1)
        if not os.path.exists(os.path.join(model_dir, '.git')):
            # 如果.git目录消失，说明下载已完成
            break

def download_model(model_type: str, test_mode: bool = False) -> str:
    """下载指定类型的模型
    
    Args:
        model_type: 模型类型 ('asr' 或 'punc')
        test_mode: 是否为测试模式，如果是则下载到临时目录
    """
    if model_type not in MODELS:
        raise ValueError(f"不支持的模型类型: {model_type}")
    
    model_info = MODELS[model_type]
    model_name = model_info['name']
    model_url = model_info['url']
    
    # 设置模型目录
    base_dir = os.path.dirname(os.path.dirname(__file__))
    if test_mode:
        model_dir = os.path.join(base_dir, 'test_models', model_name)
    else:
        model_dir = os.path.join(base_dir, 'src', 'modelscope', 'hub', 'damo', model_name)
    
    if os.path.exists(model_dir):
        logging.info(f"模型已存在于 {model_dir}")
        return model_dir

    logging.info(f"开始下载{model_type}模型...")
    
    try:
        # 创建父目录
        os.makedirs(os.path.dirname(model_dir), exist_ok=True)
        
        # 使用 git clone 下载模型
        logging.info(f"克隆仓库 {model_url}")
        process = subprocess.Popen(
            ['git', 'clone', model_url, model_dir],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # 创建进度条
        with tqdm(
            total=MODEL_SIZES[model_type],
            unit='B',
            unit_scale=True,
            desc=f"下载{model_type}模型",
            bar_format='{desc}: {percentage:3.1f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]'
        ) as pbar:
            # 启动进度监控线程
            progress_thread = threading.Thread(
                target=show_download_progress,
                args=(model_dir, model_type, pbar)
            )
            progress_thread.daemon = True  # 设置为守护线程
            progress_thread.start()
            
            # 等待下载完成
            stdout, stderr = process.communicate()
            
            # 更新到最终大小
            final_size = get_dir_size(model_dir)
            pbar.update(final_size - pbar.n)
        
        if process.returncode != 0:
            raise subprocess.CalledProcessError(
                process.returncode,
                ['git', 'clone'],
                stdout,
                stderr
            )
        
        print(f"\n✓ {model_type}模型已下载到 {model_dir}")
        
    except subprocess.CalledProcessError as e:
        logging.error(f"下载{model_type}模型失败: {e.stderr}")
        if os.path.exists(model_dir):
            shutil.rmtree(model_dir)
        raise RuntimeError(f"Git clone 失败: {e.stderr}")
    except Exception as e:
        logging.error(f"处理{model_type}模型时发生错误: {e}")
        if os.path.exists(model_dir):
            shutil.rmtree(model_dir)
        raise
    
    return model_dir

def download_all_models(test_mode: bool = False):
    """下载所有必要的模型
    
    Args:
        test_mode: 是否为测试模式，如果是则下载到临时目录
    """
    results = {}
    for model_type in MODELS:
        try:
            model_dir = download_model(model_type, test_mode)
            results[model_type] = {
                'status': 'success',
                'path': model_dir
            }
        except Exception as e:
            results[model_type] = {
                'status': 'failed',
                'error': str(e)
            }
            logging.error(f"{model_type}模型处理失败: {e}")
    return results

def cleanup_test_models():
    """清理测试模型目录"""
    base_dir = os.path.dirname(os.path.dirname(__file__))
    test_dir = os.path.join(base_dir, 'test_models')
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
        logging.info(f"已清理测试目录: {test_dir}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='下载FunASR模型')
    parser.add_argument('--test', action='store_true', help='测试模式：下载到临时目录')
    parser.add_argument('--cleanup', action='store_true', help='清理测试目录')
    args = parser.parse_args()
    
    if args.cleanup:
        cleanup_test_models()
    else:
        logging.info("开始下载所有必要的模型...")
        results = download_all_models(test_mode=args.test)
        
        # 打印下载结果
        print("\n下载结果汇总:")
        for model_type, result in results.items():
            status = result['status']
            if status == 'success':
                print(f"✓ {model_type}模型: 已下载到 {result['path']}")
            else:
                print(f"✗ {model_type}模型: 下载失败 - {result['error']}")