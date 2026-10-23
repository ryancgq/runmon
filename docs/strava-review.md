# Strava Developer Program review: Runmon

This is a working draft for the review that raises Runmon above Strava's
10-athlete limit. It has three parts: what to fix before submitting, the answers
for the form, and a privacy policy to host.

- Form: https://share.hsforms.com/1VXSwPUYqSH6IxK0y51FjHwcnkd8 (linked from
  developers.strava.com/docs/getting-started)
- Prerequisites: an active **Strava subscription** on the account that owns the
  app (required for every API tier since June 2026). The app must also already be
  at the self-serve capacity of 10, which you raise from the API settings page.
- Rules checked against: API Agreement (updated 1 June 2026), Brand Guidelines
  (revised 29 September 2025), and the Strava API FAQ.

---

## Part 1: Fix before submitting

### Blocker 1: Friends shows one athlete's Strava data to other people

The API Agreement says: *"Strava Data provided by a specific user can only be
displayed or disclosed in your Developer Application to that user"*, and
*"not sharing a Strava user's data with other users … without explicit
consent."* A friend card (`publicCard()` in `index.html`, served by
`/friends/lookup` and `/friends/cards` in the worker) contains:

| Field | Comes from Strava activity data? |
| --- | --- |
| `pet`, `species`, `form`, `stage` | No. These are game state. |
| `level` | Indirectly. It comes from XP, which comes from distance. |
| `km`, `weekKm`, `runs` | **Yes.** These are distance and activity counts. |
| `lastRun` | **Yes.** This is an activity start time. |
| `streak`, `best` | **Yes.** These are derived from activity dates. |

The reviewer is told to look at every screen that shows Strava data, so the
Friends tab will be seen. Do both of these:

1. **Cut the card down to game state** for any pet fed by Strava: pet name,
   species, form, stage and level. Drop `km`, `weekKm`, `runs`, `lastRun`,
   `streak` and `best`. A level is the game's own number, and it is the easiest
   field to defend.
2. **Add explicit opt-in consent.** Friends should stay off until the athlete
   switches it on, with text such as: *"Show your pet's name, form and level to
   people who have your friend code. No runs, distances or dates are shared."*

The worker's `rosterCard()` drops the removed fields too, so the admin summary
stops holding per-athlete km and run counts.

### Blocker 2: Brand guidelines

- **Connect button.** "Connect Strava" is currently a styled `btn primary`, used
  in onboarding (`#ob-strava-go`) and in Settings (`#strava-on`). Swap it for the
  official **"Connect with Strava"** asset: orange or white, 48px tall
  (96px @2x), and unmodified. Download it from developers.strava.com/guidelines.
  The button already lands on `strava.com/oauth/authorize` through the worker's
  `/connect` redirect.
- **"Powered by Strava" logo.** Put it where Strava data appears: the Strava
  panel in Settings, and the History list once it holds Strava runs. Keep it
  smaller than Runmon's own branding and separate from it.
- **"View on Strava" link.** Every imported run already keeps its activity id
  (`run.strava`). In `runItemHTML()`, add a link with that exact text to
  `https://www.strava.com/activities/<id>`, shown as a link: bold, underlined,
  or in `#FC5200`.
- **Naming.** The Strava app's name and description must not contain "Strava"
  ("Runmon" is fine). The worker hostname `runmon-strava.…workers.dev` is only a
  callback domain, but `runmon-api` would remove any doubt.

### Should fix: respect deauthorisation and deletions

- If someone revokes Runmon from **Strava's** settings instead of pressing
  Disconnect, the worker keeps their refresh token, save, card and roster row
  for good. Register a **webhook subscription** (`POST /push_subscriptions`) and
  add a `/webhook` route to the worker. On an `athlete` event with
  `updates.authorized = "false"`, run the same wipe as `/disconnect`. This also
  answers "respect privacy choices", and rate-limit reviewers count webhooks in
  an app's favour.
- The README describes keeping runs after they are deleted on Strava as
  deliberate. Under "comply with their privacy choices", that is hard to defend
  to a reviewer. The same webhook can carry `activity` `delete` events: mark the
  run as removed, or at least stop displaying it. Keeping the XP it earned is a
  separate choice. Whatever the policy is, state it plainly in the privacy
  policy.

### Needed for the form

- A **privacy policy URL**: draft in Part 3, to host as `privacy.html` on
  GitHub Pages.
- A **support contact**: an email address, or the GitHub issues page.
- **Screenshots** (see the list in Part 2).

### Already compliant

- Minimal scope: `activity:read` only, and private activities stay unread.
- Secrets stay server-side, and sessions are HMAC-signed with no token in the
  browser beyond the session.
- Disconnect deauthorises at Strava and deletes everything server-side.
- Polling is throttled to one sync per 60s per open app, one list call per sync
  (plus a 5-item probe only when the window is empty). That is far under
  200 requests per 15 min and 2,000 per day for hundreds of athletes.
