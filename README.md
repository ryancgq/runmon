# Runmon

A mobile running tracker where real runs level up a virtual pet. GPS tracks
your route, distance becomes XP, and XP grows a creature that evolves through
five forms — and visibly sulks if you stop running.

The entire app is one file, `index.html`. No frameworks, no build step, no
server, no account. Open it and it works.

## ▶ [Play it](https://ryancgq.github.io/runmon/) &nbsp;·&nbsp; 🎮 [Open the sandbox](https://ryancgq.github.io/runmon/demo.html)

Those two links open the running app. *Play it* is the real game; *the sandbox*
lets you jump to any of a pet's five forms in one tap, change its mood and log
runs instantly, on a save slot of its own.

Filenames below in `code style` are files in this repository — browse them in
the file list above, not by following a link that looks like the app.

---

## Demo build

**→ https://ryancgq.github.io/runmon/demo.html**

The same app, with shortcuts for looking at artwork and pacing without running
for it. It uses its own save slot (`runmon.demo.v1`), so nothing you do there
touches a real pet.

Tap the **DEMO** badge above the tab bar. It shows all five forms of the pet
you are on — **tap any of them to jump straight there**, no running required.
Below that: log a run, learn the next skill, skip a day (which walks the pet
down through all six moods), or start over and pick a different pet.

Starting a run in the sandbox runs it for you. The simulated runner covers
ground forty times as fast as a real one, and Settings → Tracking winds the
run's clock forward on top of that (1×, 10×, 30× or 60×), so seconds of
watching are worth tens of kilometres — fifteen seconds at 60× is a hundred
kilometres and a level-15 pet. The pace it records is deliberately inhuman;
real runs are never sped up.

Pets with pixel art so far are **Ember** (baby and teen) and **Verdant** (baby).
Everything else is still placeholder vector art.

Under the hood the demo is `index.html?demo=1` — the same file, one flag, no
second copy to keep in sync. `demo.html` is just a small launcher page.

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

The Cinderling and the Blazewyrm (Ember, stages 2 and 3) ship as pixel art in
[`art/ember-cinderling.png`](art/ember-cinderling.png) and
[`art/ember-blazewyrm.png`](art/ember-blazewyrm.png) — 12-frame loops at 2 fps
— and the Bamboo Cub (Verdant, stage 2) in
[`art/panda-cub.png`](art/panda-cub.png). The rest are inline SVG.

Note that this pet plays one continuous loop rather than a per-mood animation,
so its face cycles through every expression regardless of how recently you ran.
The engine still supports mood rows (`moods` below); this sheet just does not
use them.

## Skills

A form is not the end of a stage, it is the start of one: a pet keeps learning
inside the form it grew into. The Blazewyrm (Ember, stage 3) learns all three
of its moves between level 15, where the form arrives, and level 30, where the
next one does.

| Skill | Learns at | What it does |
| --- | --- | --- |
| 🔥 Fireball | Level 18 | Draws a breath and spits a packed ball of flame |
| 💥 Flame Stomp | Level 22 | Lands hard enough to throw a ring of fire out around it |
| ☄️ Flying Swoop | Level 26 | A low, fast pass trailing fire |

Learning one is called out on the run summary that earned it. After that the
move shows up as a chip under the pet — tap a chip, or the pet itself, to play
it. Evolution lists all three with the level each needs, and tapping a learnt
one there plays it on the pet screen.

The Blazewyrm also has a level-up celebration: gold energy winds up, bursts,
and the dragon opens its eyes on the other side of it. It plays on the pet
screen rather than over the run summary — you read the run's numbers first,
then come home to the pet that grew — and only for a run that actually earned
a level. `LEVEL_UP_ART` keys it by species and stage, so it belongs to the
form it was drawn for and another form simply has none until one is drawn.

Each of these is a 16-frame sheet that plays once and hands the stage back to
the idle loop. The movement is drawn into the frames, so the app never moves the sprite
itself; every frame is cropped from one rectangle to keep that motion intact.
`SKILLS` in `index.html` holds the whole definition, sprite geometry included —
`dx` and `dy` nudge a sheet so its ground line sits exactly where the idle
pet's does.

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
  (the sandbox's simulated runner raises that ceiling in step with its own
  speed, so its fixes are not thrown away as teleports)
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
