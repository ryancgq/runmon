import assert from "node:assert/strict";
import { makeHarness, REPO, OUT } from "./lib.mjs";
const { call, storageOf } = await makeHarness(null);
const iso = t => new Date(t).toISOString(), M = 60e3, H = 3600e3, now = Date.now();
const link = await call("POST", "/health/link"); const key = link.key, P = link.session, pid = P.split(".")[0];
storageOf(pid).set("healthSince", now - 10*24*H);
const D = [], S = [];
// distance and steps slices together, as a phone's pedometer writes them
const move = (t0, mins, kmPerMin, spm, src, step = 1) => {
  for (let m = 0; m < mins; m += step){
    D.push(`${iso(t0 + m*M)} | ${iso(t0 + (m+step)*M)} | ${(kmPerMin*step).toFixed(4)} | ${src}`);
    if (spm) S.push(`${iso(t0 + m*M)} | ${iso(t0 + (m+step)*M)} | ${Math.round(spm*step)} | ${src}`);
  }
};
// 1. a watch run 6:00/km, 170 spm, and the phone's copy with its own steps
const tRun = now - 2*24*H;
move(tRun, 30, 1/6, 170, "Watch"); move(tRun + 30e3, 30, 1/6.1, 168, "iPhone", 5);
// 2. a walk 12:00/km at 110 spm
const tWalk = now - 30*H; move(tWalk, 30, 1/12, 110, "iPhone");
// 3. a car at 54 km/h: distance with no steps - too fast for any slice
const tCar = now - 28*H; move(tCar, 20, 0.9, 0, "iPhone");
// 4. a bus at 21 km/h with a few shaken-out steps (stride ~ 70 m)
const tBus = now - 26*H; move(tBus, 20, 0.35, 5, "iPhone");
// 5. a 15-minute walk to the stop, then 20 min on the bus: the walk counts, the ride not
const tMix = now - 22*H; move(tMix, 15, 1/11, 115, "iPhone"); move(tMix + 15*M, 20, 0.33, 4, "iPhone");
// 6. a run whose phone wrote distance but whose steps are missing entirely
const tNo = now - 18*H; D.push(...Array.from({ length: 30 }, (_, m) => `${iso(tNo + m*M)} | ${iso(tNo + (m+1)*M)} | 0.17 | Nike Run Club`));
// 7. watch distance, phone steps (different sources): checked against the phone's
const tX = now - 14*H;
for (let m = 0; m < 25; m++){ D.push(`${iso(tX + m*M)} | ${iso(tX + (m+1)*M)} | 0.18 | Watch`); S.push(`${iso(tX + m*M)} | ${iso(tX + (m+1)*M)} | 172 | iPhone`); }

let r = await call("POST", "/health/import/" + key, { body: { samples: D.join("\n"), steps: S.join("\n") } });
console.log("reply:", JSON.stringify(r));
let sync = await call("POST", "/sync", { token: P });
const got = sync.health.map(h => ({ hAgo: Math.round((now - h.start)/H), km: +h.km.toFixed(2), min: Math.round(h.sec/60), walk: !!h.walk }));
console.log(got);
assert.deepEqual(got.map(g => g.hAgo), [48, 30, 22, 14], "run once, walk, the walk to the stop, the watch run with phone steps");
assert.ok(!got[0].walk && got[1].walk && got[2].walk && !got[3].walk);
assert.ok(Math.abs(got[2].km - 15/11) < 0.02, "only the walk part of walk-then-bus");
assert.equal(r.skipped.noSteps, 1, "no steps, no outing");
assert.ok(r.skipped.vehicleSlices >= 40, "car and bus slices dropped");
assert.match(r.message, /4 new/); assert.match(r.message, /car, bus or train/);
// 8. sending without steps at all says why
// (same run again with no steps: not counted, and the reply says to send steps)
const t9 = now - 6*H; const d9 = Array.from({ length: 20 }, (_, m) => `${iso(t9 + m*M)} | ${iso(t9 + (m+1)*M)} | 0.1 | iPhone`);
r = await call("POST", "/health/import/" + key, { body: { samples: d9.join("\n") } });
assert.equal(r.queued, 0); assert.match(r.message, /Step Count/);
// 9. re-sending: nothing new
r = await call("POST", "/health/import/" + key, { body: { samples: D.join("\n"), steps: S.join("\n") } });
assert.equal(r.queued, 0, JSON.stringify(r));
// 10. a walk sent half way, then finished: replaced while uncollected
D.length = 0; S.length = 0; const tLive = now - 60*M; move(tLive, 15, 1/12, 110, "iPhone");
r = await call("POST", "/health/import/" + key, { body: { samples: D.join("\n"), steps: S.join("\n") } }); assert.equal(r.queued, 1);
D.length = 0; S.length = 0; move(tLive, 40, 1/12, 110, "iPhone");
r = await call("POST", "/health/import/" + key, { body: { samples: D.join("\n"), steps: S.join("\n") } }); assert.equal(r.queued, 1);
sync = await call("POST", "/sync", { token: P });
const live = sync.health.filter(h => h.start === tLive);
assert.equal(live.length, 1); assert.equal(Math.round(live[0].sec/60), 40);
console.log("session checks passed");
