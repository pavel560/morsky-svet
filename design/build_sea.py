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


# ================================================================== scenery kit

def rock(a, x, y, w, h, col=(ROCK, ROCK_L, ROCK_D), ink=True, sw=3):
    pts = ellipse_pts(x, y - h * .45, w / 2, h * .55, n=11, wob=lambda t: .08 * math.sin(3 * t + x * .01) + .05 * math.sin(5 * t))
    pts = [(px, min(py, y)) for px, py in pts]
    d = smooth(a.jit(pts, w * .01), t=.18)
    c, l, dk = col
    return a.shape(d, c, l, dk, y - h, y, sw=sw if ink else 0, hi_box=(x - w * .12, y - h * .7, w * .22, h * .14), shade=ink)


def brain_coral(a, x, y, r, col):
    c, l, dk = col
    d = smooth(ellipse_pts(x, y - r * .45, r, r * .62, n=14, wob=lambda t: .04 * math.sin(4 * t)), t=.18)
    d = smooth([(px, min(py, y)) for px, py in ellipse_pts(x, y - r * .45, r, r * .62, n=14, wob=lambda t: .04 * math.sin(4 * t))], t=.18)
    out = a.shape(d, c, l, dk, y - r * 1.1, y, hi_box=(x - r * .3, y - r * .8, r * .4, r * .16))
    cl = a.clip("bc", d)
    lines = []
    for k in range(5):
        yy = y - r * .2 - k * r * .17
        pts = [(x - r + i * r / 6, yy + math.sin(i * 1.7 + k) * r * .07) for i in range(13)]
        lines.append(smooth(pts, closed=False))
    out += f'<g clip-path="{cl}">' + "".join(f'<path d="{p}" fill="none" stroke="{dk}" stroke-width="{f(r * .045)}" stroke-linecap="round" opacity=".8"/>' for p in lines) + "</g>"
    return out


def branch_coral(a, x, y, h, col, n=5, seed=0):
    c, l, dk = col
    rng = random.Random(seed + int(x))
    out_ink, out_col, out_hi = [], [], []

    def br(x0, y0, ang, L, w, depth):
        x1 = x0 + math.cos(ang) * L
        y1 = y0 - math.sin(ang) * L
        mx = (x0 + x1) / 2 + rng.uniform(-L * .12, L * .12)
        my = (y0 + y1) / 2
        d = f"M{f(x0)} {f(y0)}Q{f(mx)} {f(my)} {f(x1)} {f(y1)}"
        out_ink.append(f'<path d="{d}" stroke="{INK}" stroke-width="{f(w + 5)}" stroke-linecap="round" fill="none"/>')
        out_col.append(f'<path d="{d}" stroke="{c}" stroke-width="{f(w)}" stroke-linecap="round" fill="none"/>')
        out_hi.append(f'<path d="{d}" stroke="{l}" stroke-width="{f(w * .3)}" stroke-linecap="round" fill="none" transform="translate({f(-w * .18)} 0)" opacity=".8"/>')
        if depth > 0:
            for da in (-.45, .4):
                br(x1, y1, ang + da + rng.uniform(-.15, .15), L * .72, w * .78, depth - 1)
        else:
            out_hi.append(f'<circle cx="{f(x1)}" cy="{f(y1)}" r="{f(w * .42)}" fill="{l}"/>')
    for i in range(n):
        ang = math.radians(90 + (i - (n - 1) / 2) * 16 + rng.uniform(-6, 6))
        br(x + (i - (n - 1) / 2) * h * .06, y, ang, h * .42, h * .085, 2)
    return "".join(out_ink) + "".join(out_col) + "".join(out_hi)


def fan_coral(a, x, y, h, col):
    c, l, dk = col
    w = h * .9
    pts = [(x - 6, y), (x - w * .5, y - h * .45), (x - w * .45, y - h * .85), (x, y - h), (x + w * .45, y - h * .85), (x + w * .5, y - h * .45), (x + 6, y)]
    d = smooth(pts, t=.18)
    cl = a.clip("fan", d)
    lat = []
    for k in range(9):
        ang = math.radians(180 - k * 22.5)
        lat.append(f"M{f(x)} {f(y)}Q{f(x + math.cos(ang) * w * .3)} {f(y - h * .5)} {f(x + math.cos(ang) * w * .55)} {f(y - h * (.55 + .45 * math.sin(ang)))}")
    for k in range(1, 6):
        r = k / 6
        arc = [(x + math.cos(math.radians(180 - i * 15)) * w * .55 * r, y - h * r * (.3 + .7 * math.sin(math.radians(i * 15 + .01)))) for i in range(13)]
        lat.append(smooth(arc, closed=False))
    return (f'<path d="{d}" fill="{c}" fill-opacity=".35"/>'
            f'<g clip-path="{cl}"><path d="{"".join(lat)}" fill="none" stroke="{c}" stroke-width="{f(h * .028)}" stroke-linecap="round"/></g>'
            f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="2.6" stroke-linejoin="round"/>'
            f'<path d="M{f(x)} {f(y)}L{f(x)} {f(y - h * .25)}" stroke="{INK}" stroke-width="{f(h * .06)}" stroke-linecap="round"/>'
            f'<path d="M{f(x)} {f(y)}L{f(x)} {f(y - h * .25)}" stroke="{dk}" stroke-width="{f(h * .035)}" stroke-linecap="round"/>')


