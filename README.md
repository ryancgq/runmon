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

## Strava

Runmon can take its runs from Strava instead of its own tracker: you run with
Strava as normal, open Runmon, and the pet has grown. Connect once and it keeps
itself up to date after that.

New players are asked during onboarding, before they pick an egg — connecting
leaves the page for Strava's consent screen, and losing a chosen egg and a typed
name to that redirect is worse than asking first. Declining is fine: the step
says the offer stands in **Settings → Strava**, which is also where anyone who
skipped it can connect later. The step is skipped entirely for someone already
linked, and in the sandbox, which has no broker to connect to.

A catch-up is replayed rather than applied, whenever the pet screen is next
reached — "Check now" lives in Settings, so a sync practically never finishes
where the pet is, and a replay that only fired on the spot never fired at all. A week of running used to land in
one jump: the pet was simply whatever the total made it, so an egg that should
have cracked twice and hatched arrived already hatched and none of it was seen.
Now every run is stored and uploaded first, and then the pet is walked forward
through them one at a time — each run's own XP, then whichever celebrations that
run earned.

Within a run the earning comes before the reward: the bar runs up to the top of
the level it is on, the celebration plays over a full bar and the form the pet
still is, and only then does the bar reset and carry on with what the run had
left over. Getting that order right meant stopping two other things repainting
mid-walk — `renderHome()` draws the bar, the level badge and the pet together
from `derived`, which during a replay is already the finished total, and a
clip's own teardown does the same when it ends.

The save is never the thing being animated. `recompute()` takes a cursor, so the
displayed state is derived from the runs up to a point while `save.runs` stays
whole; leaving half way through, or locking the phone, loses nothing and the
next render simply shows the real total. Levels are not celebrated one per
level, either — a run big enough to cross four of them inside one form would
play the same clip four times — but every *distinct* celebration along the path
is, which is what makes an egg show both of its cracks and a hatch show the
hatch. Tapping the pet skips the rest; it finishes whatever is mid-flight rather
than cutting a frame, then jumps to the true state.

Nobody has to ask it to check. It syncs when the app opens, when you come back
to the tab, and when you open the pet — each throttled to once a minute so
walking between screens does not hammer Strava. **Check now** in Settings is
only there for impatience. What it cannot do is update while the app is shut:
there are no webhooks and no push, so a run is picked up the next time the app
is looked at, and the catch-up is then replayed rather than applied silently.

Deleting or editing an activity on Strava after it has been counted changes
nothing here, and that is deliberate rather than an oversight: a run's XP is
worked out once at import and stored on the run, the imported list is never
pruned, and no sync removes anything. A pet does not de-evolve because someone
tidied their feed. The cost is that a re-upload of the same run arrives with a
fresh activity id and counts twice, and that manual Strava entries count in
full — both known, both left alone, because this is a game played among people
who know each other.

Only runs recorded *after* you connect count. Your history stays yours — the
pet starts as an egg and grows from your next run, because a pet that arrives
at level forty has skipped the part that makes it a pet.

Runs and trail runs feed it. Treadmill runs are opt-in, because their distance
is whatever the machine said. Rides, walks and hikes are ignored — the pace and
calorie models would read them as impossibly fast or impossibly slow runs.

Once connected, your pet lives on the server rather than in the browser, keyed
to your Strava athlete id, so it follows you between devices. **Disconnect**
revokes Runmon's access at Strava and deletes the pet and its history; there is
no undo.

This is the only part of Runmon that is not a static file, and it exists for
one reason: Strava's OAuth needs a client secret, and a page served from
GitHub Pages cannot keep one. [`worker/`](worker/) is the smallest thing that
can — about 250 lines, one Durable Object per athlete, deployed free on
Cloudflare. It stores the save and returns activities; it knows nothing about
levels. See [`worker/README.md`](worker/README.md) to deploy your own.

`RUNMON_API` at the top of `index.html` points at it. Leave it empty and Strava
is absent from the app entirely: no panel, no network calls. **The sandbox is
always in that state**, so it keeps working offline and needs no worker to test
new artwork against.

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
three crack phases, six moods, four skills, nine level-up celebrations — each
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

Pets with pixel art so far are **Ember** (egg, baby and teen), **Verdant** (baby)
and **Nimbus** (baby and teen).
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
| **Settings** | Strava, units, body weight, simulated GPS, new game |

## The pets

Three species, five stages each, all drawn as inline SVG and animated in CSS.

- **Ember** (fire) — Cinder Egg → Cinderling → Blazewyrm → Pyrelord → Infernarch
- **Verdant** (forest) — Leaf Bud → Bamboo Cub → Fernkin → Thicketmane → Grovewarden
- **Nimbus** (storm) — Static Egg → Puffling → Zephyrite → Tempestor → Thunderarch

