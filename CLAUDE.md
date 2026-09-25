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
`main` as "N commits ahead" — that is merge commits, not content.

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

## The app is one file with nine separate `<script>` blocks

`index.html` is ~6,400 lines. The blocks are **not** one scope at parse time: a
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
