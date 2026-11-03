// End-to-end on the Explore branch: the real index.html in Chromium, its
// broker answered by the real worker code with in-memory objects and a fake Strava.
import assert from "node:assert/strict";
import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
import { makeHarness, REPO, OUT } from "./lib.mjs";
const { chromium } = createRequire(import.meta.url)("playwright");

const { worker, env, call, callback, strava, storageOf } =
  await makeHarness(null, { APP_ORIGIN: "http://localhost:8767", APP_PATH: "/index.html" });
const W = "https://runmon-strava.runmon-gq.workers.dev";

const server = http.createServer((req, res) => {
  const f = path.join(REPO, decodeURIComponent(new URL(req.url, "http://x").pathname));
  if (!f.startsWith(REPO) || !fs.existsSync(f) || fs.statSync(f).isDirectory()){ res.writeHead(404); return res.end(); }
  res.writeHead(200, { "Content-Type": f.endsWith(".html") ? "text/html" : f.endsWith(".png") ? "image/png" : "application/octet-stream" });
  fs.createReadStream(f).pipe(res);
}).listen(8767);

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 420, height: 900 } });
const errors = [], fails = [];
page.on("pageerror", e => errors.push(String(e)));
let failSave = false;
await page.route(W + "/**", async route => {
  const req = route.request();
  const u = new URL(req.url());
  if (failSave && u.pathname === "/save") return route.fulfill({ status: 503, body: "{}" });
  const r = await worker.fetch(new Request("https://broker" + u.pathname + u.search, { method: req.method(), headers: req.headers(),
    body: ["GET","HEAD"].includes(req.method()) ? undefined : req.postData() }), env, { waitUntil(){} });
  if (r.status >= 500) fails.push(u.pathname + " " + await r.clone().text());
  const headers = {}; r.headers.forEach((v, k) => headers[k] = v);
  await route.fulfill({ status: r.status, headers, body: await r.text() });
});
await page.route(/unpkg|cdnjs|jsdelivr|tile|fonts\.g/, r => r.abort());

const APP = "http://localhost:8767/index.html";
const H = 3600e3, now = Date.now(), iso = t => new Date(t).toISOString();
const seed = { v:1, species:"ember", petName:"Ash", createdAt: now - 20*24*H, runs:[], badges:{}, seenStage:1,
  settings:{ units:"km", weightKg:70, xpAnim:false }, friends:[] };
await page.goto(APP);
await page.evaluate(s => { localStorage.clear(); localStorage.setItem("runmon.save.v1", JSON.stringify(s)); }, seed);
await page.goto("about:blank"); await page.goto(APP);
await page.waitForTimeout(600);
// switch off by default: no Health section for anybody
await page.evaluate(() => go("settings"));
assert.equal(await page.evaluate(() => document.querySelector("#health-panel").hidden), false, "shown to a player not on Strava, no switch needed");
// turned on the way the owner would, and remembered
await page.goto("about:blank"); await page.goto(APP + "?health=1");
await page.waitForTimeout(600);
assert.equal(await page.evaluate(() => location.search), "", "flag scrubbed from the address");
await page.goto("about:blank"); await page.goto(APP);
await page.waitForTimeout(600);
const state = () => page.evaluate(() => ({
  runs: Runmon.state.save.runs.map(r => ({ t:r.t, km:r.km, src: r.strava ? "strava" : r.health ? "health" : "gps", key: r.health || r.strava })),
  link: Runmon.state.save.healthLink || null, session: localStorage.getItem("runmon.strava.session") }));

// 1. set up Apple Health with no Strava
await page.evaluate(() => go("settings"));
await page.click("#health-on");
await page.waitForSelector("#sheet-wrap.show [data-health=\"copy\"], #sheet-wrap.show h3"); await page.evaluate(() => closeSheet());
let st = await state();
assert.ok(st.link && /\/health\/import\/[a-z0-9]{24}$/.test(st.link.url), JSON.stringify(st.link));
assert.ok(st.session.startsWith("p"));
const pid = st.session.split(".")[0], key = st.link.url.split("/").pop();
storageOf(pid).set("healthSince", now - 10*24*H);     // as if linked ten days ago
console.log("1 ok: Health-only player", pid);

// 2. the Shortcut sends a watch run, a second app's copy of it, and the watch run again
const t0 = now - 36*H;
const watch = { start: iso(t0), end: iso(t0 + 30*60e3), distance: "5.01 km", type:"Running" };
const copy  = { start: iso(t0 + 20e3), end: iso(t0 + 29*60e3), distance: "4.97 km", type:"Running" };
let put = await call("POST", "/health/import/" + key, { body: { workouts:[watch, copy, watch] } });
assert.equal(put.queued, 1, JSON.stringify(put));
console.log("2 ok: Shortcut reply:", put.message);

