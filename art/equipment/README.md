# Pet footwear (preview only)

`shoe-runner.png` is a 2x2 atlas of one shoe drawn from four angles, described
by `shoe-runner.json` (template `pet-footwear-v1`). Future shoes keep the same
view order and cell size so they drop into the same placements.

`placements.json` says, for every frame of the Cinderling, Sparky and Bamboo
Cub (v3 sheet), which feet are shod and how: the atlas view, mirroring, the
box the shoe fills, and where the leg goes in. `fit.py` writes it:

- each shoe is the smallest that hides 95% or more of its paw in every frame
  (and at least 15% bigger than the mockup's), one size per foot for the loop
- views follow the feet: side view for the dragon's; three-quarter for the
  squirrel's, which point at the viewer - every shoe toe to the right, as
  each pet faces right
- the Bamboo Cub (v3) is placed exactly as its mockup puts the shoes: low
  side-view shoes about the size of each paw, the paw's fur left showing
  above and coming down into the collar
- a side or three-quarter shoe is placed by its ankle anchor under the leg
- which feet are shod, and how the dragon's and squirrel's paws move, come
  from `mockup-placements.json` (the hand-made mockups); the v3 cub is pinned

`equip.py` then draws the leg back over each view's `leg_opening` (in
`shoe-runner.json`), so the leg goes down into the collar with a little
shadow on the rim, instead of the shoe sitting on top of the paw. Anything a
pet holds in front of its feet (the cub's bamboo) stays in front of the shoes. A new shoe
needs its own `leg_opening` per view, or it will look stuck on.

`equip.py` renders those placements and writes, to `preview/`:

- `<pet>-shoes.json` - the attachment track: per frame and foot, the view,
  where its ankle anchor lands on the frame, [x, y] scale, rotation, flip,
  layer, draw order and whether the foot is shod.
- `<pet>-shoes.png` - the pet's 12-frame strip with the shoes composited on,
  same size and framing as the original sheet.

```
python3 art/equipment/fit.py            # placements.json from the mockups
python3 art/equipment/equip.py          # add --debug for a 4x3 contact sheet
```

Nothing here is wired into the app yet - the original sheets are untouched.
