#!/usr/bin/env python3
"""Generate the Pet Explore prototype's own art.

Everything the pets themselves wear comes from the main game's sheets in
../art/ - this only draws what the world needs that the game has never had:
ground tiles, props, and the mobs that live out there. The raid boss is the
game's own Sir Uwaaarghhhh.

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


# --------------------------------------------------------------------------
# mobs: 96x80 native cells, x3 -> 288x240, one 16-frame strip per creature
# --------------------------------------------------------------------------
# The world's own creatures, the ones that were never anybody's pet. They are
# drawn in the pets' own language rather than the props': one round, fuzzy
# ball of a body lit from the upper left, big glossy eyes with two
# highlights, little paws tucked in front, and a thick dark outline - the
# same kind of creature as the Sparky and the Cinderling, at about the Bamboo
# Cub's resolution once upscaled. Each strip is laid out the same way, so the
# page cuts them all alike:
#
#   0-3   idle loop (also the walk, two of them at a time); 3 is a blink
#   4     knocked out
#   5-9   first move
#   10-15 second move
#
# Facing right, like every pet sheet, the lowest paw on row 76 of 80 in
# every frame (the wisp floats, so for it that row is the tip of its tail).

MW_, MH_ = 96, 80
MOB_K = 3
INK = hexc("#22141c")
WHITE = hexc("#ffffff")
SCLERA = [hexc("#d9dde6"), hexc("#f4f6fa")]
PUPIL_C = hexc("#140c14")
MOUTH = hexc("#5a1424")
TONGUE = hexc("#e8607a")
BLUSH = hexc("#ff8fa0", 255)


def tex(x, y, seed):
    """A fixed scatter for the fur's texture: the same pixels every run."""
    h = (x * 73856093) ^ (y * 19349663) ^ (seed * 83492791)
    h = (h ^ (h >> 13)) * 1274126177 & 0xFFFFFFFF
    return (h & 0xFFFF) / 65535


def blob(img, cx, cy, rx, ry, ramp, fuzz=0.0, seed=0, lobes=11, grain=0.08, shine=True):
    """A round body with a tufted edge, shaded from the upper left in bands,
    a little grain through it and a soft shine high on the left."""
    n = len(ramp)
    for y in range(int(cy - ry * 1.2) - 1, int(cy + ry * 1.2) + 2):
        for x in range(int(cx - rx * 1.2) - 1, int(cx + rx * 1.2) + 2):
            nx = (x + 0.5 - cx) / rx
            ny = (y + 0.5 - cy) / ry
            a = math.atan2(ny, nx)
            edge = 1 + fuzz * (0.5 + 0.5 * math.sin(a * lobes + seed)) if fuzz else 1
            d = nx * nx + ny * ny
            if d > edge * edge:
                continue
            k = shade_index(nx / edge * 0.98, ny / edge * 0.98, n)
            t = tex(x, y, seed)
            if t < grain and k > 0:
                k -= 1
            elif t > 1 - grain * 0.6 and k < n - 1:
                k += 1
            if shine and (nx + 0.38) ** 2 + (ny + 0.5) ** 2 < 0.05:
                k = n - 1
            put(img, x, y, ramp[k])


def thick(img, c=INK):
    return outlined(outlined(img, c), c)


