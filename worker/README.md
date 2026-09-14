# Runmon's Strava broker

Runmon is a static file. Strava's OAuth needs a client secret. A static file
cannot keep one — that is the whole reason this directory exists.

It is not a game server. It stores the save and hands back activities; the
browser remains the only thing that knows what a level is, so the sandbox runs
identical game code with no worker deployed at all.

## Deploying it from a browser — no terminal, works on a phone

`wrangler` is a Node command-line tool and there is no Node on iOS, so
[`.github/workflows/deploy-worker.yml`](../.github/workflows/deploy-worker.yml)
runs it for you. Everything below happens in a browser.

**1. Make a Strava API application** at strava.com/settings/api. Note the
**Client ID** and **Client Secret**. Leave the callback domain for step 5.

**2. Set up Cloudflare** (free account — Durable Objects are on the free plan,
and only the SQLite-backed kind this worker uses).

Cloudflare rearranges its dashboard navigation, and a new account tends to land
on an "add a site" onboarding screen that hides the product list, so menu
directions here would only rot. Two steps that don't depend on any label:

- **Your Account ID** — log in at [dash.cloudflare.com](https://dash.cloudflare.com)
  and read it out of the address bar. Once you are inside an account the URL is
  `dash.cloudflare.com/<32 hex characters>/…`, and that hex string *is* the
  Account ID. Keep it; every other page is reachable by pasting it into a URL.
- **An API token** —
  [dash.cloudflare.com/profile/api-tokens](https://dash.cloudflare.com/profile/api-tokens)
  → Create Token → the *Edit Cloudflare Workers* template. Don't assemble the
  permissions by hand. Its zone section is fine left on *All zones* even with no
  domain on the account.

Then set the GitHub secrets below and run the workflow. It checks Cloudflare
before deploying anything, and if the account still needs a **workers.dev
subdomain** — the one thing that must be clicked by hand, because a first deploy
stops to ask for it and a CI runner has nobody to ask — the run summary hands
you the exact page, with your account id already in the link:

    https://dash.cloudflare.com/<your account id>/workers-and-pages

Whatever name you pick there becomes the worker's address,
`runmon-strava.<name>.workers.dev`. Then re-run the workflow.

Nothing else: no project to create, no payment method, no domain. `wrangler`
creates the worker and its Durable Object on the first deploy.

**3. Put four secrets in GitHub**, at Settings → Secrets and variables →
Actions → New repository secret:

| Name | Value |
| --- | --- |
| `CLOUDFLARE_API_TOKEN` | from step 2 |
| `CLOUDFLARE_ACCOUNT_ID` | from step 2 |
| `STRAVA_CLIENT_SECRET` | from step 1 |
| `SESSION_SECRET` | any long random string you invent |

The Strava secret goes **here and nowhere else** — never in a file, never in a
chat. GitHub encrypts these and does not show them again.

**4. Put your Client ID in `wrangler.toml`** (line 24). It is public and fine to
commit. Committing it triggers the deploy; the Actions tab then shows the
worker's URL in the run summary.

If you already committed it, or a run failed because a secret was not set yet,
there is nothing to re-commit: Actions → *Deploy the Strava broker* → **Run
workflow** starts it again. A run that stops for a missing secret says which
one in its summary, and deploys nothing.

**5. Back to Strava**, set the **Authorization Callback Domain** to that URL's
host only — `runmon-strava.<you>.workers.dev`, no scheme, no path.

**6. Put the full URL in `RUNMON_API`** at the top of `index.html`, with
`https://` and no trailing slash.

## Or from a terminal, if you have one

    cd worker
    npx wrangler login
    npx wrangler secret put STRAVA_CLIENT_SECRET
    npx wrangler secret put SESSION_SECRET
    npx wrangler deploy

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
