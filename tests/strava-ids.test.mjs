// Strava's 64-bit ids (from June 2027): athletes, runs and webhook events
// whose ids no JavaScript number holds exactly stay distinct, end to end.
//   node tests/strava-ids.test.mjs
import assert from "node:assert/strict";
import { makeHarness } from "./lib.mjs";
const { call, callback, strava, storageOf } = await makeHarness(null);
const H = 3600e3, iso = t => new Date(t).toISOString(), now = Date.now();

// Each pair is one apart and rounds to the same double, 2^63.
const A1 = 9223372036854775807n, A2 = 9223372036854775806n;
const R1 = 9223372036854770001n, R2 = 9223372036854770002n;
assert.equal(Number(A1), Number(A2), "the pair really does collide as numbers");
assert.equal(Number(R1), Number(R2));

// 1. two athletes, each sent with id_str as Strava now does, get two pets
const session = loc => decodeURIComponent(loc.split("#strava=")[1]);
const S1 = session(await callback({ id: A1, id_str: String(A1) }));
const S2 = session(await callback({ id: A2, id_str: String(A2) }));
assert.equal(S1.split(".")[0], String(A1), "session filed under the exact id");
assert.equal(S2.split(".")[0], String(A2));
assert.ok(storageOf(String(A1)) && storageOf(String(A2)), "one object each");
assert.equal(storageOf(String(A1)).get("athleteId"), String(A1));

// 2. two runs one id apart are two runs, carrying their exact ids
const run = (id, t) => ({ id, id_str: String(id), type:"Run", start_date: iso(t),
  distance: 5000, moving_time: 1500, elapsed_time: 1600 });
strava.acts = [run(R1, now - 30*H), run(R2, now - 3*H)];
let sync = await call("POST", "/sync", { token: S1 });
assert.deepEqual(sync.activities.map(a => a.id), [String(R1), String(R2)], JSON.stringify(sync.activities));

// 3. taking the first leaves the second still on offer
await call("PUT", "/save", { token: S1, body: { save: { species:"ember", petName:"Ash", runs:[] },
  imported: [String(R1)], card: null } });
sync = await call("POST", "/sync", { token: S1 });
assert.deepEqual(sync.activities.map(a => a.id), [String(R2)], "the neighbour is not mistaken for the run taken");

// 4. a reply without id_str still works for the ids issued so far
strava.acts = [{ id: 4242, type:"Run", start_date: iso(now - 2*H), distance: 3000, moving_time: 900, elapsed_time: 950 }];
sync = await call("POST", "/sync", { token: S1 });
assert.deepEqual(sync.activities.map(a => a.id), ["4242"]);

// 5. a webhook delete for R1, numbers bare in the body as Strava sends them,
//    reaches athlete A1 - not A2 - and removes R1 exactly
await call("PUT", "/save", { token: S2, body: { save: { species:"ember", petName:"Bo", runs:[] },
  imported: [String(R2)], card: null } });
const body = `{"aspect_type":"delete","event_time":${Math.floor(now/1000)},"object_id":${R1},` +
  `"object_type":"activity","owner_id":${A1},"subscription_id":1,"updates":{}}`;
await call("POST", "/strava/webhook", { body });
for (let i = 0; i < 50 && !storageOf(String(A1)).get("gone"); i++) await new Promise(r => setTimeout(r, 10));
const gone = storageOf(String(A1)).get("gone") || {};
assert.deepEqual(Object.keys(gone), [String(R1)], "the exact run is marked gone: " + JSON.stringify(gone));
assert.ok(!storageOf(String(A1)).get("importedAt")[String(R1)]);
assert.ok(!storageOf(String(A2)).get("gone"), "the other athlete is untouched");
assert.ok(storageOf(String(A2)).get("importedAt")[String(R2)]);

console.log("64-bit Strava ids: all checks passed");