def table_coral(a, x, y, w, col):
    c, l, dk = col
    stem = f'<path d="M{f(x - w * .06)} {f(y)}L{f(x - w * .04)} {f(y - w * .28)}L{f(x + w * .04)} {f(y - w * .28)}L{f(x + w * .06)} {f(y)}Z" fill="{dk}" stroke="{INK}" stroke-width="2.6" stroke-linejoin="round"/>'
    top = smooth([(x - w / 2, y - w * .3), (x - w * .3, y - w * .4), (x, y - w * .42), (x + w * .3, y - w * .4), (x + w / 2, y - w * .3),
                   (x + w * .3, y - w * .24), (x, y - w * .22), (x - w * .3, y - w * .24)], t=.18)
    return stem + a.shape(top, c, l, dk, y - w * .42, y - w * .22, hi_box=(x - w * .1, y - w * .38, w * .25, w * .03))


def tube_sponge(a, x, y, h, col):
    c, l, dk = col
    out = ""
    for k, (dx, hh, ww) in enumerate(((-h * .22, .75, .2), (0, 1.0, .24), (h * .22, .6, .19))):
        w = h * ww
        x0 = x + dx
        top = y - h * hh
        d = smooth([(x0 - w / 2, y), (x0 - w / 2 - 2, top + w * .2), (x0 - w / 2, top), (x0 + w / 2, top), (x0 + w / 2 + 2, top + w * .2), (x0 + w / 2, y)], t=.12)
        out += a.shape(d, c, l, dk, top, y, hi=False)
        out += f'<ellipse cx="{f(x0)}" cy="{f(top)}" rx="{f(w / 2 - 3)}" ry="{f(w * .18)}" fill="{dk}" stroke="{INK}" stroke-width="2.2"/>'
    return out


def seagrass(a, x, y, h, n=6, col="#6aa04a", light="#9cc96e", sway_cls=None):
    rng = random.Random(int(x * 7 + y))
    out = []
    for i in range(n):
        x0 = x + (i - n / 2) * 7 + rng.uniform(-2, 2)
        hh = h * rng.uniform(.6, 1)
        bend = rng.uniform(-.5, .5) * hh * .35
        d = f"M{f(x0 - 4)} {f(y)}Q{f(x0 + bend * .3)} {f(y - hh * .6)} {f(x0 + bend)} {f(y - hh)}Q{f(x0 + bend * .4 + 5)} {f(y - hh * .55)} {f(x0 + 4)} {f(y)}Z"
        out.append(f'<path d="{d}" fill="{col if i % 2 else light}" stroke="{INK}" stroke-width="2" stroke-linejoin="round"/>')
    inner = "".join(out)
    if sway_cls:
        return grp(sway_cls, inner, (x, y))
    return inner


def shell(a, x, y, s, col="#ffd9c0"):
    d = f"M{f(x - 10 * s)} {f(y)}Q{f(x - 12 * s)} {f(y - 14 * s)} {f(x)} {f(y - 16 * s)}Q{f(x + 12 * s)} {f(y - 14 * s)} {f(x + 10 * s)} {f(y)}Z"
    ribs = "".join(f'<path d="M{f(x)} {f(y)}L{f(x + k * 3 * s)} {f(y - 14 * s)}" stroke="#d99a7a" stroke-width="1.4"/>' for k in (-2, -1, 0, 1, 2))
    return f'<path d="{d}" fill="{col}"/>{ribs}<path d="{d}" fill="none" stroke="{INK}" stroke-width="2" stroke-linejoin="round"/>'


