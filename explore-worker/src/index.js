/* Runmon Explore - the shared world, outside Claude.
 *
 * Inside Claude, the Explore page gets everyone in one world from the
 * Artifact page's `room` (who is here, live) and `db` (a small store that
 * outlasts everyone leaving). Outside it, this worker is both, speaking just
 * enough of the same two shapes that the page's game code doesn't change:
 *
 *   presence  each page sends its own presence object about ten times a
 *             second; it is relayed to everyone else as it comes. Held in
 *             memory only - nothing about a player outlives their tab.
 *   docs      JSON documents at slash paths, with subscriptions by prefix.
 *             Only the boss's account lives here:
 *               raids/state                the round, and when he fell
 *               raids/e<round>/hits/<tab>  what one tab took off him
 *             Damage only ever grows and a round only ever moves on, so the
 *             store keeps the larger figure and never goes back a round -
 *             two pages writing at once can't undo each other.
 *
 * One Durable Object, World, holds all of it: one place, so it needs no
 * locking, and its SQLite storage keeps the account. It holds no game
 * rules: the pages fight; it relays and remembers.
 *
 * Protocol (JSON text frames):
 *   server -> page  {t:"hello", id, peers:[{id, p}]}   on connect
 *                   {t:"join", id} {t:"left", id} {t:"p", id, p}
 *                   {t:"doc", path, data}  (data null = no such document)
 *                   {t:"docs", prefix, docs:[{path, data}]}  answering a sub
 *                   {t:"ack", n} {t:"err", n, code}
 *   page -> server  {t:"p", p}  {t:"sub", prefix}  {t:"unsub", prefix}
 *                   {t:"set", n, path, data}
 */

const MAX_PEERS = 64;          // one world; past this a page plays alone
const MAX_FRAME = 8192;        // bytes of JSON in one message
const MAX_PRESENCE = 4096;     // the same bound the page keeps inside Claude
const MAX_DOCS = 20000;
const RATE = 60;               // messages a second a page may send
const IDLE_MS = 120000;        // a page that has said nothing for this long (a frozen or locked phone) is let go
const STATE = "raids/state";
const HIT = /^raids\/e(\d{1,7})\/hits\/([a-z0-9]{4,20})$/;
const PREFIX = /^raids(\/(state|e\d{1,7}(\/hits)?))?$/;

export default {
  async fetch(req, env){
    const url = new URL(req.url);
    if (url.pathname === "/health") return new Response("ok", { headers:{ "content-type":"text/plain", "access-control-allow-origin":"*" } });
    if (url.pathname !== "/world") return new Response("not found", { status:404 });
    if ((req.headers.get("Upgrade") || "").toLowerCase() !== "websocket") return new Response("this is a websocket", { status:426 });
    const origin = req.headers.get("Origin") || "";
    const allowed = String(env.ALLOWED_ORIGINS || "").split(",").map(s => s.trim()).filter(Boolean);
    if (allowed.length && !allowed.includes(origin)) return new Response("not from here", { status:403 });
    if (env.JOIN_CODE && url.searchParams.get("code") !== env.JOIN_CODE) return new Response("wrong code", { status:403 });
    return env.WORLD.get(env.WORLD.idFromName("world")).fetch(req);
  }
};

export class World {
  constructor(ctx, env){
    this.ctx = ctx; this.env = env;
    this.pres = new Map();     // peer id -> presence; rebuilt from the pages' next sends after a sleep
    this.rate = new Map();     // peer id -> [window start, count]
    this.heard = new Map();    // peer id -> when it last said anything
    this.swept = 0;
    ctx.storage.sql.exec("CREATE TABLE IF NOT EXISTS docs (path TEXT PRIMARY KEY, data TEXT NOT NULL, at INTEGER NOT NULL)");
  }

  async fetch(){
    const live = this.ctx.getWebSockets();
    if (live.length >= MAX_PEERS) return new Response("the world is full", { status:503 });
    const [client, server] = Object.values(new WebSocketPair());
    const id = "p" + crypto.randomUUID().replace(/-/g, "").slice(0, 12);
    // hibernation: the object can sleep between messages without dropping anyone
    this.ctx.acceptWebSocket(server);
    server.serializeAttachment({ id, subs:[] });
    server.send(JSON.stringify({ t:"hello", id, peers:this.everyone(server) }));
    this.broadcast({ t:"join", id }, server);
    return new Response(null, { status:101, webSocket:client });
  }

