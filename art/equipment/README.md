# Pet footwear (preview only)

`shoe-runner.png` is a 2x2 atlas of one shoe drawn from four angles, described
by `shoe-runner.json` (template `pet-footwear-v1`). Future shoes keep the same
view order and cell size so they drop into the same tracks.

`equip.py` fits the shoe to the three hatchlings and writes, to `preview/`:

- `<pet>-shoes.json` - the attachment track: per frame and per foot, the view
  used, where its ankle anchor lands on the frame, scale, rotation, flip, layer
  (`behind` the pet or in `front` of it) and whether the foot is shod.
- `<pet>-shoes.png` - the pet's 12-frame strip with the shoes composited on,
  same size and framing as the original sheet.

```
python3 art/equipment/equip.py          # add --debug for a 4x3 contact sheet
```

Paw positions: the Cinderling and Bamboo Cub are tracked from frame 1 by
template matching (`paw-tracks.json`); Sparky's are placed by hand in
`equip.py`, because its sheet reframes between rows and its paws look alike.

Nothing here is wired into the app yet - the original sheets are untouched.
