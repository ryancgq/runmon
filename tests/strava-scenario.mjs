// One Strava player's afternoon - linking, a double upload, a manual run, a
// treadmill run, a ride, Check now twice - and a new visitor skipping
// onboarding, against one build, with everything they could see or store
// written to a JSON file. strava-unchanged.mjs runs it against two builds
// and compares. Usage: node strava-scenario.mjs <appDir> <workerFile> <port> <out.json>
import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
import { makeHarness } from "./lib.mjs";
const { chromium } = createRequire(import.meta.url)("playwright");
const [REPO, WORKER, PORT, OUT] = process.argv.slice(2);

const { worker, env, callback, strava, storageOf } =
  await makeHarness(WORKER, { APP_ORIGIN: "http://localhost:" + PORT, APP_PATH: "/index.html" });
const W = "https://runmon-strava.runmon-gq.workers.dev";
const server = http.createServer((req, res) => {
  const f = path.join(REPO, decodeURIComponent(new URL(req.url, "http://x").pathname));
  if (!f.startsWith(REPO) || !fs.existsSync(f) || fs.statSync(f).isDirectory()){ res.writeHead(404); return res.end(); }
  res.writeHead(200, { "Content-Type": f.endsWith(".html") ? "text/html" : f.endsWith(".png") ? "image/png" : "application/octet-stream" });
  fs.createReadStream(f).pipe(res);
}).listen(Number(PORT));

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 420, height: 900 } });
const errors = [], calls = [];
page.on("pageerror", e => errors.push(String(e)));
await page.route(W + "/**", async route => {
  const req = route.request(); const u = new URL(req.url());
  let body = ["GET","HEAD"].includes(req.method()) ? undefined : req.postData();
  // what the app sends, minus the save (compared separately) and the card's clock
  if (body && u.pathname === "/save"){ const j = JSON.parse(body); calls.push(["PUT /save", Object.keys(j).sort()]); }
  else calls.push([req.method() + " " + u.pathname, body || null]);
  const r = await worker.fetch(new Request("https://broker" + u.pathname + u.search, { method: req.method(), headers: req.headers(), body }), env, { waitUntil(){} });
  const headers = {}; r.headers.forEach((v, k) => headers[k] = v);
  await route.fulfill({ status: r.status, headers, body: await r.text() });
});
await page.route(/unpkg|cdnjs|jsdelivr|tile|fonts\.g|workers\.dev\/(?!)/, r => r.abort());
await page.addInitScript(() => {
  window.__toasts = [];
  new MutationObserver(ms => { for (const m of ms) for (const n of m.addedNodes)
    if (n.classList && n.classList.contains("toast")) window.__toasts.push(n.textContent.trim()); })
    .observe(document, { childList: true, subtree: true });
});

const APP = `http://localhost:${PORT}/index.html`;
const H = 3600e3, now = Date.now(), iso = t => new Date(t).toISOString();
const out = {};

// a brand-new visitor: what onboarding says
await page.goto(APP); await page.evaluate(() => localStorage.clear());
await page.goto("about:blank"); await page.goto(APP); await page.waitForTimeout(700);
await page.click("#ob-go").catch(() => {});
await page.waitForTimeout(200);
await page.click("#ob-strava-skip").catch(() => {});
await page.waitForTimeout(300);
out.newVisitor = { toasts: await page.evaluate(() => window.__toasts.slice()) };

// a Strava player
const seed = { v:1, species:"ember", petName:"Ash", createdAt: now - 20*24*H, runs:[], badges:{}, seenStage:1,
  settings:{ units:"km", weightKg:70, xpAnim:false }, friends:[], stravaConsentAt: now - 5*24*H };
await page.evaluate(s => { localStorage.clear(); localStorage.setItem("runmon.save.v1", JSON.stringify(s)); }, seed);
const loc = await callback(777);
// connectedAt is set at the callback; runs from before it are not Strava's to give
storageOf("777").set("connectedAt", now - 4*24*H);
const tA = now - 3*24*H, tC = now - 30*H, tD = now - 6*H;
strava.acts = [
  { id: 1, type:"Run", start_date: iso(tA), distance: 5000, moving_time: 1600, elapsed_time: 1700 },
  // the same outing uploaded twice - watch and phone - under another id
  { id: 2, type:"Run", start_date: iso(tA + 30e3), distance: 4980, moving_time: 1580, elapsed_time: 1650 },
  { id: 3, type:"Run", start_date: iso(tC), distance: 8000, moving_time: 2600, elapsed_time: 2700, manual: true },
  { id: 4, type:"VirtualRun", start_date: iso(tD), distance: 3000, moving_time: 1000, elapsed_time: 1000 },
  { id: 5, type:"Ride", start_date: iso(tD + H), distance: 20000, moving_time: 3000, elapsed_time: 3100 },
];
await page.goto("about:blank"); await page.goto(loc.replace("https://app/runmon/", APP));
await page.waitForTimeout(3000);
const snap = () => page.evaluate(() => ({
  runs: Runmon.state.save.runs.map(r => Object.fromEntries(Object.entries(r).filter(([k]) => k !== "id").sort())),
  saveKeys: Object.keys(Runmon.state.save).sort(),
  greeting: document.querySelector("#greeting-sub").textContent,
  level: Runmon.state.derived.level, xp: Runmon.state.derived.totalXp,
  local: Object.keys(localStorage).sort()
}));
out.afterLink = await snap();
await page.evaluate(() => go("settings")); await page.waitForTimeout(300);
out.settings = await page.evaluate(() => ({
  titles: [...document.querySelectorAll("#screen-settings .section-title")].filter(e => !e.hidden && e.offsetParent).map(e => e.textContent.trim()),
  strava: document.querySelector("#strava-panel").innerText.replace(/Last checked: .*?\./, "Last checked: X."),
  healthVisible: !!(document.querySelector("#health-panel") && !document.querySelector("#health-panel").hidden),
  storage: document.querySelector("#storage-where").textContent
}));
// Check now, twice
await page.evaluate(() => { window.__toasts.length = 0; return stravaSync({ loud:true }); }); await page.waitForTimeout(800);
strava.acts.push({ id: 6, type:"Run", start_date: iso(now - 2*H), distance: 4000, moving_time: 1300, elapsed_time: 1350 });
await page.evaluate(() => stravaSync({ loud:true })); await page.waitForTimeout(800);
out.checkNow = { toasts: await page.evaluate(() => window.__toasts.slice()), after: await snap() };
const st = storageOf("777");
const clean = v => JSON.parse(JSON.stringify(v, (k, x) => ["at", "lastSync", "lastSeen", "firstSeen", "connectedAt", "stravaSyncedAt", "expires"].includes(k) ? "T" : x));
out.broker = { keys: [...st.keys()].sort(), importedAt: Object.keys(st.get("importedAt") || {}).sort(),
  raidBank: st.get("raidBank"), floor: st.get("floor") || 0,
  saveRuns: (st.get("save").runs || []).map(r => clean(Object.fromEntries(Object.entries(r).filter(([k]) => k !== "id").sort()))) };
out.calls = calls.map(c => c[0] === "PUT /save" ? c : [c[0]]);
out.errors = errors;
fs.writeFileSync(OUT, JSON.stringify(clean(out), null, 1));
console.log("wrote", OUT, "runs:", out.afterLink.runs.length, "errors:", errors.length);
await browser.close(); server.close();
