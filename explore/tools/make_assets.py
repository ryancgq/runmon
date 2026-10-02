#!/usr/bin/env python3
"""Generate the Pet Explore prototype's own art.

Everything the pets themselves wear comes from the main game's sheets in
../art/ - this only draws what the world needs that the game has never had:
ground tiles, props, the raid boss and its minion.

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
STONE = [hexc("#4b4560"), hexc("#5b5472"), hexc("#6c6585"), hexc("#857da0")]
RUNE = hexc("#c69cff")
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


# --------------------------------------------------------------------------
# Lord Lull, the raid boss: 128x96 native, x3 -> 384x288 (ART-SPEC's canvas)
# --------------------------------------------------------------------------
# The game's whole villain is the rest day - the pet sulks, then sleeps, if you
# stop running - so the boss is that, given a body: a vast plush sleep-spirit
# in a nightcap that wants everyone to lie down. It summons sheep. Of course.

LULL = [hexc("#3d2b63"), hexc("#55408a"), hexc("#6d55a8"), hexc("#8a72c4"), hexc("#a993dc")]
LULL_RAGE = [hexc("#4a1f4f"), hexc("#6a2a70"), hexc("#8a3a8f"), hexc("#a956a8"), hexc("#c77ac4")]
BELLY = [hexc("#b9a6e6"), hexc("#cdbdf2"), hexc("#e0d5fa")]
CAP_A = hexc("#2b3f7a")
CAP_B = hexc("#e9e2ff")
POM = [hexc("#d8cfee"), hexc("#f2edff"), hexc("#ffffff")]
CHEEK = hexc("#e48ab8")
MOUTH = hexc("#2a1236")
TONGUE = hexc("#e2668f")
EYE_W = hexc("#f6f3ff")
ZED = hexc("#c9b8ff")
GOLD = hexc("#ffd23f")
BASE = 88  # native baseline: 88 * 3 = 264, ART-SPEC's ground line


def zee(img, x, y, s):
    for i in range(s):
        put(img, x + i, y, ZED)
        put(img, x + i, y + s - 1, ZED)
        put(img, x + s - 1 - i, y + i, ZED)


def lord_lull(sx=1.0, sy=1.0, eyes="drowsy", mouth="small", arms="rest",
              zs=0, rage=False, dust=False, shift=0):
    W, H = 128, 96
    ramp = LULL_RAGE if rage else LULL
    rx, ry = 46 * sx, 32 * sy
    cx, cy = 64 + shift, BASE - ry
    top = cy - ry

    def fy(v):
        """Map a feature's height on the resting body onto this squash."""
        return BASE - (BASE - v) * sy

    feet = layer(W, H)
    for fx in (cx - 22 * sx, cx + 22 * sx):
        ellipse(feet, fx, BASE - 2, 9 * sx, 4, ramp[0:3])

    ears = layer(W, H)
    for ex in (cx - 30 * sx, cx + 30 * sx):
        ellipse(ears, ex, top + 8 * sy, 8, 8, ramp[1:4])
        ellipse(ears, ex, top + 9 * sy, 4, 4, (CHEEK[0], CHEEK[1], CHEEK[2], 255))

    body = layer(W, H)
    ellipse(body, cx, cy, rx, ry, ramp)
    belly = layer(W, H)
    ellipse(belly, cx, cy + 12 * sy, rx * .55, ry * .5, BELLY)
    body.alpha_composite(belly)

    arm_l, arm_r = layer(W, H), layer(W, H)
    if arms == "up":
        ellipse(arm_l, cx - rx + 4, fy(36), 7, 9, ramp[1:4])
        ellipse(arm_r, cx + rx - 4, fy(36), 7, 9, ramp[1:4])
    elif arms == "out":
        ellipse(arm_l, cx - rx - 2, BASE - 6, 10, 6, ramp[1:4])
        ellipse(arm_r, cx + rx + 2, BASE - 6, 10, 6, ramp[1:4])
    else:
        ellipse(arm_l, cx - rx + 6, fy(70), 7, 8, ramp[1:4])
        ellipse(arm_r, cx + rx - 6, fy(70), 7, 8, ramp[1:4])

    # the nightcap, slumped off to the right with a pompom on the end
    cap = layer(W, H)
    t = top + 4 * sy
    pts = [(cx - 26, t + 8), (cx - 14, t - 10), (cx + 4, t - 20), (cx + 26, t - 18),
           (cx + 40, t - 8), (cx + 44, t + 2), (cx + 36, t - 2), (cx + 22, t - 8),
           (cx + 26, t + 8)]
    if rage:  # it stands up on end when Lull is properly awake
        pts = [(cx - 24, t + 8), (cx - 16, t - 12), (cx - 4, t - 28), (cx + 6, t - 34),
               (cx + 12, t - 26), (cx + 22, t - 10), (cx + 26, t + 8)]
    polygon(cap, pts, lambda x, y: CAP_A if int((x + y) / 5) % 2 else CAP_B)
    rect(cap, cx - 28, t + 4, cx + 29, t + 10, CAP_B)
    pom = layer(W, H)
    px_, py_ = (cx + 42, t + 4) if not rage else (cx + 6, t - 35)
    ellipse(pom, px_, py_, 5, 5, POM)

    face = layer(W, H)
    ey = fy(52)
    for ex in (cx - 16 * sx, cx + 16 * sx):
        if eyes == "drowsy":
            ellipse(face, ex, ey, 6, 4, EYE_W)
            ellipse(face, ex + 1, ey + 1, 2.5, 2.5, MOUTH)
            rect(face, ex - 7, ey - 5, ex + 7, ey, ramp[2])
            line(face, ex - 6, ey, ex + 6, ey, OUTLINE)
            line(face, ex - 4, ey + 6, ex + 4, ey + 6, ramp[1])
        elif eyes == "shut":
            for k in range(-5, 6):
                put(face, ex + k, ey + 1 + (abs(k) < 4), OUTLINE)
        elif eyes == "angry":
            ellipse(face, ex, ey, 6, 5, EYE_W)
            ellipse(face, ex, ey + 1, 3, 3, hexc("#ff3b5c") if rage else MOUTH)
            put(face, ex, ey, hexc("#ffffff"))
            d = 1 if ex < cx else -1
            line(face, ex - 7, ey - 6 - 2 * d, ex + 7, ey - 6 + 2 * d, OUTLINE)
            line(face, ex - 7, ey - 7 - 2 * d, ex + 7, ey - 7 + 2 * d, OUTLINE)
        elif eyes == "hurt":
            line(face, ex - 4, ey - 3, ex + 4, ey + 3, OUTLINE)
            line(face, ex - 4, ey + 3, ex + 4, ey - 3, OUTLINE)
        elif eyes == "out":
            line(face, ex - 4, ey - 3, ex + 4, ey + 3, OUTLINE)
            line(face, ex - 4, ey + 3, ex + 4, ey - 3, OUTLINE)
            line(face, ex - 3, ey - 3, ex + 5, ey + 3, OUTLINE)
        ellipse(face, ex + (-6 if ex < cx else 6) * sx, ey + 9, 4, 2.5, CHEEK)
    my = fy(66)
    if mouth == "small":
        for k in range(-3, 4):
            put(face, cx + k, my + (1 if abs(k) == 1 else 0), OUTLINE)
    elif mouth == "yawn":
        ellipse(face, cx, my + 2, 8, 9, MOUTH)
        ellipse(face, cx, my + 7, 5, 3, TONGUE)
    elif mouth == "gasp":
        ellipse(face, cx, my + 1, 4, 4, MOUTH)
    elif mouth == "snarl":
        rect(face, cx - 6, my - 1, cx + 7, my + 4, MOUTH)
        for k in range(-5, 7, 3):
            put(face, cx + k, my - 1, EYE_W)
            put(face, cx + k, my + 3, EYE_W)

    fx = layer(W, H)
    for i in range(zs):
        zee(fx, 100 + i * 7, 30 - i * 10, 4 + i)
    if dust:
        rng = random.Random(5)
        for i in range(26):
            a = rng.uniform(math.pi, 2 * math.pi)
            r = rng.uniform(40, 62)
            put(fx, 64 + r * math.cos(a) * 1.15, BASE - 2 + r * math.sin(a) * .18, POM[1])
            put(fx, 64 + r * math.cos(a) * 1.15 + 1, BASE - 2 + r * math.sin(a) * .18, POM[0])

    img = stack((W, H), outlined(feet), outlined(ears), outlined(arm_l), outlined(arm_r),
                outlined(body), face, outlined(cap), outlined(pom), fx)
    return img