Your choice sets the app's accent colour. The pet's expression and idle
animation follow how recently you ran: elated the day you run, happy the day
after, restless at two days, sad at three, and asleep from five.

The Puffling — Nimbus's baby — is a squirrel with a charge in its ears, and its
twelve frames tell the same kind of story the Bamboo Cub's do: it sits, it
blinks, an acorn drops in, it eats. Its sheet has been redrawn once since; the
replacement came with soft edges, which are hardened on the way in because the
app renders with `image-rendering: pixelated` and feathering turns to mush. It
is calibrated to render exactly where the sheet it replaced did — same painted
area to within 1%, same ground line to the pixel — so nothing downstream moved.
The rows still each drew the squirrel higher than the last, so every frame is
pinned to one ground line. Only the squirrel is pinned — the acorn and the
lightning bolts are meant to move, and one of the bolts is drawn straight
across a grid line, so the frames are cut by which piece belongs to which cell
rather than on the grid itself. Cropping on the lines takes the top off that
bolt and leaves its tip lying in the corner of the frame above.

Its caption changed with it. The Puffling was written as a scrap of cloud that
hovers a foot off the ground, which this squirrel plainly does not, so the
description now matches what you see. The species blurb still says Nimbus never
quite touches the ground — true of its other four forms, not of this one.

The Cinder Egg is a sprite too, as of the pack that replaced the vector one.
It arrived as a 3x4 grid on a checkerboard baked into the pixels rather than
real transparency, so the pattern was keyed out and the rim decontaminated —
every edge pixel is background mixed into art, so the art colour is recovered
from the nearest solid pixel and the mix ratio becomes the alpha. Flood the
background in from the border rather than keying every neutral pixel, or the
white highlight on the shell goes with it.

The Static Egg — Nimbus's acorn — followed, as five sheets in the same shape.
Those arrived with real transparency, so no keying was needed. The three idles
were later redrawn and barely drift at all — 2px of baseline, 8px of centre and
no swell whatever, against 23px, 48px and 6% in the sheets they replaced — but
the two transitions are still the earlier art and still drift, so all five are
packed together in one pass: one body size, one anchor, one frame. Packing the
idles alone would have left them a different shape from the transitions and the
egg would jump at every handover. The body is measured as the largest connected
blob, so the sparkles that come and go cannot drag the anchor with them. After
packing, the drift across all sixty frames is 1px, 1px and 2px.

The two transition sheets hold each crack state for two or three frames rather
than drawing twelve distinct ones — the sparkles change underneath, the shell
does not. That is why their burst frames fall where they do.

Eggs crack as they level. They are the one form whose art changes inside its
own stage — intact at level 1, a first split at 2, a full web at 3 — and the
crack is the level-up celebration: `<species>:0@2` and `<species>:0@3` in
`LEVEL_UP_ART` carry the shell from one phase to the next and end on the frame
the new idle opens with, so the celebration and the change of art are one
event. `EGG_PHASES` is keyed by species, and any species with an entry gets
this behaviour; the Cinder Egg cracks on frame 9 both times, the acorn splits
on 7 and spreads on 10, and the Leaf Bud lets its leaves go on 6 and then on 5
— measured off the sheets rather than assumed, here by watching for the frame
where two loose blobs first appear beside the bud. While a level-up is armed the pet is still drawn as it was *before* it,
or you would come home to an already cracked shell and then watch it crack.

The Verdant egg is the exception that proves what the packing is for. It does
not crack — it peels, a full bud at level 1 down to a tight pale core at 3,
310px tall in the pack and then 226px, a layer of leaf gone each time. So its
three phases are packed in one pass like the other two eggs, sharing a frame,
a ground line to a pixel and a centre to about one, but they are deliberately
*not* normalised to a common body size the way the shell phases are.
Normalising is right when the art is the same object changing state and wrong
when the change of size **is** the state. All three sit on the same ground
line, so the bud shrinks down onto it rather than drifting.

Its two transitions then raise a problem the other eggs never had. Each one
shrinks its bud harder than the two phases it joins differ — about 17% against
the phases' 10% — so no single scale can make both of its ends match. The ends
really are the same drawings as the idle frames, which is how you can tell:
registered against them they sit at 0.95 to 0.98 IoU, and they ask for 0.977
at the first frame and 1.068 at the last (0.990 and 1.092 for the second
transition). One factor would leave a visible step at one end, or a smaller one
at both. So each transition carries a scale **ramp** across its twelve frames
instead. Both handovers then land exactly — measured on the pet screen, the
clip's last frame and the idle that replaces it differ by 0.4% in area and not
at all in ground line — and the correction works out at 0.8% a frame, spread
under leaves flying off the bud.

