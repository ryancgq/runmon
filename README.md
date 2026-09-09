# RunPet

A mobile running tracker where real runs level up a virtual pet. GPS tracks
your route, distance becomes XP, and XP grows a creature that evolves through
five forms — and visibly sulks if you stop running.

The entire app is one file: **[`index.html`](index.html)**. No frameworks, no
build step, no server, no account. Open it and it works.

**[Play it →](https://ryancgq.github.io/runmon/)**

---

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

### Swapping in your own art

The built-in vector pets are placeholders. Any species and stage can be
replaced with a horizontal sprite sheet, from **Settings → Sprite packs** (pick
a file, set frames and FPS, watch the live preview) or from the console:

```js
RunPet.setSprite("ember", 2, {
  src: "art/blazewyrm.png",     // URL, relative path or data: URI
  frames: 6,                    // frames laid out left to right
  fps: 8,
  moods: { sad: 1, asleep: 2 }  // optional: one sheet row per mood
});

RunPet.clearSprite("ember", 2); // back to the vector art
RunPet.listSprites();
```

A registered sheet replaces the vector pet everywhere — home, evolution tree,
summary, species picker — and is saved with the rest of your game. Nothing else
needs changing.

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
`RunPet.xpTable()` prints the whole curve in the console.

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
RunPet.addRun(9.5, 52, 0);  // km, minutes, days ago
RunPet.state;               // { save, derived }
RunPet.xpTable();
```

## Licence

MIT — see [LICENSE](LICENSE).
