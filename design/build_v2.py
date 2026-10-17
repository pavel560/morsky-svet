#!/usr/bin/env python3
"""Mořský svět v2 — title scene, richer home, logo, play bubble, door objects (designer source, stdlib only).

Run:  python3 design/build_v2.py
  art/title.svg              start screen scene (1600 x 1000, xMidYMid slice) — layered, class-named groups
  art/home.svg               home „Loďka“ v2 (same scene system, calmer, peeking animals)
  art/logo-cs.svg, logo-en.svg   hand-lettered logo (Grandstander 800 outlines from design/logo_glyphs.json,
                             custom diacritics: háček = a chubby coral wave-V, čárka = a water drop)
  art/play-bubble.svg        the big shiny bubble play button art
  art/door-sea.svg, door-quiz.svg, door-habitat.svg   illustrated door objects for the home buttons
Contract + animation spec: design/DESIGN.md „Verze 2 — úvod a Loďka“.
"""
import json
import math
import os
import random
import re

from svgkit import INK, Art, f, grp, smooth, eye, lid, blush, mix, ellipse_pts
import build_sea as sea
from build_ui import diver_sitting

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.join(HERE, "..", "art")
GLYPHS = json.load(open(os.path.join(HERE, "logo_glyphs.json")))

W, H = 1600, 1000


def write(name, svg):
    with open(os.path.join(ART, name), "w") as fh:
        fh.write(svg)


# ================================================================== nested creature art
def nest(cid, x, y, w, cls, flip=False, rot=0, extra="", file=None):
    """Embed an existing art file as a nested <svg> (ids re-prefixed so copies never collide).
    (x, y) = centre of the placed art in scene units, w = width."""
    t = open(os.path.join(ART, file or f"{cid}.svg")).read()
    vb = [float(v) for v in re.search(r'viewBox="([^"]+)"', t).group(1).split()]
    h = w * vb[3] / vb[2]
    inner = re.sub(r'^.*?<svg[^>]*>', '', t, count=1, flags=re.S).replace("</svg>\n", "").rstrip()
    if inner.endswith("</svg>"):
        inner = inner[:-6]
    inner = re.sub(r"<title>.*?</title>", "", inner)
    pre = f"{cls.split()[0]}-"
    inner = re.sub(r'id="([^"]+)"', lambda m: f'id="{pre}{m.group(1)}"', inner)
    inner = re.sub(r'url\(#([^)]+)\)', lambda m: f'url(#{pre}{m.group(1)})', inner)
    fl = f" translate({f(2 * x)} 0) scale(-1 1)" if flip else ""
    rt = f" rotate({rot} {f(x)} {f(y)})" if rot else ""
    return (f'<g class="{cls}" data-pivot="{f(x)} {f(y)}"{extra} transform="{rt.strip()}{fl}">'
            f'<svg x="{f(x - w / 2)}" y="{f(y - h / 2)}" width="{f(w)}" height="{f(h)}" viewBox="{" ".join(f(v) for v in vb)}" overflow="visible">{inner}</svg></g>')


# ================================================================== sky + surface pieces
def sky(a, wl, warm=True):
    g = a.linear("sky", [(0, "#7fc6e3"), (.55, "#c4e9f2"), (.86, "#fbeed6"), (1, "#ffe2b8")], 0, 0, 0, wl)
    return f'<rect class="sky" width="{W}" height="{wl + 20}" fill="{g}"/>'


def sun(a, x, y, r=62):
    glow = a.radial("sg", [(0, "#fff8dc", 1), (.3, "#ffe7a0", .75), (.65, "#fff3c4", .22), (1, "#fff3c4", 0)], user=(x, y, r * 4.2))
    rays = ""
    for k in range(12):
        ang = k * 30
        rays += (f'<path d="M{f(x - 9)} {f(y - r - 14)}L{f(x)} {f(y - r * 2.6 - (14 if k % 2 else 0))}L{f(x + 9)} {f(y - r - 14)}Z" '
                 f'fill="#fff6d0" opacity="{.55 if k % 2 else .8}" transform="rotate({ang} {f(x)} {f(y)})"/>')
    disc = a.radial("sd", [(0, "#fffbe6"), (.6, "#ffe68a"), (1, "#ffd25a")], cx="40%", cy="35%", r="70%")
    face_less = (f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(r)}" fill="{disc}" stroke="#f2b01e" stroke-width="5"/>'
                 f'<path d="M{f(x - r * .55)} {f(y - r * .35)}Q{f(x - r * .2)} {f(y - r * .75)} {f(x + r * .25)} {f(y - r * .7)}" fill="none" stroke="#fff" stroke-width="7" stroke-linecap="round" opacity=".8"/>')
    return (f'<circle class="sun-glow" cx="{f(x)}" cy="{f(y)}" r="{f(r * 4.2)}" fill="{glow}"/>'
            + grp("sun-rays", rays, (x, y)) + grp("sun", face_less, (x, y)))


def cloud(a, x, y, s, k):
    pts = [(x - 120 * s, y + 24 * s), (x - 110 * s, y - 4 * s), (x - 78 * s, y - 30 * s), (x - 34 * s, y - 34 * s), (x - 8 * s, y - 62 * s),
           (x + 40 * s, y - 64 * s), (x + 74 * s, y - 34 * s), (x + 110 * s, y - 22 * s), (x + 128 * s, y + 6 * s), (x + 116 * s, y + 26 * s)]
    d = smooth(pts, t=.2)
    g = a.linear("cl", [(0, "#ffffff"), (.65, "#ffffff"), (1, "#d6ecf5")], 0, y - 64 * s, 0, y + 26 * s)
    return grp(f"cloud cloud-{k}", f'<path d="{d}" fill="{g}"/>'
               f'<path d="M{f(x - 100 * s)} {f(y + 14 * s)}Q{f(x)} {f(y + 30 * s)} {f(x + 110 * s)} {f(y + 12 * s)}" fill="none" stroke="#c4e0ec" stroke-width="{f(4 * s)}" stroke-linecap="round" opacity=".8"/>',
               (x, y))


def gull(a, x, y, s, k, flap=0.0):
    """Friendly gull: white body, grey wings as separate flapping groups."""
    body = smooth([(x - 22 * s, y + 2 * s), (x - 6 * s, y - 8 * s), (x + 16 * s, y - 8 * s), (x + 26 * s, y - 2 * s), (x + 14 * s, y + 8 * s), (x - 10 * s, y + 8 * s)], t=.2)
    out = f'<path d="{body}" fill="#ffffff" stroke="{INK}" stroke-width="{f(2.4 * s)}" stroke-linejoin="round"/>'
    out += f'<path d="M{f(x - 22 * s)} {f(y + 2 * s)}l{f(-12 * s)} {f(-6 * s)}l{f(2 * s)} {f(12 * s)}z" fill="#dfe6ee" stroke="{INK}" stroke-width="{f(2 * s)}" stroke-linejoin="round"/>'
    out += f'<path d="M{f(x + 25 * s)} {f(y - 3 * s)}l{f(10 * s)} {f(3 * s)}l{f(-10 * s)} {f(3 * s)}z" fill="#ffc845" stroke="{INK}" stroke-width="{f(1.6 * s)}" stroke-linejoin="round"/>'
    out += f'<circle cx="{f(x + 18 * s)}" cy="{f(y - 3.5 * s)}" r="{f(1.8 * s)}" fill="{INK}"/>'
    wing_far = (f'<path d="M{f(x - 2 * s)} {f(y - 6 * s)}Q{f(x - 14 * s)} {f(y - 34 * s)} {f(x - 34 * s)} {f(y - 38 * s)}Q{f(x - 16 * s)} {f(y - 20 * s)} {f(x + 8 * s)} {f(y - 6 * s)}Z" '
                f'fill="#b9c4d2" stroke="{INK}" stroke-width="{f(2 * s)}" stroke-linejoin="round"/>')
    wing_near = (f'<path d="M{f(x)} {f(y - 4 * s)}Q{f(x + 6 * s)} {f(y - 36 * s)} {f(x - 18 * s)} {f(y - 48 * s)}Q{f(x + 22 * s)} {f(y - 30 * s)} {f(x + 14 * s)} {f(y - 4 * s)}Z" '
                 f'fill="#dfe6ee" stroke="{INK}" stroke-width="{f(2.2 * s)}" stroke-linejoin="round"/>'
                 f'<path d="M{f(x - 18 * s)} {f(y - 48 * s)}q{f(4 * s)} {f(4 * s)} {f(8 * s)} {f(5 * s)}" fill="none" stroke="{INK}" stroke-width="{f(3 * s)}" stroke-linecap="round"/>')
    return grp(f"gull gull-{k}", grp("wing wing-far", wing_far, (x + 2 * s, y - 6 * s)) + out + grp("wing wing-near", wing_near, (x + 6 * s, y - 4 * s)), (x, y))


