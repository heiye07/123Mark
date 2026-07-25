"""123Mark 水印渲染引擎。

仅负责图像计算，不依赖 Tkinter，便于自动化测试和复用。
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


RAINBOW_COLORS = [
    (235, 70, 77),
    (245, 139, 46),
    (242, 197, 61),
    (65, 168, 95),
    (48, 126, 226),
    (79, 76, 176),
    (153, 80, 190),
]

PRESET_COLORS = {
    "白色": (255, 255, 255),
    "黑色": (24, 27, 32),
    "红色": (220, 58, 58),
    "蓝色": (45, 112, 210),
    "绿色": (48, 153, 91),
    "黄色": (239, 190, 42),
    "橙色": (235, 126, 40),
    "紫色": (126, 77, 171),
    "灰色": (116, 122, 132),
    "彩虹": None,
}

FONT_SIZE_OPTIONS = [8, 10, 12, 14, 16, 18, 20, 24, 28, 32, 36, 42, 48, 56, 64, 72, 96, 128, 192, 256]

POSITION_PRESETS = {
    "左上": ("left", "top"),
    "中上": ("center", "top"),
    "右上": ("right", "top"),
    "左中": ("left", "center"),
    "居中": ("center", "center"),
    "右中": ("right", "center"),
    "左下": ("left", "bottom"),
    "中下": ("center", "bottom"),
    "右下": ("right", "bottom"),
}


def _clamp(value, minimum, maximum):
    return max(minimum, min(maximum, value))


def interpolate_color(c1, c2, t):
    """在两种 RGB 颜色之间插值。"""
    t = _clamp(float(t), 0.0, 1.0)
    return tuple(round(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def get_rainbow_color(ratio):
    """根据 0~1 的位置返回彩虹渐变色。"""
    ratio = _clamp(float(ratio), 0.0, 1.0)
    segment = ratio * (len(RAINBOW_COLORS) - 1)
    index = min(int(segment), len(RAINBOW_COLORS) - 2)
    return interpolate_color(RAINBOW_COLORS[index], RAINBOW_COLORS[index + 1], segment - index)


def _load_font(font_path=None, font_size=48):
    candidates = []
    if font_path:
        candidates.append(str(font_path))
    candidates.extend([
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/msyhbd.ttc",
        "C:/Windows/Fonts/simhei.ttf",
        "C:/Windows/Fonts/simsun.ttc",
        "C:/Windows/Fonts/arial.ttf",
    ])
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, max(1, int(font_size)))
        except (OSError, ValueError):
            continue
    return ImageFont.load_default()


def create_text_watermark_layer(
    text,
    size=None,
    font_path=None,
    font_size=48,
    color=(255, 255, 255),
    opacity=128,
    rotation=0,
    rainbow=False,
):
    """创建透明背景的 RGBA 文本水印图层。"""
    del size  # 保留旧版调用参数以兼容外部使用
    text = str(text or "水印")
    font_size = _clamp(int(font_size), 1, 1024)
    opacity = _clamp(int(opacity), 0, 255)
    font = _load_font(font_path, font_size)

    probe = Image.new("L", (1, 1))
    bbox = ImageDraw.Draw(probe).multiline_textbbox((0, 0), text, font=font, spacing=max(2, font_size // 6))
    text_width = max(1, bbox[2] - bbox[0])
    text_height = max(1, bbox[3] - bbox[1])
    padding = max(5, font_size // 4)
    canvas_size = (text_width + padding * 2, text_height + padding * 2)
    draw_position = (padding - bbox[0], padding - bbox[1])

    mask = Image.new("L", canvas_size, 0)
    ImageDraw.Draw(mask).multiline_text(
        draw_position,
        text,
        font=font,
        fill=opacity,
        spacing=max(2, font_size // 6),
        align="left",
    )

    if rainbow:
        layer = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
        gradient = ImageDraw.Draw(layer)
        for x in range(canvas_size[0]):
            ratio = (x - padding) / max(text_width - 1, 1)
            rgb = get_rainbow_color(ratio)
            gradient.line((x, 0, x, canvas_size[1]), fill=(*rgb, 255))
        layer.putalpha(mask)
    else:
        rgb = tuple(int(v) for v in color[:3])
        layer = Image.new("RGBA", canvas_size, (*rgb, 0))
        layer.putalpha(mask)

    rotation = float(rotation)
    if rotation:
        layer = layer.rotate(rotation, expand=True, resample=Image.Resampling.BICUBIC)
    return layer


def create_image_watermark_layer(watermark_path, target_size=None, opacity=128, scale_percent=None):
    """从图片创建 RGBA 水印图层，并按原图百分比或边界尺寸缩放。"""
    with Image.open(watermark_path) as source:
        watermark = ImageOps.exif_transpose(source).convert("RGBA")

    if scale_percent is not None:
        ratio = _clamp(float(scale_percent), 1.0, 1000.0) / 100.0
        new_size = (
            max(1, round(watermark.width * ratio)),
            max(1, round(watermark.height * ratio)),
        )
        watermark = watermark.resize(new_size, Image.Resampling.LANCZOS)
    elif target_size:
        watermark.thumbnail(tuple(max(1, int(v)) for v in target_size), Image.Resampling.LANCZOS)

    opacity = _clamp(int(opacity), 0, 255)
    alpha = watermark.getchannel("A").point(lambda value: round(value * opacity / 255))
    watermark.putalpha(alpha)
    return watermark


def _fit_watermark(watermark_layer, image_size):
    """仅在水印超出画布时等比缩小，避免完全不可见。"""
    iw, ih = image_size
    ww, wh = watermark_layer.size
    max_width = max(1, round(iw * 0.94))
    max_height = max(1, round(ih * 0.94))
    if ww <= max_width and wh <= max_height:
        return watermark_layer
    fitted = watermark_layer.copy()
    fitted.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
    return fitted


def apply_watermark(
    image,
    watermark_layer,
    position="右下",
    margin=20,
    tile=False,
    tile_rows=3,
    tile_cols=3,
):
    """将一个水印图层应用到图片，支持九宫格位置与精确行列平铺。"""
    base = image.convert("RGBA")
    watermark_layer = _fit_watermark(watermark_layer.convert("RGBA"), base.size)
    iw, ih = base.size
    ww, wh = watermark_layer.size
    margin = _clamp(int(margin), 0, max(iw, ih))

    if position in POSITION_PRESETS:
        horizontal, vertical = POSITION_PRESETS[position]
    elif isinstance(position, (list, tuple)) and len(position) == 2:
        px = round((iw - ww) * _clamp(float(position[0]), 0.0, 1.0))
        py = round((ih - wh) * _clamp(float(position[1]), 0.0, 1.0))
        base.alpha_composite(watermark_layer, (px, py))
        return base
    else:
        horizontal, vertical = POSITION_PRESETS["右下"]

    if tile:
        rows = _clamp(int(tile_rows), 1, 50)
        cols = _clamp(int(tile_cols), 1, 50)
        margin_x = min(margin, max(0, (iw - 1) // 2))
        margin_y = min(margin, max(0, (ih - 1) // 2))
        inner_width = max(1, iw - margin_x * 2)
        inner_height = max(1, ih - margin_y * 2)
        cell_width = inner_width / cols
        cell_height = inner_height / rows
        max_mark_width = max(1, round(cell_width * 0.86))
        max_mark_height = max(1, round(cell_height * 0.72))
        if ww > max_mark_width or wh > max_mark_height:
            watermark_layer = watermark_layer.copy()
            watermark_layer.thumbnail((max_mark_width, max_mark_height), Image.Resampling.LANCZOS)
            ww, wh = watermark_layer.size
        for row in range(rows):
            y = round(margin_y + (row + 0.5) * cell_height - wh / 2)
            for column in range(cols):
                x = round(margin_x + (column + 0.5) * cell_width - ww / 2)
                base.alpha_composite(watermark_layer, (x, y))
        return base

    x_positions = {
        "left": min(margin, max(0, iw - ww)),
        "center": (iw - ww) // 2,
        "right": max(0, iw - ww - margin),
    }
    y_positions = {
        "top": min(margin, max(0, ih - wh)),
        "center": (ih - wh) // 2,
        "bottom": max(0, ih - wh - margin),
    }
    base.alpha_composite(watermark_layer, (x_positions[horizontal], y_positions[vertical]))
    return base


def process_image(image_path, watermark_params):
    """读取单张图片并应用水印，返回 RGBA 图像。"""
    image_path = Path(image_path)
    with Image.open(image_path) as source:
        image = ImageOps.exif_transpose(source).convert("RGBA")

    mode = watermark_params.get("mode", "text")
    opacity = watermark_params.get("opacity", 128)
    if mode == "text":
        rainbow = bool(watermark_params.get("rainbow", False))
        watermark = create_text_watermark_layer(
            text=watermark_params.get("text", "水印"),
            font_path=watermark_params.get("font_path"),
            font_size=watermark_params.get("font_size", 48),
            color=watermark_params.get("color", (255, 255, 255)),
            opacity=opacity,
            rotation=watermark_params.get("rotation", 0),
            rainbow=rainbow,
        )
    elif mode == "image":
        watermark_path = watermark_params.get("image_path", "")
        if not watermark_path:
            raise ValueError("请选择水印图片")
        watermark = create_image_watermark_layer(
            watermark_path,
            target_size=watermark_params.get("image_size"),
            opacity=opacity,
            scale_percent=watermark_params.get("image_scale"),
        )
    else:
        raise ValueError(f"不支持的水印模式：{mode}")

    return apply_watermark(
        image,
        watermark,
        position=watermark_params.get("position", "右下"),
        margin=watermark_params.get("margin", 20),
        tile=watermark_params.get("tile", False),
        tile_rows=watermark_params.get("tile_rows", 3),
        tile_cols=watermark_params.get("tile_cols", 3),
    )
