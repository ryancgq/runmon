# Pet footwear (preview only)

`shoe-runner.png` is a 2x2 atlas of one shoe drawn from four angles, described
by `shoe-runner.json` (template `pet-footwear-v1`). Future shoes keep the same
view order and cell size so they drop into the same placements.

`placements.json` says, for every frame of the Cinderling, Sparky and Bamboo
Cub, which feet are shod and the box each shoe fills (left, bottom, width,
height, atlas view), back to front. It was fitted to the hand-made mockups of
each pet wearing the shoe:

- every shoe is the side view, toe to the right, in front of the pet
- only the feet you can see are shod - no shoes hidden behind the body
- Cinderling: near hind, far front, near front, all 12 frames
- Sparky: hind plus both front feet; frames 10-12 the front paws hold the
  acorn, so only the two hind feet
- Bamboo Cub: three ground paws in frames 1-5; frame 6 lifts the middle paw;
  frames 7-12 only the outer two while it eats
- each pet keeps its mockup's proportions (Sparky's are chunkier) and gets a
  dark outline to match its own line weight

`equip.py` renders those placements and writes, to `preview/`:

- `<pet>-shoes.json` - the attachment track: per frame and foot, the view,
  where its ankle anchor lands on the frame, [x, y] scale, rotation, flip,
  layer, draw order and whether the foot is shod.
- `<pet>-shoes.png` - the pet's 12-frame strip with the shoes composited on,
  same size and framing as the original sheet.

```
python3 art/equipment/equip.py          # add --debug for a 4x3 contact sheet
```

Nothing here is wired into the app yet - the original sheets are untouched.
