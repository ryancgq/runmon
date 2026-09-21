/* ---------------------------------------------------------------------------
   Runmon's Strava broker.

   Runmon is a static file; Strava's OAuth needs a client secret; a static file
   cannot keep one. That is the whole reason this exists. It is deliberately not
   a game server: it stores the save and hands back activities, and the browser
   goes on being the only thing that knows what a level is. Same game code runs
   in the sandbox with no worker deployed at all.

   Endpoints, all of them small:
     GET  /connect      send the athlete to Strava
     GET  /callback     trade the code, mint a session, bounce back to the app
     POST /sync         new activities since last time, plus the stored save
     PUT  /save         store the save and the ids the client actually imported
     POST /disconnect   tell Strava to forget us, then forget the athlete
--------------------------------------------------------------------------- */

const STRAVA = env => env.STRAVA_BASE || "https://www.strava.com";
const API    = env => env.STRAVA_API  || "https://www.strava.com/api/v3";

/* Runs and trail runs feed the pet. Treadmill runs are opt-in because they are
   self-reported distance; rides and walks are out because the pace and calorie
   models would read them as impossibly fast or impossibly slow runs. */
const ALWAYS = ["Run", "TrailRun"];
const OPT_IN = ["VirtualRun"];

/* --- session tokens ------------------------------------------------------ */
/* Signed, not stored: the athlete id and an expiry with an HMAC over both. The
   worker can verify one without a lookup, and there is no session table to
   leak. Rotating SESSION_SECRET logs everybody out, which is the point. */
const b64url = buf => btoa(String.fromCharCode(...new Uint8Array(buf)))
  .replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");

async function hmac(secret, msg){
  const key = await crypto.subtle.importKey("raw", new TextEncoder().encode(secret),
    { name:"HMAC", hash:"SHA-256" }, false, ["sign"]);
  return b64url(await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(msg)));
}
async function mintSession(env, athleteId){
  const exp = Date.now() + 400 * 24 * 3600 * 1000;      // long: it is a pet, not a bank
  const body = `${athleteId}.${exp}`;
  return `${body}.${await hmac(env.SESSION_SECRET, body)}`;
}
async function readSession(env, token){
  if (!token) return null;
  const i = token.lastIndexOf(".");
  if (i < 0) return null;
  const body = token.slice(0, i), sig = token.slice(i + 1);
  if (await hmac(env.SESSION_SECRET, body) !== sig) return null;
  const [athleteId, exp] = body.split(".");
  if (!athleteId || Number(exp) < Date.now()) return null;
  return athleteId;
}

/* --- plumbing ------------------------------------------------------------ */
const cors = env => ({
  "Access-Control-Allow-Origin": env.APP_ORIGIN || "*",
  "Access-Control-Allow-Headers": "Authorization, Content-Type",
  "Access-Control-Allow-Methods": "GET, POST, PUT, OPTIONS",
  "Access-Control-Max-Age": "86400"
});
const json = (env, obj, status = 200) =>
  new Response(JSON.stringify(obj), { status, headers: { "Content-Type":"application/json", ...cors(env) } });

const appURL = env => (env.APP_ORIGIN || "") + (env.APP_PATH || "/");

async function athleteStub(env, id){
  return env.ATHLETE.get(env.ATHLETE.idFromName(String(id)));
}

/* No I, O, 0 or 1: a code gets read off one screen and typed into another, and
   those are the four that get it wrong. */
const CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";
const normaliseCode = raw => {
  // Spaces, dashes and case are the athlete's business, not ours. Anything
  // outside the alphabet is simply not a code: no lookalike remapping, because
  // the four characters people confuse are the four this alphabet leaves out.
  const up = String(raw || "").toUpperCase().replace(/[^A-Z0-9]/g, "");
  return up.length === 6 && [...up].every(c => CODE_ALPHABET.includes(c)) ? up : null;
};
/* The directory lives in the same namespace, under names that cannot collide
   with an athlete id because of the prefix. A second Durable Object class would
   need a migration to deploy, and this needs none. */