  meta(ws){ return ws.deserializeAttachment() || { id:"?", subs:[] }; }
  everyone(except){
    const out = [];
    for (const ws of this.ctx.getWebSockets()){ if (ws === except) continue; const id = this.meta(ws).id; out.push({ id, p:this.pres.get(id) || {} }); }
    return out;
  }
  broadcast(msg, except){
    const s = JSON.stringify(msg);
    for (const ws of this.ctx.getWebSockets()) if (ws !== except){ try { ws.send(s); } catch(e){} }
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

    if (m.t === "p"){
      if (!m.p || typeof m.p !== "object" || Array.isArray(m.p) || JSON.stringify(m.p).length > MAX_PRESENCE) return;
      this.pres.set(me.id, m.p);
      this.broadcast({ t:"p", id:me.id, p:m.p }, ws);
      return;
    }
    if (m.t === "sub" || m.t === "unsub"){
      const prefix = String(m.prefix || "");
      if (!PREFIX.test(prefix)) return;
      const subs = new Set(me.subs);
      if (m.t === "sub") subs.add(prefix); else subs.delete(prefix);
      ws.serializeAttachment({ id:me.id, subs:[...subs].slice(0, 16) });
      if (m.t === "sub") ws.send(JSON.stringify({ t:"docs", prefix, docs:this.under(prefix) }));
      return;
    }
    if (m.t === "set"){
      const n = m.n | 0, path = String(m.path || "");
      const out = this.write(path, m.data);
      if (out.code) ws.send(JSON.stringify({ t:"err", n, code:out.code }));
      else {
        ws.send(JSON.stringify({ t:"ack", n }));
        if (out.changed) this.tell(path, out.data);
      }
    }
  }

  read(path){
    const row = this.ctx.storage.sql.exec("SELECT data FROM docs WHERE path = ?", path).toArray()[0];
    return row ? JSON.parse(row.data) : null;
  }
  under(prefix){
    return this.ctx.storage.sql.exec("SELECT path, data FROM docs WHERE path = ? OR path LIKE ?", prefix, prefix + "/%")
      .toArray().slice(0, 2000).map(r => ({ path:r.path, data:JSON.parse(r.data) }));
  }
  /* The only two kinds of document, each kept so that it can only move one
     way: a round forward (and, within a round, from standing to felled), a
     tab's damage up. A write that would go back is accepted and changes
     nothing - it is just late. */
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
    this.ctx.storage.sql.exec("INSERT INTO docs (path, data, at) VALUES (?, ?, ?) ON CONFLICT(path) DO UPDATE SET data = excluded.data, at = excluded.at",
      path, JSON.stringify(next), Date.now());
    return { changed:true, data:next };
  }
  tell(path, data){
    const s = JSON.stringify({ t:"doc", path, data });
    for (const ws of this.ctx.getWebSockets()){
      const subs = this.meta(ws).subs || [];
      if (subs.some(p => path === p || path.startsWith(p + "/"))){ try { ws.send(s); } catch(e){} }
    }
  }

  async webSocketClose(ws, code){ this.gone(ws); try { ws.close(code, "bye"); } catch(e){} }
  async webSocketError(ws){ this.gone(ws); }
  /* A live page says something at least once a second (its heartbeat), so
     one that has been silent for IDLE_MS is frozen or gone: let it go. A
     page that wakes up after that simply connects again. */
  sweep(now){
    this.swept = now;
    for (const ws of this.ctx.getWebSockets()){
      const id = this.meta(ws).id, last = this.heard.get(id);
      if (last === undefined){ this.heard.set(id, now); continue; }   // just woken: count from now
      if (now - last > IDLE_MS){ this.gone(ws); try { ws.close(4000, "idle"); } catch(e){} }
    }
  }
  gone(ws){
    const id = this.meta(ws).id;
    this.pres.delete(id); this.rate.delete(id); this.heard.delete(id);
    this.broadcast({ t:"left", id }, ws);
  }
}