def kelp(a, x, y, h, seed=0, col=(KELP, KELP_L, KELP_D), ink=True, segs=4, cls="kelp", lean=0.0):
    """Tall kelp stalk with blades and floats, as NESTED sway groups:
    g.kelp[data-pivot=base] > … > g.kelp-seg[data-pivot=joint] — rotate each by a few degrees, phase-shifted."""
    rng = random.Random(seed * 31 + int(x))
    c, l, dk = col
    seg_h = h / segs
    sw = 2.4 if ink else 0

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
            blades += (f'<path d="{d}" fill="{c if b % 2 else l}" stroke="{INK if ink else dk}" stroke-width="{sw if ink else 0}" stroke-linejoin="round"/>'
                       f'<path d="M{f(bx)} {f(by)}L{f(tip[0])} {f(tip[1])}" fill="none" stroke="{dk}" stroke-width="1.4" opacity=".45"/>')
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
    """Venus' flower basket: a slender curved vase of pale glassy lattice with a frilly rim."""
    w = h * .26
    bend = h * .12
    left = [(x - w * .18, y), (x - w * .34 + bend * .2, y - h * .3), (x - w * .5 + bend * .6, y - h * .7), (x - w * .55 + bend, y - h)]
    right = [(x + w * .55 + bend, y - h), (x + w * .5 + bend * .6, y - h * .7), (x + w * .34 + bend * .2, y - h * .3), (x + w * .18, y)]
    d = smooth(left + right, t=.16)
    # smooth living vase (NO lattice: a mesh would read like the ghost-net trash)
    g = a.linear("gsv", [(0, "#e9e2ff", .95), (.6, "#b8b2e6", .85), (1, "#7d77b8", .8)], 0, y - h, 0, y)
    pores = "".join(f'<ellipse cx="{f(x + bend * t + (k % 2 - .5) * w * .4)}" cy="{f(y - h * t)}" rx="2.6" ry="1.8" fill="#6a63a8" opacity=".55"/>'
                    for k, t in enumerate((.2, .32, .45, .58, .7, .82)))
    return (f'<path d="{d}" fill="{g}"/>{pores}'
            f'<ellipse cx="{f(x + bend)}" cy="{f(y - h)}" rx="{f(w * .55)}" ry="{f(w * .16)}" fill="#3a3470" stroke="#e9e2ff" stroke-width="2"/>'
            f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="2.4"/>')


# ================================================================== floor line + tiles

def floor_y(x, yin, yout, s_in, s_out, waves, W=TW):
    """Hermite trend (matches neighbour slopes at the edges) + enveloped wiggle (zero value+slope at edges)."""
    t = x / W
    h00, h10, h01, h11 = 2 * t ** 3 - 3 * t ** 2 + 1, t ** 3 - 2 * t ** 2 + t, -2 * t ** 3 + 3 * t ** 2, t ** 3 - t ** 2
    trend = h00 * yin + h10 * s_in * W + h01 * yout + h11 * s_out * W
    env = math.sin(math.pi * t) ** 2
    wig = sum(amp * math.sin(2 * math.pi * k * t + ph) for k, amp, ph in waves)
    return trend + wig * env


def floor_tile(name, zone, yin, yout, s_in, s_out, waves, fill, deco, defs_art, label, H=FH, under=None, extra_attr=""):
    a = defs_art
    xs = list(range(0, TW + 1, 32))
    line = [(x, floor_y(x, yin, yout, s_in, s_out, waves)) for x in xs]
    d = "M" + " L".join(f"{f(x)} {f(y)}" for x, y in line) + f" L{TW} {H} L0 {H}Z"
    c, l, dk = fill
    g = a.linear("fl", [(0, l), (.06, c), (1, dk)], 0, min(y for _, y in line), 0, H)
    body = f'<path d="{d}" fill="{g}"/>'
    if under:
        body += under(line)
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
    out = []
    for k in range(1, 7):
        pts = [(x, y + k * 60 + 10 * math.sin(x * .01 + k)) for x, y in line[::2]]
        out.append(f'<path d="M{" L".join(f"{f(x)} {f(y)}" for x, y in pts)}" fill="none" stroke="{SAND_D}" stroke-width="3" opacity=".45"/>')
    return "".join(out)


def ripples(a, line, col=SAND_D, n=40, seed=1):
    rng = random.Random(seed)
    out = []
    for _ in range(n):
        x = rng.uniform(20, TW - 20)
        y = y_at(line, x) + rng.uniform(14, 120)
        w = rng.uniform(24, 60)
        out.append(f'<path d="M{f(x - w / 2)} {f(y)}q{f(w / 4)} -6 {f(w / 2)} 0t{f(w / 2)} 0" fill="none" stroke="{col}" stroke-width="2.4" stroke-linecap="round" opacity=".7"/>')
    return "".join(out)


# ------------------------------------------------------------------ UTES
def utes_floor():
    a = Art("utesfl", seed=101)
    waves = [(3, 18, .4), (5, 9, 1.3), (9, 4, 2.0)]
    yout = IN + 120

    def deco(line):
        out = ripples(a, line, n=46, seed=3)
        items = [
            (150, lambda x, y: brain_coral(a, x, y + 6, 70, CORAL["yellow"])),
            (330, lambda x, y: branch_coral(a, x, y + 4, 170, CORAL["violet"], 5, 1)),
            (470, lambda x, y: rock(a, x, y + 14, 150, 70)),
            (560, lambda x, y: fan_coral(a, x, y + 6, 190, CORAL["red"])),
            (720, lambda x, y: seagrass(a, x, y + 8, 70, 7, sway_cls="sway")),
            (880, lambda x, y: table_coral(a, x, y + 8, 200, CORAL["teal"])),
            (1050, lambda x, y: tube_sponge(a, x, y + 6, 110, CORAL["orange"])),
            (1230, lambda x, y: branch_coral(a, x, y + 4, 140, CORAL["pink"], 4, 2)),
            (1330, lambda x, y: brain_coral(a, x, y + 6, 54, CORAL["pink"])),
            (1500, lambda x, y: rock(a, x, y + 16, 190, 90)),
            (1520, lambda x, y: seagrass(a, x - 90, y + 8, 60, 6, sway_cls="sway")),
            (1700, lambda x, y: fan_coral(a, x, y + 6, 150, CORAL["violet"])),
            (1880, lambda x, y: brain_coral(a, x, y + 6, 62, CORAL["orange"])),
            (1990, lambda x, y: seagrass(a, x, y + 8, 64, 6, sway_cls="sway")),
            # seagrass meadow (mořská tráva) — the manatee's grazing spot
            (1100, lambda x, y: seagrass(a, x - 40, y + 30, 58, 10, sway_cls="sway meadow")),
            (1180, lambda x, y: seagrass(a, x, y + 34, 52, 9, sway_cls="sway meadow")),
        ]
        for x, fn in items:
            out += wrap(x, 110, lambda xx: fn(xx, y_at(line, xx)))
        out += "".join(shell(a, x, y_at(line, x) + 40, 1.0) for x in (260, 980, 1620))
        return out
    return floor_tile("utes-floor.svg", "utes", IN, yout, S_UTES, S_UTES, waves, (SAND, SAND_L, SAND_D), deco, a, "Korálový útes — dno",
                      under=sand_under)


def far_layer(name, label, body, defs):
    return doc(name, TW, TH, body, defs, extra=' data-layer="far"', label=label, cls="ponor layer")


def ridge_band(y0, amps, col, op=1.0, W=TW, H=TH):
    pts = []
    for x in range(0, W + 1, 32):
        t = x / W
        y = y0 + sum(a_ * math.sin(2 * math.pi * k * t + ph) for k, a_, ph in amps)
        pts.append((x, y))
    d = "M" + " L".join(f"{f(x)} {f(y)}" for x, y in pts) + f" L{W} {H} L0 {H}Z"
    return f'<path d="{d}" fill="{col}" opacity="{op}"/>', pts


def utes_far():
    a = Art("utesfar", seed=102)
    body = ""
    b1, p1 = ridge_band(560, [(2, 30, .3), (5, 14, 1.1), (11, 6, .2)], mix(UTES[1], UTES[2], .35), .7)
    body += b1
    # hazy bommie silhouettes (no ink: far plane)
    rng = random.Random(5)
    for x in range(60, TW, 170):
        xx = x + rng.uniform(-30, 30)
        h = rng.uniform(80, 170)
        y = 560 + 30 * math.sin(2 * math.pi * 2 * xx / TW + .3) + 20
        body += wrap(xx, 90, lambda X, h=h, y=y: f'<path d="{smooth([(X - h * .6, y), (X - h * .5, y - h * .6), (X - h * .2, y - h), (X + h * .25, y - h * .9), (X + h * .55, y - h * .5), (X + h * .6, y)])}" fill="{mix(UTES[1], UTES[2], .5)}" opacity=".55"/>')
    b2, _ = ridge_band(640, [(3, 20, 1.5), (7, 8, .7)], mix(UTES[2], "#1d7f96", .3), .55)
    body += b2
    return far_layer("utes-far.svg", "Korálový útes — daleko", body, a.defs)


def utes_mid():
    a = Art("utesmid", seed=103)
    body = ""
    rng = random.Random(9)
    tint = .45   # mid plane: colour pushed toward the water, light ink
    for i, x in enumerate(range(100, TW, 260)):
        xx = x + rng.uniform(-40, 40)
        y = 700 + 24 * math.sin(2 * math.pi * 3 * xx / TW)
        kind = i % 4
        col = list(CORAL.values())[i % len(CORAL)]
        colm = tuple(mix(c, UTES[2], tint) for c in col)
        if kind == 0:
            fn = lambda X, y=y, colm=colm: rock(a, X, y, 260, 120, col=tuple(mix(c, UTES[2], .5) for c in (ROCK, ROCK_L, ROCK_D)), ink=False) + brain_coral(a, X - 40, y - 80, 50, colm)
        elif kind == 1:
            fn = lambda X, y=y, colm=colm: branch_coral(a, X, y, 160, colm, 5, i)
        elif kind == 2:
            fn = lambda X, y=y, colm=colm: fan_coral(a, X, y, 170, colm)
        else:
            fn = lambda X, y=y, colm=colm: table_coral(a, X, y, 210, colm)
        body += wrap(xx, 140, fn)
    band, _ = ridge_band(720, [(2, 12, .9), (6, 6, .2)], mix(SAND_D, UTES[2], .5), 1)
    body = band + body
    # mid-plane ink is lighter: swap the ink colour for a water-tinted one
    body = body.replace(INK, mix("#33243a", UTES[2], .45))
    return doc("utes-mid.svg", TW, TH, body, [d.replace(INK, mix("#33243a", UTES[2], .45)) for d in a.defs], extra=' data-layer="mid"',
               label="Korálový útes — střední plán", cls="ponor layer")


def utes_near():
    a = Art("utesnear", seed=104)
    body = ""
    # foreground clumps rise only into the bottom ~16 % of the screen (never hide a creature or trash)
    fg = lambda c: tuple(mix(x, "#1a3a4a", .3) for x in c)
    body += wrap(260, 160, lambda X: grp("near-item sway", fan_coral(a, X, 830, 190, fg(CORAL["violet"])), (X, 830)))
    body += wrap(420, 120, lambda X: seagrass(a, X, 790, 90, 9, col="#3f7a3a", light="#5e9a4a", sway_cls="sway"))
    body += wrap(1350, 160, lambda X: grp("near-item", branch_coral(a, X, 850, 190, fg(CORAL["pink"]), 6, 7), (X, 850)))
    body += wrap(1560, 120, lambda X: seagrass(a, X, 790, 80, 8, col="#3f7a3a", light="#5e9a4a", sway_cls="sway"))
    return doc("utes-near.svg", TW, TH, body, a.defs, extra=' data-layer="near"', label="Korálový útes — popředí", cls="ponor layer")


# ------------------------------------------------------------------ CHALUHY
def chaluhy_floor():
    a = Art("chalfl", seed=111)
    waves = [(2, 26, 1.1), (4, 12, .2), (7, 6, 2.3)]
    yout = IN + 160
    RK = ("#7d8796", "#a9b2c0", "#535c6c")

    def under(line):
        out = []
        rng = random.Random(4)
        for _ in range(26):
            x = rng.uniform(0, TW)
            y = y_at(line, x) + rng.uniform(60, 400)
            out.append(f'<ellipse cx="{f(x)}" cy="{f(y)}" rx="{f(rng.uniform(30, 80))}" ry="{f(rng.uniform(16, 34))}" fill="#8f876f" opacity=".35"/>')
        return "".join(out)

    def deco(line):
        out = ripples(a, line, col="#8f876f", n=30, seed=9)
        items = [
            (120, lambda x, y: rock(a, x, y + 30, 260, 130, RK)),
            (330, lambda x, y: kelp(a, x, y + 6, 520, 1, segs=4)),
            (470, lambda x, y: rock(a, x, y + 22, 150, 70, RK)),
            (640, lambda x, y: kelp(a, x, y + 6, 600, 2, segs=4)),
            (760, lambda x, y: tube_sponge(a, x, y + 8, 80, CORAL["yellow"])),
            (900, lambda x, y: rock(a, x, y + 34, 300, 160, RK)),
            (1080, lambda x, y: kelp(a, x, y + 6, 560, 3, segs=4)),
            (1250, lambda x, y: brain_coral(a, x, y + 6, 46, CORAL["pink"])),
            (1420, lambda x, y: kelp(a, x, y + 6, 640, 4, segs=4)),
            (1560, lambda x, y: rock(a, x, y + 26, 200, 100, RK)),
            (1760, lambda x, y: kelp(a, x, y + 6, 540, 5, segs=4)),
            (1930, lambda x, y: rock(a, x, y + 22, 170, 80, RK)),
        ]
        for x, fn in items:
            out += wrap(x, 140, lambda xx: fn(xx, y_at(line, xx)))
        # pink coralline crusts on rocks / floor
        rng = random.Random(8)
        for _ in range(30):
            x = rng.uniform(10, TW - 10)
            y = y_at(line, x) + rng.uniform(4, 30)
            out += f'<ellipse cx="{f(x)}" cy="{f(y)}" rx="{f(rng.uniform(6, 14))}" ry="{f(rng.uniform(3, 6))}" fill="#e98fa6" stroke="{INK}" stroke-width="1.4"/>'
        return out
    return floor_tile("chaluhy-floor.svg", "chaluhy", IN, yout, S_CHAL, S_CHAL, waves, ("#b3a98d", "#d6cdb0", "#6f6858"), deco, a,
                      "Chaluhový les — dno", under=under)


def chaluhy_far():
    a = Art("chalfar", seed=112)
    body = ""
    rng = random.Random(12)
    col = mix(CHAL[1], CHAL[2], .45)
    for x in range(40, TW, 110):
        xx = x + rng.uniform(-20, 20)
        h = rng.uniform(420, 680)
        body += wrap(xx, 60, lambda X, h=h: kelp(a, X, 768, h, int(X), col=(col, mix(col, CHAL[0], .2), col), ink=False, segs=3, cls="kelp"))
    b, _ = ridge_band(700, [(2, 14, .4), (5, 8, 1.2)], mix(CHAL[2], "#1a4f55", .3), .8)
    body += b
    return doc("chaluhy-far.svg", TW, TH, f'<g opacity=".55">{body}</g>', a.defs, extra=' data-layer="far"', label="Chaluhový les — daleko", cls="ponor layer")


def chaluhy_mid():
    a = Art("chalmid", seed=113)
    body = ""
    rng = random.Random(13)
    tint = .52
    colk = tuple(mix(c, CHAL[2], tint) for c in (KELP, KELP_L, KELP_D))
    for x in range(80, TW, 290):
        xx = x + rng.uniform(-30, 30)
        h = rng.uniform(560, 760)
        body += wrap(xx, 90, lambda X, h=h: kelp(a, X, 790, h, int(X) + 3, col=colk, ink=True, segs=4))
    body += ridge_band(730, [(3, 16, .9), (7, 7, .2)], mix("#5b5a52", CHAL[2], .45), 1)[0]
    soft_ink = mix("#33243a", CHAL[2], .4)
    body = body.replace(INK, soft_ink)
    return doc("chaluhy-mid.svg", TW, TH, body, a.defs, extra=' data-layer="mid"', label="Chaluhový les — střední plán", cls="ponor layer")


def chaluhy_near():
    a = Art("chalnear", seed=114)
    colk = tuple(mix(c, "#1f3a30", .5) for c in (KELP, KELP_L, KELP_D))
    body = ""
    for x, h in ((140, 430), (1240, 380)):
        body += wrap(x, 120, lambda X, h=h: grp("near-item", kelp(a, X, 800, h, int(X) + 9, col=colk, segs=4, lean=.6), (X, 800)))
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
    body = ""
    # distant school as a soft swirl of dots + a far whale silhouette (no ink, very faint)
    rng = random.Random(22)
    for k in range(160):
        t = k / 160 * 6.28 * 2
        r = 70 + 40 * math.sin(t * 1.7)
        x = 1400 + r * math.cos(t) * 2.2 + rng.uniform(-14, 14)
        y = 330 + r * math.sin(t) + rng.uniform(-10, 10)
        body += f'<path d="M{f(x)} {f(y)}l10 -3l0 6z" fill="{mix(SIRE[0], "#ffffff", .25)}" opacity=".5"/>'
    whale = smooth([(300, 420), (360, 396), (480, 390), (600, 404), (680, 420), (720, 410), (740, 380), (760, 432), (690, 440),
                    (600, 448), (480, 452), (360, 446)], t=.18)
    body += f'<path d="{whale}" fill="{mix(SIRE[1], SIRE[2], .55)}" opacity=".45" transform="translate(0 0) scale(-1 1) translate(-1040 0)"/>'
    return doc("sire-more-far.svg", TW, TH, body, a.defs, extra=' data-layer="far"', label="Širé moře — daleko", cls="ponor layer")


def sire_mid():
    a = Art("siremid", seed=123)
    rng = random.Random(23)
    body = ""
    for _ in range(90):
        x, y, r = rng.uniform(0, TW), rng.uniform(40, TH - 40), rng.uniform(1.5, 4.5)
        body += wrap(x, 6, lambda X, y=y, r=r: f'<circle cx="{f(X)}" cy="{f(y)}" r="{f(r)}" fill="#e6f6ff" opacity="{f(.25 + r * .05)}"/>')
    return doc("sire-more-mid.svg", TW, TH, body, a.defs, extra=' data-layer="mid"', label="Širé moře — plankton", cls="ponor layer")


def sire_near():
    a = Art("sirenear", seed=124)
    rng = random.Random(24)
    halo = a.radial("bk", [(0, "#ffffff", .35), (.7, "#ffffff", .12), (1, "#ffffff", 0)], cx="50%", cy="50%", r="50%")
    body = ""
    for _ in range(9):
        x, y, r = rng.uniform(0, TW), rng.uniform(40, 300), rng.uniform(14, 34)
        body += wrap(x, r, lambda X, y=y, r=r: f'<circle cx="{f(X)}" cy="{f(y)}" r="{f(r)}" fill="{halo}"/>')
    return doc("sire-more-near.svg", TW, TH, body, a.defs, extra=' data-layer="near"', label="Širé moře — popředí", cls="ponor layer")


# ------------------------------------------------------------------ HLUBINY
def hlubiny_floor():
    a = Art("deepfl", seed=131)
    waves = [(2, 20, .5), (5, 8, 1.9)]
    yout = IN + 90
    OOZE = ("#2b2f52", "#3e4470", "#151833")

    def deco(line):
        out = ""
        glows = ""
        rng = random.Random(31)
        for x in (180, 520, 900, 1260, 1640, 1900):
            y = y_at(line, x) + 8
            o, g = sea_pen(a, x, y, rng.uniform(90, 140))
            out += o
            glows += g
        for x in (330, 1080, 1480):
            out += wrap(x, 60, lambda X: glass_sponge(a, X, y_at(line, X) + 10, 130))
        for x in (700, 1780):
            out += wrap(x, 120, lambda X: rock(a, X, y_at(line, X) + 26, 220, 90, ("#3a3f66", "#565c8a", "#22264a")))
        # tiny glowing specks on the ooze
        for _ in range(40):
            x = rng.uniform(0, TW)
            y = y_at(line, x) + rng.uniform(6, 60)
            glows += f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(rng.uniform(1.5, 3))}" fill="{rng.choice((GLOW_C, GLOW_V, GLOW_G))}" opacity=".8"/>'
        return out + grp("glow", glows, (TW / 2, IN))
    return floor_tile("hlubiny-floor.svg", "hlubiny", IN, yout, S_DEEP, S_DEEP, waves, OOZE, deco, a, "Hlubiny — dno")