const codeStub = (env, code) => env.ATHLETE.get(env.ATHLETE.idFromName("code:" + code));
async function claimCode(env, code, athleteId){
  await codeStub(env, code).fetch("https://do/dir-set", { method:"POST",
    body: JSON.stringify({ athleteId }) });
}
async function lookupCode(env, code){
  const r = await codeStub(env, code).fetch("https://do/dir-get");
  const { athleteId } = await r.json();
  return athleteId || null;
}
/* --- the private roster ---------------------------------------------------
   Durable Objects cannot be listed, so a summary of who is playing has to be
   indexed as it goes. One object holds a row per athlete under a `row:` prefix
   - storage *within* a single object is listable, which is the enumeration the
   namespace itself does not offer.

   The key is an HMAC of the athlete id rather than the id itself. It is stable,
   so a row updates instead of duplicating, and it cannot be turned back into a
   Strava profile by anyone who gets at the table. Each row carries the pet card
   the app already computes for Friends: a pet name, a form, a level, totals.
   Nothing from Strava beyond what the game has made its own. */
const rosterStub = env => env.ATHLETE.get(env.ATHLETE.idFromName("roster:all"));
async function rosterPut(env, athleteId, card){
  const handle = (await hmac(env.SESSION_SECRET, "roster:" + athleteId)).slice(0, 12);
  await rosterStub(env).fetch("https://do/roster-put", { method:"POST",
    body: JSON.stringify({ handle, card: card || null }) });
}
/* The admin token is compared as a digest, not as a string. An early-exit
   string compare hands the token over a character at a time to anybody willing
   to time the responses. */
async function adminOk(env, given){
  if (!env.ADMIN_TOKEN || !given) return false;
  const [a, b] = await Promise.all([
    hmac(env.SESSION_SECRET, "admin:" + given),
    hmac(env.SESSION_SECRET, "admin:" + env.ADMIN_TOKEN)
  ]);
  return a === b;
}

/** Every authenticated route is the same three lines, so they live here. */
async function withAthlete(request, env, fn){
  const id = await readSession(env, (request.headers.get("Authorization") || "").replace(/^Bearer /, ""));
  if (!id) return json(env, { error:"not linked" }, 401);
  return fn(await athleteStub(env, id), id);
}

