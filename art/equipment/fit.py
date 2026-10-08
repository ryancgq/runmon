"""Size and place every shoe so it is worn, not stuck on.

Run from the repo root:   python3 art/equipment/fit.py && python3 art/equipment/equip.py

Writes placements.json. For each foot it picks the smallest shoe - one size
for the whole loop, so it never pulses - that hides at least THR of the paw in
every frame, is at least GROW x the mockup's shoe for that foot (or, where the
mockup was drawn on an older sheet, PAW_GROW x the paw), and sits with the leg
in its collar: a side-view shoe is placed by its ankle anchor under the leg,
and equip.py then draws the leg back over the collar opening.

Which feet are shod, and how the Cinderling's and Sparky's paws move between
frames, come from mockup-placements.json (where the hand-made mockups put each
shoe). The Bamboo Cub is placed exactly as its mockup (drawn on the v3
sheet) puts the shoes - see EXACT.
"""
import sys, json, itertools, os
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import equip

THR = 0.95
GROW = 1.15
PAW_GROW = 1.25
SIDE, TQ, SOLE = 0, 1, 3
P = json.load(open(os.path.join(HERE, 'mockup-placements.json')))
# height / width each pet's shoes are drawn at; views not listed keep their own
ASPECT = {('cinderling', SIDE): .55, ('sparky', TQ): .72, ('bamboo_cub', SIDE): .66}


def F(name, paw, frames, leg=None, view=SIDE, flip=False, ref=0, moves=True, dx=(-12, -8, -4, 0, 4, 8)):
    """One shod paw: its box (x0, y0, x1, y1) on frame `ref`, the frames and
    foot names that wear it, the x-range of the leg that goes into the collar
    (default: anywhere across the opening, so the heel tab and tongue are what
    close round it), the atlas view and mirroring."""
    return dict(name=name, paw=paw, frames=frames, leg=leg or (0, 10000), view=view,
                flip=flip, ref=ref, moves=moves, dx=dx)


ALL, R = range(12), range
GROUPS = {
 'cinderling': [
   # the near hind shoe sits behind the near front one: anchor it behind the
   # leg so its heel shows rather than a sliver
   F('hind_near', (94, 262, 130, 291), [(i, 'hind_near') for i in ALL], leg=(86, 128), dx=(-24, -20, -16)),
   F('front_far', (242, 258, 295, 291), [(i, 'front_far') for i in ALL], leg=(240, 296)),
   F('front_near', (120, 258, 172, 294), [(i, 'front_near') for i in ALL], leg=(112, 162))],
 'sparky': [
   # the paws stick out under the belly toward the viewer: three-quarter view,
   # the belly fur coming down into the collar
   F('hind_near', (125, 293, 170, 330), [(i, 'hind_near') for i in R(9)], view=TQ),
   F('front_far', (246, 297, 292, 333), [(i, 'front_far') for i in R(9)], view=TQ),
   F('front_near', (183, 297, 228, 333), [(i, 'front_near') for i in R(9)], view=TQ),
   F('hind_far_eat', (240, 300, 292, 336), [(i, 'hind_far') for i in R(9, 12)], view=TQ, ref=9),
   F('hind_near_eat', (150, 300, 200, 336), [(i, 'hind_near') for i in R(9, 12)], view=TQ, ref=9)],
}

# The Bamboo Cub is drawn as in its mockup, which was made on the v3 sheet:
# low side-view shoes, toes right, about the size of the paw, with the paw's
# fur left showing above and coming down into the collar - not grown to hide
# the paw. v3 is pinned, so the boxes hold still. (foot, left, width) per
# frame on the ground line; frame 6 lifts the middle paw to wave, and from
# frame 7 the cub sits up with its front paws round the bamboo.
CUB_LYING = [('hind_near', 21, 62), ('front_near', 83, 60), ('front_far', 166, 64)]
CUB_WAVING = [('hind_near', 21, 62), ('front_far', 166, 64)]
CUB_SITTING = [('hind_near', 21, 62), ('hind_far', 163, 66)]
EXACT = {'bamboo_cub': [(CUB_LYING, 289)] * 5 + [(CUB_WAVING, 289)] + [(CUB_SITTING, 290)] * 6}
ASPECT_OF = lambda pet, view: ASPECT.get((pet, view), equip.VIEWS[view]['img'].height / equip.VIEWS[view]['img'].width)


def mock(pet, i, name):
    return next((s for s in P.get(pet, [[]] * 12)[i] if s['foot'] == name), None)


