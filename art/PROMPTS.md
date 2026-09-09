# Generation prompts

Paste **Subject** + **Size in frame** for the pet you want, then the whole
**Sheet block** underneath it, unchanged. The sheet block is the same every
time; only the two lines above it change.

The engineering half of [`../ART-SPEC.md`](../ART-SPEC.md) — exact canvas
pixels, baseline coordinates, colour counts, file size — is deliberately *not*
in here. An image model cannot act on `y = 264`, and asking dilutes the
constraints it can act on. Those are handled during conversion instead.

---

## Sheet block — for any pet with a face

```
SHEET FORMAT
Pixel art sprite sheet: 12 frames in a 3x4 grid, 3 columns by 4 rows, read
left to right then top to bottom. Every frame the same size, the creature
drawn at the same scale and in the same spot in each one, its feet resting on
a single shared horizontal line so it never drifts up or down between frames.
Three-quarter side view throughout. Same character, same palette, same
silhouette in all twelve frames — only the face and small details change.

BACKGROUND
Fully transparent. No scenery, ground, floor, grass, rocks, sky or horizon.
No shadow cast beneath the creature. No borders, gutters, panels or labels
dividing the cells. If transparency is not available, use flat magenta
#FF00FF and nothing else behind the creature.

STYLE
Hard-edged pixels. No anti-aliasing, no blur, no soft gradients along the
outline. Limited flat palette, no dithering. Chunky readable shapes — the
face must stay legible when the sprite is shown small.

EXPRESSIONS, in this exact order
 1-2   delighted — biggest grin, wide bright eyes, most energy
 3-4   happy — warm closed-mouth smile
 5-6   neutral and curious — glancing around
 7-8   bored — half-lidded eyes, unimpressed
 9-10  sad or sulking — downcast
11-12  asleep — eyes shut, slumped, still
Each numbered pair is nearly the same drawing twice: the second frame differs
only by a blink, a breath, or a small ear or tail movement.

AVOID
Backgrounds of any colour, ground or terrain, cast shadows, cell borders,
text, frame numbering, watermarks, a border around the whole sheet, and any
change of camera angle or creature size between frames.
```

## Sheet block — for the three egg forms

Eggs have no face, so they get motion instead of expressions, and need fewer
frames. Everything else is identical.

```
SHEET FORMAT
Pixel art sprite sheet: 8 frames in a 4x2 grid, 4 columns by 2 rows, read
left to right then top to bottom. Every frame the same size, the egg at the
same scale and in the same spot, resting on a single shared horizontal line.

BACKGROUND
Fully transparent. No scenery, ground, floor, sky or horizon. No shadow
beneath the egg. No borders, gutters, panels or labels between cells. If
transparency is not available, use flat magenta #FF00FF and nothing else.

STYLE
Hard-edged pixels. No anti-aliasing, no blur, no soft gradients along the
outline. Limited flat palette, no dithering.

MOTION, in this exact order
1-2  at rest, faint inner light
3-4  the inner light swells and brightens
5-6  a sharp wobble, shell strained, light at its brightest
7-8  settling back to rest, light fading

AVOID
Backgrounds of any colour, ground, cast shadows, cell borders, text,
watermarks, hatching or breaking open, and any change of egg size between
frames.
```

---

## Subjects

Size in frame is what makes evolution read as growth: they all display in the
same box, so a later form must fill more of it.

### Ember — fire, aggressive and energetic

Warm reds and oranges, dark charcoal horns and wings, glowing amber highlights.

| Form | Subject line | Size in frame |
| --- | --- | --- |
| 1 · Cinder Egg | `SUBJECT: a dark obsidian egg veined with glowing molten cracks, a small flame flickering at its tip, heat radiating from the shell` | fills ~55% of frame height |
| 2 · Cinderling | *done* — `art/ember-cinderling.png` | ~70% |
| 3 · Blazewyrm | `SUBJECT: a young fire drake, round body but longer neck, small wings that now work, two curved dark horns, a flame-tipped tail, hot-tempered` | ~80% |
| 4 · Pyrelord | `SUBJECT: a full-grown fire drake, broad spread wings, a glowing molten core in its chest, heavy horns, air shimmering with heat around it` | ~90% |
| 5 · Infernarch | `SUBJECT: a regal fire dragon crowned in living flame, wide wings, blazing chest core, orbiting embers, imperious` | ~95% |

### Verdant — forest, calm and glowing

Mossy greens, warm bark browns, pale glowing yellow-green light.

| Form | Subject line | Size in frame |
| --- | --- | --- |
| 1 · Seedpod | `SUBJECT: a dormant seed pod wrapped in moss, faint green light leaking from the seams, a single small sprout at its top` | fills ~55% |
| 2 · Sproutling | `SUBJECT: a soft round forest spirit under an oversized leaf hat, big glowing eyes, tiny leaf-tipped tail, smells of rain` | ~70% |
| 3 · Fernkin | `SUBJECT: a young forest spirit with small twig antlers, a moss cloak over its shoulders, glowing eyes, a single fern frond behind one ear` | ~80% |
| 4 · Thicketmane | `SUBJECT: a forest guardian with broad antlers heavy with leaves, a thick moss mantle, small flowers opening along the antlers, a glowing rune on its chest` | ~90% |
| 5 · Grovewarden | `SUBJECT: an ancient forest warden, a crown of antlers in blossom, moss robes, a bright green heartlight in its chest, leaves drifting around it` | ~95% |

### Nimbus — storm, playful and sparky

Cloud whites and cool blue-greys, bright yellow lightning, no ground contact.

| Form | Subject line | Size in frame |
| --- | --- | --- |
| 1 · Static Egg | `SUBJECT: an egg wrapped tightly in cloud, small arcs of blue and yellow static crackling across the shell` | fills ~55% |
| 2 · Puffling | `SUBJECT: a small giggling scrap of storm cloud with a lightning-bolt tail, blushing cheeks, hovering just above the line rather than resting on it` | ~70% |
| 3 · Zephyrite | `SUBJECT: a young storm sprite with bolt-shaped wings, a fluffy cloud body, far too much energy, floating` | ~80% |
| 4 · Tempestor | `SUBJECT: a rolling storm front with a face, dark cloud mane, lightning arcing from its flanks, a glowing core, floating` | ~90% |
| 5 · Thunderarch | `SUBJECT: a crowned storm head, a jagged lightning crown, dark thunderhead body, a brilliant core, its own lightning orbiting it, floating` | ~95% |

Nimbus forms float, so "feet on a shared line" becomes "the **lowest point** of
the cloud on a shared line" — the rule is that nothing drifts vertically
between frames, not that it touches the ground.

---

## Check the output before sending it

The prompt cannot enforce these, and they are the usual failures:

- **Count the frames.** Models routinely produce 11 or 13.
- **Feet on one line.** The most common defect, and the one already visible in
  the shipping Cinderling — flip between frames and watch for the creature
  jumping up and down.
- **Real transparency.** A checkerboard in a preview usually means alpha, a
  flat white or black square usually means none.
- **Same creature throughout.** Compare the first and last frame for a drifting
  size, palette or camera angle.

Canvas pixels, colour count and file size need no checking — conversion
normalises all three.
