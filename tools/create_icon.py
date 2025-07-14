import os
import subprocess
from PIL import Image
import glob
import os

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
        icon_mtime = os.path.getmtime(icon_file)
        icns_mtime = os.path.getmtime('app_icon.icns')
        
        # 如果 .icns 文件比源图片文件新，则跳过转换
        if icns_mtime > icon_mtime:
            print(f"✓ app_icon.icns 已是最新版本，跳过转换")
            return True
        
    try:
        # 创建临时目录
        if not os.path.exists('iconset.iconset'):
            os.makedirs('iconset.iconset')
        
        # 读取图片文件
        img = Image.open(icon_file)
        
        # 如果是 RGBA 模式，保持透明度
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        # 需要的尺寸列表
        sizes = [16, 32, 64, 128, 256, 512, 1024]
        
        # 为每个尺寸创建图标
        for size in sizes:
            # 调整图像大小，使用高质量的重采样
            resized = img.resize((size, size), Image.Resampling.LANCZOS)
            
            # 保存不同尺寸的图标
            icon_name = f'iconset.iconset/icon_{size}x{size}.png'
            resized.save(icon_name, 'PNG')
            
            # 创建 @2x 版本
            icon_name_2x = f'iconset.iconset/icon_{size//2}x{size//2}@2x.png'
            if size > 16:  # 不为最小尺寸创建 @2x 版本
                resized.save(icon_name_2x, 'PNG')
        
        # 使用 iconutil 创建 .icns 文件
        subprocess.run(['iconutil', '-c', 'icns', 'iconset.iconset'])
        
        # 重命名为 app_icon.icns
        if os.path.exists('icon.icns'):
            if os.path.exists('app_icon.icns'):
                os.remove('app_icon.icns')
            os.rename('icon.icns', 'app_icon.icns')
        
        # 清理临时文件
        subprocess.run(['rm', '-rf', 'iconset.iconset'])
        
        print(f"✓ 已将 {icon_file} 转换为 app_icon.icns")
        return True
        
    except Exception as e:
        print(f"❌ 转换图标时出错: {e}")
        # 清理临时文件
        if os.path.exists('iconset.iconset'):
            subprocess.run(['rm', '-rf', 'iconset.iconset'])
        return False

if __name__ == "__main__":
    convert_to_icns()