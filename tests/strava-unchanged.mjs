// Is a Strava player's game exactly what it was before a change?
//
// Runs strava-scenario.mjs three times and compares what each run saw and
// stored, timestamps aside:
//   1. the BASELINE app on the baseline broker - how it used to be
//   2. this checkout's app on this checkout's broker - how it will be
//   3. the baseline app on this checkout's broker - the minutes between
//      deploying the broker and pushing the app, when players have the old
//      app talking to the new broker
// The baseline is a git ref, checked out into a temporary worktree; it
// defaults to 0b59689, the last build before Apple Health.
//
//   node tests/strava-unchanged.mjs [baseline-ref]
//
// What a brand-new visitor sees is left out of the comparison: onboarding
// for new players is allowed to change. Everything about a player already
// on Strava is not.
import { spawnSync, execFileSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { REPO, OUT } from "./lib.mjs";

const ref = process.argv[2] || "0b59689";
const base = path.join(OUT, "baseline-" + ref.replace(/[^\w.-]/g, "_"));
if (!fs.existsSync(base)){
  execFileSync("git", ["-C", REPO, "worktree", "add", "-f", "--detach", base, ref], { stdio: "inherit" });
}
const scenario = path.join(REPO, "tests", "strava-scenario.mjs");
const run = (app, worker, port, out) => {
  const r = spawnSync(process.execPath, [scenario, app, worker, String(port), out], { stdio: "inherit" });
  if (r.status !== 0) throw new Error("scenario failed: " + [app, worker].join(" "));
  return JSON.parse(fs.readFileSync(out, "utf8"));
};
const norm = x => Array.isArray(x) ? x.map(norm)
  : x && typeof x === "object" ? Object.fromEntries(Object.entries(x)
      .filter(([k]) => k !== "newVisitor").map(([k, v]) => [k, k === "t" ? "T" : norm(v)]))
  : x;
try {
  const was  = norm(run(base, path.join(base, "worker/src/index.js"), 8851, path.join(OUT, "strava-baseline.json")));
  const now  = norm(run(REPO, path.join(REPO, "worker/src/index.js"), 8852, path.join(OUT, "strava-current.json")));
  const gap  = norm(run(base, path.join(REPO, "worker/src/index.js"), 8853, path.join(OUT, "strava-gap.json")));
  const same = (a, b) => JSON.stringify(a) === JSON.stringify(b);
  console.log(`this app on this broker vs ${ref}: ${same(was, now) ? "identical" : "DIFFERENT"}`);
  console.log(`${ref}'s app on this broker vs ${ref}: ${same(was, gap) ? "identical" : "DIFFERENT"}`);
  if (!same(was, now) || !same(was, gap)){
    console.log("Compare the JSON files in " + OUT);
    process.exit(1);
  }
} finally {
  execFileSync("git", ["-C", REPO, "worktree", "remove", "--force", base]);
}
