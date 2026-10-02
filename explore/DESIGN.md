# Runmon Explore — design

A top-down world for the pets. You walk around it, fight wild pets with the
skills yours learnt from running, and team up against a raid boss.

This is a **standalone prototype**. It lives in `explore/`, shares nothing with
`index.html` except the sprite sheets in `art/`, and never reads or writes a
save. Its job is to answer one question before anything goes into the real
game: *is this fun with the art we already have?*

▶ Play it at `explore/` next to the game (on Pages:
`https://ryancgq.github.io/runmon/explore/`). Locally, serve the repo root
(`python3 -m http.server`) and open `/explore/`. It fetches `../art/`, so
opening the file straight from disk won't work.

---

## 1. Where it fits in the game

Runmon has one rule underneath everything: **running is the only way to grow.**
Explore must not break that rule, so:

- **Exploring earns no XP.** A pet's level, stats and skills all come from
  its running level, the same as now. Explore is somewhere to *use* that
  growth. It is not a second way to get it.
- **What Explore does pay out** is 💠 *shards*. In the prototype they only
  count up. In the real game they would buy cosmetics (hats, trails, arena
  banners) and nothing that adds power.
- **The villain is the rest day.** In the core game a pet sulks and then
  falls asleep if you stop running. Lord Lull, the raid boss, is that idea
  given a body: a huge plush sleep-spirit in a nightcap who wants everyone to
  lie down. His attacks put pets to sleep, and the way to beat them is to keep
  moving.

Two ways to tie it to real running are left open for later (§9): energy that
running refills, and a weekly raid whose HP the whole player base chips away
at with kilometres.

## 2. The world

One 84×64-tile map (32 px tiles). It is generated from a fixed seed, so it
comes out the same every time, and it has five areas:

| Region | Where | Ground | Props | Wild pets |
| --- | --- | --- | --- | --- |
| **The Trailhead** | centre-south | meadow, paths, ponds | oaks, bushes, campfire | — |
| **Verdant Grove** | west | moss | bamboo, mushrooms | Bamboo Cub, Panda |
| **Ember Crags** | east | ash, lava cracks | basalt spires | Cinderling, Blazewyrm |
| **Nimbus Heights** | north-west | cloudstone | storm crystals | Sparky, Zephyrite |
| **Lord Lull's Hollow** | north | rune flagstones | ring of standing stones | the raid |

- **Campfire**: stand next to it to heal. It is also where you wake up after
  fainting.
