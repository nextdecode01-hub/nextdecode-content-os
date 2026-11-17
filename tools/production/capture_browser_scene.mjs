#!/usr/bin/env node
/** Optional Playwright UI capture. Usage: node tools/production/capture_browser_scene.mjs <url> <output.png> */
import { resolve } from "node:path";
const [url, output] = process.argv.slice(2);
if (!url || !output || !/^https?:\/\//i.test(url)) {
  console.error("Usage: node tools/production/capture_browser_scene.mjs https://example.com output.png");
  process.exit(2);
}
let chromium;
try { ({ chromium } = await import("playwright")); }
catch {
  console.error("Playwright missing. After owner approval: npm install -D playwright && npx playwright install chromium");
  process.exit(3);
}
const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  await page.goto(url, { waitUntil: "networkidle", timeout: 30000 });
  await page.screenshot({ path: resolve(output), fullPage: false, animations: "disabled" });
  console.log(JSON.stringify({ url, output: resolve(output), viewport: "1080x1920", capturedAt: new Date().toISOString() }));
} finally { await browser.close(); }
