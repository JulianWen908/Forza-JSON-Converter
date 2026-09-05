# -*- coding: utf-8 -*-
"""生成应用图标 assets/app.ico（PIL 绘制，无外部素材）。"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def draw_icon(size: int) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 圆角方形底色（深蓝）
    pad = size * 0.06
    draw.rounded_rectangle(
        [pad, pad, size - pad, size - pad],
        radius=size * 0.22,
        fill=(30, 41, 66, 255),
    )

    # 两个圆角矩形（浅色主题的“文档”），左蓝右青
    box_w = size * 0.22
    box_h = size * 0.34
    y1 = size * 0.24
    y2 = size * 0.42
    left_x = size * 0.16
    right_x = size * 0.62
    draw.rounded_rectangle([left_x, y1, left_x + box_w, y1 + box_h], radius=size * 0.05, fill=(10, 132, 255, 255))
    draw.rounded_rectangle([right_x, y1, right_x + box_w, y1 + box_h], radius=size * 0.05, fill=(48, 176, 192, 255))

    # 双向箭头
    arrow_y = y2 + box_h + size * 0.08
    line_w = max(2, int(size * 0.04))
    draw.line([size * 0.22, arrow_y, size * 0.78, arrow_y], fill=(240, 240, 240, 255), width=line_w)
    head = size * 0.07
    # 右箭头
    draw.polygon(
        [
            (size * 0.78, arrow_y - head),
            (size * 0.78 + head, arrow_y),
            (size * 0.78, arrow_y + head),
        ],
        fill=(240, 240, 240, 255),
    )
    # 左箭头
    draw.polygon(
        [
            (size * 0.22, arrow_y - head),
            (size * 0.22 - head, arrow_y),
            (size * 0.22, arrow_y + head),
        ],
        fill=(240, 240, 240, 255),
    )

    # “FH5 / FH6” 文字
    font = ImageFont.load_default(size=max(10, int(size * 0.11)))
    text = "FH5 ↔ FH6"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(
        ((size - tw) / 2 - bbox[0], size * 0.76 - bbox[1]),
        text,
        font=font,
        fill=(255, 255, 255, 230),
    )
    return img


def main() -> None:
    out_dir = Path(__file__).resolve().parent / "assets"
    out_dir.mkdir(exist_ok=True)
    sizes = [16, 24, 32, 48, 64, 128, 256]
    images = [draw_icon(s) for s in sizes]
    ico_path = out_dir / "app.ico"
    images[-1].save(ico_path, format="ICO", sizes=[(s, s) for s in sizes])
    print(f"icon written: {ico_path}")


if __name__ == "__main__":
    main()