export default {
  async fetch(request, env){
    const url = new URL(request.url);
    const path = url.pathname.replace(/\/+$/, "") || "/";
    if (request.method === "OPTIONS") return new Response(null, { headers: cors(env) });

    try {
      if (path === "/connect"){
        // `state` is signed so a stranger cannot walk an athlete through a
        // callback we did not start
        const nonce = crypto.randomUUID();
        const state = `${nonce}.${await hmac(env.SESSION_SECRET, nonce)}`;
        const auth = new URL(STRAVA(env) + "/oauth/authorize");
        auth.searchParams.set("client_id", env.STRAVA_CLIENT_ID);
        auth.searchParams.set("redirect_uri", url.origin + "/callback");
        auth.searchParams.set("response_type", "code");
        auth.searchParams.set("approval_prompt", "auto");
        // the narrow scope on purpose: activities the athlete already shows to
        // followers. Private runs stay private unless they widen it themselves.
        auth.searchParams.set("scope", "activity:read");
        auth.searchParams.set("state", state);
        return Response.redirect(auth.toString(), 302);
      }

      if (path === "/callback"){
        const code = url.searchParams.get("code");
        const state = url.searchParams.get("state") || "";
        const [nonce, sig] = state.split(".");
        if (!code || !nonce || await hmac(env.SESSION_SECRET, nonce) !== sig)
          return Response.redirect(appURL(env) + "#strava=denied", 302);

        const r = await fetch(STRAVA(env) + "/oauth/token", {
          method:"POST", headers:{ "Content-Type":"application/json" },
          body: JSON.stringify({
            client_id: env.STRAVA_CLIENT_ID, client_secret: env.STRAVA_CLIENT_SECRET,
            code, grant_type:"authorization_code" })
        });
        if (!r.ok) return Response.redirect(appURL(env) + "#strava=failed", 302);
        const tok = await r.json();
        const athleteId = tok.athlete && tok.athlete.id;
        if (!athleteId) return Response.redirect(appURL(env) + "#strava=failed", 302);

        const stub = await athleteStub(env, athleteId);
        await stub.fetch("https://do/open", { method:"POST", body: JSON.stringify({
          athleteId, refresh: tok.refresh_token, access: tok.access_token,
          expires: tok.expires_at * 1000,
          firstName: (tok.athlete && tok.athlete.firstname) || "" }) });

        // On the roster the moment they link, so somebody who connects and never
        // runs still shows up as a connection rather than as nothing at all.
        // Guarded, and deliberately: the roster is bookkeeping, and a failed
        // write must never be the reason somebody cannot link their Strava.
        // Unguarded it would fall to the catch below and answer a 500 where the
        // athlete is owed a redirect carrying their session.
        try { await rosterPut(env, athleteId, null); } catch (e){ /* not worth a failed link */ }

        // the session rides back in the fragment, which browsers do not send to
        // servers and do not put in referrers
        return Response.redirect(appURL(env) + "#strava=" + await mintSession(env, athleteId), 302);
      }

      if (path === "/sync" && request.method === "POST")
        return await withAthlete(request, env, stub => stub.fetch("https://do/sync", { method:"POST" }));

      if (path === "/save" && request.method === "PUT")
        return await withAthlete(request, env, async (stub, id) => {
          const body = await request.text();
          const res = await stub.fetch("https://do/save", { method:"POST", body });
          // the roster row is a copy of the card, refreshed as the save lands
          try {
            const parsed = JSON.parse(body);
            if (parsed && parsed.card) await rosterPut(env, id, parsed.card);
          } catch (e){ /* a save that will not parse is the DO's problem, not the roster's */ }
          return res;
        });

      if (path === "/disconnect" && request.method === "POST")
        return await withAthlete(request, env, stub => stub.fetch("https://do/wipe", { method:"POST" }));

      /* --- friends ---------------------------------------------------------
         A friend code is a random six characters, not anything derived from the
         athlete id: the id is on the end of every Strava profile URL, and a code
         that can be turned back into one would hand out more than its holder
         meant to share. The code is claimed in a directory object named after
         the code itself, which is how a stranger's code finds their pet without
         anybody being able to enumerate the other direction. */
      if (path === "/friends/me")
        return await withAthlete(request, env, async (stub, id) => {
          const r = await stub.fetch("https://do/code", { method:"POST",
            body: JSON.stringify({ athleteId: id }) });
          const { code, card } = await r.json();
          if (code) await claimCode(env, code, id);
          return json(env, { code, card });
        });

      /* Everybody who has linked and hatched something, which while the game
         is this small is what the Friends tab shows instead of a list you have
         to build by hand. It reads the same roster the admin summary does -
         the rows are written on every save - and hands back the same card a
         friend code would have got you: a pet, a form and totals, never runs
         or routes or anything about the athlete.

         It needs a session, so this is players seeing players rather than a
         URL anybody can curl. The handle is the roster's own HMAC, not an
         athlete id, so it identifies a row without being reversible into a
         Strava profile. */
      if (path === "/friends/all")
        return await withAthlete(request, env, async (_stub, me) => {
          const mine = (await hmac(env.SESSION_SECRET, "roster:" + me)).slice(0, 12);
          const r = await rosterStub(env).fetch("https://do/roster-list");
          const { rows } = await r.json();
          const players = (rows || [])
            .filter(x => x.handle !== mine && x.pet)
            .map(x => ({ id: x.handle, card: rosterCard(x), lastSeen: x.lastSeen || 0 }))
            .sort((a, b) => (b.card.level - a.card.level) || (b.card.km - a.card.km))
            .slice(0, 200);
          return json(env, { players });
        });

      if (path === "/friends/lookup")
        return await withAthlete(request, env, async (stub, me) => {
          // 200 with an `error` for anything about the code itself. An HTTP
          // status is about the request reaching us, and the app leans on that
          // distinction: a real 404 means this broker predates Friends.
          const code = normaliseCode(url.searchParams.get("code") || "");
          if (!code) return json(env, { error:"That is not a valid code." });
          const owner = await lookupCode(env, code);
          if (!owner) return json(env, { error:"No pet has that code." });
          if (String(owner) === String(me)) return json(env, { error:"That is your own code." });
          const theirs = await athleteStub(env, owner);
          const r = await theirs.fetch("https://do/card");
          const { card } = await r.json();
          if (!card) return json(env, { error:"They have not hatched a pet yet." });
          return json(env, { code, card });
        });

      // One round trip for a whole friends list. Codes only - a card carries a
      // pet and totals, never runs, routes or anything about the athlete.
      if (path === "/friends/cards" && request.method === "POST")
        return await withAthlete(request, env, async () => {
          const body = await request.json().catch(() => ({}));
          const codes = [...new Set((body.codes || []).map(normaliseCode).filter(Boolean))].slice(0, 60);
          const cards = {};
          await Promise.all(codes.map(async code => {
            const owner = await lookupCode(env, code);
            if (!owner) return;
            const r = await (await athleteStub(env, owner)).fetch("https://do/card");
            const { card } = await r.json();
            if (card) cards[code] = card;
          }));
          return json(env, { cards });
        });

      /* --- the private summary -------------------------------------------
         Not public facing. Wrong token or no token gets the same 404 as a
         route that does not exist, so the endpoint does not advertise itself
         to anybody scanning, and the token travels in a header rather than a
         query string, which would end up in logs and browser history.

         Plain text by default because it is read in a terminal; ?format=json
         for anything that wants to parse it. */
      if (path === "/admin/summary"){
        const given = (request.headers.get("Authorization") || "").replace(/^Bearer /, "");
        if (!await adminOk(env, given)) return json(env, { error:"no such endpoint" }, 404);
        const r = await rosterStub(env).fetch("https://do/roster-list");
        const { rows } = await r.json();
        rows.sort((a, b) => (b.lastSeen || 0) - (a.lastSeen || 0));
        if (url.searchParams.get("format") === "json")
          return new Response(JSON.stringify({ count: rows.length, rows }, null, 2),
            { headers:{ "Content-Type":"application/json", "Cache-Control":"no-store" } });
        return new Response(summaryTable(rows),
          { headers:{ "Content-Type":"text/plain; charset=utf-8", "Cache-Control":"no-store" } });
      }

      return json(env, { error:"no such endpoint" }, 404);
    } catch (err){
      // every route above is `return await`, not `return`: a returned promise
      // rejects after the try block has already exited, so without the await
      // this catch never sees it and a malformed body escapes as a raw runtime
      // error instead of the 500 it is meant to become.
      return json(env, { error: String(err && err.message || err) }, 500);
    }
  }
};

