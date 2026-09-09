# Runmon pet art specification

What to produce so a new pet drops into the app with no rework. The worked
example is [`art/ember-cinderling.png`](art/ember-cinderling.png) — the
Cinderling, and the reference every number here is drawn from.

This file is canonical. If anything elsewhere disagrees with it, this wins.

---

## The short version

> A 12-frame looping animation of one creature on a **transparent** background.
> Same canvas every frame, feet on the **same baseline** every frame, no
> scenery. Deliver as an animated GIF with transparency, or a single-row PNG
> strip.

Everything below is detail on those four sentences.

---

## 1. Delivery format

Either is fine. The first is less work for everyone.

**Animated GIF** — 12 frames, 500 ms each, transparent background, looping.
This is exactly what the Cinderling arrived as and it converted cleanly.

**PNG strip** — all 12 frames in a single horizontal row, left to right, each
frame exactly the same width, **no gaps, borders or labels between them**. The
sheet width must divide by 12 with no remainder.

A 3x4 or 4x3 grid also works — it gets re-laid into a strip during conversion.
What cannot be recovered is a baked-in background or inconsistent framing, so
those matter far more than the layout.

## 2. Canvas and framing

| | |
| --- | --- |
| Canvas per frame | **384 x 288 px** (4:3) at 1x |
| Upscaled delivery | any whole multiple — 3x is 1152 x 864 — and say which |
| Baseline (feet) | y = **264** of 288, the same in every frame, +/- 2 px |
| Horizontal | body centred on x = 192; companions may sit in the margins |
| Creature height | ~70% of canvas for a baby form, rising to ~95% for a final form |

**The baseline is the rule most worth obeying.** In the current Cinderling the
feet sit anywhere from y 229 to y 263 — a 34 px swing, 13% of the canvas — so
the pet visibly hops between frames. Locking the baseline is the single largest
quality gain available on the next sheet.

Let the creature grow across its five stages. They all display in the same box,
so the only way evolution reads as growth is a later form filling more of the
frame than an earlier one.

## 3. Frames, order and timing

Twelve frames, 500 ms each: a six-second loop at 2 fps.

Order them as **six pairs**, two frames per mood:

| Frames | Mood | Shown when | Read |
| --- | --- | --- | --- |
| 0–1 | elated | ran today | biggest grin, wide eyes, most energy |
| 2–3 | happy | ran yesterday | warm closed smile |
| 4–5 | okay | idle but content | neutral, glancing about, curious |
| 6–7 | bored | 2 days idle | half-lidded, unimpressed |
| 8–9 | sad | 3–4 days idle | downcast — or cross, if the species sulks |
| 10–11 | asleep | 5+ days idle | eyes shut, slack, barely moving |

Within a pair the two frames should differ only slightly — a blink, a breath, a
tail flick. They are a two-frame loop, not two poses.

**Why this order matters.** Played straight through it reads as a lively idle
cycle, which is what the Cinderling does today. But it also means each mood is
a contiguous pair, so making the pet react to your running again is a config
change rather than new artwork. Any other ordering forecloses that.

## 4. Colour, alpha and file size

- **Real alpha.** Transparent background, no scenery, no ground, no cast shadow
  onto anything. The app supplies its own glow and backdrop.
- **Hard edges.** No anti-aliasing or feathering against the background — the
  app renders with `image-rendering: pixelated`, so soft edges turn to mush.
- **64 colours or fewer**, no dithering.
- **Under 200 KB** per finished sheet. The Cinderling is 135 KB; fifteen sheets
  at that size is a ~2 MB site, which is the practical ceiling for a phone.

If the tool needs a background colour behind the transparency, magenta
(`#FF00FF`) is fine — the Cinderling had exactly that and it caused no trouble,
because conversion resamples with nearest-neighbour and never averages that
colour into the edges.

## 5. Pixel grid

If the art is drawn at 1x and upscaled, scale by a **whole number** with
nearest-neighbour, and say which. The Cinderling was 3x, so it reduced to
native resolution losslessly. A fractional or smoothed upscale cannot be
undone, and the sheet ends up soft.

## 6. Naming

`art/<species>-<form>.png`, lowercase, hyphenated — `art/verdant-sproutling.png`.

## 7. The fifteen sheets

Three species, five forms each. Stage 1 is the starting form and stage 5 the
final one, unlocking at levels 1, 5, 15, 30 and 50.

| # | Ember — fire | Verdant — forest | Nimbus — storm |
| --- | --- | --- | --- |
| 1 | Cinder Egg | Seedpod | Static Egg |
| 2 | **Cinderling** ✅ | Sproutling | Puffling |
| 3 | Blazewyrm | Fernkin | Zephyrite |
| 4 | Pyrelord | Thicketmane | Tempestor |
| 5 | Infernarch | Grovewarden | Thunderarch |

Egg forms need far less than twelve frames — a pulse, a wobble, a crack. Four
frames is plenty; supply what the form needs and say how many.

Species should stay recognisably themselves across all five forms: same palette
family, same silhouette language, same eyes. Ember reads as fire, Verdant as
growing things, Nimbus as weather.

## 8. Wiring one in

Drop the file in `art/` and register it:

```js
Runmon.setSprite("verdant", 1, {
  src: "art/verdant-sproutling.png",
  frames: 12,
  fps: 2,
  aspect: 1.333,   // frame width / height
  scale: 1.2       // display tuning; nudge until it sits well
});
```

Or use **Settings → Sprite packs**, which has a live preview. Two frames of a
pet side by side in that preview means the frame width is wrong.

To make a sheet mood-reactive instead of one continuous loop, it needs six rows
of two frames rather than one row of twelve — the same art, re-laid.

## 9. What actually went wrong before

Real problems from the first two rounds, worth avoiding:

| Problem | Consequence |
| --- | --- |
| Background baked into the frames | Had to be flood-filled out; left flecks of forest floor stuck to the outline |
| Frames on separate scenery tiles | Cell borders and ground fragments survived the cut |
| Feet not on a common baseline | The pet hops 34 px between frames — still visible today |
| Uneven frame widths, or gutters | Frames land half-and-half; you see two half-pets at once |
| Soft or anti-aliased edges | Fringing once the app renders it pixelated |

## 10. A prompt that works

For image tools, adapt this — it is close to what produced the Cinderling:

> Pixel art sprite sheet of a *[species description]*, 12 frames arranged in a
> 3x4 grid, each frame the same size with the creature in the same position and
> its feet on the same line. Fully transparent background, no scenery, no
> ground, no borders between frames. Expressions in order: delighted (x2),
> happy (x2), neutral curious (x2), bored half-lidded (x2), sad (x2), asleep
> eyes-closed (x2). Limited palette, hard pixel edges, no anti-aliasing.

Then export as a transparent animated GIF at 500 ms per frame, or hand over the
grid as a PNG. Both convert.