def big_eye(img, cx, cy, rx, ry, mood="open", look=(1, -0.2), body=None):
    """The pets' eye: a white eye ringed in ink, a big pupil looking the way
    the creature is going, and two highlights. Closed, it is a curved line."""
    if mood in ("shut", "happy", "ko"):
        if mood == "ko":
            for t in range(-3, 4):
                put(img, cx + t, cy + t, INK)
                put(img, cx + t + 1, cy + t, INK)
                put(img, cx + t, cy - t, INK)
                put(img, cx + t + 1, cy - t, INK)
            return
        # shut: a lid line curving down; happy: curving up, like the Sparky's grin
        for t in range(-int(rx), int(rx) + 1):
            u = t / rx
            dy = (1 - u * u) * ry * 0.35
            y = cy + (dy if mood == "shut" else -dy)
            put(img, cx + t, y, INK)
            put(img, cx + t, y + 1, INK)
        return
    e = layer(MW_, MH_)
    ellipse(e, cx, cy, rx, ry, SCLERA)
    e = outlined(e, INK)
    # the heavy upper lid every pet sheet draws
    for t in range(-int(rx) - 1, int(rx) + 2):
        u = t / (rx + 1)
        if abs(u) <= 1:
            y = cy - (ry + 1) * math.sqrt(1 - u * u)
            put(e, cx + t, y, INK)
            if abs(u) < 0.8:
                put(e, cx + t, y - 1, INK)
    img.alpha_composite(e)
    px, py = cx + look[0] * rx * 0.28, cy + look[1] * ry * 0.3 + ry * 0.08
    ellipse(img, px, py, rx * 0.66, ry * 0.7, PUPIL_C)
    ellipse(img, px - rx * 0.25, py - ry * 0.3, max(1.2, rx * 0.26), max(1.2, ry * 0.24), WHITE)
    put(img, px + rx * 0.28, py + ry * 0.3, WHITE)
    if mood == "angry" and body:
        # a heavy lid slanting down to the nose, in the body's own colour
        inner = 1 if look[0] >= 0 else -1
        for x in range(int(cx - rx) - 2, int(cx + rx) + 3):
            u = (x - cx) / rx * inner
            lid = cy - ry * 0.95 + (u + 1) * ry * 0.42
            for y in range(int(cy - ry) - 3, int(lid) + 1):
                inside = ((x - cx) / (rx + 2.5)) ** 2 + ((y - cy) / (ry + 2.5)) ** 2 <= 1
                if inside and 0 <= x < MW_ and 0 <= y < MH_ and img.getpixel((x, y))[3]:
                    put(img, x, y, body)
            if ((x - cx) / (rx + 2.5)) ** 2 + ((lid - cy) / (ry + 2.5)) ** 2 <= 1:
                put(img, x, lid, INK)
                put(img, x, lid + 1, INK)


def mouth(img, cx, cy, kind, w=4):
    if kind == "smile":
        for t in range(-w, w + 1):
            put(img, cx + t, cy + (w * w - t * t) / (w * w) * 1.6, INK)
    elif kind == "frown":
        for t in range(-w, w + 1):
            put(img, cx + t, cy + 1.6 - (w * w - t * t) / (w * w) * 1.6, INK)
    elif kind in ("open", "shout"):
        m = layer(MW_, MH_)
        ry = 3.2 if kind == "open" else 4.5
        ellipse(m, cx, cy + ry * 0.6, w, ry, MOUTH)
        rect(m, cx - w - 1, cy - 4, cx + w + 2, cy + 0.6, CLEAR)
        ellipse(m, cx + 0.5, cy + ry * 1.1, w * 0.55, ry * 0.4, TONGUE)
        img.alpha_composite(outlined(m, INK))
    elif kind == "o":
        ellipse(img, cx, cy + 1.5, 2.2, 2.5, INK)
        put(img, cx, cy + 1.5, MOUTH)


def blush(img, cx, cy):
    for dx in range(-2, 3):
        if 0 <= cx + dx < MW_ and img.getpixel((int(cx + dx), int(cy)))[3]:
            put(img, cx + dx, cy, BLUSH)


def paw(img, cx, cy, ramp, claws=None, w=6.5, h=5):
    p = layer(MW_, MH_)
    blob(p, cx, cy, w, h, ramp, shine=False, grain=0)
    p = thick(p)
    img.alpha_composite(p)
    if claws:
        for k in (-1, 0, 1):
            put(img, cx + k * 2.4, cy + h, claws)
            put(img, cx + k * 2.4, cy + h + 1, claws)


def sparkle(img, x, y, c, r=2):
    for t in range(-r, r + 1):
        put(img, x + t, y, c)
        put(img, x, y + t, c)
    put(img, x, y, WHITE)


# the pose every creature reads from: where its body is, how squashed, and its face
def pose_for(f, moves):
    p = {"dx": 0, "dy": 0, "sx": 1.0, "sy": 1.0, "eyes": "open", "mouth": "smile", "look": (1, -0.2),
         "act": None, "k": 0}
    breath = (0, 1, 0, -1)[f % 4]
    if f < 4:
        p["sy"] = 1 + breath * 0.015
        p["sx"] = 1 - breath * 0.012
        p["look"] = ((1, -0.2), (1, -0.1), (0.6, -0.5), (1, -0.2))[f]
        if f == 3:
            p["eyes"] = "shut"
    elif f == 4:
        p.update(eyes="ko", mouth="o", sy=0.9, sx=1.06, dy=3)
    else:
        name, k = (moves[0], f - 5) if f < 10 else (moves[1], f - 10)
        p["act"], p["k"] = name, k
    return p


