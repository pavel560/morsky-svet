#!/usr/bin/env python3
"""Mořský svět — Ponor world, overlays, trash, cleanup patches (designer source).

Run:  python3 design/build_sea.py   -> art/ponor/*.svg, art/trash-*.svg
Deterministic, stdlib only. Geometry contract: design/DESIGN.md §6.4.

Layers per zone (utes, chaluhy, sire-more, hlubiny):
  <zone>-far.svg, <zone>-mid.svg, <zone>-near.svg   2048 x 768, seamless left/right, transparent,
                                                    SCREEN-anchored vertically, parallax horizontally
  <zone>-floor.svg                                  2048 x 1024, WORLD plane; stitched by data-in / data-out
  trans-<a>-<b>.svg                                 floor-plane transition tiles (same stitch rule)
"""
import math
import os
import random

from svgkit import INK, Art, f, grp, smooth, mix, ellipse_pts

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.join(HERE, "..", "art")
PON = os.path.join(ART, "ponor")

TW, TH, FH = 2048, 768, 1024     # layer tile, floor tile height

# palette (mirrors tokens.css; art bakes the hex values)
UTES = ("#8fe3dc", "#3fc0c4", "#239fb0")
CHAL = ("#6fc3b4", "#3c9a94", "#237479")
SIRE = ("#3a9fd6", "#2276b8", "#164f8c")
DEEP = ("#12305d", "#0c1f42", "#08142e")
SAND, SAND_L, SAND_D = "#f1d9a6", "#fbecc8", "#d8b77a"
ROCK, ROCK_L, ROCK_D = "#8a8aa0", "#b4b4c8", "#5e5e78"
CORAL = {"pink": ("#ff8a8a", "#ffb8b0", "#d65f6a"), "orange": ("#ff9f4a", "#ffc890", "#d9732a"),
         "violet": ("#b77de0", "#d9b4f4", "#8551b4"), "yellow": ("#ffd25a", "#ffe9a0", "#d6a02a"),
         "teal": ("#52c4a8", "#9ce6d0", "#2f8f7c"), "red": ("#e8604f", "#ff9a86", "#b0402f")}
DULL = "#b9ab9c"
KELP, KELP_L, KELP_D = "#c49a2c", "#e2c35a", "#7d5f1c"
GLOW_C, GLOW_V, GLOW_G = "#6ff3ff", "#b9a1ff", "#9dffc8"


def dull(col, k=.72):
    return mix(col, DULL, k)


def doc(name, w, h, body, defs, extra="", label="", cls="ponor"):
    s = (f'<svg xmlns="http://www.w3.org/2000/svg" class="{cls}" viewBox="0 0 {w} {h}" preserveAspectRatio="xMidYMax slice"{extra} '
         f'role="img" aria-label="{label}"><defs>{"".join(defs)}</defs>{body}</svg>\n')
    path = os.path.join(PON if cls.startswith("ponor") else ART, name)
    with open(path, "w") as fh:
        fh.write(s)
    return len(s)


def wrap(x, half, draw, W=TW):
    """Draw at x and, if the element crosses a tile edge, also at x±W (seamless tiles)."""
    out = draw(x)
    if x - half < 0:
        out += draw(x + W)
    if x + half > W:
        out += draw(x - W)
    return out


# ================================================================== scenery kit (v2: texture, gorgonians, soft corals)

def speckle(a, d, box, n, cols, r=(1.2, 3.0), seed=1, op=.6):
    """Gouache speckle texture clipped to a shape (Houbičky's cap speckles, under water)."""
    rng = random.Random(seed)
    x0, y0, x1, y1 = box
    c = a.clip("sp", d)
    dots = "".join(f'<circle cx="{f(rng.uniform(x0, x1))}" cy="{f(rng.uniform(y0, y1))}" r="{f(rng.uniform(*r))}" fill="{rng.choice(cols)}"/>' for _ in range(n))
    return f'<g clip-path="{c}" opacity="{op}">{dots}</g>'


def rock(a, x, y, w, h, col=(ROCK, ROCK_L, ROCK_D), ink=True, sw=3, crust=None, seed=None):
    pts = ellipse_pts(x, y - h * .45, w / 2, h * .55, n=11, wob=lambda t: .08 * math.sin(3 * t + x * .01) + .05 * math.sin(5 * t))
    pts = [(px, min(py, y)) for px, py in pts]
    d = smooth(a.jit(pts, w * .01), t=.18)
    c, l, dk = col
    out = a.shape(d, c, l, dk, y - h, y, sw=0, hi_box=(x - w * .12, y - h * .7, w * .22, h * .14), shade=ink)
    out += speckle(a, d, (x - w / 2, y - h, x + w / 2, y), int(w * h / 260) + 6, (l, dk, mix(c, "#ffffff", .3)), (1.2, 3.2), seed or int(x), .55)
    if ink:
        rr = random.Random(int(x * 3))
        cx_ = x + rr.uniform(-w * .2, w * .15)
        out += f'<path d="M{f(cx_)} {f(y - h * .8)}q{f(w * .05)} {f(h * .25)} {f(-w * .03)} {f(h * .45)}" fill="none" stroke="{dk}" stroke-width="{f(max(2, sw * .8))}" stroke-linecap="round" opacity=".7"/>'
    if crust:
        cl = a.clip("cr", d)
        out += (f'<g clip-path="{cl}"><path d="M{f(x - w * .45)} {f(y - h * .78)}Q{f(x)} {f(y - h * 1.12)} {f(x + w * .42)} {f(y - h * .74)}" fill="none" stroke="{crust}" stroke-width="{f(h * .16)}" stroke-linecap="round" opacity=".9"/>'
                + "".join(f'<circle cx="{f(x + (k - 3) * w * .12)}" cy="{f(y - h * .92 + abs(k - 3) * h * .05)}" r="{f(h * .045)}" fill="{mix(crust, "#ffffff", .35)}"/>' for k in range(7)) + "</g>")
    if ink and sw:
        out += f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="{f(sw)}" stroke-linejoin="round"/>'
    return out


def brain_coral(a, x, y, r, col):
    c, l, dk = col
    d = smooth([(px, min(py, y)) for px, py in ellipse_pts(x, y - r * .45, r, r * .62, n=14, wob=lambda t: .04 * math.sin(4 * t))], t=.18)
    out = a.shape(d, c, l, dk, y - r * 1.1, y, hi_box=(x - r * .3, y - r * .8, r * .4, r * .16))
    cl = a.clip("bc", d)
    lines = []
    for k in range(6):
        yy = y - r * .12 - k * r * .15
        pts = [(x - r + i * r / 6, yy + math.sin(i * 1.7 + k) * r * .08) for i in range(13)]
        lines.append(smooth(pts, closed=False))
    out += f'<g clip-path="{cl}">' + "".join(f'<path d="{p}" fill="none" stroke="{dk}" stroke-width="{f(r * .05)}" stroke-linecap="round" opacity=".75"/>'
                                             f'<path d="{p}" fill="none" stroke="{l}" stroke-width="{f(r * .025)}" stroke-linecap="round" transform="translate(0 {f(-r * .05)})" opacity=".8"/>' for p in lines) + "</g>"
    out += speckle(a, d, (x - r, y - r * 1.1, x + r, y), int(r * 1.2), (l, "#ffffff"), (.8, 1.8), int(x), .55)
    return out


def branch_coral(a, x, y, h, col, n=5, seed=0):
    c, l, dk = col
    rng = random.Random(seed + int(x))
    out_ink, out_col, out_hi, polyps = [], [], [], []

    def br(x0, y0, ang, L, w, depth):
        x1 = x0 + math.cos(ang) * L
        y1 = y0 - math.sin(ang) * L
        mx = (x0 + x1) / 2 + rng.uniform(-L * .12, L * .12)
        my = (y0 + y1) / 2
        d = f"M{f(x0)} {f(y0)}Q{f(mx)} {f(my)} {f(x1)} {f(y1)}"
        out_ink.append(f'<path d="{d}" stroke="{INK}" stroke-width="{f(w + 5)}" stroke-linecap="round" fill="none"/>')
        out_col.append(f'<path d="{d}" stroke="{c}" stroke-width="{f(w)}" stroke-linecap="round" fill="none"/>'
                       f'<path d="{d}" stroke="{dk}" stroke-width="{f(w * .35)}" stroke-linecap="round" fill="none" transform="translate({f(w * .22)} {f(w * .1)})" opacity=".45"/>')
        out_hi.append(f'<path d="{d}" stroke="{l}" stroke-width="{f(w * .28)}" stroke-linecap="round" fill="none" transform="translate({f(-w * .2)} 0)" opacity=".85"/>')
        for t in (.35, .7):
            px_, py_ = x0 + (x1 - x0) * t + rng.uniform(-w * .2, w * .2), y0 + (y1 - y0) * t
            polyps.append(f'<circle cx="{f(px_)}" cy="{f(py_)}" r="{f(max(1, w * .13))}" fill="{l}" opacity=".9"/>')
        if depth > 0:
            for da in (-.45, .4):
                br(x1, y1, ang + da + rng.uniform(-.15, .15), L * .72, w * .78, depth - 1)
        else:
            out_hi.append(f'<circle cx="{f(x1)}" cy="{f(y1)}" r="{f(w * .42)}" fill="{l}"/>')
    for i in range(n):
        ang = math.radians(90 + (i - (n - 1) / 2) * 16 + rng.uniform(-6, 6))
        br(x + (i - (n - 1) / 2) * h * .06, y, ang, h * .42, h * .085, 2)
    return "".join(out_ink) + "".join(out_col) + "".join(out_hi) + "".join(polyps)


