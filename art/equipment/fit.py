"""Place each pet's shoe type on its paws.

Run from the repo root:   python3 art/equipment/fit.py && python3 art/equipment/equip.py

Writes placements.json. Every pet wears the view of shoe-chunky.png drawn for
it (`pet` in shoe-chunky.json), toes to the right as every pet faces right.
Each shoe is sized from the paw it goes on - SIZE x the paw's width, one size
per foot for the whole loop - and placed with its ankle anchor (the middle of
the collar opening) under the middle of the leg and its sole on the paw's
ground line. equip.py then draws the paw's own fur back over the opening, so
the leg goes down into the collar.

Which feet are shod, and how the Cinderling's and Sparky's paws move between
frames, come from mockup-placements.json (where the hand-made mockups put each
shoe). The Bamboo Cub's v3 sheet is pinned, so its paws hold still.
"""
import sys, json, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import equip

P = json.load(open(os.path.join(HERE, 'mockup-placements.json')))
VIEW = {v['pet']: v['index'] for v in equip.tpl['views'] if v.get('pet')}
# shoe width as a multiple of the paw's width
SIZE = {'cinderling': 1.7, 'sparky': 1.5, 'bamboo_cub': 1.2}


def F(name, paw, frames, ref=0, moves=True, dx=0, drop=1):
    """One shod paw: its box (x0, y0, x1, y1) on frame `ref`, the frames and
    foot names that wear it, a nudge of the leg's x from the paw's middle,
    and how far below the paw's bottom the sole sits."""
    return dict(name=name, paw=paw, frames=frames, ref=ref, moves=moves, dx=dx, drop=drop)


ALL, R = range(12), range
GROUPS = {
 'cinderling': [
   # the near hind foot is half behind the near front one: its leg comes down
   # at the back of the paw
   F('hind_near', (94, 262, 130, 291), [(i, 'hind_near') for i in ALL], dx=-6),
   F('front_far', (242, 258, 295, 291), [(i, 'front_far') for i in ALL]),
   F('front_near', (120, 258, 172, 294), [(i, 'front_near') for i in ALL])],
 'sparky': [
   F('hind_near', (125, 293, 170, 330), [(i, 'hind_near') for i in R(9)]),
   F('front_far', (246, 297, 292, 333), [(i, 'front_far') for i in R(9)]),
   F('front_near', (183, 297, 228, 333), [(i, 'front_near') for i in R(9)]),
   F('hind_far_eat', (240, 300, 292, 336), [(i, 'hind_far') for i in R(9, 12)], ref=9),
   F('hind_near_eat', (150, 300, 200, 336), [(i, 'hind_near') for i in R(9, 12)], ref=9)],
 'bamboo_cub': [
   # lying down, frames 1-6 (frame 6 lifts the middle paw to wave)
   F('hind_near', (24, 258, 98, 297), [(i, 'hind_near') for i in R(6)], moves=False),
   F('front_near', (84, 256, 150, 299), [(i, 'front_near') for i in R(5)], moves=False),
   F('front_far', (152, 258, 228, 297), [(i, 'front_far') for i in R(6)], moves=False),
   # sitting up, frames 7-12: the hind feet, front paws round the bamboo
   F('hind_near_sit', (22, 240, 100, 300), [(i, 'hind_near') for i in R(6, 12)], ref=6, moves=False),
   F('hind_far_sit', (158, 240, 234, 300), [(i, 'hind_far') for i in R(6, 12)], ref=6, moves=False)],
}


def mock(pet, i, name):
    return next(s for s in P[pet][i] if s['foot'] == name)


result = {pet: [list() for _ in range(12)] for pet in GROUPS}
for pet, groups in GROUPS.items():
    _, _, ol = equip.PETS[pet]
    fh = equip.Image.open(equip.PETS[pet][1]).height
    view = VIEW[pet]
    v = equip.VIEWS[view]
    afrac = v['anchor'][0] / v['img'].width
    aspect = v['img'].height / v['img'].width
    for g in groups:
        x0, y0, x1, y1 = g['paw']
        w = round((x1 - x0) * SIZE[pet])
        h = round(w * aspect)
        rname = next(n for i, n in g['frames'] if i == g['ref'])
        for i, name in g['frames']:
            ddx = ddy = 0
            if g['moves']:
                a, b = mock(pet, i, name), mock(pet, g['ref'], rname)
                ddx, ddy = a['left'] - b['left'], a['bottom'] - b['bottom']
            cx = (x0 + x1) / 2 + ddx + g['dx']
            result[pet][i].append(dict(foot=name, view=view, left=round(cx - afrac * w),
                                       bottom=min(y1 + ddy + g['drop'], fh - ol),
                                       width=w, height=h, leg=[0, 10000]))
        print(f'{pet:11s} {g["name"]:14s} {v["name"]:15s} paw {x1 - x0}px -> shoe {w}x{h}')

# back to front: the mockup's order where it has one, else left to right
for pet in result:
    for i in range(12):
        order = [s['foot'] for s in P[pet][i]] if pet in P else []
        result[pet][i].sort(key=lambda s: (order.index(s['foot']) if s['foot'] in order else 99, s['left']))

with open(os.path.join(HERE, 'placements.json'), 'w') as f:
    f.write('{\n' + ',\n'.join('"%s": [\n' % k + ',\n'.join('  ' + json.dumps(fr) for fr in v) + '\n]'
                               for k, v in result.items()) + '\n}\n')