def island(a, x, wl, s=1.0):
    """Far island (no ink, hazy): hill, palm, little lighthouse."""
    hz = lambda c: mix(c, "#c4e9f2", .45)
    hill = smooth([(x - 170 * s, wl + 4), (x - 120 * s, wl - 40 * s), (x - 40 * s, wl - 78 * s), (x + 50 * s, wl - 70 * s), (x + 130 * s, wl - 36 * s), (x + 190 * s, wl + 4)], t=.2)
    out = f'<path d="{hill}" fill="{hz("#7fbf8a")}"/>'
    out += f'<path d="M{f(x - 120 * s)} {f(wl - 4)}Q{f(x)} {f(wl - 20 * s)} {f(x + 150 * s)} {f(wl - 4)}" fill="none" stroke="{hz("#f1d9a6")}" stroke-width="{f(10 * s)}" stroke-linecap="round"/>'
    # palm
    px, py = x - 40 * s, wl - 76 * s
    out += f'<path d="M{f(px)} {f(py)}Q{f(px + 10 * s)} {f(py - 60 * s)} {f(px + 30 * s)} {f(py - 110 * s)}" fill="none" stroke="{hz("#9a7a52")}" stroke-width="{f(9 * s)}" stroke-linecap="round"/>'
    tx, ty = px + 30 * s, py - 110 * s
    for ang, L in ((-160, 70), (-120, 62), (-60, 66), (-20, 72), (10, 56), (200, 54)):
        r = math.radians(ang)
        ex, ey = tx + math.cos(r) * L * s, ty + math.sin(r) * L * s + 18 * s
        out += f'<path d="M{f(tx)} {f(ty)}Q{f((tx + ex) / 2)} {f(min(ty, ey) - 22 * s)} {f(ex)} {f(ey)}" fill="none" stroke="{hz("#4f9a5a")}" stroke-width="{f(13 * s)}" stroke-linecap="round"/>'
    # lighthouse
    lx, ly = x + 90 * s, wl - 50 * s
    out += (f'<path d="M{f(lx - 14 * s)} {f(ly)}L{f(lx - 9 * s)} {f(ly - 80 * s)}L{f(lx + 9 * s)} {f(ly - 80 * s)}L{f(lx + 14 * s)} {f(ly)}Z" fill="{hz("#ffffff")}"/>'
            + "".join(f'<path d="M{f(lx - 13 * s + k * .6)} {f(ly - 14 * s - k * 22 * s)}L{f(lx + 13 * s - k * .6)} {f(ly - 14 * s - k * 22 * s)}L{f(lx + 12 * s - k * .6)} {f(ly - 26 * s - k * 22 * s)}L{f(lx - 12 * s + k * .6)} {f(ly - 26 * s - k * 22 * s)}Z" fill="{hz("#e0604f")}"/>' for k in range(3))
            + f'<rect x="{f(lx - 11 * s)}" y="{f(ly - 96 * s)}" width="{f(22 * s)}" height="{f(16 * s)}" rx="{f(3 * s)}" fill="{hz("#ffd25a")}"/>'
            + f'<path d="M{f(lx - 14 * s)} {f(ly - 96 * s)}L{f(lx)} {f(ly - 110 * s)}L{f(lx + 14 * s)} {f(ly - 96 * s)}Z" fill="{hz("#e0604f")}"/>')
    return grp("island", out, (x, wl))


def waterline(a, wl, amp=7, wl_len=150, ph=0.0):
    """Underside refraction band + the front wave lip (separate groups so they can bob)."""
    pts = lambda off, A, L, p: [(x, wl + off + A * math.sin(2 * math.pi * x / L + p)) for x in range(-40, W + 41, 10)]
    top = pts(0, amp, wl_len, ph)
    band = pts(46, 5, 110, ph + 1)
    d = "M" + " L".join(f"{f(x)} {f(y)}" for x, y in top) + " L" + " L".join(f"{f(x)} {f(y)}" for x, y in reversed(band)) + "Z"
    rng = random.Random(int(wl))
    glints = "".join(f'<path d="M{f(x)} {f(y)}q{f(w / 2)} -5 {f(w)} 0" fill="none" stroke="#ffffff" stroke-width="3" stroke-linecap="round" opacity=".7"/>'
                     for x, y, w in [(rng.uniform(0, W), wl + rng.uniform(14, 40), rng.uniform(18, 46)) for _ in range(46)])
    refraction = f'<path d="{d}" fill="#c9f5f2" opacity=".55"/>' + glints
    lip = (f'<path d="M{" L".join(f"{f(x)} {f(y)}" for x, y in top)}" fill="none" stroke="#ffffff" stroke-width="6" stroke-linecap="round"/>'
           + "".join(f'<path d="M{f(x - 16)} {f(wl - 2 + amp * math.sin(2 * math.pi * x / wl_len + ph))}q8 -9 18 -4" fill="none" stroke="#ffffff" stroke-width="4" stroke-linecap="round"/>'
                     for x in range(40, W, 150)))
    return grp("refraction", refraction, (W / 2, wl)), grp("waves-front", lip, (W / 2, wl))


def underwater(a, wl, deep="#1f8aa3"):
    g = a.linear("uw", [(0, "#a6ece4"), (.12, "#6fd4cf"), (.55, "#3fc0c4"), (1, deep)], 0, wl, 0, H)
    top = [(x, wl + 7 * math.sin(2 * math.pi * x / 150)) for x in range(-40, W + 41, 10)]
    d = "M" + " L".join(f"{f(x)} {f(y)}" for x, y in top) + f" L{W + 40} {H} L-40 {H}Z"
    return f'<path class="sea" d="{d}" fill="{g}"/>'


def uw_rays(a, wl, xs):
    out = ""
    for i, (x, w) in enumerate(xs):
        g = a.linear("ur", [(0, "#ffffff", .5), (1, "#ffffff", 0)], 0, wl, 0, H)
        out += grp(f"ray ray-{i}", f'<path d="M{f(x - w / 2)} {f(wl)}L{f(x + w / 2)} {f(wl)}L{f(x + w * .3 - 170)} {H}L{f(x - w - 170)} {H}Z" fill="{g}"/>', (x, wl))
    return grp("uw-rays", out)


def reef_floor(a, y0, items, seed=3):
    pts = [(x, y0 + 22 * math.sin(x / 150 + seed) + 9 * math.sin(x / 47)) for x in range(-40, W + 41, 20)]
    d = "M" + " L".join(f"{f(x)} {f(y)}" for x, y in pts) + f" L{W + 40} {H} L-40 {H}Z"
    g = a.linear("sand", [(0, "#fbecc8"), (.12, "#f1d9a6"), (1, "#d8b77a")], 0, y0 - 30, 0, H)
    yat = lambda x: y0 + 22 * math.sin(x / 150 + seed) + 9 * math.sin(x / 47)
    out = f'<path d="{d}" fill="{g}" stroke="{INK}" stroke-width="3"/>'
    rng = random.Random(seed)
    out += "".join(f'<path d="M{f(x)} {f(yat(x) + rng.uniform(16, 70))}q12 -5 24 0t24 0" fill="none" stroke="#d8b77a" stroke-width="2.4" stroke-linecap="round" opacity=".8"/>' for x in range(30, W, 120))
    for fn in items:
        out += fn(yat)
    return grp("reef", out)


