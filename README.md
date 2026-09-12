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

**Test animations** is the one that levels nothing. It opens a panel that does
not dim the screen, so the pet stays in view above it while you tap through
every animation the app has: fifteen idles across all three species, the egg's
three crack phases, six moods, four skills, four level-up celebrations — each
with its full wind-up, burst and caption — and the confetti, the caption and
the wind-up on their own. The pet is painted straight onto the stage and the
celebrations run without a level to spend, so you can watch a Blazewyrm's
celebration while your own pet is still an egg and its save comes out exactly
as it went in. The panel lists itself from `DEFAULT_SPRITES`, `SKILLS` and
`LEVEL_UP_ART`, so new art turns up in it without being registered twice.

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

The Cinder Egg is a sprite too, as of the pack that replaced the vector one.
It arrived as a 3x4 grid on a checkerboard baked into the pixels rather than
real transparency, so the pattern was keyed out and the rim decontaminated —
every edge pixel is background mixed into art, so the art colour is recovered
from the nearest solid pixel and the mix ratio becomes the alpha. Flood the
background in from the border rather than keying every neutral pixel, or the
white highlight on the shell goes with it.

The egg cracks as it levels. It is the one form whose art changes inside its
own stage — intact at level 1, a first split at 2, a full web at 3 — and the
crack is the level-up celebration: `ember:0@2` and `ember:0@3` in
`LEVEL_UP_ART` carry the shell from one phase to the next and end on the frame
the new idle opens with, so the celebration and the change of art are one
event. While a level-up is armed the pet is still drawn as it was *before* it,
or you would come home to an already cracked shell and then watch it crack.

Those clips sit inside the same timing template as every other celebration, but
the egg's decisive crack lands on frame 9 of 12, leaving no frames for a
settle. That time goes to the final hold instead — the shell sits there split
open while **Level Up!** arrives — so the clip still runs to 2250ms and the
caption still lands at 1380ms, the same as every other form's.

All five phases — three idles and two transitions — are packed to one
silhouette size and one position. The packs draw each row of their grid 4 to 6%
larger than the last, which unpacked would make the egg swell through its loop
and jump at every handover between phases. Normalised, the ground line moves
1.5 CSS px across all sixty frames. Scale is set so the shell has the same
painted area as the Cinderling that hatches from it — the vector egg it
replaced had that relationship, and losing it makes the egg look bigger than
the creature inside.

The Cinderling's idle is the fuzzy baby that matches its skill and
celebration packs. Its frames are anchored before packing — each shifted so
the dragon's feet land on one row and its body on one column — because the
source cells draw it in a different spot each frame and a pet that wanders
inside its own box looks like it is hopping about. Anchor on the dragon, not
on everything opaque: the butterfly is meant to move.

Anchoring is not only an idle's problem. The packs arrive as 4×4 grids, and
some of them draw each row a little higher than the last — the Cinderling's
fireball climbs 43px over its sixteen frames, the Blazewyrm's celebration
55px, which is a pet visibly floating up off its own ground line and then
dropping back when the idle returns. Measure it by cross-correlating each
frame's body against the first frame's rather than by its lowest pixel: a
lowest pixel is a toe on one frame and a smoke puff or a ray on the next,
while the correlation reports whole-body movement. Its signature is
unmistakable — every frame inside a row agrees to a pixel, and the rows step.
Real animation never lines up that neatly, so what steps between rows gets
corrected and what moves inside a row is left exactly as drawn. A clip whose
movement is genuine — the flame stomp's rear-and-land, the flying swoop's
pass — shows no such pattern and must not be touched.

 The smoother original it replaced is kept beside it at
`art/ember-cinderling-original.png` — point the `ember:1` src back at that
file, with `aspect:1.447, fps:2, scale:1.2` and no `dx`/`dy`, to return to it.

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
inside the form it grew into. The Cinderling has one move, and the Blazewyrm
learns all three of its own between level 15, where the form arrives, and
level 30, where the next one does.

| Skill | Form | Learns at | What it does |
| --- | --- | --- | --- |
| 🔥 fireball | Cinderling | Level 8 | Sold as the strongest fire you will ever see. Three seconds of winding up, then a cough and some smoke. |
| 🔥 Fireball | Blazewyrm | Level 18 | Draws a breath and spits a packed ball of flame |
| 💥 Flame Stomp | Blazewyrm | Level 22 | Lands hard enough to throw a ring of fire out around it |
| ☄️ Flying Swoop | Blazewyrm | Level 26 | A low, fast pass trailing fire |

A move belongs to the form that learnt it and retires with that form — the art
is that body's, so a Blazewyrm does not fizzle. Evolution still lists an
outgrown move, marked as such.

