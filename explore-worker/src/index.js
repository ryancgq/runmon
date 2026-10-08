/* Runmon Explore - the shared world.
 *
 * Two worlds, one Durable Object class (World), each its own instance:
 *
 *   /world  the game's. Only linked players get in: a page's first message
 *           is its game session, which this worker checks by asking the
 *           Strava broker who it belongs to (/explore/me). Sir Uwaaarghhhh's
 *           health and who took what off him are kept here, by the server:
 *           an attempt spends one of the player's swings at the broker
 *           (/explore/attempt), and what the page then reports it took off
 *           him is accepted only during that attempt and only up to what a
 *           pet of its level could do. His round follows the broker's raid
 *           epoch, which the admin switch moves; he stays down until it does.
 *           The first round carries over the old raid's health and shares
 *           (/explore/legacy), scaled so the share of him is the same.
 *   /demo   the sandbox: anyone, any pet, nothing checked, nothing linked to
 *           the game. Its own boss, back on his hill soon after he falls.
 *   /board  the game world's leaderboard, for the game's Explore tab.
 *
 * What the broker is asked is all this worker knows of a player: a roster
 * handle, a pet's name, species and level, and a swing count. Nothing about
 * runs, and nothing from Strava.
 *
 * Both worlds speak the shapes the page already uses - a room (presence) and
 * a small store (docs):
 *
 *   presence  each page's own state, sent only when it changes (and as a
 *             once-a-second heartbeat), relayed to everyone else. Memory only.
 *   docs      raids/state                {e, felledAt}  the round
 *             raids/e<round>/hits/<key>  {dm, n, f}     one player's damage
 *
 * Protocol (JSON text frames):
 *   server -> page  {t:"hello", id, peers:[{id, p}], me?}   once in
 *                   {t:"join", id} {t:"left", id} {t:"p", id, p}
 *                   {t:"doc", path, data} {t:"docs", prefix, docs:[{path, data}]}
 *                   {t:"ack", n} {t:"err", n, code}
 *                   {t:"attempt", n, ok, left, toNext, why}   (game world)
 *   page -> server  {t:"auth", token}  first, in the game world
 *                   {t:"p", p} {t:"sub", prefix} {t:"unsub", prefix}
 *                   {t:"set", n, path, data}
 *                   {t:"attempt", n} {t:"attempt-end"}        (game world)
 */

const MAX_PEERS = 64;          // one world; past this a page plays alone
const MAX_FRAME = 8192;        // bytes of JSON in one message
const MAX_PRESENCE = 4096;     // the same bound the page keeps inside Claude
const MAX_DOCS = 20000;
const RATE = 60;               // messages a second a page may send
const IDLE_MS = 120000;        // a page that has said nothing for this long (a frozen or locked phone) is let go
const AUTH_MS = 20000;         // a page in the game world that hasn't said who it is by now is let go
const ATTEMPT_MS = 3600e3;     // an attempt still open after an hour is over
const RAID_HP = 110000;        // his health; the page's RAID_HP must match
const STATE = "raids/state";
const HIT = /^raids\/e(\d{1,7})\/hits\/([A-Za-z0-9_-]{4,20})$/;
const PREFIX = /^raids(\/(state|e\d{1,7}(\/hits)?))?$/;
/* The most one attempt can take off him, by level: about three times the
   best a pet that only his roar ever touches managed in simulation. It stops
   an absurd report; a swing still costs five kilometres. */
const ATTEMPT_CAP = [[1, 900], [5, 1500], [15, 4500], [16, 6000], [26, 9000], [40, 16500], [99, 40000]];
/* Each species' forms, by the level it reaches them (the page's FORMS and the
   game's EVO_LEVELS). Below the first there is nothing in the world to be. */
const FORM_AT = { ember:[[5, "cinderling"], [16, "blazewyrm"]], nimbus:[[5, "sparky"], [16, "zephyrite"]],
                  verdant:[[5, "cub"], [16, "panda"]] };
function formOf(species, level){
  let f = null;
  for (const [lv, id] of FORM_AT[species] || []) if (level >= lv) f = id;
  return f;
}
function attemptCap(level){
  const lv = Math.max(1, Math.min(99, Number(level) || 1)), t = ATTEMPT_CAP;
  for (let i = 1; i < t.length; i++) if (lv <= t[i][0]){
    const [l0, c0] = t[i - 1], [l1, c1] = t[i];
    return Math.round(c0 + (c1 - c0) * (lv - l0) / (l1 - l0));
  }
  return t[t.length - 1][1];
}