def bubbles(xs, seed, cls="bubbles"):
    rng = random.Random(seed)
    out = ""
    for k, (x, y, n) in enumerate(xs):
        for i in range(n):
            r = rng.uniform(4, 11) * (1 - i * .08)
            cx, cy = x + rng.uniform(-10, 10) + math.sin(i) * 6, y - i * rng.uniform(26, 36)
            out += grp(f"bubble b-{k}-{i}",
                       f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(r)}" fill="#ffffff" fill-opacity=".18" stroke="#ffffff" stroke-width="2.4"/>'
                       f'<path d="M{f(cx - r * .5)} {f(cy - r * .2)}q{f(r * .2)} {f(-r * .45)} {f(r * .55)} {f(-r * .5)}" fill="none" stroke="#ffffff" stroke-width="2" stroke-linecap="round"/>',
                       (cx, cy))
    return grp(cls, out)


def school(x, y, n, seed, scale=1.0, cls="school"):
    """A swirl of school-fish (inline copies)."""
    rng = random.Random(seed)
    fish_svg = open(os.path.join(ART, "ponor", "school-fish.svg")).read()
    inner = re.sub(r'^.*?<svg[^>]*>', '', fish_svg, count=1, flags=re.S).replace("</svg>", "")
    inner = re.sub(r'<g class="body"[^>]*>', '<g>', inner)
    sym = ""
    out = ""
    for i in range(n):
        t = i / n * math.tau * 1.15
        rx, ry = 120 * scale, 46 * scale
        fx = x + rx * math.cos(t) + rng.uniform(-14, 14)
        fy = y + ry * math.sin(t) * .9 + rng.uniform(-10, 10)
        s = scale * rng.uniform(.8, 1.15) * 1.25
        out += f'<g class="fish f-{i}" transform="translate({f(fx - 30 * s)} {f(fy - 13 * s)}) scale({f(s)})">{inner}</g>'
    return grp(cls, out, (x, y))


def kelp_stand(a, xs, y, seed):
    return "".join(sea.kelp(a, x, y + 6, h, seed + i, segs=4) for i, (x, h) in enumerate(xs))


# ================================================================== the nicer boat
def boat_v2(a, x, wl, w=470):
    """Wooden rowing boat with planks, white gunwale, lifebuoy, diver-down flag, anchor rope into the water.
    Returns (above, below): 'below' = the refracted underwater part of the hull + rope (draw under the refraction band)."""
    top_y = wl - 54
    hull = smooth([(x - w / 2, top_y + 4), (x + w / 2 + 26, top_y - 4), (x + w / 2 - 6, wl + 2), (x + w * .3, wl + 32),
                   (x - w * .32, wl + 32), (x - w / 2 + 16, wl + 4)], t=.16)
    hg = a.linear("hull", [(0, "#ffb08f"), (.35, "#e9724f"), (1, "#a9452f")], 0, top_y, 0, wl + 32)
    cl = a.clip("hull", hull)
    planks = "".join(f'<path d="M{f(x - w / 2)} {f(top_y + 16 + k * 15)}Q{f(x)} {f(top_y + 26 + k * 17)} {f(x + w / 2 + 20)} {f(top_y + 10 + k * 15)}" fill="none" stroke="#a9452f" stroke-width="2.4" opacity=".55"/>' for k in range(5))
    above = f'<path d="{hull}" fill="{hg}"/><g clip-path="{cl}">{planks}'
    above += f'<path d="M{f(x - w / 2 + 6)} {f(top_y + 30)}Q{f(x)} {f(top_y + 40)} {f(x + w / 2 + 14)} {f(top_y + 24)}" fill="none" stroke="#fffaf0" stroke-width="9" stroke-linecap="round"/>'
    above += f'<path d="M{f(x + w * .1)} {f(top_y + 46)}l60 -4" fill="none" stroke="#ffffff" stroke-width="5" opacity=".35" stroke-linecap="round"/></g>'
    above += f'<path d="{hull}" fill="none" stroke="{INK}" stroke-width="3.4" stroke-linejoin="round"/>'
    # gunwale rail
    above += f'<path d="M{f(x - w / 2 - 6)} {f(top_y + 2)}L{f(x + w / 2 + 30)} {f(top_y - 6)}" stroke="{INK}" stroke-width="15" stroke-linecap="round"/>'
    above += f'<path d="M{f(x - w / 2 - 6)} {f(top_y + 2)}L{f(x + w / 2 + 30)} {f(top_y - 6)}" stroke="#e2b26e" stroke-width="9" stroke-linecap="round"/>'
    above += f'<path d="M{f(x - w / 2)} {f(top_y)}L{f(x + w / 2 + 24)} {f(top_y - 8)}" stroke="#fff3d6" stroke-width="2.4" stroke-linecap="round" opacity=".8"/>'
    # name plate (no text) + lifebuoy
    bx, by = x - w * .2, top_y + 34
    above += (f'<circle cx="{f(bx)}" cy="{f(by)}" r="22" fill="#ffffff" stroke="{INK}" stroke-width="3"/>'
              f'<circle cx="{f(bx)}" cy="{f(by)}" r="10" fill="#e9724f" stroke="{INK}" stroke-width="3"/>'
              + "".join(f'<path d="M{f(bx + 11 * math.cos(math.radians(t)))} {f(by + 11 * math.sin(math.radians(t)))}L{f(bx + 21 * math.cos(math.radians(t)))} {f(by + 21 * math.sin(math.radians(t)))}" stroke="#e0453a" stroke-width="9"/>' for t in (45, 135, 225, 315))
              + f'<circle cx="{f(bx)}" cy="{f(by)}" r="22" fill="none" stroke="{INK}" stroke-width="3"/><circle cx="{f(bx)}" cy="{f(by)}" r="10" fill="none" stroke="{INK}" stroke-width="3"/>'
              f'<path d="M{f(bx - 12)} {f(by - 14)}q8 -6 16 -4" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" opacity=".9"/>')
    # oar
    ox = x - w * .05
    above += (f'<path d="M{f(ox)} {f(top_y - 10)}L{f(ox - 150)} {f(wl + 34)}" stroke="{INK}" stroke-width="11" stroke-linecap="round"/>'
              f'<path d="M{f(ox)} {f(top_y - 10)}L{f(ox - 150)} {f(wl + 34)}" stroke="#d9a464" stroke-width="5.5" stroke-linecap="round"/>')
    # mast + diver-down flag (flag is its own group: it flutters)
    mx = x - w * .36
    above += (f'<path d="M{f(mx)} {f(top_y + 2)}V{f(top_y - 150)}" stroke="{INK}" stroke-width="8" stroke-linecap="round"/>'
              f'<path d="M{f(mx)} {f(top_y + 2)}V{f(top_y - 150)}" stroke="#d9a464" stroke-width="4" stroke-linecap="round"/>'
              f'<circle cx="{f(mx)}" cy="{f(top_y - 154)}" r="6" fill="#ffd25a" stroke="{INK}" stroke-width="2.4"/>')
    fl = f"M{f(mx + 3)} {f(top_y - 146)}c22 -6 40 6 64 0q-5 18 0 38c-24 6 -42 -6 -64 0z"
    flag = (f'<path d="{fl}" fill="#e0453a" stroke="{INK}" stroke-width="2.8" stroke-linejoin="round"/>'
            f'<path d="M{f(mx + 5)} {f(top_y - 144)}L{f(mx + 64)} {f(top_y - 112)}" stroke="#ffffff" stroke-width="9"/>'
            f'<path d="{fl}" fill="none" stroke="{INK}" stroke-width="2.8" stroke-linejoin="round"/>')
    above += grp("flag", flag, (mx, top_y - 128))
    # below the surface: refracted hull bottom + anchor rope
    below = (f'<path d="M{f(x - w * .42)} {f(wl + 10)}Q{f(x)} {f(wl + 62)} {f(x + w * .42)} {f(wl + 10)}" fill="#b5503a" opacity=".35" transform="translate(6 4)"/>'
             f'<path d="M{f(x + w * .35)} {f(wl + 20)}Q{f(x + w * .42)} {f(wl + 190)} {f(x + w * .30)} {f(wl + 330)}" fill="none" stroke="#c9a46a" stroke-width="4" stroke-dasharray="7 5" opacity=".9"/>')
    return above, below


# ================================================================== logo
def glyph_bbox(d):
    nums = [float(v) for v in re.findall(r"-?\d+(?:\.\d+)?", d)]
    xs, ys = nums[0::2], nums[1::2]
    return min(xs), min(ys), max(xs), max(ys)


