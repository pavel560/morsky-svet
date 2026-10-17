#!/usr/bin/env python3
"""Mořský svět — generator of the 20 creature SVGs + the guide turtle (designer source).

Run:  python3 design/build_creatures.py      -> art/<id>.svg, art/guide-turtle.svg
Deterministic (seeded jitter), stdlib only. Contract: design/DESIGN.md §0 and §6.1.
Every animal faces RIGHT. Pins: circle.anchor[data-look=i] in lookFor order (data/species.json).
"""
import math
import os

from svgkit import (INK, Art, f, grp, smooth, eye, lid, smile, blush, mix, creature_svg, anchors, ellipse_pts)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "art")


# ------------------------------------------------------------------ helpers

def profile(nose, L, ctrl):
    """Fish outline. nose=(x,y) tip; body runs LEFT for length L. ctrl=[(t, up, down)] t in 0..1 from nose.
    Returns closed point list: top nose->tail, bottom tail->nose."""
    nx, ny = nose
    top = [(nx - t * L, ny - u) for t, u, d in ctrl]
    bot = [(nx - t * L, ny + d) for t, u, d in ctrl][::-1]
    return top + bot[:-1] if ctrl[0][1] == 0 and ctrl[0][2] == 0 else top + bot


def fan(a, pts_base, pts_edge, fill, ray, op=1.0, sw=2.6, ink=INK, rays=True, t=.18):
    """A fin: base points (attached to the body) + free edge points; rays from base to edge."""
    pts = pts_base + pts_edge
    d = smooth(pts, t=t)
    out = f'<path d="{d}" fill="{fill}" fill-opacity="{op}" stroke="{ink}" stroke-width="{f(sw)}" stroke-linejoin="round"/>'
    if rays:
        c = a.clip("fin", d)
        r = []
        n = len(pts_edge)
        for i, (ex, ey) in enumerate(pts_edge):
            k = (i + .5) / n
            bi = min(len(pts_base) - 1, int((1 - k) * len(pts_base)))
            bx, by = pts_base[bi]
            r.append(f"M{f(bx)} {f(by)}L{f(ex)} {f(ey)}")
        out = (f'<path d="{d}" fill="{fill}" fill-opacity="{op}"/>'
               f'<g clip-path="{c}"><path d="{"".join(r)}" fill="none" stroke="{ray}" stroke-width="1.6" stroke-linecap="round" opacity=".7"/></g>'
               f'<path d="{d}" fill="none" stroke="{ink}" stroke-width="{f(sw)}" stroke-linejoin="round"/>')
    return out


def tube(pts, w, col, ink=INK, hi=True, cap="round"):
    d = smooth(pts, closed=False, t=.2)
    out = (f'<path d="{d}" fill="none" stroke="{ink}" stroke-width="{f(w + 5)}" stroke-linecap="{cap}" stroke-linejoin="round"/>'
           f'<path d="{d}" fill="none" stroke="{col}" stroke-width="{f(w)}" stroke-linecap="{cap}" stroke-linejoin="round"/>')
    if hi:
        hp = [(x - w * .12, y - w * .22) for x, y in pts]
        out += f'<path d="{smooth(hp, closed=False, t=.2)}" fill="none" stroke="#fff" stroke-opacity=".3" stroke-width="{f(w * .28)}" stroke-linecap="round"/>'
    return out


def tapered(pts, w0, w1, col, ink=INK, sw=2.6, light=None):
    """Tapered arm/tentacle as a filled outline along a polyline."""
    n = len(pts)
    left, right = [], []
    for i, (x, y) in enumerate(pts):
        x0, y0 = pts[max(0, i - 1)]
        x1, y1 = pts[min(n - 1, i + 1)]
        dx, dy = x1 - x0, y1 - y0
        L = math.hypot(dx, dy) or 1
        nx_, ny_ = -dy / L, dx / L
        w = (w0 + (w1 - w0) * i / (n - 1)) / 2
        left.append((x + nx_ * w, y + ny_ * w))
        right.append((x - nx_ * w, y - ny_ * w))
    tip = pts[-1]
    poly = left + [tip] + right[::-1]
    d = smooth(poly, t=.16)
    out = f'<path d="{d}" fill="{col}" stroke="{ink}" stroke-width="{f(sw)}" stroke-linejoin="round"/>'
    if light:
        out += f'<path d="{smooth(left[:-1], closed=False)}" fill="none" stroke="{light}" stroke-width="{f(max(1.5, w0 * .22))}" stroke-linecap="round" opacity=".7" transform="translate(0 0)"/>'
    return out, left, right


def scales(a, clipd, x0, x1, y0, y1, r, col, op=.35, sw=1.4):
    out = []
    row = 0
    y = y0
    while y < y1:
        x = x0 + (r if row % 2 else 0)
        while x < x1:
            out.append(f"M{f(x - r)} {f(y)}A{f(r)} {f(r)} 0 0 0 {f(x + r)} {f(y)}")
            x += 2 * r
        y += r * 1.1
        row += 1
    c = a.clip("sc", clipd)
    return f'<g clip-path="{c}"><path d="{"".join(out)}" fill="none" stroke="{col}" stroke-width="{f(sw)}" opacity="{op}"/></g>'


def write(cid, svg):
    with open(os.path.join(OUT, f"{cid}.svg"), "w") as fh:
        fh.write(svg)


# ================================================================== 1 klaun
def klaun():
    a = Art("klaun", seed=11)
    W, H = 260, 180
    OR, ORL, ORD = "#ff8a2a", "#ffb866", "#e0621c"
    body_pts = profile((228, 98), 168, [(0, 0, 0), (.04, 14, 10), (.15, 34, 30), (.35, 44, 38), (.6, 40, 34), (.85, 22, 20), (1, 13, 12)])
    bd = smooth(a.jit(body_pts, .4))
    # tail (rounded) — g.tail pivot at the peduncle
    tail = fan(a, [(66, 86), (66, 110)], [(36, 128), (20, 112), (18, 86), (34, 66)], ORL, ORD, sw=2.8)
    tail += f'<path d="{smooth([(36, 128), (20, 112), (18, 86), (34, 66)], closed=False)}" fill="none" stroke="{INK}" stroke-width="6" opacity=".9"/>'
    tail += f'<path d="{smooth([(38, 124), (24, 110), (22, 88), (36, 70)], closed=False)}" fill="none" stroke="#fff" stroke-width="2.4" opacity=".9"/>'
    # dorsal (two-part), anal, pelvic, pectoral
    dorsal = fan(a, [(186, 62), (110, 56)], [(100, 44), (122, 30), (142, 40), (160, 26), (184, 42)], OR, ORD)
    dorsal += f'<path d="{smooth([(100, 44), (122, 30), (142, 40), (160, 26), (184, 42)], closed=False)}" fill="none" stroke="{INK}" stroke-width="5"/>'
    anal = fan(a, [(108, 134), (84, 126)], [(78, 144), (96, 156), (112, 148)], OR, ORD)
    anal += f'<path d="{smooth([(78, 144), (96, 156), (112, 148)], closed=False)}" fill="none" stroke="{INK}" stroke-width="5"/>'
    pelvic = fan(a, [(168, 132), (150, 134)], [(140, 154), (160, 158)], OR, ORD)
    fin = fan(a, [(178, 102), (176, 118)], [(150, 132), (142, 118), (150, 100)], ORL, ORD, op=.95)
    fin += f'<path d="M150 132Q141 118 150 100" fill="none" stroke="{INK}" stroke-width="4.5" stroke-linecap="round"/>'
    torso = a.shape(bd, OR, ORL, ORD, 52, 140, hi_box=(170, 70, 50, 14))
    # three white bands with black edges (clipped to the body)
    c = a.clip("bands", bd)
    bands = ""
    for (xt, xb, w, bulge) in ((188, 184, 15, 6), (132, 128, 16, 16), (76, 74, 11, 2)):
        L = smooth([(xt - w / 2, 40), (xt - w / 2 - bulge * .3, 98), (xb - w / 2, 150), (xb + w / 2, 150), (xt + w / 2 + bulge, 98), (xt + w / 2, 40)], t=.2)
        bands += f'<path d="{L}" fill="#fff" stroke="{INK}" stroke-width="3.2"/>'
    torso_full = torso.replace('<path d="' + bd + '" fill="none" stroke', '<path data-x="1" d="' + bd + '" fill="none" stroke', 1)
    face = (eye(198, 84, 10.5) + blush(206, 104, 7, 4) + smile(222, 105, 12, sw=2.4, tilt=-.15))
    lids_ = lid(198, 84, 10.5, OR)
    body = (grp("fin-2", pelvic, (160, 134)) + grp("tail", tail, (66, 98)) + dorsal + anal + torso_full +
            f'<g clip-path="{c}">{bands}</g><path d="{bd}" fill="none" stroke="{INK}" stroke-width="3"/>' +
            face + grp("fin", fin, (177, 110)) + grp("lids", lids_, (198, 84), ' opacity="0"'))
    an = anchors([(160, 122), (130, 76), (142, 30)], (140, 98))
    write("klaun", creature_svg("klaun", "Klaun očkatý", W, H, a.defs, body, an, (18, 230), "swim", body_pivot=(140, 98)))


# ================================================================== 2 sasanka
def sasanka():
    a = Art("sasanka", seed=12)
    W, H = 240, 240
    COL, COLL, COLD = "#9b3fb0", "#c97ad8", "#66217a"
    TEN, TENL, TIP = "#bccf86", "#eef8d8", "#fbf3c8"
    # column (foot) with the face
    col_pts = [(70, 118), (86, 160), (78, 214), (92, 228), (148, 228), (162, 214), (154, 160), (170, 118)]
    cd = smooth(a.jit(col_pts, .5), t=.18)
    column = a.shape(cd, COL, COLL, COLD, 118, 228, hi_box=(104, 150, 18, 30))
    column += ''.join(f'<path d="M{f(x)} 132Q{f(x + a.j(3))} 180 {f(x + a.j(4))} 222" fill="none" stroke="{COLD}" stroke-width="1.6" opacity=".5"/>' for x in (92, 108, 132, 148))
    # oral disc (seen slightly from above) with the mouth slit
    disc = (f'<ellipse cx="120" cy="116" rx="56" ry="16" fill="{mix(COL, "#ffffff", .25)}" stroke="{INK}" stroke-width="2.8"/>'
            f'<ellipse cx="120" cy="114" rx="13" ry="4.6" fill="{COLD}" stroke="{INK}" stroke-width="2"/>')
    # tentacles: back row then front row, fat fingers with pink tips
    back, front = [], []
    for i in range(13):
        th = math.radians(200 + i * 140 / 12)
        bx, by = 120 + 50 * math.cos(th) * .95, 112 + 10 * math.sin(th)
        L = 62 + a.j(10)
        ang = math.radians(-90 + (i - 6) * 11 + a.j(5))
        pts = [(bx, by)]
        for k in range(1, 5):
            t = k / 4
            pts.append((bx + math.cos(ang) * L * t + math.sin(t * 3 + i) * 7, by + math.sin(ang) * L * t))
        back.append(pts)
    for i in range(9):
        bx = 76 + i * 11 + a.j(2)
        by = 122 + a.j(2)
        L = 54 + a.j(8)
        ang = math.radians(-90 + (i - 4) * 16 + a.j(5))
        pts = [(bx, by)]
        for k in range(1, 5):
            t = k / 4
            pts.append((bx + math.cos(ang) * L * t + math.sin(t * 3 + i * 1.7) * 6, by + math.sin(ang) * L * t))
        front.append(pts)

    def tentacle(pts, dim=0.0):
        col = mix(TEN, "#7f9a6a", dim)
        out, l, r = tapered(pts, 15, 10, col)
        tx, ty = pts[-1]
        out += f'<circle cx="{f(tx)}" cy="{f(ty)}" r="6.4" fill="{mix(TIP, "#a06080", dim)}" stroke="{INK}" stroke-width="2.4"/>'
        out += f'<circle cx="{f(tx - 1.8)}" cy="{f(ty - 2)}" r="1.8" fill="#fff" opacity=".7"/>'
        return out
    ten_back = "".join(tentacle(p, .28) for p in back)
    ten_front = "".join(tentacle(p) for i, p in enumerate(front) if i not in (4,))
    face = eye(104, 170, 9) + eye(138, 170, 9) + blush(94, 188, 7, 4) + blush(148, 188, 7, 4) + smile(121, 186, 14, sw=2.4)
    lids_ = lid(104, 170, 9, COL) + lid(138, 170, 9, COL)
    body = (grp("tentacles", ten_back + disc + ten_front, (120, 118)) + column + face + grp("lids", lids_, (121, 170), ' opacity="0"'))
    an = anchors([(64, 60), (front[2][-1][0], front[2][-1][1]), (156, 206)], (120, 150))
    write("sasanka", creature_svg("sasanka", "Sasanka", W, H, a.defs, body, an, (28, 212), "sway", floor=228, body_pivot=(120, 228)))


