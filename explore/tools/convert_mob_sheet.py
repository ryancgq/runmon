#!/usr/bin/env python3
"""Turn a generated 4x4 mob sheet into the strip Explore plays.

    python3 explore/tools/convert_mob_sheet.py beetle path/to/sheet.png

The sheet is what the prompts in ../art/PROMPTS.md ask for: sixteen frames
in a 4x4 grid on a transparent background. Out comes
explore/art/mob-<name>.png, one row of sixteen frames of FRAME_W x FRAME_H
with the creature's feet on BASE in every frame, and the numbers the page
needs printed at the end.

What it fixes, because image models don't hold to the prompt on these:

- Alpha. The sheets arrive with their "opaque" pixels at about 252, and a
  haze of near-invisible pixels (alpha 1-7) over the whole background -
  what is left of the matte the model cut the creature out of. The haze is
  dropped and the body made fully opaque; the soft edge of a glow or a dust
  cloud in between is kept.
- Bleed. The grid's cells aren't kept to: a cap swung forward or a cloud
  of dust crosses into the next cell, and a cut on the grid lines leaves a
  frame clipped flat and slivers of it in its neighbour. So nothing is cut
  on the lines: every separate shape on the sheet goes to the frame its
  middle is in.
- Drift. Each cell puts the creature somewhere slightly different. Every
  frame is moved so the bottom of its body sits on BASE and its body is
  centred, so it doesn't hop or slide when the strip plays. "Its body" is
  the largest connected shape in the cell; a spat fireball, a zap or loose
  sparks are separate shapes and travel with it.

Needs Pillow and numpy.
"""
import os
import sys
from collections import deque

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, "..", "art"))

FRAME_W, FRAME_H = 480, 360   # every mob alike, so the page sizes them the same way
SHIP = .75                    # saved at 360x270: still more than a phone draws, and a
                              # quarter of the bytes. Then 256 colours: 1.4 MB a strip at
                              # full colour, against ~400 KB for the game's biggest sheets
BASE = 330                    # the row the lowest body pixel lands on
HAZE, SOLID = 48, 200         # alpha below HAZE is matte; above SOLID is body
MIN_ROW = 10                  # px across for a row to count as the body's bottom
SPECK = 6                     # shapes smaller than this are matte, not sparks


def clean(a):
    al = a[..., 3].astype(np.int32)
    al[al < HAZE] = 0
    al[al >= SOLID] = 255
    a = a.copy()
    a[..., 3] = al.astype(np.uint8)
    a[al == 0, :3] = 0
    return a


def components(mask):
    """Every 8-connected shape in a mask, as lists of (y, x)."""
    h, w = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
    out = []
    ys, xs = np.nonzero(mask)
    for y0, x0 in zip(ys, xs):
        if seen[y0, x0]:
            continue
        q = deque([(y0, x0)])
        seen[y0, x0] = True
        pts = []
        while q:
            y, x = q.popleft()
            pts.append((y, x))
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    yy, xx = y + dy, x + dx
                    if 0 <= yy < h and 0 <= xx < w and mask[yy, xx] and not seen[yy, xx]:
                        seen[yy, xx] = True
                        q.append((yy, xx))
        out.append(pts)
    return out


def largest_component(mask):
    """The biggest shape in a frame, as a boolean mask."""
    parts = components(mask)
    out = np.zeros_like(mask, dtype=bool)
    if parts:
        py, px = zip(*max(parts, key=len))
        out[list(py), list(px)] = True
    return out


def anchor(cell):
    """Where a frame's body stands: the bottom of it, and its middle.

    The bottom is the lowest row that is really body - at least MIN_ROW
    pixels across - so a stray mote under the feet doesn't count. (A share
    of its widest row was tried first: a zap joined to the wisp's body
    widened its widest row and lifted where its tail was taken to end.) The
    middle is the centre of its solid pixels, which a trail of sparks
    behind it barely moves."""
    body = largest_component(cell[..., 3] == 255)
    rows = body.sum(1)
    if not rows.any():
        return None
    real = np.nonzero(rows >= MIN_ROW)[0]
    bottom = real.max()
    ys, xs = np.nonzero(body)
    return bottom, xs.mean()


def convert(name, path):
    src = clean(np.array(Image.open(path).convert("RGBA")))
    h, w = src.shape[:2]
    cw, ch = w / 4, h / 4
    # each shape to the frame its middle falls in
    owner = np.full((h, w), -1, dtype=np.int16)
    for pts in components(src[..., 3] > 0):
        if len(pts) < SPECK:
            continue
        py, px = np.array(pts).T
        c = min(3, int(px.mean() // cw))
        r = min(3, int(py.mean() // ch))
        owner[py, px] = r * 4 + c
    strip = Image.new("RGBA", (FRAME_W * 16, FRAME_H), (0, 0, 0, 0))
    lows, spans = [], []
    for i in range(16):
        r, c = divmod(i, 4)
        # the cell, widened by half a cell all round for whatever crossed its lines
        x0, y0 = max(0, int((c - .5) * cw)), max(0, int((r - .5) * ch))
        x1, y1 = min(w, int((c + 1.5) * cw)), min(h, int((r + 1.5) * ch))
        cell = src[y0:y1, x0:x1].copy()
        cell[owner[y0:y1, x0:x1] != i] = 0
        a = anchor(cell)
        if a is None:
            raise SystemExit(f"{name}: frame {i + 1} is empty")
        bottom, mid = a
        ox, oy = int(round(FRAME_W / 2 - mid)), BASE - bottom
        img = Image.fromarray(cell)
        strip.alpha_composite(_place(img, ox, oy), (i * FRAME_W, 0))
        al = cell[..., 3] > 0
        ys, xs = np.nonzero(al)
        spans.append((xs.min() + ox, xs.max() + ox, ys.min() + oy, ys.max() + oy))
        body = largest_component(cell[..., 3] == 255)
        bys, bxs = np.nonzero(body)
        lows.append((bxs.max() - bxs.min(), bottom - bys.min()))
    path_out = os.path.join(OUT, f"mob-{name}.png")
    strip = strip.resize((int(FRAME_W * SHIP) * 16, int(FRAME_H * SHIP)), Image.LANCZOS)
    strip.quantize(256, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.NONE).save(path_out, optimize=True)
    clip = [s for s in spans if s[0] < 0 or s[1] >= FRAME_W or s[2] < 0 or s[3] >= FRAME_H]
    idle_w = np.mean([l[0] for l in lows[:4]])
    print(f"{name}: wrote {path_out}, {os.path.getsize(path_out) // 1024} KB")
    print(f"  idle body {idle_w:.0f}px wide of {FRAME_W} ({idle_w / FRAME_W:.2f}), foot {BASE / FRAME_H:.3f}, aspect {FRAME_W / FRAME_H:.3f}")
    if clip:
        print(f"  {len(clip)} frame(s) reach past the frame and are cut: {clip}")


def _place(img, ox, oy):
    out = Image.new("RGBA", (FRAME_W, FRAME_H), (0, 0, 0, 0))
    out.paste(img, (ox, oy), img)
    return out


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    convert(sys.argv[1], sys.argv[2])