def haček(a, cx, top, s, fill):
    """Háček drawn as a chubby wave-V with a highlight (reads as a háček, feels like water)."""
    d = (f"M{f(cx - 26 * s)} {f(top - 30 * s)}Q{f(cx - 18 * s)} {f(top - 36 * s)} {f(cx - 12 * s)} {f(top - 28 * s)}L{f(cx)} {f(top - 12 * s)}"
         f"L{f(cx + 12 * s)} {f(top - 28 * s)}Q{f(cx + 18 * s)} {f(top - 36 * s)} {f(cx + 26 * s)} {f(top - 30 * s)}L{f(cx + 8 * s)} {f(top - 2 * s)}"
         f"Q{f(cx)} {f(top + 6 * s)} {f(cx - 8 * s)} {f(top - 2 * s)}Z")
    return (f'<path d="{d}" fill="{INK}" transform="translate(0 {f(7 * s)})"/>'
            f'<path d="{d}" fill="{fill}" stroke="{INK}" stroke-width="{f(5.5 * s)}" stroke-linejoin="round"/>'
            f'<path d="M{f(cx - 20 * s)} {f(top - 28 * s)}L{f(cx - 10 * s)} {f(top - 16 * s)}" stroke="#ffffff" stroke-width="{f(4 * s)}" stroke-linecap="round" opacity=".8"/>')


def carka_drop(a, cx, top, s, fill):
    """Čárka drawn as a slanted water drop."""
    d = (f"M{f(cx + 14 * s)} {f(top - 44 * s)}Q{f(cx + 20 * s)} {f(top - 30 * s)} {f(cx + 6 * s)} {f(top - 12 * s)}"
         f"Q{f(cx - 4 * s)} {f(top - 2 * s)} {f(cx - 12 * s)} {f(top - 10 * s)}Q{f(cx - 16 * s)} {f(top - 22 * s)} {f(cx + 14 * s)} {f(top - 44 * s)}Z")
    return (f'<path d="{d}" fill="{INK}" transform="translate(0 {f(7 * s)})"/>'
            f'<path d="{d}" fill="{fill}" stroke="{INK}" stroke-width="{f(5.5 * s)}" stroke-linejoin="round"/>'
            f'<circle cx="{f(cx - 4 * s)}" cy="{f(top - 14 * s)}" r="{f(3.4 * s)}" fill="#ffffff" opacity=".85"/>')


def logo(lang):
    a = Art(f"logo{lang}", seed=401)
    word_specs = {
        "cs": [("Mořský", "sun"), ("svět", "sea")],
        "en": [("Ocean", "sun"), ("World", "sea")],
    }[lang]
    upm = GLYPHS["upm"]
    size = 210                      # em in logo units
    k = size / upm
    fills = {"sun": a.linear("fsun", [(0, "#fff8d6"), (.45, "#ffd25a"), (1, "#ff9a4a")], 0, 0, 0, 1, user=False),
             "sea": a.linear("fsea", [(0, "#f2fffd"), (.4, "#8fe3dc"), (1, "#2fa9c6")], 0, 0, 0, 1, user=False)}
    acc_fill = {"sun": "#ff8a6a", "sea": "#3fc0c4"}
    base_y = 250
    x = 40
    letters = ""
    i = 0
    tops = []
    for wi, (word, tone) in enumerate(word_specs):
        for ch in word:
            base = {"ř": "r", "ý": "y", "ě": "e"}.get(ch, ch)
            gl = GLYPHS["chars"][base]
            bx0, by0, bx1, by1 = glyph_bbox(gl["d"])
            adv = gl["adv"] * k
            dy = 9 * math.sin(i * .95 + .4)
            rot = 3.5 * math.sin(i * 1.3 + .9)
            cx = x + (bx0 + bx1) / 2 * k
            tr = f"translate({f(x)} {f(base_y + dy)}) scale({f(k)} {f(-k)})"
            path = f'<path d="{gl["d"]}" transform="{tr}"'
            shadow_tr = f"translate({f(x)} {f(base_y + dy + 9)}) scale({f(k)} {f(-k)})"
            cid = a.uid("lc")
            a.defs.append(f'<clipPath id="{cid}">{path}/></clipPath>')
            top_px = base_y + dy - by1 * k
            inner = (f'<path d="{gl["d"]}" transform="{shadow_tr}" fill="{INK}"/>'
                     f'{path} fill="none" stroke="{INK}" stroke-width="{f(17 / k)}" stroke-linejoin="round"/>'
                     f'{path} fill="{fills[tone]}"/>'
                     f'<g clip-path="url(#{cid})"><ellipse cx="{f(cx - 6)}" cy="{f(top_px + 16)}" rx="{f(adv * .38)}" ry="10" fill="#ffffff" opacity=".55"/>'
                     f'<path d="M{f(x - 10)} {f(base_y + dy - 6)}L{f(x + adv + 10)} {f(base_y + dy - 6)}" stroke="{INK}" stroke-width="14" opacity=".12"/></g>')
            if ch in "řě":
                inner += haček(a, cx + (6 if ch == "ř" else 0), top_px - 4, 1.0, acc_fill[tone])
            if ch == "ý":
                inner += carka_drop(a, cx + 8, top_px - 4, 1.0, acc_fill[tone])
            letters += grp(f"letter l-{i}", inner, (cx, base_y + dy), f' transform="rotate({f(rot)} {f(cx)} {f(base_y + dy - 60)})"')
            tops.append((cx, top_px))
            x += adv + 2
            i += 1
        x += 64 if wi == 0 else 0
    total_w = x + 40
    # swash: a wave under the words with a white crest + bubbles rising
    sw_y = base_y + 46
    pts = [(xx, sw_y + 10 * math.sin(xx / 46)) for xx in range(30, int(total_w) - 10, 8)]
    swd = "M" + " L".join(f"{f(px)} {f(py)}" for px, py in pts)
    swash = (f'<path d="{swd}" fill="none" stroke="{INK}" stroke-width="20" stroke-linecap="round"/>'
             f'<path d="{swd}" fill="none" stroke="#3fc0c4" stroke-width="12" stroke-linecap="round"/>'
             f'<path d="{swd}" fill="none" stroke="#e9fbff" stroke-width="3.5" stroke-linecap="round" transform="translate(0 -3)"/>')
    bub = ""
    rng = random.Random(4)
    for bx, by, r in ((tops[1][0] + 4, tops[1][1] - 26, 9), (tops[1][0] + 18, tops[1][1] - 52, 6), (total_w - 54, base_y - 140, 12),
                      (total_w - 30, base_y - 176, 8), (total_w - 44, base_y - 206, 5), (30, base_y - 120, 7)):
        bub += grp("logo-bubble", f'<circle cx="{f(bx)}" cy="{f(by)}" r="{f(r)}" fill="#ffffff" fill-opacity=".35" stroke="{INK}" stroke-width="3"/>'
                   f'<path d="M{f(bx - r * .45)} {f(by - r * .15)}q{f(r * .2)} {f(-r * .4)} {f(r * .5)} {f(-r * .45)}" fill="none" stroke="#fff" stroke-width="2.4" stroke-linecap="round"/>', (bx, by))
    Wl, Hl = total_w, 320
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" class="logo" data-lang="{lang}" viewBox="0 0 {f(Wl)} {Hl}" role="img" '
           f'aria-label="{"Mořský svět" if lang == "cs" else "Ocean World"}"><title>{"Mořský svět" if lang == "cs" else "Ocean World"}</title>'
           f'<defs>{"".join(a.defs)}</defs>{grp("swash", swash, (Wl / 2, sw_y))}{letters}{grp("logo-bubbles", bub)}</svg>\n')
    write(f"logo-{lang}.svg", svg)