# ================================================================== 3 konik
def konik():
    """Hippocampus guttulatus — long-snouted seahorse with a shaggy 'mane' of skin filaments, white dots."""
    a = Art("konik", seed=13)
    W, H = 210, 290
    C, CL, CD = "#eaa443", "#ffd388", "#bd7424"
    pts = [(96, 30), (104, 22), (110, 30), (118, 24), (124, 34), (130, 46),        # coronet
           (152, 56), (176, 60), (182, 66), (176, 73), (152, 74), (134, 78),       # snout tube
           (132, 94), (146, 118), (152, 150), (140, 180), (118, 200), (110, 214),  # throat, belly
           (100, 214), (98, 196), (88, 182), (82, 160), (74, 132), (72, 104), (80, 76), (86, 52)]
    d = smooth(a.jit(pts, .3), t=.17)
    torso = a.shape(d, C, CL, CD, 20, 214, hi_box=(116, 124, 13, 36))
    c = a.clip("rings", d)
    rings = "".join(f'<path d="M66 {y}Q{112} {y + 8} 158 {y - 2}" fill="none" stroke="{CD}" stroke-width="2.2" opacity=".7"/>' for y in range(100, 212, 12))
    dots = "".join(f'<circle cx="{f(98 + a.j(22))}" cy="{f(64 + i * 10 + a.j(4))}" r="{f(1.8 + a.rng.random())}" fill="#fff" opacity=".85"/>' for i in range(14))
    spiral = []
    for k in range(28):
        t = k / 27
        ang = math.radians(170 - 340 * t)
        r = 28 * (1 - .66 * t)
        spiral.append((118 + r * math.cos(ang), 232 + r * math.sin(ang)))
    tail = tube([(102, 200), (96, 214)] + spiral, 12, C)
    # the 'mane': fleshy filaments on the crown and down the back
    mane = ""
    roots = [(100, 28, 200), (110, 24, 230), (120, 28, 250), (86, 50, 175), (80, 70, 170), (76, 92, 182), (73, 114, 178), (74, 136, 186), (78, 158, 192)]
    for i, (x, y, ang) in enumerate(roots):
        L = 18 + (i % 3) * 5
        th = math.radians(ang)
        p = [(x, y), (x + math.cos(th) * L * .5 + 3, y - math.sin(th) * L * .5 + 2), (x + math.cos(th) * L, y - math.sin(th) * L)]
        mane += tube(p, 4.2, "#c98a2c", hi=False)
        mane += f'<circle cx="{f(p[2][0])}" cy="{f(p[2][1])}" r="3" fill="#ffe6b0" stroke="{INK}" stroke-width="1.6"/>'
    fin = fan(a, [(80, 132), (80, 168)], [(52, 176), (44, 152), (54, 128)], "#fff1c8", CD, op=.85, sw=2.4)
    fin2 = fan(a, [(112, 86), (110, 98)], [(96, 106), (94, 88)], "#fff1c8", CD, op=.8, sw=2)
    face = eye(122, 54, 9.5) + blush(132, 72, 6, 3.4) + f'<circle cx="179" cy="66" r="1.8" fill="{INK}"/>'
    face += smile(164, 68, 8, sw=2, tilt=.2, depth=3)
    lids_ = lid(122, 54, 9.5, C)
    body = (mane + grp("fin-2", fin2, (111, 92)) + grp("tail", tail, (100, 200)) + torso + f'<g clip-path="{c}">{rings}{dots}</g>' +
            grp("fin", fin, (80, 150)) + face + grp("lids", lids_, (122, 54), ' opacity="0"'))
    an = anchors([(168, 66), (118, 234), (74, 92)], (110, 130))
    write("konik", creature_svg("konik", "Koníček mořský", W, H, a.defs, body, an, (20, 266), "hover", body_pivot=(110, 130)))


# ================================================================== 4 hvezdice
def hvezdice():
    """Linckia laevigata — the blue sea star: five long, round, sausage-like arms, all deep blue."""
    a = Art("hvezdice", seed=14)
    W, H = 270, 200
    C, CL, CD = "#2f6fd6", "#6fa6f2", "#1c4796"
    cx, cy, sy = 135, 104, .6
    pts = []
    for i in range(5):
        th = math.radians(-90 + i * 72 + 10)
        u = (math.cos(th), math.sin(th))
        v = (-u[1], u[0])
        w = 15.5
        for r, s_ in ((30, -1.05), (62, -1.0), (92, -.92), (108, -.62), (114, 0), (108, .62), (92, .92), (62, 1.0), (30, 1.05)):
            x = cx + u[0] * r + v[0] * w * s_
            y = cy + (u[1] * r + v[1] * w * s_) * sy
            pts.append((x, y))
        thv = th + math.radians(36)
        pts.append((cx + 27 * math.cos(thv), cy + 27 * math.sin(thv) * sy))
    d = smooth(a.jit(pts, .4), t=.16)
    star = a.shape(d, C, CL, CD, cy - 70, cy + 70, hi=False)
    c = a.clip("arms", d)
    # round-arm shading: a light ridge along each arm + fine pores
    ridge, pores = "", []
    for i in range(5):
        th = math.radians(-90 + i * 72 + 10)
        x0, y0 = cx + 20 * math.cos(th), cy + 20 * math.sin(th) * sy
        x1, y1 = cx + 104 * math.cos(th), cy + 104 * math.sin(th) * sy
        ridge += f'<path d="M{f(x0)} {f(y0 - 4)}L{f(x1)} {f(y1 - 4)}" stroke="#a9ccff" stroke-width="7" stroke-linecap="round" opacity=".55"/>'
        for k in range(3, 11):
            r = k * 10
            for s_ in (-7, 7):
                pores.append(f'<circle cx="{f(cx + r * math.cos(th) - s_ * math.sin(th))}" cy="{f(cy + (r * math.sin(th) + s_ * math.cos(th)) * sy)}" r="1.3" fill="{CD}" opacity=".5"/>')
    face = eye(121, 100, 8.5) + eye(151, 100, 8.5) + blush(110, 116, 6.5, 3.6) + blush(162, 116, 6.5, 3.6) + smile(136, 114, 13, sw=2.4)
    lids_ = lid(121, 100, 8.5, C) + lid(151, 100, 8.5, C)
    shadow = f'<ellipse cx="{cx}" cy="{cy + 52}" rx="104" ry="13" fill="#1e2a40" opacity=".18"/>'
    body = (shadow + star + f'<g clip-path="{c}">{ridge}{"".join(pores)}</g><path d="{d}" fill="none" stroke="{INK}" stroke-width="3"/>' + face +
            grp("lids", lids_, (136, 100), ' opacity="0"'))
    th = math.radians(-90 + 72 + 10)
    tip = (cx + 104 * math.cos(th), cy + 104 * math.sin(th) * sy)
    th2 = math.radians(-90 + 3 * 72 + 10)
    arm = (cx + 70 * math.cos(th2), cy + 70 * math.sin(th2) * sy)
    an = anchors([tip, (cx + 2, cy - 24), arm], (cx, cy))
    write("hvezdice", creature_svg("hvezdice", "Hvězdice modrá", W, H, a.defs, body, an, (22, 248), "crawl", floor=cy + 52, body_pivot=(cx, cy + 40)))


