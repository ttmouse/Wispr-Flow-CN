import os
import subprocess
from PIL import Image
import glob
import tempfile
import shutil
from contextlib import contextmanager

@contextmanager
def temp_iconset_dir():
    """创建临时图标集目录的上下文管理器"""
    temp_dir = None
    try:
        temp_dir = tempfile.mkdtemp(suffix='.iconset')
        yield temp_dir
    finally:
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)

def find_icon_file():
    """查找可用的图标文件"""
    # 优先使用 icon_1024.png
    if os.path.exists("icon_1024.png"):
        return "icon_1024.png"
        
    # 其他支持的图片格式
    icon_files = glob.glob("icon.*")
    supported_formats = ['.png', '.jpg', '.jpeg', '.ico', '.bmp']
    
    for icon_file in icon_files:
        ext = os.path.splitext(icon_file)[1].lower()
        if ext in supported_formats:
            return icon_file
    return None

def convert_to_icns():
    """将图片文件转换为 .icns 文件"""
    # 查找图标文件
    icon_file = find_icon_file()
    if not icon_file:
        print("❌ 未找到可用的图标文件")
        print("支持的格式：png, jpg, jpeg, ico, bmp")
        print("请确保图标文件名为 icon.xxx")
        return False
    
    # 检查是否需要重新生成图标
    if os.path.exists('app_icon.icns'):
        try:
            icon_mtime = os.path.getmtime(icon_file)
            icns_mtime = os.path.getmtime('app_icon.icns')
            
            # 如果 .icns 文件比源图片文件新，则跳过转换
            if icns_mtime > icon_mtime:
                print(f"✓ app_icon.icns 已是最新版本，跳过转换")
                return True
        except OSError as e:
            print(f"⚠️ 检查文件时间戳时出错: {e}")
    
    # 使用临时目录管理器确保资源清理
    with temp_iconset_dir() as temp_dir:
        try:
            # 读取并验证图片文件
            with Image.open(icon_file) as img:
                # 如果是 RGBA 模式，保持透明度；否则转换
                if img.mode not in ['RGBA', 'RGB']:
                    img = img.convert('RGBA')
                
                # 需要的尺寸列表
                sizes = [16, 32, 64, 128, 256, 512, 1024]
                
                # 为每个尺寸创建图标
                for size in sizes:
                    try:
                        # 调整图像大小，使用高质量的重采样
                        resized = img.resize((size, size), Image.Resampling.LANCZOS)
                        
                        # 保存不同尺寸的图标
                        icon_name = os.path.join(temp_dir, f'icon_{size}x{size}.png')
                        resized.save(icon_name, 'PNG', optimize=True)
                        
                        # 创建 @2x 版本（除了最小尺寸）
                        if size > 16:
                            icon_name_2x = os.path.join(temp_dir, f'icon_{size//2}x{size//2}@2x.png')
                            resized.save(icon_name_2x, 'PNG', optimize=True)
                        
                        # 立即释放内存
                        resized.close()
                        
                    except Exception as e:
                        print(f"⚠️ 创建 {size}x{size} 图标时出错: {e}")
                        continue
            
            # 使用 iconutil 创建 .icns 文件
            try:
                result = subprocess.run(
                    ['iconutil', '-c', 'icns', temp_dir, '-o', 'temp_icon.icns'],
                    capture_output=True,
                    text=True,
                    timeout=30  # 30秒超时
                )
                
                if result.returncode != 0:
                    print(f"❌ iconutil 执行失败: {result.stderr}")
                    return False
                
                # 安全地替换现有文件
                if os.path.exists('temp_icon.icns'):
                    if os.path.exists('app_icon.icns'):
                        os.remove('app_icon.icns')
                    os.rename('temp_icon.icns', 'app_icon.icns')
                    print(f"✓ 已将 {icon_file} 转换为 app_icon.icns")
                    return True
                else:
                    print("❌ iconutil 未生成预期的 .icns 文件")
                    return False
                    
            except subprocess.TimeoutExpired:
                print("❌ iconutil 执行超时")
                return False
            except Exception as e:
                print(f"❌ 执行 iconutil 时出错: {e}")
                return False
                
        except Exception as e:
            print(f"❌ 转换图标时出错: {e}")
            return False
        finally:
            # 清理可能残留的临时文件
            for temp_file in ['temp_icon.icns', 'icon.icns']:
                if os.path.exists(temp_file):
                    try:
                        os.remove(temp_file)
                    except:
                        pass

if __name__ == "__main__":
    convert_to_icns()