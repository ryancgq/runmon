# Runmon Explore — design

Pets leave the pet screen and walk around a top-down world. They fight the
wild pets they meet live, dungeon-crawler style, using their own skills on
cooldowns, and take on the raid boss, Sir Uwaaarghhhh, on his hill.
Everyone who has the link open is in the same world, and can take him on
together.

**Explore is in the game, in the raid's place.** The game's centre button
opens an Explore tab: what Explore is, how far down Sir Uwaaarghhhh is, who
has taken the most off him, your swings, and a button into the world. The
old raid's fights, swings and alerts are switched off; its health and every
player's share were carried over once, when Explore's world first opened
(§10).

There are two Explores, one page (`explore/`):

- **The game's** (`/runmon/explore/`, from the Explore tab): your own pet, as
  the game has it, in the one world everybody plays. Only for players who
  have linked Strava: the page shows the world server its game session, and
  the server asks the game who it belongs to. Every attempt at him spends
  one swing (one per 5 km run, counted by the game). His health and the
  leaderboard are kept by the world server.
- **The sandbox** (`/runmon/explore/?demo=1`, linked from the game's demo
  page `demo.html`, and anywhere off the game's site, Claude included): any
  pet at any level, free swings, prototype tools, its own world and its own
  boss. Nothing in it touches the game. It is where new things are tried.

## Try it

- **In the game:** the centre button (a compass), then **Enter the world**.
- **The sandbox:** `ryancgq.github.io/runmon/demo.html` → **Open the Explore
  sandbox**, or `ryancgq.github.io/runmon/explore/?demo=1`.
- **Hosted in Claude:** an Artifact page built from this folder (see
  [Publishing](#7-publishing)). It is always the sandbox.
- **Locally:** serve the repo root (`python3 -m http.server`) and open
  `/explore/` (the sandbox), or `/explore/?game=1&server=ws://127.0.0.1:8787`
  with a game session in the browser and local copies of both workers.
- **Deep links for testing (sandbox):** `#explore`, `#raid`, `#raid.blazewyrm`,
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

### Mobs

Beside the wild pets, the world has creatures of its own that were never
anybody's pet (`MOBS`, `MOB_SPAWNS`). There are 30 in all, spread over 18 spawns:

| Mob | Where | Levels | Comes | Temper | Moves |
| --- | --- | --- | --- | --- | --- |
| Bramble Boar | the meadow round the Trailhead | 8–15 | alone | charges if you come within 150 px | **Gore** (a charge); **Stomp** from Lv 9 (a burst that rattles guard) |
| Cinder Beetle | Ember Crags | 8–20 | in threes | goes for you from 230 px, and its pack comes with it | **Shell Ram** (a charge that leaves you flat-footed); **Cinder Spit** from Lv 12 (a shot that burns) |
| Puffcap | Verdant Grove | 8–18 | in pairs, or alone | waits to be hit | **Spore Cloud** (a burst that poisons); **Cap Bonk** from Lv 8 (a swipe that rattles guard) |
| Static Wisp | Nimbus Heights | 8–18 | alone, or two | goes for you from 260 px | **Zap** (a shot); **Discharge** from Lv 10 (a bolt, 25% through guard). It floats, and it fights from range: it backs off to about 190 px and circles there, slower going back than you are going in, so it can always be caught |

To the engine a mob is a wild pet in every way: the same `Pet`, the same
damage, riders, cooldowns, wind-ups, aim and dodging, the same berry drop and
respawn, and they're shared between pages the same way (they follow the wild
pets in `G.wild`, so every page numbers them alike). What differs is in each
mob's row: how its level's attributes are split (`split`), what share of a
whole pet's health and Power it gets (`hp`, `dmg`), its temper, and for the
wisp how far it keeps off (`keep`) and how high it floats (`hover`). When a
beetle or a Puffcap picks a fight, the rest of its kind within 220 px join in.
Poison is a burn in green: the same rider, the same ticks, its own word.

**No mob is under Lv 8.** A pet learns its first skill at 8, and with Attack
at ×0.1 a pet below that can't fell anything. In the game's world they stop
at Lv 15, like the wild pets.

**How hard they are.** Mobs are meant to be the fights you win; the wild pets
are the even ones. Simulated as in §3 (two AI pets, 40 fights a matchup, the
mob at the pet's level), win rate and the HP the pet has left:

| Pet | Boar | 3 Beetles | 2 Puffcaps | Wisp |
| --- | --- | --- | --- | --- |
| Cinderling Lv 11 | 100% · 34% | 85% · 36% | 63% · 22% | 85% · 33% |
| Sparky Lv 11 | 100% · 48% | 100% · 58% | 100% · 42% | 98% · 38% |
| Bamboo Cub Lv 11 | 100% · 44% | 78% · 44% | 80% · 18% | 83% · 29% |
| Cinderling Lv 15 | 100% · 51% | 100% · 60% | 100% · 52% | 100% · 51% |
| Sparky Lv 15 | 100% · 57% | 100% · 49% | 100% · 55% | 100% · 47% |
| Bamboo Cub Lv 15 | 100% · 54% | 98% · 48% | 55% · 28% | 90% · 46% |

A lone mob costs about half a pet's health; a pack is a real risk, the
Puffcaps' poison most of all for the slow Bamboo Cub. Before tuning, three
beetles beat almost every pet and two Puffcaps beat all of them.

**Art.** Each mob is one 16-frame strip (idle 0–3, knocked out 4, its two
moves 5–9 and 10–15), drawn by `tools/make_assets.py` in the pets' own style
(a round, fuzzy body lit from the upper left, big glossy eyes, little paws in
front, a thick dark outline) at 96×80 and upscaled ×3. They're stand-ins
until real sheets are drawn, as the tiles and props are.

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
| Attributes `attrsFor`, HP pool ×5 | the same, but HP is a fifth lower (`LIVE_HP` ×0.8), for every pet, wild ones included, so fights end sooner |
| Damage: `btHit`, divisive Defence, K, ±35% jitter, no crits | the same function |
| Each move's multiplier, pierce and riders (burn, rattle, stoke, charge, soften, open, Cuddle's squeeze, Nap's heal and guard) | the same, applied the same way |
| One move per turn | one turn = **1.4 s** of the pet's own clock |
| Cooldown `cd` turns, a 2-turn shared cooldown after any skill | **long cooldowns**, about 3× the game's (below), × 1.4 s, and no shared cooldown |
| Attack ×1, once a turn | **Attack ×0.1**, once a turn (below) |
| Speed buys extra turns against the opponent, up to 35%, chaining | **a fixed tempo for the pet's own Speed, whoever it fights.** Its Attack and skill cooldowns run `(1 + 5 × Speed / total stats) / 1.5` times as fast: Verdant at the base pace, Ember about 1.5× (cooldowns a third shorter), Nimbus about 1.6× (two-fifths shorter), plus whatever a charge adds. Walking is the same for every pet (165 px/s), and so is the pace a move plays at, so its wind-up reads the same whoever throws it. The comparison with the opponent stays in the ranked battles only. |
| The boss never gets extra turns | the same |
| Opponent picks any ready move at random (`btChoose`) | the wild pets' AI picks the same way, the moment its turn comes round |

**Attack** is a swipe where you stand at the nearest foe within arm's
length (60 px), once a turn, and it barely scratches (×0.1). It doesn't move
your pet. It used to be a dash that lunged at the target, dodged his blows
and cut a landed skill short. All of that was removed, so the only ways out
of a mark are walking and a charge.

**Skills** play their real clip from the game, fitted inside one turn (1.4 s)
so a long clip never costs extra time. Your pet stands still while it plays
(a rush carries it). The hit lands on the clip's impact frame, and between
pets it can miss: see *Aim, wind-ups and dodging* below.

### Skills over Attack

In playtesting, spamming Attack was the best play. Attack goes off at once,
while a skill plays its clip first. A first fix, Attack at ×0.75, still left
it too strong, so:

- **Attack hits at ×0.1**, 90% under the game's plain attack. The damage
  comes from skills.
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
  | Cinderling Lv 15 | fireball 12.5 s, Horn Rush 9.4, Tail Swipe 9.4, Cinder Sweep 9.4 | 5.7 s |
  | Sparky Lv 15 | Spark 7.7 s, Static Shock 7.7, Acorn Flick 12.7, Pocket Storm 15.3 | 4.5 s |
  | Bamboo Cub Lv 15 | Green Gale 16.2 s, Cuddle 16.2, Bamboo Tasting 16.2, Forest Slam 26.9 | 12.9 s |
  | Blazewyrm Lv 26 | Fireball 10.2 s, Flame Stomp 10.2, Flying Swoop 10.2 | 7.3 s |
  | Zephyrite Lv 26 | Lightning Bolt 5.0 s, Arc Lash 5.0 | 3.6 s |
  | Panda Lv 26 | Landslide 8.3 s (and a Nap) | 7.6 s |

  The Bamboo Cub waits longest. It is the slowest and toughest, and its kit
  is worth the most per turn in a battle.
- **Pets hit each other for 30% of a battle's blow** (`PET_DMG`), and their
  moves cost them 30% as much of themselves. At a battle's numbers a pet's
  HP is about four hits, so one round of moves decided a fight and the
  cooldowns never came into it. Now a fight between pets of a stage runs
  15 to 45 seconds, through several rounds. His blows, and pets' blows on
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
| Cinderling | ×1.02 | Blazewyrm | ×0.825 |
| Sparky | ×1.07 | Zephyrite | ×1.225 |
| Bamboo Cub | ×0.91 | Panda | ×0.99 |

**How they were measured.** 200 simulated fights per pairing, two AI pets
that play exactly alike. Both the win rate and how close the fights were are
recorded. Closeness is the winner's HP left: + means the first-named pet
comes out ahead by that share of its HP.

Two identical bots turn any edge into a lopsided win rate: a pet 3% stronger
wins most of its fights. Real players, who aim and dodge, swamp an edge that
size. So the paces were tuned for close fights rather than the game's win
rates:

| Matchup | Lv 13 | Lv 15 | Lv 26 | Lv 40 |
| --- | --- | --- | --- | --- |
| Verdant v Ember | 98% · +21% HP | 75% · +12% | 63% · +10% | 51% · +7% |
| Verdant v Nimbus | 9% · −22% | 5% · −12% | 5% · −10% | 7% · −11% |
| Ember v Nimbus | 5% · −13% | 70% · +11% | 55% · +4% | 72% · +8% |

- **Both stages at their full kits (Lv 15, Lv 26 and 40) form a loop**, as
  in rock-paper-scissors: Verdant beats Ember, Nimbus beats Verdant, and
  Ember beats Nimbus, each by about 4 to 14% of HP. No set of paces undoes
  a loop, so these leave each pet about even overall: one good matchup and
  one bad. (Before Attack lost its dash, stage 2 was within 4% all round;
  the dash's lunge was worth more to some forms than others.)
- **Stage 1, Lv 13:** the loop is wider, 13 to 22% of HP. Every pet has
  three moves at 13 and gets its fourth at 15, as in the game, and no single
  pace suits both levels, so Lv 15, the full kit, came first.

Fights run 15 to 45 seconds.

**Not balanced across stages.** A pet evolves into its third form at Lv 16
and learns its first skill there at Lv 18, as in the game. At Lv 16 and 17 it
has none, and with Attack this weak it barely fights, so a Lv 15 Sparky with
four skills beats it. The same goes
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

**Wind-ups are short**, so a move lands before its target can walk out of it.
From the press to the hit:

| Kind | Wind-up | Was |
| --- | --- | --- |
| Shot | 0.1 s | 0.6 to 0.8 s |
| Charge (to its launch) | 0.1 s | 0.3 to 0.7 s |
| Burst, swipe, gale, puff | 0.12 s | 0.5 to 0.8 s |
| Bolt | 0.15 s | 0.8 to 1.0 s |

Only the frames before the hit are sped up; the rest of each clip plays as
before, so a whole move now takes 0.55 to 1.2 s and your pet stands still for
less of it. A bolt keeps a little longer because it's dropped right under
you. Shots also fly at 760 rather than 460, with their range unchanged.
Dodging is now mostly about reading the other pet: keeping out of reach,
moving while its moves are ready, and stepping in once it's thrown them.

**Aiming.** Tap a move and it goes at the nearest foe. Press and hold one
that has a direction (a shot, a bolt, a swipe, a gale, a charge) and drag:
its shape follows your thumb out from your pet, blue while it's ready and
grey while it's cooling, and it goes where it points when you let go. A bolt
lands further out the further you drag. Drag back onto the button and it's
the nearest foe again. To call it off, let go on the ✕ that shows above the
buttons while you hold: nothing is thrown and the move stays ready. Bursts and the Nap go off round your pet, so they
fire on the press. It works the same on the raid.

Wind-ups are the same for every pet. Speed buys
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
marked on the ground first**, so you can walk (or charge) out of it:

| Move | How he moves | The mark | What it does |
| --- | --- | --- | --- |
| Plain swing | rears back, then lunges up to 260 px at you | **harder:** marked only 0.7 s ahead, and the mark **follows you** until 0.42 s before it lands (dashed and flickering while it follows, solid once it locks). Step away early and it comes with you; you have to react. | ×1 |
| **Torchswing** | charges up to 220 px towards you, then spins | **harder:** played 35% faster after a wind-up 15% longer (lands about 0.76 s after the mark appears), with a wider ring (210 px) round where he stops | ×1.35 to anything within reach |
| **Splitter** | leaps up to 420 px, landing beside you | a large red mark under you, landing about 1.28 s later (the sheet's wind-up, 15% longer). The big, readable one. | ×2.2, 70% through guard. It deletes a low-level pet, as in the game |
| **UWAAAARGH!** | stands and roars | **the whole hill turns red**, filling in as the roar builds. There is nowhere to stand out of it, and a charge doesn't help. He winds up for **about 2.6 s**, twice his sheet's wind-up, while a line of narration reads *"Sir Uwaaarghhhh is getting very upset and starts to…"*. As it lands, **UUUWWAAAARRGGHHHHHHHHH** comes out a letter at a time over about a second, faster as it goes, with the text shaking (and a phone buzzing) as he shouts it. | hits **everyone** on him, at ×0.6 for the first roar of a fight, plus ×0.25 for each roar after (×0.85, ×1.1, ×1.35 ...). Then, as in the game, his next two blows hit ×1.6 and he charges, getting faster and stronger, up to twice. |

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

**His health is one fixed pool: 110,000.** It is the same for one player or
twenty, and it never regenerates. Every swing anyone takes stays off him,
across attempts, sessions and days, until he is felled. He is meant to be a
group's weeks of work at the very end of the game.

**He hits 8% harder than the game's Power 90** (`BOSS_POW`), so attempts are
a little shorter.

**Sized for seven runners.** The game assumes about 30 km a week per runner,
which is 6 swings a week. Seven of them earn about 180 swings a month between
them. Average damage per attempt and the total swings needed, from
simulation:

| Level | Average player | Near-perfect player | Swings for 110,000, average / near-perfect | Time for 7 runners, average / near-perfect |
| --- | --- | --- | --- | --- |
| Lv 15 | ~200 | ~1,450 | ~550 / ~76 | ~3 months / ~2 weeks |
| Lv 26 | ~400 | ~3,000 | ~275 / ~37 | ~6 weeks / ~6 days |
| Lv 40 | ~640 | ~5,500 | ~170 / ~20 | ~4 weeks / ~3.5 days |

The average player steps out of his marks but gets caught mid-skill. The
near-perfect one is touched only by his roar. These figures are after the
long cooldowns, which cut what a pet takes off him per attempt to about a
third (quicker shots won some of it back), so his health came down from
400,000 to 150,000: about a month for an average Lv 26 field. Then Attack
lost its dash, the average player's best way out of his marks, and pets lost
a fifth of their HP. An average player now lasts about 13 s on him, not 25,
and takes about half as much off him, so his health came down again, to
110,000: about six weeks for that field. A near-perfect one is hardly
touched by the change.

**After he falls**, everyone who was on him sees the death clip and a card of
who took what off him this round. He is back on his hill 20 seconds later
for the next round, at full health. The 20 seconds is for testing; in the game
he'd stay down until the next raid.

## 4a. Together

Everyone who has the page open is in the same world. You see each other's
pets walking about, with their names, health and skills. You can take him on
at the same time, and his health is one pool for everybody.

**Who's here.** Under your own panel, a list of everyone else in the world,
nearest first (`updateRoster`, up to six, then "+ N more"): their pet's
portrait, name, form and level, whether they're away, knocked out or on the
raid, and an arrow pointing to them with how far (a tile is a metre). Tap the
👥 count to hide or show it. On the raid it gives way to the party list.

**How it works.** It uses two capabilities of the Artifact page: `room` for
who's here now, and `db`, a small shared store, for his health. There is no
server of our own.

- **Each page sets its own presence** up to ten times a second, and only
  when something has changed: a pet standing still with nothing happening
  sends a once-a-second heartbeat instead (the page running him and the wild
  pets always has something new). Every message counts against the world
  server's daily allowance on Cloudflare's free plan. Presence is its
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
- **His health** is 110,000 less the sum of what every tab has taken off him
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
- **Idle players are taken out of the world after 2 minutes** without a touch
  on the screen (`IDLE_KICK`). Their damage on him is saved first, then the
  page leaves the world (it closes its connection, so it stops counting
  against the server's allowance) and goes back to the start with a note.
  Setting out again joins the world again. A phone frozen outright can't do
  this itself, so the world server lets a connection go after 2 minutes of
  silence; a live page always sends a heartbeat at least once a second.
  Explore doesn't touch the main game yet, so its own raid damage is all
  there is to save; when it joins the game, the game's sync goes in the
  same place (`saveProgress`).
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

## 9. How it went into the game

It was laid out so it could move into the game without a rewrite, and it
did: see §10 for how the game's Explore works. What the notes said before:

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

## 10. Explore in the game

**The pieces.**

| Piece | What it does for Explore |
| --- | --- |
| The game (`index.html`) | The Explore tab in the raid's place (`renderExplore`): the intro, his health from the world server's `/board`, the leaderboard, your swings, and the button into `explore/`. It sends the world server this player's game session to ask; it changes nothing. |
| The page (`explore/`) | In the game's mode (`GAME`), it shows the world server the game session from this browser and plays the pet the server says is yours. An attempt asks the server first (`NET.server.attempt`). The sandbox works as the prototype did. |
| The world server (`explore-worker/`) | Two worlds: `/world` (the game's, verified) and `/demo` (the sandbox). In the game's world it keeps his health, the rounds, the attempts and the leaderboard (`/board`). |
| The Strava worker (`worker/`) | Three routes, all with the player's own session: `/explore/me` (roster handle, pet name, species, level, swings, raid round), `/explore/attempt` (spend a swing) and `/explore/legacy` (the old raid's health and shares, for the handover). Nothing about runs leaves it. |

**Who you are.** The page reads the game's session from this browser
(`runmon.strava.session`) and sends it as its first message. The world server
asks the Strava worker who it belongs to (`/explore/me`, cached ten minutes)
and plays that pet: its name, species and level as the game's roster has
them, so nobody can enter as another pet or another level. A session the game
doesn't know is turned away (`4001`), and the page says to link Strava.

**Attempts and damage.** An attempt asks the world server, which spends one
of the player's swings at the Strava worker (`/explore/attempt`). Refused, the
page says how far the next swing is. Granted, the server opens a window in
which this player's damage may grow, by no more than a pet of its level could
do in one attempt (`ATTEMPT_CAP`, about three times the best a near-perfect
player managed in simulation). Damage outside an attempt, damage under
someone else's name and writes to the round are refused. A player's damage is
kept under their roster handle, so it adds up across attempts, devices and
days.

**Rounds.** The round follows the Strava worker's raid epoch. When he is
felled he stays down. The admin switch that started a new raid before
(`/admin/raid`, POST) still does: the next time anyone asks, the world server
sees the new epoch and starts a new round at full health with an empty
leaderboard. The leaderboard is for the current round.

**The handover.** The first time the game's world opens, it asks for the old
raid (`/explore/legacy`) and carries it over: each player's share is scaled
from the old pool (25,000) to Explore's (110,000), so the same share of him is
gone and the leaderboard starts with the old raid's contributors. Anything the
prototype's world had stored was a test, and is cleared then.

**Linked to Strava as little as possible.** Explore's world, his health and
the leaderboard live in their own worker and storage. All it learns from the
game is a handle, a pet's name, species and level, and whether a swing was
spent. Kilometres stay in the Strava worker, which still decides how many
swings a player has.

**What's left from the old raid.** Its code is still in `index.html`, switched
off by `EXPLORE_TAB`. The centre button keeps its crossed swords.

**Orc Slayer** goes to anyone who took something off him in the round he
fell, as it did for the old raid. The game reads Explore's board
(`exploreCheck`) when the Explore tab opens and after every sync, and once he
is down with your damage on the board it marks the save (`exploreSlain`). The
badge stays earned.

**Levels.** Explore uses the game's own levels: pets evolve into their third
form at 16, and the second forms learn their last two moves at 13 and 15.

**Only your own pet, and only once it has evolved.** The page plays the pet
the server names, at its level, and nothing else. The world has no first-stage
pets, so a pet below Lv 5 can't go in: the game's Explore tab says "Evolve to
explore" with its level and the level it evolves at, and still shows the
board; the page says the same and keeps its buttons off. The world server
enforces it too: it won't relay an unevolved pet's presence or start its
attempt, and it rewrites every player's presence to the name, level and form
their roster level makes them (`formOf`), so no page can show itself as
another form. (Before this, the page lifted a Lv 4 pet to Lv 5.)

**The demo** (`index.html?demo=1`) shows the same tab: the evolve notice
for a pet below Lv 5, and the sandbox world's health and leaderboard
(`/demo-board`), each pet drawn as the form it was played as. Its button opens
the sandbox, and demo.html still links the sandbox directly.

**The leaderboard** draws each pet small, as the Rankings tab does: your own
from the save, everyone else's from their roster card (the board gives each
row's roster handle), with its form and level. A row with no roster card, an
old raid's share say, gets its species' first evolved form.

**No third forms in the game's world yet.** The game's players haven't met
the third forms, so its wild pets stop at Lv 15, the last level before them
(`spawnWild`): the Lv 24 and 34 spawns come out as Lv 15 Cinderlings, Sparkys
and Cubs. The sandbox keeps its evolved wild pets.
