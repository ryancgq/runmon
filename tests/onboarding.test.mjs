import assert from "node:assert/strict";
import http from "node:http"; import fs from "node:fs"; import path from "node:path";
import { createRequire } from "node:module"; import { makeHarness, REPO, OUT } from "./lib.mjs";
const { chromium } = createRequire(import.meta.url)("playwright");
const { worker, env } = await makeHarness(null, { APP_ORIGIN: "http://localhost:8801", APP_PATH: "/index.html" });
const W = "https://runmon-strava.runmon-gq.workers.dev";
const server = http.createServer((q, r) => { const f = path.join(REPO, new URL(q.url,"http://x").pathname);
  if (!fs.existsSync(f) || fs.statSync(f).isDirectory()){ r.writeHead(404); return r.end(); }
  r.writeHead(200, {"Content-Type": f.endsWith(".html") ? "text/html" : f.endsWith(".svg") ? "image/svg+xml" : "image/png"}); fs.createReadStream(f).pipe(r); }).listen(8801);
const b = await chromium.launch(); const errs = [];
async function phone(){
  const p = await (await b.newContext({ viewport:{ width:390, height:844 }, deviceScaleFactor: 2 })).newPage();
  p.on("pageerror", e => errs.push(String(e)));
  await p.route(W + "/**", async route => { const req = route.request(); const u = new URL(req.url());
    const r = await worker.fetch(new Request("https://broker" + u.pathname + u.search, { method: req.method(), headers: req.headers(), body: ["GET","HEAD"].includes(req.method()) ? undefined : req.postData() }), env, { waitUntil(){} });
    const h = {}; r.headers.forEach((v,k)=>h[k]=v); await route.fulfill({ status:r.status, headers:h, body: await r.text() }); });
  await p.route(/unpkg|cdnjs|jsdelivr|tile|fonts\.g|runmon-explore/, r => r.abort());
  return p;
}
const APP = "http://localhost:8801/index.html";
const title = p => p.evaluate(() => document.querySelector("#sheet-wrap.show #sheet h3")?.textContent || null);
const settings = p => p.evaluate(() => ({
  order: [...document.querySelectorAll("#screen-settings .section-title")].filter(e => !e.hidden).map(e => e.textContent.trim()).slice(0, 3),
  connect: (() => { const b = document.querySelector("#strava-panel .btn[disabled]"); return b ? "greyed" : document.querySelector("#strava-panel #strava-on") ? "enabled" : "none"; })(),
  text: document.querySelector("#strava-panel").innerText }));

// 1. a brand-new player
const p = await phone();
await p.goto(APP); await p.evaluate(() => localStorage.clear()); await p.goto("about:blank"); await p.goto(APP); await p.waitForTimeout(700);
assert.equal(await p.evaluate(() => document.querySelector("#ob-restore").hidden), false, "restore offered to everyone now");
await p.click("#ob-go"); await p.waitForTimeout(300);
const ob = await p.evaluate(() => ({ h: document.querySelector("#ob-strava-h").textContent,
  health: !document.querySelector("#ob-health-go").hidden, strava: !document.querySelector("#ob-strava-go").hidden,
  consent: !document.querySelector("#ob-consent").hidden, signin: !document.querySelector("#ob-strava-signin").hidden }));
console.log("onboarding:", JSON.stringify(ob));
assert.deepEqual(ob, { h: "Connect Apple Health", health: true, strava: false, consent: false, signin: true });
await p.screenshot({ path: OUT + "/full-ob.png" });
// a returning Strava player's way in: Strava's own sheet, official button and all
await p.click("#ob-strava-signin"); await p.waitForTimeout(250);
assert.equal(await title(p), "Connect Strava");
assert.equal(await p.evaluate(() => !!document.querySelector("#sheet #strava-go img")), true, "official Connect with Strava button");
await p.evaluate(() => closeSheet());
// Connect with Apple Health → egg → hatch → straight into setup
await p.click("#ob-health-go"); await p.waitForTimeout(300);
await p.click("[data-pick]"); await p.click("#ob-next"); await p.waitForTimeout(200);
await p.fill("#ob-name", "Pip"); await p.click("#ob-hatch"); await p.waitForTimeout(2200);
assert.equal(await title(p), "One more thing: the Shortcut", "setup opens by itself after hatching");
await p.screenshot({ path: OUT + "/full-hatch.png" });
await p.evaluate(() => closeSheet()); await p.waitForTimeout(200);
assert.ok(await p.evaluate(() => !!Runmon.state.save.healthLink), "linked");
await p.evaluate(() => go("settings")); await p.waitForTimeout(300);
const s1 = await settings(p); console.log("new player:", JSON.stringify(s1));
assert.deepEqual(s1.order.slice(0, 2), ["Apple Health", "Strava"]); assert.equal(s1.connect, "greyed");
// and the other road: "Not on an iPhone?" skips, and hatching offers it instead
const r = await phone();
await r.goto(APP); await r.evaluate(() => localStorage.clear()); await r.goto("about:blank"); await r.goto(APP); await r.waitForTimeout(700);
await r.click("#ob-go"); await r.waitForTimeout(300); await r.click("#ob-strava-skip"); await r.waitForTimeout(300);
await r.click("[data-pick]"); await r.click("#ob-next"); await r.waitForTimeout(200);
await r.fill("#ob-name", "Moss"); await r.click("#ob-hatch"); await r.waitForTimeout(2200);
assert.equal(await title(r), "Feed Moss", "skipping still gets the offer after hatching");
assert.equal(await p.evaluate(() => document.querySelector("#strava-panel .btn[disabled]").disabled), true);
await p.screenshot({ path: OUT + "/full-settings.png" });
// the sign-in for returning players still opens Strava's sheet
await p.click("#strava-panel #strava-on"); await p.waitForTimeout(250);
assert.equal(await title(p), "Connect Strava"); await p.evaluate(() => closeSheet());

// 2. a returning Strava player, disconnected within the grace period
const q = await phone(); const now = Date.now();
await q.goto(APP);
await q.evaluate(s => { localStorage.clear(); localStorage.setItem("runmon.save.v1", JSON.stringify(s)); },
  { v:1, species:"ember", petName:"Ash", createdAt: now - 40*864e5, runs:[], badges:{}, seenStage:1, settings:{ units:"km", weightKg:70, xpAnim:false }, friends:[], stravaConsentAt: now - 30*864e5, parkedAt: now - 3*864e5 });
await q.goto("about:blank"); await q.goto(APP); await q.waitForTimeout(800);
await q.evaluate(() => go("settings")); await q.waitForTimeout(300);
const s2 = await settings(q); console.log("returning:", JSON.stringify(s2));
assert.equal(s2.connect, "enabled", "a returning Strava player can always connect"); assert.match(s2.text, /Connect before/);
assert.equal(errs.length, 0, errs.join("\n"));
console.log("full checks passed");
await b.close(); server.close();