# ---- Bramble Boar ------------------------------------------------------------

BOAR = [hexc("#6e3434"), hexc("#9a4e48"), hexc("#c26e5e"), hexc("#dd8d74"), hexc("#f0b08e")]
BOAR_DK = [hexc("#4e2428"), hexc("#6e3434"), hexc("#9a4e48")]
BOAR_SNOUT = [hexc("#c46a72"), hexc("#e08890"), hexc("#f4aab0"), hexc("#ffd0d0")]
HOOF = hexc("#3a2026")


def mob_boar(f):
    p = pose_for(f, ("gore", "stomp"))
    act, k = p["act"], p["k"]
    dust, front_up = 0, 0
    if act == "gore":
        # paw the ground, drop the head, charge, and pull up
        p.update(eyes="angry", mouth="frown")
        if k == 0:
            p.update(dx=-3, sy=1.02)
        elif k == 1:
            p.update(dx=-5, dy=2, sy=0.95, sx=1.05)
        elif k in (2, 3):
            p.update(dx=4, dy=1, sx=1.08, sy=0.94, mouth="shout")
            dust = 1 + (k - 2)
        else:
            p.update(dx=1, eyes="open", mouth="smile")
    elif act == "stomp":
        p.update(eyes="angry", mouth="shout")
        if k in (0, 1):
            p.update(dy=-4 - k * 4, sy=1.04)
            front_up = 4 + k * 4
        elif k == 2:
            p.update(dy=3, sy=0.86, sx=1.12)
            dust = 3
        elif k == 3:
            p.update(dy=2, sy=0.92, sx=1.06)
            dust = 4
        else:
            p.update(eyes="open", mouth="smile")
    dx, dy, sx, sy = p["dx"], p["dy"], p["sx"], p["sy"]
    cx, cy = 44 + dx, 46 + dy
    rx, ry = 29 * sx, 26 * sy
    img = layer(MW_, MH_)
    back = layer(MW_, MH_)
    blob(back, cx - 16, 70, 7, 6, BOAR_DK, shine=False)
    blob(back, cx - 4, 71, 6.5, 5.5, BOAR_DK, shine=False)
    img.alpha_composite(thick(back))
    # a curl of a tail
    tail = layer(MW_, MH_)
    for t in range(14):
        a = t / 13 * 5.2
        put(tail, cx - rx - 1 + math.cos(a) * (4 - t * 0.2), cy - 2 + math.sin(a) * (4 - t * 0.2), BOAR[1])
        put(tail, cx - rx + math.cos(a) * (4 - t * 0.2), cy - 2 + math.sin(a) * (4 - t * 0.2), BOAR[2])
    img.alpha_composite(thick(tail))
    body = layer(MW_, MH_)
    blob(body, cx, cy, rx, ry, BOAR, fuzz=0.05, seed=3, lobes=14)
    img.alpha_composite(thick(body))
    # ears
    for ex, lean in ((cx + 6, -1), (cx + 20, 1)):
        ear = layer(MW_, MH_)
        polygon(ear, [(ex - 6, cy - ry + 9), (ex + lean * 3, cy - ry - 6), (ex + 7, cy - ry + 9)],
                lambda x, y: BOAR[2] if x < ex else BOAR[1])
        polygon(ear, [(ex - 3, cy - ry + 8), (ex + lean * 2, cy - ry - 1), (ex + 4, cy - ry + 8)],
                lambda x, y: BOAR_SNOUT[0])
        img.alpha_composite(thick(ear))
    # the bramble: a tuft of leaves and thorns down its back, with a berry
    rng = random.Random(9)
    br = layer(MW_, MH_)
    for i in range(6):
        a = math.pi * (1.05 + i * 0.13)
        bx, by = cx + math.cos(a) * rx * 0.86, cy + math.sin(a) * ry * 0.9
        ellipse(br, bx, by, 5.2, 4.2, LEAF[1:])
        ellipse(br, bx + rng.uniform(-2, 2), by - 3, 3.4, 3, LEAF[2:])
    br = thick(br)
    for i in range(5):
        a = math.pi * (1.1 + i * 0.15)
        bx, by = cx + math.cos(a) * (rx + 4), cy + math.sin(a) * (ry + 4)
        put(br, bx, by, hexc("#e8d8a8"))
        put(br, bx, by - 1, INK)
    ellipse(br, cx - rx * 0.35, cy - ry - 1, 2.6, 2.6, [hexc("#7a1c3a"), hexc("#b42c55"), hexc("#ff8fb1")])
    img.alpha_composite(br)
    # the face, on the right of the ball
    sn = layer(MW_, MH_)
    snx, sny = cx + rx * 0.72, cy + 6
    blob(sn, snx, sny, 9 * sx, 7, BOAR_SNOUT, shine=False, grain=0)
    sn = thick(sn)
    ellipse(sn, snx - 3, sny, 1.6, 2.4, INK)
    ellipse(sn, snx + 3, sny, 1.6, 2.4, INK)
    img.alpha_composite(sn)
    for tx in (snx - 7, snx + 6):
        tusk = layer(MW_, MH_)
        polygon(tusk, [(tx - 1.5, sny + 5), (tx + 0.5, sny + 11), (tx + 2, sny + 5)], lambda x, y: hexc("#f6eedc"))
        img.alpha_composite(outlined(tusk, INK))
    look = p["look"]
    big_eye(img, cx + rx * 0.2, cy - 8, 7, 8.5, p["eyes"], look, BOAR[2])
    big_eye(img, cx + rx * 0.2 + 18, cy - 8.5, 6.5, 8, p["eyes"], look, BOAR[2])
    blush(img, cx + rx * 0.2 - 6, cy + 4)
    mouth(img, snx, sny + 9, p["mouth"], 3)
    # front trotters
    for k2, fx in enumerate((cx + 2, cx + 17)):
        paw(img, fx, 71 + min(0, dy) * 0 - front_up, BOAR_DK + [BOAR[2]], None, 6.5, 5)
        put(img, fx, 75 - front_up, HOOF)
        put(img, fx, 74 - front_up, HOOF)
    if dust:
        rng = random.Random(30 + f)
        for _ in range(8 * dust):
            side = rng.choice((-1, 1)) if act == "stomp" else -1
            x = cx + side * (rx * 0.7 + rng.uniform(0, 8 + dust * 4))
            y = 74 - rng.uniform(0, 4 + dust * 2)
            ellipse(img, x, y, rng.uniform(1.5, 3), rng.uniform(1.2, 2.4), [PATH[2], PATH[3]])
    return img


