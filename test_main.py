#!/usr/bin/env python3
"""
测试修复后的主程序
"""
import sys
import os

# 添加项目根目录和src目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')

# 确保src目录在Python路径中
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

def main():
    """主函数"""
    try:
        print("🔧 测试修复后的应用启动...")
        
        # 导入并运行应用
        # 切换到src目录运行
        os.chdir('src')
        from main import main as app_main
        return app_main()
        
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
