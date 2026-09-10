# Runmon

A mobile running tracker where real runs level up a virtual pet. GPS tracks
your route, distance becomes XP, and XP grows a creature that evolves through
five forms — and visibly sulks if you stop running.

The entire app is one file: **[`index.html`](index.html)**. No frameworks, no
build step, no server, no account. Open it and it works.

### ▶ [**Play it**](https://ryancgq.github.io/runmon/) &nbsp;·&nbsp; 🎮 [**Open the demo**](https://ryancgq.github.io/runmon/demo.html)

*Play it* is the real game — you start with an egg. *The demo* skips the egg so
the pixel art is on screen from level 1, and has shortcuts for logging runs and
changing the pet's mood.

---

## Demo build

**→ https://ryancgq.github.io/runmon/demo.html**

The same app with the egg stage skipped, so any pet that has pixel art is on
screen from level 1 instead of level 5. It runs on its own save slot
(`runmon.demo.v1`), so nothing you do there touches a real pet.

Tap the **DEMO** badge above the tab bar. It shows all five forms of the pet
you are on — **tap any of them to jump straight there**, no running required.
Below that: log a run, skip a day (which walks the pet down through all six
moods), or start over and pick a different pet.

Pets with pixel art so far are **Ember** and **Verdant** — pick one of those to
see it at level 1. Nimbus still starts as an egg.

Under the hood the demo is `index.html?demo=1` — the same file, one flag, no
second copy to keep in sync. [`demo.html`](demo.html) is just a small launcher.

## Trying it out

Open the page on a phone and allow location access when it asks. If you are on
a desktop, or indoors without a GPS fix, turn on **Simulated GPS** in Settings
— it fakes a plausible route so you can walk through the whole flow. Runs
recorded that way are tagged `sim` in your history.

Nothing is uploaded anywhere. Your pet, runs, XP and settings live in this
browser's `localStorage`, on this device only. Settings has JSON export and
import if you want to move a save or keep a backup.

## Screens

| Screen | What it does |
| --- | --- |
| **Pet** | The animated pet, its name, level, XP bar, mood, weekly streak strip and recent runs |
| **Run** | Live map, distance, duration, average pace, calories, pause/resume and hold-to-finish |
| **Summary** | Route trace, run stats, a full XP breakdown, animated bar fill, and any level up or evolution |
| **Evolve** | Lifetime stats, the five-stage evolution tree for all three species, and 20 badges |
| **History** | Every run by month, with route thumbnails; tap one to reopen its summary or delete it |
| **Settings** | Units, body weight, simulated GPS, sprite packs, export/import, new game |

## The pets

Three species, five stages each, all drawn as inline SVG and animated in CSS.

- **Ember** (fire) — Cinder Egg → Cinderling → Blazewyrm → Pyrelord → Infernarch
- **Verdant** (forest) — Seedpod → Sproutling → Fernkin → Thicketmane → Grovewarden
- **Nimbus** (storm) — Static Egg → Puffling → Zephyrite → Tempestor → Thunderarch

Your choice sets the app's accent colour. The pet's expression and idle
animation follow how recently you ran: elated the day you run, happy the day
after, restless at two days, sad at three, and asleep from five.

The Cinderling (Ember, stage 2) ships as pixel art in
[`art/ember-cinderling.png`](art/ember-cinderling.png) — a single 12-frame loop
at 2 fps. The rest are inline SVG. Both are placeholders — see below.

Note that this pet plays one continuous loop rather than a per-mood animation,
so its face cycles through every expression regardless of how recently you ran.
The engine still supports mood rows (`moods` below); this sheet just does not
use them.

### Adding a new pet

[`ART-SPEC.md`](ART-SPEC.md) is the production spec for new pet artwork —
canvas, baseline, frame order, palette and file limits, with the Cinderling as
the worked example. Read it before drawing anything.

### Swapping in your own art

Any species and stage can be replaced with a horizontal sprite sheet, from
**Settings → Sprite packs** (pick a file, set frames, FPS and scale, watch the
live preview) or from the console:

```js
Runmon.setSprite("ember", 2, {
  src: "art/blazewyrm.png",     // URL, relative path or data: URI
  frames: 6,                    // frames laid out left to right
  fps: 8,
  moods: { sad: 1, asleep: 2 }  // optional: one sheet row per mood
});

Runmon.clearSprite("ember", 2); // back to the vector art
Runmon.listSprites();
```

A registered sheet replaces the built-in pet everywhere — home, evolution tree,
summary, species picker — and is saved with the rest of your game. Nothing else
needs changing. If the image cannot be fetched, the pet quietly falls back to
vector art rather than showing an empty box.

**Sheet layout.** Frames run left to right. Add `moods` and the sheet becomes a
grid: one row per mood, `frames` columns wide. A 6-row sheet ordered
`elated, happy, okay, bored, sad, asleep` gives the pet a distinct animation per
mood:

| key | what it does |
| --- | --- |
| `frames` | columns in the sheet; each is one animation frame |
| `rows` | rows in the sheet (defaults to what `moods` implies) |
| `moods` | mood name to row index |
| `fps` | playback speed |
| `moodFps` | per-mood speed override, e.g. slow breathing while asleep |
| `aspect` | frame width / height, if the frames are not square |
| `scale` | grow or shrink the pet within its slot |

Frames must be evenly sized with no gutters between them. There is a script-free
way to check yours: register it, then watch the live preview in the editor — if
you see two half-pets, the frame width is off.

## How XP works

**Distance → XP.** 100 XP per kilometre, and later kilometres inside a single
run are worth more than earlier ones. The rate climbs continuously from ×1.0 to
×2.0 at 20 km, so one long run beats the same distance chopped into short ones:
5 km earns 563 XP, but 10 km earns 1,250 rather than 1,126.

**Streaks.** +10% for each consecutive day you run, capped at +50%.

**Levels.** Level 1→2 costs 200 XP and every level costs more than the last.
The growth factor starts at ×1.5 and eases off as levels climb — a flat ×1.5
forever would put level 50 near 2.8×10¹⁰ XP, about a hundred million
kilometres, making the final form unreachable and levels 30–50 dead content.
The curve as tuned:

| Form | Level | Total XP | Roughly |
| --- | --- | --- | --- |
| Baby | 5 | 1,517 | ~13 km |
| Teen | 15 | 20,017 | ~175 km |
| Adult | 30 | 80,489 | ~700 km |
| Final | 50 | 175,228 | ~1,500 km |

`LEVEL_BASE` and `LEVEL_DECAY` near the top of the file control this, and
`Runmon.xpTable()` prints the whole curve in the console.

## How tracking works

- `navigator.geolocation.watchPosition` at high accuracy, plotted live on a
  [Leaflet](https://leafletjs.com/) map (loaded from a CDN)
- Distance between fixes via the Haversine formula
- Fixes worse than 45 m do not extend the route, and worse than 90 m are
  dropped outright, both with an explanation on screen
- The jitter gate scales with reported accuracy instead of using one fixed
  threshold, which would swallow real strides at 1 Hz
- Segments implying more than 12 m/s are treated as GPS jumps and discarded
- Pausing breaks the route into a new segment, so the line does not draw a
  straight jump across wherever you stopped
- Denied permission, unavailable position and weak signal each get their own
  in-context message rather than a silent failure
- If Leaflet or its tiles cannot load, the route still records and draws on a
  canvas fallback
- Calories use the ACSM running equation against the body weight in Settings —
  an estimate, not a measurement

## Data

Everything derives from the run log, so deleting a run correctly rolls back XP,
level, evolution stage, streaks and badges. Routes are simplified to 320 points
before saving to keep `localStorage` small.

## Development

There is nothing to install or build. Edit `index.html` and reload.

Useful console helpers for previewing later stages without running 1,500 km:

```js
Runmon.addRun(9.5, 52, 0);  // km, minutes, days ago
Runmon.state;               // { save, derived }
Runmon.xpTable();
```

## Licence

MIT — see [LICENSE](LICENSE).
