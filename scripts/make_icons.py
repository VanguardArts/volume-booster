#!/usr/bin/env python3
"""
Generate the Volume Booster icon set (PNG) with Pillow.

Renders a clean "volume up" speaker (magnet + cone + two sound waves) on a
rounded-square gradient, supersampled 4x for smooth anti-aliased edges, then
downscaled to the standard hicolor sizes. Also emits packaging/preview.png.

Output:
  packaging/icons/hicolor/<size>x<size>/apps/volume-booster.png
"""
import math
import os

from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ICON_DIR = os.path.join(ROOT, "packaging", "icons", "hicolor")

GRADIENT_TOP = (255, 171, 64)     # amber
GRADIENT_BOT = (255, 109, 0)      # deep orange
WHITE = (255, 255, 255, 255)
SUPERSAMPLE = 4


def _lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _roundrect_mask(size, radius):
    m = Image.new("L", (size, size), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, size - 1, size - 1], radius, fill=255)
    return m


def _arc_points(cx, cy, r, start_deg, end_deg, steps=200):
    pts = []
    for i in range(steps + 1):
        t = math.radians(start_deg + (end_deg - start_deg) * i / steps)
        pts.append((cx + r * math.cos(t), cy - r * math.sin(t)))
    return pts


def _render_raw(size):
    """Draw the icon at `size` (no anti-aliasing; used for supersampling)."""
    bg = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    dbg = ImageDraw.Draw(bg)
    for y in range(size):
        t = y / max(1, size - 1)
        dbg.line([(0, y), (size, y)], fill=_lerp(GRADIENT_TOP, GRADIENT_BOT, t) + (255,))

    radius = int(size * 0.22)
    img = Image.composite(bg, Image.new("RGBA", (size, size), (0, 0, 0, 0)),
                          _roundrect_mask(size, radius))

    d = ImageDraw.Draw(img)
    s = size / 512.0
    sc = lambda pts: [(int(x * s), int(y * s)) for x, y in pts]  # noqa: E731

    # --- magnet (small rounded bar) ------------------------------------------
    d.rounded_rectangle(sc([(150, 232), (192, 280)]), radius=int(8 * s), fill=WHITE)

    # --- cone (trapezoid: narrow left, flaring out to the right) -------------
    d.polygon(sc([(192, 232), (268, 200), (268, 312), (192, 280)]), fill=WHITE)

    # --- sound waves (two arcs opening to the right) -------------------------
    wave_width = max(3, int(18 * s))
    for r in (52, 88):
        d.line(sc(_arc_points(278, 256, r, -58, 58)), fill=WHITE, width=wave_width,
               joint="curve")

    return img


def render_icon(size):
    big = _render_raw(size * SUPERSAMPLE)
    return big.resize((size, size), Image.LANCZOS)


def main():
    os.makedirs(ICON_DIR, exist_ok=True)
    for size in (16, 24, 32, 48, 64, 96, 128, 256, 512):
        out_dir = os.path.join(ICON_DIR, f"{size}x{size}", "apps")
        os.makedirs(out_dir, exist_ok=True)
        render_icon(size).save(os.path.join(out_dir, "volume-booster.png"))

    render_icon(512).save(os.path.join(ROOT, "packaging", "preview.png"))
    print("icons written to", ICON_DIR)


if __name__ == "__main__":
    main()