# ================================================================== play bubble
def play_bubble():
    a = Art("playb", seed=411)
    S = 220
    c = S / 2
    r = 92
    body = a.radial("pb", [(0, "#ffffff", .55), (.55, "#b9f1ee", .55), (.86, "#62d3d0", .8), (1, "#2fa9c6", .95)], cx="42%", cy="38%", r="62%")
    out = (f'<circle cx="{c}" cy="{c + 6}" r="{r}" fill="#0b3a4a" opacity=".22"/>'
           + grp("bubble-body", f'<circle cx="{c}" cy="{c}" r="{r}" fill="{body}" stroke="{INK}" stroke-width="5"/>'
                 f'<circle cx="{c}" cy="{c}" r="{r - 7}" fill="none" stroke="#ffffff" stroke-width="4" opacity=".7"/>', (c, c)))
    tri = f"M{c - 26} {c - 40}L{c + 44} {c}L{c - 26} {c + 40}Z"
    glyph = (f'<path d="{tri}" fill="{INK}" transform="translate(0 6)"/>'
             f'<path d="{tri}" fill="#ffc845" stroke="{INK}" stroke-width="7" stroke-linejoin="round"/>'
             f'<path d="M{c - 16} {c - 22}L{c + 14} {c - 4}" stroke="#fff6d0" stroke-width="7" stroke-linecap="round"/>')
    shine = (f'<path d="M{c - 62} {c - 22}A66 66 0 0 1 {c - 10} {c - 70}" fill="none" stroke="#ffffff" stroke-width="13" stroke-linecap="round"/>'
             f'<circle cx="{c - 66}" cy="{c + 4}" r="6.5" fill="#ffffff"/>'
             f'<path d="M{c + 50} {c + 58}A70 70 0 0 1 {c + 20} {c + 78}" fill="none" stroke="#ffffff" stroke-width="7" stroke-linecap="round" opacity=".8"/>')
    sats = ""
    for k, (x, y, rr) in enumerate(((c + 92, c - 74, 14), (c + 76, c - 104, 8), (c - 98, c + 62, 10))):
        sats += grp(f"satellite s-{k}", f'<circle cx="{x}" cy="{y}" r="{rr}" fill="#ffffff" fill-opacity=".35" stroke="{INK}" stroke-width="3"/>'
                    f'<path d="M{x - rr * .45} {y - rr * .15}q{rr * .2} {-rr * .4} {rr * .5} {-rr * .45}" fill="none" stroke="#fff" stroke-width="2.4" stroke-linecap="round"/>', (x, y))
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" class="play-bubble" viewBox="-20 -20 {S + 40} {S + 40}" data-pivot="{c} {c}" role="img" aria-label="Začneme?">'
           f'<defs>{"".join(a.defs)}</defs>{out}{grp("bubble-glyph", glyph, (c, c))}{grp("bubble-shine", shine, (c, c))}{grp("satellites", sats)}</svg>\n')
    write("play-bubble.svg", svg)


# ================================================================== door objects (home)
def door_sea():
    """Můj kousek moře = a round glass bowl with sand, seaweed, a starfish and a clownfish (her own little sea)."""
    a = Art("dsea", seed=421)
    S = 200
    cx, cy, r = 100, 108, 76
    glass = a.radial("gl", [(0, "#ffffff", .35), (.7, "#c9f5f2", .45), (1, "#7fd6d2", .7)], cx="40%", cy="35%", r="70%")
    water = a.linear("wa", [(0, "#8fe3dc"), (1, "#2fa9c6")], 0, cy - 40, 0, cy + r)
    bowl = smooth([(cx - 46, cy - 64), (cx - 74, cy - 20), (cx - 70, cy + 40), (cx - 30, cy + r - 6), (cx + 30, cy + r - 6), (cx + 70, cy + 40), (cx + 74, cy - 20), (cx + 46, cy - 64)], t=.18)
    cl = a.clip("bw", bowl)
    inside = (f'<rect x="0" y="{cy - 36}" width="{S}" height="{S}" fill="{water}"/>'
              f'<path d="M{cx - 80} {cy - 36}q20 -8 40 0t40 0t40 0t40 0" fill="none" stroke="#e9fbff" stroke-width="4"/>'
              f'<path d="M{cx - 80} {cy + 50}Q{cx} {cy + 34} {cx + 80} {cy + 52}L{cx + 80} {S}L{cx - 80} {S}Z" fill="#f1d9a6" stroke="{INK}" stroke-width="2.4"/>'
              + sea.seagrass(a, cx - 36, cy + 50, 56, 5) + sea.seagrass(a, cx + 44, cy + 50, 40, 4))
    fish = (nest("klaun", cx + 6, cy - 2, 62, "door-fish") + nest("hvezdice", cx - 6, cy + 54, 44, "door-star"))
    out = (f'<ellipse cx="{cx}" cy="{cy + r - 2}" rx="62" ry="10" fill="#0b3a4a" opacity=".22"/>'
           f'<g clip-path="{cl}">{inside}{fish}</g>'
           f'<path d="{bowl}" fill="{glass}"/>'
           f'<path d="M{cx - 54} {cy - 30}Q{cx - 64} {cy + 8} {cx - 50} {cy + 40}" fill="none" stroke="#ffffff" stroke-width="7" stroke-linecap="round" opacity=".85"/>'
           f'<path d="{bowl}" fill="none" stroke="{INK}" stroke-width="4"/>'
           f'<ellipse cx="{cx}" cy="{cy - 64}" rx="46" ry="9" fill="#e9fbff" fill-opacity=".6" stroke="{INK}" stroke-width="4"/>')
    return out, (S, S), "Můj kousek moře", a.defs


def door_quiz():
    """Kvíz = an open clam holding a big pearl with a „?“ (a riddle pearl). Not a bottle: bottles are trash in this game."""
    a = Art("dquiz", seed=422)
    S = 200
    cx, cy = 100, 120
    lower = smooth([(cx - 82, cy), (cx - 60, cy + 44), (cx, cy + 58), (cx + 60, cy + 44), (cx + 82, cy)], t=.2)
    upper = smooth([(cx - 82, cy - 6), (cx - 70, cy - 70), (cx - 20, cy - 98), (cx + 20, cy - 98), (cx + 70, cy - 70), (cx + 82, cy - 6), (cx + 40, cy - 22), (cx, cy - 26), (cx - 40, cy - 22)], t=.18)
    shell = ("#f6b8c4", "#ffe2e8", "#d97f94")
    ug = a.shape(upper, shell[0], shell[1], shell[2], cy - 98, cy - 6, hi_box=(cx - 20, cy - 74, 30, 10))
    ug += "".join(f'<path d="M{cx} {cy - 22}L{f(cx + 76 * math.cos(math.radians(t)))} {f(cy - 14 - 80 * math.sin(math.radians(t)))}" stroke="{shell[2]}" stroke-width="2.4" opacity=".7"/>' for t in range(20, 170, 20))
    lg = a.shape(lower + "", shell[0], shell[1], shell[2], cy, cy + 58, hi=False)
    inner_lip = f'<path d="M{cx - 76} {cy}Q{cx} {cy + 22} {cx + 76} {cy}Q{cx} {cy - 12} {cx - 76} {cy}Z" fill="#ffe9ef" stroke="{INK}" stroke-width="3"/>'
    pg = a.radial("pearl", [(0, "#ffffff"), (.55, "#f3eefe"), (1, "#c6b8e6")], cx="38%", cy="32%", r="70%")
    pearl = (f'<circle cx="{cx}" cy="{cy - 14}" r="34" fill="{pg}" stroke="{INK}" stroke-width="4"/>'
             f'<path d="M{cx - 12} {cy - 26}a12 12 0 1 1 17 11q-5 3 -5 9" fill="none" stroke="#9b6fd6" stroke-width="7" stroke-linecap="round"/>'
             f'<circle cx="{cx}" cy="{cy + 6}" r="4.4" fill="#9b6fd6"/>'
             f'<path d="M{cx - 22} {cy - 30}q6 -10 16 -12" fill="none" stroke="#fff" stroke-width="5" stroke-linecap="round"/>')
    glint = "".join(f'<path d="M{x} {y - 9}v18M{x - 9} {y}h18" stroke="#ffffff" stroke-width="3.4" stroke-linecap="round"/>' for x, y in ((cx + 50, cy - 62), (cx - 54, cy - 40)))
    out = (f'<ellipse cx="{cx}" cy="{cy + 56}" rx="70" ry="10" fill="#0b3a4a" opacity=".22"/>' + lg + inner_lip + ug + pearl + grp("door-glint", glint))
    return out, (S, S), "Kvíz", a.defs


