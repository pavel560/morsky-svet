#!/usr/bin/env python3
"""Mořský svět — comps + contact sheet (designer sight loop).

Each comp is a static HTML page in design/comps/ that composes the real art exactly the way the
engine should (DESIGN.md §6.4): water gradient from tokens, screen-anchored far/mid/near tiles with
parallax offsets, floor tiles stitched by data-in/data-out, creatures in world space, darkness
overlay with glow clones in the deep, HUD from tokens + ui-icons.svg. Then headless Chrome shoots
it at 1024 x 768 @2x -> design/comp-*.png.

Run:  python3 design/build_comps.py [names…]
"""
import json
import os
import re
import sys

from shoot import shoot

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
ART = os.path.join(ROOT, "art")
PON = os.path.join(ART, "ponor")
OUT = os.path.join(HERE, "comps")

SPECIES = {s["id"]: s for s in json.load(open(os.path.join(ROOT, "data", "species.json")))} \
    if os.path.exists(os.path.join(ROOT, "data", "species.json")) else {}
ZONES = {z["id"]: z for z in json.load(open(os.path.join(ROOT, "data", "zones.json")))} \
    if os.path.exists(os.path.join(ROOT, "data", "zones.json")) else {}

ZONE_ORDER = ["utes", "chaluhy", "sire-more", "hlubiny"]
GROUP_WORD = {"ryba": "Ryba", "savec": "Savec — dýchá vzduch jako my", "plaz": "Plaz", "korys": "Korýš",
              "mekkys": "Měkkýš", "ostnokozec": "Ostnokožec", "zahavec": "Žahavec"}
EATS_WORD = {"plankton": "plankton", "algae": "řasy", "fish": "rybky", "shellfish": "mušle a krabíky", "jellyfish": "medúzy",
             "squid": "olihně", "seagrass": "mořskou trávu", "krill": "krill", "mixed": "trošku od všeho"}


def read(path):
    return open(path).read()


def svg_meta(text):
    vb = [float(v) for v in re.search(r'viewBox="([^"]+)"', text).group(1).split()]
    looks = [(float(x), float(y)) for _, x, y in sorted(
        (int(m.group(1)), m.group(2), m.group(3)) for m in re.finditer(r'class="anchor" data-look="(\d)" cx="([\d.\-]+)" cy="([\d.\-]+)"', text))]
    span = re.search(r'data-span="([\d.\-]+) ([\d.\-]+)"', text)
    attrs = dict(re.findall(r'data-([a-z\-]+)="([^"]*)"', text.split(">", 1)[0]))
    return vb, looks, (tuple(float(v) for v in span.groups()) if span else None), attrs


def inl(path, cls="", style=""):
    t = read(path)
    t = re.sub(r'<\?xml[^>]*>', '', t)
    t = t.replace("<svg ", f'<svg {"style=" + chr(34) + style + chr(34) + " " if style else ""}', 1)
    if cls:
        t = re.sub(r'class="([^"]*)"', lambda m: f'class="{m.group(1)} {cls}"', t, count=1)
    return t


def creature(cid, cx, cy, w, cls="", flip=False, anchor="center", z=10, extra_style=""):
    """Place a creature by screen centre (or by its data-floor line when anchor='floor')."""
    path = os.path.join(ART, f"{cid}.svg") if cid != "guide-turtle" else os.path.join(ART, "guide-turtle.svg")
    t = read(path)
    vb, _, _, attrs = svg_meta(t)
    h = w * vb[3] / vb[2]
    left = cx - w / 2
    top = cy - h / 2
    if anchor == "floor" and "floor" in attrs:
        top = cy - h * float(attrs["floor"]) / vb[3]
    tr = "transform:scaleX(-1);" if flip else ""
    return f'<div class="obj {cls}" style="left:{left:.0f}px;top:{top:.0f}px;width:{w:.0f}px;height:{h:.0f}px;z-index:{z};{tr}{extra_style}">{inl(path)}</div>'


def head(title, extra_css=""):
    return f"""<!doctype html><html lang="cs"><head><meta charset="utf-8"><title>{title}</title>
<link rel="stylesheet" href="../tokens.css"><link rel="stylesheet" href="../../css/fonts.css">
<style>
html,body{{margin:0;width:100%;height:100%;overflow:hidden;background:var(--hlubiny-low)}}
#stage{{position:relative;width:100vw;height:100vh;overflow:hidden;font-family:var(--font-text);color:var(--ink)}}
.obj,.layer,.tile{{position:absolute}} .obj>svg,.layer>svg,.tile>svg{{width:100%;height:100%;display:block;overflow:visible}}
.layer{{top:0;height:100%}} .tile{{}}
.btn{{position:absolute;display:grid;place-items:center;border-radius:50%;background:var(--paper);border:var(--stroke-ink) solid var(--ink);
  box-shadow:var(--shadow-paper);color:var(--ink);z-index:var(--z-ui);box-sizing:border-box}}
.btn>svg{{width:46%;height:46%}} .btn.m{{width:var(--touch-min);height:var(--touch-min)}}
.btn.main{{width:var(--touch-main);height:var(--touch-main);background:var(--primary);border-color:var(--primary-ink);box-shadow:0 4px 0 var(--primary-edge),0 10px 20px rgb(10 30 60 / .25)}}
.btn.hero{{width:var(--touch-hero);height:var(--touch-hero);background:var(--primary);box-shadow:0 5px 0 var(--primary-edge),0 14px 26px rgb(10 30 60 / .3)}}
.btn .lbl{{position:absolute;top:100%;margin-top:6px;font:var(--fw-display) var(--fs-small)/1 var(--font-display);color:var(--on-color);
  text-shadow:0 2px 0 var(--ink),0 0 6px var(--ink);white-space:nowrap}}
.pill{{position:absolute;background:var(--paper);border:var(--stroke-ink) solid var(--ink);border-radius:var(--r-pill);box-shadow:var(--shadow-paper);z-index:var(--z-ui)}}
.silhouette svg{{filter:brightness(0);opacity:.55}}
.glowclone svg *{{visibility:hidden}} .glowclone svg .glow,.glowclone svg .glow *{{visibility:visible}}
.lamp-on .lamp{{opacity:1}} .near-fade .near-item:nth-of-type(2){{opacity:.4}} .near-fade-utes .near-item:not(.sway){{opacity:.4}}
{extra_css}
</style></head><body>{read(os.path.join(ART, "ui-icons.svg"))}<div id="stage">"""