/* What a roster row keeps of a card. Named rather than spread wholesale so
   that a field added to the card for the game does not silently land in the
   private table as well. */
function rosterCard(c){
  return {
    pet: String(c.pet || "").slice(0, 24),
    species: String(c.species || "").slice(0, 12),
    form: String(c.form || "").slice(0, 24),
    stage: Number(c.stage) || 0,
    level: Number(c.level) || 0,
    km: Number(c.km) || 0,
    weekKm: Number(c.weekKm) || 0,
    runs: Number(c.runs) || 0,
    streak: Number(c.streak) || 0,
    best: Number(c.best) || 0,
    lastRun: Number(c.lastRun) || null
  };
}
/* A plain-text table, because this is read over curl in a terminal. Columns are
   padded to their widest value rather than to a guess, so a long pet name does
   not push everything out of line. */
function summaryTable(rows){
  const DAY = 86400000, now = Date.now();
  const ago = t => !t ? "\u2014" : (d => d === 0 ? "today" : d === 1 ? "1 day" : d + " days")
    (Math.round((now - t) / DAY));
  const head = ["HANDLE","PET","SPECIES","FORM","LV","KM","WEEK","RUNS","STREAK","LAST RUN","LINKED"];
  const body = rows.map(r => [
    r.handle || "", r.pet || "\u2014", r.species || "\u2014", r.form || "not hatched",
    String(r.level || "\u2014"), (r.km || 0).toFixed(1), (r.weekKm || 0).toFixed(1),
    String(r.runs || 0), String(r.streak || 0), ago(r.lastRun), ago(r.firstSeen)
  ]);
  const w = head.map((h, i) => Math.max(h.length, ...body.map(b => b[i].length)));
  const line = cells => cells.map((c, i) => c.padEnd(w[i])).join("  ").trimEnd();

  const hatched = rows.filter(r => (r.stage || 0) > 0).length;
  const active7 = rows.filter(r => r.lastRun && now - r.lastRun < 7 * DAY).length;
  const km = rows.reduce((a, r) => a + (r.km || 0), 0);
  const runs = rows.reduce((a, r) => a + (r.runs || 0), 0);
  const out = [
    `Runmon \u00b7 ${new Date().toISOString().slice(0, 16).replace("T", " ")} UTC`,
    "",
    `Connected to Strava   ${rows.length}`,
    `Hatched               ${hatched}`,
    `Ran in the last week  ${active7}`,
    `Lifetime              ${km.toFixed(1)} km over ${runs} runs`,
    "",
    line(head),
    w.map(n => "-".repeat(n)).join("  "),
    ...body.map(line)
  ];
  // the blank lines above are structure, so only the conditional tail is dropped
  if (rows.length >= 1000) out.push("", "(1000-row page limit reached)");
  return out.join("\n") + "\n";
}

