# Runmon Explore — design

Pets leave the pet screen and walk around a top-down world. They fight the
wild pets they meet live, dungeon-crawler style, using their own skills on
cooldowns, and take on the raid boss, Sir Uwaaarghhhh, on his hill.

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
- **Fights run on the game's numbers.** They are live, but use the same
  attributes, damage, moves, effects and cooldowns, with one turn equal to
  1.4 s. See §3.
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

- **Ember** pets come at you.
- **Nimbus** and **Verdant** pets mind their own business until you hit them.

**Controls.** Drag on the left half of the screen to walk. Your right thumb
has Attack, with up to four skills in an arc around it.

## 3. Combat: live, on the game's numbers

Fights are live, dungeon-crawler style. Move with the left thumb. Tap
**👊 Attack** or any of your pet's skills whenever they're off cooldown.
Each button counts its own cooldown down.

Everything a fight is made of comes from the game's battle engine:

| Game (turn-based) | Here (live) |
| --- | --- |
| Attributes `attrsFor`, HP pool ×5 | the same |
| Damage: `btHit`, divisive Defence, K, ±35% jitter, no crits | the same function |
| Each move's multiplier, pierce and riders (burn, rattle, stoke, charge, soften, open, Nap's heal and expose) | the same, applied the same way |
| One move per turn | one turn = **1.4 s** of the pet's own clock |
| Cooldown `cd` turns, a 2-turn shared cooldown after any skill | `cd × 1.4 s`, and 2.8 s shared |
| Speed buys extra turns, up to 35%, chaining | the pet's whole clock runs `1/(1−p)` faster against its opponent: Attack, cooldowns, clips, its burn and guard timers |
| The boss never gets extra turns | the same |
| Opponent picks any ready move at random (`btChoose`) | the wild pets' AI picks the same way, the moment its turn comes round |

**Attack** is the plain move (×1). It lunges at whatever is closest. With
nothing in reach it is a dash, and nothing *he* swings can land on you
mid-dash.

**Skills** play their real clip from the game, sped up to fit inside one turn
so a long clip never costs extra time. The hit is drawn on the clip's impact
frame. Shots and strikes find their target, rushes steer onto it and stop when
they connect, and novas, swipes and gales take whatever is in their shape.

### Keeping it close to the game's balance

Live fights do not reproduce turn-based win rates by themselves. Things a
battle never charges for showed up as large swings:

- walking back into reach after a shove
- a rush that carries on past its target
- a slow clip whose hit was still in the air when its pet died

Each was measured against the game's engine and removed:

- **Pets don't shove each other.** Only his blows knock you back.
- **Rushes stop when they connect.**
- **Between pets, a move resolves the moment it's taken**, as `btAct` does.
  The clip shows the number, flash and knockout on its impact frame. His
  blows still land on impact, so they can be dodged.
- **No opening coin.** The game weights who moves first by Speed. Adding that
  live made every matchup worse, so both pets start together.

Per move, the live version now matches the game: the same moves per fight and
the same damage per move. For example, in Panda v Blazewyrm at Lv 26, Attack
averages 69 and Landslide 99, against 69 and 101 in the game.

Simulated AI v AI at levels 12, 26 and 40, the species matchups land **9
points from the game's on average** (game 46–57%, live 32–70%). Some of that
is sampling noise at 160 fights a pairing. The worst case is Verdant v Nimbus,
which runs about 15 points Verdant's way.

Some difference is unavoidable. Verdant's matchups are knife-edge races in the
game too, decided by a fraction of an action, and real time moves those
fractions about. A player who dodges and spaces well will beat these numbers;
that is the point of making it live.

**Out of a fight** you get your breath back slowly, faster at the campfire.
Berries heal 30%. Lose to a wild pet and you wake at the campfire.

## 4. The raid: Sir UwaaarghhhhUWAAGRRHH, live

Everything about him is the game's:

- his four worn-down sheets, which change at 75%, 50% and 25%
- his three moves, each with its own sheet and the game's numbers:
  **UWAAAARGH!**, **Splitter** and **Torchswing**
- his plain swing (×1)
- his death clip
- his stats: Power 90, Defence 25, Speed 60, and no extra turns

He chooses the way the game's `btChoose` does: any ready move at random, with
cooldowns counted in his own turns, which come every 2.1 s and quicken as his
roar charges him. **Every blow is marked on the ground first**, so you can
walk or dash out of it:

| Move | What you see | What it does |
| --- | --- | --- |
| Plain swing | a red mark under one pet | ×1, a short lunge |
| **Splitter** | a large red mark under a pet, as he raises the torch | ×2.2, 70% through guard. It deletes a low-level pet, as in the game |
| **Torchswing** | a ring all round him | ×1.35 to anything within reach |
| **UWAAAARGH!** | he roars | no damage, but his next two blows hit ×1.6 and he charges, getting faster and stronger, up to twice |

**As in the game:**

- You always get the first swing.
- An attempt ends when your pet falls.
- His health carries over to the next attempt.
- His bar shows a percentage.

You get three swings; the menu gives you more. The game earns one per 5 km
run.

**His health pool.** The game's pool is 25,000, sized for a whole field of
runners over weeks. Here it is 70 of your plain Attacks at your level. In
simulation, a player who half-dodges fells him in 2–7 swings, with attempts
lasting 17–45 s. In the menu you can bring two other runners' pets, AI allies
that step out of his marks, to try the raid as a group.

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
