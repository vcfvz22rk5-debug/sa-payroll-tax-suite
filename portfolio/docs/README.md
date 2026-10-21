# The walkthrough

`portfolio-walkthrough.pdf` is a complete guide to the portfolio: what
each project is, the accounting behind it, how the code is put together,
the design system, how it is tested and hosted, the mistakes I made, and
twenty-two questions you might be asked — each with a model answer.

It is written to be read by somebody who is not me: to prepare for an
interview, to hand to a lecturer, or to give a client a sense of how the
work was done.

## Building it

The document is HTML, so it can be read in a browser as well as printed.

```bash
npm i -D playwright
npx playwright install chromium
node docs/build_pdf.mjs
```

That writes `docs/portfolio-walkthrough.pdf`. On a machine without the
browser libraries, `npx playwright install-deps chromium` will sort it.

The PDF is rendered by the same engine that draws the website, so the
typography and the diagrams match the site.

## What is in it

| Part | |
|---|---|
| 01 | The one-minute version — what to say when somebody asks what you built |
| 02 | What was built, and how the four projects relate |
| 03 | The accounting — the slabs, the annualised method, the rebates, the forms |
| 04 | How the code fits together, with the architecture and the schema |
| 05 | Twenty-two concepts: what they are, where they live, and one sentence each |
| 06 | The design system — colour, type, motion, accessibility |
| 07 | Testing — what is covered, what is not, and why the numbers are hand-worked |
| 08 | How it is hosted for free |
| 09 | The mistakes I made and how each was found |
| 10 | Twenty-two questions with model answers |
| 11 | The numbers — the inventory of everything |

The source is `docs/guide.html`. It is one long file with the styling
inline, so it can be printed without anything else.
