# Mob generation prompts

Explore has four creatures that were never anybody's pet. Their sheets
(`mob-*.png` here) were generated from these prompts. They are drawn in **the pets'
own language** — the reference is the Cinderling: one round, fuzzy ball of a
body, big glossy eyes with a heavy top lid and white highlights, small paws
tucked in front, soft shading lit from the upper left, a thick dark outline.
A mob should look like it could live next to a pet, not like an enemy from
a different game. Unlike a pet it has no moods to show; it has two attacks.

Paste **Subject** + **Size in frame**, then the **Mob sheet block**.

## Mob sheet block

```
SHEET FORMAT
Pixel art sprite sheet: 16 frames in a 4x4 grid, 4 columns by 4 rows, read
left to right then top to bottom. Every frame the same size, the creature
drawn at the same scale and in the same spot in each one, its feet resting
on a single shared horizontal line so it never drifts up or down between
frames (a floating creature: its lowest point on that line). Three-quarter
side view, facing right, throughout. Same character, same palette, same
silhouette in all sixteen frames.

BACKGROUND
Fully transparent. No scenery, ground, floor, grass, rocks, sky or horizon.
No shadow cast beneath the creature. No borders, gutters, panels or labels
dividing the cells. If transparency is not available, use flat magenta
#FF00FF and nothing else behind the creature.

STYLE
Cute chibi pixel art, matching a round pink baby dragon with big glossy eyes:
a round soft body, big shiny eyes with white highlights and a dark upper lid,
small paws in front, soft shading lit from the upper left, a thick dark
outline. Hard-edged pixels, no blur. The face must stay legible when the
sprite is shown small.

FRAMES, in this exact order
 1-4   idle: breathing gently, content; frame 4 is a blink
 5     knocked out: squashed flat, dizzy X eyes, mouth a small "o"
 6-10  FIRST MOVE (described in the subject), cross face, in five steps:
       wind-up, wind-up held, the strike, follow-through, settling back
 11-16 SECOND MOVE (described in the subject), cross face, in six steps:
       wind-up, wind-up held, the strike, follow-through, recovering,
       back to calm

AVOID
Backgrounds of any colour, ground or terrain, cast shadows, cell borders,
text, frame numbering, watermarks, a border around the whole sheet, any
change of camera angle or creature size between frames, and anything
scary or realistic.
```

## Mob subjects

| Mob | Subject line | Size in frame |
| --- | --- | --- |
| Bramble Boar (meadow) | `SUBJECT: a round little wild piglet, warm pinky-tan fur, a pink snout, two tiny cream tusks, pointed ears, a hedge of green leaves and small thorns growing down its back with one pink berry in it, a curly tail. FIRST MOVE: it paws the ground, lowers its head and charges forward with dust kicking up behind. SECOND MOVE: it rears up on its back legs and stomps down, dust bursting out on both sides.` | ~65% |
| Cinder Beetle (Ember Crags) | `SUBJECT: a small round beetle, a dark charcoal dome of a shell with glowing orange lava cracks along it, a warm glowing orange face on the front of the ball, two short antennae tipped with embers, six stubby legs. FIRST MOVE: it tucks in and rams forward, sparks trailing behind it. SECOND MOVE: it rears its head back and spits a small fireball forward.` | ~55% (it comes in threes) |
| Puffcap (Verdant Grove) | `SUBJECT: a walking toadstool, a big round red cap with cream spots worn like an oversized hat, a chubby cream stem body with the face on it, rosy cheeks, two stubby feet. FIRST MOVE: it squashes down, then puffs up and bursts out a cloud of yellow-green spores. SECOND MOVE: it leans back and bonks forward with its cap.` | ~65% |
| Static Wisp (Nimbus Heights) | `SUBJECT: a small floating storm cloud, a puffy pale-blue cloud body, a tail of smaller puffs curling down to a point, a little gold lightning bolt sticking up from its head like a tuft, cheeks blushing cyan. It floats and has no legs. FIRST MOVE: it charges up, glowing brighter, and fires a small zap of lightning forward. SECOND MOVE: it crackles all over and lightning bursts out around it in every direction.` | ~60% |

To use a new sheet:

    python3 explore/tools/convert_mob_sheet.py <boar|beetle|puffcap|wisp> sheet.png

It lays the grid out as one 16-frame strip, cleans the background, puts the
feet on one line and saves over `mob-<name>.png` in this folder. The frame
layout above is the one the page already plays, so no code changes are
needed unless the creature comes out a different size (each mob's `scale`
in `MOBS`).

Check each sheet before converting it, as for the pets: 16 frames, the feet
(or a floating creature's lowest point) on one line, real transparency, and
the same creature from the first frame to the last.
