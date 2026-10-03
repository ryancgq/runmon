# Runmon Explore — design

Pets leave the pet screen and walk around a top-down world. They fight the
wild pets they meet live, dungeon-crawler style, using their own skills on
cooldowns, and take on the raid boss, Sir Uwaaarghhhh, on his hill.
Everyone who has the link open is in the same world, and can take him on
together.

This is a **standalone prototype** for phones. It lives in `explore/`, shares
nothing with the game's `index.html`, and never reads or writes a save. Its
job is to show whether the idea works before any of it goes into the game.

## Try it

- **Hosted link:** an Artifact page built from this folder (see
  [Publishing](#7-publishing)). Open it on a phone. To play together, share it
  from the page's Share menu as **Contributor**. Testers must be signed in to
  Claude to join the shared world, and need Contributor for their damage to
  be saved. A Viewer still plays with everyone, and their damage is saved
  while a Contributor is in the world. A public link opens the same game,
  solo.
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
has Attack, with up to four skills in an arc around it. The select screen
asks for a name; it is what other people see over your pet.

## 3. Combat: live, on the game's numbers

Fights are live, dungeon-crawler style. Move with the left thumb. Tap any of
your pet's skills whenever they're off cooldown, and **👊 Attack** between
them. Each button counts its own cooldown down.

Everything a fight is made of comes from the game's battle engine:

| Game (turn-based) | Here (live) |
| --- | --- |
| Attributes `attrsFor`, HP pool ×5 | the same |
| Damage: `btHit`, divisive Defence, K, ±35% jitter, no crits | the same function |
| Each move's multiplier, pierce and riders (burn, rattle, stoke, charge, soften, open, Nap's heal and expose) | the same, applied the same way |
| One move per turn | one turn = **1.4 s** of the pet's own clock |
| Cooldown `cd` turns, a 2-turn shared cooldown after any skill | shorter cooldowns (below), × 1.4 s, and **no shared cooldown** |
| Attack ×1, once a turn | **Attack ×0.1**, once a turn (below) |
| Speed buys extra turns, up to 35%, chaining | the pet's whole clock runs `1/(1−p)` faster against its opponent: Attack, cooldowns, clips, its burn and guard timers |
| The boss never gets extra turns | the same |
| Opponent picks any ready move at random (`btChoose`) | the wild pets' AI picks the same way, the moment its turn comes round |

**Attack** is mostly a dash: it lunges at whatever is closest, but its swipe
barely scratches (×0.1). With nothing in reach it is just the dash,
and nothing *he* swings can land on you mid-dash. Once a skill has landed,
Attack's dash cuts the rest of its clip short, which is how you get out from
under him mid-move. It buys room, not time: the rest of that move's turn
still runs before the next skill.

**Skills** play their real clip from the game, sped up to fit inside one turn
so a long clip never costs extra time. The hit is drawn on the clip's impact
frame. Shots and strikes find their target, rushes steer onto it and stop when
they connect, and novas, swipes and gales take whatever is in their shape.

### Skills over Attack

In playtesting, spamming Attack was the best play. Attack goes off at once
and dashes you onto the target, while a skill plays its clip first. A first
fix, Attack at ×0.75, still left it too strong, so:

- **Attack hits at ×0.1**, 90% under the game's plain attack. It's there for
  its dash, to get out from under him or to cut a landed skill short. The
  damage comes from skills.
- **No shared cooldown.** With Attack worth nothing, the game's rhythm of a
  skill then an Attack would be a dead turn after every skill. Here a pet
  chains its skills: about 95% of moves are skills.
- **Shorter cooldowns, so the moves a pet learns first come round more.** The
  first damaging move of each form comes back every 2 turns. The rest come
  back one turn sooner than in the game, never under 2. A Nap is still once a
  fight.

  | Form | Skill | Game | Here |
  | --- | --- | --- | --- |
  | Cinderling | fireball, Horn Rush, Tail Swipe, Cinder Sweep | 4, 3, 3, 3 | 2, 2, 2, 2 |
  | Blazewyrm | Fireball, Flame Stomp, Flying Swoop | 3, 3, 3 | 2, 2, 2 |
  | Sparky | Spark, Static Shock, Acorn Flick, Pocket Storm | 3, 3, 5, 6 | 2, 2, 4, 5 |
  | Zephyrite | Lightning Bolt, Arc Lash | 3, 3 | 2, 2 |
  | Bamboo Cub | Green Gale, Bamboo Toss | 3, 3 | 2, 2 |
  | Panda | Nap, Landslide | 4 (once), 5 | 4 (once), 2 |

- **Bigger areas for the moves that go off around your pet.** They don't seek
  a target, so they hardly ever caught anything. Novas are about 40% wider:
  Cinder Sweep 105→150, Flame Stomp 115→160, Spark 95→135, Static Shock
  110→150. The fireball's puff goes from 85 to 120.
**What it costs in balance.** Measured against the game's engine, simulated at
levels 12, 26 and 40 with 320 fights a pairing, species matchups now land
**about 22 points from the game on average**. They were 12 with the game's
Attack, and 14 at ×0.75. Every way of making Attack this weak measured 22 to
25; keeping the shared cooldown didn't help. Where it shows:

- **Blazewyrm v Zephyrite: Ember wins 13–17%** (game about 48%). Ember's high
  Power showed up mostly in its plain attacks, which now do nothing, and
  Zephyrite gets more skills in a fight that lasts three moves a side.
- **Bamboo Cub wins about 80%** against both Lv 12 rivals (game about 50%).
- **Pets with a single skill are weak.** A Lv 8 Cinderling has only its ×0.4
  fireball, and a Lv 15–21 Blazewyrm only Fireball. In the raid, the Lv 8
  Cinderling takes 13 to 19 swings to fell him alone; most pets take 2 to 5.

The fix for these is per-species tuning, which would move away from the
game's numbers, so it is left as an open question (§8).

While measuring this I found and fixed an AI bug. Wild pets only looked at
their skills when their Attack was ready, so an Attack taken in a gap held
their skills back for a turn.

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

With the old rules, simulated AI v AI at levels 12, 26 and 40, the species
matchups landed 9 to 12 points from the game's on average. Fights are short,
about five moves a side, so one extra action swings a result by 20 points,
and much of that difference is noise.

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
cooldowns counted in his own turns. His turns come every **1.3 s** (they were
2.1 s) and quicken as his roar charges him. At the old rhythm he was too easy
to stay away from.

**He moves.** Standing still, he was easy to read. Now he walks at whoever he
has picked between blows, and circles once he's close. He switches targets
now and then, and every blow carries him somewhere new. **Every blow is still
marked on the ground first**, so you can walk or dash out of it:

| Move | How he moves | The mark | What it does |
| --- | --- | --- | --- |
| Plain swing | rears back, then lunges up to 260 px at you | **harder:** marked only 0.6 s ahead, and the mark **follows you** until 0.35 s before it lands (dashed and flickering while it follows, solid once it locks). Step away early and it comes with you; you have to react. | ×1 |
| **Torchswing** | charges up to 220 px towards you, then spins | **harder:** played 35% faster (lands about 0.65 s after the mark appears), with a wider ring (210 px) round where he stops | ×1.35 to anything within reach |
| **Splitter** | leaps up to 420 px, landing beside you | unchanged: a large red mark under you, landing about 1.1 s later. The big, readable one. | ×2.2, 70% through guard. It deletes a low-level pet, as in the game |
| **UWAAAARGH!** | stands and roars | unchanged: none | no damage, but his next two blows hit ×1.6 and he charges, getting faster and stronger, up to twice |

If he lands on you, you're shoved clear of him.

**As in the game:**

- You always get the first swing.
- An attempt ends when your pet falls.
- His health carries over to the next attempt, and never regenerates.
- His bar shows a percentage.

You get three swings; the menu gives you ten more. The game earns one per 5 km
run.

**His health is one fixed pool: 100,000.** It is the same for one player or
twenty, and it never regenerates. Every swing anyone takes stays off him,
across attempts, sessions and days, until he is felled. He is meant to be
the very end of the game.

The game ships 25,000, sized so a field of six level-26 runners fells him in
about 1.7 weeks, some 60 attempts between them. A live attempt takes far more
off him than a battle does, so the pool here is sized by attempts instead. In
simulation, a test player steps out of his marks, waits for a following mark
to lock before it dashes, and doesn't start a skill under one. Its average
damage per attempt at each level:

| Level | Damage per attempt | Attempts to fell him |
| --- | --- | --- |
| Lv 14 | about 550 | about 180 |
| Lv 18 Blazewyrm (one skill) | about 470 | about 210 |
| Lv 26 | about 1,450 (1,000 to 1,900 by species) | about 70 |
| Lv 40 | about 2,600 | about 40 |

Attempts last 10 to 35 s, and his plain swing lands 60 to 75% of the time,
because a skill's clip often holds the player in place when the mark locks. A
Lv 8 Cinderling, with only its ×0.4 fireball, is effectively no threat to
him. Bringing friends doesn't change his health. It only shares the work.

**After he falls**, everyone who was on him sees the death clip and a card of
who took what off him this round. He is back on his hill 20 seconds later
for the next round, at full health. The 20 seconds is for testing; in the game
he'd stay down until the next raid.

## 4a. Together

Everyone who has the page open is in the same world. You see each other's
pets walking about, with their names, health and skills. You can take him on
at the same time, and his health is one pool for everybody.

**How it works.** It uses two capabilities of the Artifact page: `room` for
who's here now, and `db`, a small shared store, for his health. There is no
server of our own.

- **Each page sets its own presence** about ten times a second. That is its
  pet's form, level and position, the move it is playing, its health, whether
  it's on him, and how much it has taken off him this time round. Other pages
  draw a pet from that. They never simulate it, and they never take hits on
  its behalf.
- **One page runs him.** It walks him, picks his moves and puts all of it in
  its presence: where he is, the blow in progress (start, landing, mark, and
  when it lands), the pool, and everyone's damage. The other pages draw him
  from that and play each blow from the same record.
- **Each page settles his blows on its own pet only**, at the moment the mark
  fills. The page running him decides where he goes, and your page decides
  whether you were standing in it.
- **His health** is 100,000 less the sum of what every tab has taken off him
  this round. Each tab keeps its own figure, which survives a reload, so two
  tabs never overwrite each other. Figures only ever grow, so every copy of
  the account (the store, the presence of the page running him, this
  browser) merges by keeping the larger number per tab.
- **Kept in the store.** Each tab's damage this round is its own document,
  `raids/e<round>/hits/<tab>`. `raids/state` holds the round number and when
  he fell. A tab writes its own document; the page running him also writes
  any figure the store is behind on, so a Viewer's damage is saved while a
  Contributor is around. Everyone closing the page loses nothing.
- **Without the store** (signed out, a public link, the repo copy) the same
  account lives in this browser's local storage. A browser's solo progress
  never leaks into the shared one.
- **Handing him over.** The page that has run him longest keeps him, so
  someone arriving never takes him over with a fresh pool. If that page
  closes or goes into the background, the lowest-labelled page still on
  screen picks him up from the last state it saw. In testing, his health,
  position and charges came through the hand-off intact.
- **Wild pets stay per player.** Each page has its own, so nobody steals
  anybody's fight.
- **Alone, it's the same game.** With no room (a public link, or the page
  outside Claude) the page runs him itself and nothing else changes.