# ---- Cinder Beetle -----------------------------------------------------------

SHELL = [hexc("#1a1218"), hexc("#281c24"), hexc("#3a2932"), hexc("#523b44"), hexc("#6e5560")]
EMBERFACE = [hexc("#8a2a16"), hexc("#b4401e"), hexc("#d85c2a"), hexc("#f07e3a"), hexc("#ffad62")]
GLOW = [hexc("#c23a1c"), hexc("#ff6b35"), hexc("#ffd23f"), hexc("#fff3b0")]


def mob_beetle(f):
    p = pose_for(f, ("ram", "spit"))
    act, k = p["act"], p["k"]
    hot = f % 4 in (1, 2) if f < 4 else True
    trail, spit = 0, 0
    if act == "ram":
        p.update(eyes="angry", mouth="frown")
        if k in (0, 1):
            p.update(dx=-2 - k * 2, dy=1 + k, sy=0.95 - k * 0.03, sx=1.04)
        elif k in (2, 3):
            p.update(dx=4, sx=1.1, sy=0.9, mouth="shout")
            trail = k - 1
        else:
            p.update(dx=1, eyes="open", mouth="smile")
    elif act == "spit":
        if k in (0, 1):
            p.update(dy=-1 - k, sy=1.04, mouth="o", look=(1, -0.6), eyes="angry")
        elif k in (2, 3):
            p.update(dx=-2, sx=1.04, mouth="shout", eyes="angry")
            spit = k - 1
        else:
            p.update(eyes="open")
    elif f == 4:
        hot = False
    dx, dy, sx, sy = p["dx"], p["dy"], p["sx"], p["sy"]
    cx, cy = 44 + dx, 47 + dy
    rx, ry = 30 * sx, 25 * sy
    img = layer(MW_, MH_)
    legs = layer(MW_, MH_)
    for i, lx in enumerate((-18, -6, 6)):
        step = ((f + i) % 2) * 2 if f < 4 or trail else 0
        line(legs, cx + lx, 66, cx + lx - 3 + step, 75, SHELL[2])
        line(legs, cx + lx + 1, 66, cx + lx - 2 + step, 75, SHELL[3])
        line(legs, cx + lx + 2, 66, cx + lx - 1 + step, 75, SHELL[2])
    img.alpha_composite(thick(legs))
    body = layer(MW_, MH_)
    blob(body, cx, cy, rx, ry, SHELL, fuzz=0.02, seed=7, lobes=6, grain=0.05)
    img.alpha_composite(thick(body))
    # the seam down the shell, and the lava showing through it
    g = GLOW[2] if hot else GLOW[1]
    for t in range(-26, 22):
        x = cx + t * sx
        u = t / 30
        y = cy - ry * math.sqrt(max(0, 1 - u * u)) * 0.92 + 3
        put(img, x, y, g if t % 5 else GLOW[3] if hot else GLOW[2])
        put(img, x, y + 1, GLOW[0])
    for (ox, oy, ln) in ((-14, -4, 7), (-4, 4, 6), (-20, 8, 5), (-9, -12, 4)):
        for t in range(ln):
            put(img, cx + ox + t * 0.8, cy + oy + (t % 2), GLOW[1] if t % 3 else g)
    # the face: a warm, glowing plate on the front of the ball
    face = layer(MW_, MH_)
    fcx, fcy = cx + rx * 0.5, cy + 4
    blob(face, fcx, fcy, 18 * sx, 17 * sy, EMBERFACE, grain=0.04)
    img.alpha_composite(thick(face))
    # antennae, ember-tipped
    for ax, lean in ((fcx - 4, -1), (fcx + 7, 1)):
        ant = layer(MW_, MH_)
        top = (ax + lean * 6 + 3, fcy - 15 * sy - 12)
        for t in range(12):
            u = t / 11
            put(ant, ax + (top[0] - ax) * u + math.sin(u * 3) * 2, fcy - 13 * sy + (top[1] - fcy + 13 * sy) * u, SHELL[3])
        ant = thick(ant)
        ellipse(ant, top[0], top[1], 2.4, 2.4, [GLOW[1], GLOW[2], GLOW[3]])
        img.alpha_composite(ant)
    big_eye(img, fcx - 6, fcy - 4, 6.5, 7.8, p["eyes"], p["look"], EMBERFACE[2])
    big_eye(img, fcx + 10, fcy - 4.5, 6, 7.4, p["eyes"], p["look"], EMBERFACE[2])
    blush(img, fcx - 11, fcy + 6)
    mouth(img, fcx + 2, fcy + 8, p["mouth"], 3)
    if trail:
        rng = random.Random(50 + f)
        for _ in range(10 * trail):
            x, y = cx - rx - rng.uniform(0, 14), cy + rng.uniform(-ry * 0.6, ry * 0.6)
            ellipse(img, x, y, rng.uniform(1, 2.6), rng.uniform(1, 2.2), [GLOW[0], GLOW[1], GLOW[2]])
    if spit:
        bx, r = fcx + 15 + spit * 6, 3 + spit * 1.6
        ball = layer(MW_, MH_)
        ellipse(ball, bx, fcy + 5, r, r, [GLOW[0], GLOW[1], GLOW[2], GLOW[3]])
        img.alpha_composite(outlined(ball, hexc("#7a1f10")))
    return img


