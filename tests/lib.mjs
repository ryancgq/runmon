// Shared harness for the tests: the real broker (worker/src/index.js) with
// in-memory Durable Objects and a fake Strava, plus where the repo is and
// where screenshots go. See tests/README.md.
import { webcrypto } from "node:crypto";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

export const REPO = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
export const OUT = process.env.RUNMON_TEST_OUT || path.join(os.tmpdir(), "runmon-tests");
fs.mkdirSync(OUT, { recursive: true });

/* worker/src/index.js is an ES module with a .js name and no package.json to
   say so, so Node would read it as CommonJS. It is copied to a .mjs beside
   OUT and imported from there. */
export async function loadWorker(file = path.join(REPO, "worker/src/index.js")){
  const copy = path.join(OUT, `worker-${process.pid}-${Math.random().toString(36).slice(2)}.mjs`);
  fs.copyFileSync(file, copy);
  return import(pathToFileURL(copy).href);
}

export async function makeHarness(workerFile, envExtra = {}){
  const mod = await loadWorker(workerFile || undefined);
  const worker = mod.default, Athlete = mod.Athlete;
  const clone = v => v === undefined ? undefined : JSON.parse(JSON.stringify(v));
  class Storage {
    constructor(){ this.m = new Map(); }
    async get(k){ if (Array.isArray(k)) return new Map(k.map(x => [x, clone(this.m.get(x))])); return clone(this.m.get(k)); }
    async put(k, v){ if (typeof k === "object") for (const [a, b] of Object.entries(k)) this.m.set(a, clone(b)); else this.m.set(k, clone(v)); }
    async delete(k){ for (const x of [].concat(k)) this.m.delete(x); }
    async deleteAll(){ this.m.clear(); }
    async list({ prefix = "", limit } = {}){ return new Map([...this.m].filter(([k]) => k.startsWith(prefix)).map(([k, v]) => [k, clone(v)])); }
    async getAlarm(){ return null; } async setAlarm(){} async deleteAlarm(){}
  }
  const objects = new Map();
  const env = { SESSION_SECRET:"s3cret", STRAVA_CLIENT_ID:"1", STRAVA_CLIENT_SECRET:"x",
    APP_ORIGIN:"https://app", APP_PATH:"/runmon/",
    STRAVA_BASE:"https://strava.test", STRAVA_API:"https://strava.test/api", ...envExtra };
  const ns = name => ({
    idFromName: n => n,
    get: n => {
      const key = name + ":" + n;
      if (!objects.has(key)) objects.set(key, new Athlete({ storage: new Storage(), id: { toString: () => n } }, env));
      const o = objects.get(key);
      return { fetch: (u, init) => o.fetch(new Request(u, init)) };
    }
  });
  env.ATHLETE = ns("A");
  const strava = { acts: [], athlete: 777 };
  const realFetch = globalThis.fetch;
  globalThis.fetch = async (u, init) => {
    const url = new URL(u instanceof Request ? u.url : String(u));
    if (url.host !== "strava.test") return realFetch(u, init);
    if (url.pathname === "/oauth/token") return Response.json({ access_token:"A", refresh_token:"R", expires_at: Date.now()/1000 + 3600, athlete:{ id: strava.athlete } });
    if (url.pathname === "/api/athlete/activities") return Response.json(strava.acts);
    if (url.pathname === "/oauth/revoke" || url.pathname === "/oauth/deauthorize") return Response.json({});
    if (url.pathname === "/api/athlete") return Response.json({ id: strava.athlete });
    return new Response("not found", { status: 404 });
  };
  const W = "https://broker";
  const call = async (method, p, { token, body } = {}) => {
    const r = await worker.fetch(new Request(W + p, { method,
      headers: token ? { Authorization: "Bearer " + token } : {},
      body: body == null ? undefined : (typeof body === "string" ? body : JSON.stringify(body)) }), env, { waitUntil(){} });
    const text = await r.text();
    try { return { status: r.status, ...JSON.parse(text) }; } catch (e){ return { status: r.status, text, headers: r.headers }; }
  };
  const callback = async athlete => {
    strava.athlete = athlete;
    const k = await webcrypto.subtle.importKey("raw", new TextEncoder().encode(env.SESSION_SECRET), { name:"HMAC", hash:"SHA-256" }, false, ["sign"]);
    const sig = Buffer.from(await webcrypto.subtle.sign("HMAC", k, new TextEncoder().encode("n1"))).toString("base64url");
    const r = await worker.fetch(new Request(`${W}/callback?code=c&state=n1.${sig}`), env, { waitUntil(){} });
    return r.headers.get("Location");
  };
  const storageOf = n => { const o = objects.get("A:" + n); return o ? o.state.storage.m : null; };
  return { worker, env, call, callback, strava, storageOf, objects };
}
