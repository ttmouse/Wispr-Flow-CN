#!/usr/bin/env python3
"""
ASR问题诊断脚本
"""

import sys
import os
import json
import numpy as np
from pathlib import Path

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

def check_settings():
    """检查设置文件"""
    print("🔍 检查设置文件...")
    
    try:
        with open('settings.json', 'r', encoding='utf-8') as f:
            settings = json.load(f)
        
        print(f"✅ 设置文件加载成功")
        print(f"📝 自动标点: {settings.get('asr', {}).get('auto_punctuation', 'N/A')}")
        print(f"📝 实时显示: {settings.get('asr', {}).get('real_time_display', 'N/A')}")
        print(f"📝 发音纠错: {settings.get('asr', {}).get('enable_pronunciation_correction', 'N/A')}")
        print(f"📝 热词权重: {settings.get('asr', {}).get('hotword_weight', 'N/A')}")
        
        return settings
    except Exception as e:
        print(f"❌ 设置文件检查失败: {e}")
        return None

def check_hotwords():
    """检查热词文件"""
    print("\n🔍 检查热词文件...")
    
    try:
        hotwords_file = Path("resources/hotwords.txt")
        if hotwords_file.exists():
            content = hotwords_file.read_text(encoding="utf-8")
            hotwords = [line.strip() for line in content.split('\n') if line.strip()]
            print(f"✅ 热词文件存在，包含 {len(hotwords)} 个热词")
            print(f"📝 前5个热词: {hotwords[:5]}")
            
            # 检查是否有可能导致问题的热词
            problematic = []
            for word in hotwords:
                if len(word) == 1 or word in ['的', '据', '一', '十']:
                    problematic.append(word)
            
            if problematic:
                print(f"⚠️  可能有问题的热词: {problematic}")
            
            return hotwords
        else:
            print(f"❌ 热词文件不存在: {hotwords_file}")
            return []
    except Exception as e:
        print(f"❌ 热词文件检查失败: {e}")
        return []

def check_models():
    """检查模型文件"""
    print("\n🔍 检查模型文件...")
    
    model_paths = [
        "src/modelscope/hub/damo/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch",
        "src/modelscope/hub/damo/punc_ct-transformer_zh-cn-common-vocab272727-pytorch"
    ]
    
    for model_path in model_paths:
        path = Path(model_path)
        if path.exists():
            print(f"✅ 模型目录存在: {model_path}")
            
            # 检查模型文件
            model_file = path / "model.pt"
            if model_file.exists():
                size = model_file.stat().st_size / (1024 * 1024)  # MB
                print(f"   📁 模型文件: {model_file.name} ({size:.1f} MB)")
            else:
                print(f"   ❌ 模型文件不存在: model.pt")
                
            # 检查配置文件
            config_file = path / "config.yaml"
            if config_file.exists():
                print(f"   📁 配置文件: {config_file.name}")
            else:
                print(f"   ⚠️  配置文件不存在: config.yaml")
        else:
            print(f"❌ 模型目录不存在: {model_path}")

def test_funasr_engine():
    """测试FunASR引擎"""
    print("\n🔍 测试FunASR引擎...")
    
    try:
        from src.funasr_engine import FunASREngine
        from src.settings_manager import SettingsManager
        
        # 创建设置管理器
        settings_manager = SettingsManager()
        
        # 创建引擎
        engine = FunASREngine(settings_manager)
        
        print(f"✅ FunASR引擎创建成功")
        print(f"📝 ASR模型状态: {'已加载' if engine.has_asr_model else '未加载'}")
        print(f"📝 标点模型状态: {'已加载' if engine.has_punc_model else '未加载'}")
        
        # 测试简单的音频数据
        print("\n🧪 测试简单音频识别...")
        
        # 创建一个简单的测试音频（静音）
        test_audio = np.zeros(16000, dtype=np.float32)  # 1秒静音
        
        result = engine.transcribe(test_audio)
        print(f"📝 静音测试结果: {result}")
        
        return engine
        
    except Exception as e:
        print(f"❌ FunASR引擎测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """主函数"""
    print("🔧 ASR问题诊断开始...")
    print("=" * 50)
    
    # 1. 检查设置
    settings = check_settings()
    
    # 2. 检查热词
    hotwords = check_hotwords()
    
    # 3. 检查模型
    check_models()
    
    # 4. 测试引擎
    engine = test_funasr_engine()
    
    print("\n" + "=" * 50)
    print("🔧 诊断完成")
    
    # 给出建议
    print("\n💡 建议:")
    if settings and settings.get('asr', {}).get('auto_punctuation', True):
        print("1. 尝试关闭自动标点功能")
    
    if hotwords and any(len(word) == 1 for word in hotwords):
        print("2. 移除单字符热词（如'的'、'据'等）")
    
    if not engine:
        print("3. 重新下载或重新安装模型")
    
    print("4. 检查录音设备和音频质量")
    print("5. 尝试重启应用程序")

if __name__ == "__main__":
    main()