# ================================================================== 5 krab
def krab():
    a = Art("krab", seed=15)
    W, H = 330, 210
    C, CL, CD = "#6f8f3a", "#a3c264", "#465e22"
    cx, cy = 165, 118
    # legs: 4 per side, jointed, behind the shell
    legs = ""
    for side in (-1, 1):
        for k in range(4):
            sx = cx + side * (40 + k * 8)
            sy = cy + 10 + k * 4
            kx = cx + side * (74 + k * 17)
            ky = cy - 4 + k * 6
            tx = cx + side * (84 + k * 24)
            ty = 198 - k * 7
            legs += tube([(sx, sy), (kx, ky), (tx, ty)], 9 - k * .6, mix(C, CD, .45 - k * .1), hi=False)
            legs += f'<circle cx="{f(kx)}" cy="{f(ky)}" r="3" fill="#e9c46a" stroke="{INK}" stroke-width="1.4"/>'
    shell_pts = [(cx - 78, cy - 6), (cx - 60, cy - 36), (cx - 20, cy - 46), (cx + 20, cy - 46), (cx + 60, cy - 36),
                 (cx + 78, cy - 6), (cx + 64, cy + 22), (cx + 20, cy + 34), (cx - 20, cy + 34), (cx - 64, cy + 22)]
    sd = smooth(a.jit(shell_pts, .5), t=.18)
    shell = a.shape(sd, C, CL, CD, cy - 46, cy + 34, hi_box=(cx - 20, cy - 30, 40, 9))
    shell += "".join(f'<circle cx="{f(cx + x)}" cy="{f(cy + y)}" r="2.2" fill="{CD}" opacity=".55"/>' for x, y in ((-50, -16), (-38, -26), (44, -20), (54, -8), (-56, 2), (30, -30)))
    # five soft teeth on each front-side edge of the shell (shore crab)
    for side in (-1, 1):
        for k in range(5):
            tx_, ty_ = cx + side * (40 + k * 8.5), cy - 40 + k * 7.5
            shell += f'<path d="M{f(tx_ - side * 5)} {f(ty_ - 4)}L{f(tx_ + side * 6)} {f(ty_ - 1)}L{f(tx_ - side * 2)} {f(ty_ + 5)}Z" fill="{C}" stroke="{INK}" stroke-width="2" stroke-linejoin="round"/>'

    def claw(side):
        bx, by = cx + side * 62, cy - 4
        ex, ey = cx + side * 96, cy - 34
        arm = tube([(bx, by), (cx + side * 84, cy - 10), (ex, ey)], 12, mix(C, CD, .15), hi=False)
        # pincer: big rounded upper + smaller lower finger (closed, friendly)
        px, py = ex + side * 4, ey - 18
        up = smooth([(px - side * 20, py + 8), (px - side * 14, py - 16), (px + side * 10, py - 24), (px + side * 30, py - 10),
                     (px + side * 24, py - 2), (px + side * 2, py + 2), (px - side * 2, py + 14)], t=.18)
        lo = smooth([(px - side * 4, py + 6), (px + side * 20, py + 2), (px + side * 22, py + 10), (px - side * 2, py + 20)], t=.2)
        g1 = a.shape(up, C, CL, CD, py - 24, py + 14, hi_box=(px, py - 14, 10, 5))
        g2 = a.shape(lo, mix(C, CD, .2), CL, CD, py, py + 20, hi=False)
        return arm + g2 + g1, (ex, ey)
    claw_l, pl = claw(-1)
    claw_r, pr = claw(1)
    # eyes on stalks
    stalks = ""
    for ex in (cx - 22, cx + 22):
        stalks += tube([(ex, cy - 38), (ex + (ex - cx) * .25, cy - 64)], 7, mix(C, CD, .2), hi=False)
    face = (eye(cx - 27, cy - 72, 11) + eye(cx + 27, cy - 72, 11) + blush(cx - 34, cy - 4, 8, 4.5) + blush(cx + 34, cy - 4, 8, 4.5)
            + smile(cx, cy - 2, 18, sw=2.6))
    lids_ = lid(cx - 27, cy - 72, 11, mix(C, CD, .2)) + lid(cx + 27, cy - 72, 11, mix(C, CD, .2))
    body = (grp("legs", legs, (cx, cy + 10)) + grp("claw-2", claw_l, (cx - 62, cy - 4)) + stalks + shell + face +
            grp("claw", claw_r, (cx + 62, cy - 4)) + grp("lids", lids_, (cx, cy - 72), ' opacity="0"'))
    an = anchors([(cx + 114, cy - 58), (cx - 118, cy + 50), (cx + 59, cy - 24)], (cx, cy))
    write("krab", creature_svg("krab", "Krab pobřežní", W, H, a.defs, body, an, (12, 318), "crawl-side", floor=196, body_pivot=(cx, 196)))


# ================================================================== 6 chobotnice
def chobotnice():
    a = Art("chobotnice", seed=16)
    W, H = 280, 270
    C, CL, CD = "#ec6f5a", "#ffa08a", "#b9443a"
    SUCK = "#ffd2c4"
    # arms first (behind the head), each curling at the tip
    arms_back, arms_front = "", ""
    front_pts = []
    specs = [  # base x, base y, direction, curl, length, front?
        (104, 150, 200, -1, 96, 0), (118, 156, 230, -1, 104, 0), (186, 150, -20, 1, 96, 0), (172, 156, -50, 1, 104, 0),
        (122, 160, 250, 1, 108, 1), (140, 162, 268, -1, 100, 1), (158, 162, 288, 1, 104, 1), (172, 158, 312, -1, 96, 1)]
    for (bx, by, ang0, curl, L, front) in specs:
        pts = []
        ang = math.radians(ang0)
        x, y = bx, by
        n = 9
        for k in range(n):
            pts.append((x, y))
            step = L / (n - 1)
            x += math.cos(ang) * step
            y -= math.sin(ang) * step
            ang += math.radians(curl * (6 + k * 6))
        pts = [(px, py) for px, py in pts]
        col = C if front else mix(C, CD, .45)
        arm, l, r = tapered(pts, 26, 6, col)
        suck = ""
        if front:
            side = r if curl > 0 else l
            for k in range(1, 7):
                sx, sy = side[k]
                rr = 4.4 - k * .45
                suck += f'<circle cx="{f(sx)}" cy="{f(sy)}" r="{f(rr)}" fill="{SUCK}" stroke="{INK}" stroke-width="1.3"/>'
            arms_front += arm + suck
            front_pts.append(pts)
        else:
            arms_back += arm
    mantle = smooth(a.jit([(84, 120), (70, 82), (82, 40), (120, 18), (166, 22), (198, 50), (206, 92), (196, 132),
                           (176, 158), (140, 166), (104, 158)], .5), t=.18)
    head = a.shape(mantle, C, CL, CD, 18, 166, hi_box=(118, 50, 34, 18))
    c = a.clip("spots", mantle)
    spots = "".join(f'<ellipse cx="{f(x)}" cy="{f(y)}" rx="{f(r)}" ry="{f(r * .8)}" fill="{CD}" opacity=".35"/>'
                    for x, y, r in ((100, 60, 7), (130, 42, 5), (164, 46, 8), (92, 96, 5), (184, 84, 5), (150, 70, 4)))
    face = (eye(130, 122, 12) + eye(172, 120, 11) + blush(118, 142, 8, 4.5) + blush(186, 140, 7, 4) + smile(152, 142, 14, sw=2.6))
    lids_ = lid(130, 122, 12, C) + lid(172, 120, 11, C)
    body = (grp("fin-2", arms_back, (145, 150)) + head + f'<g clip-path="{c}">{spots}</g>' + face +
            grp("tentacles", arms_front, (145, 158)) + grp("lids", lids_, (151, 121), ' opacity="0"'))
    an = anchors([front_pts[0][-2], front_pts[3][3], (110, 56)], (145, 120))
    write("chobotnice", creature_svg("chobotnice", "Chobotnice pobřežní", W, H, a.defs, body, an, (20, 262), "jet", body_pivot=(145, 140)))


# ================================================================== 7 papousek
def papousek():
    a = Art("papousek", seed=17)
    W, H = 300, 200
    C, CL, CD = "#3cc3a8", "#8fe8d0", "#1f8a7c"
    EDGE = "#2f6fe0"
    body_pts = profile((262, 104), 200, [(0, 0, 0), (.05, 22, 18), (.18, 46, 40), (.4, 58, 50), (.65, 50, 44), (.88, 26, 24), (1, 16, 15)])
    bd = smooth(a.jit(body_pts, .4))
    tail = fan(a, [(64, 92), (64, 118)], [(40, 134), (14, 152), (30, 120), (26, 104), (30, 88), (14, 56), (40, 74)], "#ff9fae", "#d8607a", sw=2.8)
    dorsal = fan(a, [(214, 66), (110, 60)], [(100, 50), (140, 36), (190, 40), (214, 52)], "#ff9fae", "#d8607a")
    dorsal += f'<path d="M104 52Q150 40 208 50" fill="none" stroke="#4fa8ff" stroke-width="4" opacity=".8"/>'
    anal = fan(a, [(150, 150), (96, 140)], [(90, 156), (126, 168), (150, 160)], "#ff9fae", "#d8607a")
    torso = a.shape(bd, C, CL, CD, 46, 156, hi_box=(180, 76, 60, 14))
    sc = scales(a, bd, 70, 220, 56, 160, 9, "#ffffff", op=.45, sw=1.6)
    sc += scales(a, bd, 70, 220, 60, 160, 9, EDGE, op=.75, sw=2)
    # head colour patch + beak (fused teeth: smooth, closed, like a parrot's beak — never bared)
    c = a.clip("head", bd)
    headpatch = f'<g clip-path="{c}"><path d="M226 40Q206 104 228 170L300 170L300 40Z" fill="#5fd9c0" opacity=".55"/>' \
                f'<path d="M196 72Q206 104 196 140" fill="none" stroke="{CD}" stroke-width="3" opacity=".6"/></g>'
    beak = smooth([(250, 98), (264, 96), (272, 104), (266, 114), (250, 114), (246, 106)], t=.2)
    beakg = a.shape(beak, "#e9f7f2", "#ffffff", "#a8d8cc", 96, 114, hi=False, shade=False)
    beakg += f'<path d="M248 106Q260 108 270 105" fill="none" stroke="{INK}" stroke-width="2"/>'
    fin = fan(a, [(206, 108), (204, 124)], [(174, 140), (166, 124), (176, 104)], "#ffc2cc", "#d8607a", op=.95)
    face = eye(226, 88, 10) + blush(228, 112, 6, 3.6)
    lids_ = lid(226, 88, 10, C)
    body = (grp("tail", tail, (64, 104)) + dorsal + anal + torso + sc + headpatch + beakg + face +
            grp("fin", fin, (205, 116)) + grp("lids", lids_, (226, 88), ' opacity="0"'))
    an = anchors([(268, 106), (140, 92), (196, 140)], (150, 104))
    write("papousek", creature_svg("papousek", "Ploskozubec", W, H, a.defs, body, an, (14, 272), "swim", body_pivot=(150, 104)))


