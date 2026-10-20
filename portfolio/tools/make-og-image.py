#!/usr/bin/env python3
"""
make-og-image.py - generate the social preview image (og-image.png).

Social platforms (LinkedIn, X, WhatsApp) show this image when someone
shares a link to the portfolio. It is worth having, because without it a
shared link renders as a plain grey box.

This script draws the preview from scratch using only the standard
library - it renders the "AS" monogram as anti-aliased gradient strokes
over an aurora background, then writes a PNG.

Run it again whenever you change the monogram or the colours:

    python3 tools/make-og-image.py
"""

import math
import os
import struct
import zlib

W, H = 1200, 630
OUT = os.path.join(os.path.dirname(__file__), "..", "assets", "img", "og-image.png")

# --- the palette, matching assets/css/styles.css -------------------
BG_TOP = (5, 7, 13)
BG_BOTTOM = (12, 17, 32)
CYAN = (103, 232, 249)
VIOLET = (167, 139, 250)
PINK = (244, 114, 182)
GRID = (255, 255, 255)


# ── tiny raster canvas ─────────────────────────────────────────────
class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = [[float(bg[0]), float(bg[1]), float(bg[2])] for _ in range(w * h)]

    def set(self, x, y, rgb, a=1.0):
        if x < 0 or y < 0 or x >= self.w or y >= self.h or a <= 0:
            return
        p = self.px[y * self.w + x]
        p[0] += (rgb[0] - p[0]) * a
        p[1] += (rgb[1] - p[1]) * a
        p[2] += (rgb[2] - p[2]) * a

    def add(self, x, y, rgb, a=1.0):
        """Additive blend - used for the glows."""
        if x < 0 or y < 0 or x >= self.w or y >= self.h or a <= 0:
            return
        p = self.px[y * self.w + x]
        p[0] += rgb[0] * a
        p[1] += rgb[1] * a
        p[2] += rgb[2] * a

    def to_png(self, path):
        rows = bytearray()
        for y in range(self.h):
            rows.append(0)  # filter type 0
            for x in range(self.w):
                p = self.px[y * self.w + x]
                rows += bytes(
                    (
                        max(0, min(255, int(p[0] + 0.5))),
                        max(0, min(255, int(p[1] + 0.5))),
                        max(0, min(255, int(p[2] + 0.5))),
                    )
                )

        def chunk(tag, data):
            return (
                struct.pack(">I", len(data))
                + tag
                + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
            )

        png = b"\x89PNG\r\n\x1a\n"
        png += chunk(b"IHDR", struct.pack(">IIBBBBB", self.w, self.h, 8, 2, 0, 0, 0))
        png += chunk(b"IDAT", zlib.compress(bytes(rows), 9))
        png += chunk(b"IEND", b"")
        with open(path, "wb") as f:
            f.write(png)


# ── geometry helpers ───────────────────────────────────────────────
def lerp(a, b, t):
    return a + (b - a) * t


def mix(c1, c2, t):
    return tuple(lerp(c1[i], c2[i], t) for i in range(3))


def dist_to_segment(px, py, x1, y1, x2, y2):
    dx, dy = x2 - x1, y2 - y1
    if dx == 0 and dy == 0:
        return math.hypot(px - x1, py - y1)
    t = ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))
    return math.hypot(px - (x1 + t * dx), py - (y1 + t * dy))


def flatten_cubic(p0, p1, p2, p3, steps=18):
    pts = []
    for i in range(1, steps + 1):
        t = i / steps
        u = 1 - t
        x = u**3 * p0[0] + 3 * u**2 * t * p1[0] + 3 * u * t**2 * p2[0] + t**3 * p3[0]
        y = u**3 * p0[1] + 3 * u**2 * t * p1[1] + 3 * u * t**2 * p2[1] + t**3 * p3[1]
        pts.append((x, y))
    return pts


# ── the "AS" monogram, in a 64x64 space ────────────────────────────
# The same letterforms as assets/img/favicon.svg and the nav brand mark.
def monogram_paths():
    # A - two legs with a flat top, plus a crossbar
    a_leg = [(14, 45), (25, 19), (27.4, 19), (38, 45)]
    a_bar = [(18, 37), (34, 37)]

    # S - a proper S: top bowl, diagonal spine, bottom bowl.
    # (The old path stopped halfway down and read as a "P".)
    x0, y0, bw, bh = 46, 19, 15, 26

    def P(u, v):
        return (x0 + u * bw, y0 + v * bh)

    s = [P(0.95, 0.18)]
    s += flatten_cubic(P(0.95, 0.18), P(0.95, 0.02), P(0.05, 0.02), P(0.05, 0.22))
    s += flatten_cubic(P(0.05, 0.22), P(0.05, 0.42), P(0.95, 0.58), P(0.95, 0.78))
    s += flatten_cubic(P(0.95, 0.78), P(0.95, 0.98), P(0.05, 0.98), P(0.05, 0.82))

    return [a_leg, a_bar, s]


