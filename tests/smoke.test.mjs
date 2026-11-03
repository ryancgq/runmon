import http from "node:http"; import fs from "node:fs"; import path from "node:path";
import { createRequire } from "node:module"; import { REPO } from "./lib.mjs"; const { chromium } = createRequire(import.meta.url)("playwright");
const server = http.createServer((q, r) => { const f = path.join(REPO, new URL(q.url,"http://x").pathname);
  if (!fs.existsSync(f) || fs.statSync(f).isDirectory()){ r.writeHead(404); return r.end(); }
  r.writeHead(200, {"Content-Type": f.endsWith(".html") ? "text/html" : "image/png"}); fs.createReadStream(f).pipe(r); }).listen(8768);
const b = await chromium.launch();
for (const u of ["/index.html?demo=1", "/index.html"]){
  const p = await b.newPage(); const errs = []; p.on("pageerror", e => errs.push(String(e)));
  await p.route(/workers\.dev|unpkg|cdnjs|jsdelivr|tile/, r => r.abort());
  await p.goto("http://localhost:8768" + u); await p.waitForTimeout(800);
  const vis = await p.evaluate(() => ({ healthHidden: document.querySelector("#health-panel").hidden, onboarding: document.querySelector("#onboard").classList.contains("show") }));
  console.log(u, JSON.stringify(vis), errs.length ? errs : "no errors");
}
await b.close(); server.close();