def fan_coral(a, x, y, h, col):
    """Gorgonian sea fan as a living branching plant (v2): no lattice and no outline envelope —
    a short trunk splitting into many fine branches in one plane, with polyp dots."""
    c, l, dk = col
    rng = random.Random(int(x * 7 + h))
    ink, colr, polyps = [], [], []

    def br(x0, y0, ang, L, w, depth):
        bend = rng.uniform(-.25, .25)
        x1, y1 = x0 + math.cos(ang) * L, y0 - math.sin(ang) * L
        mx, my = x0 + math.cos(ang + bend) * L * .55, y0 - math.sin(ang + bend) * L * .55
        d = f"M{f(x0)} {f(y0)}Q{f(mx)} {f(my)} {f(x1)} {f(y1)}"
        ink.append(f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="{f(w + 3)}" stroke-linecap="round"/>')
        colr.append(f'<path d="{d}" fill="none" stroke="{c}" stroke-width="{f(w)}" stroke-linecap="round"/>')
        if depth <= 1:
            for t in (.4, .8):
                polyps.append(f'<circle cx="{f(x0 + (x1 - x0) * t)}" cy="{f(y0 + (y1 - y0) * t)}" r="{f(max(1.2, w * .45))}" fill="{l}"/>')
        if depth > 0:
            k = 2 if depth > 1 else rng.choice((1, 2))
            for j in range(k):
                da = (-.32 if j == 0 else .3) + rng.uniform(-.12, .12) if k == 2 else rng.uniform(-.2, .2)
                br(x1, y1, ang + da, L * rng.uniform(.7, .85), max(1.6, w * .72), depth - 1)
    trunk = h * .16
    ink.append(f'<path d="M{f(x)} {f(y)}L{f(x)} {f(y - trunk)}" stroke="{INK}" stroke-width="{f(h * .06 + 3)}" stroke-linecap="round"/>')
    colr.append(f'<path d="M{f(x)} {f(y)}L{f(x)} {f(y - trunk)}" stroke="{dk}" stroke-width="{f(h * .06)}" stroke-linecap="round"/>')
    for ang in (60, 82, 100, 122):
        br(x, y - trunk, math.radians(ang + rng.uniform(-5, 5)), h * .26, h * .035 + 1.5, 4)
    return "".join(ink) + "".join(colr) + "".join(polyps)


def table_coral(a, x, y, w, col):
    c, l, dk = col
    stem = f'<path d="M{f(x - w * .06)} {f(y)}L{f(x - w * .04)} {f(y - w * .28)}L{f(x + w * .04)} {f(y - w * .28)}L{f(x + w * .06)} {f(y)}Z" fill="{dk}" stroke="{INK}" stroke-width="2.6" stroke-linejoin="round"/>'
    top = smooth([(x - w / 2, y - w * .3), (x - w * .3, y - w * .4), (x, y - w * .42), (x + w * .3, y - w * .4), (x + w / 2, y - w * .3),
                   (x + w * .3, y - w * .24), (x, y - w * .22), (x - w * .3, y - w * .24)], t=.18)
    out = stem + a.shape(top, c, l, dk, y - w * .42, y - w * .22, hi_box=(x - w * .1, y - w * .38, w * .25, w * .03))
    out += speckle(a, top, (x - w / 2, y - w * .42, x + w / 2, y - w * .22), int(w * .4), (l, "#ffffff"), (.8, 2), int(x), .6)
    out += "".join(f'<path d="M{f(x + k * w * .1)} {f(y - w * .225)}l{f(k * 1.5)} 7" stroke="{dk}" stroke-width="2.2" stroke-linecap="round"/>' for k in range(-4, 5))
    return out


def tube_sponge(a, x, y, h, col):
    c, l, dk = col
    out = ""
    for k, (dx, hh, ww) in enumerate(((-h * .22, .75, .2), (0, 1.0, .24), (h * .22, .6, .19))):
        w = h * ww
        x0 = x + dx
        top = y - h * hh
        d = smooth([(x0 - w / 2, y), (x0 - w / 2 - 2, top + w * .2), (x0 - w / 2, top), (x0 + w / 2, top), (x0 + w / 2 + 2, top + w * .2), (x0 + w / 2, y)], t=.12)
        out += a.shape(d, c, l, dk, top, y, hi=False)
        out += speckle(a, d, (x0 - w, top, x0 + w, y), int(h * hh * .5), (dk, l), (.8, 1.8), int(x0), .6)
        out += f'<ellipse cx="{f(x0)}" cy="{f(top)}" rx="{f(w / 2 - 3)}" ry="{f(w * .18)}" fill="{dk}" stroke="{INK}" stroke-width="2.2"/>'
    return out


def soft_coral(a, x, y, h, col):
    """Leathery soft coral: a cluster of rounded lobes with a fuzz of polyps."""
    c, l, dk = col
    rng = random.Random(int(x))
    out = ""
    for k, (dx, hh, rr) in enumerate(((-h * .3, .7, .32), (h * .28, .62, .3), (0, 1.0, .38))):
        cx_, cy_ = x + dx, y - h * hh
        stalk = f"M{f(x + dx * .3 - 8)} {f(y)}Q{f(cx_ - 6)} {f((y + cy_) / 2)} {f(cx_ - h * rr * .5)} {f(cy_ + h * .08)}L{f(cx_ + h * rr * .5)} {f(cy_ + h * .08)}Q{f(cx_ + 6)} {f((y + cy_) / 2)} {f(x + dx * .3 + 8)} {f(y)}Z"
        out += f'<path d="{stalk}" fill="{mix(c, "#ffffff", .35)}" stroke="{INK}" stroke-width="2.4" stroke-linejoin="round"/>'
        cap = smooth(ellipse_pts(cx_, cy_, h * rr, h * rr * .62, n=12, wob=lambda t: .1 * math.sin(5 * t + k)), t=.2)
        out += a.shape(cap, c, l, dk, cy_ - h * rr * .62, cy_ + h * rr * .62, sw=2.6, hi_box=(cx_ - h * rr * .3, cy_ - h * rr * .3, h * rr * .3, h * rr * .14))
        out += speckle(a, cap, (cx_ - h * rr, cy_ - h * rr, cx_ + h * rr, cy_ + h * rr), int(h * rr * 2.2), ("#ffffff", l), (1, 2.2), int(cx_), .8)
    return out


def sea_whip(a, x, y, h, col, n=3):
    c, l, dk = col
    rng = random.Random(int(x * 3))
    out_i, out_c = "", ""
    for k in range(n):
        x0 = x + (k - (n - 1) / 2) * 10
        hh = h * rng.uniform(.7, 1.0)
        pts = [(x0 + math.sin(t * 2.4 + k) * 10 * t + (k - 1) * 18 * t, y - hh * t) for t in [i / 8 for i in range(9)]]
        d = smooth(pts, closed=False)
        out_i += f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="7.5" stroke-linecap="round"/>'
        out_c += (f'<path d="{d}" fill="none" stroke="{c}" stroke-width="4.5" stroke-linecap="round"/>'
                  f'<path d="{d}" fill="none" stroke="{l}" stroke-width="1.6" stroke-linecap="round" stroke-dasharray="2 6"/>')
    return out_i + out_c


def zoanthids(a, x, y, n, col, seed=1):
    """A little garden of button polyps (flower discs) on a rock top."""
    c, l, dk = col
    rng = random.Random(seed + int(x))
    out = ""
    for k in range(n):
        px_, py_ = x + rng.uniform(-n * 5, n * 5), y + rng.uniform(-6, 6)
        r = rng.uniform(4.5, 7.5)
        out += (f'<circle cx="{f(px_)}" cy="{f(py_)}" r="{f(r)}" fill="{c}" stroke="{INK}" stroke-width="1.6"/>'
                f'<circle cx="{f(px_)}" cy="{f(py_)}" r="{f(r * .45)}" fill="{l}"/>')
    return out


def seagrass(a, x, y, h, n=6, col="#6aa04a", light="#9cc96e", sway_cls=None):
    rng = random.Random(int(x * 7 + y))
    out = []
    for i in range(n):
        x0 = x + (i - n / 2) * 7 + rng.uniform(-2, 2)
        hh = h * rng.uniform(.6, 1)
        bend = rng.uniform(-.5, .5) * hh * .35
        d = f"M{f(x0 - 4)} {f(y)}Q{f(x0 + bend * .3)} {f(y - hh * .6)} {f(x0 + bend)} {f(y - hh)}Q{f(x0 + bend * .4 + 5)} {f(y - hh * .55)} {f(x0 + 4)} {f(y)}Z"
        out.append(f'<path d="{d}" fill="{col if i % 2 else light}" stroke="{INK}" stroke-width="2" stroke-linejoin="round"/>'
                   f'<path d="M{f(x0)} {f(y - 4)}Q{f(x0 + bend * .3)} {f(y - hh * .55)} {f(x0 + bend * .9)} {f(y - hh * .92)}" fill="none" stroke="{mix(light, "#ffffff", .4)}" stroke-width="1.2" opacity=".7"/>')
    inner = "".join(out)
    if sway_cls:
        return grp(sway_cls, inner, (x, y))
    return inner


def shell(a, x, y, s, col="#ffd9c0"):
    d = f"M{f(x - 10 * s)} {f(y)}Q{f(x - 12 * s)} {f(y - 14 * s)} {f(x)} {f(y - 16 * s)}Q{f(x + 12 * s)} {f(y - 14 * s)} {f(x + 10 * s)} {f(y)}Z"
    ribs = "".join(f'<path d="M{f(x)} {f(y)}L{f(x + k * 3 * s)} {f(y - 14 * s)}" stroke="#d99a7a" stroke-width="1.4"/>' for k in (-2, -1, 0, 1, 2))
    return f'<path d="{d}" fill="{col}"/>{ribs}<path d="{d}" fill="none" stroke="{INK}" stroke-width="2" stroke-linejoin="round"/>'


def snail_shell(a, x, y, s, col="#f6c9a0"):
    d = smooth([(x - 12 * s, y), (x - 14 * s, y - 10 * s), (x - 4 * s, y - 18 * s), (x + 10 * s, y - 14 * s), (x + 14 * s, y - 4 * s), (x + 8 * s, y + 1 * s)], t=.2)
    return (f'<path d="{d}" fill="{col}" stroke="{INK}" stroke-width="2" stroke-linejoin="round"/>'
            f'<path d="M{f(x + 4 * s)} {f(y - 4 * s)}a{f(5 * s)} {f(5 * s)} 0 1 0 {f(-6 * s)} {f(-6 * s)}a{f(9 * s)} {f(9 * s)} 0 1 1 {f(12 * s)} {f(4 * s)}" fill="none" stroke="#c98a5a" stroke-width="1.6"/>')


def pebbles(a, line, n, seed, yrange=(6, 60), col=("#c9b48c", "#a9967a", "#e3d2ad")):
    rng = random.Random(seed)
    out = ""
    for _ in range(n):
        x = rng.uniform(10, TW - 10)
        y = y_at(line, x) + rng.uniform(*yrange)
        rx = rng.uniform(4, 11)
        out += f'<ellipse cx="{f(x)}" cy="{f(y)}" rx="{f(rx)}" ry="{f(rx * .62)}" fill="{rng.choice(col)}" stroke="{INK}" stroke-width="1.4" opacity=".9"/>'
    return out


def kelp(a, x, y, h, seed=0, col=(KELP, KELP_L, KELP_D), ink=True, segs=4, cls="kelp", lean=0.0):
    """Tall kelp stalk with blades and floats, as NESTED sway groups:
    g.kelp[data-pivot=base] > … > g.kelp-seg[data-pivot=joint] — rotate each by a few degrees, phase-shifted."""
    rng = random.Random(seed * 31 + int(x))
    c, l, dk = col
    seg_h = h / segs
    sw = 2.4 if ink else 0
    shade = [c, l, mix(c, dk, .25)]

    def seg(k, x0, y0):
        x1 = x0 + rng.uniform(-14, 14) + lean * seg_h * .1
        y1 = y0 - seg_h
        stipe = f'<path d="M{f(x0)} {f(y0)}Q{f((x0 + x1) / 2 + rng.uniform(-10, 10))} {f((y0 + y1) / 2)} {f(x1)} {f(y1)}" fill="none" stroke="{dk}" stroke-width="5" stroke-linecap="round"/>'
        blades = ""
        for b in range(3):
            t = (b + .5) / 3
            bx, by = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            side = -1 if (b + k) % 2 else 1
            L = seg_h * rng.uniform(.75, 1.0)
            W = L * .15
            ang = math.radians(rng.uniform(52, 66))
            ux, uy = side * math.cos(ang), -math.sin(ang)
            nx_, ny_ = -uy, ux
            tip = (bx + ux * L, by + uy * L)
            up, dn = [], []
            for q in range(1, 7):
                tq = q / 7
                w = W * math.sin(math.pi * min(1, tq * 1.15)) * (1 + .18 * math.sin(q * 2.3))
                cx_, cy_ = bx + ux * L * tq + nx_ * W * .5 * math.sin(tq * 5), by + uy * L * tq + ny_ * W * .5 * math.sin(tq * 5)
                up.append((cx_ + nx_ * w / 2, cy_ + ny_ * w / 2))
                dn.append((cx_ - nx_ * w / 2, cy_ - ny_ * w / 2))
            d = smooth([(bx, by)] + up + [tip] + dn[::-1], t=.18)
            fc = shade[(b + k + seed) % 3]
            blades += (f'<path d="{d}" fill="{fc}" stroke="{INK if ink else dk}" stroke-width="{sw if ink else 0}" stroke-linejoin="round"/>'
                       f'<path d="M{f(bx)} {f(by)}L{f(tip[0])} {f(tip[1])}" fill="none" stroke="{dk}" stroke-width="1.4" opacity=".45"/>')
            if ink:
                blades += f'<path d="M{f(up[1][0])} {f(up[1][1])}L{f(up[4][0])} {f(up[4][1])}" fill="none" stroke="#ffffff" stroke-width="1.6" opacity=".35" stroke-linecap="round"/>'
            blades += f'<circle cx="{f(bx + side * 4)}" cy="{f(by - 3)}" r="{f(max(4, W * .42))}" fill="{l}" stroke="{INK if ink else dk}" stroke-width="{1.6 if ink else 0}"/>'
        inner = stipe + blades
        if k + 1 < segs:
            inner += seg(k + 1, x1, y1)
        return grp(f"{cls}-seg", inner, (x0, y0)) if k else inner
    hold = (f'<path d="M{f(x - 18)} {f(y)}Q{f(x)} {f(y - 22)} {f(x + 18)} {f(y)}Z" fill="{dk}" stroke="{INK if ink else dk}" stroke-width="{sw}"/>')
    return grp(cls, hold + seg(0, x, y), (x, y))


def sea_pen(a, x, y, h, glow=True, lit=1.0):
    """Deep-sea sea pen: a feather on a stalk. Its glow = small dots along the feather + one soft halo."""
    out = f'<path d="M{f(x)} {f(y)}Q{f(x + 4)} {f(y - h * .5)} {f(x)} {f(y - h)}" fill="none" stroke="{INK}" stroke-width="5" stroke-linecap="round"/>'
    out += f'<path d="M{f(x)} {f(y)}Q{f(x + 4)} {f(y - h * .5)} {f(x)} {f(y - h)}" fill="none" stroke="#d8c9a8" stroke-width="2.6" stroke-linecap="round"/>'
    leaf = ""
    for k in range(8):
        yy = y - h * .32 - k * h * .085
        L = h * .2 * (1 - abs(k - 3.5) / 5.5)
        for s_ in (-1, 1):
            leaf += f'<path d="M{f(x)} {f(yy)}q{f(s_ * L * .5)} {f(-L * .55)} {f(s_ * L)} {f(-L * .3)}" fill="none" stroke="#f3d6a0" stroke-width="3.2" stroke-linecap="round"/>'
    out += leaf
    g = ""
    if glow:
        halo = a.radial("sph", [(0, GLOW_V, .45), (1, GLOW_V, 0)], user=(x, y - h * .62, h * .42))
        g = f'<ellipse cx="{f(x)}" cy="{f(y - h * .62)}" rx="{f(h * .3)}" ry="{f(h * .42)}" fill="{halo}"/>'
        g += "".join(f'<circle cx="{f(x + s_ * h * .2 * (1 - abs(k - 3.5) / 5.5))}" cy="{f(y - h * .32 - k * h * .085 - h * .06)}" r="{f(max(1.8, h * .018))}" fill="{GLOW_C if k % 2 else GLOW_V}"/>'
                     for k in range(8) for s_ in (-1, 1))
    return out, g


def glass_sponge(a, x, y, h):
    """Venus' flower basket v2: a slender curved lilac vase with a frilly rim and pores (no lattice: a mesh reads as the ghost net)."""
    w = h * .28
    bend = h * .1
    left = [(x - w * .2, y), (x - w * .36 + bend * .2, y - h * .3), (x - w * .5 + bend * .6, y - h * .7), (x - w * .56 + bend, y - h)]
    right = [(x + w * .56 + bend, y - h), (x + w * .5 + bend * .6, y - h * .7), (x + w * .36 + bend * .2, y - h * .3), (x + w * .2, y)]
    d = smooth(left + right, t=.16)
    g = a.linear("gsv", [(0, "#f1eaff"), (.55, "#c9bff2"), (1, "#8a82c6")], 0, y - h, 0, y)
    pores = "".join(f'<ellipse cx="{f(x + bend * t + (k % 2 - .5) * w * .42)}" cy="{f(y - h * t)}" rx="2.4" ry="1.6" fill="#6a63a8" opacity=".6"/>'
                    for k, t in enumerate((.18, .3, .42, .54, .66, .78)))
    frill = "".join(f'<circle cx="{f(x - w * .56 + bend + k * w * 1.12 / 7)}" cy="{f(y - h - 2 + (k % 2) * 3)}" r="3.4" fill="#f6f1ff" stroke="{INK}" stroke-width="1.2"/>' for k in range(8))
    return (f'<path d="{d}" fill="{g}"/>{pores}'
            f'<path d="M{f(x - w * .3 + bend * .5)} {f(y - h * .8)}Q{f(x - w * .2)} {f(y - h * .4)} {f(x - w * .1)} {f(y - h * .1)}" fill="none" stroke="#ffffff" stroke-width="3" opacity=".6" stroke-linecap="round"/>'
            f'<ellipse cx="{f(x + bend)}" cy="{f(y - h)}" rx="{f(w * .55)}" ry="{f(w * .16)}" fill="#3a3470" stroke="{INK}" stroke-width="2"/>'
            f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="2.4"/>' + frill)


def bamboo_coral(a, x, y, h, seed=1):
    """Deep bamboo coral: pale branching stalks with glowing nodes. Returns (body, glow)."""
    rng = random.Random(seed + int(x))
    body, glow = "", ""

    def br(x0, y0, ang, L, depth):
        nonlocal body, glow
        x1, y1 = x0 + math.cos(ang) * L, y0 - math.sin(ang) * L
        body += (f'<path d="M{f(x0)} {f(y0)}L{f(x1)} {f(y1)}" stroke="{INK}" stroke-width="6" stroke-linecap="round"/>'
                 f'<path d="M{f(x0)} {f(y0)}L{f(x1)} {f(y1)}" stroke="#e9e4d6" stroke-width="3" stroke-linecap="round"/>')
        body += f'<circle cx="{f(x1)}" cy="{f(y1)}" r="3.2" fill="#3a3470"/>'
        glow += f'<circle cx="{f(x1)}" cy="{f(y1)}" r="3.6" fill="{GLOW_C}"/><circle cx="{f(x1)}" cy="{f(y1)}" r="9" fill="{GLOW_C}" opacity=".22"/>'
        if depth:
            for da in (-.5, .45):
                br(x1, y1, ang + da + rng.uniform(-.15, .15), L * .78, depth - 1)
    br(x, y, math.radians(90 + rng.uniform(-6, 6)), h * .32, 3)
    return body, glow


def sea_lily(a, x, y, h):
    """Crinoid (sea lily): a stalk with a feathery crown. Returns (body, glow)."""
    out = (f'<path d="M{f(x)} {f(y)}Q{f(x + 10)} {f(y - h * .5)} {f(x + 4)} {f(y - h * .8)}" fill="none" stroke="{INK}" stroke-width="6" stroke-linecap="round"/>'
           f'<path d="M{f(x)} {f(y)}Q{f(x + 10)} {f(y - h * .5)} {f(x + 4)} {f(y - h * .8)}" fill="none" stroke="#f2b8a0" stroke-width="3" stroke-linecap="round" stroke-dasharray="4 3"/>')
    cx_, cy_ = x + 4, y - h * .8
    glow = ""
    for k in range(7):
        ang = math.radians(200 + k * 23)
        ex, ey = cx_ + math.cos(ang) * h * .24, cy_ + math.sin(ang) * h * .2 - h * .08
        d = f"M{f(cx_)} {f(cy_)}Q{f((cx_ + ex) / 2)} {f(min(cy_, ey) - h * .08)} {f(ex)} {f(ey)}"
        out += (f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="6" stroke-linecap="round"/>'
                f'<path d="{d}" fill="none" stroke="#ff9fb8" stroke-width="3.2" stroke-linecap="round"/>')
        glow += f'<circle cx="{f(ex)}" cy="{f(ey)}" r="2.6" fill="{GLOW_V}"/>'
    out += f'<circle cx="{f(cx_)}" cy="{f(cy_)}" r="6" fill="#ff9fb8" stroke="{INK}" stroke-width="2"/>'
    return out, glow


# ================================================================== floor line + tiles

def floor_y(x, yin, yout, s_in, s_out, waves, W=TW):
    """Hermite trend (matches neighbour slopes at the edges) + enveloped wiggle (zero value+slope at edges)."""
    t = x / W
    h00, h10, h01, h11 = 2 * t ** 3 - 3 * t ** 2 + 1, t ** 3 - 2 * t ** 2 + t, -2 * t ** 3 + 3 * t ** 2, t ** 3 - t ** 2
    trend = h00 * yin + h10 * s_in * W + h01 * yout + h11 * s_out * W
    env = math.sin(math.pi * t) ** 2
    wig = sum(amp * math.sin(2 * math.pi * k * t + ph) for k, amp, ph in waves)
    return trend + wig * env


def floor_tile(name, zone, yin, yout, s_in, s_out, waves, fill, deco, defs_art, label, H=FH, under=None, extra_attr="", grain=None, lip=None):
    """v2: sand-grain texture over the whole body, a sunlit lip under the floor line, strata + pebbles in the cut."""
    a = defs_art
    xs = list(range(0, TW + 1, 32))
    line = [(x, floor_y(x, yin, yout, s_in, s_out, waves)) for x in xs]
    d = "M" + " L".join(f"{f(x)} {f(y)}" for x, y in line) + f" L{TW} {H} L0 {H}Z"
    c, l, dk = fill
    top = min(y for _, y in line)
    g = a.linear("fl", [(0, l), (.08, c), (.45, mix(c, dk, .45)), (1, dk)], 0, top, 0, H)
    body = f'<path d="{d}" fill="{g}"/>'
    if under:
        body += under(line)
    # strata: wavy darker bands in the cut, with pebbles + shell bits (Houbičky's soil cut, under water)
    rng = random.Random(len(name) * 7)
    cl = a.clip("cut", d)
    strata = ""
    for k in range(1, 6):
        pts = [(x, y + 70 + k * 62 + 12 * math.sin(x * .006 + k * 1.7)) for x, y in line[::2]]
        strata += f'<path d="M{" L".join(f"{f(x)} {f(y)}" for x, y in pts)}" fill="none" stroke="{mix(c, dk, .7)}" stroke-width="{4 - k * .4:.1f}" opacity=".5"/>'
    for _ in range(46):
        x = rng.uniform(0, TW)
        y = y_at(line, x) + rng.uniform(80, H - y_at(line, x) - 20)
        r = rng.uniform(5, 14)
        strata += f'<ellipse cx="{f(x)}" cy="{f(y)}" rx="{f(r)}" ry="{f(r * .6)}" fill="{mix(c, dk, rng.uniform(.3, .7))}" stroke="{mix(c, dk, .85)}" stroke-width="1.6" opacity=".85"/>'
    gcols = grain or (l, dk, mix(c, "#ffffff", .4))
    grains = "".join(f'<circle cx="{f(rng.uniform(0, TW))}" cy="{f(rng.uniform(top, H))}" r="{f(rng.uniform(.9, 2.4))}" fill="{rng.choice(gcols)}"/>' for _ in range(900))
    lipc = lip or mix(l, "#ffffff", .35)
    lip_path = f'<path d="M{" L".join(f"{f(x)} {f(y + 9)}" for x, y in line)}" fill="none" stroke="{lipc}" stroke-width="16" stroke-linejoin="round" opacity=".75"/>'
    body += f'<g clip-path="{cl}">{strata}<g opacity=".55">{grains}</g>{lip_path}</g>'
    body += f'<path d="M{" L".join(f"{f(x)} {f(y)}" for x, y in line)}" fill="none" stroke="{INK}" stroke-width="3" stroke-linejoin="round"/>'
    body += deco(line)
    samples = ",".join(f(floor_y(x, yin, yout, s_in, s_out, waves)) for x in range(0, TW + 1, 128))
    extra = f' data-zone="{zone}" data-in="{f(yin)}" data-out="{f(yout)}" data-floor-y="{samples}" data-fill="{dk}"{extra_attr}'
    return doc(name, TW, H, body, a.defs, extra=extra, label=label, cls="ponor floor")


def y_at(line, x):
    x = max(0, min(TW, x))
    i = min(len(line) - 2, int(x // 32))
    (x0, y0), (x1, y1) = line[i], line[i + 1]
    return y0 + (y1 - y0) * (x - x0) / (x1 - x0)


# slopes (units per unit x) — shared so transitions meet their neighbours smoothly
S_UTES, S_CHAL, S_SIRE, S_DEEP = 120 / TW, 160 / TW, 220 / TW, 90 / TW
IN = 560


def sand_under(line):
    return ""


def ripples(a, line, col=SAND_D, n=40, seed=1):
    rng = random.Random(seed)
    out = []
    for _ in range(n):
        x = rng.uniform(20, TW - 20)
        y = y_at(line, x) + rng.uniform(16, 110)
        w = rng.uniform(30, 70)
        out.append(f'<path d="M{f(x - w / 2)} {f(y)}q{f(w / 4)} -6 {f(w / 2)} 0t{f(w / 2)} 0" fill="none" stroke="{col}" stroke-width="2.6" stroke-linecap="round" opacity=".8"/>'
                   f'<path d="M{f(x - w / 2)} {f(y - 3)}q{f(w / 4)} -6 {f(w / 2)} 0" fill="none" stroke="#fff6dc" stroke-width="1.6" stroke-linecap="round" opacity=".7"/>')
    return "".join(out)


def light_pools(a, spots, col="#ffffff"):
    """Soft painterly light pools in the water (bbox gradients, so the seamless copies need no extra defs)."""
    out = ""
    for x, y, rx, ry, op in spots:
        g = a.radial("lp", [(0, col, op), (1, col, 0)], cx="50%", cy="50%", r="50%")
        out += wrap(x, rx, lambda X, g=g, y=y, rx=rx, ry=ry: f'<ellipse cx="{f(X)}" cy="{f(y)}" rx="{f(rx)}" ry="{f(ry)}" fill="{g}"/>')
    return out


def haze_band(a, y0, col, op=.55):
    g = a.linear("hz", [(0, col, 0), (1, col, op)], 0, y0, 0, TH)
    return f'<rect x="0" y="{f(y0)}" width="{TW}" height="{f(TH - y0)}" fill="{g}"/>'


def ridge_band(y0, amps, col, op=1.0, W=TW, H=TH):
    pts = []
    for x in range(0, W + 1, 32):
        t = x / W
        y = y0 + sum(a_ * math.sin(2 * math.pi * k * t + ph) for k, a_, ph in amps)
        pts.append((x, y))
    d = "M" + " L".join(f"{f(x)} {f(y)}" for x, y in pts) + f" L{W} {H} L0 {H}Z"
    return f'<path d="{d}" fill="{col}" opacity="{op}"/>', pts


def silhouette_reef(a, y0, amps, col, op, seed, density=150, hmin=60, hmax=150):
    """A hazy reef ridge with coral-shaped tops (branch + fan + dome silhouettes), no ink."""
    band, pts = ridge_band(y0, amps, col, op)
    rng = random.Random(seed)
    out = band
    yat = lambda x: y0 + sum(a_ * math.sin(2 * math.pi * k * x / TW + ph) for k, a_, ph in amps)
    for x in range(40, TW, density):
        xx = x + rng.uniform(-30, 30)
        h = rng.uniform(hmin, hmax)
        kind = rng.choice(("dome", "branch", "fan", "branch"))
        y = yat(xx) + 6

        def draw(X, kind=kind, h=h, y=y):
            if kind == "dome":
                return f'<path d="{smooth([(X - h * .7, y), (X - h * .55, y - h * .45), (X, y - h * .62), (X + h * .55, y - h * .45), (X + h * .7, y)])}" fill="{col}" opacity="{op}"/>'
            if kind == "fan":
                return f'<path d="M{f(X - h * .45)} {f(y - h * .5)}Q{f(X)} {f(y - h * 1.15)} {f(X + h * .45)} {f(y - h * .5)}Q{f(X + h * .2)} {f(y)} {f(X)} {f(y)}Q{f(X - h * .2)} {f(y)} {f(X - h * .45)} {f(y - h * .5)}Z" fill="{col}" opacity="{op}"/>'
            s_ = ""
            for k in range(5):
                ang = math.radians(60 + k * 15)
                x1, y1 = X + math.cos(ang) * h * .9, y - math.sin(ang) * h
                s_ += f'<path d="M{f(X)} {f(y)}Q{f(X + (x1 - X) * .3)} {f(y - h * .5)} {f(x1)} {f(y1)}" fill="none" stroke="{col}" stroke-width="{f(h * .1)}" stroke-linecap="round" opacity="{op}"/>'
            return s_
        out += wrap(xx, h, draw)
    return out


def far_layer(name, label, body, defs):
    return doc(name, TW, TH, body, defs, extra=' data-layer="far"', label=label, cls="ponor layer")


def school_silhouette(x, y, n, col, op, seed, s=1.0):
    rng = random.Random(seed)
    out = ""
    for k in range(n):
        t = k / n * math.tau
        fx, fy = x + math.cos(t) * 90 * s + rng.uniform(-18, 18) * s, y + math.sin(t * 2) * 24 * s + rng.uniform(-12, 12) * s
        out += f'<path d="M{f(fx)} {f(fy)}q{f(8 * s)} {f(-5 * s)} {f(16 * s)} 0q{f(-8 * s)} {f(5 * s)} {f(-16 * s)} 0zM{f(fx)} {f(fy)}l{f(-6 * s)} {f(-4 * s)}v{f(8 * s)}z" fill="{col}" opacity="{op}"/>'
    return out


# ------------------------------------------------------------------ UTES
def utes_floor():
    a = Art("utesfl", seed=101)
    waves = [(3, 18, .4), (5, 9, 1.3), (9, 4, 2.0)]
    yout = IN + 120

    def deco(line):
        out = ripples(a, line, n=40, seed=3) + pebbles(a, line, 30, 5)
        Y = lambda x: y_at(line, x)
        items = [
            # cluster A (left)
            (110, lambda x: fan_coral(a, x, Y(x) + 4, 210, CORAL["violet"])),
            (200, lambda x: rock(a, x, Y(x) + 16, 200, 92, crust="#e98fa6")),
            (190, lambda x: zoanthids(a, x, Y(x) - 70, 6, ("#7fe0b0", "#e8fff2", "#3a9a70"))),
            (150, lambda x: brain_coral(a, x, Y(x) + 8, 58, CORAL["yellow"])),
            (300, lambda x: branch_coral(a, x, Y(x) + 4, 160, CORAL["pink"], 5, 1)),
            (380, lambda x: seagrass(a, x, Y(x) + 8, 62, 7, sway_cls="sway")),
            # cluster B
            (690, lambda x: soft_coral(a, x, Y(x) + 6, 96, ("#f7b26a", "#ffe0b0", "#cf7b3a"))),
            (800, lambda x: table_coral(a, x, Y(x) + 8, 210, CORAL["teal"])),
            (900, lambda x: tube_sponge(a, x, Y(x) + 6, 116, CORAL["orange"])),
            (960, lambda x: sea_whip(a, x, Y(x) + 6, 170, ("#ff7f6a", "#ffd0c4", "#c94f3f"))),
            # (meadow 1060–1200 stays open for the manatee)
            (1060, lambda x: seagrass(a, x - 40, Y(x) + 28, 58, 10, sway_cls="sway meadow")),
            (1180, lambda x: seagrass(a, x, Y(x) + 32, 52, 9, sway_cls="sway meadow")),
            # cluster C
            (1340, lambda x: fan_coral(a, x, Y(x) + 4, 230, CORAL["red"])),
            (1420, lambda x: rock(a, x, Y(x) + 18, 230, 100, crust="#c58cf0")),
            (1390, lambda x: brain_coral(a, x, Y(x) - 60, 46, CORAL["pink"])),
            (1520, lambda x: branch_coral(a, x, Y(x) + 4, 150, CORAL["violet"], 4, 2)),
            (1600, lambda x: soft_coral(a, x, Y(x) + 6, 80, ("#d58cf0", "#f6dcff", "#9a5ac0"))),
            # cluster D (wraps)
            (1880, lambda x: brain_coral(a, x, Y(x) + 6, 64, CORAL["orange"])),
            (1960, lambda x: sea_whip(a, x, Y(x) + 6, 150, ("#ffd25a", "#fff1b0", "#d6a02a"))),
            (2010, lambda x: seagrass(a, x, Y(x) + 8, 64, 6, sway_cls="sway")),
        ]
        for x, fn in items:
            out += wrap(x, 130, fn)
        out += "".join(shell(a, x, Y(x) + 40, 1.0) for x in (520, 1000, 1700))
        out += "".join(snail_shell(a, x, Y(x) + 60, 1.1) for x in (600, 1260, 1760))
        return out
    return floor_tile("utes-floor.svg", "utes", IN, yout, S_UTES, S_UTES, waves, (SAND, SAND_L, SAND_D), deco, a, "Korálový útes — dno")


def utes_far():
    a = Art("utesfar", seed=102)
    body = light_pools(a, ((300, 160, 360, 140, .16), (1200, 120, 420, 160, .14), (1800, 220, 300, 120, .12)))
    body += silhouette_reef(a, 560, [(2, 26, .3), (5, 12, 1.1)], mix(UTES[1], UTES[0], .35), .55, 5, 140, 60, 130)
    body += school_silhouette(700, 330, 22, mix(UTES[1], "#ffffff", .25), .45, 3, .9)
    body += school_silhouette(1620, 400, 16, mix(UTES[1], "#ffffff", .2), .4, 4, .7)
    body += silhouette_reef(a, 640, [(3, 18, 1.5), (7, 8, .7)], mix(UTES[2], "#1d7f96", .2), .7, 6, 170, 80, 170)
    body += haze_band(a, 470, mix(UTES[0], "#ffffff", .3), .35)
    return far_layer("utes-far.svg", "Korálový útes — daleko", body, a.defs)


def utes_mid():
    a = Art("utesmid", seed=103)
    body = ""
    rng = random.Random(9)
    tint = .42
    tc = lambda col: tuple(mix(c, UTES[2], tint) for c in col)
    band, _ = ridge_band(722, [(2, 12, .9), (6, 6, .2)], mix(SAND_D, UTES[2], .45), 1)
    body += band
    for i, x in enumerate(range(140, TW, 330)):
        xx = x + rng.uniform(-40, 40)
        y = 728 + 10 * math.sin(xx * .01)
        cols = list(CORAL.values())

        def bommie(X, y=y, i=i):
            s_ = rock(a, X, y + 10, 280, 120, col=tc((ROCK, ROCK_L, ROCK_D)), ink=True, sw=2.4)
            s_ += [lambda: branch_coral(a, X - 70, y - 90, 130, tc(cols[i % 6]), 4, i),
                   lambda: fan_coral(a, X - 60, y - 80, 170, tc(cols[(i + 2) % 6])),
                   lambda: soft_coral(a, X - 60, y - 90, 80, tc(("#f7b26a", "#ffe0b0", "#cf7b3a")))][i % 3]()
            s_ += brain_coral(a, X + 40, y - 100, 48, tc(cols[(i + 3) % 6]))
            s_ += seagrass(a, X + 110, y + 4, 60, 6, col=mix("#6aa04a", UTES[2], tint), light=mix("#9cc96e", UTES[2], tint))
            return s_
        body += wrap(xx, 170, bommie)
    soft_ink = mix("#33243a", UTES[2], .45)
    body = body.replace(INK, soft_ink)
    return doc("utes-mid.svg", TW, TH, body, [d.replace(INK, soft_ink) for d in a.defs], extra=' data-layer="mid"',
               label="Korálový útes — střední plán", cls="ponor layer")


def utes_near():
    a = Art("utesnear", seed=104)
    body = ""
    fg = lambda c: tuple(mix(x, "#1a3a4a", .32) for x in c)
    # foreground framing clumps rise only into the bottom ~20 % (faded by the engine when they overlap a tappable)
    clump1 = lambda X: grp("near-item", rock(a, X, 860, 300, 150, fg((ROCK, ROCK_L, ROCK_D))) + branch_coral(a, X - 80, 740, 190, fg(CORAL["pink"]), 6, 7)
                           + soft_coral(a, X + 70, 730, 90, fg(("#f7b26a", "#ffe0b0", "#cf7b3a"))) + seagrass(a, X + 150, 790, 110, 9, col="#3f7a3a", light="#5e9a4a", sway_cls="sway"), (X, 860))
    clump2 = lambda X: grp("near-item", fan_coral(a, X, 820, 230, fg(CORAL["violet"])) + seagrass(a, X - 110, 790, 120, 10, col="#3f7a3a", light="#5e9a4a", sway_cls="sway")
                           + brain_coral(a, X + 90, 800, 60, fg(CORAL["yellow"])), (X, 820))
    body += wrap(300, 260, clump1) + wrap(1400, 240, clump2)
    return doc("utes-near.svg", TW, TH, body, a.defs, extra=' data-layer="near"', label="Korálový útes — popředí", cls="ponor layer")


# ------------------------------------------------------------------ CHALUHY
RK_CH = ("#7d8796", "#a9b2c0", "#535c6c")


def chaluhy_floor():
    a = Art("chalfl", seed=111)
    waves = [(2, 26, 1.1), (4, 12, .2), (7, 6, 2.3)]
    yout = IN + 160

    def deco(line):
        Y = lambda x: y_at(line, x)
        out = ripples(a, line, col="#8f876f", n=26, seed=9) + pebbles(a, line, 36, 7, col=("#9aa2ae", "#7d8796", "#c3c9d2"))
        hk = lambda x, h: min(h, Y(x) - 40)          # kelp never pokes out of the tile (floor tiles are <img>)
        items = [
            (120, lambda x: rock(a, x, Y(x) + 30, 260, 130, RK_CH, crust="#e98fa6")),
            (330, lambda x: kelp(a, x, Y(x) + 6, hk(x, 600), 1, segs=4)),
            (470, lambda x: rock(a, x, Y(x) + 22, 150, 70, RK_CH, crust="#e98fa6")),
            (560, lambda x: tube_sponge(a, x, Y(x) + 8, 80, CORAL["yellow"])),
            (640, lambda x: kelp(a, x, Y(x) + 6, hk(x, 600), 2, segs=4)),
            (900, lambda x: rock(a, x, Y(x) + 34, 300, 160, RK_CH, crust="#f2a0b0")),
            (860, lambda x: zoanthids(a, x, Y(x) - 110, 7, ("#ffb37a", "#fff0d8", "#d97b3a"))),
            (1080, lambda x: kelp(a, x, Y(x) + 6, hk(x, 600), 3, segs=4)),
            (1250, lambda x: soft_coral(a, x, Y(x) + 6, 70, ("#f2a0b0", "#ffe0e6", "#c46a80"))),
            (1420, lambda x: kelp(a, x, Y(x) + 6, hk(x, 600), 4, segs=4)),
            (1560, lambda x: rock(a, x, Y(x) + 26, 200, 100, RK_CH, crust="#e98fa6")),
            (1680, lambda x: sea_whip(a, x, Y(x) + 6, 120, ("#ff9f4a", "#ffd8b0", "#cf6f2a"))),
            (1760, lambda x: kelp(a, x, Y(x) + 6, hk(x, 600), 5, segs=4)),
            (1930, lambda x: rock(a, x, Y(x) + 22, 170, 80, RK_CH)),
        ]
        for x, fn in items:
            out += wrap(x, 140, fn)
        out += "".join(snail_shell(a, x, Y(x) + 50, 1.0, "#e6d6c0") for x in (700, 1340))
        return out
    return floor_tile("chaluhy-floor.svg", "chaluhy", IN, yout, S_CHAL, S_CHAL, waves, ("#b3a98d", "#d6cdb0", "#6f6858"), deco, a,
                      "Chaluhový les — dno")


def chaluhy_far():
    a = Art("chalfar", seed=112)
    body = light_pools(a, ((420, 120, 380, 150, .14), (1450, 160, 400, 150, .12)))
    rng = random.Random(12)
    for lvl, (col, op, base, hmin, hmax, step) in enumerate(((mix(CHAL[1], CHAL[0], .35), .45, 760, 380, 560, 120),
                                                           (mix(CHAL[1], CHAL[2], .5), .7, 790, 460, 700, 170))):
        for x in range(40 + lvl * 60, TW, step):
            xx = x + rng.uniform(-20, 20)
            h = rng.uniform(hmin, hmax)
            body += wrap(xx, 70, lambda X, h=h, col=col, base=base, op=op: f'<g opacity="{op}">' + kelp(a, X, base, h, int(X) + lvl, col=(col, mix(col, CHAL[0], .15), col), ink=False, segs=3) + '</g>')
    body += ridge_band(712, [(2, 14, .4), (5, 8, 1.2)], mix(CHAL[2], "#1a4f55", .3), .85)[0]
    body += haze_band(a, 430, mix(CHAL[0], "#ffffff", .2), .3)
    return doc("chaluhy-far.svg", TW, TH, body, a.defs, extra=' data-layer="far"', label="Chaluhový les — daleko", cls="ponor layer")


def chaluhy_mid():
    a = Art("chalmid", seed=113)
    body = ""
    rng = random.Random(13)
    tint = .5
    colk = tuple(mix(c, CHAL[2], tint) for c in (KELP, KELP_L, KELP_D))
    body += ridge_band(730, [(3, 16, .9), (7, 7, .2)], mix("#5b5a52", CHAL[2], .45), 1)[0]
    for x in range(80, TW, 310):
        xx = x + rng.uniform(-40, 40)
        h = rng.uniform(520, 700)
        body += wrap(xx, 90, lambda X, h=h: kelp(a, X, 790, h, int(X) + 3, col=colk, ink=True, segs=4))
        body += wrap(xx + 120, 90, lambda X: rock(a, X, 800, 200, 90, tuple(mix(c, CHAL[2], .55) for c in RK_CH), sw=2.2))
    soft_ink = mix("#33243a", CHAL[2], .4)
    body = body.replace(INK, soft_ink)
    return doc("chaluhy-mid.svg", TW, TH, body, [d.replace(INK, soft_ink) for d in a.defs], extra=' data-layer="mid"', label="Chaluhový les — střední plán", cls="ponor layer")


def chaluhy_near():
    a = Art("chalnear", seed=114)
    colk = tuple(mix(c, "#1f3a30", .45) for c in (KELP, KELP_L, KELP_D))
    body = ""
    body += wrap(140, 200, lambda X: grp("near-item", rock(a, X + 60, 870, 300, 150, tuple(mix(c, "#1f2a30", .4) for c in RK_CH)) + kelp(a, X, 800, 430, int(X) + 9, col=colk, segs=4, lean=.6), (X, 800)))
    body += wrap(1240, 200, lambda X: grp("near-item", kelp(a, X, 800, 380, int(X) + 11, col=colk, segs=4, lean=-.5) + kelp(a, X + 70, 810, 300, int(X) + 12, col=colk, segs=3), (X, 800)))
    return doc("chaluhy-near.svg", TW, TH, body, a.defs, extra=' data-layer="near"', label="Chaluhový les — popředí", cls="ponor layer")


def kelp_single(n, h, seed):
    a = Art(f"kelp{n}", seed=seed)
    W, H = 360, h + 40
    body = kelp(a, W / 2, H - 10, h, seed, segs=5)
    return doc(f"kelp-{n}.svg", W, H, body, a.defs, extra=f' data-pivot="{f(W / 2)} {f(H - 10)}"', label="Chaluha", cls="ponor prop")


# ------------------------------------------------------------------ SIRE MORE (no floor)
def sire_floor():
    """No visible floor. A 'virtual' descent line keeps the stitch rule uniform (data-floor="none")."""
    a = Art("sirefl", seed=121)
    yout = IN + 220
    samples = ",".join(f(IN + 220 * x / TW) for x in range(0, TW + 1, 128))
    return doc("sire-more-floor.svg", TW, FH, "", a.defs,
               extra=f' data-zone="sire-more" data-floor="none" data-in="{IN}" data-out="{yout}" data-floor-y="{samples}" data-fill="none"',
               label="Širé moře — bez dna", cls="ponor floor")


def sire_far():
    a = Art("sirefar", seed=122)
    body = light_pools(a, ((1024, 0, 1000, 300, .3), (300, 40, 420, 160, .18), (1760, 60, 420, 160, .18), (420, 300, 300, 120, .1), (1640, 330, 320, 120, .1)))
    far = mix(SIRE[1], SIRE[2], .35)
    farther = mix(SIRE[0], SIRE[1], .5)
    # distant humpback (proper silhouette from the keporkak outline), manta, dolphin pod, bait ball — hazy, no ink
    hp = [(412, 96), (400, 80), (370, 68), (330, 60), (270, 54), (210, 54), (176, 50), (160, 54), (120, 68), (80, 86), (64, 94),
          (66, 106), (110, 118), (170, 138), (240, 154), (300, 154), (360, 138), (398, 116)]
    k_, ox, oy = 1.7, 180, 220
    T = lambda pts: [(ox + x * k_, oy + y * k_) for x, y in pts]
    body += f'<path d="{smooth(T(hp), t=.17)}" fill="{far}" opacity=".42"/>'
    body += f'<path d="{smooth(T([(70, 94), (42, 74), (12, 58), (20, 80), (14, 100), (20, 128), (12, 146), (44, 124), (70, 104)]), t=.15)}" fill="{far}" opacity=".42"/>'
    body += f'<path d="{smooth(T([(310, 130), (290, 150), (256, 172), (220, 192), (184, 206), (174, 200), (194, 180), (230, 160), (266, 140), (290, 126)]), t=.18)}" fill="{mix(far, "#ffffff", .25)}" opacity=".42"/>'
    manta = f"M1500 300q60 -50 120 -20q40 10 70 0q-30 30 -70 30q-60 40 -120 -10z"
    body += f'<path d="{manta}" fill="{farther}" opacity=".45"/><path d="M1500 300l-60 8" stroke="{farther}" stroke-width="3" opacity=".45"/>'
    for k, (x, y) in enumerate(((1180, 220), (1250, 200), (1320, 232))):
        body += f'<path d="M{x} {y}q30 -18 64 -4l10 -12l0 18q-8 10 -28 10q-30 2 -46 -12z" fill="{farther}" opacity=".4"/>'
    rng = random.Random(22)
    for k in range(160):
        t = k / 160 * 6.28 * 2
        r = 70 + 40 * math.sin(t * 1.7)
        x = 1460 + r * math.cos(t) * 2.2 + rng.uniform(-14, 14)
        y = 520 + r * math.sin(t) + rng.uniform(-10, 10)
        body += f'<path d="M{f(x)} {f(y)}l10 -3l0 6z" fill="{mix(SIRE[0], "#ffffff", .25)}" opacity=".45"/>'
    body += school_silhouette(560, 250, 18, mix(SIRE[0], "#ffffff", .15), .35, 9, .8)
    g = a.linear("dp", [(0, SIRE[2], 0), (1, SIRE[2], .55)], 0, 420, 0, TH)
    body += f'<rect x="0" y="420" width="{TW}" height="{TH - 420}" fill="{g}"/>'
    return doc("sire-more-far.svg", TW, TH, body, a.defs, extra=' data-layer="far"', label="Širé moře — daleko", cls="ponor layer")


def sire_mid():
    a = Art("siremid", seed=123)
    rng = random.Random(23)
    body = ""
    for _ in range(110):
        x, y, r = rng.uniform(0, TW), rng.uniform(40, TH - 40), rng.uniform(1.5, 4.5)
        body += wrap(x, 6, lambda X, y=y, r=r: f'<circle cx="{f(X)}" cy="{f(y)}" r="{f(r)}" fill="#e6f6ff" opacity="{f(.25 + r * .05)}"/>')
    # tiny far jellies (hazy, no faces — scenery, not tappable) + two small far schools
    for x, y, s in ((380, 300, 1.0), (1180, 560, .8), (1760, 200, .9)):
        body += wrap(x, 30, lambda X, y=y, s=s: f'<path d="M{f(X - 16 * s)} {f(y)}q{f(16 * s)} {f(-22 * s)} {f(32 * s)} 0z" fill="#e9e0ff" opacity=".6"/>'
                     + "".join(f'<path d="M{f(X - 10 * s + k * 7 * s)} {f(y)}q{f(3 * s)} {f(12 * s)} 0 {f(24 * s)}" fill="none" stroke="#e9e0ff" stroke-width="1.6" opacity=".4"/>' for k in range(4)))
    body += (school_silhouette(900, 180, 16, "#cfe8f8", .5, 11, .7) + school_silhouette(1600, 640, 14, "#cfe8f8", .45, 12, .6)
             + school_silhouette(300, 520, 14, "#cfe8f8", .45, 13, .65) + school_silhouette(1350, 330, 12, "#cfe8f8", .4, 14, .5))
    return doc("sire-more-mid.svg", TW, TH, body, a.defs, extra=' data-layer="mid"', label="Širé moře — plankton", cls="ponor layer")


def sire_near():
    a = Art("sirenear", seed=124)
    rng = random.Random(24)
    halo = a.radial("bk", [(0, "#ffffff", .35), (.7, "#ffffff", .12), (1, "#ffffff", 0)], cx="50%", cy="50%", r="50%")
    body = ""
    for _ in range(11):
        x, y, r = rng.uniform(0, TW), rng.uniform(40, 330), rng.uniform(14, 38)
        body += wrap(x, r, lambda X, y=y, r=r: f'<circle cx="{f(X)}" cy="{f(y)}" r="{f(r)}" fill="{halo}"/>')
    return doc("sire-more-near.svg", TW, TH, body, a.defs, extra=' data-layer="near"', label="Širé moře — popředí", cls="ponor layer")


# ------------------------------------------------------------------ HLUBINY
OOZE = ("#3a3f6a", "#555c8f", "#1a1d3a")


def hlubiny_floor():
    a = Art("deepfl", seed=131)
    waves = [(2, 20, .5), (5, 8, 1.9)]
    yout = IN + 90

    def deco(line):
        Y = lambda x: y_at(line, x)
        out, glows = "", ""
        rng = random.Random(31)
        out += pebbles(a, line, 22, 9, col=("#4a507e", "#3a3f6a", "#5f668f"))
        for x in (180, 560, 940, 1300, 1700):
            o, g = sea_pen(a, x, Y(x) + 8, rng.uniform(100, 150))
            out += o
            glows += g
        for x in (330, 1110, 1520):
            out += glass_sponge(a, x, Y(x) + 10, 140)
        for x in (760, 1880):
            b, g = bamboo_coral(a, x, Y(x) + 8, 170, x)
            out += b
            glows += g
        for x in (450, 1220, 1960):
            b, g = sea_lily(a, x, Y(x) + 10, 120)
            out += b
            glows += g
        for x in (640, 1820):
            out += rock(a, x, Y(x) + 26, 220, 90, ("#3a3f66", "#565c8a", "#22264a"))
        for _ in range(60):
            x = rng.uniform(0, TW)
            y = Y(x) + rng.uniform(6, 70)
            glows += f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(rng.uniform(1.5, 3))}" fill="{rng.choice((GLOW_C, GLOW_V, GLOW_G))}" opacity=".85"/>'
        return out + grp("glow", glows, (TW / 2, IN))
    return floor_tile("hlubiny-floor.svg", "hlubiny", IN, yout, S_DEEP, S_DEEP, waves, OOZE, deco, a, "Hlubiny — dno",
                      grain=("#6a72a8", "#22264a", "#8a92c8"), lip="#6f78b0")


def hlubiny_far():
    a = Art("deepfar", seed=132)
    rng = random.Random(32)
    body = ""
    # far bioluminescent life: siphonophore chains, comb-jelly ovals, lantern-dot rows (all faint, no faces)
    for x, y, L in ((300, 220, 260), (1300, 140, 300), (1800, 420, 220)):
        pts = [(x + i * L / 14, y + 26 * math.sin(i * .6)) for i in range(15)]
        body += f'<path d="M{" L".join(f"{f(px)} {f(py)}" for px, py in pts)}" fill="none" stroke="{GLOW_C}" stroke-width="1.4" opacity=".25"/>'
        body += "".join(f'<circle cx="{f(px)}" cy="{f(py)}" r="3" fill="{GLOW_C}" opacity=".55"/><circle cx="{f(px)}" cy="{f(py)}" r="9" fill="{GLOW_C}" opacity=".12"/>' for px, py in pts[::2])
    for x, y in ((760, 330), (1560, 260), (120, 470)):
        body += (f'<ellipse cx="{x}" cy="{y}" rx="18" ry="26" fill="{GLOW_V}" opacity=".12" stroke="{GLOW_V}" stroke-width="1.4" stroke-opacity=".4"/>'
                 + "".join(f'<path d="M{x - 14 + k * 9} {y - 20}q2 20 0 40" fill="none" stroke="{["#9dffc8", "#6ff3ff", "#b9a1ff", "#ffb8f0"][k]}" stroke-width="1.6" opacity=".55"/>' for k in range(4)))
    for _ in range(80):
        x, y, r = rng.uniform(0, TW), rng.uniform(30, TH - 60), rng.uniform(3, 8)
        col = rng.choice((GLOW_C, GLOW_V, GLOW_G))
        body += wrap(x, r, lambda X, y=y, r=r, col=col: f'<circle cx="{f(X)}" cy="{f(y)}" r="{f(r)}" fill="{col}" opacity=".14"/><circle cx="{f(X)}" cy="{f(y)}" r="{f(r * .3)}" fill="{col}" opacity=".6"/>')
    body += ridge_band(690, [(2, 22, .1), (5, 10, 1.7)], "#0e1a38", .9)[0]
    return doc("hlubiny-far.svg", TW, TH, f'<g class="glow">{body}</g>', a.defs, extra=' data-layer="far"', label="Hlubiny — daleko", cls="ponor layer")


def hlubiny_mid():
    a = Art("deepmid", seed=133)
    rng = random.Random(33)
    body = ridge_band(720, [(3, 26, .6), (8, 9, 1.4)], "#141c3e", 1)[0]
    glow = ""
    for x in range(120, TW, 300):
        xx = x + rng.uniform(-50, 50)
        h = rng.uniform(160, 280)
        sp = smooth([(xx - 70, 760), (xx - 36, 760 - h * .6), (xx - 12, 760 - h), (xx + 16, 760 - h * .95), (xx + 40, 760 - h * .5), (xx + 80, 760)], t=.18)
        body += wrap(xx, 90, lambda X, sp=sp, xx=xx: f'<path d="{sp}" fill="#1b2550" transform="translate({f(X - xx)} 0)"/>'
                     f'<path d="{sp}" fill="none" stroke="#2c3a72" stroke-width="3" transform="translate({f(X - xx)} 0)"/>')
        for k in range(4):
            gx, gy = xx + rng.uniform(-30, 30), 760 - h * rng.uniform(.25, .9)
            col = rng.choice((GLOW_C, GLOW_V))
            glow += wrap(gx, 10, lambda X, gy=gy, col=col: f'<circle cx="{f(X)}" cy="{f(gy)}" r="4.5" fill="{col}" opacity=".75"/><circle cx="{f(X)}" cy="{f(gy)}" r="13" fill="{col}" opacity=".15"/>')
    return doc("hlubiny-mid.svg", TW, TH, body + grp("glow", glow), a.defs, extra=' data-layer="mid"', label="Hlubiny — střední plán", cls="ponor layer")


def hlubiny_near():
    a = Art("deepnear", seed=134)
    body = ""
    for x, w in ((200, 380), (1300, 440)):
        def item(X, w=w):
            b, g = bamboo_coral(a, X + w * .25, 700, 160, int(X))
            return grp("near-item", rock(a, X, 820, w, 180, ("#0d1430", "#1c2550", "#060a1c"), ink=False) + b + grp("glow", g), (X, 820))
        body += wrap(x, w / 2, item)
    return doc("hlubiny-near.svg", TW, TH, body, a.defs, extra=' data-layer="near"', label="Hlubiny — popředí", cls="ponor layer")


# ------------------------------------------------------------------ transitions (floor plane)
def trans_utes_chaluhy():
    a = Art("tuc", seed=141)
    yin, yout = IN, IN + 260
    waves = [(3, 14, .3), (6, 7, 1.0)]

    def deco(line):
        Y = lambda x: y_at(line, x)
        out = ripples(a, line[:30], n=14, seed=5) + pebbles(a, line, 26, 11)
        out += wrap(220, 100, lambda X: brain_coral(a, X, Y(X) + 6, 56, CORAL["yellow"]))
        out += wrap(420, 100, lambda X: branch_coral(a, X, Y(X) + 4, 120, CORAL["pink"], 4, 4))
        out += fan_coral(a, 600, Y(600) + 4, 170, CORAL["violet"])
        out += rock(a, 900, Y(900) + 40, 340, 170, RK_CH, crust="#e98fa6")
        out += kelp(a, 1180, Y(1180) + 6, min(480, Y(1180) - 40), 11, segs=4)
        out += rock(a, 1420, Y(1420) + 26, 200, 100, RK_CH)
        out += kelp(a, 1650, Y(1650) + 6, min(560, Y(1650) - 40), 12, segs=4)
        out += kelp(a, 1900, Y(1900) + 6, min(520, Y(1900) - 40), 13, segs=4)
        return out

    def under(line):
        g = a.linear("sr", [(0, SAND, 1), (.45, SAND, 1), (.75, "#b3a98d", 1), (1, "#b3a98d", 1)], 0, 0, TW, 0)
        d = "M" + " L".join(f"{f(x)} {f(y)}" for x, y in line) + f" L{TW} {FH} L0 {FH}Z"
        return f'<path d="{d}" fill="{g}" opacity=".85"/>'
    return floor_tile("trans-utes-chaluhy.svg", "utes/chaluhy", yin, yout, S_UTES, S_CHAL, waves, (SAND, SAND_L, "#6f6858"), deco, a,
                      "Přechod útes → chaluhy", under=under)


def trans_chaluhy_sire():
    """The drop-off: the rocky floor ends in a cliff that falls away into the blue. Tile is 2048 x 2048."""
    a = Art("tcs", seed=142)
    H = 2048
    yin = IN
    yout = IN + 420
    pts = []
    for x in range(0, TW + 1, 32):
        if x < 1000:
            y = floor_y(x, yin, yin + 160, S_CHAL, S_CHAL, [(2, 10, .3)], W=1000)
        else:
            t = (x - 1000) / 400
            y = yin + 160 + (H - yin - 160) * (min(1, t) ** 1.6) + (x - 1400) * 3 if x > 1400 else yin + 160 + (H - yin - 160) * (t ** 1.6)
        pts.append((x, min(H + 40, y)))
    pts = [p for p in pts if p[1] <= H + 40]
    d = "M" + " L".join(f"{f(x)} {f(y)}" for x, y in pts) + f" L{f(pts[-1][0])} {H} L0 {H}Z"
    rockg = a.linear("cl", [(0, "#c9bfa4"), (.06, "#9a937e"), (.5, "#4f5260"), (1, "#20304a")], 0, IN, 0, H)
    body = f'<path d="{d}" fill="{rockg}"/>'
    cl = a.clip("wall", d)
    wall = ""
    rng = random.Random(42)
    for k in range(18):
        y = IN + 220 + k * 70
        wall += f'<path d="M{f(600 + k * 8)} {f(y)}Q{f(900)} {f(y - 10)} {f(1060 + k * 14)} {f(y + 6)}" fill="none" stroke="#2f3446" stroke-width="3" opacity="{f(max(.1, .6 - k * .03))}"/>'
    for k in range(40):
        x, y = rng.uniform(820, 1250), rng.uniform(IN + 200, IN + 900)
        wall += f'<ellipse cx="{f(x)}" cy="{f(y)}" rx="{f(rng.uniform(6, 14))}" ry="{f(rng.uniform(3, 6))}" fill="{rng.choice(("#e98fa6", "#ffd25a", "#c58cf0"))}" opacity="{f(max(.15, .8 - (y - IN) / 1200))}"/>'
    body += f'<g clip-path="{cl}">{wall}</g>'
    body += f'<path d="M{" L".join(f"{f(x)} {f(y)}" for x, y in pts)}" fill="none" stroke="{INK}" stroke-width="3" stroke-linejoin="round"/>'
    fy = lambda x: floor_y(x, yin, yin + 160, S_CHAL, S_CHAL, [(2, 10, .3)], W=1000)
    body += kelp(a, 260, fy(260) + 6, min(560, fy(260) - 40), 21, segs=4)
    body += kelp(a, 620, fy(620) + 6, min(480, fy(620) - 40), 22, segs=4)
    body += rock(a, 860, yin + 160 + 30, 220, 110, RK_CH, crust="#e98fa6")
    body += sea_whip(a, 960, yin + 180, 120, ("#ff9f4a", "#ffd8b0", "#cf6f2a"))
    fade = a.linear("fd", [(0, SIRE[2], 0), (1, SIRE[2], 1)], 0, H - 700, 0, H)
    body += f'<rect x="0" y="{H - 700}" width="{TW}" height="700" fill="{fade}"/>'
    samples = ",".join(f(yin + (yout - yin) * x / TW) for x in range(0, TW + 1, 128))
    return doc("trans-chaluhy-sire-more.svg", TW, H, body, a.defs,
               extra=f' data-zone="chaluhy/sire-more" data-in="{yin}" data-out="{yout}" data-floor-y="{samples}" data-floor-visible-until="1000" data-fill="none"',
               label="Přechod chaluhy → širé moře (útesová stěna)", cls="ponor floor")


def trans_sire_hlubiny():
    """The floor of the deep rises into view from below. Left part: no floor (virtual line)."""
    a = Art("tsh", seed=143)
    H = 1536
    yin, yout = IN, IN + 120
    pts = []
    for x in range(0, TW + 1, 32):
        t = x / TW
        y = H + 60 - (H + 60 - yout) * (max(0, (t - .3) / .7) ** .7)
        y += 10 * math.sin(x * .006) * (t > .3)
        pts.append((x, y))
    d = "M" + " L".join(f"{f(x)} {f(y)}" for x, y in pts) + f" L{TW} {H} L0 {H}Z"
    g = a.linear("oz", [(0, OOZE[1]), (.1, OOZE[0]), (1, OOZE[2])], 0, yout, 0, H)
    body = f'<path d="{d}" fill="{g}"/><path d="M{" L".join(f"{f(x)} {f(y)}" for x, y in pts)}" fill="none" stroke="#6f78b0" stroke-width="3"/>'
    body += glass_sponge(a, 1600, pts[50][1] + 10, 130)
    o, gl = sea_pen(a, 1880, pts[59][1] + 8, 110)
    b2, g2 = sea_lily(a, 1740, pts[54][1] + 10, 110)
    body += o + b2 + grp("glow", gl + g2)
    samples = ",".join(f(min(y_ for x_, y_ in pts if abs(x_ - x) < 17) if x / TW > .55 else yin + (yout - yin) * x / TW) for x in range(0, TW + 1, 128))
    return doc("trans-sire-more-hlubiny.svg", TW, H, body, a.defs,
               extra=f' data-zone="sire-more/hlubiny" data-in="{yin}" data-out="{yout}" data-floor-y="{samples}" data-fill="{OOZE[2]}"',
               label="Přechod širé moře → hlubiny", cls="ponor floor")


# ================================================================== overlays + particles
def surface_under():
    """Underside of the surface (the bright wobbling ceiling), seamless 2048 x 220. Place y=110 at world y 0."""
    a = Art("surf", seed=151)
    g = a.linear("su", [(0, "#ffffff", .95), (.5, "#e9fbff", .7), (1, "#e9fbff", 0)], 0, 60, 0, 220)
    pts = [(x, 110 + 10 * math.sin(2 * math.pi * 8 * x / TW) + 5 * math.sin(2 * math.pi * 19 * x / TW + 1)) for x in range(0, TW + 1, 16)]
    d = f"M0 0L{TW} 0L" + " L".join(f"{f(x)} {f(y)}" for x, y in reversed(pts)) + "Z"
    body = f'<rect x="0" y="0" width="{TW}" height="220" fill="{g}"/><path d="{d}" fill="#d3f4ff" opacity=".85"/>'
    body += f'<path d="M{" L".join(f"{f(x)} {f(y)}" for x, y in pts)}" fill="none" stroke="#ffffff" stroke-width="4" opacity=".9"/>'
    # Snell-window glints
    rng = random.Random(51)
    for _ in range(40):
        x = rng.uniform(0, TW)
        y = rng.uniform(116, 170)
        w = rng.uniform(20, 60)
        body += f'<path d="M{f(x)} {f(y)}q{f(w / 2)} -6 {f(w)} 0" fill="none" stroke="#ffffff" stroke-width="3" stroke-linecap="round" opacity=".55"/>'
    return doc("surface-under.svg", TW, 220, body, a.defs, extra=' data-surface-y="110"', label="Hladina zespodu", cls="ponor overlay")


def rays():
    a = Art("rays", seed=152)
    W, H = 1024, 768
    body = ""
    for i, (x, w, ang, op) in enumerate(((120, 70, -14, .5), (300, 120, -10, .4), (520, 60, -6, .55), (700, 140, -4, .35), (900, 80, 2, .45))):
        g = a.linear("r", [(0, "#fffce1", op), (1, "#fffce1", 0)], 0, 0, 0, H)
        x2 = x + math.tan(math.radians(ang)) * H * -1
        body += grp(f"ray ray-{i}", f'<path d="M{f(x - w / 2)} -10L{f(x + w / 2)} -10L{f(x2 + w)} {H}L{f(x2 - w * .6)} {H}Z" fill="{g}"/>', (x, 0))
    return doc("rays.svg", W, H, body, a.defs, extra=' data-overlay="screen"', label="Sluneční paprsky", cls="ponor overlay")


def caustics():
    """v2: a thin, organic light net (seamless 512 tile), drawn faint so the engine's .32 strip stays gentle."""
    a = Art("caus", seed=153)
    S = 512
    rng = random.Random(53)
    N = 7
    P = [[((i + .5) * S / N + rng.uniform(-22, 22), (j + .5) * S / N + rng.uniform(-22, 22)) for j in range(N)] for i in range(N)]
    get = lambda i, j: (P[i % N][j % N][0] + (i // N) * S, P[i % N][j % N][1] + (j // N) * S)
    segs = []
    for i in range(-1, N + 1):
        for j in range(-1, N + 1):
            for di, dj in ((1, 0), (0, 1), (1, 1)):
                if (di, dj) == (1, 1) and rng.random() < .55:
                    continue
                (x0, y0), (x1, y1) = get(i, j), get(i + di, j + dj)
                mx, my = (x0 + x1) / 2 + rng.uniform(-10, 10), (y0 + y1) / 2 + rng.uniform(-10, 10)
                w = rng.uniform(1.6, 3.4)
                segs.append(f'<path d="M{f(x0)} {f(y0)}Q{f(mx)} {f(my)} {f(x1)} {f(y1)}" fill="none" stroke="#fffff0" stroke-width="{f(w)}" stroke-linecap="round"/>')
    body = f'<g opacity=".42">{"".join(segs)}</g>'
    return doc("caustics.svg", S, S, body, a.defs, extra=' data-tile="512"', label="Kaustiky", cls="ponor overlay")


def particles():
    a = Art("part", seed=154)
    hb = a.radial("bub", [(0, "#ffffff", .05), (.7, "#e6faff", .25), (.92, "#ffffff", .9), (1, "#ffffff", .2)], cx="50%", cy="50%", r="50%")
    bubble = (f'<circle cx="32" cy="32" r="28" fill="{hb}" stroke="#ffffff" stroke-width="2.5" stroke-opacity=".9"/>'
              f'<path d="M18 22Q22 14 30 12" fill="none" stroke="#ffffff" stroke-width="4" stroke-linecap="round"/>'
              f'<circle cx="42" cy="44" r="3" fill="#ffffff" opacity=".7"/>')
    doc("bubble.svg", 64, 64, bubble, a.defs, label="Bublinka", cls="ponor particle")
    a2 = Art("plk", seed=155)
    pl = ('<circle cx="8" cy="8" r="2.4" fill="#e9fff4" opacity=".9"/><circle cx="16" cy="12" r="1.6" fill="#fff8d0" opacity=".8"/>'
          '<path d="M20 5l3 2l-3 2z" fill="#d8fff0" opacity=".8"/><circle cx="12" cy="18" r="1.2" fill="#ffffff" opacity=".7"/>')
    doc("plankton.svg", 26, 24, pl, a2.defs, label="Plankton", cls="ponor particle")
    a3 = Art("snow", seed=156)
    sn = ('<path d="M6 10q3 -5 7 -2q4 -4 7 1q2 4 -3 5q-3 3 -7 0q-5 0 -4 -4z" fill="#dce6ff" opacity=".75"/>'
          '<circle cx="24" cy="6" r="1.8" fill="#e8eeff" opacity=".7"/><circle cx="20" cy="20" r="1.3" fill="#e8eeff" opacity=".6"/>')
    doc("snow.svg", 30, 26, sn, a3.defs, label="Mořský sníh", cls="ponor particle")


def school_fish():
    a = Art("hejno", seed=157)
    from svgkit import eye as eye_
    body_d = smooth([(58, 14), (50, 8), (34, 5), (18, 8), (10, 13), (18, 19), (34, 22), (50, 20)], t=.18)
    g = a.linear("sf", [(0, "#5a8fd0"), (.45, "#cfe4f6"), (1, "#f4f9ff")], 0, 5, 0, 22)
    body = (f'<path d="M12 13L2 4L4 13L2 22Z" fill="#ffd25a" stroke="{INK}" stroke-width="1.6" stroke-linejoin="round"/>'
            f'<path d="{body_d}" fill="{g}" stroke="{INK}" stroke-width="1.8"/>'
            f'<path d="M14 13Q34 11 54 13" fill="none" stroke="#ffd25a" stroke-width="2.6" stroke-linecap="round"/>'
            + eye_(48, 11, 2.8, look=(.25, 0), sw=1))
    return doc("school-fish.svg", 60, 27, f'<g class="body" data-pivot="30 13">{body}</g>', a.defs, extra=' data-pivot="30 13"',
               label="Rybka z hejna", cls="ponor particle")


# ================================================================== trash
def trash():
    out = {}
    # bottle: clear plastic, blue-green tint, cap, a soft label band (no brand)
    a = Art("lahev", seed=161)
    d = smooth([(30, 40), (30, 30), (40, 24), (44, 14), (56, 14), (60, 24), (70, 30), (70, 40), (72, 120), (66, 132), (34, 132), (28, 120)], t=.14)
    g = a.linear("pl", [(0, "#d8fbff", .9), (.5, "#9fe0e8", .7), (1, "#5bb7c6", .8)], 28, 0, 72, 0)
    body = (f'<path d="{d}" fill="{g}"/><path d="M36 50L36 118" stroke="#ffffff" stroke-width="5" stroke-linecap="round" opacity=".8"/>'
            f'<rect x="29" y="66" width="42" height="26" fill="#ffffff" opacity=".55"/>'
            f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="3" stroke-linejoin="round"/>'
            f'<rect x="42" y="4" width="16" height="12" rx="3" fill="#4f8fdc" stroke="{INK}" stroke-width="2.6"/>')
    out["lahev"] = (a, 100, 140, f'<g transform="rotate(-62 50 70)">{body}</g>', "Plastová lahev")
    # bag: a white-grey plastic bag with handles, drifting (looks a bit like a jellyfish — that is the lesson)
    a = Art("sacek", seed=162)
    d = smooth([(24, 40), (20, 20), (34, 12), (40, 30), (60, 30), (66, 12), (80, 20), (76, 40), (84, 96), (70, 108), (58, 100), (50, 112), (40, 100), (28, 108), (16, 96)], t=.15)
    g = a.linear("bg", [(0, "#ffffff", .9), (1, "#dfe6ee", .75)], 0, 10, 0, 110)
    body = (f'<path d="{d}" fill="{g}"/><path d="M34 48Q50 60 66 48M30 70Q52 82 74 68" fill="none" stroke="#c4ccd8" stroke-width="2.4"/>'
            f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="2.8" stroke-linejoin="round"/>')
    out["sacek"] = (a, 100, 120, body, "Igelitový sáček")
    # can: silver + plain red band, dented, no brand
    a = Art("plech", seed=163)
    g = a.linear("cn", [(0, "#9aa3b0"), (.3, "#eef2f6"), (.7, "#b9c2ce"), (1, "#7e8796")], 30, 0, 70, 0)
    body = (f'<path d="M30 20L70 20L70 104L30 104Z" fill="{g}"/><path d="M30 46L70 46L70 80L30 80Z" fill="#e0604f"/>'
            f'<path d="M30 54L70 60M30 72L70 70" stroke="#ffffff" stroke-width="3" opacity=".6"/>'
            f'<path d="M30 20L70 20L70 104L30 104Z" fill="none" stroke="{INK}" stroke-width="3" stroke-linejoin="round"/>'
            f'<ellipse cx="50" cy="20" rx="20" ry="6" fill="#d8dee6" stroke="{INK}" stroke-width="2.6"/>'
            f'<path d="M60 86l8 6" stroke="{INK}" stroke-width="2" opacity=".6"/>')
    out["plechovka"] = (a, 100, 120, f'<g transform="rotate(72 50 62)">{body}</g>', "Plechovka")
    # ghost net: a tangle of rope + mesh, orange/green
    a = Art("sit", seed=164)
    mesh = a.pattern("ms", 14, 14, '<path d="M0 7L7 0L14 7L7 14Z" fill="none" stroke="#2f8f6c" stroke-width="2"/>')
    d = smooth([(10, 50), (30, 20), (70, 14), (110, 26), (126, 60), (110, 92), (66, 100), (24, 88)], t=.18)
    body = (f'<path d="{d}" fill="{mesh}"/><path d="{d}" fill="none" stroke="{INK}" stroke-width="2" stroke-dasharray="6 5" opacity=".6"/>'
            f'<path d="M6 60Q40 30 80 44Q120 58 132 34" fill="none" stroke="{INK}" stroke-width="9" stroke-linecap="round"/>'
            f'<path d="M6 60Q40 30 80 44Q120 58 132 34" fill="none" stroke="#f2a33a" stroke-width="5" stroke-linecap="round"/>'
            f'<path d="M20 90Q60 70 100 96" fill="none" stroke="{INK}" stroke-width="8" stroke-linecap="round"/>'
            f'<path d="M20 90Q60 70 100 96" fill="none" stroke="#f2a33a" stroke-width="4" stroke-linecap="round"/>'
            f'<circle cx="34" cy="34" r="8" fill="#ffd25a" stroke="{INK}" stroke-width="2.4"/>')
    out["sit"] = (a, 140, 110, body, "Kus rybářské sítě")
    for tid, (a, w, h, body, label) in out.items():
        s = (f'<svg xmlns="http://www.w3.org/2000/svg" class="trash" data-id="{tid}" viewBox="0 0 {w} {h}" data-pivot="{w // 2} {h // 2}" '
             f'role="img" aria-label="{label}"><title>{label}</title><defs>{"".join(a.defs)}</defs><g class="body" data-pivot="{w // 2} {h // 2}">{body}</g>'
             f'<g class="anchors" fill="none" stroke="none"><circle class="anchor-center" cx="{w // 2}" cy="{h // 2}" r="4"/></g></svg>\n')
        with open(os.path.join(ART, f"trash-{tid}.svg"), "w") as fh:
            fh.write(s)


# ================================================================== cleanup patches (g.bright under g.dull)
def patches():
    # utes: coral cluster
    W, H = 520, 300
    a = Art("pu", seed=171)
    y = 280

    def cluster(dk):
        col = (lambda c: tuple(dull(x) for x in c)) if dk else (lambda c: c)
        return (rock(a, 250, y, 300, 90, col((ROCK, ROCK_L, ROCK_D))) + branch_coral(a, 140, y - 10, 170, col(CORAL["pink"]), 5, 3) +
                fan_coral(a, 400, y - 6, 200, col(CORAL["violet"])) + brain_coral(a, 270, y - 60, 62, col(CORAL["yellow"])) +
                tube_sponge(a, 330, y - 30, 90, col(CORAL["orange"])) + seagrass(a, 60, y, 70, 6) + seagrass(a, 470, y, 60, 5))
    body = grp("bright", cluster(False)) + grp("dull", cluster(True))
    doc("patch-utes.svg", W, H, body, a.defs, extra=' data-floor="280" data-pivot="260 280"', label="Korály po úklidu", cls="ponor patch")
    # chaluhy: rock with pink coralline, sponges, anemone-like tufts
    a = Art("pc", seed=172)
    RK = ("#7d8796", "#a9b2c0", "#535c6c")

    def rockset(dk):
        col = (lambda c: tuple(dull(x) for x in c)) if dk else (lambda c: c)
        out = rock(a, 260, y, 360, 150, col(RK)) + tube_sponge(a, 150, y - 40, 90, col(CORAL["yellow"])) + tube_sponge(a, 360, y - 70, 70, col(CORAL["red"]))
        out += "".join(f'<ellipse cx="{f(x)}" cy="{f(yy)}" rx="12" ry="6" fill="{dull("#e98fa6") if dk else "#e98fa6"}" stroke="{INK}" stroke-width="1.4"/>'
                       for x, yy in ((210, y - 110), (290, y - 124), (330, y - 96), (240, y - 70)))
        return out
    body = grp("bright", rockset(False)) + grp("dull", rockset(True))
    doc("patch-chaluhy.svg", W, H, body, a.defs, extra=' data-floor="280" data-pivot="260 280"', label="Skála po úklidu", cls="ponor patch")
    # hlubiny: sea pens that glow again after cleanup (g.dull = unlit)
    a = Art("ph", seed=173)
    lit, unlit = "", ""
    for x, h in ((120, 120), (220, 160), (330, 130), (420, 110)):
        o, g = sea_pen(a, x, y, h)
        lit += o + g
        unlit += o.replace("#f3d6a0", "#6a6a80").replace("#d8c9a8", "#5a5a70")
    lit += glass_sponge(a, 270, y + 4, 100)
    unlit += glass_sponge(a, 270, y + 4, 100)
    body = grp("bright", lit) + grp("dull", unlit)
    doc("patch-hlubiny.svg", W, H, body, a.defs, extra=' data-floor="280" data-pivot="260 280"', label="Světélkující péra po úklidu", cls="ponor patch")


if __name__ == "__main__":
    os.makedirs(PON, exist_ok=True)
    for fn in (utes_floor, utes_far, utes_mid, utes_near, chaluhy_floor, chaluhy_far, chaluhy_mid, chaluhy_near,
               sire_floor, sire_far, sire_mid, sire_near, hlubiny_floor, hlubiny_far, hlubiny_mid, hlubiny_near,
               trans_utes_chaluhy, trans_chaluhy_sire, trans_sire_hlubiny, surface_under, rays, caustics, particles, school_fish,
               trash, patches):
        fn()
    for n, h, s_ in ((1, 640, 201), (2, 760, 202), (3, 560, 203)):
        kelp_single(n, h, s_)
    print("sea ok:", sorted(os.listdir(PON)))