/* --- one athlete --------------------------------------------------------- */
export class Athlete {
  constructor(state, env){ this.state = state; this.env = env; }

  async fetch(request){
    const path = new URL(request.url).pathname;
    if (path === "/open")  return this.open(await request.json());
    if (path === "/sync")  return this.sync();
    if (path === "/save")  return this.commit(await request.json());
    if (path === "/wipe")  return this.wipe();
    if (path === "/code")  return this.code(await request.json());
    if (path === "/card")  return this.ok({ card: await this.state.storage.get("card") || null });
    // the same class standing in as a directory entry, keyed by a friend code
    if (path === "/dir-set"){
      const { athleteId } = await request.json();
      await this.state.storage.put("owner", String(athleteId));
      return this.ok({ ok: true });
    }
    if (path === "/dir-get")
      return this.ok({ athleteId: await this.state.storage.get("owner") || null });
    /* the same class standing in as the roster, one key per athlete. `firstSeen`
       is kept from whatever was there, so a row records when somebody linked
       rather than when they last saved. */
    if (path === "/roster-put"){
      const { handle, card } = await request.json();
      const key = "row:" + handle;
      const prev = await this.state.storage.get(key) || {};
      await this.state.storage.put(key, {
        handle,
        ...(card ? rosterCard(card) : {}),
        ...(prev.pet && !card ? rosterCard(prev) : {}),   // a re-link keeps the pet
        firstSeen: prev.firstSeen || Date.now(),
        lastSeen: Date.now()
      });
      return this.ok({ ok: true });
    }
    if (path === "/roster-list"){
      const map = await this.state.storage.list({ prefix: "row:", limit: 1000 });
      return this.ok({ rows: [...map.values()] });
    }
    return new Response("no", { status: 404 });
  }

  async open(tok){
    const s = this.state.storage;
    await s.put({
      athleteId: tok.athleteId, refresh: tok.refresh, access: tok.access, expires: tok.expires,
      // Runs before this moment are somebody's training history, not this pet's
      // food. The pet starts as an egg and grows from here.
      connectedAt: (await s.get("connectedAt")) || Date.now()
    });
    return this.ok({ linked: true });
  }

  /** A live access token, refreshed if it is close to expiring. */
  async accessToken(){
    const s = this.state.storage;
    const [access, expires, refresh] = await Promise.all(
      [s.get("access"), s.get("expires"), s.get("refresh")]);
    if (access && expires && expires - Date.now() > 120000) return access;
    if (!refresh) return null;

    const r = await fetch(STRAVA(this.env) + "/oauth/token", {
      method:"POST", headers:{ "Content-Type":"application/json" },
      body: JSON.stringify({
        client_id: this.env.STRAVA_CLIENT_ID, client_secret: this.env.STRAVA_CLIENT_SECRET,
        grant_type:"refresh_token", refresh_token: refresh })
    });
    if (!r.ok) return null;
    const tok = await r.json();
    // Strava invalidates the old refresh token the moment it issues a new one,
    // so this write has to happen before anything else can ask for a token. It
    // does, because a Durable Object runs one request at a time.
    await s.put({ access: tok.access_token, refresh: tok.refresh_token,
                  expires: tok.expires_at * 1000 });
    return tok.access_token;
  }

