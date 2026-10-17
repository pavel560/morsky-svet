"""Mořský svět — shared SVG kit for the deterministic art generators (stdlib only).

Style system (same craft as Houbičky, new world):
  * warm aubergine ink outline (INK) ~3 units on a ~240-unit character, never black;
  * gouache volume: a top-lit vertical gradient (light from the surface), a soft upper highlight
    clipped to the shape, a cool shadow band on the lower edge (bounce light from the water);
  * storybook faces: round eyes with two highlights, small closed smile, cheek blush; no teeth ever.
"""
import math
import random

INK = "#33243a"
INK_SOFT = "rgba(51,36,58,.55)"
WHITE = "#ffffff"
BLUSH = "#ff8f8f"


def f(v):
    s = f"{v:.1f}"
    if s == "-0.0":
        s = "0.0"
    return s[:-2] if s.endswith(".0") else s


def P(pts):
    return " ".join(f"{f(x)},{f(y)}" for x, y in pts)


def smooth(pts, closed=True, t=1 / 6):
    """Catmull-Rom through pts -> cubic bezier path."""
    n = len(pts)
    if n < 2:
        return ""
    out = [f"M{f(pts[0][0])} {f(pts[0][1])}"]
    rng = range(n) if closed else range(n - 1)
    for i in rng:
        p0 = pts[(i - 1) % n] if (closed or i > 0) else pts[i]
        p1 = pts[i]
        p2 = pts[(i + 1) % n]
        p3 = pts[(i + 2) % n] if (closed or i + 2 < n) else pts[(i + 1) % n]
        c1 = (p1[0] + (p2[0] - p0[0]) * t, p1[1] + (p2[1] - p0[1]) * t)
        c2 = (p2[0] - (p3[0] - p1[0]) * t, p2[1] - (p3[1] - p1[1]) * t)
        out.append(f"C{f(c1[0])} {f(c1[1])} {f(c2[0])} {f(c2[1])} {f(p2[0])} {f(p2[1])}")
    if closed:
        out.append("Z")
    return "".join(out)


def ellipse_pts(cx, cy, rx, ry, n=16, rot=0.0, wob=None):
    out = []
    cr, sr = math.cos(rot), math.sin(rot)
    for i in range(n):
        th = 2 * math.pi * i / n
        k = 1.0 + (wob(th) if wob else 0.0)
        x, y = rx * k * math.cos(th), ry * k * math.sin(th)
        out.append((cx + x * cr - y * sr, cy + x * sr + y * cr))
    return out


def lerp(a, b, t):
    return a + (b - a) * t


def mix(c1, c2, t):
    """Mix two #rrggbb colours."""
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(lerp(x, y, t)):02x}" for x, y in zip(a, b))


class Art:
    """One SVG document with namespaced defs."""

    def __init__(self, sid, seed=1):
        self.id = sid
        self.defs = []
        self.rng = random.Random(seed)
        self.n = 0

    def j(self, a=1.0):
        return self.rng.uniform(-a, a)

    def jit(self, pts, a=0.8):
        return [(x + self.j(a), y + self.j(a)) for x, y in pts]

    def uid(self, name):
        self.n += 1
        return f"{self.id}-{name}{self.n}"

    def radial(self, name, stops, cx="38%", cy="30%", r="75%", fx=None, fy=None, user=None):
        i = self.uid(name)
        st = "".join(f'<stop offset="{o}" stop-color="{c}"' + (f' stop-opacity="{op}"' if op is not None else "") + "/>"
                     for o, c, op in [(s + (None,))[:3] for s in stops])
        foc = (f' fx="{fx}" fy="{fy}"' if fx is not None else "")
        if user:
            ucx, ucy, ur = user
            self.defs.append(f'<radialGradient id="{i}" gradientUnits="userSpaceOnUse" cx="{f(ucx)}" cy="{f(ucy)}" r="{f(ur)}">{st}</radialGradient>')
        else:
            self.defs.append(f'<radialGradient id="{i}" cx="{cx}" cy="{cy}" r="{r}"{foc}>{st}</radialGradient>')
        return f"url(#{i})"

    def linear(self, name, stops, x1, y1, x2, y2, user=True):
        i = self.uid(name)
        st = "".join(f'<stop offset="{o}" stop-color="{c}"' + (f' stop-opacity="{op}"' if op is not None else "") + "/>"
                     for o, c, op in [(s + (None,))[:3] for s in stops])
        units = ' gradientUnits="userSpaceOnUse"' if user else ""
        self.defs.append(f'<linearGradient id="{i}"{units} x1="{f(x1)}" y1="{f(y1)}" x2="{f(x2)}" y2="{f(y2)}">{st}</linearGradient>')
        return f"url(#{i})"

    def clip(self, name, d):
        i = self.uid(name)
        self.defs.append(f'<clipPath id="{i}"><path d="{d}"/></clipPath>')
        return f"url(#{i})"

    def pattern(self, name, w, h, body, transform=""):
        i = self.uid(name)
        tr = f' patternTransform="{transform}"' if transform else ""
        self.defs.append(f'<pattern id="{i}" patternUnits="userSpaceOnUse" width="{f(w)}" height="{f(h)}"{tr}>{body}</pattern>')
        return f"url(#{i})"

    def blur(self, name, sd):
        i = self.uid(name)
        self.defs.append(f'<filter id="{i}" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="{sd}"/></filter>')
        return f"url(#{i})"

    # ------------------------------------------------------------ volume recipe
    def shape(self, d, base, light, dark, top, bottom, sw=3.0, hi=True, hi_box=None, shade=True, ink=INK,
              extra_inside=""):
        """Gouache volume: vertical gradient (top-lit), clipped highlight + lower cool shadow, ink outline.
        top/bottom: y-extent of the shape for the gradient."""
        g = self.linear("v", [(0, light), (.45, base), (1, dark)], 0, top, 0, bottom)
        out = f'<path d="{d}" fill="{g}"/>'
        inside = extra_inside
        if hi and hi_box:
            x, y, rx, ry = hi_box
            inside += f'<ellipse cx="{f(x)}" cy="{f(y)}" rx="{f(rx)}" ry="{f(ry)}" fill="#fff" opacity=".22"/>'
        if shade:
            inside += f'<path d="{d}" fill="none" stroke="{dark}" stroke-width="{f(sw * 3.2)}" opacity=".35" transform="translate(0 {f(sw * 1.4)})"/>'
        if inside:
            c = self.clip("c", d)
            out += f'<g clip-path="{c}">{inside}</g>'
        if sw:
            out += f'<path d="{d}" fill="none" stroke="{ink}" stroke-width="{f(sw)}" stroke-linejoin="round"/>'
        return out


