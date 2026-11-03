import assert from "node:assert/strict";
import { makeHarness, REPO, OUT } from "./lib.mjs";
const { call, callback, strava, storageOf } = await makeHarness(null);
const H = 3600e3, iso = t => new Date(t).toISOString();
const imp = (key, workouts) => call("POST", "/health/import/" + key, { body: { workouts } });

// 1. Health-only player
const link = await call("POST", "/health/link");
assert.equal(link.status, 200, JSON.stringify(link));
const P = link.session, key = link.key;
assert.ok(P.startsWith("p")); assert.match(key, /^[a-z0-9]{24}$/);
assert.equal((await call("POST", "/health/link", { token: P })).key, key, "same key on relink");
// pretend the link was made ten days ago, so the test can use past workouts
const now = Date.now();
storageOf(P.split(".")[0]).set("healthSince", now - 10*24*H);

// 2. a watch run + a second app's overlapping copy + an exact repeat → one taken
const watch = { start: iso(now - 4*24*H), end: iso(now - 4*24*H + 30*60e3), distance: "5.01 km", type: "Running" };
const copy  = { start: iso(now - 4*24*H + 30e3), end: iso(now - 4*24*H + 29*60e3), distance: "4.9 km", type: "Running" };
let put = await imp(key, [copy, watch, watch]);
assert.equal(put.queued, 1, JSON.stringify(put)); assert.equal(put.already, 2);
// the earlier-starting copy was kept
let sync = await call("POST", "/sync", { token: P });
assert.equal(sync.health.length, 1); assert.equal(sync.health[0].start, now - 4*24*H);
assert.equal(sync.error, undefined, "no reauth for a Health-only player"); assert.equal(sync.strava, false);
assert.ok(sync.healthInfo.since);

// 3. old, pre-link, walking, junk
put = await imp(key, [
  { start: iso(now - 6*24*H), end: iso(now - 6*24*H + H), distance: 10, type: "Running" },
  { start: iso(now - 11*24*H), end: iso(now - 11*24*H + H), distance: 10, type: "Running" },
  { start: iso(now - 3*H), end: iso(now - 2*H), distance: "3 mi", type: "Walking" },
  { start: iso(now - 7*H), end: iso(now - 6*H), distance: "20 km", type: "Cycling" },
  { start: "yesterday", end: "today", distance: 5 },
  { start: iso(now - 9*H), end: iso(now - 9*H + 60e3), distance: "5 km" },
  { start: iso(now + 5*H), end: iso(now + 5.5*H), distance: "5 km" },
]);
assert.equal(put.queued, 1, "the walk is taken now - as a walk");
assert.equal(put.tooOld, 1, "six days old is past the five-day horizon");
assert.equal(put.beforeLink, 1);
assert.deepEqual(put.skipped, { notRun:1, badDate:2, tooFast:1 });

// 4. swings: Health-only players earn them from Health. 5.01 km = 1 swing.
let swings = await call("GET", "/explore/me", { token: P }); // needs a pet; check the bank directly instead
let st = storageOf(P.split(".")[0]);
assert.equal(st.get("raidBank").earned, 1, JSON.stringify(st.get("raidBank")));
// re-sending the same run buys nothing
await imp(key, [watch]); assert.equal(storageOf(P.split(".")[0]).get("raidBank").earned, 1);

// 5. commit with healthDone drains the queue, and never touches Strava's id map
sync = await call("POST", "/sync", { token: P });
assert.equal(sync.health.filter(h => h.walk).length, 1, "the walk is queued as a walk");
await call("PUT", "/save", { token: P, body: { save: { species:"ember", petName:"Ash", runs:[] }, imported: [], healthDone: sync.health.map(h => h.key), card: null } });
sync = await call("POST", "/sync", { token: P });
assert.equal(sync.health.length, 0);
st = storageOf(P.split(".")[0]);
assert.ok(!st.get("importedAt") || !Object.keys(st.get("importedAt")).some(k => k.startsWith("h:")), "no Health key in importedAt");
assert.ok(!(Number(st.get("floor")) > 0), "Strava floor untouched");

// 6. text format, comma decimals, miles
const tB = now - 2*24*H;
put = await call("POST", "/health/import/" + key, { body: { text:
  `${iso(tB)} | ${iso(tB + 20*60e3)} | 3,1 km | Running\n${iso(tB + 3*H)};${iso(tB + 3*H + 40*60e3)};4.2 mi;HKWorkoutActivityTypeRunning` } });
assert.equal(put.queued, 2, JSON.stringify(put));
sync = await call("POST", "/sync", { token: P });
assert.ok(Math.abs(sync.health[1].km - 4.2 * 1.609344) < 1e-9);
assert.equal((await call("POST", "/health/import/nope")).status, 404);

// 7. friend code, then the player connects Strava: adopt
const code = (await call("GET", "/friends/me", { token: P })).code;
assert.ok(code);
const loc = await callback(777);
const S = decodeURIComponent(/strava=([^&]+)/.exec(loc)[1]);
const ad = await call("POST", "/health/adopt", { token: S, body: { from: P } });
assert.equal(ad.adopted, true, JSON.stringify(ad));
sync = await call("POST", "/sync", { token: S });
assert.equal(sync.health.length, 2, "queued runs followed"); assert.ok(sync.healthInfo);
assert.equal((await call("GET", "/friends/me", { token: S })).code, code, "friend code followed");
console.log("bank after adopt", JSON.stringify(storageOf("777").get("raidBank")), JSON.stringify(storageOf("777").get("healthKmAfter")));
assert.equal(storageOf("777").get("raidBank").earned, 3, "unspent swings followed (17.28 km, the walk at half)"); assert.ok(Math.abs(storageOf("777").get("raidBank").part - 2.28) < 0.02, JSON.stringify(storageOf("777").get("raidBank")));
// the same key now feeds the athlete, and remembers what was taken
put = await imp(key, [watch]); assert.equal(put.already, 1, JSON.stringify(put));
// the player object is gone
assert.equal((await call("POST", "/sync", { token: P })).health.length, 0);
assert.equal(storageOf(P.split(".")[0]).size, 0, "player object erased");
// a Strava athlete earns no swings from Health
const tC = now - 12*H;
await imp(key, [{ start: iso(tC), end: iso(tC + H), distance: 12, type: "Running" }]);
assert.equal(storageOf("777").get("raidBank").earned, 3, "no Health swings once on Strava");

// 8. Strava activities carry elapsed time; Health rides along
strava.acts = [{ id: 1, type:"Run", start_date: iso(now - 6*H), distance: 5000, moving_time: 1500, elapsed_time: 1700 }];
sync = await call("POST", "/sync", { token: S });
assert.equal(sync.activities.length, 1); assert.equal(sync.activities[0].elapsed, 1700);
assert.equal(sync.health.length, 3);

// 9. unlink kills the key; relink gives a new one; disconnect kills that too
assert.equal((await call("POST", "/health/unlink", { token: S })).unlinked, true);
assert.equal((await imp(key, [watch])).status, 404);
assert.equal((await call("POST", "/sync", { token: S })).healthInfo, null);
const l3 = await call("POST", "/health/link", { token: S });
assert.notEqual(l3.key, key);
const dis = await call("POST", "/disconnect", { token: S });
assert.equal(dis.disconnected, true, JSON.stringify(dis));
assert.equal((await imp(l3.key, [watch])).status, 404, "disconnect retires the link");
assert.equal((await call("POST", "/health/link", { token: S })).status, 409, "a parked athlete cannot link");

console.log("all worker checks passed");