const cors = env => ({ "access-control-allow-origin": allowedOrigins(env)[0] || "*",
  "access-control-allow-headers": "Authorization", "access-control-allow-methods": "GET, OPTIONS", "vary": "Origin" });
const allowedOrigins = env => String(env.ALLOWED_ORIGINS || "").split(",").map(s => s.trim()).filter(Boolean);

export default {
  async fetch(req, env){
    const url = new URL(req.url);
    if (url.pathname === "/health") return new Response("ok", { headers:{ "content-type":"text/plain", "access-control-allow-origin":"*" } });
    if (url.pathname === "/board" || url.pathname === "/demo-board"){
      const origin = req.headers.get("Origin") || "", ok = allowedOrigins(env);
      const h = { ...cors(env), "access-control-allow-origin": ok.includes(origin) ? origin : ok[0] || "*" };
      if (req.method === "OPTIONS") return new Response(null, { headers:h });
      const r = url.pathname === "/board"
        ? await world(env, "world").fetch(new Request("https://world/board", { headers:{ authorization: req.headers.get("Authorization") || "" } }))
        : await world(env, "demo").fetch(new Request("https://world/demo-board"));
      return new Response(r.body, { status:r.status, headers:{ ...h, "content-type":"application/json", "cache-control":"no-store" } });
    }
    const mode = url.pathname === "/world" ? "game" : url.pathname === "/demo" ? "demo" : null;
    if (!mode) return new Response("not found", { status:404 });
    if ((req.headers.get("Upgrade") || "").toLowerCase() !== "websocket") return new Response("this is a websocket", { status:426 });
    const origin = req.headers.get("Origin") || "", allowed = allowedOrigins(env);
    if (allowed.length && !allowed.includes(origin)) return new Response("not from here", { status:403 });
    if (env.JOIN_CODE && url.searchParams.get("code") !== env.JOIN_CODE) return new Response("wrong code", { status:403 });
    const fwd = new Request(req); fwd.headers.set("x-world", mode);
    return world(env, mode === "game" ? "world" : "demo").fetch(fwd);
  }
};
const world = (env, name) => env.WORLD.get(env.WORLD.idFromName(name));

export class World {
  constructor(ctx, env){
    this.ctx = ctx; this.env = env;
    this.pres = new Map();     // peer id -> presence; rebuilt from the pages' next sends after a sleep
    this.rate = new Map();     // peer id -> [window start, count]
    this.heard = new Map();    // peer id -> when it last said anything
    this.seenAt = new Map();   // session token -> { me, at }: who it was, lately
    this.swept = 0;
    const sql = ctx.storage.sql;
    sql.exec("CREATE TABLE IF NOT EXISTS docs (path TEXT PRIMARY KEY, data TEXT NOT NULL, at INTEGER NOT NULL)");
    sql.exec("CREATE TABLE IF NOT EXISTS attempts (handle TEXT PRIMARY KEY, e INTEGER NOT NULL, start INTEGER NOT NULL, cap INTEGER NOT NULL, at INTEGER NOT NULL)");
    sql.exec("CREATE TABLE IF NOT EXISTS meta (k TEXT PRIMARY KEY, v TEXT NOT NULL)");
  }
  get mode(){
    if (!this._mode){ const r = this.ctx.storage.sql.exec("SELECT v FROM meta WHERE k = 'mode'").toArray()[0]; this._mode = r ? r.v : "demo"; }
    return this._mode;
  }
  set mode(m){
    // the game world starts clean: whatever the prototype left in this object was a test, and the
    // round that counts is carried over from the game's raid (round())
    if (m === "game"){ this.ctx.storage.sql.exec("DELETE FROM docs"); this.ctx.storage.sql.exec("DELETE FROM attempts"); }
    this._mode = m; this.ctx.storage.sql.exec("INSERT OR REPLACE INTO meta (k, v) VALUES ('mode', ?)", m);
  }

