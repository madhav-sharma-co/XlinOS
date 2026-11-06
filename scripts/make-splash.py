#!/usr/bin/env python3
"""Makes the boot-menu splash (640x480, the size syslinux wants) from the Xlin X mark. Usage: make-splash.py out.png"""
import sys, glob
from PIL import Image, ImageDraw, ImageFont, ImageFilter
ROOT = __import__("os").path.dirname(__import__("os").path.dirname(__import__("os").path.abspath(__file__)))
BG = (3, 8, 28)
src = Image.open(f"{ROOT}/assets/logo/xlin-soft-dark.png").convert("RGB")
mark = src.crop((142, 480, 452, 775))              # the X, with its glow
img = Image.new("RGB", (640, 480), BG)
mark = mark.resize((310, 295), Image.LANCZOS)
# cut the X out of its own background (the bright pixels) and put it on a fresh soft glow
import numpy as np
arr = np.asarray(mark).astype(float)
alpha = np.clip((arr.max(axis=2) - 130) / 50, 0, 1)
cut = Image.fromarray((alpha * 255).astype("uint8")).filter(ImageFilter.GaussianBlur(0.6))
yy, xx = np.mgrid[0:480, 0:640]
r = np.sqrt(((xx - 320) / 230.0) ** 2 + ((yy - 188) / 190.0) ** 2)
g = np.clip(1 - r, 0, 1) ** 2
glow = np.stack([BG[0] + g * 0, BG[1] + g * 45, BG[2] + g * 150], axis=2)
img = Image.fromarray(np.clip(glow, 0, 255).astype("uint8"))
img.paste(mark, (165, 40), cut)
d = ImageDraw.Draw(img)
font = None
for pat in ("/usr/share/fonts/**/Inter*Bold*.ttf", "/usr/share/fonts/**/Inter*.ttf", "/usr/share/fonts/**/DejaVuSans-Bold.ttf", "/usr/share/fonts/**/LiberationSans-Bold.ttf"):
    f = glob.glob(pat, recursive=True)
    if f:
        font = ImageFont.truetype(f[0], 44); break
font = font or ImageFont.load_default()
t = "XlinOS"
w = d.textlength(t, font=font)
d.text(((640 - w) / 2, 335), t, fill=(255, 255, 255), font=font)
sub = ImageFont.truetype(font.path, 16) if hasattr(font, "path") else font
s = "Clean. Fast. Smooth."
d.text(((640 - d.textlength(s, font=sub)) / 2, 392), s, fill=(120, 150, 210), font=sub)
img.save(sys.argv[1])
