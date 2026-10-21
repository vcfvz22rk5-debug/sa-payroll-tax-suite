"""
docs/build_pdf.py - render the walkthrough to a PDF.

The document is written as HTML so it can be read in a browser, and
rendered with headless Chromium, which is the same engine that draws
the site. Fonts are embedded in the PDF.

    python3 docs/build_pdf.py

Needs Playwright with Chromium:
    pip install playwright && playwright install chromium
"""

import asyncio
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(HERE, "guide.html")
OUTPUT = os.path.join(HERE, "portfolio-walkthrough.pdf")

FOOTER = """
<div style="width:100%;font-size:8px;color:#8c8373;font-family:'IBM Plex Mono',monospace;
            padding:0 15mm;display:flex;justify-content:space-between;">
  <span>Ayanda Shongwe &middot; Payroll Portfolio &middot; A Complete Walkthrough</span>
  <span><span class="pageNumber"></span> / <span class="totalPages"></span></span>
</div>
"""

HEADER = """
<div style="width:100%;font-size:8px;color:#a89f8e;font-family:'IBM Plex Mono',monospace;
            padding:8mm 15mm 0;display:flex;justify-content:space-between;">
  <span>Payroll Portfolio</span>
  <span>A Complete Walkthrough</span>
</div>
"""


async def build():
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("Playwright is not installed.\n"
              "  pip install playwright && playwright install chromium",
              file=sys.stderr)
        return 1

    if not os.path.exists(SOURCE):
        print(f"Missing {SOURCE}", file=sys.stderr)
        return 1

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(f"file://{SOURCE}", wait_until="networkidle")
        # Let the webfonts settle, or the PDF falls back to Times.
        await page.evaluate("document.fonts.ready")
        await page.wait_for_timeout(1200)

        await page.pdf(
            path=OUTPUT,
            format="A4",
            print_background=True,
            display_header_footer=True,
            header_template=HEADER,
            footer_template=FOOTER,
            margin={"top": "0", "bottom": "0", "left": "0", "right": "0"},
        )
        await browser.close()

    size = os.path.getsize(OUTPUT) / 1024
    print(f"wrote {OUTPUT}  ({size:.0f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(build()))
