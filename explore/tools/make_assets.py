#!/usr/bin/env python3
"""Generate the Pet Explore prototype's own art.

Everything the pets themselves wear comes from the main game's sheets in
../art/ - this only draws what the world needs that the game has never had:
ground tiles and props. The raid boss is the game's own Sir Uwaaarghhhh.

Drawn at native resolution and upscaled by a whole number with
nearest-neighbour, the same rule ART-SPEC.md sets for pets, so the output is
hard-edged and can be reduced back losslessly. Deterministic: run it twice and
the PNGs come out byte-identical, so a diff in art/ always means a real change.

    python3 explore/tools/make_assets.py

Needs Pillow only.
"""
import math
import os
import random

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, "..", "art"))
os.makedirs(OUT, exist_ok=True)

OUTLINE = (26, 16, 40, 255)
CLEAR = (0, 0, 0, 0)


def hexc(h, a=255):
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


# --------------------------------------------------------------------------
# drawing helpers
# --------------------------------------------------------------------------

def layer(w, h):
    return Image.new("RGBA", (w, h), CLEAR)


def put(img, x, y, c):
    x, y = int(x), int(y)
    if 0 <= x < img.width and 0 <= y < img.height:
        img.putpixel((x, y), c)


def shade_index(nx, ny, n):
    """Light from the upper left, the same side every pet sheet is lit from."""
    nz = math.sqrt(max(0.0, 1 - nx * nx - ny * ny))
    v = -0.5 * nx - 0.62 * ny + 0.62 * nz
    v = (v + 0.55) / 1.45
    return max(0, min(n - 1, int(v * n)))


def ellipse(img, cx, cy, rx, ry, ramp, flat=False):
    for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
        for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
            nx = (x + 0.5 - cx) / rx
            ny = (y + 0.5 - cy) / ry
            if nx * nx + ny * ny <= 1:
                if flat or isinstance(ramp, tuple):
                    put(img, x, y, ramp if isinstance(ramp, tuple) else ramp[0])
                else:
                    put(img, x, y, ramp[shade_index(nx, ny, len(ramp))])


def rect(img, x0, y0, x1, y1, c):
    for y in range(int(y0), int(y1)):
        for x in range(int(x0), int(x1)):
            put(img, x, y, c)


def polygon(img, pts, colour_at):
    """Scanline fill; colour_at(x, y) picks each pixel's colour."""
    ys = [p[1] for p in pts]
    for y in range(int(min(ys)), int(max(ys)) + 1):
        yc = y + 0.5
        xs = []
        for i in range(len(pts)):
            (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % len(pts)]
            if (y0 <= yc < y1) or (y1 <= yc < y0):
                xs.append(x0 + (yc - y0) * (x1 - x0) / (y1 - y0))
        xs.sort()
        for a, b in zip(xs[0::2], xs[1::2]):
            for x in range(int(round(a)), int(round(b))):
                put(img, x, y, colour_at(x, y))


def line(img, x0, y0, x1, y1, c):
    n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
    for i in range(n + 1):
        t = i / max(1, n)
        put(img, round(x0 + (x1 - x0) * t), round(y0 + (y1 - y0) * t), c)


def outlined(img, c=OUTLINE):
    """Give a part the chunky dark outline the pet sheets all have."""
    out = img.copy()
    w, h = img.size
    px = img.load()
    po = out.load()
    for y in range(h):
        for x in range(w):
            if px[x, y][3] == 0:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    xx, yy = x + dx, y + dy
                    if 0 <= xx < w and 0 <= yy < h and px[xx, yy][3] > 0:
                        po[x, y] = c
                        break
    return out


def stack(size, *parts):
    base = layer(*size)
    for p in parts:
        base.alpha_composite(p)
    return base


def upscale(img, k):
    return img.resize((img.width * k, img.height * k), Image.NEAREST)


def quantise_check(img, name):
    n = len(img.getcolors(1 << 16) or [])
    print(f"  {name:28s} {img.size[0]}x{img.size[1]}  {n} colours")


# --------------------------------------------------------------------------
# palette
# --------------------------------------------------------------------------

