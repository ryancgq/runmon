"""Fit the pet-footwear-v1 shoe atlas to the three hatchling sheets.

Writes, per pet, an attachment track (per frame: view, anchor position, scale,
rotation, flip, layer, visibility per foot) and the composited 12-frame strip.
"""
import json, sys, os
import numpy as np
from PIL import Image, ImageDraw

# Run from the repo root:  python3 art/equipment/equip.py
# --debug also writes a 4x3 contact sheet per pet.
HERE = os.path.dirname(os.path.abspath(__file__))
ATLAS = os.path.join(HERE, "shoe-runner.png")
TEMPLATE = os.path.join(HERE, "shoe-runner.json")
TRACKS = os.path.join(HERE, "paw-tracks.json")
OUT = os.path.join(HERE, "preview")
DEBUG = '--debug' in sys.argv
atlas = Image.open(ATLAS).convert('RGBA')
tpl = json.load(open(TEMPLATE))
tracks = json.load(open(TRACKS))

# Each view cropped to its silhouette; the ankle anchor kept relative to it.
VIEWS = []
for v in tpl['views']:
    x, y, w, h = v['rect']
    cell = atlas.crop((x, y, x + w, y + h))
    a = np.asarray(cell)[..., 3] > 128
    ys, xs = np.nonzero(a)
    bx0, by0, bx1, by1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
    VIEWS.append(dict(name=v['name'], img=cell.crop((bx0, by0, bx1, by1)),
                      anchor=(v['ankle_anchor'][0] - bx0, v['ankle_anchor'][1] - by0)))

SIDE, THREEQ, FRONT, SOLE = 0, 1, 2, 3

# Paws: frame-0 position (centre x, bottom y) and how the shoe sits on it.
# width = shoe silhouette width in sheet px; fx = which fraction of the shoe's
# width sits over the paw centre (the toe runs ahead of the paw in profile).
PETS = {
 "cinderling": dict(form="ember:1", src="art/ember-cinderling.png", feet={
   # drawn back to front: the far feet first, then the near ones over them
   "hind_far":   dict(x=226, y=284, width=58, view=THREEQ, fx=.40, layer="behind", follow="front_far"),
   "hind_near":  dict(x=110, y=289, width=56, view=THREEQ, fx=.40, layer="front"),
   "front_far":  dict(x=264, y=292, width=66, view=THREEQ, fx=.42, layer="front"),
   "front_near": dict(x=150, y=293, width=64, view=THREEQ, fx=.40, layer="front"),
 }, bare={}),
 "sparky": dict(form="nimbus:1", src="art/nimbus-sparky.png", feet={
   "hind_far":   dict(width=56, view=SIDE, fx=.40, layer="behind"),
   "hind_near":  dict(width=58, view=SIDE, fx=.40, layer="front"),
   "front_far":  dict(width=62, view=THREEQ, fx=.42, layer="front"),
   "front_near": dict(width=62, view=THREEQ, fx=.42, layer="front"),
 }, bare={}),
 "bamboo_cub": dict(form="verdant:1", src="art/verdant-bamboo-cub.png", feet={
   "hind_far":   dict(x=36, y=274, width=52, view=SOLE, fx=.5, flip=True, layer="behind", rot=-20),
   "hind_near":  dict(x=72, y=326, width=78, view=SOLE, fx=.55, flip=True, layer="front"),
   "front_far":  dict(x=220, y=328, width=58, view=FRONT, fx=.5, layer="front"),
   "front_near": dict(x=138, y=330, width=64, view=FRONT, fx=.5, layer="front"),
 }, bare={5: ["front_far"], 6: ["front_near", "front_far"], 7: ["front_near", "front_far"],
          8: ["front_near", "front_far"], 9: ["front_near", "front_far"],
          10: ["front_near", "front_far"], 11: ["front_near", "front_far"]}),
}

# Sparky's sheet changes framing between rows and the tracker mistakes one paw
# for its neighbour, so its paws are placed by hand: (centre x, bottom y).
# In frames 10-12 the front paws hold the acorn; the two paws on the ground
# there are the hind feet.
SPARKY = [
  dict(hind_near=(150,329), front_near=(205,331), front_far=(270,331), hind_far=(236,322)),
  dict(hind_near=(162,320), front_near=(195,333), front_far=(272,333), hind_far=(236,324)),
  dict(hind_near=(162,320), front_near=(195,333), front_far=(272,333), hind_far=(236,324)),
  dict(hind_near=(162,320), front_near=(197,333), front_far=(273,333), hind_far=(237,324)),
  dict(hind_near=(145,320), front_near=(178,336), front_far=(252,336), hind_far=(216,326)),
  dict(hind_near=(145,320), front_near=(178,336), front_far=(252,336), hind_far=(216,326)),
  dict(hind_near=(152,322), front_near=(180,331), front_far=(258,331), hind_far=(220,322)),
  dict(hind_near=(148,320), front_near=(177,331), front_far=(253,331), hind_far=(216,322)),
  dict(hind_near=(150,320), front_near=(180,336), front_far=(262,336), hind_far=(222,326)),
  dict(hind_near=(175,335), hind_far=(265,335)),
  dict(hind_near=(175,335), hind_far=(263,336)),
  dict(hind_near=(172,338), hind_far=(263,338)),
]
SPARKY_BARE = {9: ["front_near", "front_far"], 10: ["front_near", "front_far"], 11: ["front_near", "front_far"]}
# where those two ground paws are the hind feet they are in plain view
SPARKY_HIND_FRONT = {9, 10, 11}