FOOT = "</div></body></html>"


def icon(i, extra=""):
    return f'<svg {extra}><use href="#{i}"/></svg>'


# ================================================================== Ponor
def water(zone):
    z = {"utes": "utes", "chaluhy": "chaluhy", "sire-more": "sire", "hlubiny": "hlubiny"}[zone]
    return f'<div class="layer" style="left:0;width:100%;z-index:var(--z-water);background:linear-gradient(var(--{z}-top),var(--{z}-mid) 55%,var(--{z}-low))"></div>'


def layer_tiles(zone, kind, camx, k, z, opacity=1.0, cls=""):
    """Screen-anchored tile row: height 100vh (768 at the comp size), width 2048/768*vh, offset = -camx*k mod W."""
    path = os.path.join(PON, f"{zone}-{kind}.svg")
    W = 2048
    off = -(camx * k) % W
    out = ""
    for i in (-1, 0, 1):
        out += f'<div class="layer {cls}" style="left:{off - W + i * W + W:.0f}px;width:{W}px;z-index:{z};opacity:{opacity}">{inl(path)}</div>'
    return out


def floor_chain(tiles, camx, camy, x0=0, top0=0):
    """Stitch floor tiles: next.top = prev.top + prev.out - next.in; x advances by 2048."""
    out = ""
    x, top = x0, top0
    tops = []
    for name in tiles:
        t = read(os.path.join(PON, name))
        _, _, _, attrs = svg_meta(t)
        vb = [float(v) for v in re.search(r'viewBox="([^"]+)"', t).group(1).split()]
        if tops:
            top = top + prev_out - float(attrs["in"])
        tops.append((x, top, attrs, vb))
        out += f'<div class="tile" style="left:{x - camx:.0f}px;top:{top - camy:.0f}px;width:{vb[2]:.0f}px;height:{vb[3]:.0f}px;z-index:var(--z-floor)">{inl(os.path.join(PON, name))}</div>'
        prev_out = float(attrs["out"])
        x += 2048
    return out, tops


