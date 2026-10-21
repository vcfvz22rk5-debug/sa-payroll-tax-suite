/**
 * docs/build_pdf.mjs - render the walkthrough to a PDF.
 *
 * The document is written as HTML so it can be read in a browser, and
 * rendered with headless Chromium - the same engine that draws the
 * site. The fonts are embedded in the PDF.
 *
 *     npm i -D playwright && npx playwright install chromium
 *     node portfolio/docs/build_pdf.mjs
 *
 * On a machine without the browser libraries:
 *     npx playwright install-deps chromium
 */
import { chromium } from "playwright";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { statSync } from "node:fs";

const HERE = dirname(fileURLToPath(import.meta.url));
const SOURCE = join(HERE, "guide.html");
const OUTPUT = join(HERE, "portfolio-walkthrough.pdf");

const FOOTER = `
<div style="width:100%;font-size:8px;color:#8c8373;font-family:'IBM Plex Mono',monospace;
            padding:0 15mm;display:flex;justify-content:space-between;">
  <span>Ayanda Shongwe &middot; Payroll Portfolio &middot; A Complete Walkthrough</span>
  <span><span class="pageNumber"></span> / <span class="totalPages"></span></span>
</div>`;

const HEADER = `
<div style="width:100%;font-size:8px;color:#a89f8e;font-family:'IBM Plex Mono',monospace;
            padding:8mm 15mm 0;display:flex;justify-content:space-between;">
  <span>Payroll Portfolio</span>
  <span>A Complete Walkthrough</span>
</div>`;

const browser = await chromium.launch();
const page = await browser.newPage();
await page.goto(`file://${SOURCE}`, { waitUntil: "networkidle" });
// Let the webfonts settle, or the PDF falls back to Times.
await page.evaluate(() => document.fonts.ready);
await page.waitForTimeout(1500);

await page.pdf({
  path: OUTPUT,
  format: "A4",
  printBackground: true,
  displayHeaderFooter: true,
  headerTemplate: HEADER,
  footerTemplate: FOOTER,
  margin: { top: "0", bottom: "0", left: "0", right: "0" },
});

await browser.close();

const kb = (statSync(OUTPUT).size / 1024).toFixed(0);
console.log(`wrote ${OUTPUT}  (${kb} KB)`);