# ================================================================== 8 vydra
def vydra():
    a = Art("vydra", seed=18)
    W, H = 320, 190
    C, CL, CD = "#7b5235", "#a7774f", "#523420"
    PALE = "#ead7b6"
    # floating on her back, head to the right; belly up
    torso_pts = [(50, 110), (68, 80), (120, 64), (180, 62), (228, 70), (252, 96), (242, 128), (190, 142), (120, 144), (64, 134)]
    td = smooth(a.jit(torso_pts, .6), t=.18)
    torso = a.shape(td, C, CL, CD, 70, 138, hi_box=(150, 80, 70, 10))
    c = a.clip("fur", td)
    fur = "".join(f'<path d="M{f(x)} {f(y)}q3 -6 6 0" fill="none" stroke="{CL}" stroke-width="1.6" opacity=".7"/>'
                  for x, y in [(80 + i * 13 + a.j(3), 90 + (i % 3) * 12 + a.j(3)) for i in range(12)])
    belly = f'<path d="M84 76Q150 52 236 72Q214 98 160 100Q110 100 84 76Z" fill="#c9a27a" opacity=".75"/>'
    tail = tapered([(58, 110), (34, 106), (14, 96)], 22, 10, mix(C, CD, .2))[0]
    hind = ""
    for (x, y, rot) in ((70, 74, -30), (94, 66, -10)):
        foot = smooth([(x - 8, y + 6), (x - 14, y - 16), (x - 4, y - 28), (x + 8, y - 24), (x + 10, y - 6), (x + 4, y + 6)], t=.2)
        hind += f'<path d="{foot}" fill="{mix(C, CD, .3)}" stroke="{INK}" stroke-width="2.6" stroke-linejoin="round"/>'
        hind += f'<path d="M{x - 6} {y - 18}l2 8M{x} {y - 22}l1 10M{x + 5} {y - 18}l-1 8" stroke="{INK}" stroke-width="1.4" opacity=".6"/>'
    # head: round, pale face, small ears, whiskers
    hd = smooth(ellipse_pts(262, 92, 40, 36, n=14, wob=lambda t: .03 * math.sin(3 * t)), t=.18)
    head = a.shape(hd, C, CL, CD, 56, 128, hi=False)
    face_patch = smooth(ellipse_pts(270, 98, 30, 26, n=12), t=.18)
    head += f'<path d="{face_patch}" fill="{PALE}"/>'
    head += f'<circle cx="236" cy="62" r="8" fill="{C}" stroke="{INK}" stroke-width="2.4"/><circle cx="236" cy="62" r="3.5" fill="{CD}"/>'
    head += f'<circle cx="292" cy="64" r="7" fill="{C}" stroke="{INK}" stroke-width="2.4"/><circle cx="292" cy="64" r="3" fill="{CD}"/>'
    head += f'<path d="{hd}" fill="none" stroke="{INK}" stroke-width="3"/>'
    face = (eye(256, 88, 7.5, look=(.15, -.1)) + eye(284, 86, 7, look=(.15, -.1)) +
            f'<ellipse cx="274" cy="102" rx="7" ry="5" fill="{INK}"/><ellipse cx="272" cy="100" rx="2.4" ry="1.4" fill="#fff" opacity=".7"/>'
            + smile(274, 112, 12, sw=2.2) + blush(250, 106, 6, 3.4) + blush(296, 104, 5, 3))
    whisk = "".join(f'<path d="M{f(x0)} {f(y0)}q{f(dx * .5)} {f(dy * .3 - 3)} {f(dx)} {f(dy)}" fill="none" stroke="{INK}" stroke-width="3.6" stroke-linecap="round" opacity=".8"/>'
                    f'<path d="M{f(x0)} {f(y0)}q{f(dx * .5)} {f(dy * .3 - 3)} {f(dx)} {f(dy)}" fill="none" stroke="#ffffff" stroke-width="1.8" stroke-linecap="round"/>'
                    for x0, y0, dx, dy in ((264, 104, -36, -6), (264, 108, -34, 6), (284, 104, 32, -10), (284, 108, 34, 2), (284, 111, 28, 12)))
    # front paws on the chest holding a small pebble (otters use stones as tools)
    paws = (tube([(186, 78), (192, 58)], 13, mix(C, CD, .1), hi=False) + tube([(214, 80), (214, 58)], 13, mix(C, CD, .1), hi=False) +
            f'<ellipse cx="203" cy="50" rx="15" ry="10" fill="#9aa6b8" stroke="{INK}" stroke-width="2.4"/>'
            f'<path d="M196 46q6 -4 11 0" fill="none" stroke="#fff" stroke-width="2.2" opacity=".75"/>'
            f'<ellipse cx="190" cy="56" rx="9.5" ry="8" fill="{mix(C, CD, .25)}" stroke="{INK}" stroke-width="2.4"/>'
            f'<ellipse cx="216" cy="56" rx="9.5" ry="8" fill="{mix(C, CD, .25)}" stroke="{INK}" stroke-width="2.4"/>')
    lids_ = lid(256, 88, 7.5, PALE) + lid(284, 86, 7, PALE)
    body = (grp("tail", tail, (58, 110)) + grp("legs", hind, (80, 86)) + torso + f'<g clip-path="{c}">{belly}{fur}</g>' +
            head + face + whisk + grp("fin", paws, (210, 82)) + grp("lids", lids_, (270, 87), ' opacity="0"'))
    an = anchors([(160, 82), (110, 118), (312, 100)], (170, 100))
    write("vydra", creature_svg("vydra", "Vydra mořská", W, H, a.defs, body, an, (12, 302), "surface", body_pivot=(170, 104)))


# ================================================================== 9 tulen
def tulen():
    a = Art("tulen", seed=19)
    W, H = 330, 180
    C, CL, CD = "#9aa3ad", "#c9d0d8", "#6b7581"
    body_pts = profile((304, 96), 250, [(0, 0, 0), (.03, 16, 14), (.1, 30, 30), (.2, 36, 34), (.4, 44, 44), (.65, 40, 38), (.85, 24, 22), (1, 10, 10)])
    bd = smooth(a.jit(body_pts, .4))
    torso = a.shape(bd, C, CL, CD, 50, 142, hi_box=(200, 64, 70, 12))
    c = a.clip("spots", bd)
    spots = "".join(f'<ellipse cx="{f(x)}" cy="{f(y)}" rx="{f(r)}" ry="{f(r * .7)}" fill="#5b636e" opacity=".55" transform="rotate({int(a.j(30))} {f(x)} {f(y)})"/>'
                    for x, y, r in [(90 + i * 17 + a.j(6), 72 + (i * 37 % 50) + a.j(5), 3 + (i % 3)) for i in range(11)])
    belly = f'<path d="M80 128Q170 150 280 112L300 140L60 150Z" fill="#e6eaee" opacity=".55"/>'
    tail = fan(a, [(66, 90), (66, 104)], [(34, 120), (18, 112), (34, 98), (18, 84), (34, 76)], mix(C, CD, .3), CD, sw=2.6)
    fin = smooth([(226, 120), (214, 150), (196, 160), (190, 152), (204, 132), (210, 116)], t=.2)
    fing = a.shape(fin, mix(C, CD, .2), CL, CD, 116, 160, hi=False)
    fing += "".join(f'<path d="M{193 + k * 4} {155 - k * 2}l-4 3" stroke="{INK}" stroke-width="1.6" stroke-linecap="round"/>' for k in range(3))
    face = (eye(280, 82, 10.5, look=(.2, .05)) + blush(282, 104, 7, 4) +
            f'<path d="M298 94q4 -3 7 0M298 99q4 2 7 0" fill="none" stroke="{INK}" stroke-width="2" stroke-linecap="round"/>'
            + smile(292, 108, 10, sw=2.2, tilt=-.2) + f'<circle cx="262" cy="80" r="2.6" fill="{INK}"/>')
    whisk = "".join(f'<path d="M{f(296)} {f(y0)}q14 {f(dy * .4)} 28 {f(dy)}" fill="none" stroke="{INK}" stroke-width="1.3" stroke-linecap="round" opacity=".75"/>'
                    for y0, dy in ((100, -8), (102, 0), (104, 8)))
    lids_ = lid(280, 82, 10.5, C)
    body = (grp("tail", tail, (66, 97)) + torso + f'<g clip-path="{c}">{belly}{spots}</g>' + face + whisk +
            grp("fin", fing, (214, 120)) + grp("lids", lids_, (280, 82), ' opacity="0"'))
    an = anchors([(266, 70), (140, 82), (198, 152)], (170, 96))
    write("tulen", creature_svg("tulen", "Tuleň obecný", W, H, a.defs, body, an, (18, 306), "swim", body_pivot=(170, 96)))


# ================================================================== 10 jezovka
def jezovka():
    """Strongylocentrotus purpuratus — round like a ball, spines all around, purple."""
    a = Art("jezovka", seed=20)
    W, H = 250, 240
    C, CL, CD = "#7a4fb0", "#a983dc", "#4f2f80"
    SP, SPL = "#5b3592", "#c7a7f0"
    cx, cy, R = 125, 126, 54

    def spine(th, r0, L, front):
        x0, y0 = cx + r0 * math.cos(th), cy + r0 * math.sin(th)
        x1, y1 = cx + (R + L) * math.cos(th), cy + (R + L) * math.sin(th)
        col = SP if not front else mix(SP, SPL, .25)
        return (f'<path d="M{f(x0)} {f(y0)}L{f(x1)} {f(y1)}" stroke="{INK}" stroke-width="{6.6 if front else 6}" stroke-linecap="round"/>'
                f'<path d="M{f(x0)} {f(y0)}L{f(x1)} {f(y1)}" stroke="{col}" stroke-width="{3.6 if front else 3}" stroke-linecap="round"/>'
                f'<path d="M{f((x0 + x1) / 2)} {f((y0 + y1) / 2)}L{f(x1)} {f(y1)}" stroke="{SPL}" stroke-width="1.5" stroke-linecap="round" opacity=".85"/>')
    back, front = "", ""
    for i in range(40):
        th = 2 * math.pi * i / 40 + a.j(.03)
        deg = math.degrees(th) % 360
        if 62 < deg < 118:
            continue                        # leave the underside for the tube feet
        back += spine(th + math.pi / 40, R * .6, 40 + a.j(6), False)
    for i in range(30):
        th = 2 * math.pi * i / 30 + a.j(.04)
        deg = math.degrees(th) % 360
        if 55 < deg < 125:
            continue
        front += spine(th, R - 6, 44 + a.j(6), True)
    ball = smooth(ellipse_pts(cx, cy, R, R * .96, n=16, wob=lambda t: .015 * math.sin(5 * t)), t=.18)
    ballg = a.shape(ball, C, CL, CD, cy - R, cy + R, hi_box=(cx - 18, cy - 30, 24, 12))
    c = a.clip("knobs", ball)
    knobs = "".join(f'<circle cx="{f(cx + r * math.cos(t))}" cy="{f(cy + r * math.sin(t))}" r="2.6" fill="{SPL}" opacity=".75"/>'
                    for r in (24, 40) for t in [math.radians(k * 30 + (r % 3) * 15) for k in range(12)] if not (20 < math.degrees(t) % 360 < 160 and r == 24))
    feet = "".join(f'<path d="M{f(cx - 30 + k * 12)} {f(cy + R - 6)}q{f(a.j(3))} 9 {f(a.j(4))} 15" stroke="{INK}" stroke-width="5" stroke-linecap="round"/>'
                   f'<path d="M{f(cx - 30 + k * 12)} {f(cy + R - 6)}q{f(a.j(1))} 9 {f(a.j(1))} 15" stroke="#f1d4ff" stroke-width="2.6" stroke-linecap="round"/>' for k in range(6))
    face = eye(cx - 15, cy + 6, 9) + eye(cx + 17, cy + 6, 9) + blush(cx - 28, cy + 22, 6.5, 3.6) + blush(cx + 30, cy + 22, 6.5, 3.6) + smile(cx + 1, cy + 22, 12, sw=2.4)
    lids_ = lid(cx - 15, cy + 6, 9, C) + lid(cx + 17, cy + 6, 9, C)
    body = (back + grp("legs", feet, (cx, cy + R)) + ballg + f'<g clip-path="{c}">{knobs}</g><path d="{ball}" fill="none" stroke="{INK}" stroke-width="3"/>' +
            front + face + grp("lids", lids_, (cx + 1, cy + 6), ' opacity="0"'))
    an = anchors([(cx + 30, cy + 36), (cx - 70, cy - 66), (cx - 30, cy - 26)], (cx, cy))
    write("jezovka", creature_svg("jezovka", "Ježovka purpurová", W, H, a.defs, body, an, (14, 236), "crawl", floor=cy + R + 10, body_pivot=(cx, cy + R)))