GRASS = [hexc("#2f5a3a"), hexc("#3c6e43"), hexc("#4a8250"), hexc("#5d995a")]
PATH = [hexc("#7a5f45"), hexc("#8d6f50"), hexc("#a3845f"), hexc("#b89870")]
WATER = [hexc("#1d3a66"), hexc("#25508a"), hexc("#3168a6"), hexc("#7fb4e0")]
SAND = [hexc("#b7a074"), hexc("#c9b386"), hexc("#d9c697")]
ASH = [hexc("#3a2a2c"), hexc("#4a3434"), hexc("#5a3f3a"), hexc("#6b4a40")]
LAVA = [hexc("#ff6b35"), hexc("#ffd23f"), hexc("#c23a1c")]
MOSS = [hexc("#2c4f33"), hexc("#355f37"), hexc("#43723f"), hexc("#6f9a4c")]
CLOUD = [hexc("#4a5674"), hexc("#5b6888"), hexc("#6f7d9e"), hexc("#93a3c4")]
# the hill the orc came down off: packed earth-grey flagstone, torch-lit runes
STONE = [hexc("#4a4238"), hexc("#5a5144"), hexc("#6b6152"), hexc("#857a66")]
RUNE = hexc("#ffb347")
FLOWERS = [hexc("#ffd23f"), hexc("#ff8fb1"), hexc("#ffffff"), hexc("#9fd8ff")]


# --------------------------------------------------------------------------
# tiles: 16x16 native, x2 -> 32px
# --------------------------------------------------------------------------

def noise_tile(rng, ramp, weights, specks=()):
    t = layer(16, 16)
    for y in range(16):
        for x in range(16):
            t.putpixel((x, y), rng.choices(ramp, weights)[0])
    for colour, count in specks:
        for _ in range(count):
            put(t, rng.randrange(16), rng.randrange(16), colour)
    return t


def grass_blades(rng, t, n, c):
    for _ in range(n):
        x, y = rng.randrange(1, 15), rng.randrange(2, 16)
        put(t, x, y, c)
        put(t, x, y - 1, c)


