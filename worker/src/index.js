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

        // the session rides back in the fragment, which browsers do not send to
        // servers and do not put in referrers
        return Response.redirect(appURL(env) + "#strava=" + await mintSession(env, athleteId), 302);
      }

      if (path === "/sync" && request.method === "POST")
        return withAthlete(request, env, stub => stub.fetch("https://do/sync", { method:"POST" }));

      if (path === "/save" && request.method === "PUT")
        return withAthlete(request, env, async stub =>
          stub.fetch("https://do/save", { method:"POST", body: await request.text() }));

      if (path === "/disconnect" && request.method === "POST")
        return withAthlete(request, env, stub => stub.fetch("https://do/wipe", { method:"POST" }));

      return json(env, { error:"no such endpoint" }, 404);
    } catch (err){
      return json(env, { error: String(err && err.message || err) }, 500);
    }
  }
};

/* --- one athlete --------------------------------------------------------- */
export class Athlete {
  constructor(state, env){ this.state = state; this.env = env; }

  async fetch(request){
    const path = new URL(request.url).pathname;
    if (path === "/open")  return this.open(await request.json());
    if (path === "/sync")  return this.sync();
    if (path === "/save")  return this.commit(await request.json());
    if (path === "/wipe")  return this.wipe();
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
    return this.ok({ save, activities,
                     seen: { since: raw.length, fresh: fresh.length, kinds } });
  }

  /** The client says what it stored and what it managed to import, together, so
      an activity cannot be marked imported by a save that never landed. */
  async commit({ save, imported }){
    const s = this.state.storage;
    const seen = new Set(await s.get("imported") || []);
    for (const id of imported || []) seen.add(String(id));
    await s.put({ save, imported: [...seen] });
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