// 3. the Shortcut opens the app at #health; the tab is open already
await page.evaluate(() => go("home"));
await page.goto(APP + "#health");
await page.waitForTimeout(1800);
st = await state();
assert.equal(st.runs.length, 1, JSON.stringify(st.runs)); assert.equal(st.runs[0].src, "health");
assert.equal(await page.evaluate(() => location.hash), "");
console.log("3 ok: one run from three copies");

// 4. tapped again from a fresh tab: nothing new
put = await call("POST", "/health/import/" + key, { body: { workouts:[watch, copy] } });
assert.equal(put.queued, 0);
await page.goto("about:blank"); await page.goto(APP + "#health"); await page.waitForTimeout(1800);
assert.equal((await state()).runs.length, 1);
console.log("4 ok: re-sent workouts not counted");
const ex = await page.evaluate(() => stravaCall("/explore/me").then(r => r, e => ({ err: String(e) })));
assert.equal(ex.pet, "Ash", "Explore knows the Health-only pet: " + JSON.stringify(ex));
assert.equal(ex.swings.earned, 1, "5.01 km from Health bought a swing");
console.log("4b ok: Explore works for a Health-only player:", JSON.stringify(ex.swings));

// 5. a second run is queued, then the player connects Strava; Strava has the
//    first run too (watch synced there), the second one, and one of its own
const t1 = now - 20*H, t2 = now - 4*H;
await call("POST", "/health/import/" + key, { body: { workouts:[{ start: iso(t1), end: iso(t1 + 40*60e3), distance: "8 km", type:"Running" }] } });
const loc = await callback(777);
strava.acts = [
  { id: 11, type:"Run", start_date: iso(t0 + 5e3), distance: 5020, moving_time: 1700, elapsed_time: 1790 },
  { id: 12, type:"Run", start_date: iso(t1 + 2e3), distance: 8010, moving_time: 2300, elapsed_time: 2390 },
  { id: 13, type:"Run", start_date: iso(t2), distance: 6000, moving_time: 1900, elapsed_time: 1950 },
];
await page.goto("about:blank"); await page.goto(loc.replace("https://app/runmon/", APP));
await page.waitForTimeout(2500);
st = await state();
console.log("5 runs:", JSON.stringify(st.runs.map(r => [r.src, r.km.toFixed(2)])));
assert.ok(st.session.startsWith("777."));
assert.equal(st.runs.length, 3, "three real runs, each once");
assert.deepEqual(st.runs.map(r => r.src).sort(), ["health", "strava", "strava"]);
assert.equal(storageOf(pid).size, 0, "player object erased after adopt");
console.log("5 ok: Strava + Health copies counted once; adopt carried the queue");

// 6. again: nothing changes; queue drained; no Health key in Strava's id map
await page.evaluate(() => stravaSync({ loud:true })); await page.waitForTimeout(1500);
assert.equal((await state()).runs.length, 3);
const a = storageOf("777");
assert.equal(Object.keys(a.get("healthPending") || {}).length, 0, "queue drained");
assert.ok(!Object.keys(a.get("importedAt") || {}).some(k => k.startsWith("h:")), "no Health key in importedAt");
console.log("6 ok: steady state");

// 7. a lost upload, then a retry: still once
const t3 = now - 2*H;
await call("POST", "/health/import/" + key, { body: { workouts:[{ start: iso(t3), end: iso(t3 + 20*60e3), distance: 3, type:"Running" }] } });
failSave = true;
await page.evaluate(() => stravaSync({ loud:true })); await page.waitForTimeout(1500);
assert.equal((await state()).runs.length, 4);
failSave = false;
await page.evaluate(() => stravaSync({ loud:true })); await page.waitForTimeout(1500);
assert.equal((await state()).runs.length, 4, "retry after a failed upload counts nothing twice");
assert.equal(Object.keys(storageOf("777").get("healthPending") || {}).length, 0);
console.log("7 ok: failed upload + retry");

// 8. a Health workout older than the horizon that was somehow queued is not counted
const t4 = now - 5.5*24*H;
const pend = storageOf("777").get("healthPending") || {};
pend["h:" + Math.round(t4/1000)] = { key: "h:" + Math.round(t4/1000), start: t4, end: t4 + 30*60e3, km: 5, sec: 1800 };
storageOf("777").set("healthPending", pend);
await page.evaluate(() => stravaSync({ loud:true })); await page.waitForTimeout(1500);
assert.equal((await state()).runs.length, 4, "past-horizon workout dropped");
console.log("8 ok: horizon held in the app too");

assert.deepEqual(errors, [], "page errors: " + errors.join("\n"));
assert.deepEqual(fails, [], "broker 5xx: " + fails.join("\n"));
await page.evaluate(() => go("settings"));
await page.waitForTimeout(6500);
await page.setViewportSize({ width: 420, height: 1200 });
await page.locator("#health-title").scrollIntoViewIfNeeded();
await page.waitForTimeout(400);
await page.screenshot({ path: OUT + "/settings2.png" });
console.log("all app checks passed");
await browser.close(); server.close();
