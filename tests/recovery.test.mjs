import assert from "node:assert/strict";
import http from "node:http"; import fs from "node:fs"; import path from "node:path";
import { createRequire } from "node:module"; import { makeHarness, REPO, OUT } from "./lib.mjs";
const { chromium } = createRequire(import.meta.url)("playwright");
const { worker, env, call, callback, storageOf, objects } = await makeHarness(null, { APP_ORIGIN: "http://localhost:8796", APP_PATH: "/index.html" });
const W = "https://runmon-strava.runmon-gq.workers.dev";
const server = http.createServer((q, r) => { const f = path.join(REPO, new URL(q.url,"http://x").pathname);
  if (!fs.existsSync(f) || fs.statSync(f).isDirectory()){ r.writeHead(404); return r.end(); }
  r.writeHead(200, {"Content-Type": f.endsWith(".html") ? "text/html" : "image/png"}); fs.createReadStream(f).pipe(r); }).listen(8796);
const b = await chromium.launch();
const errs = [];
async function phone(){
  const ctx = await b.newContext({ viewport:{ width:390, height:844 }, deviceScaleFactor: 2 });
  await ctx.grantPermissions(["clipboard-read", "clipboard-write"], { origin: "http://localhost:8796" });
  const p = await ctx.newPage(); p.on("pageerror", e => errs.push(String(e)));
  await p.route(W + "/**", async route => { const req = route.request(); const u = new URL(req.url());
    const r = await worker.fetch(new Request("https://broker" + u.pathname + u.search, { method: req.method(), headers: req.headers(), body: ["GET","HEAD"].includes(req.method()) ? undefined : req.postData() }), env, { waitUntil(){} });
    const h = {}; r.headers.forEach((v,k)=>h[k]=v); await route.fulfill({ status:r.status, headers:h, body: await r.text() }); });
  await p.route(/unpkg|cdnjs|jsdelivr|tile|fonts\.g|runmon-explore/, r => r.abort());
  return p;
}
const APP = "http://localhost:8796/index.html", now = Date.now();
const title = p => p.evaluate(() => document.querySelector("#sheet-wrap.show #sheet h3")?.textContent || null);

// --- phone 1: a Health-only player sets up and saves their code
const p1 = await phone();
await p1.goto(APP);
await p1.evaluate(s => { localStorage.clear(); localStorage.setItem("runmon.save.v1", JSON.stringify(s)); },
  { v:1, species:"verdant", petName:"Bao", createdAt: now - 20*864e5, runs:[], badges:{}, seenStage:1, settings:{ units:"km", weightKg:70, xpAnim:false }, friends:[] });
await p1.goto("about:blank"); await p1.goto(APP + "?health=1"); await p1.waitForTimeout(900);
await p1.evaluate(() => go("settings")); await p1.click("#health-on"); await p1.waitForTimeout(900);
assert.equal(await p1.evaluate(() => document.querySelectorAll("#sheet .hg-dots i").length), 5, "five steps for a Health-only player");
for (let i = 0; i < 4; i++){ await p1.click('[data-sheet-act="1"]'); await p1.waitForTimeout(250); }
await p1.waitForTimeout(500);
assert.equal(await title(p1), "Save your recovery code");
const shown = await p1.evaluate(() => document.querySelector(".recovery-code").textContent.trim());
assert.match(shown, /^[A-Z2-9]{4}-[A-Z2-9]{4}-[A-Z2-9]{4}-[A-Z2-9]{4}$/, shown);
await p1.screenshot({ path: OUT + "/rc-guide.png" });
await p1.click('[data-health="rc-copy"]'); await p1.waitForTimeout(250);
assert.equal(await p1.evaluate(() => navigator.clipboard.readText()), shown);
await p1.click('[data-sheet-act="1"]'); await p1.waitForTimeout(400);
const panel = await p1.evaluate(() => document.querySelector("#health-panel").innerText);
assert.match(panel, /Recovery code/); assert.doesNotMatch(panel, /Not saved yet/);
// a run in, so the restored pet has something to prove it is the same one
await p1.evaluate(() => { Runmon.state.save.runs.push(makeRun(Date.now() - 3600e3, 5, 1800, { health: "h:x" })); persist(); });
await p1.waitForTimeout(2000);                                   // the debounced push
const pid1 = (await p1.evaluate(() => localStorage.getItem("runmon.strava.session"))).split(".")[0];

// --- phone 2: a brand-new browser
const p2 = await phone();
await p2.goto(APP); await p2.waitForTimeout(700);
assert.equal(await p2.evaluate(() => document.querySelector("#ob-restore").hidden), false, "offered to every new visitor now");
await p2.goto(APP + "?health=1"); await p2.waitForTimeout(700);
assert.equal(await p2.evaluate(() => document.querySelector("#ob-restore").hidden), false);
await p2.click("#ob-restore"); await p2.waitForTimeout(200);
await p2.fill("#rc-in", "AAAA-BBBB-CCCC-DDDD"); await p2.click('[data-sheet-act="1"]'); await p2.waitForTimeout(500);
assert.match(await p2.evaluate(() => document.querySelector("#toasts").innerText), /not recognised/);
await p2.screenshot({ path: OUT + "/rc-restore.png" });
await p2.fill("#rc-in", shown.toLowerCase().replace(/-/g, " ")); await p2.click('[data-sheet-act="1"]'); await p2.waitForTimeout(2500);
const st2 = await p2.evaluate(() => ({ name: Runmon.state.save.petName, runs: Runmon.state.save.runs.length,
  link: !!Runmon.state.save.healthLink, onboard: document.querySelector("#onboard").classList.contains("show"),
  pid: localStorage.getItem("runmon.strava.session").split(".")[0] }));
console.log("restored:", JSON.stringify(st2));
assert.equal(st2.name, "Bao"); assert.equal(st2.runs, 1); assert.equal(st2.link, true); assert.equal(st2.onboard, false);
assert.equal(st2.pid, pid1, "the same player");
await p2.screenshot({ path: OUT + "/rc-back.png" });

// --- a new code retires the old
const S = await p1.evaluate(() => localStorage.getItem("runmon.strava.session"));
const fresh = (await call("POST", "/recovery/code", { token: S, body: { rotate: true } })).code;
assert.notEqual(fresh, shown.replace(/-/g, ""));
assert.equal((await call("POST", "/recovery/restore", { body: { code: shown } })).status, 404, "old code dead");
assert.ok((await call("POST", "/recovery/restore", { body: { code: fresh } })).session.startsWith(pid1));
// --- Strava accounts get none
const loc = await callback(901);
const strava = decodeURIComponent(/strava=([^&]+)/.exec(loc)[1]);
assert.equal((await call("POST", "/recovery/code", { token: strava })).status, 400);
assert.deepEqual(errs, []);
console.log("recovery checks passed");
await b.close(); server.close();