BOSS_FRAMES = [
    # 0-3 idle: a slow breath, the zeds drifting off it
    dict(sy=1.00, zs=1), dict(sy=1.03, sx=.99, zs=2), dict(sy=1.05, sx=.985, zs=3), dict(sy=1.02, zs=2),
    # 4-5 wind-up for the Pillow Slam: up on its toes, arms over its head
    dict(sy=1.12, sx=.93, eyes="angry", mouth="gasp", arms="up"),
    dict(sy=1.18, sx=.90, eyes="angry", mouth="snarl", arms="up"),
    # 6-7 the slam: flattened, dust thrown out
    dict(sy=.80, sx=1.12, eyes="shut", mouth="snarl", arms="out", dust=True),
    dict(sy=.90, sx=1.06, eyes="angry", mouth="small", arms="out"),
    # 8-9 the Yawn
    dict(sy=1.06, eyes="shut", mouth="yawn", arms="up"),
    dict(sy=1.10, sx=.98, eyes="shut", mouth="yawn", arms="up", zs=1),
    # 10 hurt, 11 enraged (phase two onward holds this as its idle)
    dict(sy=.96, sx=1.03, eyes="hurt", mouth="gasp", shift=-2),
    dict(sy=1.04, eyes="angry", mouth="snarl", rage=True),
]
# extra rows for the enraged phase and the defeat, appended after the twelve
BOSS_EXTRA = [
    dict(sy=1.02, eyes="angry", mouth="small", rage=True),           # 12 rage idle b
    dict(sy=.70, sx=1.16, eyes="out", mouth="gasp", arms="out"),       # 13 defeated
    dict(sy=.68, sx=1.18, eyes="shut", mouth="small", arms="out", zs=3),  # 14 asleep at last
]