def door_habitat():
    """Kdo kde bydlí? = a little sea map: a rolled-out scroll with the four floors of the sea, animal dots and a compass."""
    a = Art("dhab", seed=423)
    S = 200
    x0, x1, y0, y1 = 30, 170, 40, 168
    paper = f'<path d="M{x0} {y0}Q{(x0 + x1) / 2} {y0 - 8} {x1} {y0}L{x1} {y1}Q{(x0 + x1) / 2} {y1 + 8} {x0} {y1}Z" fill="#fdf6e9" stroke="{INK}" stroke-width="4"/>'
    bands = ""
    cols = ("#8fe3dc", "#6fc3b4", "#3a9fd6", "#12305d")
    for k, c in enumerate(cols):
        ya = y0 + 14 + k * 27
        bands += f'<path d="M{x0 + 10} {ya}Q{(x0 + x1) / 2} {ya - 3} {x1 - 10} {ya}L{x1 - 10} {ya + 27}Q{(x0 + x1) / 2} {ya + 24} {x0 + 10} {ya + 27}Z" fill="{c}"/>'
    bands += f'<path d="M{x0 + 10} {y0 + 14}L{x0 + 48} {y0 + 30}L{x0 + 62} {y0 + 70}L{x0 + 70} {y0 + 122}" fill="none" stroke="#d8b77a" stroke-width="7" stroke-linecap="round"/>'
    dots = "".join(f'<path d="M{x - 9} {y}q9 -8 16 0q-7 8 -16 0z" fill="{c}" stroke="{INK}" stroke-width="1.6"/><path d="M{x + 7} {y}l5 -4v8z" fill="{c}" stroke="{INK}" stroke-width="1.4"/>'
                   for x, y, c in ((112, y0 + 28, "#ff9a4a"), (130, y0 + 56, "#c49a2c"), (104, y0 + 84, "#ffd25a"), (126, y0 + 112, "#9dffc8")))
    rolls = (f'<rect x="{x0 - 10}" y="{y0 - 12}" width="16" height="{y1 - y0 + 24}" rx="8" fill="#e2b26e" stroke="{INK}" stroke-width="3.4"/>'
             f'<rect x="{x1 - 6}" y="{y0 - 12}" width="16" height="{y1 - y0 + 24}" rx="8" fill="#e2b26e" stroke="{INK}" stroke-width="3.4"/>')
    comp_c = (150, 152)
    compass = (f'<circle cx="{comp_c[0]}" cy="{comp_c[1]}" r="24" fill="#ffd25a" stroke="{INK}" stroke-width="3.4"/>'
               f'<circle cx="{comp_c[0]}" cy="{comp_c[1]}" r="16" fill="#fdf6e9" stroke="{INK}" stroke-width="2.4"/>'
               f'<path d="M{comp_c[0]} {comp_c[1] - 14}L{comp_c[0] + 5} {comp_c[1]}L{comp_c[0]} {comp_c[1] + 14}L{comp_c[0] - 5} {comp_c[1]}Z" fill="#e0453a" stroke="{INK}" stroke-width="1.8"/>')
    out = f'<ellipse cx="100" cy="{y1 + 14}" rx="72" ry="9" fill="#0b3a4a" opacity=".22"/>' + paper + bands + dots + rolls + grp("door-needle", compass, comp_c)
    return out, (S, S), "Kdo kde bydlí?", a.defs


def doors():
    for name, fn in (("door-sea", door_sea), ("door-quiz", door_quiz), ("door-habitat", door_habitat)):
        body, (w, h), label, defs = fn()
        write(f"{name}.svg", f'<svg xmlns="http://www.w3.org/2000/svg" class="door-art" data-door="{name[5:]}" viewBox="0 0 {w} {h}" '
                             f'data-pivot="{w / 2} {h}" role="img" aria-label="{label}"><title>{label}</title><defs>{"".join(defs)}</defs>{grp("door-body", body, (w / 2, h))}</svg>\n')


# ================================================================== scenes
def title_scene():
    a = Art("title", seed=431)
    WL = 520
    body = sky(a, WL)
    body += sun(a, 1400, 110, 54)
    body += cloud(a, 330, 120, .8, 1) + cloud(a, 840, 70, .55, 2) + cloud(a, 1420, 300, .6, 3) + cloud(a, 600, 300, .45, 4)
    body += grp("gulls", gull(a, 300, 330, .9, 1) + gull(a, 380, 300, .65, 2) + gull(a, 1250, 330, .8, 3))
    body += island(a, 330, WL, 1.05)
    body += f'<path class="horizon-glints" d="' + "".join(f"M{x} {WL - 8}h{w}" for x, w in ((560, 40), (720, 26), (900, 60), (1330, 34))) + f'" stroke="#ffffff" stroke-width="3" stroke-linecap="round" opacity=".8"/>'
    # underwater
    uw = underwater(a, WL)
    uw += uw_rays(a, WL, ((330, 110), (640, 70), (960, 140), (1250, 80), (1500, 110)))
    whale = nest("keporkak", 1240, 720, 420, "whale-far", flip=True)
    uw += f'<g class="whale-far-wrap" opacity=".42">{whale}</g>'
    uw += school(1010, 640, 16, 7, 1.0)
    uw += nest("meduza", 300, 690, 110, "jelly")
    uw += kelp_stand(a, ((1440, 360), (1510, 440), (1560, 330)), 950, 70)
    items = [
        lambda y: sea.brain_coral(a, 180, y(180) + 8, 60, sea.CORAL["yellow"]),
        lambda y: sea.branch_coral(a, 300, y(300) + 6, 160, sea.CORAL["violet"], 5, 3),
        lambda y: sea.fan_coral(a, 430, y(430) + 6, 150, sea.CORAL["red"]),
        lambda y: sea.seagrass(a, 540, y(540) + 10, 70, 8, sway_cls="sway"),
        lambda y: sea.tube_sponge(a, 1180, y(1180) + 8, 100, sea.CORAL["orange"]),
        lambda y: sea.table_coral(a, 1320, y(1320) + 8, 170, sea.CORAL["teal"]),
        lambda y: sea.branch_coral(a, 1060, y(1060) + 6, 130, sea.CORAL["pink"], 4, 9),
        lambda y: sea.brain_coral(a, 820, y(820) + 10, 46, sea.CORAL["pink"]),
        lambda y: sea.seagrass(a, 900, y(900) + 10, 60, 7, sway_cls="sway"),
    ]
    uw += reef_floor(a, 930, items, seed=5)
    boat_above, boat_below = boat_v2(a, 1010, WL, 420)
    uw += boat_below
    refr, lip = waterline(a, WL)
    uw += refr
    uw += bubbles(((560, 840, 6), (760, 900, 5), (1240, 880, 5), (210, 880, 4)), 9)
    body += grp("underwater", uw)
    # boat above water + diver + turtle
    boat_grp = boat_above + diver_sitting(a, 1010 + 200, WL - 54, 1.0)
    body += grp("boat", boat_grp, (1010, WL))
    body += nest("guide-turtle", 1350, WL + 14, 140, "turtle")
    # dolphin leaping through the surface (+ splash) — animate along data-arc
    dol = nest("delfin", 640, WL - 110, 250, "dolphin", rot=-28)
    splash = ""
    for k, (dx, h) in enumerate(((-90, 46), (-70, 70), (-50, 50))):
        splash += f'<path d="M{640 + dx} {WL}q-6 -{h} -2 -{h + 12}q6 {h * .4} 8 {h + 12}" fill="#ffffff" stroke="#bfeaf0" stroke-width="2"/>'
    splash += "".join(f'<circle cx="{640 + dx}" cy="{WL - dy}" r="{r}" fill="#ffffff"/>' for dx, dy, r in ((-110, 54, 6), (-36, 80, 5), (-128, 30, 4), (-20, 44, 4)))
    body += grp("splash", splash, (560, WL)) + dol
    body += lip
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" class="scene title-scene" viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMid slice" '
           f'data-waterline="{WL}" data-arc="440 {WL + 40} 840 {WL + 40} 220" role="img" aria-label="Mořský svět"><defs>{"".join(a.defs)}</defs>{body}</svg>\n')
    write("title.svg", svg)