result = {pet: [list() for _ in range(12)] for pet in list(GROUPS) + list(EXACT)}
cache = {}
for pet, groups in GROUPS.items():
    _, src, ol = equip.PETS[pet]
    sheet = np.asarray(Image.open(src).convert('RGBA'))
    fw, fh = sheet.shape[1] // 12, sheet.shape[0]
    for g in groups:
        x0, y0, x1, y1 = g['paw']
        r0, rname = g['ref'], next(n for i, n in g['frames'] if i == g['ref'])
        frames = []
        for i, name in g['frames']:
            ddx = ddy = 0
            if g['moves']:
                a, b = mock(pet, i, name), mock(pet, r0, rname)
                ddx, ddy = a['left'] - b['left'], a['bottom'] - b['bottom']
            box = (x0 + ddx, y0 + ddy, x1 + ddx, y1 + ddy)
            paw = sheet[box[1]:box[3], i * fw + box[0]: i * fw + box[2], 3] > 60
            frames.append((i, name, box, ddx, paw))
        pw, view = x1 - x0, g['view']
        v = equip.VIEWS[view]
        afrac = v['anchor'][0] / v['img'].width
        if g['flip']:   # mirrored, the anchor is as far from the right edge
            afrac = 1 - afrac
        if g['moves']:
            ws = sorted(mock(pet, i, n)['width'] for i, n in g['frames'])
            floor = round(ws[len(ws) // 2] * GROW)
        else:
            floor = round(pw * PAW_GROW)
        best = None
        for w in range(max(int(pw * 1.05), floor), int(pw * 2.6), 2):
            h = round(w * ASPECT_OF(pet, view))
            key = (view, w, h, ol, g['flip'])
            if key not in cache:
                img, _, _, opening = equip.shoe(view, w, h, ol, g['flip'])
                m = np.asarray(img)[..., 3] > 0
                if opening is not None:
                    m &= ~opening
                cache[key] = m
            m = cache[key]
            for dx, d in itertools.product(g['dx'], (0, 2, 4)):
                covs = []
                for i, name, (bx0, by0, bx1, by1), _, paw in frames:
                    cx = bx0 + pw / 2 + dx
                    if view != SOLE:   # the ankle anchor under the leg
                        left = round(cx - afrac * w)
                    else:              # the sole centred on the paw
                        left = round(cx - w / 2)
                    left -= ol
                    top = min(by1 + d, fh - ol) + ol - m.shape[0]
                    sub = np.zeros_like(paw)
                    ys0, xs0 = max(0, top - by0), max(0, left - bx0)
                    ys1, xs1 = min(paw.shape[0], top - by0 + m.shape[0]), min(paw.shape[1], left - bx0 + m.shape[1])
                    if ys1 > ys0 and xs1 > xs0:
                        sub[ys0:ys1, xs0:xs1] = m[ys0 - (top - by0):ys1 - (top - by0), xs0 - (left - bx0):xs1 - (left - bx0)]
                    covs.append((paw & sub).sum() / max(1, paw.sum()))
                if min(covs) >= THR:
                    cand = (w, abs(dx), -np.mean(covs), dx, d)
                    if best is None or cand < best:
                        best = cand
            if best:
                break
        w, _, negc, dx, d = best
        h = round(w * ASPECT_OF(pet, view))
        print(f'{pet:11s} {g["name"]:14s} {v["name"]:20s} paw {pw}px -> shoe {w}x{h} dx={dx} drop={d} cover={-negc:.3f}')
        for i, name, (bx0, by0, bx1, by1), ddx, _ in frames:
            cx = bx0 + pw / 2 + dx
            left = round(cx - afrac * w) if view != SOLE else round(cx - w / 2)
            s = dict(foot=name, view=view, left=left, bottom=min(by1 + d, fh - ol), width=w, height=h)
            if g['flip']:
                s['flip'] = True
            if v['opening']:
                s['leg'] = [g['leg'][0] + ddx, g['leg'][1] + ddx]
            result[pet][i].append(s)

for pet, frames in EXACT.items():
    for i, (feet, bottom) in enumerate(frames):
        for foot, left, w in feet:
            result[pet][i].append(dict(foot=foot, view=SIDE, left=left, bottom=bottom, width=w,
                                       height=round(w * ASPECT_OF(pet, SIDE)), leg=[0, 10000]))

# back to front: the mockup's order where it has one, else left to right
for pet in result:
    for i in range(12):
        order = [s['foot'] for s in P[pet][i]] if pet in P else []
        result[pet][i].sort(key=lambda s: (order.index(s['foot']) if s['foot'] in order else 99, s['left']))

with open(os.path.join(HERE, 'placements.json'), 'w') as f:
    f.write('{\n' + ',\n'.join('"%s": [\n' % k + ',\n'.join('  ' + json.dumps(fr) for fr in v) + '\n]'
                               for k, v in result.items()) + '\n}\n')