  /* ---------- the broker, asked as the player ---------- */
  broker(path, token, init = {}){
    const headers = { Authorization: "Bearer " + token };
    if (this.env.BROKER) return this.env.BROKER.fetch("https://broker" + path, { ...init, headers });
    return fetch(String(this.env.BROKER_URL || "").replace(/\/+$/, "") + path, { ...init, headers });
  }
  async whoIs(token){
    if (typeof token !== "string" || token.length < 10 || token.length > 400) return null;
    const hit = this.seenAt.get(token);
    if (hit && Date.now() - hit.at < 600e3) return hit.me;
    try {
      const r = await this.broker("/explore/me", token);
      if (!r.ok) return null;
      const me = await r.json();
      if (!me || typeof me.handle !== "string" || !/^[A-Za-z0-9_-]{4,20}$/.test(me.handle)) return null;
      const out = { handle:me.handle, pet:String(me.pet || "").slice(0, 24), species:String(me.species || ""),
                    level:Math.max(1, Math.min(99, Number(me.level) || 1)), swings:me.swings || null, epoch:Number(me.epoch) || 1 };
      this.seenAt.set(token, { me:out, at:Date.now() });
      if (this.seenAt.size > 500) this.seenAt.delete(this.seenAt.keys().next().value);
      await this.round(out.epoch, token);
      return out;
    } catch(e){ return null; }
  }

  /* ---------- the round ----------
     It follows the broker's raid epoch. The very first one carries the old
     raid over: its health and everyone's share of it, scaled to his health
     here, so the same share of him is gone. */
  async round(epoch, token){
    if (this.mode !== "game") return;
    const cur = this.read(STATE);
    if (!cur){
      let st = { e:Math.max(1, epoch | 0), felledAt:0 };
      try {
        const r = await this.broker("/explore/legacy", token);
        if (r.ok){
          const old = await r.json(), max = Number(old.max) || 0;
          if (max > 0){
            st = { e:Math.max(1, old.epoch | 0), felledAt:old.felledAt ? Number(old.felledAt) : 0 };
            for (const x of Array.isArray(old.roll) ? old.roll : []){
              if (!x || !/^[A-Za-z0-9_-]{4,20}$/.test(String(x.handle))) continue;
              const dm = Math.round((Number(x.dealt) || 0) * RAID_HP / max);
              if (dm > 0) this.put(`raids/e${st.e}/hits/${x.handle}`, { dm, n:String(x.pet || "").slice(0, 24), sp:String(x.species || "").slice(0, 12), f:"", at:Date.now() });
            }
          }
        }
      } catch(e){}
      if (this.read(STATE)) return;   // another arrival got here first
      this.put(STATE, st); this.tell(STATE, st);
      return;
    }
    if ((epoch | 0) > cur.e){   // the switch was thrown: a new round, at full health
      const st = { e:epoch | 0, felledAt:0 };
      this.put(STATE, st); this.tell(STATE, st);
      this.ctx.storage.sql.exec("DELETE FROM attempts");
    }
  }
  dealt(e){
    let sum = 0;
    for (const r of this.ctx.storage.sql.exec("SELECT data FROM docs WHERE path LIKE ?", `raids/e${e}/hits/%`).toArray())
      sum += Number(JSON.parse(r.data).dm) || 0;
    return sum;
  }

  /* ---------- the sandbox's leaderboard, for the demo's Explore tab ----------
     Anyone may read it: it is test pets under made-up names. Rows carry the
     form each was played as, since the sandbox has no roster to look it up. */
  demoBoard(){
    if (this.mode !== "demo") return new Response(JSON.stringify({ error:"not the sandbox" }), { status:404 });
    const st = this.read(STATE) || { e:1, felledAt:0 };
    const rows = this.ctx.storage.sql.exec("SELECT path, data FROM docs WHERE path LIKE ?", `raids/e${Number(st.e) || 1}/hits/%`).toArray()
      .map(r => { const d = JSON.parse(r.data); return { pet:String(d.n || "").slice(0, 24), form:String(d.f || "").slice(0, 12), dm:Number(d.dm) || 0 }; })
      .filter(r => r.dm > 0).sort((a, b) => b.dm - a.dm);
    const dealt = rows.reduce((a, r) => a + r.dm, 0);
    return new Response(JSON.stringify({
      round:Number(st.e) || 1, max:RAID_HP, dealt:Math.min(RAID_HP, dealt), felledAt:st.felledAt || null,
      rows:rows.slice(0, 50).map((r, i) => ({ rank:i + 1, pet:r.pet, form:r.form, dm:r.dm }))
    }));
  }

