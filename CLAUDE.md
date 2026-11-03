# Notes for Claude

## How this ships — read this before saying anything about deploying

**GitHub Pages serves `claude/runpet-tracker-app-x6ospu`, not `main`.**

Pushing to that branch puts the app in front of real players within about two
minutes. There is no staging step and no merge required. Check it rather than
assuming — the Pages source is a repo setting, not a workflow file, so nothing
in `.github/workflows/` reveals it:

```
# which branch did Pages actually build from?
mcp__github__actions_list → list_workflow_runs, look for
"pages build and deployment" and read its head_branch
```

I told the user twice that the app ships from `main` and that merging was
needed to release. Both were wrong, and the second time they had already seen
the feature live on their phone. The visible cost was small; the real cost is
that advice about release timing was confidently wrong.

`main` is a lagging snapshot that only ever receives this branch's work back
through PR merges. It has never carried independent development. Git may report
`main` as "N commits ahead" — that is merge commits, not content. Since November
2026 the repo's **default branch is the live branch**, so a fresh clone or
session starts on live code; one session before that built a whole feature on
a `main` 156 commits stale before anyone noticed.

### Releasing a change that touches the broker

Deploy the broker from the work branch **first** (Actions → Deploy the Strava
broker → that branch), check the run succeeded, **then** fast-forward the live
branch to it. The broker must keep serving the live app in the gap — test that
with `tests/strava-unchanged.mjs`, which runs the old app against the new
broker. An app-only change needs only the push; check with
`git diff --stat <last deployed commit> HEAD -- worker/`.

### Consequences that follow from this

- **The worker cannot be deployed "first" after the app code is already
  pushed.** The push ships the app immediately, so the worker can only catch
  up. To genuinely land the broker first, deploy it from a commit *before* the
  app change reaches this branch.
- **A push is a release.** Anything gated on "when we merge" — a feature flag,
  a notice to players, a migration — has to be decided before pushing.

## Deploying the worker

Actions → **Deploy the Strava broker** → Run workflow → pick the branch. The
checkout step pins no `ref`, so a manual dispatch deploys whichever branch is
selected. All five secrets are configured and working.

Test it locally before deploying: `npx wrangler@4 dev --local` with a throwaway
`SESSION_SECRET` in `worker/.dev.vars`, mint session tokens with the same
base64url HMAC the worker uses (**not hex** — this has cost two debugging
rounds), and drive the routes over HTTP. Delete `.dev.vars` and `.wrangler`
afterwards; there is no `.gitignore` in this repo.

## Credentials

The user has been explicit and it still stands: never ask for, generate, or
handle their Strava client secret, `SESSION_SECRET`, `ADMIN_TOKEN` or
Cloudflare credentials. Generating a secret for them puts it in the transcript,
which defeats the point. Strava's terms also forbid putting activity data
through an AI system, so never ask them to paste run data.

## Strava's API rules are load-bearing — don't regress them

The app is being submitted for Strava's athlete-capacity review, and the code
is built to its API Agreement and API Policy (2026). README → "Strava's rules"
has the full list; the ones easiest to break by accident:

- Nothing Strava measured (distance, run count, run times, dates) goes on a
  card, Rankings, the dashboard or a backup. Cards are `rosterCard()` fields only.
- A run is folded into `save.past` after six full days (`foldOldRuns`); every
  replay of mood/streak must go through the seeded functions, and
  `foldeq.mjs`-style equivalence (full log vs folded) must still hold. A
  linked phone must sync *before* it folds: folding first misprices every run
  from a player's absence and cuts their streak (it did, once).
- Disconnected players and deleted pets are erased after `GRACE_DAYS` (28) —
  never "kept forever". Strava's limit is 30.
- No lifetime distance anywhere. No Strava data, or anything derived from it,
  into any AI — including this chat.

## Apple Health — and keeping Strava players exactly as they were

Runs also come from Apple Health, through an iPhone Shortcut (README → "Apple
Health"). With Strava's athlete cap reached it is the way in for new players.
What to hold to:

- **A player connected to Strava must not notice any of it.** `healthOn()` is
  false for them unless they set Health up themselves, and anything Health adds
  hangs on that or on `save.healthLink` — not on "has a broker session", which
  Health-only players have too (`stravaLinked()` means the latter;
  `stravaAthlete()` means Strava). Every change near this gets
  `node tests/strava-unchanged.mjs <live commit>`: identical, or it does not ship.
- **`STRAVA_FULL`** closes Strava to *new* players only. Anyone who has played
  with Strava before (`stravaReturning()`) can always connect — a new phone,
  a disconnect inside the four weeks, Strava asking again. Set it to `false`
  when the athlete-capacity review comes through.
- **A run is counted once whatever it came through**: any run whose span
  crosses one already held is the same run (`runOverlapping`). That only works
  while the other copy's times still exist — Strava runs lose theirs when they
  fold at six days — so Health only takes outings **under five days old**, in
  the broker (`HEALTH_HORIZON_MS`) and the app alike. Don't widen one without
  the other, and don't widen past the fold.
- **Health keys never go into `importedAt`.** Pruning it moves Strava's fetch
  floor up to each id's start time, so a Health time in there stops real
  Strava runs being fetched. They travel as `healthDone`.
- **Swings from Health are paid only to Health-only players**, per outing
  taken — the broker cannot see a Strava copy to tell one run from two.
- **Shortcuts cannot read workouts** on current iOS, so runs and walks are
  rebuilt from Walking + Running Distance slices, checked against Step Count
  for vehicles (`sessionsFromSamples`). The thresholds were set on simulated
  data; real outings are the test that matters.
- **Health-only players have no Strava to sign back in with.** Their session is
  the only key to their pet; the recovery code is the second. Never make the
  Shortcut's sync link able to read a save — it is in a file people share.
- The shared Shortcut's link is `HEALTH_SHORTCUT_URL`. A new share must carry
  an **import question with an empty default** on Get Contents of URL; the
  first one did not, and would have sent every new player's runs to the
  owner's pet. Check by opening the link and seeing it ask.

## Tests

`node tests/run-all.mjs` before every push to the live branch — see
`tests/README.md`. The real broker runs in-process with a fake Strava, and the
browser tests drive this checkout's `index.html` against it. They cover the
code, not an iPhone: the Shortcut and Health's real data are checked by hand.

## The app is one file with nine separate `<script>` blocks

`index.html` is ~10,600 lines. The blocks are **not** one scope at parse time: a
`const` declared in a later block is invisible to an earlier one during
top-level execution, and cannot be reassigned or stubbed from outside. This has
bitten twice while testing (`stravaLinked`, `stravaCall`). Use Playwright
`page.route()` network interception instead of trying to stub functions.

## Conventions

- `BUILD_ID` names the **previous** commit's sha — check with
  `git show <prev>:index.html` rather than guessing.
- Commit messages are long and explain *why*, including what was tried and
  failed. Match that register.
- Code comments carry the reasoning, not a restatement of the code. Match the
  density of the surrounding block.

## Verify in a real browser

Every graphical or gameplay claim in this project has to be checked by running
it, not by reading the code. Inspection has produced confident wrong answers
several times — including a "12 of 16 frames play" measurement that was really
a parent transform scaling `getBoundingClientRect()`, and an assertion that a
sprite grid was aligned when it was not. `offsetWidth` is unscaled by
ancestors; `getBoundingClientRect()` is not.

Simulate balance changes against the real engine rather than reasoning about
them. It has overturned confident guesses more than once — most recently the
claim that a five-level gap is a near-even fight, when the attacker wins 11%.