# ================================================================== 11 meduza (Aurelia aurita)
def meduza():
    a = Art("meduza", seed=21)
    W, H = 240, 270
    cx = 120
    BELL = "#efe6ff"
    RING = "#b65fd0"
    bell = smooth([(cx - 98, 120), (cx - 90, 82), (cx - 58, 42), (cx, 28), (cx + 58, 42), (cx + 90, 82), (cx + 98, 120),
                   (cx + 60, 132), (cx, 136), (cx - 60, 132)], t=.18)
    bg = a.radial("bell", [(0, "#ffffff", .95), (.55, BELL, .75), (1, "#c9b4f2", .7)], cx="45%", cy="30%", r="70%")
    # oral arms (frilly ribbons) + fringe tentacles — g.tentacles
    arms = ""
    for k, (x0, sway) in enumerate(((104, -1), (116, 1), (126, -1), (138, 1))):
        pts = [(x0, 126)]
        for i in range(1, 6):
            pts.append((x0 + sway * 8 * math.sin(i * 1.3 + k) + (x0 - cx) * .25 * i / 5, 126 + i * 21))
        o, l, r = tapered(pts, 14, 4, "#f7c9e6", sw=2)
        arms += o.replace('fill="#f7c9e6"', 'fill="#f7c9e6" fill-opacity=".8"')
        arms += f'<path d="{smooth(l, closed=False)}" fill="none" stroke="#e48cc4" stroke-width="2" stroke-dasharray="3 4" opacity=".8"/>'
    fringe_b, fringe_f = "", ""
    for i in range(30):
        th = math.pi * i / 29
        x = cx - 96 * math.cos(th)
        yb = 122 - 10 * math.sin(th)
        yf = 124 + 12 * math.sin(th)
        L = 20 + 6 * math.sin(i * 1.7)
        fringe_b += f'<path d="M{f(x)} {f(yb)}q{f(a.j(4))} {f(L / 2)} {f(a.j(3))} {f(L)}" fill="none" stroke="#d6c4f6" stroke-width="2" stroke-linecap="round" opacity=".8"/>'
        fringe_f += (f'<path d="M{f(x)} {f(yf)}q{f(a.j(4))} {f(L / 2)} {f(a.j(3))} {f(L)}" fill="none" stroke="{INK}" stroke-width="3.6" stroke-linecap="round" opacity=".55"/>'
                     f'<path d="M{f(x)} {f(yf)}q{f(a.j(4))} {f(L / 2)} {f(a.j(3))} {f(L)}" fill="none" stroke="#efe2ff" stroke-width="2" stroke-linecap="round"/>')
    # the four rings (cloverleaf) seen through the bell
    rings = ""
    for k, (rx_, ry_) in enumerate(((cx - 20, 58), (cx + 20, 58), (cx - 17, 81), (cx + 17, 81))):
        th = math.atan2(ry_ - 70, rx_ - cx)
        a0 = th + math.pi + .45
        hs = [(rx_ + 13 * math.cos(a0 + (2 * math.pi - .9) * i / 14), ry_ + 8.5 * math.sin(a0 + (2 * math.pi - .9) * i / 14)) for i in range(15)]
        hd = smooth(hs, closed=False)
        rings += (f'<path d="{hd}" fill="none" stroke="{RING}" stroke-width="5.5" stroke-linecap="round" opacity=".9"/>'
                  f'<path d="{hd}" fill="none" stroke="#f6d2ff" stroke-width="1.8" stroke-linecap="round"/>')
    bellg = (f'<path d="{bell}" fill="{bg}"/>' + rings +
             f'<ellipse cx="{cx}" cy="124" rx="96" ry="12" fill="none" stroke="#c9b4f2" stroke-width="3" opacity=".8"/>'
             f'<path d="M{cx - 70} 66Q{cx - 50} 44 {cx - 18} 38" fill="none" stroke="#fff" stroke-width="5" stroke-linecap="round" opacity=".9"/>'
             f'<path d="{bell}" fill="none" stroke="{INK}" stroke-width="2.6" stroke-linejoin="round"/>')
    face = eye(cx - 22, 106, 8) + eye(cx + 22, 106, 8) + blush(cx - 36, 119, 7, 3.6) + blush(cx + 36, 119, 7, 3.6) + smile(cx, 119, 13, sw=2.3)
    lids_ = lid(cx - 22, 106, 8, "#f2ecff") + lid(cx + 22, 106, 8, "#f2ecff")
    body = (grp("tentacles", fringe_b + arms, (cx, 126)) + bellg + grp("tentacles fringe", fringe_f, (cx, 126)) + face +
            grp("lids", lids_, (cx, 104), ' opacity="0"'))
    an = anchors([(cx - 66, 66), (cx + 20, 50), (cx + 88, 146)], (cx, 100))
    write("meduza", creature_svg("meduza", "Talířovka ušatá", W, H, a.defs, body, an, (22, 218), "pulse", body_pivot=(cx, 110)))


# ================================================================== 12 delfin
def delfin():
    a = Art("delfin", seed=22)
    W, H = 340, 180
    C, CL, CD = "#7891a8", "#a9bfd2", "#556e86"
    BELLY = "#eef3f6"
    pts = [(334, 104), (326, 98), (306, 94), (300, 80), (284, 64), (250, 56), (200, 52), (140, 62), (96, 78), (64, 90),
           (60, 100), (90, 108), (150, 122), (220, 132), (274, 124), (304, 112), (326, 110)]
    bd = smooth(a.jit(pts, .3), t=.17)
    tail = smooth([(66, 92), (40, 76), (16, 64), (22, 84), (36, 98), (20, 116), (16, 134), (42, 118), (66, 102)], t=.16)
    tailg = a.shape(tail, mix(C, CD, .2), CL, CD, 60, 134, hi=False)
    dorsal = smooth([(206, 54), (176, 34), (156, 16), (170, 40), (160, 58)], t=.2)
    dorg = a.shape(dorsal, mix(C, CD, .25), CL, CD, 16, 58, hi=False)
    torso = a.shape(bd, C, CL, CD, 52, 132, hi_box=(230, 64, 60, 9))
    c = a.clip("belly", bd)
    belly = (f'<g clip-path="{c}"><path d="M330 108Q296 114 270 112Q210 112 140 104Q100 100 70 102L70 140L340 140Z" fill="{BELLY}"/>'
             f'<path d="M330 108Q296 114 270 112Q210 112 140 104Q100 100 70 102" fill="none" stroke="{CD}" stroke-width="2" opacity=".5"/></g>')
    fin = smooth([(258, 120), (240, 140), (222, 156), (232, 138), (240, 122)], t=.2)
    fing = a.shape(fin, mix(C, CD, .1), CL, CD, 118, 156, hi=False)
    face = (eye(276, 92, 8.5, look=(.25, 0)) + blush(282, 106, 6, 3.4) +
            f'<path d="M332 106Q312 112 290 106" fill="none" stroke="{INK}" stroke-width="2.4" stroke-linecap="round"/>'
            f'<path d="M290 106q-4 -1 -5 -4" fill="none" stroke="{INK}" stroke-width="2.2" stroke-linecap="round"/>'
            f'<path d="M256 58q6 -4 12 0" fill="none" stroke="{INK}" stroke-width="2.6" stroke-linecap="round"/>')
    lids_ = lid(276, 92, 8.5, C)
    body = (grp("tail", tailg, (66, 97)) + dorg + torso + belly + face + grp("fin", fing, (248, 122)) +
            grp("lids", lids_, (276, 92), ' opacity="0"'))
    an = anchors([(330, 104), (166, 32), (262, 56)], (190, 94))
    write("delfin", creature_svg("delfin", "Delfín skákavý", W, H, a.defs, body, an, (16, 334), "swim", body_pivot=(190, 94)))


# ================================================================== 13 zelva + guide turtle
def turtle(guide=False):
    a = Art("guide" if guide else "zelva", seed=23)
    W, H = 320, 210
    SH, SHL, SHD = "#b8643a", "#df915e", "#7f3f22"
    SK, SKL, SKD = "#e6b56a", "#f6d699", "#b07e3c"
    PL = "#f3d98e"
    # far front flipper (behind)
    fin2 = smooth([(222, 96), (198, 72), (172, 56), (160, 58), (178, 80), (206, 106)], t=.2)
    fin2g = a.shape(fin2, mix(SK, SKD, .4), SKL, SKD, 56, 106, hi=False)
    # rear flippers + tail
    rear = smooth([(76, 120), (54, 128), (34, 140), (44, 146), (70, 140), (86, 130)], t=.2)
    rearg = a.shape(rear, mix(SK, SKD, .2), SKL, SKD, 118, 146, hi=False)
    # plastron band + shell dome
    plast = smooth([(70, 118), (120, 134), (190, 136), (238, 120), (232, 112), (80, 110)], t=.2)
    plastg = a.shape(plast, PL, "#fff0c0", "#d8b860", 110, 136, hi=False)
    shell = smooth(a.jit([(62, 116), (72, 84), (104, 54), (150, 40), (196, 46), (230, 72), (244, 102), (238, 118), (150, 122), (88, 122)], .5), t=.18)
    shellg = a.shape(shell, SH, SHL, SHD, 40, 122, hi_box=(140, 56, 50, 12))
    c = a.clip("scutes", shell)
    sc = ""
    # vertebral row (top) + costal plates (side): soft hexagon outlines
    for x, y, w, h in ((110, 58, 30, 22), (150, 50, 32, 22), (192, 58, 30, 22)):
        hx = smooth([(x - w / 2, y), (x - w / 3, y - h / 2), (x + w / 3, y - h / 2), (x + w / 2, y), (x + w / 3, y + h / 2), (x - w / 3, y + h / 2)], t=.12)
        sc += f'<path d="{hx}" fill="{SHL}" fill-opacity=".35" stroke="{SHD}" stroke-width="2.4"/>'
    for x, y in ((92, 92), (132, 86), (172, 86), (212, 92)):
        hx = smooth([(x - 20, y - 8), (x, y - 16), (x + 20, y - 8), (x + 18, y + 14), (x - 18, y + 14)], t=.12)
        sc += f'<path d="{hx}" fill="{SHL}" fill-opacity=".25" stroke="{SHD}" stroke-width="2.2"/>'
    sc += "".join(f'<path d="M{f(70 + i * 17)} 116l4 -6" stroke="{SHD}" stroke-width="2" opacity=".7"/>' for i in range(10))
    # head (big — loggerhead) + neck
    neck = smooth([(226, 92), (252, 84), (260, 112), (232, 118)], t=.2)
    neckg = a.shape(neck, SK, SKL, SKD, 84, 118, hi=False)
    head = smooth([(246, 92), (256, 70), (280, 62), (304, 70), (314, 88), (308, 106), (284, 116), (258, 114)], t=.2)
    headg = a.shape(head, SK, SKL, SKD, 62, 116, hi_box=(282, 74, 16, 6))
    c2 = a.clip("hs", head)
    plates = "".join(f'<path d="M{f(x)} {f(y)}l8 -4l8 4" fill="none" stroke="{SKD}" stroke-width="1.6" opacity=".6"/>' for x, y in ((262, 80), (276, 72), (290, 74)))
    face_e = eye(290, 86, 9.5, look=(.3, .05)) + blush(296, 102, 6, 3.4)
    mouth = f'<path d="M313 98Q300 108 286 104" fill="none" stroke="{INK}" stroke-width="2.4" stroke-linecap="round"/>'
    talk = (f'<path d="M313 97Q300 102 286 103Q298 116 312 104Z" fill="#8a2f3c" stroke="{INK}" stroke-width="2.2" stroke-linejoin="round"/>')
    lids_ = lid(290, 86, 9.5, SK)
    fin = smooth([(214, 116), (196, 140), (164, 166), (146, 172), (160, 152), (192, 122)], t=.2)
    fing = a.shape(fin, SK, SKL, SKD, 116, 172, hi_box=(184, 136, 16, 5))
    fing += "".join(f'<path d="M{f(x)} {f(y)}l6 -2" stroke="{SKD}" stroke-width="1.8" opacity=".7"/>' for x, y in ((178, 146), (190, 136), (166, 158)))
    mouths = mouth if not guide else grp("mouth", mouth) + grp("mouth-talk", talk, None, ' opacity="0"')
    body = (grp("fin-2", fin2g, (214, 98)) + grp("tail", rearg, (80, 124)) + neckg + plastg + shellg +
            f'<g clip-path="{c}">{sc}</g><path d="{shell}" fill="none" stroke="{INK}" stroke-width="3"/>' +
            headg + f'<g clip-path="{c2}">{plates}</g><path d="{head}" fill="none" stroke="{INK}" stroke-width="3"/>' +
            face_e + mouths + grp("fin", fing, (206, 118)) + grp("lids", lids_, (290, 86), ' opacity="0"'))
    an = anchors([(280, 66), (150, 60), (164, 162)], (160, 100))
    if guide:
        svg = creature_svg("zelva", "Želvička", W, H, a.defs, body, an, (30, 316), "glide", root_cls="creature guide", body_pivot=(160, 104))
        with open(os.path.join(OUT, "guide-turtle.svg"), "w") as fh:
            fh.write(svg)
    else:
        write("zelva", creature_svg("zelva", "Kareta obecná", W, H, a.defs, body, an, (30, 316), "glide", body_pivot=(160, 104)))