def tiles():
    rng = random.Random(7)
    out = []
    # 0-1 grass
    for i in range(2):
        t = noise_tile(rng, GRASS[1:3], [5, 3])
        grass_blades(rng, t, 6, GRASS[3])
        grass_blades(rng, t, 4, GRASS[0])
        out.append(t)
    # 2 flowers
    t = noise_tile(rng, GRASS[1:3], [5, 3])
    grass_blades(rng, t, 4, GRASS[3])
    for _ in range(4):
        x, y = rng.randrange(2, 14), rng.randrange(2, 14)
        c = rng.choice(FLOWERS)
        for dx, dy in ((0, -1), (-1, 0), (1, 0), (0, 1)):
            put(t, x + dx, y + dy, c)
        put(t, x, y, FLOWERS[0] if c != FLOWERS[0] else hexc("#ff6b35"))
    out.append(t)
    # 3 tall grass
    t = noise_tile(rng, GRASS[0:2], [3, 5])
    for x in range(0, 16, 3):
        h = rng.randrange(5, 9)
        base = rng.randrange(10, 16)
        for k in range(h):
            put(t, x + (k // 4), base - k, GRASS[3] if k > h - 3 else GRASS[2])
    out.append(t)
    # 4 path
    t = noise_tile(rng, PATH[0:3], [2, 5, 3], [(PATH[3], 6), (hexc("#5e4836"), 5)])
    out.append(t)
    # 5-6 water, two frames
    for f in range(2):
        t = noise_tile(rng, WATER[1:3], [6, 2])
        for k in range(3):
            y = (3 + k * 5 + f * 2) % 16
            x = (2 + k * 6 + f * 3) % 12
            for dx in range(4):
                put(t, x + dx, y, WATER[3] if dx in (1, 2) else WATER[2])
        out.append(t)
    # 7 sand
    out.append(noise_tile(rng, SAND, [3, 5, 2]))
    # 8 ash ground
    out.append(noise_tile(rng, ASH[0:3], [2, 5, 3], [(ASH[3], 6)]))
    # 9 ash with a lava crack
    t = noise_tile(rng, ASH[0:3], [2, 5, 3])
    x, y = 2, rng.randrange(4, 12)
    while x < 15:
        put(t, x, y, LAVA[0])
        put(t, x, y + 1, LAVA[2])
        if rng.random() < .3:
            put(t, x, y, LAVA[1])
        x += 1
        y = max(2, min(13, y + rng.choice((-1, 0, 0, 1))))
    out.append(t)
    # 10-11 moss
    t = noise_tile(rng, MOSS[0:3], [2, 5, 3])
    grass_blades(rng, t, 3, MOSS[3])
    out.append(t)
    t = noise_tile(rng, MOSS[0:3], [2, 5, 3])
    for _ in range(3):
        x, y = rng.randrange(2, 14), rng.randrange(2, 14)
        for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1)):
            put(t, x + dx, y + dy, MOSS[3])
        put(t, x, y, hexc("#a8d36a"))
    out.append(t)
    # 12-13 cloudstone (Nimbus heights)
    t = noise_tile(rng, CLOUD[1:3], [5, 3], [(CLOUD[3], 5), (CLOUD[0], 5)])
    out.append(t)
    t = noise_tile(rng, CLOUD[1:3], [5, 3])
    for x in range(3, 13):
        put(t, x, 8 + (x % 3 == 0), CLOUD[0])
    put(t, 7, 7, hexc("#5fe6ff"))
    put(t, 8, 7, hexc("#5fe6ff"))
    out.append(t)
    # 14-15 arena flagstones
    t = noise_tile(rng, STONE[1:3], [5, 3])
    rect(t, 0, 0, 16, 1, STONE[0])
    rect(t, 0, 0, 1, 16, STONE[0])
    rect(t, 0, 8, 16, 9, STONE[0])
    rect(t, 8, 1, 9, 8, STONE[0])
    rect(t, 4, 9, 5, 16, STONE[0])
    for x in range(1, 16):
        put(t, x, 1, STONE[3])
        put(t, x, 9, STONE[3])
    out.append(t)
    t = out[-1].copy()
    for a in range(0, 360, 20):
        r = 5
        put(t, 8 + round(r * math.cos(math.radians(a))), 8 + round(r * math.sin(math.radians(a))), RUNE)
    put(t, 8, 8, RUNE)
    put(t, 7, 8, RUNE)
    put(t, 8, 7, RUNE)
    out.append(t)

    sheet = layer(16 * len(out), 16)
    for i, t in enumerate(out):
        sheet.alpha_composite(t, (i * 16, 0))
    return upscale(sheet, 2)


# --------------------------------------------------------------------------
# props: 32x48 native cells, x2 -> 64x96, anchored bottom-centre
# --------------------------------------------------------------------------

LEAF = [hexc("#24502e"), hexc("#2f6a37"), hexc("#3f8441"), hexc("#5ea24e"), hexc("#86c35c")]
BARK = [hexc("#4a2f22"), hexc("#5f3d2a"), hexc("#7a5136")]
BAMBOO = [hexc("#4f7a2c"), hexc("#6c9c35"), hexc("#94c24a"), hexc("#c3e07a")]
BASALT = [hexc("#231b22"), hexc("#30242b"), hexc("#3f2f35"), hexc("#55403f")]
CRYSTAL = [hexc("#1b6f9a"), hexc("#25a0cf"), hexc("#5fe6ff"), hexc("#d4fbff")]
ROCK = [hexc("#4c4a58"), hexc("#615e6f"), hexc("#7a7789"), hexc("#9a97a8")]


def prop_tree():
    trunk = layer(32, 48)
    rect(trunk, 13, 32, 19, 46, BARK[1])
    rect(trunk, 13, 32, 15, 46, BARK[2])
    rect(trunk, 18, 32, 19, 46, BARK[0])
    rect(trunk, 11, 44, 21, 46, BARK[1])
    canopy = layer(32, 48)
    for cx, cy, r in ((16, 20, 12), (8, 27, 7), (24, 27, 7), (11, 14, 7), (21, 13, 7), (16, 29, 8)):
        ellipse(canopy, cx, cy, r, r * .9, LEAF[0:4])
    rng = random.Random(3)
    for _ in range(18):
        x, y = rng.randrange(5, 27), rng.randrange(6, 30)
        if canopy.getpixel((x, y))[3] and canopy.getpixel((x, y)) in (LEAF[2], LEAF[3]):
            put(canopy, x, y, LEAF[4])
    return stack((32, 48), outlined(trunk), outlined(canopy))


