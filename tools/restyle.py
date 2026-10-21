"""
tools/restyle.py - the design pass on the portfolio stylesheet.

The stylesheet is parsed into a tree first, so a change is applied to a
whole rule rather than to a fragment of text. Rules inside media queries
are found the same way. A rule that is edited wrongly can never leave
the file with unbalanced braces, and nothing is written unless every
check passes.

    python3 tools/restyle.py
"""
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSS = os.path.join(ROOT, "portfolio", "assets", "css", "styles.css")

LOG = []


# ── a small CSS parser ───────────────────────────────────────────────
class Node:
    """A rule, or a piece of raw text between rules."""

    def __init__(self, kind, before="", selector="", body="", after="", children=None):
        self.kind = kind              # "raw" | "rule" | "at"
        self.before = before
        self.selector = selector
        self.body = body
        self.after = after
        self.children = children or []

    def text(self):
        if self.kind == "raw":
            return self.before
        if self.kind == "gone":
            return ""
        if self.kind == "rule":
            return self.before + self.selector + self.body + self.after
        # an at-rule: the body holds the nested nodes
        inner = "".join(c.text() for c in self.children)
        return self.before + self.selector + self.body + inner + self.after


def _split_selector(raw):
    """
    Split the text before a '{' into (before, selector).

    A leading comment belongs to the "before" part, not the selector.
    """
    if "*/" in raw:
        idx = raw.rindex("*/") + 2
        before, rest = raw[:idx], raw[idx:]
    else:
        before, rest = "", raw
    stripped = rest.lstrip()
    gap = rest[: len(rest) - len(stripped)]
    before += gap
    selector = stripped.rstrip()
    trailing = stripped[len(selector):]
    return before, selector, trailing


def parse(text):
    """Parse a stylesheet into a list of nodes."""
    nodes = []
    i, n = 0, len(text)
    while i < n:
        j = text.find("{", i)
        if j == -1:
            nodes.append(Node("raw", before=text[i:]))
            break
        k = j
        depth = 0
        while k < n:
            if text[k] == "{":
                depth += 1
            elif text[k] == "}":
                depth -= 1
                if depth == 0:
                    break
            k += 1
        before, selector, trailing = _split_selector(text[i:j])
        body = text[j:k + 1]                 # the '{' ... '}'
        if selector.startswith("@") and "{" in body:
            # an at-rule: recurse into it
            inner_text = body[body.index("{") + 1: body.rindex("}")]
            children = parse(inner_text)
            node = Node("at", before=before, selector=selector,
                        body=body[:body.index("{") + 1], after="}", children=children)
        else:
            node = Node("rule", before=before, selector=selector + trailing,
                        body=body, after="")
        nodes.append(node)
        i = k + 1
    return nodes


def render(nodes):
    return "".join(n.text() for n in nodes)


def balance(text):
    d = 0
    for ch in text:
        if ch == "{":
            d += 1
        elif ch == "}":
            d -= 1
    return d


# ── the changes ──────────────────────────────────────────────────────
REPLACE = {}
DELETE = set()
TEXT_REPLACE = []


def block(body):
    return "{\n" + body.strip("\n") + "\n}"


