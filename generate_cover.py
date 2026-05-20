"""Generate AGREEABLE podcast cover art (3000x3000 px)."""

from PIL import Image, ImageDraw, ImageFont, ImageFilter
import math
from pathlib import Path

OUT = Path(__file__).resolve().parent / "cover.png"
SIZE = 3000

img = Image.new("RGB", (SIZE, SIZE), (8, 10, 20))
draw = ImageDraw.Draw(img)

# ── background gradient (top dark navy -> bottom near-black) ──────────────
for y in range(SIZE):
    t = y / SIZE
    r = int(8  + (18 - 8)  * (1 - t))
    g = int(10 + (24 - 10) * (1 - t))
    b = int(20 + (48 - 20) * (1 - t))
    draw.line([(0, y), (SIZE, y)], fill=(r, g, b))

# ── subtle dot grid ───────────────────────────────────────────────────────
GRID = 75
for gx in range(0, SIZE, GRID):
    for gy in range(0, SIZE, GRID):
        draw.ellipse([gx - 1, gy - 1, gx + 1, gy + 1], fill=(40, 55, 90))

# ── concentric rings (centred, very faint) ────────────────────────────────
cx, cy = SIZE // 2, SIZE // 2
for r in range(200, 1600, 200):
    draw.ellipse([cx - r, cy - r, cx + r, cy + r],
                 outline=(30, 50, 100, 60), width=1)

# ── glowing centre dot ────────────────────────────────────────────────────
for r, alpha in [(180, 15), (90, 30), (40, 60), (14, 130), (6, 220)]:
    colour = (100 + (220 - 100) * (1 - r / 180),
              140 + (240 - 140) * (1 - r / 180),
              255)
    colour = tuple(int(c) for c in colour)
    glow = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    gd   = ImageDraw.Draw(glow)
    gd.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(*colour, alpha))
    img.paste(Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB"))

# ── font helper: fall back gracefully ────────────────────────────────────
def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = (
        ["/System/Library/Fonts/Helvetica.ttc",
         "/System/Library/Fonts/HelveticaNeue.ttc",
         "/System/Library/Fonts/SFNSDisplay.ttf",
         "/System/Library/Fonts/SFNS.ttf",
         "/Library/Fonts/Arial Bold.ttf" if bold else "/Library/Fonts/Arial.ttf",
         "/System/Library/Fonts/Supplemental/Arial.ttf"]
    )
    for path in candidates[0]:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass
    return ImageFont.load_default()

draw = ImageDraw.Draw(img)

# ── title: AGREEABLE ──────────────────────────────────────────────────────
title      = "AGREEABLE"
title_font = font(320, bold=True)
bbox       = draw.textbbox((0, 0), title, font=title_font, stroke_width=0)
tw         = bbox[2] - bbox[0]
th         = bbox[3] - bbox[1]
tx         = (SIZE - tw) // 2
ty         = cy - th // 2 - 180

# soft drop shadow
for ox, oy in [(-4, 4), (-2, 4), (0, 4), (2, 4), (4, 4)]:
    draw.text((tx + ox, ty + oy), title, font=title_font, fill=(0, 0, 0, 80))

# main text — white with subtle blue tint
draw.text((tx, ty), title, font=title_font, fill=(230, 238, 255))

# ── thin rule below title ─────────────────────────────────────────────────
rule_y = ty + th + 40
draw.rectangle([tx, rule_y, tx + tw, rule_y + 3], fill=(80, 120, 220))

# ── tagline ───────────────────────────────────────────────────────────────
tagline      = "the politest apocalypse in history"
tag_font     = font(88)
tbbox        = draw.textbbox((0, 0), tagline, font=tag_font)
tag_w        = tbbox[2] - tbbox[0]
draw.text(((SIZE - tag_w) // 2, rule_y + 30), tagline,
          font=tag_font, fill=(120, 155, 220))

# ── episode count ─────────────────────────────────────────────────────────
sub      = "6 EPISODES"
sub_font = font(70)
sbbox    = draw.textbbox((0, 0), sub, font=sub_font)
sub_w    = sbbox[2] - sbbox[0]
draw.text(((SIZE - sub_w) // 2, SIZE - 280), sub,
          font=sub_font, fill=(60, 90, 160))

# ── very slight vignette ──────────────────────────────────────────────────
vignette = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
vd = ImageDraw.Draw(vignette)
for i in range(300):
    a = int(120 * (i / 300) ** 2)
    vd.rectangle([i, i, SIZE - i, SIZE - i], outline=(0, 0, 0, a))
img = Image.alpha_composite(img.convert("RGBA"), vignette).convert("RGB")

img.save(OUT, "PNG")
print(f"Saved: {OUT}  ({OUT.stat().st_size // 1024} KB)")
