from PIL import Image, ImageDraw, ImageFont
import os

def create_default_icon():
    # 创建一个512x512的图像
    size = 512
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # 绘制圆形背景
    circle_margin = size // 10
    circle_size = size - (2 * circle_margin)
    circle_pos = (circle_margin, circle_margin)
    draw.ellipse([circle_pos, (circle_pos[0] + circle_size, circle_pos[1] + circle_size)], 
                fill='#007AFF')
    
    # 添加文字
    try:
        # 尝试加载系统字体
        font_size = size // 2
        font = ImageFont.truetype("/System/Library/Fonts/SFCompact.ttf", font_size)
    except:
        # 如果失败，使用默认字体
        font = ImageFont.load_default()
    
    # 绘制文字
    text = "D"
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    text_x = (size - text_width) // 2
    text_y = (size - text_height) // 2
    draw.text((text_x, text_y), text, font=font, fill='white')
    
    # 保存图标
    img.save('icon.png', 'PNG')
    print("✓ 已创建默认图标：icon.png")

if __name__ == "__main__":
    create_default_icon() 