def home_scene():
    a = Art("home2", seed=441)
    WL = 470
    body = sky(a, WL)
    body += sun(a, 1040, 150, 54)
    body += cloud(a, 300, 150, .7, 1) + cloud(a, 760, 80, .5, 2) + cloud(a, 1380, 210, .65, 3)
    body += grp("gulls", gull(a, 560, 230, .8, 1) + gull(a, 640, 196, .6, 2))
    body += island(a, 1300, WL, .85)
    uw = underwater(a, WL, deep="#1d7f99")
    uw += uw_rays(a, WL, ((260, 100), (560, 70), (900, 130), (1230, 80)))
    uw += school(1180, 600, 12, 3, .85)
    uw += kelp_stand(a, ((1460, 380), (1530, 450)), 960, 80)
    uw += kelp_stand(a, ((150, 330),), 950, 90)
    items = [
        lambda y: sea.rock(a, 300, y(300) + 34, 230, 120),
        lambda y: sea.brain_coral(a, 450, y(450) + 8, 50, sea.CORAL["yellow"]),
        lambda y: sea.branch_coral(a, 1250, y(1250) + 6, 150, sea.CORAL["violet"], 5, 3),
        lambda y: sea.fan_coral(a, 1370, y(1370) + 6, 150, sea.CORAL["red"]),
        lambda y: sea.rock(a, 1100, y(1100) + 30, 170, 80),
        lambda y: sea.seagrass(a, 640, y(640) + 10, 60, 8, sway_cls="sway"),
        lambda y: sea.seagrass(a, 980, y(980) + 10, 64, 8, sway_cls="sway"),
    ]
    uw += reef_floor(a, 900, items, seed=2)
    # peeking animals (small, so the doors stay the subject)
    peek = (nest("chobotnice", 1190, 846, 88, "peek peek-octopus") + nest("krab", 1060, 868, 80, "peek peek-crab")
            + nest("konik", 980, 800, 46, "peek peek-seahorse") + nest("klaun", 1300, 760, 70, "peek peek-clown", flip=True))
    uw += grp("peekers", peek)
    boat_above, boat_below = boat_v2(a, 600, WL, 470)
    uw += boat_below
    refr, lip = waterline(a, WL, ph=.7)
    uw += refr
    uw += bubbles(((760, 860, 5), (1180, 700, 4), (420, 760, 4)), 13)
    body += grp("underwater", uw)
    body += grp("boat", boat_above + diver_sitting(a, 600 + 225, WL - 54, 1.0), (600, WL))
    body += lip
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" class="scene home-scene-v2" viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMid slice" '
           f'data-waterline="{WL}" data-turtle="310 {WL + 6}" role="img" aria-label="Loďka na hladině"><defs>{"".join(a.defs)}</defs>{body}</svg>\n')
    write("home.svg", svg)



# ================================================================== quiz + summary backgrounds, cross-section v2, flag buttons
def calm_reef_bg(name, label, wl_bright=True, golden=False):
    """A calm reef 'stage': painterly water, hazy reef planes, coral clusters only at the left/right edges,
    an open middle for UI cards. 1600 x 1000, xMidYMid slice."""
    a = Art(name.replace("-", ""), seed=451 + len(name))
    top = "#ffe9b0" if golden else "#a6ece4"
    g = a.linear("w", [(0, top), (.16, "#8fe3dc"), (.55, "#3fc0c4"), (1, "#1f8aa3")], 0, 0, 0, H)
    body = f'<rect width="{W}" height="{H}" fill="{g}"/>'
    for x, y, rx, ry, op in ((400, 90, 420, 150, .25), (1200, 60, 480, 160, .22), (800, 380, 520, 160, .1)):
        lp = a.radial("lp", [(0, "#ffffff" if not golden else "#fff3c4", op), (1, "#ffffff", 0)], cx="50%", cy="50%", r="50%")
        body += f'<ellipse cx="{x}" cy="{y}" rx="{rx}" ry="{ry}" fill="{lp}"/>'
    body += uw_rays(a, 0, ((260, 110), (620, 70), (980, 140), (1340, 90)))
    for y0, col, op, sd in ((800, mix("#3fc0c4", "#8fe3dc", .4), .5, 3), (850, mix("#3fc0c4", "#239fb0", .45), .7, 4)):
        body += sea.silhouette_reef(a, y0, [(2, 22, sd), (5, 10, sd * .7)], col, op, sd, 150, 50, 120).replace(f'width="{sea.TW}"', f'width="{W}"')
    items = [
        lambda y: sea.fan_coral(a, 80, y(80) + 6, 250, sea.CORAL["violet"]),
        lambda y: sea.rock(a, 240, y(240) + 40, 300, 150, crust="#e98fa6"),
        lambda y: sea.brain_coral(a, 200, y(200) - 90, 50, sea.CORAL["yellow"]),
        lambda y: sea.branch_coral(a, 380, y(380) + 6, 150, sea.CORAL["pink"], 5, 2),
        lambda y: sea.seagrass(a, 470, y(470) + 10, 70, 8, sway_cls="sway"),
        lambda y: sea.seagrass(a, 1130, y(1130) + 10, 64, 8, sway_cls="sway"),
        lambda y: sea.soft_coral(a, 1220, y(1220) + 6, 90, ("#f7b26a", "#ffe0b0", "#cf7b3a")),
        lambda y: sea.table_coral(a, 1350, y(1350) + 8, 190, sea.CORAL["teal"]),
        lambda y: sea.fan_coral(a, 1520, y(1520) + 6, 240, sea.CORAL["red"]),
        lambda y: sea.sea_whip(a, 1440, y(1440) + 6, 170, ("#ffd25a", "#fff1b0", "#d6a02a")),
    ]
    body += reef_floor(a, 900, items, seed=7)
    body += bubbles(((560, 700, 5), (1060, 760, 4), (300, 560, 4), (1300, 600, 4)), 21)
    return body, a


def quiz_bg():
    body, a = calm_reef_bg("quiz-bg", "Kvíz")
    write("quiz-bg.svg", f'<svg xmlns="http://www.w3.org/2000/svg" class="scene quiz-bg" viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMid slice" '
                         f'role="img" aria-label="Kvíz"><defs>{"".join(a.defs)}</defs>{body}</svg>\n')


def summary_bg():
    """End of the dive: looking up from just under the surface toward the boat, warm late light, bubbles rising."""
    a = Art("summarybg", seed=461)
    g = a.linear("w", [(0, "#fff0c4"), (.12, "#bfeee6"), (.45, "#5fd0cc"), (1, "#1f7f99")], 0, 0, 0, H)
    body = f'<rect width="{W}" height="{H}" fill="{g}"/>'
    sunw = a.radial("sw", [(0, "#fffbe6", .95), (.35, "#fff3c4", .55), (1, "#fff3c4", 0)], user=(800, 0, 560))
    body += f'<rect width="{W}" height="{H}" fill="{sunw}"/>'
    body += uw_rays(a, 0, ((420, 120), (700, 90), (980, 150), (1240, 90)))
    # the boat seen from below + its anchor rope (connects the end screen to the home boat)
    hull = smooth([(560, 40), (1040, 40), (1000, 96), (820, 128), (620, 112)], t=.18)
    body += f'<path d="{hull}" fill="#7a4a3a" opacity=".55"/><path d="M1000 96Q1060 300 980 520" fill="none" stroke="#c9a46a" stroke-width="5" stroke-dasharray="8 6" opacity=".8"/>'
    body += f'<path d="M0 40' + "".join(f" L{x} {f(40 + 8 * math.sin(x / 50))}" for x in range(0, W + 1, 20)) + '" fill="none" stroke="#ffffff" stroke-width="5" opacity=".9"/>'
    items = [
        lambda y: sea.kelp(a, 120, y(120) + 6, 420, 61, segs=4),
        lambda y: sea.rock(a, 260, y(260) + 40, 300, 150, crust="#e98fa6"),
        lambda y: sea.branch_coral(a, 420, y(420) + 6, 140, sea.CORAL["pink"], 5, 3),
        lambda y: sea.fan_coral(a, 1260, y(1260) + 6, 220, sea.CORAL["violet"]),
        lambda y: sea.soft_coral(a, 1380, y(1380) + 6, 90, ("#f7b26a", "#ffe0b0", "#cf7b3a")),
        lambda y: sea.kelp(a, 1500, y(1500) + 6, 460, 62, segs=4),
    ]
    body += reef_floor(a, 930, items, seed=11)
    body += bubbles(((300, 820, 8), (640, 900, 7), (960, 880, 8), (1280, 860, 7), (820, 700, 5)), 31)
    write("summary-bg.svg", f'<svg xmlns="http://www.w3.org/2000/svg" class="scene summary-bg" viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMid slice" '
                            f'role="img" aria-label="Konec ponoru"><defs>{"".join(a.defs)}</defs>{body}</svg>\n')