# ---- Puffcap -----------------------------------------------------------------

CAP = [hexc("#6a1626"), hexc("#962536"), hexc("#c23c44"), hexc("#e2604f"), hexc("#f6906a")]
STEM = [hexc("#9c8462"), hexc("#bea782"), hexc("#dac8a2"), hexc("#efe3c6"), hexc("#fff8e8")]
GILL = [hexc("#8a6e58"), hexc("#a88a70")]
SPORES = [hexc("#9cc84a"), hexc("#c8e86a"), hexc("#eeffa8")]


def mob_puffcap(f):
    p = pose_for(f, ("spores", "bonk"))
    act, k = p["act"], p["k"]
    lean, puff, spores = 0, 0, 0
    if f < 4:
        puff = (0, 1, 0, -1)[f] * 0.6
    if act == "spores":
        if k in (0, 1):
            p.update(sy=0.92 - k * 0.05, sx=1.05, eyes="shut", mouth="frown")
            puff = -2 - k
        elif k in (2, 3):
            p.update(sy=1.06, mouth="open", eyes="angry")
            puff, spores = 3, k - 1
        else:
            p.update(eyes="open")
    elif act == "bonk":
        p.update(eyes="angry", mouth="frown")
        if k in (0, 1):
            lean = -3 - k * 3
        elif k in (2, 3):
            lean, p["mouth"] = 9, "shout"
            p.update(dy=1)
        elif k == 4:
            lean = 3
        else:
            p.update(eyes="open", mouth="smile")
    dx, dy, sx, sy = p["dx"], p["dy"], p["sx"], p["sy"]
    img = layer(MW_, MH_)
    # stubby feet
    for fx in (34, 54):
        step = 2 if f < 4 and ((f + (fx > 40)) % 2) else 0
        paw(img, fx + dx, 72 - step, STEM[:4], None, 6, 4.5)
    # the stem is the body, and the face is on it
    st = layer(MW_, MH_)
    scx, scy = 45 + dx, 56 + dy + (1 - sy) * 20
    blob(st, scx, scy, 21 * sx, 18 * sy, STEM, fuzz=0, grain=0.04)
    img.alpha_composite(thick(st))
    look = p["look"]
    big_eye(img, scx, scy + 1, 6.2, 7.4, p["eyes"], look, STEM[2])
    big_eye(img, scx + 15, scy + 0.5, 5.8, 7, p["eyes"], look, STEM[2])
    blush(img, scx - 5, scy + 9)
    blush(img, scx + 20, scy + 9)
    mouth(img, scx + 8, scy + 10, p["mouth"], 3)
    # the cap, sitting on it like a hat a size too big
    cap = layer(MW_, MH_)
    ccx, ccy = 45 + dx + lean, 31 + dy + (1 - sy) * 26 - puff * 0.5 + abs(lean) * 0.25
    crx, cry = 36 + puff, 22 + puff * 0.8
    blob(cap, ccx, ccy, crx, cry, CAP, fuzz=0, grain=0.05)
    cut = ccy + cry * 0.38 + lean * 0.0
    for y in range(int(cut), MH_):
        for x in range(MW_):
            # the rim slopes with the lean
            if y > cut + (x - ccx) * lean * 0.02:
                put(cap, x, y, CLEAR)
    for x in range(int(ccx - crx), int(ccx + crx) + 1):
        for y in range(int(cut) - 3, int(cut) + 2):
            if cap.getpixel((x, y))[3] and y > cut - 3 + (x - ccx) * lean * 0.02:
                put(cap, x, y, GILL[(x // 3) % 2])
    for sx_, sy_, r in ((-18, -6, 5), (-2, -14, 6), (14, -8, 5.5), (24, 1, 3.6), (-27, 3, 3.2), (4, -2, 3)):
        ellipse(cap, ccx + sx_ * (crx / 36), ccy + sy_ * (cry / 22), r, r * 0.8, STEM[2:])
    img.alpha_composite(thick(cap))
    if spores:
        rng = random.Random(60 + f)
        for _ in range(16 * spores):
            a = rng.uniform(-math.pi, 0.2)
            r = 30 + spores * 8 + rng.uniform(0, 6)
            x, y = 45 + math.cos(a) * r * 1.05, 40 + math.sin(a) * r * 0.75
            sp = layer(MW_, MH_)
            ellipse(sp, x, y, 1.6, 1.6, SPORES)
            img.alpha_composite(outlined(sp, hexc("#3a5020")))
    return img


# ---- Static Wisp -------------------------------------------------------------

CLOUD_ = [hexc("#33608e"), hexc("#4f86ba"), hexc("#7cb2e0"), hexc("#b4dcf6"), hexc("#ecfaff")]
WISP_INK = hexc("#142640")
BOLT = [hexc("#ff9a2a"), hexc("#ffd23f"), hexc("#fff6b0")]


def bolt_shape(img, x, y, s, lean=0):
    b = layer(MW_, MH_)
    pts = [(x, y - 7 * s), (x + 4 * s + lean, y - 7 * s), (x + 1 * s, y - 1 * s), (x + 4 * s, y - 1 * s),
           (x - 3 * s, y + 8 * s), (x - 0.5 * s, y + 1 * s), (x - 3.5 * s, y + 1 * s)]
    polygon(b, pts, lambda px, py: BOLT[2] if px < x else BOLT[1])
    img.alpha_composite(thick(b, hexc("#7a3a10")))


def mob_wisp(f):
    p = pose_for(f, ("zap", "discharge"))
    act, k = p["act"], p["k"]
    arcs, glow, zap = 0, 0, 0
    if act == "zap":
        p.update(eyes="angry", mouth="frown")
        if k in (0, 1):
            p.update(sx=0.95, sy=1.05, dx=-2 - k)
            glow = 1 + k
        elif k == 2:
            p.update(sx=1.08, sy=0.94, dx=3, mouth="shout")
            zap, glow = 1, 2
        elif k == 3:
            p.update(dx=2, mouth="shout")
            zap = 2
        else:
            p.update(eyes="open", mouth="smile")
    elif act == "discharge":
        p.update(eyes="angry", mouth="shout")
        if k < 5:
            arcs = (1, 2, 3, 4, 2)[k]
            p.update(sx=1 + arcs * 0.025, sy=1 + arcs * 0.025)
        else:
            p.update(eyes="open", mouth="smile")
    dx, dy, sx, sy = p["dx"], p["dy"], p["sx"], p["sy"]
    bob = (0, -1, 0, 1)[f % 4] if f < 4 else 0
    cx, cy = 50 + dx, 34 + dy + bob
    img = layer(MW_, MH_)
    if glow or arcs:
        halo = layer(MW_, MH_)
        r = 32 + (glow or arcs) * 2.5
        for y in range(MH_):
            for x in range(MW_):
                d = math.hypot((x - cx) / r, (y - cy) / (r * 0.9))
                if d < 1 and tex(x, y, 5) < 0.18 * (1 - d):
                    put(halo, x, y, hexc("#bff8ff"))
        img.alpha_composite(halo)
    # the tail: a run of smaller and smaller puffs, curling down to a point
    tail = layer(MW_, MH_)
    for i in range(7):
        u = i / 6
        tx = cx - 14 - u * 14 + math.sin(u * 3 + f * 0.6) * 3
        ty = cy + 16 + u * 24
        r = 11 * (1 - u * 0.78)
        blob(tail, tx, ty, r, r * 0.9, CLOUD_[:4], shine=False, grain=0.03)
    img.alpha_composite(thick(tail, WISP_INK))
    body = layer(MW_, MH_)
    for ox, oy, r in ((-16, 4, 12), (16, 6, 12), (-8, -14, 12), (9, -15, 12), (0, 2, 24)):
        blob(body, cx + ox * sx, cy + oy * sy, r * sx, r * 0.92 * sy, CLOUD_, grain=0.04, shine=(r == 24))
    img.alpha_composite(thick(body, WISP_INK))
    bolt_shape(img, cx - 2, cy - 26 * sy, 1.15 + (0.25 if glow or arcs else 0), lean=1)
    look = p["look"]
    big_eye(img, cx + 1, cy + 1, 7, 8.4, p["eyes"], look, CLOUD_[3])
    big_eye(img, cx + 19, cy + 0.5, 6.5, 8, p["eyes"], look, CLOUD_[3])
    blush(img, cx - 5, cy + 12)
    blush(img, cx + 25, cy + 12)
    mouth(img, cx + 10, cy + 12, p["mouth"], 3)
    rng = random.Random(80 + f)
    for _ in range(arcs * 3 + glow):
        a = rng.random() * math.tau
        x, y = cx + math.cos(a) * 26, cy + math.sin(a) * 24
        for _ in range(5 + arcs):
            x2, y2 = x + math.cos(a) * 3 + rng.uniform(-2, 2), y + math.sin(a) * 3 + rng.uniform(-2, 2)
            line(img, x, y, x2, y2, BOLT[1])
            put(img, x, y, BOLT[2])
            x, y = x2, y2
    if zap:
        bolt_shape(img, cx + 36 + zap * 4, cy + 2, 0.9 + zap * 0.25, lean=2)
        for t in range(3):
            sparkle(img, cx + 30 + t * 6, cy - 6 + t * 7, BOLT[1], 1 + zap)
    return img


MOBS = [("beetle", mob_beetle), ("puffcap", mob_puffcap), ("wisp", mob_wisp), ("boar", mob_boar)]


def mobs():
    out = []
    for name, fn in MOBS:
        sheet = layer(MW_ * 16, MH_)
        for f in range(16):
            sheet.alpha_composite(fn(f), (f * MW_, 0))
        out.append(("mob-" + name + ".png", upscale(sheet, MOB_K)))
    return out



def main():
    print("writing", OUT)
    for name, img in (("tiles.png", tiles()), ("props.png", props()), *mobs()):
        img.save(os.path.join(OUT, name), optimize=True)
        quantise_check(img, name)


if __name__ == "__main__":
    main()
