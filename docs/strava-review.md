# Getting Runmon past 10 athletes: Strava's review

Runmon is at Strava's self-serve ceiling of 10 connected athletes. Going past it
needs Strava's **Developer Program review**. This is the plan for passing it,
written against the live branch (`claude/runpet-tracker-app-x6ospu`), which is
the code a reviewer will actually open.

- **Form:** https://share.hsforms.com/1VXSwPUYqSH6IxK0y51FjHwcnkd8
  (linked from developers.strava.com/docs/getting-started)
- **Rules it is judged on:** the API Agreement and the API Policy (both effective
  1 June 2026), and the Brand Guidelines (revised 29 September 2025). The
  README's "Strava's rules, and what they change" section maps each rule to the
  code that follows it.
- **What Strava says it looks for:** apps that "complement the Strava
  experience", meet its quality bar, respect athlete privacy, follow the brand
  guidelines and stay within rate limits. Apps that send athlete data to AI
  tools are not approved. Increased access "is not a guarantee", and Strava only
  raises capacity for apps that are close to their limit.

---

## 1. Where the app stands

The code is already in good shape for review. What a reviewer checks, and where
Runmon answers it:

| Requirement | Status | Where |
| --- | --- | --- |
| Least access | ✅ `activity:read` only, so "Only You" activities are never read | `worker/src/index.js` `/connect` |
| Official Connect with Strava button | ✅ Unmodified orange SVG, in onboarding and Settings | `art/strava/btn_strava_connect_with_orange.svg` |
| Powered by Strava | ✅ Unmodified logo | `art/strava/api_logo_pwrdBy_strava_horiz_white.svg` |
| "View on Strava" on Strava data | ✅ On every run, bold Strava orange | `index.html`, run detail |
| Device attribution (Garmin rule) | ✅ The recording device is named | run detail |
| A user's data shown only to that user (2.3) | ✅ Card v2 holds no distance, run count, run time or date. `rosterCard()` enforces this on the server | `publicCard()`, `rosterCard()`, `playerCard()` |
| Retention (6.2) | ✅ Run details are folded away after seven days, on the phone and on the broker | `foldOldRuns`, nightly fold |
| Deauthorisation and deletions (6.3) | ✅ Webhook: a revoke counts as a disconnect, and a deleted or hidden run is removed within 48h | `/strava/webhook` |
| Disconnect and erase (2.5, 7.4) | ✅ Token revoked, runs deleted at once, everything else erased after 28 days (Strava's limit is 30) | `/disconnect`, `GRACE_DAYS` |
| Consent before reading (2.1, 7.3) | ✅ The Connect step, plus a one-time sheet for players who connected earlier | onboarding |
| Access and portability (2.2) | ✅ Settings → Download my data | Settings |
| Privacy policy and terms | ✅ Published, effective 30 Sep 2026 | `privacy.html` |
| No AI (5.3) | ✅ Nothing from Strava, or derived from it, goes into any AI | README, CLAUDE.md |
| Rate limits | ✅ At most one sync a minute while the app is open: one list call, plus a 5-item probe only when the window is empty | `stravaSync()` |
| Not replicating Strava | ✅ A game played on top of runs that are still recorded in Strava | n/a |

---

## 2. Before you submit (in your accounts, not in the code)

1. **Strava subscription.** Since June 2026 every API tier requires one on the
   account that owns the app. There is no extra fee.
2. **API settings page** (strava.com/settings/api):
   - The application name is **Runmon**. It must not contain "Strava".
   - The icon is Runmon's own art. No Strava logo, and no part of one.
   - Website: `https://ryancgq.github.io/runmon/`. Callback domain:
     `runmon-strava.runmon-gq.workers.dev`.
   - The description is plain and factual, for example "A running game where
     your runs raise a virtual pet."
   - Capacity already shows **10 / 10**. Strava asks you to apply only at that
     point.
3. **Webhook subscription is live.** Open the admin dashboard and check that
   the webhook status (`/admin/webhook`) shows an active subscription. The
   deletion rule depends on it, and a reviewer may test it.
4. **`privacy.html` loads** at `https://ryancgq.github.io/runmon/privacy.html`,
   and Settings links to it.
5. **Decide the three judgement calls** in section 3.

---

## 3. Judgement calls a reviewer could question

None of these breaks a rule as written. Each one, though, is a number shown to
other players that comes from Strava activities. Either change it before
submitting, or explain it in the form. Explaining up front is better than the
reviewer finding it.

1. **Streak and best streak on cards.** A streak is the number of consecutive
   days with a run, so "streak 12" tells other players the person ran on each
   of the last 12 days. That is activity dates, one step removed.
   *Safest:* show other players the streak only as a mood or flame (on or off),
   or drop it from other players' view. That is a change in `rosterCard()` and
   the card UI.
2. **Explore leaderboard damage.** Swings come from runs (one per 5 km run), so
   a high damage total hints at a lot of long runs. The cap per attempt follows
   level, not distance, and swings are never shown as kilometres.
   *Recommendation:* keep it, and describe it in the form as game currency.
3. **Admin dashboard shows XP.** XP is the run log summed. Only you see it, it
   is disclosed in the privacy policy, and it shows no runs or distances.
   *Recommendation:* keep it.

---

## 4. Form answers (draft)

| Field | Answer |
| --- | --- |
| App name | Runmon |
| Client ID | 279235 |
| Website | https://ryancgq.github.io/runmon/ |
| Privacy policy and terms | https://ryancgq.github.io/runmon/privacy.html |
| Source code | https://github.com/ryancgq/runmon |
| Contact | the address in `privacy.html` |
| Athletes connected / requested | 10 / *(your target, for example 100)* |

Ask for a number you can justify from real demand. Strava has granted less than
asked for before, and a second review is possible later.

**What does your app do?**
> Runmon is a free mobile web game where real runs raise a virtual pet. Players
> keep recording runs in Strava as normal. Runmon reads the runs recorded after
> they connect, turns them into XP, and their pet hatches, levels up and evolves
> through five forms. Rankings, friend codes and a shared world boss let small
> groups of friends play together, using only the pets' game stats. There are
> no ads, no payments and no data sales. Runmon complements Strava: you still
> record every run there.

**How do you use the Strava API?**
> OAuth with `activity:read` only, so "Only You" activities are never read. A
> Cloudflare Worker holds the client secret and tokens, which never reach the
> phone. When the app is opened (at most once a minute) it calls
> `GET /athlete/activities` with `after=` set to the time the player connected.
> For each Run or TrailRun (and VirtualRun, if the player opts in) it keeps the
> start time, distance, moving time, elevation, type, manual flag, device name
> and id. A webhook subscription handles deauthorisation and activity
> deletions and privacy changes, within 48 hours.

**Where is Strava data shown, and to whom?**
> Only to the athlete it belongs to: their run list, each run's detail (with
> "View on Strava" and the recording device), and their pet's growth. Other
> players see a pet card with the pet's name, species, form, level, streak and
> badge count, all game state. They never see distance, run count, times, dates
> or any Strava profile data. The server enforces this by building cards from a
> fixed allow-list, so a card from an older app is cut down too. The admin
> dashboard shows no runs or distances.
>
> *(Adjust the streak wording to match what you decide in section 3.)*