def main():
    global TEXT_REPLACE
    src = io.open(CSS, encoding="utf-8").read()
    nodes = parse(src)

    # ── 1. the palette ───────────────────────────────────────────────
    REPLACE[":root"] = block('''
  --bg:          #0d0c0a;
  --bg-soft:     #131210;
  --bg-elev:     #1a1815;

  --surface:     rgba(242, 237, 227, 0.045);
  --surface-2:   rgba(242, 237, 227, 0.08);
  --surface-3:   rgba(242, 237, 227, 0.13);
  --border:      rgba(242, 237, 227, 0.10);
  --border-str:  rgba(242, 237, 227, 0.20);

  --text:        #f2ede3;
  --text-soft:   #cfc7b8;
  --muted:       #a89f8e;
  --faint:       #b0a695;

  --a1: #d4a94f;   /* brass      - the accent, like a printed figure */
  --a2: #8aa070;   /* olive      - money in */
  --a3: #c2705a;   /* terracotta - money out */
  --a4: #86a9b5;   /* slate      - information */
  --a5: #b08bb0;   /* plum       - a second series */

  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.4);
  --shadow:    0 14px 34px -18px rgba(0, 0, 0, 0.8);
  --shadow-lg: 0 34px 80px -28px rgba(0, 0, 0, 0.85);

  --r-sm: 8px;
  --r:    14px;
  --r-lg: 18px;

  /* A ledger, not a dashboard. */
  --ff-display: "IBM Plex Sans", "Segoe UI", system-ui, sans-serif;
  --ff-body:    "IBM Plex Sans", system-ui, -apple-system, "Segoe UI", sans-serif;
  --ff-mono:    "IBM Plex Mono", ui-monospace, "SF Mono", Menlo, monospace;

  --nav-h: 72px;
  --maxw: 1200px;

  /* Easing. Never ease-in on the way in: it reads as sluggish. */
  --ease:        cubic-bezier(0.23, 1, 0.32, 1);
  --ease-out:    cubic-bezier(0.23, 1, 0.32, 1);
  --ease-in-out: cubic-bezier(0.77, 0, 0.175, 1);
  --ease-linear: linear;

  /* Type scale. Nothing functional below 12.5px. */
  --fs-micro: 0.78rem;    /* 12.5px - the smallest functional text */
  --fs-small: 0.8125rem;  /* 13px   - secondary text */
  --fs-body:  1rem;       /* 16px   - body copy */
''')

    REPLACE['[data-theme="light"]'] = block('''
  --bg:      #f6f2e9;
  --bg-soft: #fffdf7;
  --bg-elev: #fffdf7;
  --surface:   rgba(27, 25, 23, 0.035);
  --surface-2: rgba(27, 25, 23, 0.06);
  --surface-3: rgba(27, 25, 23, 0.09);
  --border:    rgba(27, 25, 23, 0.12);
  --border-str: rgba(27, 25, 23, 0.22);
  --text:      #1b1917;
  --text-soft: #45403a;
  --muted:     #5e574d;
  --faint:     #6f675b;
  --a1: #8a6a1f;
  --a2: #4f6b3c;
  --a3: #a8452c;
  --a4: #3d6270;
  --a5: #6f4a7a;
  --shadow-sm: 0 1px 2px rgba(15, 23, 42, 0.07);
  --shadow:    0 14px 34px -18px rgba(15, 23, 42, 0.24);
  --shadow-lg: 0 34px 70px -26px rgba(15, 23, 42, 0.28);
''')

    # ── 2. gradient text becomes a solid colour ─────────────────────
    REPLACE[".grad-text"] = block("  color: var(--a1);")
    REPLACE[".grad-text--2"] = block("  color: var(--a2);")

    # ── 3. the accent as a fill ─────────────────────────────────────
    TEXT_REPLACE += [
        (r"background: var\(--grad-2\); -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent;",
         "color: var(--a2);"),
        (r"background: var\(--grad\); -webkit-background-clip: text; background-clip: text;",
         "color: var(--a1);"),
        (r"background: var\(--grad\); color: #06080f;", "background: var(--a1); color: #14120e;"),
        (r"color: #06080f; background: var\(--grad\);", "color: #14120e; background: var(--a1);"),
        (r"background: var\(--grad\); border-color: transparent;", "background: var(--a1); border-color: transparent;"),
        (r"height: 2px; border-radius: 2px; background: var\(--grad\);",
         "height: 2px; border-radius: 2px; background: var(--a1);"),
        (r"background: var\(--card-grad, var\(--grad\)\);", "background: var(--icon-bd, var(--border));"),
        (r"background: var\(--grad\);", "background: var(--a1);"),
        (r"\n\s*-webkit-text-fill-color: transparent;", ""),
        (r"\n\s*-webkit-background-clip: text; background-clip: text;", ""),
        (r"\n\s*color: transparent;", ""),
    ]

    # ── 4. the breakdown bars ───────────────────────────────────────
    TEXT_REPLACE += [
        (r"\.bar__seg--tax \{[^}]*\}", ".bar__seg--tax { background: var(--a3); }"),
        (r"\.bar__seg--uif \{[^}]*\}", ".bar__seg--uif { background: var(--a1); }"),
        (r"\.bar__seg--ra  \{[^}]*\}", ".bar__seg--ra  { background: var(--a5); }"),
        (r"\.bar__seg--net \{[^}]*\}", ".bar__seg--net { background: var(--a2); }"),
        (r"\.dot--tax \{[^}]*\}", ".dot--tax { background: var(--a3); }"),
        (r"\.dot--uif \{[^}]*\}", ".dot--uif { background: var(--a1); }"),
        (r"\.dot--ra \{[^}]*\}", ".dot--ra { background: var(--a5); }"),
        (r"\.dot--net \{[^}]*\}", ".dot--net { background: var(--a2); }"),
        (r"\.bar__seg--out \{[^}]*\}", ".bar__seg--out { background: var(--a4); }"),
        (r"\.bar__seg--in  \{[^}]*\}", ".bar__seg--in  { background: var(--a1); }"),
        (r"\.dot--out \{[^}]*\}", ".dot--out { background: var(--a4); }"),
        (r"\.dot--in \{[^}]*\}", ".dot--in { background: var(--a1); }"),
    ]

    # ── 5. the terminal ──────────────────────────────────────────────
    TEXT_REPLACE += [
        (r"\.term__body \.t-dim   \{[^}]*\}", ".term__body .t-dim   { color: #7d7466; }"),
        (r"\.term__body \.t-key   \{[^}]*\}", ".term__body .t-key   { color: var(--a1); }"),
        (r"\.term__body \.t-val   \{[^}]*\}", ".term__body .t-val   { color: var(--text); }"),
        (r"\.term__body \.t-green \{[^}]*\}", ".term__body .t-green { color: var(--a2); }"),
        (r"\.term__body \.t-amber \{[^}]*\}", ".term__body .t-amber { color: var(--a1); }"),
        (r"\.term__body \.t-pink  \{[^}]*\}", ".term__body .t-pink  { color: var(--a3); }"),
        (r"color: #b6c2da; overflow-x: auto;", "color: var(--text-soft); overflow-x: auto;"),
        (r"font-family: var\(--ff-mono\); font-size: 0\.72rem; color: #7c8aa8;",
         "font-family: var(--ff-mono); font-size: var(--fs-micro); color: var(--faint);"),
        (r"background: linear-gradient\(180deg, rgba\(12,17,32,\.94\), rgba\(7,10,20,\.96\)\);",
         "background: linear-gradient(180deg, #16140f, #0f0e0a);"),
    ]

    # ── 6. the type scale ───────────────────────────────────────────
    for old, new in [("0.63rem", "0.78rem"), ("0.64rem", "0.78rem"), ("0.66rem", "0.78rem"),
                     ("0.68rem", "0.78rem"), ("0.7rem", "0.78rem"), ("0.72rem", "var(--fs-micro)"),
                     ("0.735rem", "0.78rem"), ("0.74rem", "0.78rem"), ("0.76rem", "0.8125rem"),
                     ("0.78rem", "0.8125rem"), ("0.8rem", "0.8125rem"), ("0.82rem", "0.875rem"),
                     ("0.83rem", "0.875rem"), ("0.85rem", "0.875rem"), ("0.87rem", "0.9375rem"),
                     ("0.9rem", "0.9375rem"), ("0.93rem", "0.9375rem"), ("0.86rem", "0.875rem"),
                     ("0.95rem", "0.9375rem"), ("0.84rem", "0.875rem")]:
        TEXT_REPLACE.append((rf"font-size: {re.escape(old)};", f"font-size: {new};"))

    # ── 7. never `transition: all` ──────────────────────────────────
    TEXT_REPLACE.append((
        r"transition: all \.25s var\(--ease\);",
        "transition: color .18s var(--ease), background-color .18s var(--ease), "
        "border-color .18s var(--ease), transform .18s var(--ease);"))

    # ── 8. a ledger is flat: no frosted glass ──────────────────────
    TEXT_REPLACE += [
        (r"\n\s*backdrop-filter: blur\([^;]*\);", ""),
        (r"\n\s*-webkit-backdrop-filter: blur\([^;]*\);", ""),
        (r"background: color-mix\(in srgb, var\(--bg-elev\) 94%, transparent\);", "background: var(--bg-elev);"),
        (r"background: color-mix\(in srgb, var\(--bg\) 90%, transparent\);", "background: var(--bg);"),
    ]
    REPLACE[".glass"] = block('''
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--r-lg);
  position: relative;
  overflow: hidden;
''')

    # ── 9. one elevation, not two ───────────────────────────────────
    REPLACE[".card"] = block('''
  position: relative; padding: 26px;
  display: flex; flex-direction: column; gap: 15px;
  border-radius: var(--r-lg);
  border: 1px solid var(--border);
  background: linear-gradient(180deg, rgba(242,237,227,.05), rgba(242,237,227,.016));
  overflow: hidden;
  transition: transform .3s var(--ease), border-color .3s var(--ease), background-color .3s var(--ease);
''')
    REPLACE[".card::after"] = block('''
  content: ""; position: absolute; inset: 0; border-radius: inherit;
  padding: 1px; pointer-events: none;
  background: var(--icon-bd, var(--border));
  -webkit-mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0);
  -webkit-mask-composite: xor; mask-composite: exclude;
  opacity: 0; transition: opacity .3s var(--ease);
''')
    TEXT_REPLACE.append((r"\.card:hover \{[^}]*\}",
                         ".card:hover { transform: translateY(-3px); border-color: var(--border-str); }"))

    # ── 10. the cover figures become a ledger strip ─────────────────
    DELETE.add(".cover__stats")
    DELETE.add(".cover__stats div")
    DELETE.add(".cover__stats dt")
    DELETE.add(".cover__stats dd")
    DELETE.add(".cover__stats dd small")
    DELETE.add(".cover__stats div:last-child")
    REPLACE[".ledger-strip"] = block('''
  display: grid; grid-template-columns: repeat(3, minmax(0, 1fr));
  margin-top: 38px;
  border: 1px solid var(--border);
  border-radius: var(--r);
  background: var(--surface);
  overflow: hidden;
''')
    REPLACE[".ledger-strip > div"] = block(
        "  padding: 16px 18px; border-right: 1px solid var(--border); min-width: 0; ")
    REPLACE[".ledger-strip > div:last-child"] = block("  border-right: none; ")
    REPLACE[".ledger-strip dt"] = block('''
  font-family: var(--ff-mono); font-size: var(--fs-micro);
  letter-spacing: .1em; text-transform: uppercase; color: var(--faint);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
''')
    REPLACE[".ledger-strip dd"] = block('''
  font-family: var(--ff-mono); font-size: 1.3rem; font-weight: 600;
  color: var(--a1); margin-top: 4px;
  font-variant-numeric: tabular-nums;
''')
    REPLACE[".ledger-strip dd small"] = block(
        "  font-size: .55em; color: var(--muted); margin-left: 2px; ")

    # ── 11. tabular numbers ─────────────────────────────────────────
    REPLACE[".calc__rows dd"] = block('''
  font-family: var(--ff-mono); font-size: 0.9375rem; font-weight: 500;
  font-variant-numeric: tabular-nums;
''')
    REPLACE[".ledger td.num"] = block('''
  font-family: var(--ff-mono); font-size: 0.875rem;
  font-variant-numeric: tabular-nums;
''')
    REPLACE[".status__item b"] = block('''
  color: var(--text-soft); font-weight: 500;
  font-variant-numeric: tabular-nums;
''')

    # ── 12. the table floats on the panel ───────────────────────────
    REPLACE[".payroll__table-wrap"] = block("  overflow-x: auto; border-radius: var(--r); ")

    # ── 13. the command palette opens on a keystroke: no animation ──
    REPLACE[".palette__backdrop"] = block(
        "  position: absolute; inset: 0; background: rgba(8,7,6,.7); backdrop-filter: blur(6px); ")
    TEXT_REPLACE.append((r"\n\s*animation: paletteIn \.28s var\(--ease\);", ""))

    # ── 14. the sheet change is the one authored moment ────────────
    TEXT_REPLACE.append((
        r"\.sheet\.is-active \{ animation: sheetIn \.32s var\(--ease-out\); \}",
        ".sheet.is-active { animation: sheetIn .16s var(--ease-out); }"))
    TEXT_REPLACE.append((r"@keyframes sheetIn \{[^}]*\}",
                         "@keyframes sheetIn { from { opacity: 0; } }"))

    # ── 15. the cell selection is instant, and the chrome says so ──
    REPLACE["[data-formula].is-selected"] = block('''
  background: var(--surface-2);
  box-shadow: inset 0 0 0 1px var(--a1);
''')
    REPLACE[".bar.is-inspecting .bar__formula"] = block("  border-color: var(--a1); ")
    REPLACE[".bar.is-inspecting .bar__name-box"] = block("  color: var(--a1); border-color: var(--a1); ")

    # ── 16. the scrollbar and the caret belong to the palette ──────
    REPLACE["::-webkit-scrollbar"] = block("  width: 12px; height: 12px; ")
    REPLACE["::-webkit-scrollbar-track"] = block("  background: var(--bg-soft); ")
    REPLACE["::-webkit-scrollbar-thumb"] = block('''
  background: var(--border-str);
  border-radius: 99px;
  border: 3px solid var(--bg-soft);
''')
    REPLACE["::selection"] = block("  background: var(--a1); color: #14120e; ")
    REPLACE["input, textarea, select"] = block("  caret-color: var(--a1); ")

    # ── 17. the print sheet ─────────────────────────────────────────
    TEXT_REPLACE.append((r"body \{ background: #fff; color: #000; \}",
                         "body { background: #fff !important; color: #000 !important; }"))
    TEXT_REPLACE.append((r"\.fx, \.nav, \.palette, \.scroll-cue, \.marquee, \.hero__glow \{[^}]*\}",
                         ".fx, .palette, .toast { display: none !important; }"))

    # ── 18. the things that are gone ────────────────────────────────
    for selector in [".fx__noise", ".fx__cursor", ".fx__cursor.is-on",
                     '[data-theme="light"] .fx__cursor', ".hero__glow",
                     ".contact__card-glow", ".blob", ".blob--1", ".blob--2",
                     ".blob--3", ".blob--4"]:
        DELETE.add(selector)
    for kf in ["@keyframes drift1", "@keyframes drift2", "@keyframes drift3",
               "@keyframes drift4", "@keyframes paletteIn", "@keyframes fadeIn",
               "@keyframes pulse"]:
        DELETE.add(kf)
    REPLACE[".pill__dot"] = block(
        "  width: 7px; height: 7px; border-radius: 50%; background: var(--a2); ")
    TEXT_REPLACE.append((r"\.pulse \{[^}]*\}",
                         ".pulse { width: 8px; height: 8px; border-radius: 50%; background: var(--a2); flex: none; }"))
    TEXT_REPLACE.append((r"\.fx__aurora, \.fx__cursor \{ display: none; \}",
                         ".fx { display: none; }"))

    # ═══════════════════════════════════════════════════════════════
    def walk(nodes):
        for node in nodes:
            if node.kind == "rule":
                key = node.selector.strip()
                if key in DELETE:
                    LOG.append(f"  removed  {key}")
                    node.kind = "gone"
                    continue
                if key in REPLACE:
                    LOG.append(f"  replaced {key}")
                    node.body = REPLACE[key]
                    continue
                # the patterns are written against the whole rule, so the
                # selector is part of the text being matched
                full = node.selector + node.body
                for pattern, repl in TEXT_REPLACE:
                    full = re.sub(pattern, repl, full)
                if full != node.selector + node.body:
                    # split it back up
                    brace = full.index("{")
                    node.selector = full[:brace]
                    node.body = full[brace:]
                if node.body.strip() in ("{}", "{ }"):
                    node.kind = "gone"
            elif node.kind == "at":
                key = node.selector.strip()
                if key in DELETE:
                    LOG.append(f"  removed  {key}")
                    node.kind = "gone"
                    continue
                walk(node.children)
                full = node.selector + node.body
                for pattern, repl in TEXT_REPLACE:
                    full = re.sub(pattern, repl, full)
                if full != node.selector + node.body:
                    brace = full.index("{")
                    node.selector = full[:brace]
                    node.body = full[brace:]
        return nodes

    walk(nodes)
    result = render(nodes)
    d = balance(result)
    print("\n".join(LOG))
    print(f"\nbrace balance {d}")
    if d != 0:
        print("ABORTED: the stylesheet would be unbalanced")
        return 1

    io.open(CSS, "w", encoding="utf-8").write(result)
    print("written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
