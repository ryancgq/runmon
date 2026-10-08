# Pet footwear (preview only)

`shoe-chunky.png` is a 2x2 sheet of one shoe in four types, all side-on with
the toe to the right. `shoe-chunky.json` (template `pet-footwear-v2`) names
each type, the pet it is drawn for, its ankle anchor (the middle of the
collar opening) and its `leg_opening` (the dark collar lining and everything
above it):

| cell | type | worn by |
| --- | --- | --- |
| top left | runner_long | Cinderling |
| top right | runner_low | spare |
| bottom left | runner_compact | Sparky |
| bottom right | runner_round | Bamboo Cub (v3 sheet) |

`fit.py` writes `placements.json`: each shoe sized from the paw it goes on
(1.7x the paw's width on the dragon, 1.5x on the squirrel, 1.2x on the cub),
one size per foot for the loop, its ankle anchor under the middle of the leg
and its sole on the paw's ground line. Which feet are shod, and how the
dragon's and squirrel's paws move, come from `mockup-placements.json`.

`equip.py` draws the shoes and then the pet's own paw back into each collar,
so the fur goes down into the shoe instead of the shoe sitting on top of the
paw. Only the dark collar lining is opened, plus the strip of outline across
the top of the opening where the leg comes in (`leg_opening` just bounds the
search); the outline round the heel tab and tongue is kept, so the collar
has a clean rounded rim rather than a sharp cut. Anything a pet holds in front of its feet (the
cub's bamboo) stays in front of the shoes. It writes to `preview/`:

- `<pet>-shoes.json` - per frame and foot: shoe type, where its ankle anchor
  lands, scale, layer, draw order and whether the foot is shod.
- `<pet>-shoes.png` - the pet's 12-frame strip with the shoes on.

```
python3 art/equipment/fit.py
python3 art/equipment/equip.py          # add --debug for a 4x3 contact sheet
```

A new loot shoe: draw the same four cells (side-on, toe right, dark collar
lining), then find each cell's anchor and opening with
`python3 art/equipment/tools/find_openings.py <sheet.png> <template.json> <debug.png>`,
check the debug image, set each view's `pet`, and point equip.py at it.

`shoe-runner.png/.json` is the first shoe design, kept for reference.

Nothing here is wired into the app yet - the original sheets are untouched.