def draw_polyline(canvas, pts, scale, ox, oy, width, color_at):
    """Anti-aliased thick stroke along a polyline."""
    segs = list(zip(pts, pts[1:]))
    if not segs:
        return
    xs = [p[0] * scale + ox for p in pts]
    ys = [p[1] * scale + oy for p in pts]
    half = width / 2.0
    min_x = int(max(0, min(xs) - half - 2))
    max_x = int(min(canvas.w - 1, max(xs) + half + 2))
    min_y = int(max(0, min(ys) - half - 2))
    max_y = int(min(canvas.h - 1, max(ys) + half + 2))

    for py in range(min_y, max_y + 1):
        for px in range(min_x, max_x + 1):
            d = min(dist_to_segment(px + 0.5, py + 0.5, *a, *b) for a, b in segs)
            cov = half - d + 0.5
            if cov <= 0:
                continue
            cov = min(1.0, cov)
            canvas.set(px, py, color_at(px), cov)


# ── build the image ────────────────────────────────────────────────
def build():
    c = Canvas(W, H, BG_TOP)

    # 1. vertical background gradient
    for y in range(H):
        t = y / (H - 1)
        c1 = mix(BG_TOP, BG_BOTTOM, t)
        for x in range(W):
            c.px[y * W + x] = [c1[0], c1[1], c1[2]]

    # 2. faint grid
    for x in range(0, W, 60):
        for y in range(H):
            c.add(x, y, GRID, 0.030)
    for y in range(0, H, 60):
        for x in range(W):
            c.add(x, y, GRID, 0.030)

    # 3. aurora glows
    for cx, cy, r, col, strength in (
        (250, 150, 520, CYAN, 0.55),
        (980, 120, 480, VIOLET, 0.50),
        (820, 560, 520, PINK, 0.34),
        (120, 600, 420, VIOLET, 0.30),
    ):
        for y in range(max(0, cy - r), min(H, cy + r)):
            for x in range(max(0, cx - r), min(W, cx + r)):
                d = math.hypot(x - cx, y - cy) / r
                if d >= 1:
                    continue
                falloff = (1 - d) ** 2
                c.add(x, y, col, falloff * strength * 0.30)

    # 4. the monogram, stroked in the brand gradient
    scale = 8.2
    paths = monogram_paths()
    # fit the monogram into the middle of the canvas
    all_pts = [p for path in paths for p in path]
    min_x = min(p[0] for p in all_pts)
    max_x = max(p[0] for p in all_pts)
    min_y = min(p[1] for p in all_pts)
    max_y = max(p[1] for p in all_pts)
    draw_w = (max_x - min_x) * scale
    draw_h = (max_y - min_y) * scale
    ox = (W - draw_w) / 2 - min_x * scale
    oy = (H - draw_h) / 2 - min_y * scale - 18

    def gradient_at(t):
        t = max(0.0, min(1.0, t))
        return mix(CYAN, VIOLET, t / 0.55) if t < 0.55 else mix(VIOLET, PINK, (t - 0.55) / 0.45)

    # the gradient runs across the monogram itself, not the whole canvas
    def mono_gradient(px):
        return gradient_at((px - (ox + min_x * scale)) / draw_w)

    # a soft halo behind the monogram
    for path in paths:
        pts = [(p[0] * scale + ox, p[1] * scale + oy) for p in path]
        draw_polyline(c, pts, 1.0, 0, 0, 34, mono_gradient)
    # the crisp stroke on top
    for path in paths:
        pts = [(p[0] * scale + ox, p[1] * scale + oy) for p in path]
        draw_polyline(c, pts, 1.0, 0, 0, 10, mono_gradient)

    # 5. a gradient rule under the monogram
    bar_y = int(oy + max_y * scale + 42)
    bar_w = int(draw_w * 0.5)
    bar_x = (W - bar_w) // 2
    for i in range(bar_w):
        t = i / bar_w
        col = gradient_at(t)
        for dy in range(5):
            c.set(bar_x + i, bar_y + dy, col, 0.9)

    c.to_png(OUT)
    return OUT


if __name__ == "__main__":
    path = build()
    print(f"  wrote {os.path.abspath(path)}  ({os.path.getsize(path):,} bytes)")