def boss():
    frames = [lord_lull(**f) for f in BOSS_FRAMES + BOSS_EXTRA]
    sheet = layer(128 * len(frames), 96)
    for i, f in enumerate(frames):
        sheet.alpha_composite(f, (i * 128, 0))
    return upscale(sheet, 3)


# --------------------------------------------------------------------------
# Snoozling: the sheep Lord Lull counts. 32x24 native, x3 -> 96x72
# --------------------------------------------------------------------------

WOOL = [hexc("#b8b0d6"), hexc("#d6d0ee"), hexc("#efeafc"), hexc("#ffffff")]
SHEEP_FACE = [hexc("#2d2440"), hexc("#3d3256"), hexc("#524470")]


def snoozling(lift=0, squash=1.0, eyes="drowsy", hit=False):
    W, H = 32, 24
    b = 21 - lift
    legs = layer(W, H)
    if lift == 0:
        for x in (11, 14, 18, 21):
            rect(legs, x, b - 3, x + 2, b + 1, SHEEP_FACE[0])
    else:
        for x in (10, 14, 18, 22):
            rect(legs, x, b - 3, x + 2, b, SHEEP_FACE[0])
    wool = layer(W, H)
    for cx, cy, r in ((11, 14, 5), (16, 11, 6), (21, 14, 5), (13, 17, 5), (19, 17, 5)):
        ellipse(wool, cx, b - (21 - cy) * squash, r, r * squash, WOOL)
    head = layer(W, H)
    hx, hy = 24, b - 9 * squash
    ellipse(head, hx, hy, 4.5, 4, SHEEP_FACE)
    ellipse(head, hx - 4, hy - 3, 2, 1.5, SHEEP_FACE[1:])
    face = layer(W, H)
    if eyes == "drowsy":
        put(face, hx - 2, hy, WOOL[3])
        put(face, hx - 1, hy, WOOL[3])
        put(face, hx + 1, hy, WOOL[3])
        put(face, hx + 2, hy, WOOL[3])
    elif eyes == "shut":
        put(face, hx - 2, hy + 1, WOOL[1])
        put(face, hx + 1, hy + 1, WOOL[1])
    elif eyes == "x":
        for d in (-1, 0, 1):
            put(face, hx - 2 + d, hy + d, WOOL[3])
            put(face, hx + 2 + d, hy - d, WOOL[3])
    put(face, hx, hy + 2, CHEEK)
    img = stack((W, H), outlined(legs), outlined(wool), outlined(head), face)
    if hit:
        px = img.load()
        for y in range(H):
            for x in range(W):
                r, g, bb, a = px[x, y]
                if a:
                    px[x, y] = (min(255, r + 90), min(255, g + 60), min(255, bb + 60), a)
    return img


def sheep():
    frames = [snoozling(0, 1.0), snoozling(0, .9), snoozling(3, 1.05),
              snoozling(0, .95, "x", True), snoozling(0, .8, "shut"), snoozling(0, .78, "shut")]
    sheet = layer(32 * len(frames), 24)
    for i, f in enumerate(frames):
        sheet.alpha_composite(f, (i * 32, 0))
    return upscale(sheet, 3)


def main():
    print("writing", OUT)
    for name, img in (("tiles.png", tiles()), ("props.png", props()),
                      ("boss-lord-lull.png", boss()), ("snoozling.png", sheep())):
        img.save(os.path.join(OUT, name), optimize=True)
        quantise_check(img, name)


if __name__ == "__main__":
    main()
