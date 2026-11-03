# Tests

Run all of them before pushing to `claude/runpet-tracker-app-x6ospu` — a push
there is a release (see `CLAUDE.md`):

    node tests/run-all.mjs

Each one also runs on its own, e.g. `node tests/recovery.test.mjs`. They need
Node 20+ and Playwright with Chromium (`require("playwright")` must work).
Nothing is deployed and nothing reaches the network: the real broker code
(`worker/src/index.js`) runs in-process with in-memory Durable Objects and a
fake Strava, and the browser tests serve this checkout's `index.html` locally
and answer its broker calls from that same in-process broker. Screenshots and
JSON land in `$RUNMON_TEST_OUT`, or `<tmp>/runmon-tests`.

| File | What it holds to |
| --- | --- |
| `broker.test.mjs` | The broker's Health routes: linking, the five-day window, overlapping copies taken once, swings for Health-only players only, Health keys kept out of Strava's `importedAt`, adopting onto a Strava athlete, unlink and disconnect retiring the link |
| `health-sessions.test.mjs` | Runs and walks rebuilt from distance slices; a phone and watch copy counted once; pottering ignored; cars, buses and trains dropped on speed and stride; no steps, no outing; a half-finished walk replaced by the whole one |
| `health-app.test.mjs` | The app end to end: setup, three copies of one run counted once, re-sends ignored, moving to Strava, a Strava and Health copy counted once, a failed upload retried without double counting, the horizon held in the app too |
| `health-guide.test.mjs` | The setup guide: opens on Set up, each page, leaving early (red panel, reminder), Finish setup, and the success message on the first word from the Shortcut |
| `health-walks.test.mjs` | Walks pay half and leave mood, streak and "last run" alone |
| `recovery.test.mjs` | Recovery codes across two browsers: saved, restored, a wrong code refused, a new code retiring the old, none for Strava accounts |
| `onboarding.test.mjs` | Strava full: a new player is led to Apple Health; a returning Strava player can still connect |
| `smoke.test.mjs` | The app and the sandbox load with no errors |
| `strava-unchanged.mjs` | **A Strava player's game is exactly what it was.** Runs `strava-scenario.mjs` against a baseline (default `0b59689`, the last build before Apple Health), this checkout, and the baseline app on this checkout's broker — the window between deploying the broker and pushing the app — and fails on any difference but the clock |

`strava-unchanged.mjs` takes another baseline as an argument
(`node tests/strava-unchanged.mjs <ref>`). Use the commit currently live when
a change is meant to leave Strava players alone.

What these do not cover: anything on a real iPhone. The Shortcut, Health's
real data and Safari's storage were only ever checked by hand, on the owner's
phone.