def prop_bamboo():
    parts = []
    rng = random.Random(11)
    for x, top in ((8, 6), (14, 2), (20, 9), (25, 14)):
        s = layer(32, 48)
        rect(s, x, top, x + 3, 46, BAMBOO[1])
        rect(s, x, top, x + 1, 46, BAMBOO[2])
        for y in range(top + 5, 46, 7):
            rect(s, x, y, x + 3, y + 1, BAMBOO[0])
            put(s, x - 1, y, BAMBOO[0])
            put(s, x + 3, y, BAMBOO[0])
        for _ in range(2):
            y = rng.randrange(top + 2, 30)
            d = rng.choice((-1, 1))
            for k in range(6):
                put(s, x + 1 + d * (2 + k), y - k // 2, BAMBOO[3] if k < 3 else BAMBOO[2])
                put(s, x + 1 + d * (2 + k), y - k // 2 + 1, BAMBOO[1])
        parts.append(outlined(s))
    return stack((32, 48), *parts)


def prop_ember_spire():
    s = layer(32, 48)
    pts = [(5, 46), (8, 24), (12, 30), (15, 6), (19, 22), (23, 16), (27, 46)]
    polygon(s, pts, lambda x, y: BASALT[1] if x < 14 else BASALT[2] if x < 20 else BASALT[0])
    s = outlined(s)
    x, y = 15, 12
    while y < 44:
        put(s, x, y, LAVA[0])
        if y % 4 == 0:
            put(s, x, y, LAVA[1])
        y += 1
        x += (1 if (y // 5) % 2 else -1)
    for (x, y) in ((10, 38), (11, 39), (22, 34), (21, 35), (22, 36)):
        put(s, x, y, LAVA[0])
    return s


def prop_crystal():
    parts = []
    for (bx, h, w, lean) in ((10, 22, 6, -3), (21, 18, 5, 3), (16, 34, 8, 0)):
        s = layer(32, 48)
        top = (bx + lean, 46 - h)
        pts = [(bx - w // 2, 46), (bx - w // 2 + lean // 2, 46 - h + 6), top,
               (bx + w // 2 + lean // 2, 46 - h + 6), (bx + w // 2, 46)]
        polygon(s, pts, lambda x, y, bx=bx: CRYSTAL[2] if x < bx else CRYSTAL[1])
        line(s, bx - 1, 44, top[0] - 1, top[1] + 4, CRYSTAL[3])
        parts.append(outlined(s))
    return stack((32, 48), *parts)


def prop_boulder():
    s = layer(32, 48)
    ellipse(s, 16, 38, 12, 9, ROCK)
    ellipse(s, 9, 41, 6, 5, ROCK)
    s = outlined(s)
    put(s, 13, 33, ROCK[3])
    put(s, 14, 32, ROCK[3])
    line(s, 18, 36, 22, 40, ROCK[0])
    return s


def prop_bush():
    s = layer(32, 48)
    for cx, cy, r in ((10, 39, 7), (22, 39, 7), (16, 34, 8)):
        ellipse(s, cx, cy, r, r * .85, LEAF[0:4])
    s = outlined(s)
    for x, y in ((11, 36), (19, 33), (22, 40), (14, 41)):
        put(s, x, y, hexc("#e2475a"))
        put(s, x + 1, y, hexc("#ff8fb1"))
    return s


def prop_standing_stone():
    s = layer(32, 48)
    pts = [(8, 46), (9, 10), (13, 5), (20, 6), (24, 12), (25, 46)]
    polygon(s, pts, lambda x, y: STONE[2] if x < 13 else STONE[1] if x < 21 else STONE[0])
    s = outlined(s)
    for k in range(5):
        put(s, 16, 16 + k * 4, RUNE)
        put(s, 15 + (k % 2) * 2, 18 + k * 4, RUNE)
    return s


def prop_campfire(f):
    s = layer(32, 48)
    logs = layer(32, 48)
    rect(logs, 7, 41, 25, 44, BARK[1])
    rect(logs, 9, 39, 23, 41, BARK[2])
    logs = outlined(logs)
    flame = layer(32, 48)
    sway = (-1, 1)[f]
    ellipse(flame, 16, 36, 6, 6, LAVA[0])
    polygon(flame, [(10, 37), (16 + sway * 2, 20), (22, 37)], lambda x, y: LAVA[0])
    ellipse(flame, 16, 37, 3, 3, LAVA[1])
    polygon(flame, [(13, 37), (16 - sway, 28), (19, 37)], lambda x, y: LAVA[1])
    for x, y in ((12 + f * 6, 22), (19 - f * 5, 18)):
        put(flame, x, y, LAVA[1])
    return stack((32, 48), logs, outlined(flame, hexc("#7a1f10")))


def prop_sign():
    s = layer(32, 48)
    rect(s, 15, 30, 17, 46, BARK[1])
    rect(s, 7, 24, 25, 33, BARK[2])
    s = outlined(s)
    for x in range(10, 22, 2):
        put(s, x, 28, BARK[0])
    return s


def prop_acorn():
    """The Sparky's acorn, so a pickup in Nimbus country is one it would know."""
    s = layer(32, 48)
    nut = layer(32, 48)
    ellipse(nut, 16, 39, 6, 6, [hexc("#8a2a10"), hexc("#c23a1c"), hexc("#ff6b35"), hexc("#ff9a5c")])
    cap = layer(32, 48)
    ellipse(cap, 16, 34, 7, 4, [hexc("#5f2a14"), hexc("#7a3a1c"), hexc("#a3532a")])
    rect(cap, 15, 28, 17, 31, BARK[1])
    return stack((32, 48), s, outlined(nut), outlined(cap))


def prop_berry():
    s = layer(32, 48)
    for cx, cy in ((13, 40), (19, 40), (16, 35)):
        ellipse(s, cx, cy, 4, 4, [hexc("#7a1c3a"), hexc("#b42c55"), hexc("#e2475a"), hexc("#ff8fb1")])
    leaf = layer(32, 48)
    polygon(leaf, [(16, 31), (22, 27), (19, 32)], lambda x, y: LEAF[3])
    return stack((32, 48), outlined(s), outlined(leaf))


def prop_mushroom():
    s = layer(32, 48)
    rect(s, 14, 36, 19, 46, hexc("#efe2c8"))
    cap = layer(32, 48)
    ellipse(cap, 16, 36, 9, 6, [hexc("#5a2a6e"), hexc("#7a3a94"), hexc("#a35ac0")])
    rect(cap, 6, 36, 27, 43, CLEAR)
    cap = outlined(cap)
    for x, y in ((12, 32), (18, 31), (21, 34)):
        put(cap, x, y, hexc("#e8d6ff"))
    return stack((32, 48), outlined(s), cap)


PROPS = [
    ("tree", prop_tree), ("bamboo", prop_bamboo), ("spire", prop_ember_spire),
    ("crystal", prop_crystal), ("boulder", prop_boulder), ("bush", prop_bush),
    ("stone", prop_standing_stone), ("fire0", lambda: prop_campfire(0)),
    ("fire1", lambda: prop_campfire(1)), ("sign", prop_sign),
    ("acorn", prop_acorn), ("berry", prop_berry), ("mushroom", prop_mushroom),
]


def props():
    sheet = layer(32 * len(PROPS), 48)
    for i, (_, fn) in enumerate(PROPS):
        sheet.alpha_composite(fn(), (i * 32, 0))
    return upscale(sheet, 2)


def main():
    print("writing", OUT)
    for name, img in (("tiles.png", tiles()), ("props.png", props())):
        img.save(os.path.join(OUT, name), optimize=True)
        quantise_check(img, name)


if __name__ == "__main__":
    main()