**How long is data kept, and how is it deleted?**
> A run's details are kept seven days, then deleted and folded into the pet's
> XP (Policy 6.2). A run deleted on Strava, or made private there, is removed
> within 48 hours of the webhook. Disconnecting revokes the token and deletes
> runs at once; the pet is kept 28 days in case the player returns, then erased
> from storage and backups. Players can download their data from Settings.

**Data sharing and AI.**
> No third parties beyond hosting (Cloudflare, GitHub Pages). Nothing from
> Strava, or derived from it, goes into any AI system or is used for analytics
> or training.

**Expected API usage.**
> About 1 to 2 requests per player per app open, at most one sync a minute.
> 100 players opening the app a few times a day is under 1,000 requests a day,
> well inside the default 200 per 15 minutes and 2,000 per day.

---

## 5. Screenshots to attach

Strava asks for **every place Strava data is shown, plus the Connect button**.
Take them on a real phone, with a real connected account:

1. Onboarding: the consent text and the **Connect with Strava** button.
2. Strava's own authorisation screen, showing that only the read permission
   (`activity:read`) is asked for.
3. The pet screen after a sync.
4. The run list, then a run's detail with **View on Strava** and the device name.
5. Settings → Strava, connected: Powered by Strava, Disconnect, Download my
   data, and the privacy link.
6. Rankings and a friend's card, to show that no distance or dates appear.
7. Explore, with the leaderboard.
8. The Disconnect confirmation.

`STRAVA_FULL` is `true` on the live app, so a **new** player currently sees
Strava greyed out in onboarding. For screenshot 1, use a returning account
(`stravaReturning()` still offers Connect) or a local copy with the flag off.
Do not push that change. Say in the form that new sign-ups are paused at the
cap.

---

## 6. After you submit

- Reviews have taken from one to several weeks. If nothing arrives after about
  two weeks, follow up at developers@strava.com. Other developers report that
  posting in the Developer Community Hub gets answers faster, but that is
  their experience, not official guidance.
- If Strava sends feedback, fix exactly what it names and resubmit.
- **When it is approved:** confirm the new capacity on the API settings page,
  set `STRAVA_FULL = false` in `index.html`, and update the note about it in
  CLAUDE.md. That push ships straight to players.
- Showing distance to other players stays off. The policy's consent wording
  (2.3 against 5.13) is unresolved, and there is no Strava ruling. If it is ever
  wanted, ask Strava in writing first.
