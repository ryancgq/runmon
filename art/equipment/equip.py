"""Put the pet-footwear-v1 shoe on the three hatchlings.

Run from the repo root:   python3 art/equipment/equip.py [--debug]

Reads `placements.json` - for every frame of every pet, the shoes to draw in
back-to-front order, each as the atlas view and the box the shoe itself
fills on that frame (left edge, bottom, width, height; the outline goes around
it, as in the mockups) - and writes to `preview/`:

- `<pet>-shoes.json`  the attachment track: per frame and foot, the atlas view,
  where its ankle anchor lands, scale, rotation, flip, layer and visibility.
- `<pet>-shoes.png`   the pet's 12-frame strip with the shoes composited on,
  same size and framing as the original sheet.
- `<pet>-debug.png`   (--debug) a 4x3 contact sheet.

The placements were fitted to the hand-made mockups of each pet wearing the
shoe. Any shoe drawn to the same template reuses them unchanged.
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
    "cinderling": ("ember:1", "art/ember-cinderling.png", 3),
    "sparky": ("nimbus:1", "art/nimbus-sparky.png", 4),
    "bamboo_cub": ("verdant:1", "art/verdant-bamboo-cub.png", 3),
}
FEET = ["hind_near", "hind_far", "front_near", "front_far"]

# A shoe this small loses its own 1-2px outline when it is scaled down, so it
# gets a fresh one - the heavy dark rim the mockups have, which is also what
# keeps a pale shoe readable against a pale belly.
OUTLINE_RGB = (24, 20, 28)

atlas = Image.open(ATLAS).convert("RGBA")
tpl = json.load(open(TEMPLATE))
placements = json.load(open(PLACEMENTS))

# Each view cropped to its silhouette; the ankle anchor kept relative to it.
VIEWS = []
for v in tpl["views"]:
    x, y, w, h = v["rect"]
    cell = atlas.crop((x, y, x + w, y + h))
    a = np.asarray(cell)[..., 3] > 128
    ys, xs = np.nonzero(a)
    bx0, by0 = xs.min(), ys.min()
    VIEWS.append(dict(name=v["name"], img=cell.crop((bx0, by0, xs.max() + 1, ys.max() + 1)),
                      anchor=(v["ankle_anchor"][0] - bx0, v["ankle_anchor"][1] - by0)))


def shoe(view, width, height, outline):
    """The view fitted to a width x height box, with the outline around it.
    Returns the image, the [x, y] scale applied to the atlas, and the ankle
    anchor's position inside the returned image."""
    v = VIEWS[view]
    inner, h = width, height
    sx, sy = inner / v["img"].width, h / v["img"].height
    # Box-filter down, then snap alpha hard so the edge stays crisp on the
    # pixelated renderer instead of feathering into the backdrop.
    small = np.asarray(v["img"].resize((inner, h), Image.BOX)).copy()
    small[..., 3] = np.where(small[..., 3] >= 128, 255, 0)
    body = Image.fromarray(small)
    canvas = Image.new("RGBA", (width + 2 * outline, height + 2 * outline), (0, 0, 0, 0))
    canvas.paste(body, (outline, outline))
    rim = canvas.getchannel("A").filter(ImageFilter.MaxFilter(2 * outline + 1))
    out = Image.new("RGBA", canvas.size, OUTLINE_RGB + (0,))
    out.putalpha(rim)
    out.alpha_composite(canvas)
    ax, ay = v["anchor"]
    return out, [round(sx, 4), round(sy, 4)], (outline + ax * sx, outline + ay * sy)


def build(pet):
    form, src, outline = PETS[pet]
    sheet = Image.open(src).convert("RGBA")
    fw, fh = sheet.width // 12, sheet.height
    strip = Image.new("RGBA", sheet.size, (0, 0, 0, 0))
    track = dict(form=form, sheet=src, frame_size=[fw, fh], template=tpl["template"],
                 coordinates="frame pixels; anchor is where the view's ankle anchor lands",
                 frames=[])
    for i, shoes in enumerate(placements[pet]):
        frame = sheet.crop((i * fw, 0, (i + 1) * fw, fh))
        worn = {s["foot"] for s in shoes}
        entries = []
        for z, s in enumerate(shoes):
            img, scale, (ax, ay) = shoe(s["view"], s["width"], s["height"], outline)
            left, top = s["left"] - outline, s["bottom"] + outline - img.height
            frame.alpha_composite(img, (left, top))
            entries.append(dict(foot=s["foot"], visible=True, view=s["view"],
                                view_name=VIEWS[s["view"]]["name"],
                                anchor=[round(left + ax), round(top + ay)],
                                scale=scale, rotation=0, flip=False,
                                layer="front", z=z))
        entries += [dict(foot=f, visible=False) for f in FEET if f not in worn]
        strip.paste(frame, (i * fw, 0))
        track["frames"].append(dict(frame=i, shoes=entries))
    return strip, track


def main():
    os.makedirs(OUT, exist_ok=True)
    for pet in PETS:
        img, track = build(pet)
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
