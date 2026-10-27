"""
Prepare a real (photographic) profile picture for ASCII conversion on a DARK
terminal card:
  1. remove the background (rembg) so the subject is isolated
  2. CLAHE local contrast so the face reads even under moody lighting
  3. invert: make_ascii_svg.py maps dark -> dense glyphs, and on a dark card
     dense glyphs read as bright, so bright features (face, highlights) must
     come out dark here. The subject is squeezed into [0, CEIL]; CEIL sits just past
     WHITE_FLOOR so the black suit fades out instead of filling with noise.
  4. composite onto white (white -> blank space) and crop a head-and-shoulders
     square centered on the top of the head, so the face is big enough to read

Output: source-prepped.png (grayscale), consumed by make_ascii_svg.py.

    python scripts/prep_photo.py <input.jpg> [output.png]
"""
import os
import sys

import cv2
import numpy as np
from PIL import Image
from rembg import remove

HERE = os.path.dirname(os.path.abspath(__file__))
INP = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "source-photo.jpg")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "source-prepped.png")

CEIL = 0.88           # darkest subject pixel -> this (past WHITE_FLOOR: black suit fades out)
CLAHE_CLIP = 5.0
CLAHE_TILE = 6       # small tiles even out hard side lighting across the face
HIGHLIGHT_GAMMA = 1.15 # >1 spreads the bright face so features survive
ALPHA_MIN = 128      # drop soft rembg edges (stray glyphs around hair/shoulders)
CROP = 0.72           # crop side as a fraction of the subject width (head + shoulders)

# 1. cut out the subject
cut = remove(Image.open(INP).convert("RGBA"))
rgb = np.array(cut.convert("RGB"))
alpha = np.array(cut.split()[-1])                 # 0 = background
alpha[alpha <= ALPHA_MIN] = 0
gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)

# 2. local contrast
gray = cv2.createCLAHE(clipLimit=CLAHE_CLIP, tileGridSize=(CLAHE_TILE, CLAHE_TILE)).apply(gray)
gray = cv2.bilateralFilter(gray, 7, 30, 7)

# tone stretch over the subject only
lo, hi = np.percentile(gray[alpha > 128], [3, 99])
tone = np.clip((gray.astype(np.float32) - lo) / (hi - lo), 0, 1) ** HIGHLIGHT_GAMMA

# 3. invert into [0, CEIL]: bright -> 0 (dense), dark -> CEIL (sparse)
inv = (1.0 - tone) * CEIL

# 4. paste onto white, square crop
mask = cv2.GaussianBlur(alpha.astype(np.float32) / 255.0, (0, 0), 1.0)
out = (inv * mask + 1.0 * (1.0 - mask)) * 255.0

ys, xs = np.where(alpha > 20)
side = int((xs.max() - xs.min()) * CROP)
top = ys.min()
head_xs = xs[ys < top + 40]                       # top of the head centers the crop
cx = int(np.median(head_xs))
canvas = np.full((side, side), 255, np.uint8)
x0, y0 = cx - side // 2, top - 12
sx0, sy0 = max(x0, 0), max(y0, 0)
sx1, sy1 = min(x0 + side, out.shape[1]), min(y0 + side, out.shape[0])
canvas[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0] = out[sy0:sy1, sx0:sx1].astype(np.uint8)

Image.fromarray(canvas, mode="L").save(OUT)
print("wrote", OUT, canvas.shape)
