"""Size every shoe so it swallows its paw.

Run from the repo root:   python3 art/equipment/fit.py && python3 art/equipment/equip.py

Starts from mockup-placements.json (where the hand-made mockups put each shoe)
and writes placements.json. For each foot it picks the smallest shoe - one
size for the whole loop, so it never pulses - that is at least GROW x the
mockup's and hides at least THR of the paw's pixels in every frame, with the
paw at fraction fx of the shoe's width so the leg drops into the collar and
the toe runs ahead. Frame-to-frame motion is the mockup's.
"""
import sys, json, itertools, os
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import equip
THR = 0.95
GROW = 1.15
P = json.load(open(os.path.join(HERE, 'mockup-placements.json')))
SRC = {k: v[1] for k, v in equip.PETS.items()}
OUTL = {k: v[2] for k, v in equip.PETS.items()}
ASPECT = {'cinderling': .55, 'sparky': .72, 'bamboo_cub': .56}
# paw boxes (x0, y0, x1, y1) on the reference frame, and the frames/names
# that wear a shoe on that paw. Positions in other frames follow the
# placement deltas, which came from the mockups and the paw tracks.
GROUPS = {
 'cinderling': [
   ('hind_near', (94, 262, 130, 291), 0, [(i, 'hind_near') for i in range(12)]),
   ('front_far', (242, 258, 295, 291), 0, [(i, 'front_far') for i in range(12)]),
   ('front_near', (120, 258, 172, 294), 0, [(i, 'front_near') for i in range(12)])],
 'sparky': [
   ('hind_near', (125, 293, 170, 330), 0, [(i, 'hind_near') for i in range(9)]),
   ('front_far', (246, 297, 292, 333), 0, [(i, 'front_far') for i in range(9)]),
   ('front_near', (183, 297, 228, 333), 0, [(i, 'front_near') for i in range(9)]),
   ('hind_far_eat', (240, 300, 292, 336), 9, [(i, 'hind_far') for i in range(9, 12)]),
   ('hind_near_eat', (150, 300, 200, 336), 9, [(i, 'hind_near') for i in range(9, 12)])],
 'bamboo_cub': [
   ('hind_near', (30, 272, 105, 327), 0, [(i, 'hind_near') for i in range(12)]),
   ('front_near', (96, 272, 172, 329), 0, [(i, 'front_near') for i in range(5)]),
   ('front_far', (190, 276, 251, 328), 0, [(i, 'front_far') for i in range(6)] + [(i, 'hind_far') for i in range(6, 12)])],
}

def place(pet, i, name):
    return next(s for s in P[pet][i] if s['foot'] == name)

# The dragon's near hind shoe sits behind the near front one: set it further
# back so its heel shows, as in the mockup, rather than a sliver.
FX = {('cinderling', 'hind_near'): (.62, .66, .70)}

result = {pet: [list() for _ in range(12)] for pet in GROUPS}
cache = {}
for pet, groups in GROUPS.items():
    sheet = np.asarray(Image.open(SRC[pet]).convert('RGBA'))
    fw = sheet.shape[1] // 12; fh = sheet.shape[0]
    ol = OUTL[pet]
    for gname, (x0, y0, x1, y1), r0, members in groups:
        ref = place(pet, r0, members[0][1] if members[0][0] == r0 else members[0][1])
        frames = []
        for i, name in members:
            s = place(pet, i, name)
            dx, dy = s['left'] - ref['left'], s['bottom'] - ref['bottom']
            box = (x0 + dx, y0 + dy, x1 + dx, y1 + dy)
            a = sheet[box[1]:box[3], i * fw + box[0]: i * fw + box[2], 3] > 60
            frames.append((i, name, box, a))
        pw, cx = x1 - x0, (x0 + x1) / 2
        # never smaller than GROW x the mockup's own shoe for this foot
        mock = sorted(place(pet, i, n)['width'] for i, n in members)[len(members) // 2]
        best = None
        for w in range(max(int(pw * 1.05), round(mock * GROW)), int(pw * 2.6), 2):
            h = round(w * ASPECT[pet])
            if (w, h, ol) not in cache:
                img, _, _ = equip.shoe(0, w, h, ol)
                cache[(w, h, ol)] = np.asarray(img)[..., 3] > 0
            m = cache[(w, h, ol)]
            for fx, d in itertools.product(FX.get((pet, gname), (.36, .40, .44, .48, .52)), (0, 2, 4, 6)):
                covs = []
                for i, name, (bx0, by0, bx1, by1), a in frames:
                    left = round(bx0 + pw / 2 - fx * w) - ol
                    top = min(by1 + d, fh - ol) + ol - m.shape[0]
                    # shoe mask in box coordinates
                    sub = np.zeros_like(a)
                    ys0, xs0 = max(0, top - by0), max(0, left - bx0)
                    ys1, xs1 = min(a.shape[0], top - by0 + m.shape[0]), min(a.shape[1], left - bx0 + m.shape[1])
                    if ys1 > ys0 and xs1 > xs0:
                        sub[ys0:ys1, xs0:xs1] = m[ys0 - (top - by0):ys1 - (top - by0), xs0 - (left - bx0):xs1 - (left - bx0)]
                    covs.append((a & sub).sum() / max(1, a.sum()))
                if min(covs) >= THR:
                    cand = (w, -np.mean(covs), fx, d)
                    if best is None or cand < best: best = cand
            if best: break
        w, negc, fx, d = best
        print(f'{pet:11s} {gname:14s} paw {pw}px -> shoe {w}px (x{w/pw:.2f}) fx={fx} drop={d} cover={-negc:.3f}')
        for i, name, (bx0, by0, bx1, by1), a in frames:
            result[pet][i].append(dict(foot=name, left=round(bx0 + pw / 2 - fx * w), bottom=min(by1 + d, fh - ol),
                                       width=w, height=round(w * ASPECT[pet]), view=0))
# keep each frame's back-to-front order from the mockup placements
for pet in result:
    for i in range(12):
        order = [s['foot'] for s in P[pet][i]]
        result[pet][i].sort(key=lambda s: order.index(s['foot']))
with open(os.path.join(HERE, 'placements.json'), 'w') as f:
    f.write('{\n' + ',\n'.join('"%s": [\n' % k + ',\n'.join('  ' + json.dumps(fr) for fr in v) + '\n]'
                               for k, v in result.items()) + '\n}\n')