  /* ---------- the leaderboard, for the game's Explore tab ---------- */
  async board(req){
    if (this.mode !== "game") this.mode = "game";   // only the game world has a board
    const token = (req.headers.get("authorization") || "").replace(/^Bearer /, "");
    const me = await this.whoIs(token);
    if (!me) return new Response(JSON.stringify({ error:"not linked" }), { status:401 });
    const st = this.read(STATE) || { e:me.epoch, felledAt:0 };
    const rows = this.ctx.storage.sql.exec("SELECT path, data FROM docs WHERE path LIKE ?", `raids/e${st.e}/hits/%`).toArray()
      .map(r => { const d = JSON.parse(r.data); return { key:r.path.split("/").pop(), pet:d.n || "", species:d.sp || "", dm:Number(d.dm) || 0 }; })
      .filter(r => r.dm > 0).sort((a, b) => b.dm - a.dm);
    const dealt = rows.reduce((a, r) => a + r.dm, 0), mine = rows.findIndex(r => r.key === me.handle);
    return new Response(JSON.stringify({
      round:st.e, max:RAID_HP, dealt:Math.min(RAID_HP, dealt), felledAt:st.felledAt || null,
      rows:rows.slice(0, 50).map((r, i) => ({ rank:i + 1, id:r.key, pet:r.pet, species:r.species, dm:r.dm, you:r.key === me.handle })),
      you:{ pet:me.pet, species:me.species, level:me.level, rank:mine >= 0 ? mine + 1 : null, dm:mine >= 0 ? rows[mine].dm : 0, swings:me.swings }
    }));
  }

  async fetch(req){
    if (new URL(req.url).pathname === "/board") return this.board(req);
    if (new URL(req.url).pathname === "/demo-board") return this.demoBoard();
    const mode = req.headers.get("x-world") === "game" ? "game" : "demo";
    if (this.mode !== mode) this.mode = mode;
    const live = this.ctx.getWebSockets();
    if (live.length >= MAX_PEERS) return new Response("the world is full", { status:503 });
    const [client, server] = Object.values(new WebSocketPair());
    const id = "p" + crypto.randomUUID().replace(/-/g, "").slice(0, 12);
    // hibernation: the object can sleep between messages without dropping anyone
    this.ctx.acceptWebSocket(server);
    server.serializeAttachment({ id, subs:[], since:Date.now(), me:null });
    if (mode === "demo") this.welcome(server, null);   // the game world waits to hear who it is
    return new Response(null, { status:101, webSocket:client });
  }
  welcome(ws, me){
    const m = this.meta(ws);
    ws.serializeAttachment({ ...m, me });
    ws.send(JSON.stringify({ t:"hello", id:m.id, peers:this.everyone(ws), me:me && { handle:me.handle, pet:me.pet, species:me.species, level:me.level, swings:me.swings } }));
    this.broadcast({ t:"join", id:m.id }, ws);
  }

  meta(ws){ return ws.deserializeAttachment() || { id:"?", subs:[], me:null }; }
  inside(ws){ const m = this.meta(ws); return this.mode !== "game" || !!m.me; }
  everyone(except){
    const out = [];
    for (const ws of this.ctx.getWebSockets()){ if (ws === except || !this.inside(ws)) continue; const id = this.meta(ws).id; out.push({ id, p:this.pres.get(id) || {} }); }
    return out;
  }
  broadcast(msg, except){
    const s = JSON.stringify(msg);
    for (const ws of this.ctx.getWebSockets()) if (ws !== except && this.inside(ws)){ try { ws.send(s); } catch(e){} }
  }
  limited(id){
    const now = Date.now(), r = this.rate.get(id) || [now, 0];
    if (now - r[0] > 1000){ r[0] = now; r[1] = 0; }
    r[1]++; this.rate.set(id, r);
    return r[1] > RATE;
  }