- Strava data is not sent to any AI tool or third party. The FAQ says apps that
  do this will not be approved.
- Runmon does not replicate Strava. It is a game layered on runs that are still
  recorded in Strava.

---

## Part 2: Form answers (draft)

**App name:** Runmon

**Client ID:** 279235

**Website:** https://ryancgq.github.io/runmon/

**Source code:** https://github.com/ryancgq/runmon

**Privacy policy:** https://ryancgq.github.io/runmon/privacy.html

**Support contact:** *(your email)*

**Athletes currently connected / capacity requested:** *(current count, e.g. 10)* / *(target, e.g. 100)*.
Ask for a realistic number tied to real demand. Strava says it only raises
limits for apps nearing capacity, and has granted fewer than asked for before.

**What does your app do?**
> Runmon is a free mobile web game where your real runs raise a virtual pet.
> Athletes keep recording runs in Strava as normal. Runmon reads the runs
> recorded after they connect, turns distance into XP, and the pet hatches,
> levels up and evolves through five forms. A pet left alone too long visibly
> sulks, which gives people a playful reason to get out again. Runmon has no
> ads, no payments and no accounts beyond the Strava link.

**How does it use the Strava API?**
> OAuth with the `activity:read` scope only, so activities set to "Only You"
> are never read. A small Cloudflare Worker holds the client secret and the
> rotating refresh token. When the app is opened (at most once a minute), it
> calls `GET /athlete/activities` with `after=` set to the connection time.
> From each Run or TrailRun (and VirtualRun, if the athlete opts in), it keeps
> only the id, start time, distance, moving time, elevation gain, type and
> manual flag. Nothing else from the athlete's profile or activities is stored.

**Where is Strava data shown?**
> Only to the athlete it belongs to: their pet screen (level and XP from their
> runs), their run history (each imported run, with a "View on Strava" link),
> and the Strava section of Settings. Friends shows other players only the pet's
> name, form and level, which are game data. Friends is opt-in, and no
> distances, runs or dates are shared.

**How is data stored, protected and deleted?**
> One Cloudflare Durable Object per athlete, keyed by athlete id, holds the
> refresh token, the game save and the ids of imported activities. Sessions are
> HMAC-signed and expire. The client secret lives only in Cloudflare and GitHub
> secrets. "Disconnect" in Settings calls `/oauth/deauthorize` and deletes
> everything stored for the athlete. A deauthorisation webhook does the same
> when access is revoked from Strava's side.

**Expected API usage:**
> About 1–2 requests per athlete per app open, capped at one sync a minute.
> At 100 athletes that is well under 1,000 requests a day.

**Does the app share data with third parties or AI tools?** No.

**Screenshots to attach** (take them after the Part 1 changes):
1. Onboarding "Connect with Strava" step, showing the official button.
2. Strava's consent screen, reached from that button.
3. Settings → Strava, connected, with "Powered by Strava" and Disconnect visible.
4. History, with imported runs and their "View on Strava" links.
5. The pet screen after a sync (XP from Strava runs).
6. Friends: your own card, a friend's card showing only pet, form and level, and
   the opt-in switch.
7. The Disconnect confirmation.

---

## Part 3: Privacy policy (draft for `privacy.html`)

> **Runmon privacy policy**: last updated *(date)*
>
> Runmon is a game run by *(your name)*. Contact: *(email)*.
>
> **Without Strava.** Your pet, runs and settings stay on your device in
> browser storage. Runs you record with Runmon's own tracker, including GPS
> routes, never leave your device.
>
> **With Strava.** When you connect, Strava gives Runmon read access to the
> activities you show to followers or everyone (the `activity:read` scope).
> Runmon stores, on Cloudflare's servers:
> - your Strava athlete id, an access token and a refresh token;
> - for each run recorded after you connected: its Strava id, start time,
>   distance, moving time, elevation gain, activity type and whether it was
>   entered manually;
> - your game save (pet, levels, settings, run log) so it follows you across
>   devices;
> - a pet card (pet name, form, level) used for Friends and for an aggregate
>   usage summary visible only to the developer.
>
> Runmon does not read private activities, routes, heart rate, photos or your
> profile. It does not sell data, show ads, or send your data to any third
> party or AI service.
>
> **Friends.** Only if you switch it on: people you give your friend code to
> can see your pet's name, form and level. Nothing about your runs is shared.
>
> **Deleting your data.** Settings → Strava → Disconnect revokes Runmon's access
> and immediately deletes everything stored about you on the server. Revoking
> Runmon from Strava's own settings does the same automatically. Clearing your
> browser data removes the on-device copy.
>
> Runmon uses data from Strava under the Strava API Agreement. Runmon is not
> developed or endorsed by Strava.
