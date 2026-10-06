# Runmon Explore — world server

Explore's shared world, at `ryancgq.github.io/runmon/explore/`. It is a
separate Cloudflare Worker from the Strava broker in `worker/`, named
`runmon-explore`, with its own storage and its own deploy. It never touches
the game's saves and never sees a run.

## Two worlds

- **`/world`, the game's.** Only players who have linked Strava. A page's
  first message is its game session; this worker asks the Strava broker who
  it belongs to (`/explore/me`) and plays that pet, as the game's roster has
  it. Sir Uwaaarghhhh's health, the rounds and the leaderboard are kept here:
  - an attempt spends one of the player's swings at the broker
    (`/explore/attempt`; one swing per 5 km run, counted there);
  - during an attempt a player's damage may grow by no more than a pet of its
    level could do (`ATTEMPT_CAP`); outside one it can't;
  - the round follows the broker's raid epoch. When he is felled he stays down
    until the admin switch (`/admin/raid` on the broker) starts a new one;
  - the first round carries over the old raid's health and shares
    (`/explore/legacy`), scaled to his health here (`RAID_HP`, 110,000).
- **`/demo`, the sandbox.** Anyone, any pet, nothing checked. Its own boss,
  back on his hill 20 seconds after he falls.
- **`/board`.** The game world's leaderboard for the current round, for the
  game's Explore tab. Needs the player's game session.

Over one websocket each world relays **presence** (each page's own state,
sent when it changes and as a once-a-second heartbeat; memory only) and keeps
a small **store** of documents in the Durable Object's SQLite storage
(`raids/state`, `raids/e<round>/hits/<player>`). Inside Claude the page uses
the Artifact page's own `room` and `db` instead, always as the sandbox.

## The broker

Reached through a service binding (`BROKER` in `wrangler.toml`), because a
fetch from one `workers.dev` worker to another on the same account is refused.
The broker has to be deployed with its `/explore/*` routes before this
worker's game world can let anyone in. Locally, set `BROKER_URL` instead.

## Deploy

Pushing a change under `explore-worker/` to the Pages branch or `main`
deploys it (`.github/workflows/deploy-explore.yml`). It uses the same two
Cloudflare credentials as the broker and needs no secrets of its own.

## Settings (`wrangler.toml`)

- `ALLOWED_ORIGINS`: the pages allowed to connect.
- `JOIN_CODE`: unset, anyone with the link can join. Set it, and players need
  `?code=<it>` on the link.

## Idle pages

A live page sends something at least once a second. A connection that has
been silent for two minutes (a frozen or locked phone) is closed (`IDLE_MS`),
and in the game world one that hasn't said who it is within 20 seconds. The
check runs while handling other pages' messages, so it costs no request of
its own. The page also leaves by itself after two minutes without a touch.

## Test locally

```
# a copy of the broker, with a throwaway SESSION_SECRET in worker/.dev.vars
cd worker && npx wrangler@4 dev --local --port 8788
# this worker, pointed at it (BROKER_URL = "http://127.0.0.1:8788", no [[services]])
cd explore-worker && npx wrangler@4 dev --local --port 8787
# serve the repo root on :8765, then open
# http://localhost:8765/explore/?game=1&server=ws://127.0.0.1:8787   (the game's world)
# http://localhost:8765/explore/?server=ws://127.0.0.1:8787          (the sandbox)
```

Delete `.wrangler` and `worker/.dev.vars` afterwards.