**Trust.** It's a prototype for friends. Presence and the store are
unverified, so a page could claim damage it never dealt. Names are shown as text only, and are
never parsed as markup. If this goes into the game, the raid pool should
live on the game's own server (the raid Durable Object already exists), with
the room only for showing who is where.

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

The page is published with `capabilities: {room: {}, db: {}}`, using the
store's default rules: everyone admitted reads, and Contributors and above
write. Only people signed in to Claude whom the owner has shared it with join
the shared world. Opened any other way, both resolve `null` and the page
plays solo, keeping his health in the browser. From the repo, served locally,
it is always solo.

## 8. Open questions

1. **Is the shared raid worth bringing into the game?** In the game, other
   runners' swings at him are invisible. The prototype shows them as other
   pets on the hill, on one pool. It would need the game's server to own the
   pool (see §4a).
2. **Should exploring be tied to running directly?** For example, energy that
   each kilometre refills. It would make the link explicit. It would also
   gate fun behind exercise, which might be right or might put people off.
3. **Battling friends.** The engine already plays the defender on its own.
   Meeting a friend's pet out in the world, as a wandering "ghost" of it, is
   the natural place for the game's battles to happen.
4. **Wild pets as a reason to visit.** They give nothing yet. Cosmetics, and
   never power, would keep running as the only way to grow.

5. **Attack at ×0.1 moves species balance a long way** from the game's (§3).
   Is a skills-only feel worth that? If so, the fix is per-species tuning of
   the live cooldowns, which the game itself doesn't need.

## 9. If it graduates

1. Move the attribute, engine, `SKILLS` and `RAID_BOSS` tables into one shared
   script that both pages load, instead of the copies here.
2. Read the real save **read-only** for species and level. Have the raid use
   the real attempts and the broker's shared pool.
3. Commission the art in §5.
4. Add an Explore entry on the pet screen.