  async webSocketMessage(ws, raw){
    if (typeof raw !== "string" || raw.length > MAX_FRAME) return;
    const me = this.meta(ws), now = Date.now();
    this.heard.set(me.id, now);
    if (now - this.swept > 30000) this.sweep(now);   // on someone else's message: costs no request of its own
    if (this.limited(me.id)) return;
    let m; try { m = JSON.parse(raw); } catch(e){ return; }
    if (!m || typeof m !== "object") return;

    if (this.mode === "game" && !me.me){
      if (m.t !== "auth") return;
      const who = await this.whoIs(m.token);
      if (!who){ try { ws.close(4001, "not linked"); } catch(e){} return; }
      ws.serializeAttachment({ ...me, token:m.token });
      this.welcome(ws, who);
      return;
    }

    if (m.t === "p"){
      if (!m.p || typeof m.p !== "object" || Array.isArray(m.p) || JSON.stringify(m.p).length > MAX_PRESENCE) return;
      if (me.me){
        // a pet is what the roster says it is: its name, its level and the form that level makes it
        const f = formOf(me.me.species, me.me.level);
        if (!f) return;   // not evolved yet: it can't be in the world
        m.p.n = me.me.pet; m.p.l = me.me.level; m.p.f = f;
      }
      this.pres.set(me.id, m.p);
      this.broadcast({ t:"p", id:me.id, p:m.p }, ws);
      return;
    }
    if (m.t === "sub" || m.t === "unsub"){
      const prefix = String(m.prefix || "");
      if (!PREFIX.test(prefix)) return;
      const subs = new Set(me.subs);
      if (m.t === "sub") subs.add(prefix); else subs.delete(prefix);
      ws.serializeAttachment({ ...me, subs:[...subs].slice(0, 16) });
      if (m.t === "sub") ws.send(JSON.stringify({ t:"docs", prefix, docs:this.under(prefix) }));
      return;
    }
    if (m.t === "set"){
      const n = m.n | 0, path = String(m.path || "");
      const out = this.mode === "game" ? this.gameWrite(me.me, path, m.data) : this.write(path, m.data);
      if (out.code) ws.send(JSON.stringify({ t:"err", n, code:out.code }));
      else {
        ws.send(JSON.stringify({ t:"ack", n }));
        if (out.changed) this.tell(path, out.data);
        if (out.felled) this.tell(STATE, out.felled);
      }
      return;
    }
    if (m.t === "attempt" && this.mode === "game") return this.attempt(ws, me, m.n | 0);
    if (m.t === "attempt-end" && this.mode === "game")
      this.ctx.storage.sql.exec("DELETE FROM attempts WHERE handle = ?", me.me.handle);
  }

  /* An attempt: a swing spent at the broker, then a window in which this
     player's damage may grow - by no more than a pet of its level could do. */
  async attempt(ws, meta, n){
    const me = meta.me, say = o => { try { ws.send(JSON.stringify({ t:"attempt", n, ...o })); } catch(e){} };
    if (!formOf(me.species, me.level)) return say({ ok:false, why:"your pet has to evolve first" });
    let st = this.read(STATE);
    if (st && st.felledAt){
      // down - unless the switch has been thrown since: ask the game for its round
      this.seenAt.delete(meta.token); await this.whoIs(meta.token);
      st = this.read(STATE);
      if (st && st.felledAt) return say({ ok:false, why:"he is down" });
    }
    let r, out;
    try { r = await this.broker("/explore/attempt", meta.token, { method:"POST" }); out = await r.json(); }
    catch(e){ return say({ ok:false, why:"the game's server can't be reached" }); }
    if (!out || !out.ok) return say({ ok:false, why:out && out.why || "refused", left:out && out.left || 0, toNext:out && out.toNext });
    await this.round(Number(out.epoch) || 1, meta.token);
    const cur = this.read(STATE), key = `raids/e${cur.e}/hits/${me.handle}`, have = this.read(key);
    this.ctx.storage.sql.exec("INSERT OR REPLACE INTO attempts (handle, e, start, cap, at) VALUES (?, ?, ?, ?, ?)",
      me.handle, cur.e, have ? Number(have.dm) || 0 : 0, attemptCap(out.level || me.level), Date.now());
    const hit = this.seenAt.get(meta.token);
    if (hit) hit.me.swings = { ...(hit.me.swings || {}), left:out.left, earned:out.earned, spent:out.spent, toNext:out.toNext };
    say({ ok:true, left:out.left, toNext:out.toNext, round:cur.e });
  }

  /* The game world's store: the round is the server's alone, and a player's
     damage only grows inside an attempt they have paid for. */
  gameWrite(me, path, data){
    if (!me || !data || typeof data !== "object" || Array.isArray(data)) return { code:"invalid_argument" };
    const h = HIT.exec(path);
    if (!h || h[2] !== me.handle) return { code:"permission_denied" };
    const st = this.read(STATE);
    if (!st || (h[1] | 0) !== st.e) return { code:"failed_precondition" };
    const att = this.ctx.storage.sql.exec("SELECT e, start, cap, at FROM attempts WHERE handle = ?", me.handle).toArray()[0];
    if (!att || att.e !== st.e || Date.now() - att.at > ATTEMPT_MS) return { code:"failed_precondition" };
    const cur = this.read(path), was = cur ? Number(cur.dm) || 0 : 0;
    const dm = Math.round(Math.min(att.start + att.cap, Math.max(0, +data.dm || 0)));
    if (dm <= was) return { changed:false };
    const next = { dm, n:me.pet, sp:me.species, f:String(data.f || "").slice(0, 12), at:Date.now() };
    this.put(path, next);
    let felled = null;
    if (!st.felledAt && this.dealt(st.e) >= RAID_HP){ felled = { e:st.e, felledAt:Date.now() }; this.put(STATE, felled); }
    return { changed:true, data:next, felled };
  }