def hlubiny_far():
    a = Art("deepfar", seed=132)
    rng = random.Random(32)
    halo = a.radial("dh", [(0, "#ffffff", .9), (.3, "#ffffff", .35), (1, "#ffffff", 0)], cx="50%", cy="50%", r="50%")
    body = ""
    for _ in range(70):
        x, y, r = rng.uniform(0, TW), rng.uniform(30, TH - 60), rng.uniform(4, 10)
        col = rng.choice((GLOW_C, GLOW_V, GLOW_G))
        body += wrap(x, r, lambda X, y=y, r=r, col=col: f'<circle cx="{f(X)}" cy="{f(y)}" r="{f(r)}" fill="{col}" opacity=".18"/><circle cx="{f(X)}" cy="{f(y)}" r="{f(r * .3)}" fill="{col}" opacity=".6"/>')
    body += ridge_band(690, [(2, 22, .1), (5, 10, 1.7)], "#0e1a38", .9)[0]
    return doc("hlubiny-far.svg", TW, TH, f'<g class="glow">{body}</g>', a.defs, extra=' data-layer="far"', label="Hlubiny — daleko", cls="ponor layer")


def hlubiny_mid():
    a = Art("deepmid", seed=133)
    rng = random.Random(33)
    body = ridge_band(720, [(3, 26, .6), (8, 9, 1.4)], "#141c3e", 1)[0]
    glow = ""
    for x in range(120, TW, 300):
        xx = x + rng.uniform(-50, 50)
        h = rng.uniform(160, 260)
        sp = smooth([(xx - 60, 760), (xx - 30, 760 - h * .6), (xx - 10, 760 - h), (xx + 14, 760 - h * .95), (xx + 36, 760 - h * .5), (xx + 70, 760)], t=.18)
        body += wrap(xx, 80, lambda X, sp=sp, xx=xx: f'<path d="{sp}" fill="#1b2550" transform="translate({f(X - xx)} 0)"/>')
        for k in range(3):
            gx, gy = xx + rng.uniform(-30, 30), 760 - h * rng.uniform(.3, .9)
            glow += wrap(gx, 10, lambda X, gy=gy: f'<circle cx="{f(X)}" cy="{f(gy)}" r="5" fill="{GLOW_C}" opacity=".7"/><circle cx="{f(X)}" cy="{f(gy)}" r="14" fill="{GLOW_C}" opacity=".15"/>')
    return doc("hlubiny-mid.svg", TW, TH, body + grp("glow", glow), a.defs, extra=' data-layer="mid"', label="Hlubiny — střední plán", cls="ponor layer")


