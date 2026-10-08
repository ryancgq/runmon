# Pet footwear (preview only)

`shoe-runner.png` is a 2x2 atlas of one shoe drawn from four angles, described
by `shoe-runner.json` (template `pet-footwear-v1`). Future shoes keep the same
view order and cell size so they drop into the same placements.

`placements.json` says, for every frame of the Cinderling, Sparky and Bamboo
Cub, which feet are shod and the box each shoe fills (left, bottom, width,
height, atlas view), back to front. `fit.py` writes it from
`mockup-placements.json` - where the hand-made mockups of each pet put the
shoes - by sizing every shoe up until it swallows its paw:

- at least 15% bigger than the mockup's shoe, and big enough to hide 95% or
  more of the paw in every frame, so no claw, pad or paw fur shows around it
- the paw sits a third of the way along the shoe, so the leg drops into the
  collar and the toe runs ahead
- one size per foot for the whole loop, so a shoe never pulses
- frame-to-frame motion and which feet are shod are the mockup's: every shoe
  is the side view in front of the pet; Sparky's front paws go bare while
  they hold the acorn, the cub's while it eats

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
