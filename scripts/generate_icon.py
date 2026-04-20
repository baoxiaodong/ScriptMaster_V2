from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "electron"
PNG_PATH = OUT_DIR / "icon.png"
ICO_PATH = OUT_DIR / "icon.ico"


def rounded_box(draw, box, radius, fill):
    draw.rounded_rectangle(box, radius=radius, fill=fill)


def main():
    size = 1024
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    # Background gradient.
    bg = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    bg_draw = ImageDraw.Draw(bg)
    for y in range(size):
      t = y / (size - 1)
      r = int(14 + (44 - 14) * t)
      g = int(18 + (56 - 18) * t)
      b = int(27 + (72 - 27) * t)
      bg_draw.line([(0, y), (size, y)], fill=(r, g, b, 255))

    shadow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.rounded_rectangle((120, 110, 904, 914), radius=220, fill=(0, 0, 0, 210))
    shadow = shadow.filter(ImageFilter.GaussianBlur(32))
    image.alpha_composite(shadow)
    image.alpha_composite(bg)

    # Outer tile.
    tile = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    tile_draw = ImageDraw.Draw(tile)
    tile_draw.rounded_rectangle((120, 100, 904, 884), radius=220, fill=(24, 29, 44, 255))
    tile_draw.rounded_rectangle((138, 118, 886, 866), radius=202, outline=(87, 98, 132, 255), width=4)
    image.alpha_composite(tile)

    # Warm accent glow.
    glow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    glow_draw.ellipse((540, 120, 980, 560), fill=(255, 164, 65, 90))
    glow_draw.ellipse((120, 500, 520, 940), fill=(245, 127, 31, 60))
    glow = glow.filter(ImageFilter.GaussianBlur(70))
    image.alpha_composite(glow)

    draw = ImageDraw.Draw(image)

    # Storyboard panels.
    panel_fill = (243, 239, 228, 255)
    panel_stroke = (212, 199, 170, 255)
    rounded_box(draw, (218, 220, 806, 740), 110, panel_fill)
    draw.rounded_rectangle((218, 220, 806, 740), radius=110, outline=panel_stroke, width=6)
    draw.line((510, 250, 510, 710), fill=(220, 208, 184, 255), width=10)
    draw.line((250, 480, 774, 480), fill=(220, 208, 184, 255), width=10)

    # Inner frame lines.
    line_color = (91, 90, 103, 150)
    for x1, y1, x2, y2 in [
        (278, 320, 450, 320),
        (278, 360, 430, 360),
        (278, 560, 450, 560),
        (278, 600, 420, 600),
        (570, 320, 730, 320),
        (570, 360, 700, 360),
        (570, 560, 730, 560),
        (570, 600, 710, 600),
    ]:
        draw.rounded_rectangle((x1, y1, x2, y2), radius=12, fill=line_color)

    # Central S mark.
    font = ImageFont.truetype("arialbd.ttf", 340)
    mark = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    mark_draw = ImageDraw.Draw(mark)
    bbox = mark_draw.textbbox((0, 0), "S", font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    text_x = (size - text_w) // 2
    text_y = (size - text_h) // 2 - 12

    # Glow behind the mark.
    glow_mark = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    glow_mark_draw = ImageDraw.Draw(glow_mark)
    glow_mark_draw.text((text_x, text_y), "S", font=font, fill=(255, 155, 52, 230))
    glow_mark = glow_mark.filter(ImageFilter.GaussianBlur(24))
    image.alpha_composite(glow_mark)

    # Solid mark.
    mark_draw.text((text_x, text_y), "S", font=font, fill=(255, 146, 43, 255))
    image.alpha_composite(mark)

    # Highlight edge.
    highlight = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    highlight_draw = ImageDraw.Draw(highlight)
    highlight_draw.text((text_x - 6, text_y - 6), "S", font=font, fill=(255, 220, 170, 120))
    highlight = highlight.filter(ImageFilter.GaussianBlur(2))
    image.alpha_composite(highlight)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    image.save(PNG_PATH)
    image.save(
        ICO_PATH,
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )


if __name__ == "__main__":
    main()