Learning one is called out on the run summary that earned it. After that the
move shows up as a chip under the pet — tap a chip, or the pet itself, to play
it. Evolution lists all three with the level each needs, and tapping a learnt
one there plays it on the pet screen.

The Cinderling and the Blazewyrm each have a level-up celebration of their
own, and it is in two halves. The
anticipation is motion, not frames: the pet shivers harder and harder while
its glow swells, for 1.5s, driven entirely by CSS. Only then does the sheet
take over — gold gathering and quickening, the burst, then the settle — with
the glow easing out across the sheet's own wind-up so one hands to the other
rather than restarting.

A gold **Level Up!** lands as the burst resolves, rides the settle and lifts
away — timed off the sheet's own frame list rather than a fixed delay, so it
still lands on the right beat if those holds are ever retuned. It sits above
the pet's right shoulder, clear of it and of the burst going off underneath,
and scales from that corner so the bounce never runs off the edge. Each form
places it: the stage's own corner suits the Blazewyrm, which fills 158px of
the 143px box, but strands the words out in the dark beside the Cinderling,
which only draws 130px. A `cap` on the celebration's config brings them in, so
the caption sits the same distance off the art whatever is wearing it.

The wind-up in front of the sheet plays over the idle, so the idle holds its
first frame while it braces — the Cinderling's has a butterfly wandering
through four of its twelve frames, and a celebration is no place for it. That
frame is also the one every celebration sheet opens on, so the handover lands
on the pose it left.

Every celebration runs to one template, `LEVEL_UP_TIMING`, so a level-up feels
the same whichever pet you are watching: 1.5s of CSS wind-up, then a held lead,
650ms or so of gold gathering and quickening, the flash at 810ms into the
sheet, an easing settle, and **Level Up!** at 1380ms. A sheet does not carry
those sixteen numbers — it names two frames, `gather` (the first frame with
something happening in it) and `burst` (the frame the flash breaks on), and
`levelUpBeats()` stretches each phase across however many frames it was given.

That matters because artists do not pace their sheets alike. The Blazewyrm's
gold starts gathering on frame 2, the Cinderling's not until frame 4 — it
scowls, then shuts its eyes, before anything lights up. Timed off one shared
frame list the Cinderling's build read for 330ms against the Blazewyrm's
650ms: the same clip length, half the anticipation, and it showed. Under the
template its lead snaps by at 80ms a frame and its three build frames hold
214/163/113ms instead of 130/110/90, so the gold gathers for 490ms and the
flash still breaks at exactly 810ms. Adding a celebration is now two numbers
rather than a retuning session.

Splitting it that way is deliberate. Motion stretches to any length, frames do
not: much past 400ms a held frame stops reading as movement and starts reading
as a stutter. So the length lives in `LEVEL_UP_CHARGE_MS` and the drawing lives
in the sheet. The sheet's frames still hold for different lengths — `durations`
in its config lists a hold per frame, and the engine writes those out as a
keyframes rule rather than using `steps()`, which can only hold every frame for
the same time. It plays on the pet
screen rather than over the run summary — you read the run's numbers first,
then come home to the pet that grew — and only for a run that actually earned
a level. `LEVEL_UP_ART` keys it by species and stage, so it belongs to the
form it was drawn for and another form simply has none until one is drawn.

Each of these is a 16-frame sheet that plays once and hands the stage back to
the idle loop, and each carries its own `durations` — the hold per frame. The
packs' own suggested timings are combat speeds; here a move is a performance
you tap to watch, so they run about 1.6 to 2 times longer, with the pacing
shaped to the move: a breath that holds and a release that snaps, a swoop
whose pass stays fast so the dragon does not float, a failed fireball whose
pauses are the joke. Speed lives entirely in the app — a sheet never needs
re-exporting to change it. The movement is drawn into the frames, so the app never moves the sprite
itself; every frame is cropped from one rectangle to keep that motion intact.
`SKILLS` in `index.html` holds the whole definition, sprite geometry included —
`dx` and `dy` nudge a sheet so its ground line sits exactly where the idle
pet's does.

A clip can also name the frames it wants, in any order, with `order` — a beat
is then a frame of that list rather than the next cell along. The Cinderling's
fireball is the reason: its joke only works if you believe it this time, so the
wind-up runs three seconds, three times what it did. Its sheet draws six charge
frames, and holding those half a second each would have read as a stutter
rather than as effort. So it pumps instead — inflate, hold, squash, over and
over and faster each round, then the ember catches and dies twice — out of the
same six cells, with the coughing after it timed exactly as before. No sheet
needs re-exporting to loop a stretch of itself.

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
