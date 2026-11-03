// Every test, one after another. Stops at the first failure.
//   node tests/run-all.mjs
import { spawnSync } from "node:child_process";
import path from "node:path";
import { REPO, OUT } from "./lib.mjs";

const tests = [
  "broker.test.mjs",          // the broker's Health routes, adopt, swings, unlink
  "health-sessions.test.mjs", // runs and walks rebuilt from distance; vehicles
  "health-app.test.mjs",      // the app end to end against the real broker
  "health-guide.test.mjs",    // the setup guide, its reminders and success
  "health-walks.test.mjs",    // walks: half XP, no mood or streak
  "recovery.test.mjs",        // recovery codes across two browsers
  "onboarding.test.mjs",      // Strava full: new and returning players
  "smoke.test.mjs",           // the app and the sandbox load cleanly
  "strava-unchanged.mjs"      // a Strava player's game is exactly as before
];
for (const t of tests){
  console.log(`\n=== ${t}`);
  const r = spawnSync(process.execPath, [path.join(REPO, "tests", t)], { stdio: "inherit" });
  if (r.status !== 0){ console.log(`\nFAILED: ${t}`); process.exit(1); }
}
console.log(`\nAll ${tests.length} passed. Screenshots and JSON are in ${OUT}`);