def zelva():
    turtle(False)


def guide():
    turtle(True)


# ================================================================== 14 keporkak
def keporkak():
    a = Art("keporkak", seed=24)
    W, H = 420, 220
    C, CL, CD = "#4c6384", "#7189ab", "#33465f"
    WHITE = "#eef2f6"
    pts = [(412, 96), (400, 80), (370, 68), (330, 60), (270, 54), (210, 54), (176, 50), (160, 54), (120, 68), (80, 86), (64, 94),
           (66, 106), (110, 118), (170, 138), (240, 154), (300, 154), (360, 138), (398, 116)]
    bd = smooth(a.jit(pts, .4), t=.17)
    tail = smooth([(70, 94), (42, 74), (12, 58), (20, 78), (14, 92), (24, 100), (14, 112), (20, 128), (12, 146), (44, 124), (70, 104)], t=.15)
    tailg = a.shape(tail, mix(C, CD, .2), CL, CD, 58, 146, hi=False)
    torso = a.shape(bd, C, CL, CD, 58, 142, hi_box=(260, 74, 90, 10))
    c = a.clip("pleats", bd)
    pleats = (f'<path d="M408 104Q370 128 300 146L300 160L420 160Z" fill="{WHITE}"/>' +
              "".join(f'<path d="M{f(404 - k * 4)} {f(106 + k * 4)}Q{f(350 - k * 8)} {f(130 + k * 3)} {f(250 - k * 10)} {f(142 + k * 2)}" fill="none" stroke="#9fb0c4" stroke-width="2.2"/>' for k in range(6)))
    knobs = "".join(f'<circle cx="{f(x)}" cy="{f(y)}" r="3.6" fill="{CL}" stroke="{CD}" stroke-width="1.4"/>'
                    for x, y in ((396, 86), (386, 81), (374, 78), (392, 94), (380, 89), (366, 84), (402, 102)))
    mouth = f'<path d="M410 102Q380 110 344 112" fill="none" stroke="{INK}" stroke-width="2.6" stroke-linecap="round"/>'
    face = eye(336, 100, 7, look=(.25, 0)) + blush(338, 116, 6, 3.2)
    # the famous long white pectoral fin, scalloped leading edge
    fin_pts = [(310, 130), (290, 150), (256, 172), (220, 192), (184, 206), (174, 200), (194, 180), (230, 160), (266, 140), (290, 126)]
    fin = smooth(fin_pts, t=.18)
    fing = a.shape(fin, WHITE, "#ffffff", "#b9c6d4", 124, 196, hi=False)
    fing += "".join(f'<circle cx="{f(x)}" cy="{f(y)}" r="3.2" fill="{WHITE}" stroke="{INK}" stroke-width="1.6"/>' for x, y in ((282, 154), (256, 170), (230, 184), (204, 196)))
    dors = smooth([(186, 54), (170, 42), (154, 52), (162, 58)], t=.2)
    lids_ = lid(336, 100, 7, C)
    body = (grp("tail", tailg, (70, 99)) + f'<path d="{dors}" fill="{CD}" stroke="{INK}" stroke-width="2.6"/>' + torso +
            f'<g clip-path="{c}">{pleats}</g><path d="{bd}" fill="none" stroke="{INK}" stroke-width="3"/>' + knobs + mouth + face +
            grp("fin", fing, (298, 126)) + grp("lids", lids_, (336, 100), ' opacity="0"'))
    an = anchors([(214, 186), (386, 80), (330, 140)], (220, 104))
    write("keporkak", creature_svg("keporkak", "Keporkak", W, H, a.defs, body, an, (12, 412), "glide", body_pivot=(220, 104)))


# ================================================================== 15 zralok (Rhincodon typus)
def zralok():
    a = Art("zralok", seed=25)
    W, H = 420, 200
    C, CL, CD = "#41628c", "#6b8fbb", "#2b4466"
    BELLY = "#eaf0f6"
    pts = [(412, 104), (408, 90), (390, 80), (340, 70), (280, 64), (220, 64), (160, 72), (110, 84), (76, 94), (72, 104),
           (110, 112), (180, 122), (260, 128), (330, 126), (390, 118), (410, 112)]
    bd = smooth(a.jit(pts, .3), t=.17)
    tail = smooth([(78, 96), (54, 70), (30, 30), (24, 26), (32, 70), (40, 100), (30, 140), (34, 146), (58, 120), (80, 106)], t=.15)
    tailg = a.shape(tail, mix(C, CD, .2), CL, CD, 26, 146, hi=False)
    d1 = smooth([(230, 66), (206, 42), (190, 26), (186, 30), (190, 64)], t=.2)
    d1g = a.shape(d1, mix(C, CD, .2), CL, CD, 26, 66, hi=False)
    torso = a.shape(bd, C, CL, CD, 64, 128, hi_box=(300, 74, 80, 8))
    c = a.clip("spots", bd)
    belly = f'<path d="M412 108Q360 118 300 118Q200 116 100 106L100 140L420 140Z" fill="{BELLY}"/>'
    spots = []
    for col in range(16):
        x = 110 + col * 18
        for row in range(4):
            y = 74 + row * 11 + (col % 2) * 5
            spots.append(f'<circle cx="{f(x + a.j(2))}" cy="{f(y + a.j(1.5))}" r="{f(2.8 + a.j(.6))}" fill="#f4f8ff"/>')
    stripes = "".join(f'<path d="M{f(120 + k * 36)} 70L{f(118 + k * 36)} 110" stroke="#dfe9f6" stroke-width="2" opacity=".55"/>' for k in range(8))
    ridges = "".join(f'<path d="M{f(380)} {f(y)}Q260 {f(y - 4)} 100 {f(y + 4)}" fill="none" stroke="{CL}" stroke-width="2.4" opacity=".8"/>' for y in (86, 98))
    gills = "".join(f'<path d="M{f(x)} 92q-4 12 0 22" fill="none" stroke="{CD}" stroke-width="2.4" stroke-linecap="round"/>' for x in (336, 344, 352, 360))
    mouth = (f'<path d="M412 108Q394 116 370 112" fill="none" stroke="{INK}" stroke-width="2.8" stroke-linecap="round"/>'
             f'<path d="M370 112q-4 -1 -5 -5" fill="none" stroke="{INK}" stroke-width="2.4" stroke-linecap="round"/>')
    face = eye(378, 92, 7, look=(.25, 0)) + blush(388, 104, 5, 3)
    fin = smooth([(318, 122), (298, 146), (272, 172), (264, 168), (282, 140), (300, 120)], t=.2)
    fing = a.shape(fin, mix(C, CD, .1), CL, CD, 120, 172, hi=False)
    lids_ = lid(378, 92, 7, C)
    body = (grp("tail", tailg, (78, 100)) + d1g + torso +
            f'<g clip-path="{c}">{belly}{stripes}{"".join(spots)}{ridges}{gills}</g><path d="{bd}" fill="none" stroke="{INK}" stroke-width="3"/>' +
            mouth + face + grp("fin", fing, (308, 124)) + grp("lids", lids_, (378, 92), ' opacity="0"'))
    an = anchors([(220, 80), (406, 108), (160, 96)], (230, 96))
    write("zralok", creature_svg("zralok", "Žralok obrovský", W, H, a.defs, body, an, (24, 412), "glide", body_pivot=(230, 98)))


# ================================================================== 16 manta
def manta():
    """Mobula birostris seen from above-side: triangular wings, two horn-like head lobes, dark back with white shoulder patches."""
    a = Art("manta", seed=26)
    W, H = 380, 270
    C, CL, CD = "#2f3e62", "#5a6ea0", "#1e2944"
    WHITE = "#f1f4fa"
    # wings are drawn from the body axis outward; the body core covers their roots with the SAME fill (no seam)
    far = smooth([(306, 122), (262, 88), (200, 40), (170, 18), (158, 26), (160, 70), (140, 122)], t=.17)
    farg = a.shape(far, mix(C, CD, .35), mix(CL, CD, .3), CD, 18, 122, hi=False)
    near = smooth([(306, 140), (262, 178), (196, 228), (156, 256), (142, 246), (150, 196), (136, 140)], t=.17)
    nearg = a.shape(near, C, CL, CD, 140, 256, hi_box=(206, 186, 36, 10))
    c = a.clip("nw", near)
    nearg += (f'<g clip-path="{c}"><path d="M152 240Q210 210 276 160" fill="none" stroke="#ffffff" stroke-width="5" opacity=".18"/>'
              f'<path d="M156 254Q220 222 300 152" fill="none" stroke="{WHITE}" stroke-width="7" opacity=".6"/></g>'
              f'<path d="{near}" fill="none" stroke="{INK}" stroke-width="3"/>')
    core = smooth([(132, 131), (170, 112), (240, 106), (300, 110), (328, 122), (332, 140), (304, 154), (240, 158), (170, 152)], t=.18)
    coreg = a.linear("core", [(0, CL), (.5, C), (1, CD)], 0, 106, 0, 158)
    c2 = a.clip("core", core)
    patches = (f'<path d="M286 112Q256 122 222 116Q250 110 278 108Z" fill="{WHITE}" opacity=".95"/>'
               f'<path d="M288 150Q256 142 222 148Q252 156 280 154Z" fill="{WHITE}" opacity=".95"/>')
    head_outline = smooth([(300, 110), (328, 122), (332, 140), (304, 154)], closed=False)
    tail = (f'<path d="M140 132Q90 140 20 152" fill="none" stroke="{INK}" stroke-width="7" stroke-linecap="round"/>'
            f'<path d="M140 132Q90 140 20 152" fill="none" stroke="{CD}" stroke-width="3.5" stroke-linecap="round"/>')
    horns = ""
    for (y0, s_) in ((120, -1), (142, 1)):
        h = smooth([(322, y0), (346, y0 + s_ * 2), (360, y0 + s_ * 12), (352, y0 + s_ * 18), (340, y0 + s_ * 8), (322, y0 + s_ * 8)], t=.2)
        horns += a.shape(h, mix(C, CD, .2), CL, CD, min(y0, y0 + s_ * 18), max(y0, y0 + s_ * 18), hi=False)
    mouth = f'<path d="M334 125Q343 131 334 138" fill="none" stroke="{WHITE}" stroke-width="3.4" stroke-linecap="round"/>'
    face = eye(312, 121, 7, look=(.3, 0)) + eye(314, 146, 8, look=(.3, 0)) + blush(304, 158, 5, 2.8)
    lids_ = lid(312, 121, 7, C) + lid(314, 146, 8, C)
    body = (grp("fin-2", farg, (240, 118)) + tail + grp("fin", nearg, (240, 144)) +
            f'<path d="{core}" fill="{coreg}"/><g clip-path="{c2}">{patches}</g>'
            f'<path d="{head_outline}" fill="none" stroke="{INK}" stroke-width="3" stroke-linecap="round"/>' +
            horns + mouth + face + grp("lids", lids_, (313, 134), ' opacity="0"'))
    an = anchors([(176, 228), (356, 108), (254, 114)], (240, 134))
    write("manta", creature_svg("manta", "Manta obrovská", W, H, a.defs, body, an, (20, 360), "glide", body_pivot=(240, 134)))