def grp(cls, inner, pivot=None, extra=""):
    pv = f' data-pivot="{f(pivot[0])} {f(pivot[1])}"' if pivot else ""
    return f'<g class="{cls}"{pv}{extra}>{inner}</g>'


# ------------------------------------------------------------------ faces

def eye(x, y, r, look=(0.28, 0.05), ink=INK, white=True, sw=None):
    """Friendly round eye looking slightly forward (right): white sclera, big dark pupil, two highlights."""
    sw = sw if sw is not None else max(1.2, r * 0.22)
    out = ""
    if white:
        out += f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(r)}" fill="#fff" stroke="{ink}" stroke-width="{f(sw)}"/>'
        pr = r * 0.66
        px, py = x + look[0] * r, y + look[1] * r
    else:
        pr = r
        px, py = x, y
    out += f'<circle cx="{f(px)}" cy="{f(py)}" r="{f(pr)}" fill="{ink}"/>'
    out += f'<circle cx="{f(px + pr * .32)}" cy="{f(py - pr * .38)}" r="{f(pr * .36)}" fill="#fff"/>'
    out += f'<circle cx="{f(px - pr * .35)}" cy="{f(py + pr * .38)}" r="{f(pr * .15)}" fill="#fff" opacity=".9"/>'
    return out


def lid(x, y, r, skin, ink=INK, sw=None):
    """Closed eye for g.lids: skin disc over the eye + a happy closed-lash curve."""
    sw = sw if sw is not None else max(1.4, r * 0.24)
    rr = r + sw * 0.6
    return (f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(rr)}" fill="{skin}"/>'
            f'<path d="M{f(x - r * .85)} {f(y + r * .05)}Q{f(x)} {f(y + r * .75)} {f(x + r * .85)} {f(y + r * .05)}" '
            f'fill="none" stroke="{ink}" stroke-width="{f(sw)}" stroke-linecap="round"/>')


def smile(x, y, w, ink=INK, sw=2.2, depth=None, open_=False, tilt=0.0):
    depth = depth if depth is not None else w * 0.45
    x0, x1 = x - w / 2, x + w / 2
    y0, y1 = y - tilt * w / 2, y + tilt * w / 2
    if open_:
        return (f'<path d="M{f(x0)} {f(y0)}Q{f(x)} {f(y + depth * 1.6)} {f(x1)} {f(y1)}Q{f(x)} {f(y + depth * .35)} {f(x0)} {f(y0)}Z" '
                f'fill="#8a2f3c" stroke="{ink}" stroke-width="{f(sw)}" stroke-linejoin="round"/>')
    return (f'<path d="M{f(x0)} {f(y0)}Q{f(x)} {f(y + depth)} {f(x1)} {f(y1)}" fill="none" stroke="{ink}" '
            f'stroke-width="{f(sw)}" stroke-linecap="round"/>')


def blush(x, y, rx, ry=None, op=.5):
    ry = ry if ry is not None else rx * .6
    return f'<ellipse cx="{f(x)}" cy="{f(y)}" rx="{f(rx)}" ry="{f(ry)}" fill="{BLUSH}" opacity="{op}"/>'


def creature_svg(cid, title, w, h, defs, body, anchors, span, motion, floor=None, root_cls="creature", extra_root="",
                 body_pivot=None):
    fl = f' data-floor="{f(floor)}"' if floor is not None else ""
    bp = body_pivot or (w / 2, h / 2)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" class="{root_cls}" data-id="{cid}" viewBox="0 0 {f(w)} {f(h)}" '
            f'data-span="{f(span[0])} {f(span[1])}" data-motion="{motion}"{fl}{extra_root} role="img" aria-label="{title}">'
            f'<title>{title}</title><defs>{"".join(defs)}</defs>'
            f'<g class="body" data-pivot="{f(bp[0])} {f(bp[1])}">{body}</g>'
            f'<g class="anchors" fill="none" stroke="none">{anchors}</g></svg>\n')


def anchors(looks, center):
    out = "".join(f'<circle class="anchor" data-look="{i}" cx="{f(x)}" cy="{f(y)}" r="4"/>' for i, (x, y) in enumerate(looks))
    out += f'<circle class="anchor-center" cx="{f(center[0])}" cy="{f(center[1])}" r="4"/>'
    return out