def cross_section_v2():
    a = Art("xsec2", seed=471)
    SKY = 110
    bands = [("utes", SKY, 330, ("#8fe3dc", "#3fc0c4")), ("chaluhy", 330, 540, ("#6fc3b4", "#237479")),
             ("sire-more", 540, 760, ("#3a9fd6", "#164f8c")), ("hlubiny", 760, H, ("#12305d", "#08142e"))]
    sky_g = a.linear("sky", [(0, "#9fd6e8"), (1, "#ffeccc")], 0, 0, 0, SKY)
    body = f'<rect width="{W}" height="{SKY + 10}" fill="{sky_g}"/>' + sun(a, 1460, 52, 28)
    for z, y0, y1, (c0, c1) in bands:
        g = a.linear(z, [(0, c0), (1, c1)], 0, y0, 0, y1)
        body += grp("band", f'<rect x="0" y="{y0}" width="{W}" height="{y1 - y0}" fill="{g}"/>', None, f' data-zone="{z}" data-y0="{y0}" data-y1="{y1}"')
    body += uw_rays(a, SKY, ((700, 90), (1000, 120), (1300, 80)))
    for _, y0, _, _ in bands[1:]:
        body += f'<path d="M0 {y0}H{W}" stroke="#ffffff" stroke-width="3" stroke-dasharray="14 12" opacity=".5"/>'
    # band life (scenery silhouettes, not tappable)
    body += sea.school_silhouette(1100, 640, 18, "#cfe8f8", .45, 3, .9).replace("", "")
    body += f'<g opacity=".35">' + "".join(f'<circle cx="{f(x)}" cy="{f(y)}" r="3" fill="#6ff3ff"/>' for x, y in ((900, 820), (1200, 860), (1420, 800), (1050, 900), (1300, 930))) + '</g>'
    slope = [(0, SKY + 40), (180, 260), (330, 330), (420, 470), (520, 540), (600, 760), (700, 900), (900, 940), (1200, 930), (1600, 950)]
    d = smooth(slope + [(1640, H + 40), (-40, H + 40)], t=.15)
    sg = a.linear("bed", [(0, "#f1d9a6"), (.25, "#b0aa96"), (.5, "#5b5a52"), (.8, "#2b2f52"), (1, "#151833")], 0, SKY, 0, H)
    body += f'<path d="{d}" fill="{sg}"/>'
    body += sea.speckle(a, d, (0, SKY, 900, H), 900, ("#fff6dc", "#3a3a4a", "#d8c9a8"), (1, 3), 5, .45)
    cl = a.clip("bed", d)
    body += f'<g clip-path="{cl}">' + "".join(f'<path d="M{-40} {y}Q{300} {y + 40} {760} {y + 160}" fill="none" stroke="#2a2a3a" stroke-width="3" opacity=".25"/>' for y in range(260, 1000, 90)) + '</g>'
    body += f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="3"/>'
    body += sea.brain_coral(a, 150, 250, 34, sea.CORAL["yellow"]) + sea.branch_coral(a, 250, 290, 80, sea.CORAL["pink"], 4, 2)
    body += sea.fan_coral(a, 330, 334, 90, sea.CORAL["violet"]) + sea.soft_coral(a, 90, 214, 40, ("#f7b26a", "#ffe0b0", "#cf7b3a"))
    body += sea.kelp(a, 380, 410, 160, 51, segs=3) + sea.kelp(a, 460, 500, 190, 52, segs=3) + sea.kelp(a, 520, 540, 150, 53, segs=3)
    o, gl = sea.sea_pen(a, 980, 938, 60)
    o2, gl2 = sea.sea_pen(a, 1300, 932, 50)
    b3, gl3 = sea.bamboo_coral(a, 1150, 936, 80, 3)
    body += o + o2 + b3 + sea.glass_sponge(a, 1420, 942, 60) + grp("glow", gl + gl2 + gl3)
    body += f'<path d="M0 {SKY}' + "".join(f" L{x} {f(SKY + 4 * math.sin(x / 40))}" for x in range(0, W + 1, 20)) + '" fill="none" stroke="#e9fbff" stroke-width="5"/>'
    above, _ = boat_v2(a, 1180, SKY + 4, 440)
    body += f'<g transform="translate(1180 {SKY + 4}) scale(.34) translate(-1180 {-(SKY + 4)})">{above}</g>'
    write("cross-section.svg", f'<svg xmlns="http://www.w3.org/2000/svg" class="scene cross-section" viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMid slice" '
                               f'role="img" aria-label="Řez mořem: útes, chaluhy, širé moře, hlubiny"><defs>{"".join(a.defs)}</defs>{body}</svg>\n')


def flag_buttons():
    """i-flag-cz-btn / i-flag-en-btn: a round waving-flag badge (48 x 48) appended to art/ui-icons.svg."""
    def wave_rect(x0, y0, x1, y1, amp=2.2):
        top = " ".join(f"L{f(x)} {f(y0 + amp * math.sin((x - x0) / 7))}" for x in range(int(x0), int(x1) + 1, 3))
        bot = " ".join(f"L{f(x)} {f(y1 + amp * math.sin((x - x0) / 7))}" for x in range(int(x1), int(x0) - 1, -3))
        return f"M{f(x0)} {f(y0)} {top} {bot}Z"
    ring = ('<circle cx="24" cy="24" r="21.5" fill="#fdf6e9" stroke="#33243a" stroke-width="2.5"/>')
    clip = lambda i: f'<clipPath id="{i}"><circle cx="24" cy="24" r="17"/></clipPath>'
    cz = (clip("fbcz") + ring + '<g clip-path="url(#fbcz)">'
          f'<path d="{wave_rect(4, 8, 44, 24)}" fill="#ffffff"/><path d="{wave_rect(4, 24, 44, 40)}" fill="#d7141a"/>'
          '<path d="M4 6L26 24L4 42Z" fill="#11457e"/></g>'
          '<circle cx="24" cy="24" r="17" fill="none" stroke="#33243a" stroke-width="2"/>'
          '<path d="M12 14a14 14 0 0 1 9 -5" fill="none" stroke="#ffffff" stroke-width="2.6" stroke-linecap="round" opacity=".85"/>')
    en = (clip("fben") + ring + '<g clip-path="url(#fben)"><rect x="4" y="4" width="40" height="40" fill="#012169"/>'
          '<path d="M4 8L44 40M44 8L4 40" stroke="#ffffff" stroke-width="7"/><path d="M4 8L44 40M44 8L4 40" stroke="#c8102e" stroke-width="2.6"/>'
          '<path d="M24 4V44M4 24H44" stroke="#ffffff" stroke-width="10"/><path d="M24 4V44M4 24H44" stroke="#c8102e" stroke-width="6"/></g>'
          '<circle cx="24" cy="24" r="17" fill="none" stroke="#33243a" stroke-width="2"/>'
          '<path d="M12 14a14 14 0 0 1 9 -5" fill="none" stroke="#ffffff" stroke-width="2.6" stroke-linecap="round" opacity=".85"/>')
    p = os.path.join(ART, "ui-icons.svg")
    s = open(p).read()
    s = re.sub(r'<symbol id="i-flag-(cz|en)-btn".*?</symbol>', '', s)
    s = s.replace("</svg>", f'<symbol id="i-flag-cz-btn" viewBox="0 0 48 48">{cz}</symbol><symbol id="i-flag-en-btn" viewBox="0 0 48 48">{en}</symbol></svg>')
    open(p, "w").write(s)

if __name__ == "__main__":
    logo("cs")
    logo("en")
    play_bubble()
    title_scene()
    home_scene()
    doors()
    quiz_bg()
    summary_bg()
    cross_section_v2()
    flag_buttons()
    print("v2 ok")