- **Pickups** come back after a while: 🍓 berries heal 30%, and 🌰 acorns
  (the Sparky's acorn, found in Nimbus country) give shards.
- Each region has its own weather: embers drift in the Crags, leaves blow
  through the Grove, and sparks hang in the Heights.

The camera is top-down with a slight tilt, the way most monster-collecting
RPGs do it, so the pets' front-on 3/4 art reads correctly. **None of the pet
sheets had to be redrawn from above.**

## 3. Controls

| | Touch | Keyboard |
| --- | --- | --- |
| Move | drag anywhere on the left half (floating stick) | WASD / arrows |
| Tackle 💨 | big button | Space / J |
| Skills | up to three buttons | 1 2 3 / K L ; |
| Start the raid | button inside the Hollow | E / Enter |
| Pause / tools | ☰ | Esc |

Skills **aim themselves** at the nearest enemy. Aiming by hand on a phone,
mid-dodge, was the first thing that felt bad, and every move here is short
range anyway.

## 4. Combat

Combat is real-time and happens right in the overworld, with no separate
battle screen. That fits a top-down world, and it is the only way a raid with
three pets and a boss could work.

**Stats** come from the running level: HP = (70 + 9·lv) × the species'
multiplier, and ATK = 10 + 1.6·lv. Species have different feels:

| Species | Speed | HP | Beats |
| --- | --- | --- | --- |
| Ember | 150 | ×1.00 | Verdant (fire burns forest) |
| Verdant | 132 | ×1.18 | Nimbus (forest grounds storm) |
| Nimbus | 172 | ×0.90 | Ember (storm rain douses fire) |

A type advantage deals ×1.5 damage and a disadvantage ×0.67, with an 8% crit
chance on top.

**Tackle** is the move every pet has: a 0.19 s dash, 0.65 s cooldown. While
dashing **you cannot be hit**. That one rule is what makes dodging feel good,
and the boss is built around it.

### Skills: the existing animation, with gameplay on top

Every skill plays **its real sheet from the game**, with the same frames,
`order` and `durations` copied from `SKILLS`, sped up to `CLIP_SPEED = 0.6`.
The pet screen deliberately runs these 1.6–2× slower than combat speed,
because there a skill is something you watch. Here it is something you use.

The gameplay effect fires on an **impact beat**: the frame where the drawing
lands. The hitbox and the art therefore go off together.

All seven sheets turned out to animate in place (the lightning lands beside
the pet, Green Gale vents out the back, the swoop comes back home). That means
they drop into a top-down world unchanged.

| Skill | Pet | Kind | What it does here |
| --- | --- | --- | --- |
| 🔥 "fireball" (fizzle) | Cinderling | joke | 3 s of wind-up and then a cough: weak damage to anything adjacent. **15% of the time it actually works** and a huge fireball comes out. The joke stays a joke, but you can't rule it out. |
| ⚡ Spark | Sparky | nova | Damages and stuns everything nearby, and **singes the squirrel** for 6% of its own HP. |
| 🍃 Green Gale | Bamboo Cub | cone | The cub **turns its back** on the target. Knockback, damage, and a "stinky" slow. |
| 🔥 Fireball | Blazewyrm | projectile | The ball is let go on the frame the sheet releases it. |
| 💥 Flame Stomp | Blazewyrm | nova | A big ring of fire with knockback and screen shake. |
| ☄️ Flying Swoop | Blazewyrm | dash | Travels 250 px while the sheet's swoop plays, can't be hit, and leaves burning ground behind. |
| 🌩️ Lightning Bolt | Zephyrite | strike | The bolt comes down **on the target** within 330 px. |

The three baby moves are still the joke the README describes, but each joke
now has a tactical side. That was a design goal: a Cinderling player should
laugh at the fizzle *and* sometimes want to use it.

The Panda has no skill in the core game, so here it only has Tackle. It is on
the select screen on purpose, to show how thin a pet without skills feels.
That is an argument for drawing it one.

## 5. Wild pets

Fifteen wild pets roam their home regions at levels 9–24, and each species
has its own temperament:

- **Ember** is aggressive and will start a fight from 220 px away.
- **Nimbus** is skittish and only gets close (130 px) before reacting.
- **Verdant** is passive and never starts a fight, but fights back.

Wild pets use the same skills and AI as everything else. They give up and heal
if dragged more than about 520 px from home, drop shards (and sometimes a
berry) when they faint, and come back after 28 s, though never while you are
standing on their spot.

## 6. Raid boss: Lord Lull

> *Here sleeps Lord Lull. Let him lie.*

He sleeps in the Hollow until you walk in and press **Wake Lord Lull**. A
barrier then closes the ring, and **two allies** arrive: one of each of the
other two species, at your level. That shows the co-op shape a real raid would
have.

HP is scaled to the party (60 × the sum of their ATK), which gives about a
two-minute fight. An autopilot that only stands still and mashes buttons
clears it in about 1:30 with god mode on.

| Move | Tell | What it does | Counter |
| --- | --- | --- | --- |
| **Pillow Slam** | red ellipse under a pet for 1.15 s, arms raised | A pillow drops out of the sky: heavy damage and knockback | Walk out of the circle |
| **Yawn** | 1 s inhale, "Yawn – dash through it!" | An expanding ring. Anything it touches **falls asleep** for 2.3 s, shown with the pet's own eyes-shut frame | **Tackle through the ring** (i-frames) |
| **Counting Sheep** | "one... two... three..." | Summons 3–4 Snoozlings that hop at the nearest pet and bonk | Kill them, or let them pop on a tank |
| **Lullaby** (phase 3) | gold shield and music notes | A 6.5 s channel behind a shield worth 9% of his HP. If the song finishes, Lull heals 12% and **everyone falls asleep** | Burst the shield. Breaking it stuns him for 3.2 s and he takes ×1.5 damage |

**Phases.** Phase 1 runs from 100% to 55%. In phase 2 (55%–25%) he enrages,
turns magenta, the slam drops three pillows and every tell is 25% faster.
Phase 3 (below 25%) adds the Lullaby, up to twice.

**Fainting in a raid.** A fainted pet gets back up after 6–8 s at half HP, as
long as someone is still standing. If all three are down, the raid fails.
Afterwards there is a damage table, and a choice of *Fight again* or *Back to
exploring*.

The allies' AI walks out of slam circles, and about half the time it dashes
through yawns. They are allowed to be imperfect, so a good player
outperforms them.

## 7. Art

### Reused from the game, with no changes

- All six idle sheets and all seven skill sheets, with their `aspect`,
  `scale`, `dx` and `dy` copied from `DEFAULT_SPRITES` / `SKILLS`. A pet in
  the world is the pet on the pet screen, just smaller (a 66 px box for a baby
  form, 80 px for stage 2, so growth still shows).
- **Walking** has no frames of its own yet. Each form names two clean,
  eyes-open idle frames (`walk`) that alternate under a procedural hop,
  squash and tilt, plus dust puffs.
- **Sleeping and fainting** use an eyes-shut idle frame (`doze`). The
  Panda's own snoring frame is the best of them.
- Each sheet is resampled **once per frame at exact device size** and cached.
  Drawing a 400 px painted frame down to 80 px every tick looked shimmery and
  cost too much.

### New, generated for this (`explore/art/`)

`explore/tools/make_assets.py` draws these in plain Pillow. It is
deterministic, so re-running it gives identical files. Everything is drawn at
native size and scaled up by a whole number, following ART-SPEC §5, with the
pets' chunky dark outline and upper-left lighting so it sits next to them.

| File | What | Size |
| --- | --- | --- |
| `tiles.png` | 16 ground tiles: grass ×4, path, water ×2 (animated), sand, ash, lava crack, moss ×2, cloudstone ×2, arena flagstone, rune | 16 px native → 32 px |
| `props.png` | oak, bamboo, basalt spire, storm crystal, boulder, berry bush, standing stone, campfire ×2, sign, acorn, berries, mushroom | 32×48 → 64×96 |
| `boss-lord-lull.png` | Lord Lull, 15 frames: idle breath ×4, slam wind-up ×2, slam ×2, yawn ×2, hurt, rage ×2, defeated, asleep | **384×288, ART-SPEC's canvas**, feet on y = 264 |
| `snoozling.png` | the sheep he counts: hop ×3, hit, asleep ×2 | 32×24 → 96×72 |

These are placeholders that are *good enough to judge the game with*. They are
not final art. Lull in particular should go to the same artist as the pets if
this ships.

### What to ask the artist for if this ships

In priority order:

1. **A walk cycle per form**: a 6-frame side-on loop on the ART-SPEC canvas
   and baseline. Facing right only, because the game mirrors it. This is the
   single biggest visual gain available; the hop gets the prototype through,
   but you can tell.
2. **A hurt frame and a faint pose per form.** At the moment that is a white
   flash and a tilted, desaturated idle.
3. **Lord Lull and the Snoozling, redrawn properly**, using these sheets as
   the frame list and timing reference.
4. **A tileset in the pets' painted style.** The pixel tiles work, but the
   pets are painted and the ground is pixel art. Hold off on this until 1–3
   have been seen in place.

## 8. How it's built

- **One HTML file, no build step, no dependencies**, the same as the main
  game. It uses Canvas 2D for the world and DOM for the HUD.
- The sprite and skill tables at the top are **copies** of the ones in
  `index.html`, marked as such. If this is integrated they become shared
  imports.
- Fixed order each frame: entities → projectiles → effects → camera →
  render → HUD. Draw order is y-sorted (props and entities), with ground FX
  underneath and air FX on top.
- Collision is circle-against-tile. The boss is a squashed circle. Pets push
  each other apart.

### Testing hooks

| URL | |
| --- | --- |
| `?go=1&pet=blazewyrm` | skip the select screen |
| `?go=raid&pet=cub` | straight into the raid |
| `&level=40` | override the level |
| `&god=1` | take no damage |

The ☰ menu also has teleports to camp and the arena, a full heal, god mode,
hit-circle display, and a live level slider. `window.__G` exposes the game
state for the console.

## 9. Open questions

The prototype is meant to help answer these:

1. **Is it fun at baby level?** At Lv 8 with one joke move, is the raid
   satisfying or just frustrating? If it is frustrating, raids may need a
   minimum form (stage 2).
2. **Energy from running.** One option is a "trail energy" bar that each km
   refills and each exploration minute or raid entry spends. That would tie
   Explore to running directly, but it also gates fun behind exercise, which
   may be the right call or may be off-putting.
3. **Real multiplayer raids.** The obvious shape is *asynchronous*: a weekly
   Lord Lull whose HP is shared across all players, where your damage is
   scaled by the distance you ran that week. Synchronous co-op would need a
   server, and the game deliberately has almost none.
4. **PvP.** Fighting a friend's pet as an AI "ghost" (stats plus skills,
   played by the same AI the allies use) fits the existing Friends feature
   with no realtime networking.
5. **Do the skills need rebalancing for the core game?** They don't today,
   because the core game has no combat. Explore would be the first place
   their numbers matter.

## 10. If it graduates

1. Pull `FORMS` / `SKILLS` geometry out of both files into one shared table.
2. Read the real save **read-only** for species, stage and level, and keep
   Explore's own state (shards, cosmetics) under a separate key.
3. Commission art in the §7 order.
4. Add an **Explore** entry point on the pet screen behind a setting, the way
   the sandbox is kept apart today.
