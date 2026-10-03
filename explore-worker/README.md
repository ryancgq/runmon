# Runmon Explore — world server

The shared world for the Explore prototype (`explore/`) when it is played
outside Claude, at `ryancgq.github.io/runmon/explore/`. It is a separate
Cloudflare Worker from the Strava broker in `worker/`, named
`runmon-explore`, with its own storage and its own deploy. It holds no game
rules and nothing from Strava, and it never touches the game or its saves.

It does two things over one websocket at `/world`:

- **Presence.** Each page sends its own state about ten times a second, and
  the worker relays it to everyone else. This is kept in memory only.
- **His health.** Sir Uwaaarghhhh's account is kept as small documents in
  the Durable Object's SQLite storage: the round in `raids/state`, and each
  tab's damage in `raids/e<round>/hits/<tab>`. Values only move forward, so
  a late or repeated write can't undo anyone's damage.

Inside Claude the page uses the Artifact page's own `room` and `db` instead.
This worker speaks the same two shapes, so the game code is the same either
way (see `openServer` in `explore/index.html`).

## Deploy

Pushing a change under `explore-worker/` to the Pages branch or `main`
deploys it (`.github/workflows/deploy-explore.yml`). It uses the same two
Cloudflare credentials as the broker and needs no secrets of its own.

## Settings (`wrangler.toml`)

- `ALLOWED_ORIGINS`: the pages allowed to connect.
- `JOIN_CODE`: unset, anyone with the link can join. Set it, and players need
  `?code=<it>` on the link.

## Test locally

```
cd explore-worker && npx wrangler@4 dev --local --port 8787
# serve the repo root on :8765, then open
# http://localhost:8765/explore/?server=ws://127.0.0.1:8787/world
```

Delete `explore-worker/.wrangler` afterwards.
