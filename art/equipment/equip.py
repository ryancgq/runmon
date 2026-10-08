"""Put the pet-footwear-v1 shoe on the three hatchlings.

Run from the repo root:   python3 art/equipment/equip.py [--debug]

Reads `placements.json` (written by fit.py) - for every frame of every pet,
the shoes to draw back to front, each as an atlas view, whether it is
mirrored, the box the shoe itself fills (left, bottom, width, height; the
outline goes around it) and the x-range of the leg that goes into it - and
writes to `preview/`:

- `<pet>-shoes.json`  the attachment track: per frame and foot, the view,
  where its ankle anchor lands, [x, y] scale, rotation, flip, layer, draw
  order and whether the foot is shod.
- `<pet>-shoes.png`   the pet's 12-frame strip with the shoes on, same size
  and framing as the original sheet.
- `<pet>-debug.png`   (--debug) a 4x3 contact sheet.

A shoe is worn, not stuck on: after it is drawn, the pet's own leg is drawn
again wherever it crosses the view's `leg_opening`, so the leg goes down into
the collar and the heel tab and tongue close round it, with a little shadow
where it meets the rim.
"""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ATLAS = os.path.join(HERE, "shoe-runner.png")
TEMPLATE = os.path.join(HERE, "shoe-runner.json")
PLACEMENTS = os.path.join(HERE, "placements.json")
OUT = os.path.join(HERE, "preview")
DEBUG = "--debug" in sys.argv

# form, sheet, and the outline weight that matches the pet's own line work
PETS = {
    "cinderling": ("ember:1", "art/ember-cinderling.png", 2),
    "sparky": ("nimbus:1", "art/nimbus-sparky.png", 4),
    "bamboo_cub": ("verdant:1", "art/verdant-bamboo-cub-v3.png", 2),
}
FEET = ["hind_near", "hind_far", "front_near", "front_far"]

# A shoe this small loses its own 1-2px outline when it is scaled down, so it
# gets a fresh one in the pet's own line weight.
OUTLINE_RGB = (24, 20, 28)
# how far down the rim the leg's shadow falls, and how dark
SHADOW_PX, SHADOW = 3, 0.62

atlas = Image.open(ATLAS).convert("RGBA")
tpl = json.load(open(TEMPLATE))

# Each view cropped to its silhouette; anchor and leg opening kept relative to it.
VIEWS = []
for v in tpl["views"]:
    x, y, w, h = v["rect"]
    cell = atlas.crop((x, y, x + w, y + h))
    a = np.asarray(cell)[..., 3] > 128
    ys, xs = np.nonzero(a)
    bx0, by0 = xs.min(), ys.min()
    VIEWS.append(dict(name=v["name"], img=cell.crop((bx0, by0, xs.max() + 1, ys.max() + 1)),
                      anchor=(v["ankle_anchor"][0] - bx0, v["ankle_anchor"][1] - by0),
                      opening=[(px - bx0, py - by0) for px, py in v.get("leg_opening", [])]))


def shoe(view, width, height, outline, flip=False):
    """The view fitted to a width x height box, mirrored if asked, with the
    outline around it. Returns the image, the [x, y] scale applied to the
    atlas, the ankle anchor's position in the image, and the leg opening as a
    mask over the image (None for a view without one)."""
    v = VIEWS[view]
    sx, sy = width / v["img"].width, height / v["img"].height
    # Box-filter down, then snap alpha hard so the edge stays crisp on the
    # pixelated renderer instead of feathering into the backdrop.
    small = np.asarray(v["img"].resize((width, height), Image.BOX)).copy()
    small[..., 3] = np.where(small[..., 3] >= 128, 255, 0)
    body = Image.fromarray(small)
    canvas = Image.new("RGBA", (width + 2 * outline, height + 2 * outline), (0, 0, 0, 0))
    canvas.paste(body, (outline, outline))
    rim = canvas.getchannel("A").filter(ImageFilter.MaxFilter(2 * outline + 1))
    img = Image.new("RGBA", canvas.size, OUTLINE_RGB + (0,))
    img.putalpha(rim)
    img.alpha_composite(canvas)
    ax, ay = outline + v["anchor"][0] * sx, outline + v["anchor"][1] * sy
    opening = None
    if v["opening"]:
        m = Image.new("L", img.size, 0)
        ImageDraw.Draw(m).polygon([(outline + px * sx, outline + py * sy)
                                   for px, py in v["opening"]], fill=255)
        opening = np.asarray(m) > 0
    if flip:
        img = img.transpose(Image.FLIP_LEFT_RIGHT)
        ax = img.width - ax
        opening = None if opening is None else opening[:, ::-1]
    return img, [round(sx, 4), round(sy, 4)], (ax, ay), opening


