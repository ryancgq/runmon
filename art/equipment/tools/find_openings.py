# Find each view's collar opening (the dark lining) and write the template.
import json, sys, numpy as np, cv2
from PIL import Image, ImageDraw
from scipy import ndimage
src, out, dbg = sys.argv[1:4]
a = np.asarray(Image.open(src).convert('RGBA'))
H, W = a.shape[:2]; cw, ch = W // 2, H // 2
names = [('side_long', None), ('side_low', 'cinderling'), ('side_chunky', 'sparky'), ('side_round', 'bamboo_cub')]
views = []
canvas = Image.new('RGBA', (W, H), (60, 60, 90, 255)); canvas.alpha_composite(Image.fromarray(a)); d = ImageDraw.Draw(canvas)
for k, (name, pet) in enumerate(names):
    r, c = divmod(k, 2)
    cell = a[r * ch:(r + 1) * ch, c * cw:(c + 1) * cw]
    rgb = cell[..., :3].astype(int); al = cell[..., 3] > 128
    mean = rgb.mean(-1); sat = rgb.max(-1) - rgb.min(-1)
    lining = al & (mean > 12) & (mean < 75) & (sat < 25)
    lining = ndimage.binary_opening(lining, iterations=2)
    lab, n = ndimage.label(lining)
    sizes = ndimage.sum(lining, lab, range(1, n + 1))
    ys_all = np.nonzero(al)[0]; top = ys_all.min()
    # the lining: the biggest dark blob in the shoe's upper half
    best = None
    for i in np.argsort(sizes)[::-1]:
        ys, xs = np.nonzero(lab == i + 1)
        if ys.mean() < top + (ys_all.max() - top) * 0.45:
            best = lab == i + 1; break
    ys, xs = np.nonzero(best)
    # opening = the lining and everything above it in its columns
    m = np.zeros_like(best)
    for x in range(xs.min(), xs.max() + 1):
        col = np.nonzero(best[:, x])[0]
        if len(col): m[:col.max() + 1, x] = True
    m = ndimage.binary_closing(m, iterations=3)
    cs, _ = cv2.findContours(m.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    poly = cv2.approxPolyDP(max(cs, key=cv2.contourArea), 2.0, True)[:, 0].tolist()
    # ankle: the middle of the opening, at the bottom of the lining there
    ax = int(round(xs.mean()))
    ay = int(np.nonzero(best[:, ax])[0].max()) if best[:, ax].any() else int(ys.max())
    views.append(dict(index=k, name=name, pet=pet, rect=[c * cw, r * ch, cw, ch],
                      ankle_anchor=[ax, ay], leg_opening=poly))
    d.polygon([(px + c * cw, py + r * ch) for px, py in poly], outline=(255, 0, 0, 255))
    d.ellipse([ax + c * cw - 6, ay + r * ch - 6, ax + c * cw + 6, ay + r * ch + 6], outline=(0, 255, 255, 255), width=3)
    print(name, pet, 'lining px', int(best.sum()), 'anchor', (ax, ay), 'poly pts', len(poly))
canvas.save(dbg)
tpl = dict(template='pet-footwear-v2', image='shoe-chunky.png', image_size=[W, H],
           grid=dict(columns=2, rows=2, cell_width=cw, cell_height=ch),
           coordinates='Pixels; origin at top-left of each cell; x rightward, y downward.',
           views=views,
           pet='The pet this shoe type is drawn for; null for a spare.',
           ankle_anchor='Middle of the collar opening, at the bottom of its lining: placed under the middle of the leg.',
           leg_opening="Polygon over the collar lining and everything above it. Where the pet's leg crosses it, the leg is drawn over the shoe, so it goes into the collar.")
json.dump(tpl, open(out, 'w'), indent=1)