def paw(pet, name, ft, i):
    if pet == "sparky":
        return SPARKY[i].get(name)
    key = ft.get("follow", name)
    dx, dy, _ = tracks[pet][key][i]
    return ft["x"] + dx, ft["y"] + dy

def shoe_image(view, width, flip, rot):
    v = VIEWS[view]
    img = v["img"]
    scale = width / img.width
    h = max(1, round(img.height * scale))
    # Box-filter down then snap alpha hard, so edges stay crisp on the
    # pixelated renderer instead of feathering into the backdrop.
    small = img.resize((width, h), Image.BOX)
    ax, ay = v["anchor"][0] * scale, v["anchor"][1] * scale
    if flip:
        small = small.transpose(Image.FLIP_LEFT_RIGHT)
        ax = width - ax
    if rot:
        # rotate around the bottom-centre so the sole stays planted
        small = small.rotate(rot, resample=Image.NEAREST, expand=True)
    arr = np.asarray(small).copy()
    arr[..., 3] = np.where(arr[..., 3] >= 128, 255, 0)
    return Image.fromarray(arr), scale, (ax, ay)

def build(pet, cfg):
    sheet = Image.open(cfg["src"]).convert("RGBA")
    fw, fh = sheet.width // 12, sheet.height
    out = Image.new("RGBA", sheet.size, (0, 0, 0, 0))
    track = dict(form=cfg["form"], sheet=cfg["src"], frame_size=[fw, fh],
                 template=tpl["template"], frames=[])
    for i in range(12):
        frame = sheet.crop((i * fw, 0, (i + 1) * fw, fh))
        behind = Image.new("RGBA", (fw, fh), (0, 0, 0, 0))
        front = Image.new("RGBA", (fw, fh), (0, 0, 0, 0))
        bare = (SPARKY_BARE if pet == "sparky" else cfg["bare"]).get(i, [])
        entries = []
        for name, ft in cfg["feet"].items():
            p = paw(pet, name, ft, i)
            if name in bare or p is None:
                entries.append(dict(foot=name, visible=False))
                continue
            cx, by = p
            layer = ft["layer"]
            if pet == "sparky" and i in SPARKY_HIND_FRONT:
                layer = "front"
            width, view = ft["width"], ft["view"]
            if pet == "sparky" and i in SPARKY_HIND_FRONT:
                width, view = 64, THREEQ
            img, scale, (ax, ay) = shoe_image(view, width, ft.get("flip", False), ft.get("rot", 0))
            left = round(cx - ft["fx"] * img.width)
            top = round(by + 2 - img.height)
            (behind if layer == "behind" else front).alpha_composite(img, (left, top))
            entries.append(dict(foot=name, visible=True, view=view,
                                view_name=VIEWS[view]["name"],
                                anchor=[round(left + ax), round(top + ay)],
                                scale=round(scale, 4), rotation=ft.get("rot", 0),
                                flip=ft.get("flip", False), layer=layer))
        comp = behind.copy()
        comp.alpha_composite(frame)
        comp.alpha_composite(front)
        out.paste(comp, (i * fw, 0))
        track["frames"].append(dict(frame=i, shoes=entries))
    return out, track

os.makedirs(OUT, exist_ok=True)
for pet, cfg in PETS.items():
    img, track = build(pet, cfg)
    img.save(f"{OUT}/{pet}-shoes.png", optimize=True)
    json.dump(track, open(f"{OUT}/{pet}-shoes.json", "w"), indent=1)
    if DEBUG:
        fw, fh = img.width // 12, img.height
        grid = Image.new("RGBA", (4 * fw, 3 * fh), (40, 40, 60, 255))
        d = ImageDraw.Draw(grid)
        for i in range(12):
            fr = img.crop((i * fw, 0, (i + 1) * fw, fh))
            x, y = (i % 4) * fw, (i // 4) * fh
            grid.alpha_composite(fr, (x, y))
            d.rectangle([x, y, x + fw - 1, y + fh - 1], outline=(200, 200, 0, 255))
            d.text((x + 4, y + 4), str(i + 1), fill=(255, 255, 0, 255))
        grid.save(f"{OUT}/{pet}-debug.png")
    print(pet, "ok")
