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
- **On the game's site, no Claude needed:** `ryancgq.github.io/runmon/explore/`.
  It's the same page. Here the shared world (players, PvP and his health)
  comes from Runmon Explore's own server, `explore-worker/` (see
  [Publishing](#7-publishing)). Anyone with the link can join. It is a
  separate page: the game doesn't link to it and nothing in the game changed.
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

Wild pets are the same for everyone in the world. Each spawn has a fixed
level that rises further from the Trailhead: 8, 12, 14, 24 and 34 in each
region. Their form follows their level, the same way your pet's does.

Each species has a temperament:

- **Ember** pets come at you.
- **Nimbus** and **Verdant** pets mind their own business until you hit them.

**Controls.** Drag on the left half of the screen to walk. Every pet walks at
the same pace (165 px/s); Speed shortens its cooldowns instead (§3). The
select screen shows by how much. Your right thumb
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
| Each move's multiplier, pierce and riders (burn, rattle, stoke, charge, soften, open, Cuddle's squeeze, Nap's heal and guard) | the same, applied the same way |
| One move per turn | one turn = **1.4 s** of the pet's own clock |
| Cooldown `cd` turns, a 2-turn shared cooldown after any skill | **long cooldowns**, about 3× the game's (below), × 1.4 s, and no shared cooldown |
| Attack ×1, once a turn | **Attack ×0.1**, once a turn (below) |
| Speed buys extra turns against the opponent, up to 35%, chaining | **a fixed tempo for the pet's own Speed, whoever it fights.** Its Attack and skill cooldowns run `(1 + 5 × Speed / total stats) / 1.5` times as fast: Verdant at the base pace, Ember about 1.5× (cooldowns a third shorter), Nimbus about 1.6× (two-fifths shorter), plus whatever a charge adds. Walking is the same for every pet (165 px/s), and so is the pace a move plays at, so its wind-up reads the same whoever throws it. The comparison with the opponent stays in the ranked battles only. |
| The boss never gets extra turns | the same |
| Opponent picks any ready move at random (`btChoose`) | the wild pets' AI picks the same way, the moment its turn comes round |

**Attack** is mostly a dash: it lunges at whatever is closest, but its swipe
barely scratches (×0.1). With nothing in reach it is just the dash,
and nothing *he* swings can land on you mid-dash. Once a skill has landed,
Attack's dash cuts the rest of its clip short, which is how you get out from
under him mid-move. It buys room, not time: the rest of that move's turn
still runs before the next skill.

**Skills** play their real clip from the game, fitted inside one turn (1.4 s)
so a long clip never costs extra time. Your pet stands still while it plays
(a rush carries it). The hit lands on the clip's impact frame, and between
pets it can miss: see *Aim, wind-ups and dodging* below.

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
- **Long cooldowns, so a fight isn't a race to press buttons.** Every pet,
  the quickest included, throws its whole kit and then waits with nothing
  ready, so there are stretches of just moving: getting into place, stepping
  out of the other pet's marks. Each move's cooldown is the game's × 3
  (`CD_MULT`), scaled by the pet's kit as a whole (`cdTurns`, `kitPace`).
  In a battle the turns between moves are Attacks at full weight. Here they
  are nothing, so a kit's moves alone would decide, and a pet that has just
  learnt its third move would be twice the pet it was. So each pet's
  cooldowns are stretched or shrunk until its moves do, per turn, what the
  pet does per turn in a battle. A move counts its hit, a burn's ticks, what
  gets through guard, and the hits a stoke, charge, open or rattle makes
  bigger. And no cooldown is ever shorter than the time it takes to throw the
  whole kit plus a turn and a half. A Nap is still once a fight.

  Cooldowns in seconds, with each pet's own Speed and pace, and the shortest
  spell with nothing ready once its whole kit is thrown:

  | Pet | Moves and cooldowns | Nothing ready for at least |
  | --- | --- | --- |
  | Cinderling Lv 14 | fireball 11.7 s, Horn Rush 8.8, Tail Swipe 8.8, Cinder Sweep 8.8 | 3.2 s |
  | Sparky Lv 14 | Spark 8.2 s, Static Shock 8.2, Acorn Flick 13.7, Pocket Storm 16.4 | 2.6 s |
  | Bamboo Cub Lv 14 | Green Gale 16.3 s, Cuddle 16.3, Bamboo Tasting 16.3, Forest Slam 27.2 | 10.7 s |
  | Blazewyrm Lv 26 | Fireball 10.0 s, Flame Stomp 10.0, Flying Swoop 10.0 | 5.8 s |
  | Zephyrite Lv 26 | Lightning Bolt 5.2 s, Arc Lash 5.2 | 2.4 s |
  | Panda Lv 26 | Landslide 8.1 s (and a Nap) | 6.7 s |

  The Bamboo Cub waits longest. It is the slowest and toughest, and its kit
  is worth the most per turn in a battle.
- **Pets hit each other for 30% of a battle's blow** (`PET_DMG`), and their
  moves cost them 30% as much of themselves. At a battle's numbers a pet's
  HP is about four hits, so one round of moves decided a fight and the
  cooldowns never came into it. Now a fight between pets of a stage runs
  20 to 60 seconds, through several rounds. His blows, and pets' blows on
  him, are unchanged.
- **Bigger areas for the moves that go off around your pet.** They don't seek
  a target, so they hardly ever caught anything. Novas are about 40% wider:
  Cinder Sweep 105→150, Flame Stomp 115→160, Spark 95→135, Static Shock
  110→150. The fireball's puff goes from 85 to 120.
**Speed for the pet's level.** A flat cut per point of Speed was tried first.
It meant almost nothing at Lv 5 and cut a Lv 40 Zephyrite's cooldowns by
nearly 60%, and with clips still at full length, Verdant won 99% of its
matchups. Measuring Speed against the pet's total stats keeps a quick
species' edge the same at every level. With it, the matchups land about 18
points from the game's, closer than the opponent-comparison rule managed
(about 22).

**Each form's own pace.** On top of its Speed, each form has a pace
multiplier (`FORM_PACE`) for its cooldowns. It is tuned so the forms of a
stage are even with each other:

| Form | Pace | Form | Pace |
| --- | --- | --- | --- |
| Cinderling | ×1.10 | Blazewyrm | ×0.84 |
| Sparky | ×1.00 | Zephyrite | ×1.17 |
| Bamboo Cub | ×0.90 | Panda | ×1.02 |

**How they were measured.** 200 simulated fights per pairing, two AI pets
that play exactly alike. Both the win rate and how close the fights were are
recorded. Closeness is the winner's HP left: + means the first-named pet
comes out ahead by that share of its HP.

Two identical bots turn any edge into a lopsided win rate: a pet 3% stronger
wins most of its fights. Real players, who aim and dodge, swamp an edge that
size. So the paces were tuned for close fights rather than the game's win
rates:

| Matchup | Lv 12 | Lv 14 | Lv 26 | Lv 40 |
| --- | --- | --- | --- | --- |
| Verdant v Ember | 85% · +10% HP | 56% · +3% | 34% · −1% | 36% · 0% |
| Verdant v Nimbus | 4% · −14% | 46% · +2% | 35% · +3% | 24% · −2% |
| Ember v Nimbus | 18% · −6% | 68% · +12% | 38% · −2% | 36% · −2% |

- **Stage 2:** every pairing is within 3% of HP.
- **Stage 1:** even at Lv 14, but spread at Lv 12. Sparky is ahead at Lv 12
  and Cinderling at Lv 14: their HP grows differently between the two
  levels, and Cinder Sweep comes in at 14. No single pace fixes both levels,
  so the pace splits the difference. Fights run 20 to 60 seconds.

**Not balanced across stages.** An evolved form learns its first skill at Lv
18, as in the game. From Lv 15 to 17 it has none, and with Attack this weak
it barely fights, so a Lv 14 Sparky with four skills beats it. The same goes
for a stage-1 form at Lv 5 to 7. More evolved skills are planned.

While measuring this I found and fixed an AI bug. Wild pets only looked at
their skills when their Attack was ready, so an Attack taken in a gap held
their skills back for a turn.

### Aim, wind-ups and dodging

A move is aimed when it's taken and lands on its impact frame where it was
aimed, so it can miss: a pet, or him on the raid, with the same rules for
both. For the wind-up, its shape is marked on
the ground where it will land. Other players' and wild pets' marks are amber
and solid; your own are faint and dashed. Each kind of move is dodged its own
way:

| Kind | Moves | Lands | To dodge it |
| --- | --- | --- | --- |
| Burst (nova) | Cinder Sweep, Flame Stomp, Spark, Static Shock | all round its user | get out of its ring |
| Swipe (cone), gale, puff | Tail Swipe, Arc Lash, Forest Slam, Green Gale, fireball | the way it was facing | get behind it or out of reach |
| Bolt (strike) | Pocket Storm, Lightning Bolt | on the spot you stood on when it was taken | leave the circle |
| Charge (rush) | Horn Rush, Flying Swoop, Cuddle, Landslide | straight down its lane, stopping on the first pet it hits | step aside |
| Shot | Fireball, Acorn Flick, Bamboo Tasting | flies straight at where you were when it's let go, hitting the first one in its path | move across its line; the further off, the more time you have |

Shots are the hardest to land, so they are let go 0.35 s into the move (they
were 0.6 to 0.8 s) and fly at 760 rather than 460. Their range is unchanged.

**Aiming.** Tap a move and it goes at the nearest foe. Press and hold one
that has a direction (a shot, a bolt, a swipe, a gale, a charge) and drag:
its shape follows your thumb out from your pet, blue while it's ready and
grey while it's cooling, and it goes where it points when you let go. A bolt
lands further out the further you drag. Drag back onto the button and it's
the nearest foe again. To call it off, let go on the ✕ that shows above the
buttons while you hold: nothing is thrown and the move stays ready. Bursts and the Nap go off round your pet, so they
fire on the press. It works the same on the raid.

Other wind-ups run about 0.3 to 1.1 s and are the same for every pet. Speed buys
shorter cooldowns, not quicker moves. A pet that takes a move also stands
still for it: committing is a risk.

On the raid it is all the same: tap and a move goes at him; hold and drag to
aim it anywhere, a charge away from him included, to get out of a mark. He
is big and slow, so a move aimed at him rarely misses; one aimed away does.

Other rules kept from earlier tuning:

- **Pets don't shove each other.** Only his blows knock you back.
- **Rushes stop when they connect.**
- **No opening coin.** The game weights who moves first by Speed. Adding that
  live made every matchup worse, so both pets start together.

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
| Plain swing | rears back, then lunges up to 260 px at you | **harder:** marked only 0.7 s ahead, and the mark **follows you** until 0.42 s before it lands (dashed and flickering while it follows, solid once it locks). Step away early and it comes with you; you have to react. | ×1 |
| **Torchswing** | charges up to 220 px towards you, then spins | **harder:** played 35% faster after a wind-up 15% longer (lands about 0.76 s after the mark appears), with a wider ring (210 px) round where he stops | ×1.35 to anything within reach |
| **Splitter** | leaps up to 420 px, landing beside you | a large red mark under you, landing about 1.28 s later (the sheet's wind-up, 15% longer). The big, readable one. | ×2.2, 70% through guard. It deletes a low-level pet, as in the game |
| **UWAAAARGH!** | stands and roars | **the whole hill turns red**, filling in as the roar builds. There is nowhere to stand out of it, and a dash doesn't help. He winds up for **about 2.6 s**, twice his sheet's wind-up, while a line of narration reads *"Sir Uwaaarghhhh is getting very upset and starts to…"*. As it lands, **UUUWWAAAARRGGHHHHHHHHH** comes out a letter at a time over about a second, faster as it goes, with the text shaking (and a phone buzzing) as he shouts it. | hits **everyone** on him, at ×0.6 for the first roar of a fight, plus ×0.25 for each roar after (×0.85, ×1.1, ×1.35 ...). Then, as in the game, his next two blows hit ×1.6 and he charges, getting faster and stronger, up to twice. |

If he lands on you, you're shoved clear of him.

**Nobody outlasts him.** The roar is what makes every attempt end. Its hit is
the lightest of his, but it can't be avoided and it grows with every roar, and
there is no healing in a raid beyond Panda's one Nap. In simulation, a perfect
player (one whom every blow but the roar misses) still falls within 43 to 152
s on average, after 2 to 7 roars. The longest of 72 runs was 244 s, a Lv 40
Panda, which can heal once. Playing well buys
time, and time is damage: a perfect Lv 26 player takes about 5 times as much
off him per attempt as the test player. Every attempt still ends, and more
attempts means more running.

**As in the game:**

- You always get the first swing.
- An attempt ends when your pet falls.
- His health carries over to the next attempt, and never regenerates.
- His bar shows a percentage.

You get three swings; the menu gives you ten more. The game earns one per 5 km
run.

**His health is one fixed pool: 400,000.** It is the same for one player or
twenty, and it never regenerates. Every swing anyone takes stays off him,
across attempts, sessions and days, until he is felled. He is meant to be a
group's weeks of work at the very end of the game.

**He hits 8% harder than the game's Power 90** (`BOSS_POW`), so attempts are
a little shorter.

**Sized for seven runners.** The game assumes about 30 km a week per runner,
which is 6 swings a week. Seven of them earn about 180 swings a month between
them. Average damage per attempt and the total swings needed, from
simulation:

| Level | Average player | Near-perfect player | Swings for 400,000, average / near-perfect | Time for 7 runners, average / near-perfect |
| --- | --- | --- | --- | --- |
| Lv 14 | ~440 | ~1,700 | ~920 / ~240 | ~5 months / ~5.5 weeks |
| Lv 26 | ~910 | ~3,600 | ~440 / ~110 | ~2.5 months / ~2.5 weeks |
| Lv 40 | ~1,150 | ~5,800 | ~350 / ~70 | ~2 months / ~12 days |

The average player steps out of his marks but gets caught mid-skill. The
near-perfect one is touched only by his roar. These figures are after the
long cooldowns, which cut what a pet takes off him per attempt to about a
third (quicker shots won some of it back). At 400,000, an average Lv 26
field now needs about two and a half months, not one. Keeping it to a month
would mean about 140,000.

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
- **His health** is 400,000 less the sum of what every tab has taken off him
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
- **Open PvP.** Out in the world, other players' pets are fair game, and
  yours is theirs. Your moves aim at, and land on, their pets as they would on
  a wild pet. The hit (its damage, and any burn, rattled guard or Cuddle's
  squeeze) goes into your page's presence addressed to that player's page, and
  their page takes it off their pet, once per hit. When a player is knocked
  out, they wake at the campfire and are told who got them. **Nobody fighting
  the boss can hit or be hit by another player.** Both pages check this. No
  win/loss record for now.
- **Wild pets are shared.** The page that runs the boss also runs the wild
  pets and puts them in its presence: where each is, its health, the move
  it's playing, and who it's after. Every other page draws its copy from
  that. A hit on a wild pet from another page goes to the running page,
  which takes it off and turns the pet on whoever hit it. The wild pets go
  for any player out in the world, never anyone on the raid. When the page
  running them changes, the next one carries on from its copy.
- **Everyone sees everyone's moves.** Each page plays other players' skills
  from their presence, and the damage another player does to the boss shows
  over him in blue.
- **No hiding from him.** An idle player is still a player. A hidden tab
  still plays: browsers stop drawing it, so it runs on a timer and catches
  up, and your pet stays where he can hit it. A phone that freezes the page
  outright (a locked screen) goes quiet, and after 4 seconds of silence the
  page running him **stands in** for it: it keeps that pet's health, lets
  his blows land on it where it stands (and other players' and wild pets'
  hits too), and shares the figure in its presence (`px`) so every page
  shows it. A page that runs him and freezes hands him to the next page.
  - Wake up while your pet still stands, and your page takes the health it
    was left with ("hit while you were away").
  - If your pet falls while you are away (frozen or hidden), you are taken
    out of Explore, back to the start, with a note saying why.
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

**Two homes, one page.** The page finds its world in one of three ways:
1. **Inside Claude:** the Artifact page's `room` and `db`.
2. **On the game's site:** its own server, `explore-worker/`. This is a
   separate Cloudflare Worker (`runmon-explore`), not the Strava broker,
   reached at `wss://runmon-explore.runmon-gq.workers.dev/world`. You can
   also point the page at any server with `?server=` on its link.
3. **Neither:** solo, with his health kept in the browser.

The server speaks the same two shapes as the Artifact page's `room` and `db`
(`openServer` in `index.html`), so the game code has one path for all
three. It relays presence in memory and keeps his account in its Durable
Object's SQLite storage. Values there only move forward: a round never goes
back, and a tab's damage never goes down. It only accepts connections from
the game's site, and an optional `JOIN_CODE` can require `?code=` on the
link. Pushing a change under `explore-worker/` deploys it
(`.github/workflows/deploy-explore.yml`).

The Artifact page is published with `capabilities: {room: {}, db: {}}`, using the
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

It is laid out so it can move into the game without a rewrite:

- **The page** is one folder, `explore/`, already served at
  `/runmon/explore/` beside the game. Graduating it means a link from the pet
  screen, and reading the player's real pet and level from the save
  (read-only) in place of the select screen.
- **The world server** is already a separate worker on the same Cloudflare
  account. It can stay as it is, or its `World` class can move into the
  Strava broker as a second Durable Object, which would let it check players'
  sessions.
- **One seam for the network.** Everything the game needs from "the world"
  goes through two shapes, a room and a store (`connectNet`, `openServer`).
  Swapping the transport touches nothing else.
- **What has to change before real players:**

1. Make the server check who is playing (a game session) and settle damage
   itself, rather than trusting each page's word.
2. Move the attribute, engine, `SKILLS` and `RAID_BOSS` tables into one shared
   script that both pages load, instead of the copies here.
3. Read the real save **read-only** for species and level. Have the raid use
   the real attempts and the broker's shared pool.
4. Commission the art in §5.
5. Add an Explore entry on the pet screen.
