# Runmon Explore — design

Pets leave the pet screen and walk around a top-down world. They battle the
wild pets they meet, and take swings at the raid boss, Sir Uwaaarghhhh, on his
hill.

This is a **standalone prototype** for phones. It lives in `explore/`, shares
nothing with the game's `index.html`, and never reads or writes a save. Its
job is to show whether the idea works before any of it goes into the game.

## Try it

- **Hosted link:** a private Artifact page built from this folder (see
  [Publishing](#publishing)). Open it on a phone.
- **Locally:** serve the repo root (`python3 -m http.server`) and open
  `/explore/` with a phone-sized window or the device toolbar.
- **Deep links for testing:** `#explore`, `#raid`, `#raid.blazewyrm`,
  `#explore.sparky`.

It is built for phones held upright. On a desktop it draws itself inside a
phone-sized frame, and on a phone held sideways it asks you to turn it back.

---

## 1. Fit with the game

- **Running is still the only way to grow.** Explore earns no XP. A pet's
  level, stats and moves come from its running level, the same as the game.
  The select screen lets you choose a level, but only for testing.
- **Fights are the game's battles.** The same attributes, the same moves, the
  same damage, the same turns. See §3.
- **The raid is the game's raid.** The same boss, art, moves and stats, and the
  same rule that his wounds carry over from one attempt to the next.

## 2. The world

One 84×64-tile map, generated from a fixed seed so it comes out the same every
time.

| Region | Where | Wild pets |
| --- | --- | --- |
| The Trailhead | centre-south, with a campfire | — |
| Verdant Grove | west, moss and bamboo | Bamboo Cub / Panda |
| Ember Crags | east, ash and basalt | Cinderling / Blazewyrm |
| Nimbus Heights | north-west, cloudstone and crystals | Sparky / Zephyrite |
| The hill | north, a ring of standing stones | Sir Uwaaarghhhh |

Wild pets are within a few levels of yours, and their form follows their
level, the same way your pet's does. So there is a fight worth having at any
level you test.

Each species has a temperament:

- **Ember** pets come at you. When one charges, a "!" appears over it, and you
  battle when it reaches you.
- **Nimbus** and **Verdant** pets mind their own business. When you walk up to
  one, a **⚔ Battle** button appears.

**Controls.** Drag anywhere on the lower half of the screen to walk. Everything
else is a button.

## 3. Battles: the game's engine, in the world

When a fight starts, both pets square off where they met, and a sheet slides
up over the bottom of the screen. It holds the game's battle screen, folded
down:

- both pets' health
- status tags straight from the engine (stoked, charged, guard open, burning,
  wide open)
- a line saying what just happened
- your moves, which show "ready in N turns" exactly as the game counts it

**Auto** lets your pet choose, using the game's own chooser. **Run** leaves a
wild battle at any time.

### Why the engine is copied rather than re-imagined

The first version fought in real time. Every move used the game's damage
formula and multipliers, with turns converted to seconds. It did not hold the
balance. Simulated against the game's own engine at levels 12, 26 and 40, the
species matchups came out like this:

| Matchup | Game | Real-time version |
| --- | --- | --- |
| Verdant v Ember | 44–47% | 3–13% |
| Verdant v Nimbus | 52–56% | 23–65% |
| Ember v Nimbus | 47–50% | 20–90% |

Walking into range, closing speed and both sides acting at once all
favour speed and burst in ways a turn-based battle doesn't. So fights now run on
`btSide`, `btHit`, `btAct` and `btChoose`, copied line for line.

Verified:

- **The same seed plays the same fight.** Seed 12345 gives the identical move
  list and final HP in this page and in the game.
- **The win rates match.** Over 4,000 fights per pairing at levels 12, 26 and
  40, every matchup lands at 44–56%, as in the game.

What the world adds is staging only. The attacker plays its real skill clip,
taken from `SKILLS` with its own `order` and `durations` at 0.8× pace. The
hit lands on the clip's impact frame:

- a ring for novas
- a bolt dropping on the target for strikes
- a fireball, acorn or bamboo flying across for shots
- an arc for swipes and lashes
- the gas cloud for Green Gale
- the body crossing to the target and back for rushes
- a lunge for a plain Attack, landing 400 ms in, as on the battle screen

The bars only move when the blow lands, which is the same fix the game's
battle screen needed.

**Winning or losing.** Beat a wild pet and it wanders off, then comes back
later. Lose and you wake at the campfire. Every battle starts at full health,
as every battle in the game does.

## 4. The raid: Sir UwaaarghhhhUWAAGRRHH

Everything about him is the game's:

- his four worn-down sheets, which change at 75%, 50% and 25%
- his three moves, each with its own sheet: **UWAAAARGH!**, **Splitter** and
  **Torchswing**
- his plain swing, a lunge
- the death clip that plays when he falls
- his stats: Power 90, Defence 25, Speed 60, and no extra turns

As in the game:

- You always get the first swing at him.
- An attempt ends when your pet falls.
- His health carries over to the next attempt.
- His bar shows a percentage, so the raw pool number never appears.
- What changes is only where he stands: out on the hill, turned to face you.

**Swings.** You get three. The game earns one per 5 km run; here they refill
from the menu.

**Pool size.** The game's pool is 25,000, sized for a whole field of runners
over weeks. One person testing would never see him fall, so here the pool is
sized by running the engine itself. Before the first swing, the page simulates
300 attempts at your pet's level and sets the pool to six average attempts.
That works out to a handful of swings at any level. The result card after each
attempt shows what you took off him and his running total.

## 5. Art

**From the game, unchanged.** These are copied into `art/game/` so the folder
stands alone and the hosted page needs nothing else:

- 6 idle sheets: Cinderling, Sparky, Bamboo Cub (the v2 sheet), Blazewyrm,
  Zephyrite, Panda
- 17 skill sheets
- Sir Uwaaarghhhh: four phase sheets, three move sheets and the death sheet

Each pet is drawn with its `aspect`, `scale`, `dx` and `dy` from the game, so
a pet in the world is the pet on the pet screen, just smaller. Feet sit on a
ground line measured from each idle sheet. Sheets are resampled once per
frame at device resolution and cached.

**New for the world.** `tools/make_assets.py` draws these in Pillow. It is
deterministic, and draws at native size before upscaling by a whole number
with chunky outlines, following ART-SPEC:

- `tiles.png`: 16 ground tiles
- `props.png`: trees, bamboo, spires, crystals, rocks, standing stones, the
  campfire, signs, an acorn and berries

The hill is tinted earth and torch-orange to suit the orc.

**What to ask the artist for next:**

1. **A walk cycle per form.** For now a pet alternates two idle frames under a
   small hop.
2. **A faint pose per form.** For now it tilts, desaturates and shows an
   eyes-shut idle frame.
3. **A tileset in the pets' painted style**, once 1 and 2 are in place.

## 6. Phone-first details

- **Portrait only.** It uses the safe areas and never scrolls or zooms. Long
  presses and double-taps do nothing.
- **Big targets.** The move buttons are two-across, at least 48 px tall.
- **One thumb at a time.** The joystick appears wherever you put your thumb,
  and in a fight, everything is a tap.
- **Haptics.** A short buzz when you are hit, on Android. iOS ignores it.
- **Remembered settings.** The last pet, level and Auto setting are kept in
  this browser's local storage.

## 7. Publishing

`tools/build_artifact.py` turns `index.html` into a page body for the hosted
Artifact and lists the files that go with it (`art/*.png` and
`art/game/*.png`). The page and the repo copy are the same game; the build
only strips the outer `<html>`, `<head>` and `<body>` tags that the host
supplies.

## 8. Open questions

1. **Should the raid go social in the world?** In the game, other runners' swings
   at him are invisible. Out here they could show up as other pets on the hill,
   or as a running tally on his sign.
2. **Should exploring be tied to running directly?** For example, energy that
   each kilometre refills. It would make the link explicit. It would also
   gate fun behind exercise, which might be right or might put people off.
3. **Battling friends.** The engine already plays the defender on its own.
   Meeting a friend's pet out in the world, as a wandering "ghost" of it, is
   the natural place for the game's battles to happen.
4. **Wild pets as a reason to visit.** They give nothing yet. Cosmetics, and
   never power, would keep running as the only way to grow.

## 9. If it graduates

1. Move the attribute, engine, `SKILLS` and `RAID_BOSS` tables into one shared
   script that both pages load, instead of the copies here.
2. Read the real save **read-only** for species and level. Have the raid use
   the real attempts and the broker's shared pool.
3. Commission the art in §5.
4. Add an Explore entry on the pet screen.
