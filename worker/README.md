# Runmon's Strava broker

Runmon is a static file. Strava's OAuth needs a client secret. A static file
cannot keep one — that is the whole reason this directory exists.

It is not a game server. It stores the save and hands back activities; the
browser remains the only thing that knows what a level is, so the sandbox runs
identical game code with no worker deployed at all.

## Deploying it

You need a free Cloudflare account and a Strava API application
(https://www.strava.com/settings/api).

    cd worker
    npx wrangler login
    npx wrangler secret put STRAVA_CLIENT_SECRET   # from your Strava app
    npx wrangler secret put SESSION_SECRET         # any long random string
    npx wrangler deploy

Put your Strava **Client ID** in `wrangler.toml` (it is public; the secret is
not, and must never be committed or pasted into a chat). Deploy prints a URL
like `https://runmon-strava.<you>.workers.dev` — then:

1. Set that host as the **Authorization Callback Domain** on your Strava app
   (domain only: `runmon-strava.<you>.workers.dev`, no scheme, no path).
2. Put the full URL in `RUNMON_API` in `index.html`.

## What it stores

Per athlete, in one Durable Object keyed by Strava athlete id: the rotating
refresh token, the game save, and the ids of activities already imported.
`POST /disconnect` deauthorises with Strava and deletes all of it.

## Why a Durable Object rather than KV

A Durable Object runs one request at a time for a given athlete. That makes the
two things that would otherwise race atomic for free: Strava's refresh token
rotation (it invalidates the old token the moment it issues a new one, so two
concurrent refreshes lock the athlete out), and the read-modify-write of the
save. No locking code, no eventual-consistency window.

## Endpoints

| | |
| --- | --- |
| `GET /connect` | send the athlete to Strava, with signed state |
| `GET /callback` | trade the code, mint a session, bounce back to the app |
| `POST /sync` | activities since last time, plus the stored save |
| `PUT /save` | store the save and the ids the client actually imported |
| `POST /disconnect` | deauthorise at Strava, then forget the athlete |

Sessions are signed, not stored: athlete id plus expiry with an HMAC over both.
There is no session table to leak, and rotating `SESSION_SECRET` signs everyone
out.