def hlubiny_near():
    a = Art("deepnear", seed=134)
    body = ""
    for x, w in ((200, 360), (1300, 420)):
        body += wrap(x, w / 2, lambda X, w=w: grp("near-item", rock(a, X, 800, w, 170, ("#0d1430", "#1c2550", "#060a1c"), ink=False), (X, 800)))
    glow = "".join(f'<circle cx="{f(x)}" cy="{f(y)}" r="4" fill="{GLOW_V}" opacity=".85"/>' for x, y in ((150, 690), (260, 700), (1240, 680), (1390, 690)))
    return doc("hlubiny-near.svg", TW, TH, body + grp("glow", glow), a.defs, extra=' data-layer="near"', label="Hlubiny — popředí", cls="ponor layer")


# ------------------------------------------------------------------ transitions (floor plane)
def trans_utes_chaluhy():
    a = Art("tuc", seed=141)
    yin, yout = IN, IN + 260
    waves = [(3, 14, .3), (6, 7, 1.0)]
    RK = ("#7d8796", "#a9b2c0", "#535c6c")

    def deco(line):
        out = ripples(a, line[:30], n=14, seed=5)
        out += wrap(220, 100, lambda X: brain_coral(a, X, y_at(line, X) + 6, 56, CORAL["yellow"]))
        out += wrap(420, 100, lambda X: branch_coral(a, X, y_at(line, X) + 4, 120, CORAL["pink"], 4, 4))
        out += rock(a, 900, y_at(line, 900) + 40, 340, 170, RK)
        out += kelp(a, 1180, y_at(line, 1180) + 6, 480, 11, segs=4)
        out += rock(a, 1420, y_at(line, 1420) + 26, 200, 100, RK)
        out += kelp(a, 1650, y_at(line, 1650) + 6, 560, 12, segs=4)
        out += kelp(a, 1900, y_at(line, 1900) + 6, 520, 13, segs=4)
        return out

    def under(line):
        # sand on the left blends into rock on the right
        g = a.linear("sr", [(0, SAND, 1), (.45, SAND, 1), (.75, "#b3a98d", 1), (1, "#b3a98d", 1)], 0, 0, TW, 0)
        d = "M" + " L".join(f"{f(x)} {f(y)}" for x, y in line) + f" L{TW} {FH} L0 {FH}Z"
        return f'<path d="{d}" fill="{g}"/>'
    return floor_tile("trans-utes-chaluhy.svg", "utes/chaluhy", yin, yout, S_UTES, S_CHAL, waves, (SAND, SAND_L, "#5b5a52"), deco, a,
                      "Přechod útes → chaluhy", under=under)