# ================================================================== 17 sardinky
def sardine(a, nose, L, dim=0.0, eye_on=True):
    SIL, SILL, SILD = mix("#c9d6e2", "#7fb3c8", dim), mix("#f4f8fb", "#a8d0de", dim), mix("#8fa3b6", "#5f8aa0", dim)
    BACK = mix("#3a8a74", "#5fa79a", dim)
    nx, ny = nose
    pts = profile(nose, L, [(0, 0, 0), (.04, 6, 5), (.14, 14, 12), (.35, 18, 16), (.65, 15, 13), (.88, 8, 7), (1, 5, 5)])
    bd = smooth(pts)
    tx = nx - L
    tail = smooth([(tx + 2, ny - 4), (tx - 16, ny - 18), (tx - 12, ny), (tx - 16, ny + 18), (tx + 2, ny + 4)], t=.12)
    out = f'<path d="{tail}" fill="{SILD}" stroke="{INK}" stroke-width="2.2" stroke-linejoin="round"/>'
    out += f'<path d="{smooth([(nx - L * .45, ny - 15), (nx - L * .36, ny - 26), (nx - L * .28, ny - 16)])}" fill="{BACK}" stroke="{INK}" stroke-width="2"/>'
    out += a.shape(bd, SIL, SILL, SILD, ny - 18, ny + 16, sw=2.4, hi_box=(nx - L * .4, ny + 4, L * .3, 3))
    c = a.clip("sb", bd)
    out += (f'<g clip-path="{c}"><path d="M{f(nx)} {f(ny - 4)}Q{f(nx - L * .5)} {f(ny - 8)} {f(tx)} {f(ny - 2)}L{f(tx)} {f(ny - 30)}L{f(nx)} {f(ny - 30)}Z" fill="{BACK}"/>'
            + "".join(f'<circle cx="{f(nx - L * (.3 + k * .09))}" cy="{f(ny - 4 + k * .4)}" r="{f(max(1.6, L * .016))}" fill="#22364a"/>' for k in range(5))
            + f'</g><path d="{bd}" fill="none" stroke="{INK}" stroke-width="2.4"/>')
    if eye_on:
        out += eye(nx - L * .1, ny - 2, max(4, L * .045), look=(.25, 0)) + smile(nx - L * .02, ny + 4, L * .04, sw=1.8, tilt=-.2)
    return out


def sardinky():
    a = Art("sardinky", seed=27)
    W, H = 320, 210
    back1 = sardine(a, (196, 52), 128, dim=.35)
    back2 = sardine(a, (176, 168), 116, dim=.35)
    main = sardine(a, (300, 112), 210)
    lids_ = lid(300 - 21, 110, 9.4, "#c9d6e2")
    body = (grp("fin-2", back1 + back2, (150, 110)) + main + grp("lids", lids_, (279, 110), ' opacity="0"'))
    an = anchors([(200, 122), (196, 96), (170, 110)], (190, 112))
    write("sardinky", creature_svg("sardinky", "Sardinka obecná", W, H, a.defs, body, an, (74, 300), "school", body_pivot=(190, 112)))


# ================================================================== 18 das (Melanocetus johnsonii)
def das():
    a = Art("das", seed=28)
    W, H = 280, 250
    C, CL, CD = "#5a3f6e", "#8466a0", "#3a2850"
    cx, cy = 128, 150
    bd = smooth(a.jit([(cx + 86, cy - 20), (cx + 70, cy - 66), (cx + 20, cy - 86), (cx - 40, cy - 76), (cx - 78, cy - 34), (cx - 84, cy + 20),
                       (cx - 56, cy + 62), (cx, cy + 80), (cx + 52, cy + 66), (cx + 84, cy + 30)], .6), t=.18)
    tail = smooth([(cx - 76, cy - 6), (cx - 108, cy - 34), (cx - 116, cy), (cx - 108, cy + 34), (cx - 76, cy + 16)], t=.18)
    tailg = a.shape(tail, mix(C, CD, .2), CL, CD, cy - 34, cy + 34, hi=False)
    torso = a.shape(bd, C, CL, CD, cy - 86, cy + 80, hi_box=(cx - 10, cy - 60, 40, 14))
    c = a.clip("rim", bd)
    rim = (f'<g clip-path="{c}"><path d="{bd}" fill="none" stroke="#9ff7ff" stroke-width="10" opacity=".22" transform="translate(-4 4)"/>'
           f'<ellipse cx="{cx + 10}" cy="{cy + 54}" rx="70" ry="26" fill="#c3a6dc" opacity=".35"/></g>')
    # the big friendly closed mouth (lips only, never teeth)
    mouth = (f'<path d="M{cx + 84} {cy - 8}Q{cx + 60} {cy + 52} {cx - 4} {cy + 36}" fill="none" stroke="{INK}" stroke-width="3.4" stroke-linecap="round"/>'
             f'<path d="M{cx + 82} {cy - 2}Q{cx + 58} {cy + 46} {cx + 4} {cy + 32}" fill="none" stroke="#e7a0c0" stroke-width="3" stroke-linecap="round" opacity=".7"/>'
             f'<path d="M{cx - 4} {cy + 36}q-6 -2 -7 -9" fill="none" stroke="{INK}" stroke-width="3" stroke-linecap="round"/>')
    face = eye(cx + 46, cy - 36, 8.5, look=(.3, .05)) + blush(cx + 36, cy - 14, 8, 4.5)
    # rod + lure
    rod = f'<path d="M{cx + 30} {cy - 82}Q{cx + 70} {cy - 140} {cx + 116} {cy - 116}" fill="none" stroke="{INK}" stroke-width="5" stroke-linecap="round"/>' \
          f'<path d="M{cx + 30} {cy - 82}Q{cx + 70} {cy - 140} {cx + 116} {cy - 116}" fill="none" stroke="{CL}" stroke-width="2.4" stroke-linecap="round"/>'
    lx, ly = cx + 118, cy - 104
    halo = a.radial("halo", [(0, "#c8fff0", .95), (.3, "#6ff3ff", .55), (1, "#6ff3ff", 0)], user=(lx, ly, 46))
    glow = (f'<circle cx="{lx}" cy="{ly}" r="46" fill="{halo}"/>')
    bulb = (f'<circle cx="{lx}" cy="{ly}" r="10" fill="#d8fff4" stroke="{INK}" stroke-width="2.6"/>'
            f'<circle cx="{lx - 3}" cy="{ly - 3}" r="3.4" fill="#fff"/>')
    fin = fan(a, [(cx - 30, cy + 14), (cx - 32, cy + 30)], [(cx - 60, cy + 44), (cx - 68, cy + 26), (cx - 58, cy + 10)], mix(C, "#ffffff", .2), CD, op=.9)
    lids_ = lid(cx + 46, cy - 36, 8.5, C)
    body = (grp("tail", tailg, (cx - 76, cy + 4)) + torso + rim + mouth + face + rod + grp("glow", glow, (lx, ly), ' opacity="1"') + bulb +
            grp("fin", fin, (cx - 31, cy + 22)) + grp("lids", lids_, (cx + 46, cy - 36), ' opacity="0"'))
    an = anchors([(lx, ly), (cx + 62, cy + 30), (cx - 40, cy - 30)], (cx, cy))
    write("das", creature_svg("das", "Hlubinný ďas", W, H, a.defs, body, an, (12, 246), "hover", body_pivot=(cx, cy)))


# ================================================================== 19 dumbo
def dumbo():
    a = Art("dumbo", seed=29)
    W, H = 260, 260
    C, CL, CD = "#f4a7ae", "#ffd6d2", "#d27a86"
    cx = 130
    ear2 = smooth([(92, 70), (66, 50), (42, 52), (40, 74), (64, 92), (90, 92)], t=.2)
    ear2g = a.shape(ear2, mix(C, CD, .35), CL, CD, 50, 92, hi=False)
    ear = smooth([(170, 66), (196, 42), (224, 40), (230, 64), (206, 88), (176, 92)], t=.2)
    earg = a.shape(ear, C, CL, CD, 40, 92, hi_box=(206, 54, 10, 5))
    mantle = smooth(a.jit([(cx - 62, 150), (cx - 70, 104), (cx - 50, 56), (cx, 36), (cx + 50, 56), (cx + 70, 104), (cx + 62, 150)], .5), t=.18)
    # webbed skirt: scalloped edge with arm tips
    sk = [(cx - 62, 146)]
    for k in range(7):
        x0 = cx - 62 + k * 124 / 6
        sk.append((x0, 220 - 10 * math.sin(k * 1.1)))
    sk.append((cx + 62, 146))
    skirt_pts = [(cx - 64, 144), (cx - 84, 196), (cx - 70, 214), (cx - 50, 202), (cx - 30, 226), (cx - 10, 210), (cx + 10, 230),
                 (cx + 30, 210), (cx + 50, 226), (cx + 70, 204), (cx + 86, 214), (cx + 84, 192), (cx + 64, 144)]
    skirt = smooth(skirt_pts, t=.16)
    skg = a.shape(skirt, mix(C, CD, .25), C, CD, 144, 226, hi=False)
    c = a.clip("web", skirt)
    arms = "".join(f'<path d="M{f(cx + (k - 3.5) * 14)} 150Q{f(cx + (k - 3.5) * 22)} 190 {f(x)} {f(y - 4)}" fill="none" stroke="{CD}" stroke-width="5" stroke-linecap="round" opacity=".8"/>'
                   for k, (x, y) in enumerate([(cx - 84, 196), (cx - 50, 202), (cx - 30, 226), (cx - 10, 210), (cx + 30, 210), (cx + 50, 226), (cx + 70, 204), (cx + 86, 214)]))
    cirri = "".join(f'<circle cx="{f(cx + (k - 3) * 22 + 6)}" cy="{f(196 + (k % 2) * 6)}" r="2.6" fill="#ffe6e6" opacity=".9"/>' for k in range(7))
    mant = a.shape(mantle, C, CL, CD, 36, 150, hi_box=(cx - 18, 62, 26, 12))
    face = eye(cx - 24, 112, 14, look=(.25, .05)) + eye(cx + 26, 110, 14, look=(.25, .05)) + blush(cx - 42, 134, 8, 4.5) + blush(cx + 44, 132, 8, 4.5) + smile(cx + 2, 134, 14, sw=2.4)
    lids_ = lid(cx - 24, 112, 14, C) + lid(cx + 26, 110, 14, C)
    body = (grp("fin-2", ear2g, (90, 80)) + grp("tentacles", skg + f'<g clip-path="{c}">{arms}{cirri}</g><path d="{skirt}" fill="none" stroke="{INK}" stroke-width="3"/>', (cx, 146)) +
            mant + face + grp("fin", earg, (172, 78)) + grp("lids", lids_, (cx + 1, 111), ' opacity="0"'))
    an = anchors([(214, 56), (cx + 46, 214), (cx + 34, 62)], (cx, 120))
    write("dumbo", creature_svg("dumbo", "Chobotnice dumbo", W, H, a.defs, body, an, (40, 232), "flap", body_pivot=(cx, 120)))