  read(path){
    const row = this.ctx.storage.sql.exec("SELECT data FROM docs WHERE path = ?", path).toArray()[0];
    return row ? JSON.parse(row.data) : null;
  }
  put(path, data){
    this.ctx.storage.sql.exec("INSERT INTO docs (path, data, at) VALUES (?, ?, ?) ON CONFLICT(path) DO UPDATE SET data = excluded.data, at = excluded.at",
      path, JSON.stringify(data), Date.now());
  }
  under(prefix){
    return this.ctx.storage.sql.exec("SELECT path, data FROM docs WHERE path = ? OR path LIKE ?", prefix, prefix + "/%")
      .toArray().slice(0, 2000).map(r => ({ path:r.path, data:JSON.parse(r.data) }));
  }
  /* The demo's store, as before: each kept so that it can only move one way:
     a round forward (and, within a round, from standing to felled), a tab's
     damage up. A write that would go back is accepted and changes nothing -
     it is just late. */
  write(path, data){
    if (!data || typeof data !== "object" || Array.isArray(data)) return { code:"invalid_argument" };
    let next;
    if (path === STATE){
      const e = data.e | 0, felledAt = Math.max(0, +data.felledAt || 0);
      if (e < 1) return { code:"invalid_argument" };
      const cur = this.read(path) || { e:1, felledAt:0 };
      if (e < cur.e) return { changed:false };
      next = e > cur.e ? { e, felledAt } : { e, felledAt:cur.felledAt || felledAt };
      if (e === cur.e && next.felledAt === cur.felledAt) return { changed:false };
    } else if (HIT.test(path)){
      const dm = Math.round(Math.min(1e7, Math.max(0, +data.dm || 0)));
      const cur = this.read(path);
      if (cur && cur.dm >= dm) return { changed:false };
      if (!cur){
        const count = this.ctx.storage.sql.exec("SELECT COUNT(*) AS c FROM docs").toArray()[0].c;
        if (count >= MAX_DOCS) return { code:"quota_exceeded" };
      }
      next = { dm, n:String(data.n || "").slice(0, 14), f:String(data.f || "").slice(0, 12), at:Date.now() };
    } else return { code:"invalid_argument" };
    this.put(path, next);
    return { changed:true, data:next };
  }
  tell(path, data){
    const s = JSON.stringify({ t:"doc", path, data });
    for (const ws of this.ctx.getWebSockets()){
      if (!this.inside(ws)) continue;
      const subs = this.meta(ws).subs || [];
      if (subs.some(p => path === p || path.startsWith(p + "/"))){ try { ws.send(s); } catch(e){} }
    }
  }

  async webSocketClose(ws, code){ this.gone(ws); try { ws.close(code, "bye"); } catch(e){} }
  async webSocketError(ws){ this.gone(ws); }
  /* A live page says something at least once a second (its heartbeat), so
     one that has been silent for IDLE_MS is frozen or gone: let it go. A
     page that wakes up after that simply connects again. In the game world
     a page that never said who it is is let go sooner. */
  sweep(now){
    this.swept = now;
    for (const ws of this.ctx.getWebSockets()){
      const m = this.meta(ws), last = this.heard.get(m.id);
      if (this.mode === "game" && !m.me && now - (m.since || now) > AUTH_MS){ this.gone(ws); try { ws.close(4001, "not linked"); } catch(e){} continue; }
      if (last === undefined){ this.heard.set(m.id, now); continue; }   // just woken: count from now
      if (now - last > IDLE_MS){ this.gone(ws); try { ws.close(4000, "idle"); } catch(e){} }
    }
  }
  gone(ws){
    const m = this.meta(ws);
    this.pres.delete(m.id); this.rate.delete(m.id); this.heard.delete(m.id);
    if (this.inside(ws)) this.broadcast({ t:"left", id:m.id }, ws);
  }
}