A celebration's sheet is not the sheet the pet is already wearing, and a CSS
background does not start loading until something paints it — which for a
celebration is the instant the clip takes over from the idle. So the first play
of any celebration left a hole where the pet should be, and every play after it
was fine, because by then the file was cached. The wind-up is a second and a
half of cover doing nothing, so the fetch starts there instead. Throttled to
120 KB/s the pet used to vanish for about a second; now it does not dip at all.

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

The Puffling's celebration is the one that charges rather than flashes: two
calm frames, a build through six, a spike-ring on frame 7 held over 8, then four
frames of sparkles easing back to the pose its idle holds. The beats were read
off the sheet's own cyan pixel count, which runs about 1,100 at rest, 33,000 on
the burst and 1,100 again by the last frame — a more honest signal than counting
frames by eye.

Its rows drift like the rest, 5px and 51px, but the usual body measure fails on
it: at the burst the lightning washes over the squirrel and a dark-pixel mask
loses most of it, reporting the pet a dozen pixels higher than it is. Take the
baseline from the least-lit frame of each row and correct per row, not per
frame. Per frame would also cancel the crouch the squirrel does before it fires,
which is animation, not drift.

The Zephyrite's celebration works the same way as the Puffling's and needed
the same care, with one number different: its effect pixels - cyan aura and
orange bolts together - rest near nothing, build from frame 3, and peak on frame
8 rather than 7, so its flash is told to land a frame later rather than
inheriting the baby's timing. Its rows drift 20px and 33px, and again the burst
frames read low because the aura washes over the squirrel's outline, so each
row's baseline comes from its least-lit frame. Frames 1 and 12 were 33px apart
and now share a ground line exactly.

Fitting it against its idle is where the measuring went wrong twice. The total
bounding box compares effects rather than the pet - the celebration's first
frame carries bigger lightning than the idle's - and the largest dark blob in
the source art turned out to be the squirrel merged with a bolt's outline, which
put the scale out by 16%. The white face and chest is the landmark that works:
no bolt or aura shares it, and it is the same feature in both sheets.

The Bamboo Cub's celebration needed something else again. Its green bloom is
drawn on two frames of twelve, and walked straight through the template those
two got 165ms between them while the 960ms settle landed on a frame that is
just the panda back at rest: the biggest moment in the sheet was over before
you could see it. The fix is not new artwork but an `order`, the frame list a
clip can name instead of counting 1..12 — here it cycles the two bloom frames
across the flash and most of the settle, so the aura churns for 666ms and then
dissipates. They are genuinely different drawings, rays pointing elsewhere in
each, so cycling them reads as sustained energy where holding one would read as
a freeze. The clip still runs to the same 2,250ms as every other celebration
and the confetti still goes off on 810ms.

The cub's skill sheet needed one thing none of the others did. Its twelve
frames arrive as a 4x3 grid, and the top row's paws run six pixels past the
line an even split of the sheet's height would draw. Cut there, those six rows
of black were not lost - they landed at the top of every frame in the row
below, and played back as two small dark crescents hanging in mid-air above
the panda while it charged. The fix is to cut on the sheet's own rows: the
bands of actual content, found by looking for the empty rows between them,
which here sit 77 to 99 pixels deep and leave no doubt where one row ends.
Column boundaries did fall where an even split puts them, checked the same
way. Worth doing for every sheet from now on - an even split is an assumption,
and this one had been quietly wrong.

The same sheet then needed the anchoring taken a step further than any before
it. The other packs correct a drift that is regular - each row drawn a little
higher than the last - and one ground line per row is enough to answer it.
This one drifts about ten pixels left per column as well, and underneath both
it simply does not draw the cub in the same place twice: 55 source pixels
between the leftmost frame and the rightmost, which on the pet screen was the
cub hopping some 26 pixels about the stage while it charged. So every frame is
anchored on its own here. The floor fixes y, because the cub is planted in all
twelve frames and its lowest pixel is the ground line, and the body's centre
of mass fixes x. The head alone and the paws alone were measured too; the
whole body scored best, taking frame-to-frame overlap from 0.77 to 0.86. What
is left on screen is a pixel of wander and no bob at all: the cub's ground
line lands on the same row in all fourteen beats of the clip.

That sheet also arrived keyed on blue rather than with an alpha channel of
its own, which the earlier ones had. Keying it is the same three steps as
anywhere: take the key colour from the sheet's own border rather than assuming
`#0000FF`, since this one sits at (0, 8, 253) and wanders a few values either
side; keep only the blue that reaches the border, so a gap between two paws
stays a gap but nothing inside the cub is cut away; and solve the edge pixels
for how much of each is cub and how much is key, then clamp any blue left in
them back down. Nothing in this art is meant to be bluer than it is red or
green, which is what makes that last step safe.