def trans_chaluhy_sire():
    """The drop-off: the rocky floor ends in a cliff that falls away into the blue. Tile is 2048 x 2048."""
    a = Art("tcs", seed=142)
    H = 2048
    yin = IN
    yout = IN + 420          # virtual descent line continues into the open ocean
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
    rockg = a.linear("cl", [(0, "#b0aa96"), (.08, "#8b8676"), (.5, "#4f5260"), (1, "#20304a")], 0, IN, 0, H)
    body = f'<path d="{d}" fill="{rockg}"/>'
    # wall texture: horizontal ledges fading with depth
    for k in range(18):
        y = IN + 220 + k * 70
        body += f'<path d="M{f(700 + k * 8)} {f(y)}Q{f(900)} {f(y - 10)} {f(1060 + k * 14)} {f(y + 6)}" fill="none" stroke="#2f3446" stroke-width="3" opacity="{f(max(.1, .6 - k * .03))}"/>'
    body += f'<path d="M{" L".join(f"{f(x)} {f(y)}" for x, y in pts)}" fill="none" stroke="{INK}" stroke-width="3" stroke-linejoin="round"/>'
    body += kelp(a, 260, floor_y(260, yin, yin + 160, S_CHAL, S_CHAL, [(2, 10, .3)], W=1000) + 6, 560, 21, segs=4)
    body += kelp(a, 620, floor_y(620, yin, yin + 160, S_CHAL, S_CHAL, [(2, 10, .3)], W=1000) + 6, 480, 22, segs=4)
    body += rock(a, 860, yin + 160 + 30, 220, 110, ("#7d8796", "#a9b2c0", "#535c6c"))
    # depth fade at the bottom of the wall
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
    OOZE = ("#2b2f52", "#3e4470", "#151833")
    pts = []
    for x in range(0, TW + 1, 32):
        t = x / TW
        y = H + 60 - (H + 60 - yout) * (max(0, (t - .3) / .7) ** .7)
        y += 10 * math.sin(x * .006) * (t > .3)
        pts.append((x, y))
    d = "M" + " L".join(f"{f(x)} {f(y)}" for x, y in pts) + f" L{TW} {H} L0 {H}Z"
    g = a.linear("oz", [(0, OOZE[1]), (.1, OOZE[0]), (1, OOZE[2])], 0, yout, 0, H)
    body = f'<path d="{d}" fill="{g}"/><path d="M{" L".join(f"{f(x)} {f(y)}" for x, y in pts)}" fill="none" stroke="#4a5080" stroke-width="3"/>'
    body += glass_sponge(a, 1600, pts[50][1] + 10, 120)
    o, gl = sea_pen(a, 1880, pts[59][1] + 8, 110)
    body += o + grp("glow", gl)
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
    """Seamless 512 x 512 caustic net (white, transparent ground). Two copies drift at different speeds."""
    a = Art("caus", seed=153)
    S = 512
    rng = random.Random(53)
    cells = []
    for i in range(6):
        for j in range(6):
            cells.append(((i + .5) * S / 6 + rng.uniform(-24, 24), (j + .5) * S / 6 + rng.uniform(-24, 24)))
    body = ""
    for (x, y) in cells:
        r = S / 12 * rng.uniform(.85, 1.15)
        pts = ellipse_pts(x, y, r, r * .9, n=7, wob=lambda t: .18 * math.sin(3 * t + x))
        d = smooth(pts, t=.22)
        for dx in (-S, 0, S):
            for dy in (-S, 0, S):
                body += f'<path d="{d}" transform="translate({dx} {dy})" fill="none" stroke="#fffff0" stroke-width="{f(rng.uniform(3, 6))}" stroke-linejoin="round" opacity=".7"/>'
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