  async sync(){
    const s = this.state.storage;
    const save = await s.get("save") || null;
    const token = await this.accessToken();
    if (!token) return this.ok({ save, activities: [], error:"reauth" });

    const connectedAt = await s.get("connectedAt") || Date.now();
    const imported = new Set(await s.get("imported") || []);
    const virtual = !!(save && save.settings && save.settings.stravaVirtual);
    const want = new Set([...ALWAYS, ...(virtual ? OPT_IN : [])]);

    const url = new URL(API(this.env) + "/athlete/activities");
    url.searchParams.set("after", Math.floor(connectedAt / 1000));
    // Strava returns newest first, so a new run is always inside this window;
    // the cap only bites if someone logs more than this between two app opens.
    // 200 is the endpoint's maximum, and costs the same one request as 100.
    url.searchParams.set("per_page", "200");
    const r = await fetch(url, { headers:{ Authorization:`Bearer ${token}` } });
    if (!r.ok) return this.ok({ save, activities: [], error:`strava ${r.status}` });

    // Counts, not activities: enough for the athlete to see why a sync came back
    // empty - nothing recorded since connecting, nothing of a type that counts,
    // or everything already taken - without anyone having to read a log.
    const raw = await r.json();
    const fresh = raw.filter(a => !imported.has(String(a.id)));
    const kinds = {};
    for (const a of fresh) kinds[a.type] = (kinds[a.type] || 0) + 1;

    const activities = fresh
      .filter(a => want.has(a.type) && a.distance > 0)
      .map(a => ({
        id: String(a.id),
        t: Date.parse(a.start_date),
        km: a.distance / 1000,
        sec: a.moving_time,
        elev: a.total_elevation_gain || 0,
        type: a.type,
        manual: !!a.manual                 // typed in by hand on Strava, not recorded
      }))
      .sort((x, y) => x.t - y.t);

    await s.put("lastSync", Date.now());
    // connectedAt matters more than it looks: the window is on an activity's
    // START time, not when it was uploaded, so a run begun before the link was
    // made never appears however recently it landed on Strava.
    const seen = { since: raw.length, fresh: fresh.length, kinds, connectedAt };

    // An empty window has two very different causes that look identical from
    // the app: nothing has been run since connecting, or Strava is showing us
    // nothing at all because the athlete's activities are private - the
    // activity:read scope cannot see "Only You". One call without the window
    // separates them. Counts and a date only; nothing is read or imported.
    if (raw.length === 0){
      const probe = new URL(API(this.env) + "/athlete/activities");
      probe.searchParams.set("per_page", "5");
      const pr = await fetch(probe, { headers:{ Authorization:`Bearer ${token}` } });
      if (pr.ok){
        const recent = await pr.json();
        seen.anyAtAll = recent.length;
        if (recent.length) seen.latestStart = Date.parse(recent[0].start_date) || null;
      }
    }
    return this.ok({ save, activities, seen });
  }

  /** This athlete's friend code, minted once and kept. */
  async code(){
    const s = this.state.storage;
    let code = await s.get("friendCode");
    if (!code){
      const bytes = crypto.getRandomValues(new Uint8Array(6));
      code = [...bytes].map(b => CODE_ALPHABET[b % CODE_ALPHABET.length]).join("");
      await s.put("friendCode", code);
    }
    return this.ok({ code, card: await s.get("card") || null });
  }

  /** The client says what it stored and what it managed to import, together, so
      an activity cannot be marked imported by a save that never landed. Its
      public card rides along: the app knows the XP curve and the form names, and
      working them out again here would be the same rules written twice. */
  async commit({ save, imported, card }){
    const s = this.state.storage;
    const seen = new Set(await s.get("imported") || []);
    for (const id of imported || []) seen.add(String(id));
    const write = { save, imported: [...seen] };
    if (card) write.card = card;
    await s.put(write);
    return this.ok({ saved: true });
  }

  async wipe(){
    const token = await this.accessToken();
    if (token) await fetch(STRAVA(this.env) + "/oauth/deauthorize", {
      method:"POST", headers:{ Authorization:`Bearer ${token}` } }).catch(()=>{});
    await this.state.storage.deleteAll();
    return this.ok({ disconnected: true });
  }

  ok(obj){
    return new Response(JSON.stringify(obj),
      { headers:{ "Content-Type":"application/json", ...cors(this.env) } });
  }
}