Matching two sheets by their silhouettes turns out not to be enough. The idle
and the skill measured within a percent of each other - registered against one
another at every combination of resting poses, the best fit sat at 0.99 to
1.03 - and the cub still read as the larger animal on the pet screen, where
the two swap on the same spot a second apart. The drawings differ where the
eye looks: rounder cheeks and a bigger eye on the idle sheet. So the idle is
taken down 4% against a judgement rather than a measurement, and its dx and dy
move with the scale so the ground line stays exactly where it was, which is
what the skill and the celebration were both fitted against. The celebration
is now the outlier at around 14% larger than the two of them.

An `order` turns up a second problem worth naming, because it applies to every
clip with its own timing. A keyframes rule that stops at its last frame has no
100% stop, so the browser writes one from the element's own style — which is
frame 1 — and a finished clip snapped back there for the moment before its
teardown. Barely visible on a celebration, plainly wrong on an egg, whose first
frame is the shell still whole. The generated rule now ends on an explicit stop
holding the last frame.

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
[`art/verdant-bamboo-cub.png`](art/verdant-bamboo-cub.png). The Verdant egg
ships as five: three phases,
[`art/verdant-egg.png`](art/verdant-egg.png),
[`-cracked`](art/verdant-egg-cracked.png) and
[`-breaking`](art/verdant-egg-breaking.png), and the two transitions between
them in [`-crack-1`](art/verdant-egg-crack-1.png) and
[`-crack-2`](art/verdant-egg-crack-2.png). The rest are inline SVG.

Note that this pet plays one continuous loop rather than a per-mood animation,
so its face cycles through every expression regardless of how recently you ran.
The engine still supports mood rows (`moods` below); this sheet just does not
use them.

## Skills

A form is not the end of a stage, it is the start of one: a pet keeps learning
inside the form it grew into. The Cinderling, the Puffling and the Bamboo Cub
have one move each, all at level 8; the Blazewyrm learns all three of its own
between level 15, where the form arrives, and level 30, where the next one
does; and the Zephyrite has the first of its own at 18, the same level the
Blazewyrm starts.

| Skill | Form | Learns at | What it does |
| --- | --- | --- | --- |
| 🔥 fireball | Cinderling | Level 8 | Sold as the strongest fire you will ever see. Three seconds of winding up, then a cough and some smoke. |
| ⚡ Spark | Puffling | Level 8 | Guaranteed to leave something scorched. The something is the squirrel. |
| 🍃 Green Gale | Bamboo Cub | Level 8 | The forest's strength, gathered and released. Out of the wrong end. |
| 🔥 Fireball | Blazewyrm | Level 18 | Draws a breath and spits a packed ball of flame |
| 💥 Flame Stomp | Blazewyrm | Level 22 | Lands hard enough to throw a ring of fire out around it |
| ☄️ Flying Swoop | Blazewyrm | Level 26 | A low, fast pass trailing fire |
| 🌩️ Lightning Bolt | Zephyrite | Level 18 | Asks the sky for help. The sky, this time, obliges. |

All three babies' moves are the same joke told three times, which is
deliberate: a first skill is named for what the pet thinks it is doing. The
Cinderling coughs smoke; the Puffling's Spark gathers the whole storm and
earths it through itself, and spends the last second and a half sitting there
singed while the smoke drifts off it; the Bamboo Cub braces, pulls a whole
orbiting ring of green in around itself over six quickening frames, and opens
the wrong end. Its timing is built around the beat rather than the build. The
ring reaches its widest and then frame 7 draws nothing at all — no orbs, no
trails, only the cub straining — and that stop gets the longest hold in the
clip, 600ms, the one beat with no effect on screen anywhere. The joke is the
pause, not the puff. What follows is the punchline and is paced like one:
1.66 seconds over three frames, more than the whole charge takes, because a
fart that goes past in a tenth of a second is a fart nobody saw. The cub
spends the last second and a half lying flat, glancing left and right — the
two flattened frames alternate, so it is checking whether anyone saw rather
than lying perfectly still.
The Zephyrite's is the same idea grown up and not played for laughs: it
gathers, the sky answers with an orb, and a bolt comes down. Its charge quickens
the same way, but the four strike frames grow rather than flicker, so they are
held instead of cycled and the last one holds longest.

Its charge frames genuinely progress — the bolts multiply — so unlike the
Cinderling's they are not cycled, just slowed and then quickened, from 400ms a
frame down to 170. What is cycled is the discharge, two frames alternating so
the light flickers, and the aftermath, two more so the smoke moves.

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

### The art is fixed

Every pet is a sheet in `DEFAULT_SPRITES`, keyed `"species:stage"`, and there is
no way for a player to substitute their own. The settings panel that allowed it,
its console methods and the per-device `save.sprites` override are all gone: in
a game people play against each other, everyone should be looking at the same
creature. Adding or changing art means editing `DEFAULT_SPRITES` and shipping
it, which is what `ART-SPEC.md` describes.

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