# ================================================================== 20 svetluska = Atolla wyvillei
def svetluska():
    a = Art("svetluska", seed=30)
    W, H = 240, 290
    C, CL, CD = "#b0263f", "#e2566e", "#6a1024"
    cx = 120
    # one long trailing tentacle (the atolla's signature) + many short ones (g.tentacles)
    long_t = [(cx + 30, 118), (cx + 46, 160), (cx + 34, 200), (cx + 52, 240), (cx + 40, 276)]
    lt = f'<path d="{smooth(long_t, closed=False)}" fill="none" stroke="{INK}" stroke-width="5.5" stroke-linecap="round"/>' \
         f'<path d="{smooth(long_t, closed=False)}" fill="none" stroke="#f08aa0" stroke-width="2.8" stroke-linecap="round"/>'
    short = ""
    for i in range(18):
        x = cx - 80 + i * 160 / 17
        L = 18 + 4 * math.sin(i * 2.1)
        short += (f'<path d="M{f(x)} {f(116 + 6 * math.sin(i / 17 * math.pi))}q{f(a.j(3))} {f(L / 2)} {f(a.j(2))} {f(L)}" fill="none" stroke="{INK}" stroke-width="3.4" stroke-linecap="round" opacity=".6"/>'
                  f'<path d="M{f(x)} {f(116 + 6 * math.sin(i / 17 * math.pi))}q{f(a.j(3))} {f(L / 2)} {f(a.j(2))} {f(L)}" fill="none" stroke="#e57a90" stroke-width="1.8" stroke-linecap="round"/>')
    # bell: low crown dome over a scalloped margin of lappets
    crown = smooth([(cx - 66, 92), (cx - 56, 60), (cx - 24, 44), (cx + 24, 44), (cx + 56, 60), (cx + 66, 92), (cx, 100)], t=.18)
    lapp = []
    for i in range(16):
        t0 = i / 16
        th = math.pi * (1 - t0)
        lapp.append((cx + 92 * math.cos(th), 104 + 14 * math.sin(th) * .2))
        th2 = math.pi * (1 - (i + .5) / 16)
        lapp.append((cx + 100 * math.cos(th2), 120 + 4 * math.sin(th2)))
    margin_pts = [(cx - 92, 104)] + lapp + [(cx + 92, 104), (cx + 60, 86), (cx - 60, 86)]
    margin = smooth(margin_pts, t=.15)
    mg = a.shape(margin, mix(C, CD, .15), CL, CD, 86, 124, hi=False)
    cg = a.shape(crown, C, CL, CD, 44, 100, hi_box=(cx - 14, 58, 26, 8))
    groove = f'<path d="M{cx - 64} 90Q{cx} 106 {cx + 64} 90" fill="none" stroke="{CD}" stroke-width="3" opacity=".7"/>'
    lights = ""
    halo = a.radial("bl", [(0, "#a8f2ff", 1), (.35, "#4fb8ff", .55), (1, "#4fb8ff", 0)], cx="50%", cy="50%", r="50%")
    for i in range(14):
        th = math.pi * (1 - (i + .5) / 14)
        x, y = cx + 86 * math.cos(th), 110 + 6 * math.sin(th)
        lights += f'<circle cx="{f(x)}" cy="{f(y)}" r="9" fill="{halo}"/><circle cx="{f(x)}" cy="{f(y)}" r="2.6" fill="#e6fbff"/>'
    face = eye(cx - 20, 74, 8.5) + eye(cx + 20, 74, 8.5) + blush(cx - 34, 88, 6, 3.2, .4) + blush(cx + 34, 88, 6, 3.2, .4) + smile(cx, 88, 12, sw=2.3)
    lids_ = lid(cx - 20, 74, 8.5, C) + lid(cx + 20, 74, 8.5, C)
    body = (grp("tentacles", short + lt, (cx, 112)) + mg + cg + groove + face + grp("glow", lights, (cx, 110), ' opacity="1"') +
            grp("lids", lids_, (cx, 74), ' opacity="0"'))
    an = anchors([(cx - 40, 56), (cx + 46, 236), (cx + 82, 116)], (cx, 90))
    write("svetluska", creature_svg("svetluska", "Medúza atolla", W, H, a.defs, body, an, (20, 220), "pulse", body_pivot=(cx, 96)))


# ================================================================== 21 kapustnak (manatee)
def kapustnak():
    """Trichechus — the gentle 'sea cow': round wrinkly grey-brown body, round paddle tail,
    whiskery snout with a big upper lip, front flippers with little nails."""
    a = Art("kapustnak", seed=31)
    W, H = 360, 200
    C, CL, CD = "#9a8f84", "#c7bdb1", "#6b6158"
    # far flipper (behind)
    fin2 = smooth([(254, 120), (240, 150), (228, 168), (216, 162), (228, 136), (242, 116)], t=.2)
    fin2g = a.shape(fin2, mix(C, CD, .35), CL, CD, 114, 160, hi=False)
    # round paddle tail
    tail = smooth(ellipse_pts(34, 104, 30, 36, n=14, wob=lambda t: .03 * math.sin(3 * t)), t=.18)
    tailg = a.shape(tail, mix(C, CD, .15), CL, CD, 68, 140, hi_box=(30, 86, 12, 8))
    tailg += f'<path d="M14 104Q34 98 54 104" fill="none" stroke="{CD}" stroke-width="1.6" opacity=".5"/>'
    body_pts = [(340, 112), (334, 90), (316, 74), (292, 62), (240, 42), (170, 38), (110, 50), (72, 76), (54, 96),
                (56, 114), (78, 134), (130, 156), (210, 166), (280, 154), (318, 136), (338, 124)]
    bd = smooth(a.jit(body_pts, .4), t=.17)
    torso = a.shape(bd, C, CL, CD, 38, 166, hi_box=(190, 56, 80, 12))
    c = a.clip("wr", bd)
    wrinkles = "".join(f'<path d="M{f(x)} {f(y0)}q{f(-6)} {f((y1 - y0) / 2)} 0 {f(y1 - y0)}" fill="none" stroke="{CD}" stroke-width="2" opacity=".55" stroke-linecap="round"/>'
                       for x, y0, y1 in ((286, 76, 136), (275, 70, 142), (264, 64, 146)))
    wrinkles += "".join(f'<path d="M{f(x)} {f(y)}q8 -3 16 0" fill="none" stroke="{CD}" stroke-width="1.6" opacity=".45" stroke-linecap="round"/>'
                        for x, y in ((150, 70), (190, 62), (120, 92), (170, 108), (220, 98), (100, 118), (150, 136)))
    algae = "".join(f'<ellipse cx="{f(x)}" cy="{f(y)}" rx="{f(r)}" ry="{f(r * .6)}" fill="#8fae6a" opacity=".35"/>'
                    for x, y, r in ((160, 50, 9), (200, 46, 6), (128, 60, 5)))
    belly = f'<path d="M80 136Q170 168 300 144L320 180L60 180Z" fill="{CL}" opacity=".45"/>'
    # muzzle: big bristly upper lip
    lip = smooth([(316, 96), (334, 92), (344, 104), (342, 120), (330, 128), (316, 124), (310, 110)], t=.2)
    lipg = a.shape(lip, mix(C, "#ffffff", .2), "#ddd4ca", C, 92, 128, hi=False)
    bristles = "".join(f'<circle cx="{f(x)}" cy="{f(y)}" r="1.5" fill="{CD}"/>' for x, y in ((324, 104), (330, 101), (336, 106), (326, 112), (333, 114), (339, 112), (320, 116)))
    bristles += "".join(f'<path d="M{f(x)} {f(y)}l{f(dx)} {f(dy)}" stroke="{INK}" stroke-width="1.4" stroke-linecap="round" opacity=".7"/>'
                        for x, y, dx, dy in ((338, 108, 9, -3), (340, 114, 9, 1), (336, 120, 8, 5), (330, 122, 3, 8)))
    nostrils = f'<path d="M330 88q4 -2 6 1M338 92q3 -1 4 2" fill="none" stroke="{INK}" stroke-width="2" stroke-linecap="round"/>'
    face = (eye(300, 88, 8.5, look=(.25, 0)) + blush(306, 108, 6, 3.4) +
            f'<path d="M314 128Q322 133 330 129" fill="none" stroke="{INK}" stroke-width="2.2" stroke-linecap="round"/>')
    lids_ = lid(300, 88, 8.5, C)
    fin = smooth([(274, 124), (266, 154), (252, 180), (228, 180), (232, 150), (248, 120)], t=.2)
    fing = a.shape(fin, mix(C, CD, .1), CL, CD, 120, 180, hi_box=(254, 140, 7, 12))
    fing += "".join(f'<ellipse cx="{f(x)}" cy="{f(y)}" rx="3.2" ry="2.4" fill="#f4ead8" stroke="{INK}" stroke-width="1.4"/>' for x, y in ((234, 175), (242, 177), (250, 173)))
    body = (grp("fin-2", fin2g, (244, 118)) + grp("tail", tailg, (56, 104)) + torso +
            f'<g clip-path="{c}">{belly}{algae}{wrinkles}</g><path d="{bd}" fill="none" stroke="{INK}" stroke-width="3"/>' +
            lipg + bristles + nostrils + face + grp("fin", fing, (260, 122)) + grp("lids", lids_, (300, 88), ' opacity="0"'))
    an = anchors([(26, 104), (334, 110), (242, 174)], (190, 104))
    write("kapustnak", creature_svg("kapustnak", "Kapustňák", W, H, a.defs, body, an, (4, 344), "glide", floor=172, body_pivot=(190, 104)))

if __name__ == "__main__":
    import sys
    os.makedirs(OUT, exist_ok=True)
    names = sys.argv[1:] or [n for n in ("klaun", "sasanka", "konik", "hvezdice", "krab", "chobotnice", "papousek", "vydra", "tulen",
                                         "jezovka", "meduza", "delfin", "zelva", "keporkak", "zralok", "manta", "sardinky", "das",
                                         "dumbo", "svetluska", "kapustnak", "guide")]
    g = globals()
    for n in names:
        if n in g:
            g[n]()
            print("ok", n)