def floor_y_world(tops, wx):
    for x, top, attrs, vb in tops:
        if x <= wx < x + 2048:
            ys = [float(v) for v in attrs["floor-y"].split(",")]
            i = int((wx - x) // 128)
            t = ((wx - x) - i * 128) / 128
            return top + ys[i] + (ys[min(i + 1, len(ys) - 1)] - ys[i]) * t
    return None


def hud(zone, chips, found, depth_frac, depth_label, caption, net=0, deep=False, swim_label="Plav dál"):
    out = f'<div class="btn m" style="left:16px;top:16px">{icon("i-home")}</div>'
    out += f'<div class="btn main" style="right:16px;top:12px">{icon("i-speaker")}</div>'
    # silhouette bar
    n = len(chips)
    bw = 64 + n * 72 + 16
    out += f'<div class="pill" style="left:calc(50% - {bw / 2}px);top:14px;height:76px;width:{bw}px;display:flex;align-items:center;gap:8px;padding:0 12px;box-sizing:border-box">'
    out += f'<div style="width:48px;height:48px;border-radius:50%;background:var(--zone-{zone});display:grid;place-items:center;color:var(--on-color);flex:none">{icon("i-zone-" + zone, "style=width:32px;height:32px")}</div>'
    for cid in chips:
        on = cid in found
        ring = "box-shadow:var(--halo-found);" if on else ""
        out += (f'<div class="{"" if on else "silhouette"}" style="width:64px;height:64px;border-radius:50%;background:var(--paper-deep);display:grid;place-items:center;flex:none;{ring}">'
                f'<div style="width:52px;height:52px">{inl(os.path.join(ART, cid + ".svg"), style="width:100%;height:100%")}</div></div>')
    out += "</div>"
    # depth gauge
    top, bot = 112, 600
    bands = "".join(f'<div style="flex:1;background:var(--zone-{z});{"border-radius:var(--r-pill) var(--r-pill) 0 0;" if i == 0 else ""}{"border-radius:0 0 var(--r-pill) var(--r-pill);" if i == 3 else ""}"></div>'
                    for i, z in enumerate(ZONE_ORDER))
    out += (f'<div style="position:absolute;left:24px;top:{top}px;height:{bot - top}px;width:20px;display:flex;flex-direction:column;border:var(--stroke-ink) solid var(--ink);'
            f'border-radius:var(--r-pill);overflow:hidden;z-index:var(--z-ui);box-shadow:var(--shadow-paper)">{bands}</div>')
    my = top + (bot - top) * depth_frac
    out += (f'<div style="position:absolute;left:14px;top:{my - 20:.0f}px;width:40px;height:40px;border-radius:50%;background:var(--paper);border:var(--stroke-ink) solid var(--ink);'
            f'z-index:var(--z-ui);display:grid;place-items:center;color:var(--ink)">{icon("i-level-1", "style=width:26px;height:26px")}</div>'
            f'<div class="pill" style="left:60px;top:{my - 17:.0f}px;padding:4px 12px;font:var(--fw-display) var(--fs-small)/1.2 var(--font-display);border-width:2px">{depth_label}</div>')
    # bottom controls
    out += f'<div class="btn m" style="left:16px;bottom:20px">{icon("i-back")}</div>'
    out += (f'<div class="btn m" style="left:96px;bottom:20px;background:var(--paper)">{icon("i-net")}'
            f'<div style="position:absolute;right:-8px;top:-8px;min-width:30px;height:30px;border-radius:15px;background:var(--good);color:var(--on-color);'
            f'font:var(--fw-display) 18px/30px var(--font-display);text-align:center;border:2px solid var(--ink)">{net}</div></div>')
    out += f'<div class="btn main" style="right:28px;bottom:36px;width:104px;height:104px">{icon("i-swim-on", "style=width:58%;height:58%")}<span class="lbl">{swim_label}</span></div>'
    return out


def bubble(x, y, text, tail="left", deep=False):
    bg = "var(--paper)"
    return (f'<div style="position:absolute;left:{x}px;top:{y}px;max-width:330px;background:{bg};border:var(--stroke-ink) solid var(--ink);border-radius:var(--r-md);'
            f'padding:10px 16px 10px 52px;font:var(--fw-text-bold) var(--fs-body)/var(--lh-text) var(--font-text);box-shadow:var(--shadow-lift);z-index:var(--z-ui)">'
            f'<span style="position:absolute;left:12px;top:12px;width:30px;height:30px;color:var(--ink-soft)">{icon("i-speaker", "style=width:100%;height:100%")}</span>{text}'
            f'<span style="position:absolute;{tail}:28px;bottom:-14px;width:22px;height:22px;background:{bg};border-right:var(--stroke-ink) solid var(--ink);'
            f'border-bottom:var(--stroke-ink) solid var(--ink);transform:rotate(45deg)"></span></div>')


def diver_el(x, y, w=270, lamp=False, flip=False, tilt=-4):
    t = inl(os.path.join(ART, "diver.svg"))
    cls = "lamp-on" if lamp else ""
    h = w / 2
    return f'<div class="obj {cls}" style="left:{x - w / 2:.0f}px;top:{y - h / 2:.0f}px;width:{w}px;height:{h:.0f}px;z-index:var(--z-chars);transform:rotate({tilt}deg)">{t}</div>'


def particles(kind, n, seed, region=(0, 0, 1024, 768), size=(8, 18), op=.8, z=11):
    import random
    rng = random.Random(seed)
    path = os.path.join(PON, f"{kind}.svg")
    t = inl(path)
    out = ""
    for _ in range(n):
        s = rng.uniform(*size)
        x, y = rng.uniform(region[0], region[2]), rng.uniform(region[1], region[3])
        out += f'<div class="obj" style="left:{x:.0f}px;top:{y:.0f}px;width:{s:.0f}px;height:{s:.0f}px;opacity:{op};z-index:{z}">{t}</div>'
    return out


def bubbles_from(x, y, seed=1):
    import random
    rng = random.Random(seed)
    t = inl(os.path.join(PON, "bubble.svg"))
    out = ""
    for k in range(6):
        s = 10 + k * 2.4
        out += f'<div class="obj" style="left:{x + rng.uniform(-6, 10) + k * 3:.0f}px;top:{y - k * 30:.0f}px;width:{s:.0f}px;height:{s:.0f}px;z-index:11">{t}</div>'
    return out


def ponor_utes():
    camx, camy = 520, -50
    html = head("Ponor — útes")
    html += water("utes")
    html += f'<div class="layer" style="left:0;width:100%;z-index:1;opacity:.9">{inl(os.path.join(PON, "rays.svg"))}</div>'
    html += layer_tiles("utes", "far", camx, .25, 1)
    html += layer_tiles("utes", "mid", camx, .55, 2)
    surf = inl(os.path.join(PON, "surface-under.svg"))
    html += f'<div class="tile" style="left:{-camx % 2048 - 2048}px;top:{-110 - camy}px;width:2048px;height:220px;z-index:2">{surf}</div>'
    html += f'<div class="tile" style="left:{-camx % 2048}px;top:{-110 - camy}px;width:2048px;height:220px;z-index:2">{surf}</div>'
    fl, tops = floor_chain(["utes-floor.svg", "utes-floor.svg"], camx, camy)
    html += fl
    html += ('<div class="layer" style="left:0;width:100%;z-index:4;opacity:.13;background:url(../../art/ponor/caustics.svg) 0 0/300px 300px;'
             'mask-image:linear-gradient(transparent 62%,#000 82%);-webkit-mask-image:linear-gradient(transparent 62%,#000 82%)"></div>')
    fy = lambda wx: floor_y_world(tops, wx) - camy
    # cleanup patch: still dull, with a bottle lying in front of it
    px = 1250
    html += f'<div class="obj" style="left:{px - camx - 160:.0f}px;top:{fy(px) - 172:.0f}px;width:320px;height:185px;z-index:5">{inl(os.path.join(PON, "patch-utes.svg"))}</div>'
    html += f'<div class="obj" style="left:{px - camx - 30:.0f}px;top:{fy(px) - 46:.0f}px;width:86px;height:120px;z-index:9;transform:rotate(8deg)">{inl(os.path.join(ART, "trash-lahev.svg"))}</div>'
    html += creature("sasanka", 1100 - camx, fy(1100) + 6, 150, anchor="floor", z=6)
    html += creature("klaun", 1185 - camx, fy(1100) - 150, 104, z=7)
    html += creature("krab", 860 - camx, fy(860) + 34, 108, anchor="floor", z=8)
    html += creature("hvezdice", 780 - camx, fy(780) + 50, 120, anchor="floor", z=8)
    html += creature("konik", 1000 - camx, fy(1000) - 120, 66, z=8)
    html += creature("papousek", 1300 - camx, 260, 150, z=7)
    html += diver_el(450, 410, 280)
    html += bubbles_from(550, 380, 3)
    html += creature("guide-turtle", 200, 470, 150, z=9)
    html += layer_tiles("utes", "near", camx, 1.25, "var(--z-near)", cls="near-fade-utes")
    html += bubble(128, 190, "Korály potřebují světlo, proto rostou blízko hladiny.", tail="left")
    html += hud("utes", ["klaun", "konik", "hvezdice", "krab", "chobotnice"], {"klaun", "konik"}, .1, "8 m",
                "", net=0)
    return html + FOOT


def ponor_chaluhy():
    camx, camy = 600, 380
    html = head("Ponor — chaluhy")
    html += water("chaluhy")
    html += f'<div class="layer" style="left:0;width:100%;z-index:1;opacity:.6">{inl(os.path.join(PON, "rays.svg"))}</div>'
    html += layer_tiles("chaluhy", "far", camx, .25, 1)
    html += layer_tiles("chaluhy", "mid", camx, .55, 2)
    fl, tops = floor_chain(["utes-floor.svg", "trans-utes-chaluhy.svg", "chaluhy-floor.svg"], camx - 4096 + 0, camy, x0=-4096 + 4096)
    # place so that chaluhy-floor starts at world 4096 and the camera looks at it
    fl, tops = floor_chain(["utes-floor.svg", "trans-utes-chaluhy.svg", "chaluhy-floor.svg"], camx + 4096, camy)
    html += fl

    fy = lambda wx: floor_y_world(tops, wx + 4096) - camy
    html += creature("jezovka", 1190 - camx, fy(1190) + 20, 92, anchor="floor", z=8)
    html += creature("tulen", 1330 - camx, 300, 250, z=7, flip=True)
    html += creature("meduza", 1010 - camx, 150, 112, z=8)
    html += f'<div class="obj" style="left:{1300 - camx}px;top:{fy(1300) - 150:.0f}px;width:100px;height:120px;z-index:9;transform:rotate(-10deg)">{inl(os.path.join(ART, "trash-sacek.svg"))}</div>'
    html += diver_el(420, 400, 280, tilt=6)
    html += bubbles_from(520, 375, 5)
    html += creature("guide-turtle", 180, 470, 150, z=9)
    html += layer_tiles("chaluhy", "near", camx, 1.25, "var(--z-near)", cls="near-fade")
    html += bubble(128, 236, "Chaluhy rostou ze dna k hladině jako stromy v lese.", tail="left")
    html += hud("chaluhy", ["vydra", "tulen", "jezovka", "meduza"], {"meduza"}, .36, "25 m", "", net=1)
    return html + FOOT


def ponor_sire():
    camx, camy = 300, 300
    html = head("Ponor — širé moře")
    html += water("sire-more")
    html += f'<div class="layer" style="left:0;width:100%;z-index:1;opacity:.55">{inl(os.path.join(PON, "rays.svg"))}</div>'
    html += layer_tiles("sire-more", "far", camx, .25, 1)
    html += layer_tiles("sire-more", "mid", camx, .55, 2)
    # far whale (creature art, pushed back: smaller + water haze)
    html += creature("keporkak", 640, 190, 560, z=2, extra_style="opacity:.55;filter:saturate(.6)")
    html += creature("zralok", 740, 560, 380, z=7)
    html += creature("manta", 860, 330, 230, z=8)
    import random
    rng = random.Random(4)
    for k in range(14):
        x, y = 150 + k * 9 + rng.uniform(-30, 30), 160 + (k % 5) * 22 + rng.uniform(-8, 8)
        html += f'<div class="obj" style="left:{x + 380:.0f}px;top:{y + 300:.0f}px;width:46px;height:21px;z-index:6;opacity:.95">{inl(os.path.join(PON, "school-fish.svg"))}</div>'
    html += diver_el(360, 360, 280, tilt=-2)
    html += bubbles_from(460, 335, 7)
    html += creature("guide-turtle", 150, 470, 150, z=9)
    html += layer_tiles("sire-more", "near", camx, 1.25, "var(--z-near)")
    html += bubble(110, 540, "Tady už není vidět dno. Jen modrá voda!", tail="left")
    html += hud("sire-more", ["delfin", "zelva", "keporkak", "zralok", "manta", "sardinky"], {"zelva", "keporkak", "zralok"}, .62, "120 m", "", net=2)
    return html + FOOT


def ponor_hlubiny():
    camx, camy = 700, 160
    html = head("Ponor — hlubiny")
    html += water("hlubiny")
    html += layer_tiles("hlubiny", "far", camx, .25, 1)
    html += layer_tiles("hlubiny", "mid", camx, .55, 2)
    fl, tops = floor_chain(["hlubiny-floor.svg", "hlubiny-floor.svg"], camx, camy)
    html += fl
    fy = lambda wx: floor_y_world(tops, wx) - camy
    dx, dyy = 420, 330
    world = ""
    world += creature("dumbo", 640, 300, 120, z=8)
    world += creature("das", 900, 470, 150, z=8)
    world += creature("svetluska", 210, 170, 110, z=8)
    html += world
    html += f'<div class="obj" style="left:{1250 - camx}px;top:{fy(1250) - 62:.0f}px;width:150px;height:118px;z-index:9">{inl(os.path.join(ART, "trash-sit.svg"))}</div>'
    html += diver_el(dx, dyy, 280, lamp=True, tilt=-2)
    html += bubbles_from(dx + 100, dyy - 25, 9)
    html += creature("guide-turtle", 300, 430, 150, z=9)
    html += particles("snow", 46, 11, size=(10, 22), op=.75, z=12)
    html += layer_tiles("hlubiny", "near", camx, 1.25, "var(--z-near)")
    # darkness with a warm lamp circle around the diver (radial gradient centred on anchor-lamp)
    lx, ly = dx + 270 * (376 - 240) / 480, dyy + 135 * (66 - 120) / 240
    html += (f'<div class="layer" style="left:0;width:100%;z-index:var(--z-dark);background:radial-gradient(circle at {lx + 60:.0f}px {ly + 30:.0f}px,'
             f'transparent 0,transparent calc(var(--lamp-radius) * .55),var(--deep-dim) var(--lamp-radius))"></div>')
    # glow clones above the darkness (far/mid glows, floor glows, creature glows, the lamp)
    html += layer_tiles("hlubiny", "far", camx, .25, 15, opacity=1)
    html += f'<div class="glowclone" style="position:absolute;inset:0;z-index:15">{layer_tiles("hlubiny", "mid", camx, .55, 15) + fl.replace("z-index:var(--z-floor)", "z-index:15")}</div>'
    html += f'<div class="glowclone" style="position:absolute;inset:0;z-index:16">{world}</div>'
    html += bubble(130, 560, "Čím hlouběji, tím je větší tma a zima.", tail="left")
    html += hud("hlubiny", ["das", "dumbo", "svetluska"], {"svetluska"}, .88, "1000 m", "", net=3)
    return html + FOOT


# ================================================================== home
def home():
    html = head("Úvod — Loďka", ".door{position:absolute;display:flex;flex-direction:column;align-items:center;gap:6px;z-index:var(--z-ui)}"
                ".door .btn{position:relative} .door b{font:var(--fw-display) var(--fs-label)/1 var(--font-display);color:var(--on-color);text-shadow:0 2px 0 var(--ink),0 0 8px rgb(20 40 60 / .6)}")
    html += f'<div class="layer" style="left:0;width:100%;z-index:0">{inl(os.path.join(ART, "home.svg"))}</div>'
    # turtle peeking at the waterline (home.svg data-turtle, mapped through the slice: 1600x1000 -> 1229x768, x offset -102)
    html += creature("guide-turtle", 1010 * .768 - 102 + 70, 470 * .768 + 14, 140, z=5)
    html += ('<div style="position:absolute;left:36px;top:28px;z-index:var(--z-ui);font:var(--fw-display) var(--fs-hero)/var(--lh-tight) var(--font-display);'
             'color:var(--paper);text-shadow:0 3px 0 var(--ink),0 0 14px rgb(30 60 90 / .45);letter-spacing:.01em">Mořský svět</div>')
    html += f'<div class="btn m" style="right:16px;top:16px;color:var(--ink-soft)">{icon("i-parents")}</div>'
    html += f'<div class="btn main" style="right:96px;top:12px">{icon("i-speaker")}</div>'
    # hero action (left-centre, under the boat)
    html += (f'<div style="position:absolute;left:96px;top:470px;z-index:var(--z-ui);display:flex;align-items:center;gap:16px;'
             f'background:var(--primary);border:var(--stroke-ink-heavy) solid var(--ink);border-radius:var(--r-pill);padding:12px 34px 12px 14px;'
             f'box-shadow:0 5px 0 var(--primary-edge),0 16px 30px rgb(10 30 60 / .35)">'
             f'<span style="width:var(--touch-main);height:var(--touch-main);border-radius:50%;background:var(--paper);border:var(--stroke-ink) solid var(--ink);display:grid;place-items:center">'
             f'{icon("i-down", "style=width:56%;height:56%")}</span><b style="font:var(--fw-display) var(--fs-title)/1 var(--font-display)">Ponořit se!</b></div>')
    # three doors: a right-hand column, paper label + coloured 88 px door
    doors = [("i-collection", "Můj kousek moře", "var(--zone-utes)"), ("i-quiz", "Kvíz", "var(--coral-violet)"), ("i-who-where", "Kdo kde bydlí?", "var(--zone-sire-more)")]
    for i, (ic, lbl, col) in enumerate(doors):
        y = 410 + i * 108
        html += (f'<div style="position:absolute;right:24px;top:{y}px;display:flex;align-items:center;gap:10px;z-index:var(--z-ui)">'
                 f'<span class="pill" style="position:relative;padding:8px 16px;font:var(--fw-display) var(--fs-label)/1 var(--font-display)">{lbl}</span>'
                 f'<div class="btn main" style="position:relative;background:{col};color:var(--on-color)">{icon(ic, "style=width:56%;height:56%")}</div></div>')
    html += (f'<div class="pill" style="left:24px;bottom:16px;padding:6px 16px 6px 10px;display:flex;align-items:center;gap:8px;font:var(--fw-text-bold) var(--fs-small)/1.2 var(--font-text);color:var(--ink-soft)">'
             f'{icon("i-parents", "style=width:26px;height:26px")}Pod vodu se potápíme jen s dospělým.</div>')
    return html + FOOT


# ================================================================== card
def card(cid):
    sp = SPECIES[cid]
    t = read(os.path.join(ART, f"{cid}.svg"))
    vb, looks, span, attrs = svg_meta(t)
    css = """
.veil{position:absolute;inset:0;background:var(--veil);z-index:30}
.card{position:absolute;left:24px;top:22px;right:24px;bottom:22px;background:var(--paper);border-radius:var(--r-lg);box-shadow:var(--shadow-lift);z-index:40;border:var(--stroke-ink) solid var(--ink)}
.pin{position:absolute;width:44px;height:44px;margin:-22px 0 0 -22px;border-radius:50%;background:var(--paper);border:var(--stroke-ink) solid var(--ink);
 font:var(--fw-display) 22px/38px var(--font-display);text-align:center;box-shadow:0 0 0 6px rgb(255 255 255 / .55);box-sizing:border-box}
.lf{display:flex;gap:12px;align-items:center;background:var(--paper-deep);border-radius:var(--r-md);padding:7px 14px;font:var(--fw-text) var(--fs-body)/1.25 var(--font-text)}
.lf i{flex:none;width:34px;height:34px;border-radius:50%;border:var(--stroke-ink) solid var(--ink);font:normal var(--fw-display) 18px/28px var(--font-display);text-align:center;background:var(--paper);box-sizing:border-box}
.chip{display:inline-flex;align-items:center;gap:8px;border-radius:var(--r-pill);padding:4px 14px 4px 4px;font:var(--fw-text-bold) var(--fs-small)/1.2 var(--font-text);background:var(--paper-deep)}
.chip .ic{width:40px;height:40px;border-radius:50%;display:grid;place-items:center;color:var(--on-color);flex:none}
.chip .ic svg{width:66%;height:66%}
"""
    zone = sp["zone"]
    zbg = {"utes": "utes", "chaluhy": "chaluhy", "sire-more": "sire", "hlubiny": "hlubiny"}[zone]
    html = head(f"Kartička — {sp['name']['cs']}", css)
    html += f'<div class="layer" style="left:0;width:100%;background:linear-gradient(var(--{zbg}-top),var(--{zbg}-low))"></div><div class="veil"></div><div class="card">'
    # creature + pins (left half)
    boxw, boxh = 430, 400
    bx, by = 20, 40
    s = min(boxw / vb[2], boxh / vb[3])
    w, h = vb[2] * s, vb[3] * s
    ox, oy = bx + (boxw - w) / 2, by + (boxh - h) / 2
    glow = a_glow = ""
    html += f'<div class="obj" style="left:{ox:.0f}px;top:{oy:.0f}px;width:{w:.0f}px;height:{h:.0f}px;filter:var(--shadow-char)">{inl(os.path.join(ART, cid + ".svg"))}</div>'
    for i, (x, y) in enumerate(looks):
        html += f'<div class="pin" style="left:{ox + x * s:.0f}px;top:{oy + y * s:.0f}px;z-index:2">{i + 1}</div>'
    # size bar (left column): diver 115 cm and the animal in ONE scale, fitted to the plot box by length AND height
    size = sp["sizeCm"]
    PW, PH, GAP = 380, 104, 22
    d_ratio, a_ratio = .5, vb[3] / vb[2]
    k = min((PW - GAP) / (115 + size), PH / (115 * d_ratio), PH / (size * a_ratio))
    dw, aw = 115 * k, size * k
    tiny = dw < 34
    diver_svg = inl(os.path.join(ART, "diver.svg"))
    cmp_icon = {"dlaň": "i-cmp-dlan", "kočk": "i-cmp-kocka", "postel": "i-cmp-postel", "auto": "i-cmp-auto", "autobus": "i-cmp-autobus", "dům": "i-cmp-dum"}
    say = sp["sizeSay"]["cs"]
    ic = next((v for k_, v in sorted(cmp_icon.items(), key=lambda kv: -len(kv[0])) if k_ in say.lower()), "i-size")
    html += (f'<div style="position:absolute;left:28px;top:446px;width:{PW + 24}px;height:192px;background:var(--paper-deep);border-radius:var(--r-md);padding:10px 12px;box-sizing:border-box">'
             f'<div style="display:flex;align-items:center;gap:8px;font:var(--fw-display) var(--fs-small)/1 var(--font-display);color:var(--ink-soft)">{icon("i-size", "style=width:26px;height:26px")}Velikost</div>'
             f'<div style="position:relative;height:{PH}px;margin-top:6px;border-bottom:3px solid var(--paper-edge)">'
             f'<div style="position:absolute;left:0;bottom:0;width:{dw:.0f}px;height:{dw * d_ratio:.0f}px">{diver_svg}</div>'
             + (f'<div style="position:absolute;left:{dw / 2 - 14:.0f}px;bottom:{dw * d_ratio / 2 - 14:.0f}px;width:28px;height:28px;border-radius:50%;border:3px solid var(--suit);box-sizing:border-box"></div>' if tiny else "")
             + f'<div style="position:absolute;left:{dw + GAP:.0f}px;bottom:0;width:{aw:.0f}px;height:{aw * a_ratio:.0f}px">{inl(os.path.join(ART, cid + ".svg"), style="width:100%;height:100%")}</div>'
             f'</div><div style="display:flex;align-items:center;gap:8px;margin-top:6px;font:var(--fw-text-bold) var(--fs-small)/1.2 var(--font-text)">'
             f'{icon(ic, "style=width:30px;height:30px;color:var(--ink-soft)")}{say}</div></div>')
    html += (f'<div style="position:absolute;left:28px;top:648px;width:{PW + 24}px;font:var(--fw-text) var(--fs-small)/1.3 var(--font-text);color:var(--ink-soft);'
             f'background:var(--paper-deep);border-radius:var(--r-md);padding:8px 12px;box-sizing:border-box">'
             f'<b style="font-family:var(--font-display);color:var(--ink)">Víš, že…?</b> {sp["fact"]["cs"]}</div>')
    # right column
    rx = 480
    name = sp["name"]["cs"]
    nfs = "var(--fs-hero)" if len(name) <= 11 else "var(--fs-title)"
    html += f'<div style="position:absolute;left:{rx}px;top:22px;right:28px;display:flex;flex-direction:column;gap:9px">'
    html += f'<div style="font:var(--fw-display) {nfs}/var(--lh-tight) var(--font-display)">{name}</div>'
    html += (f'<div style="display:flex;align-items:center;gap:10px;font:var(--fw-text) var(--fs-label)/1.1 var(--font-text);color:var(--ink-soft)">'
             f'{icon("i-flag-en", "style=width:30px;height:30px;flex:none")}<span>{sp["name"]["en"]}<i style="display:block;font-size:var(--fs-small)">{sp["latin"]}</i></span></div>')
    grp_ = sp["group"]
    html += '<div style="display:flex;flex-wrap:wrap;gap:8px">'
    html += f'<span class="chip"><span class="ic" style="background:var(--grp-{grp_})">{icon("i-grp-" + grp_)}</span>{GROUP_WORD[grp_]}</span>'
    zn = ZONES.get(zone, {}).get("name", {}).get("cs", zone)
    html += f'<span class="chip"><span class="ic" style="background:var(--zone-{zone})">{icon("i-zone-" + zone)}</span>{zn}</span>'
    html += f'<span class="chip"><span class="ic" style="background:var(--ink-soft)">{icon("i-eats-" + sp["eats"])}</span>Jím {EATS_WORD[sp["eats"]]}</span>'
    html += "</div>"
    if sp.get("touch", "look") != "look":
        html += (f'<div style="display:flex;align-items:center;gap:12px;background:var(--look-only-soft);border:var(--stroke-ink) solid var(--look-only);border-radius:var(--r-md);'
                 f'padding:6px 14px;color:var(--look-only-ink);font:var(--fw-text-bold) var(--fs-body)/1.2 var(--font-text)">'
                 f'<span style="flex:none;width:44px;height:44px;color:var(--look-only)">{icon("i-look-only", "style=width:100%;height:100%")}</span>'
                 f'{ {"sting": "Pozor, žahá — jen se díváme.", "spines": "Pozor, píchá — jen se díváme.", "pinch": "Pozor, štípe — jen se díváme."}[sp["touch"]]}</div>')
    else:
        html += (f'<div style="display:flex;align-items:center;gap:10px;color:var(--ink-soft);font:var(--fw-text) var(--fs-small)/1.2 var(--font-text)">'
                 f'{icon("i-eye", "style=width:26px;height:26px")}Na zvířátka nesaháme, jen se díváme.</div>')
    html += '<div style="font:var(--fw-display) var(--fs-small)/1 var(--font-display);color:var(--ink-soft);margin-top:2px">Poznáš mě podle…</div>'
    for i, lf in enumerate(sp["lookFor"]):
        html += f'<div class="lf"><i>{i + 1}</i>{lf["cs"]}</div>'
    html += "</div>"
    # buttons: bottom-right row (repeat 88, photo 88, close 64)
    html += (f'<div style="position:absolute;right:28px;bottom:20px;display:flex;align-items:center;gap:16px">'
             f'<div class="btn main" style="position:relative">{icon("i-speaker")}</div>'
             f'<div class="btn main" style="position:relative">{icon("i-photo")}</div>'
             f'<div class="btn m" style="position:relative">{icon("i-close")}</div></div>')
    html += "</div>"
    return html + FOOT


# ================================================================== Můj kousek moře
def my_sea(night=False):
    css = (".drawer{position:absolute;left:0;right:0;bottom:0;height:150px;background:var(--paper);border-top:var(--stroke-ink) solid var(--ink);"
           "border-radius:var(--r-lg) var(--r-lg) 0 0;box-shadow:0 -6px 20px rgb(10 30 60 / .2);z-index:var(--z-ui);display:flex;align-items:center;gap:12px;padding:0 24px;justify-content:center;box-sizing:border-box}"
           ".slot{flex:none;width:96px;height:96px;border-radius:var(--r-md);background:var(--paper-deep);display:grid;place-items:center}"
           ".slot>div{width:80px;height:80px}")
    html = head("Můj kousek moře", css)
    html += f'<div class="layer" style="left:0;width:100%">{inl(os.path.join(ART, "my-sea-night.svg" if night else "my-sea-day.svg"))}</div>'
    fy = 780 * .768
    if night:
        world = (creature("das", 640, 300, 140, z=8) + creature("svetluska", 330, 190, 110, z=8) + creature("dumbo", 860, 250, 120, z=8)
                 + creature("hvezdice", 520, fy + 18, 110, anchor="floor", z=8))
        html += world + '<div class="layer" style="left:0;width:100%;z-index:14;background:rgb(4 9 24 / .35)"></div>'
        html += f'<div class="glowclone" style="position:absolute;inset:0;z-index:15">{world}</div>'
    else:
        html += creature("sasanka", 860, fy + 8, 140, anchor="floor", z=7)
        html += creature("klaun", 760, 400, 100, z=8)
        html += creature("hvezdice", 520, fy + 18, 110, anchor="floor", z=8)
        html += creature("krab", 1000 - 60, fy + 20, 100, anchor="floor", z=8, flip=True)
        html += creature("meduza", 420, 170, 100, z=8)
        html += creature("konik", 640, 260, 70, z=8)
        html += creature("zelva", 250, 340, 190, z=8)
    html += f'<div class="btn m" style="left:16px;top:16px">{icon("i-home")}</div>'
    html += f'<div class="btn main" style="right:16px;top:12px">{icon("i-speaker")}</div>'
    html += (f'<div class="pill" style="right:120px;top:20px;display:flex;gap:6px;padding:6px">'
             f'<div style="width:64px;height:64px;border-radius:50%;display:grid;place-items:center;{"" if night else "background:var(--primary);"}">{icon("i-day", "style=width:60%;height:60%")}</div>'
             f'<div style="width:64px;height:64px;border-radius:50%;display:grid;place-items:center;{"background:var(--zone-hlubiny);color:var(--on-deep);" if night else ""}">{icon("i-night", "style=width:56%;height:56%")}</div></div>')
    html += '<div class="drawer">'
    order = ["delfin", "keporkak", "chobotnice", "vydra", "tulen", "zralok", "papousek", "manta"] if not night else ["chobotnice", "delfin", "keporkak", "vydra", "tulen", "zralok", "manta", "sardinky"]
    found = {"delfin", "chobotnice", "vydra", "keporkak"}
    for cid in order:
        cls = "" if cid in found else "silhouette"
        html += f'<div class="slot {cls}"><div>{inl(os.path.join(ART, cid + ".svg"), style="width:100%;height:100%")}</div></div>'
    html += "</div>"
    return html + FOOT


# ================================================================== Kvíz
def quiz():
    css = (".choice{position:absolute;top:330px;width:270px;height:270px;background:var(--paper);border:var(--stroke-ink) solid var(--ink);border-radius:var(--r-lg);"
           "box-shadow:var(--shadow-lift);display:grid;place-items:center;z-index:var(--z-ui)} .choice>div{width:220px;height:200px}")
    html = head("Kvíz — Kdo jsem?", css)
    html += water("utes") + f'<div class="layer" style="left:0;width:100%;z-index:1;opacity:.7">{inl(os.path.join(PON, "rays.svg"))}</div>'
    html += layer_tiles("utes", "far", 300, .25, 2, opacity=.8)
    html += f'<div class="btn m" style="left:16px;top:16px">{icon("i-home")}</div>'
    # progress: five bubbles (no score) — two done
    html += '<div class="pill" style="left:calc(50% - 150px);top:18px;width:300px;height:64px;display:flex;align-items:center;justify-content:center;gap:16px">'
    for k in range(5):
        st = "background:var(--good);border-color:var(--ink)" if k < 2 else ("background:var(--primary)" if k == 2 else "background:var(--paper-deep)")
        html += f'<span style="width:30px;height:30px;border-radius:50%;border:3px solid var(--ink);box-sizing:border-box;{st}"></span>'
    html += "</div>"
    html += creature("guide-turtle", 170, 210, 190, z=20)
    html += (f'<div style="position:absolute;left:290px;top:120px;width:520px;background:var(--paper);border:var(--stroke-ink) solid var(--ink);border-radius:var(--r-md);'
             f'padding:16px 20px;font:var(--fw-display) var(--fs-label)/1.2 var(--font-display);box-shadow:var(--shadow-lift);z-index:var(--z-ui)">'
             f'{SPECIES.get("chobotnice", {}).get("riddle", {}).get("cs", "Mám osm chapadel a umím měnit barvu.")}'
             f'<span style="position:absolute;left:-14px;top:40px;width:22px;height:22px;background:var(--paper);border-left:var(--stroke-ink) solid var(--ink);border-bottom:var(--stroke-ink) solid var(--ink);transform:rotate(45deg)"></span></div>')
    html += f'<div class="btn main" style="right:24px;top:122px">{icon("i-speaker")}</div>'
    for i, cid in enumerate(("hvezdice", "chobotnice", "krab")):
        html += f'<div class="choice" style="left:{62 + i * 310}px"><div>{inl(os.path.join(ART, cid + ".svg"), style="width:100%;height:100%")}</div></div>'
    return html + FOOT


# ================================================================== Kdo kde bydlí?
def who_where():
    html = head("Kdo kde bydlí?", ".slot{position:absolute;width:110px;height:110px;border-radius:var(--r-md);background:var(--paper);border:var(--stroke-ink) solid var(--ink);display:grid;place-items:center;box-shadow:var(--shadow-paper);z-index:var(--z-ui)} .slot>div{width:92px;height:92px}")
    html += f'<div class="layer" style="left:0;width:100%">{inl(os.path.join(ART, "cross-section.svg"))}</div>'
    html += f'<div class="btn m" style="left:16px;top:16px">{icon("i-home")}</div><div class="btn main" style="right:16px;top:12px">{icon("i-speaker")}</div>'
    bands = [("utes", 110, 330), ("chaluhy", 330, 540), ("sire-more", 540, 760), ("hlubiny", 760, 1000)]
    for z, y0, y1 in bands:
        y = (y0 + y1) / 2 * .768
        html += (f'<div style="position:absolute;left:{1024 - 220}px;top:{y - 28:.0f}px;display:flex;align-items:center;gap:8px;z-index:var(--z-ui);'
                 f'font:var(--fw-display) var(--fs-small)/1 var(--font-display);color:var(--on-color);text-shadow:0 2px 0 var(--ink)">'
                 f'<span style="width:56px;height:56px;border-radius:50%;background:var(--zone-{z});border:3px solid var(--paper);display:grid;place-items:center">{icon("i-zone-" + z, "style=width:64%;height:64%")}</span>'
                 f'{ZONES.get(z, {}).get("name", {}).get("cs", z)}</div>')
    html += creature("klaun", 470, 180, 90, z=8) + creature("das", 610, 680, 110, z=8)
    for i, cid in enumerate(("vydra", "keporkak", "dumbo", "hvezdice")):
        html += f'<div class="slot" style="left:{120 + i * 130}px;top:{646}px"><div>{inl(os.path.join(ART, cid + ".svg"), style="width:100%;height:100%")}</div></div>'
    return html + FOOT


# ================================================================== contact sheet
def contact_sheet():
    ids = list(SPECIES) or ["klaun"]
    ids += [x for x in ("kapustnak",) if x not in ids and os.path.exists(os.path.join(ART, x + ".svg"))]
    css = (".grid{position:absolute;inset:16px;display:grid;grid-template-columns:repeat(6,minmax(0,1fr));grid-template-rows:repeat(4,minmax(0,1fr));gap:10px}"
           ".cell{background:var(--paper);border:2px solid var(--paper-edge);border-radius:var(--r-md);position:relative;overflow:hidden}"
           ".cell .a{position:absolute;inset:8px 8px 46px} .cell .a svg{width:100%;height:100%}"
           ".cell b{position:absolute;left:8px;right:8px;bottom:6px;font:var(--fw-display) 15px/1.1 var(--font-display);text-align:center}"
           ".cell small{display:block;font:var(--fw-text) 11px/1.2 var(--font-text);color:var(--ink-soft)}"
           ".cell.deep{background:var(--hlubiny-mid);border-color:var(--hlubiny-top)} .cell.deep b{color:var(--on-deep)} .cell.deep small{color:var(--silhouette-deep)}"
           ".pinlayer .anchors circle{fill:var(--primary);stroke:var(--ink);stroke-width:2px} .anchors .anchor-center{fill:none!important;stroke:none!important}")
    html = head("Contact sheet", css).replace('<div id="stage">', '<div id="stage" style="background:var(--paper-deep)">')
    html += '<div class="grid pinlayer">'
    for cid in ids + ["diver", "guide-turtle"]:
        sp = SPECIES.get(cid, {})
        name = sp.get("name", {}).get("cs", {"diver": "Potápěčka", "guide-turtle": "Želvička (průvodkyně)", "kapustnak": "Kapustňák"}.get(cid, cid))
        deep = " deep" if sp.get("zone") == "hlubiny" else ""
        sub = f'{cid} · {sp.get("group", "")} · L{sp.get("level", "")}' if sp else cid
        html += f'<div class="cell{deep}"><div class="a">{inl(os.path.join(ART, cid + ".svg"))}</div><b>{name}<small>{sub}</small></b></div>'
    html += "</div>"
    return html + FOOT


COMPS = {
    "comp-home": home,
    "comp-ponor-utes": ponor_utes,
    "comp-ponor-chaluhy": ponor_chaluhy,
    "comp-ponor-sire-more": ponor_sire,
    "comp-ponor-hlubiny": ponor_hlubiny,
    "comp-card-meduza": lambda: card("meduza"),
    "comp-card-keporkak": lambda: card("keporkak"),
    "comp-my-sea-day": lambda: my_sea(False),
    "comp-my-sea-night": lambda: my_sea(True),
    "comp-quiz": quiz,
    "comp-kdo-kde-bydli": who_where,
    "contact-sheet": contact_sheet,
}

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    names = sys.argv[1:] or list(COMPS)
    for n in names:
        html = COMPS[n]()
        p = os.path.join(OUT, n + ".html")
        open(p, "w").write(html)
        if n == "contact-sheet":
            shoot(p, os.path.join(HERE, n + ".png"), 1280, 1000, 2)
        else:
            shoot(p, os.path.join(HERE, n + ".png"), 1024, 768, 2)
        print("shot", n)