def wear(frame, orig, img, left, top, opening, leg):
    """Draw the shoe, then the leg back over its opening, with a shadow on the
    rim below. frame is modified in place; orig is the untouched pet frame."""
    frame.alpha_composite(img, (left, top))
    if opening is None or leg is None:
        return
    fh, fw = orig.shape[:2]
    h, w = opening.shape
    # the opening, in frame coordinates
    m = np.zeros((fh, fw), bool)
    y0, x0 = max(0, top), max(0, left)
    y1, x1 = min(fh, top + h), min(fw, left + w)
    m[y0:y1, x0:x1] = opening[y0 - top:y1 - top, x0 - left:x1 - left]
    band = np.zeros(fw, bool)
    band[max(0, leg[0]):min(fw, leg[1])] = True
    m &= band[None, :] & (orig[..., 3] > 0)
    if not m.any():
        return
    out = np.asarray(frame).copy()
    # shadow first, on the shoe just below where the leg goes in
    shoe_a = np.zeros((fh, fw), bool)
    sa = np.asarray(img)[..., 3] > 0
    shoe_a[y0:y1, x0:x1] = sa[y0 - top:y1 - top, x0 - left:x1 - left]
    for x in np.nonzero(m.any(0))[0]:
        yb = np.nonzero(m[:, x])[0].max()
        ys = np.arange(yb + 1, min(fh, yb + 1 + SHADOW_PX))
        ys = ys[shoe_a[ys, x]]
        out[ys, x, :3] = (out[ys, x, :3] * SHADOW).astype(np.uint8)
    out[m] = orig[m]
    frame.paste(Image.fromarray(out))


def build(pet, placements):
    form, src, outline = PETS[pet]
    sheet = Image.open(src).convert("RGBA")
    fw, fh = sheet.width // 12, sheet.height
    strip = Image.new("RGBA", sheet.size, (0, 0, 0, 0))
    track = dict(form=form, sheet=src, frame_size=[fw, fh], template=tpl["template"],
                 coordinates="frame pixels; anchor is where the view's ankle anchor lands",
                 frames=[])
    for i, shoes in enumerate(placements[pet]):
        frame = sheet.crop((i * fw, 0, (i + 1) * fw, fh))
        orig = np.asarray(frame).copy()
        worn = {s["foot"] for s in shoes}
        entries = []
        for z, s in enumerate(shoes):
            flip = s.get("flip", False)
            img, scale, (ax, ay), opening = shoe(s["view"], s["width"], s["height"], outline, flip)
            left, top = s["left"] - outline, s["bottom"] + outline - img.height
            wear(frame, orig, img, left, top, opening, s.get("leg"))
            entries.append(dict(foot=s["foot"], visible=True, view=s["view"],
                                view_name=VIEWS[s["view"]]["name"],
                                anchor=[round(left + ax), round(top + ay)],
                                scale=scale, rotation=0, flip=flip,
                                layer="front", z=z, leg=s.get("leg")))
        entries += [dict(foot=f, visible=False) for f in FEET if f not in worn]
        strip.paste(frame, (i * fw, 0))
        track["frames"].append(dict(frame=i, shoes=entries))
    return strip, track


def main():
    placements = json.load(open(PLACEMENTS))
    os.makedirs(OUT, exist_ok=True)
    for pet in PETS:
        img, track = build(pet, placements)
        img.save(f"{OUT}/{pet}-shoes.png", optimize=True)
        with open(f"{OUT}/{pet}-shoes.json", "w") as f:
            json.dump(track, f, indent=1)
        if DEBUG:
            fw, fh = img.width // 12, img.height
            grid = Image.new("RGBA", (4 * fw, 3 * fh), (40, 40, 60, 255))
            d = ImageDraw.Draw(grid)
            for i in range(12):
                x, y = (i % 4) * fw, (i // 4) * fh
                grid.alpha_composite(img.crop((i * fw, 0, (i + 1) * fw, fh)), (x, y))
                d.text((x + 4, y + 4), str(i + 1), fill=(255, 255, 0, 255))
            grid.save(f"{OUT}/{pet}-debug.png")
        print(pet, "ok")


if __name__ == "__main__":
    main()
