"""
从 水印logo.png 生成应用图标 icon.ico
"""
import os
from PIL import Image

def create_icon():
    src = os.path.join(os.path.dirname(os.path.abspath(__file__)), "水印logo.png")
    dst = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")

    if not os.path.exists(src):
        print(f"错误: 未找到 {src}")
        return

    img = Image.open(src).convert("RGBA")

    # 生成多种尺寸的 ICO
    sizes = [16, 32, 48, 64, 128, 256]
    icons = []
    for s in sizes:
        resized = img.resize((s, s), Image.LANCZOS)
        icons.append(resized)

    icons[0].save(dst, format="ICO", sizes=[(s, s) for s in sizes], append_images=icons[1:])
    print(f"图标已生成: {dst}")


if __name__ == "__main__":
    create_icon()
