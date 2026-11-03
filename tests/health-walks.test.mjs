import assert from "node:assert/strict";
import http from "node:http"; import fs from "node:fs"; import path from "node:path";
import { createRequire } from "node:module"; import { makeHarness, REPO, OUT } from "./lib.mjs";
const { chromium } = createRequire(import.meta.url)("playwright");
const { worker, env, call, storageOf } = await makeHarness(null, { APP_ORIGIN: "http://localhost:8792", APP_PATH: "/index.html" });
const W = "https://runmon-strava.runmon-gq.workers.dev";
const server = http.createServer((q, r) => { const f = path.join(REPO, new URL(q.url,"http://x").pathname);
  if (!fs.existsSync(f) || fs.statSync(f).isDirectory()){ r.writeHead(404); return r.end(); }
  r.writeHead(200, {"Content-Type": f.endsWith(".html") ? "text/html" : "image/png"}); fs.createReadStream(f).pipe(r); }).listen(8792);
const b = await chromium.launch(); const p = await b.newPage({ viewport:{ width:390, height:844 } });
const errs = []; p.on("pageerror", e => errs.push(String(e)));
await p.route(W + "/**", async route => { const req = route.request(); const u = new URL(req.url());
  const r = await worker.fetch(new Request("https://broker" + u.pathname + u.search, { method: req.method(), headers: req.headers(), body: ["GET","HEAD"].includes(req.method()) ? undefined : req.postData() }), env, { waitUntil(){} });
  const h = {}; r.headers.forEach((v,k)=>h[k]=v); await route.fulfill({ status:r.status, headers:h, body: await r.text() }); });
await p.route(/unpkg|cdnjs|jsdelivr|tile|fonts\.g|runmon-explore/, r => r.abort());
const now = Date.now(), APP = "http://localhost:8792/index.html", M = 60e3, H = 3600e3, iso = t => new Date(t).toISOString();
await p.goto(APP);
await p.evaluate(s => { localStorage.clear(); localStorage.setItem("runmon.save.v1", JSON.stringify(s)); },
  { v:1, species:"ember", petName:"Ash", createdAt: now - 20*864e5, runs:[], badges:{}, seenStage:1, settings:{ units:"km", weightKg:70, xpAnim:false }, friends:[] });
await p.goto("about:blank"); await p.goto(APP + "?health=1"); await p.waitForTimeout(900);
await p.evaluate(() => go("settings")); await p.click("#health-on"); await p.waitForTimeout(700); await p.evaluate(() => closeSheet());
const key = (await p.evaluate(() => Runmon.state.save.healthLink.url)).split("/").pop();
const pid = (await p.evaluate(() => localStorage.getItem("runmon.strava.session"))).split(".")[0];
storageOf(pid).set("healthSince", now - 10*24*H);
const slices = (t0, mins, kmPerMin, src) => Array.from({ length: mins }, (_, m) => `${iso(t0 + m*M)} | ${iso(t0 + (m+1)*M)} | ${kmPerMin.toFixed(4)} | ${src}`);
// a 4 km walk two days ago, a 4 km walk yesterday, nothing else
const lines = [...slices(now - 50*H, 48, 1/12, "iPhone"), ...slices(now - 26*H, 48, 1/12, "iPhone")];
// and the steps the phone counted alongside, about 110 a minute
const steps = lines.map(l => l.replace(/\| [0-9.]+ \|/, "| 110 |"));
await call("POST", "/health/import/" + key, { body: { samples: lines.join("\n"), steps: steps.join("\n") } });
await p.evaluate(() => go("home")); await p.goto(APP + "#health"); await p.waitForTimeout(2500);
const st = await p.evaluate(() => ({ runs: Runmon.state.save.runs.map(r => ({ walk: !!r.walk, km: r.km, xp: r.xp, mood: r.mood })),
  mood: Runmon.state.derived.mood.key, streak: Runmon.state.derived.streak, gap: Runmon.state.derived.gapDays,
  greeting: (go("home"), document.querySelector("#greeting-sub").textContent),
  // what a run of the same distance at the same moment would have been paid
  runXp: (() => { const r = makeRun(Runmon.state.save.runs[0].t, Runmon.state.save.runs[0].km, Runmon.state.save.runs[0].sec); return r.xp; })() }));
console.log(JSON.stringify(st, null, 1));
assert.equal(st.runs.length, 2); assert.ok(st.runs.every(r => r.walk));
assert.equal(st.mood, "happy", "two 4 km walks do not climb the ladder (a new pet starts Happy)");
assert.equal(st.streak, 0, "walks keep no streak");
assert.equal(st.gap, Infinity, "and are not the last run");
assert.doesNotMatch(st.greeting, /Infinity/, "greeting: " + st.greeting);
assert.ok(Math.abs(st.runs[0].xp - st.runXp / 2) <= 2, `walk paid half: ${st.runs[0].xp} vs run ${st.runXp}`);
await p.evaluate(() => go("history")); await p.waitForTimeout(300);
assert.match(await p.evaluate(() => document.body.innerText), /walk, half XP/);
assert.deepEqual(errs, []);
console.log("walk checks passed");
await b.close(); server.close();
