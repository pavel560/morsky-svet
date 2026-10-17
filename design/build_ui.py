#!/usr/bin/env python3
"""Mořský svět — UI icon sprite, app icon source and the full-screen scenes (designer source).

Run:  python3 design/build_ui.py
  art/ui-icons.svg        <symbol id="i-…" viewBox="0 0 48 48"> — line glyphs use currentColor; flags are coloured
  art/app-icon.svg        1024 x 1024 source for icons/ (programmer rasterises)
  art/home.svg            úvod „Loďka“ — 1600 x 1000, slice; safe area = centre 1024 x 768 (x 288–1312, y 116–884)
  art/my-sea-day.svg      Můj kousek moře — den    (1600 x 1000, data-floor-y)
  art/my-sea-night.svg    Můj kousek moře — noc
  art/cross-section.svg   Kdo kde bydlí? — řez mořem, g.band[data-zone] = drop targets
"""
import math
import os
import random
import re

from svgkit import INK, Art, f, grp, smooth, eye, lid, blush, mix, ellipse_pts
import build_sea as sea

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.join(HERE, "..", "art")

SW = 'stroke="currentColor" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"'
FILL = 'fill="currentColor"'
NONE = 'fill="none"'

ICONS = {
    # ---- navigation / actions
    "i-home": f'<path d="M7 23L24 8l17 15M12 20v19h9V29h6v10h9V20" {NONE} {SW}/>',
    "i-speaker": f'<path d="M8 19h7l10-8v26l-10-8H8z" {FILL} {SW}/><path d="M31 17q5 7 0 14M36 12q10 12 0 24" {NONE} {SW}/>',
    "i-repeat": f'<path d="M8 19h7l10-8v26l-10-8H8z" {FILL} {SW}/><path d="M31 17q5 7 0 14M36 12q10 12 0 24" {NONE} {SW}/>',
    "i-close": f'<path d="M13 13l22 22M35 13L13 35" {NONE} stroke="currentColor" stroke-width="4.5" stroke-linecap="round"/>',
    "i-swim-on": f'<path d="M8 27h28M27 17l10 10-10 10" {NONE} stroke="currentColor" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>'
                 f'<circle cx="12" cy="15" r="3.2" {NONE} stroke="currentColor" stroke-width="2.6"/><circle cx="19" cy="9" r="2.2" {NONE} stroke="currentColor" stroke-width="2.4"/>',
    "i-back": f'<path d="M38 24H12M21 14L11 24l10 10" {NONE} stroke="currentColor" stroke-width="4.5" stroke-linecap="round" stroke-linejoin="round"/>',
    "i-down": f'<path d="M6 11q4.5-4 9 0t9 0 9 0 9 0" {NONE} {SW}/><path d="M24 17v24M15 32l9 9 9-9" {NONE} stroke="currentColor" stroke-width="4.5" stroke-linecap="round" stroke-linejoin="round"/>',
    "i-up": f'<path d="M6 11q4.5-4 9 0t9 0 9 0 9 0" {NONE} {SW}/><path d="M24 41V18M15 27l9-9 9 9" {NONE} stroke="currentColor" stroke-width="4.5" stroke-linecap="round" stroke-linejoin="round"/>',
    "i-play": f'<path d="M16 10l22 14-22 14z" {FILL} {SW}/>',
    "i-check": f'<path d="M10 25l9 9 19-20" {NONE} stroke="currentColor" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>',
    "i-flip": f'<path d="M12 18a13 13 0 0 1 23-4l3 4M36 30a13 13 0 0 1-23 4l-3-4" {NONE} {SW}/><path d="M39 9v9h-9M9 39v-9h9" {NONE} {SW}/>',
    "i-photo": f'<rect x="6" y="14" width="36" height="25" rx="5" {NONE} {SW}/><path d="M17 14l3-5h8l3 5" {NONE} {SW}/><circle cx="24" cy="26" r="7" {NONE} {SW}/>',
    "i-rotate": f'<rect x="15" y="6" width="18" height="30" rx="3" {NONE} {SW}/><path d="M8 30a17 17 0 0 0 14 12M42 18A17 17 0 0 0 30 6" {NONE} {SW}/><path d="M18 38l4 4-4 4M34 2l-4 4 4 4" {NONE} {SW}/>',
    "i-parents": f'<circle cx="17" cy="11" r="5" {FILL}/><path d="M9 40V27q0-8 8-8t8 8v13" {NONE} {SW}/><circle cx="33" cy="20" r="4" {FILL}/><path d="M27 40v-9q0-5 6-5t6 5v9" {NONE} {SW}/>',
    "i-hold": f'<path d="M20 22V10a3 3 0 0 1 6 0v12l7 2q4 1 4 5l-2 10H20l-6-9q-1-3 2-4l4 2" {NONE} {SW}/><path d="M12 8a9 9 0 0 1 4-4" {NONE} {SW}/>',
    "i-lock": f'<rect x="10" y="21" width="28" height="20" rx="5" {FILL} {SW}/><path d="M16 21v-6a8 8 0 0 1 16 0v6" {NONE} {SW}/>',
    "i-lock-open": f'<rect x="10" y="21" width="28" height="20" rx="5" {FILL} {SW}/><path d="M16 21v-6a8 8 0 0 1 15-4" {NONE} {SW}/>',
    "i-day": f'<circle cx="24" cy="24" r="8" {FILL} {SW}/><path d="M24 5v6M24 37v6M5 24h6M37 24h6M10.5 10.5l4 4M33.5 33.5l4 4M10.5 37.5l4-4M33.5 14.5l4-4" {NONE} {SW}/>',
    "i-night": f'<path d="M30 8a16 16 0 1 0 10 26A13 13 0 0 1 30 8z" {FILL} {SW}/><path d="M12 9l1.5 3 3 1.5-3 1.5L12 18l-1.5-3-3-1.5 3-1.5z" {FILL}/>',
    "i-collection": f'<path d="M6 30q9-6 18 0t18 0" {NONE} {SW}/><path d="M6 38q9-6 18 0t18 0" {NONE} {SW}/><path d="M14 20q8-9 18-1-10 8-18-1z" {FILL}/><path d="M32 19l6-5v10z" {FILL}/><path d="M10 10q2 6 0 12" {NONE} {SW}/>',
    "i-quiz": f'<path d="M8 10h32a3 3 0 0 1 3 3v17a3 3 0 0 1-3 3H22l-9 8v-8H8a3 3 0 0 1-3-3V13a3 3 0 0 1 3-3z" {NONE} {SW}/><path d="M19 17a5 5 0 1 1 7 5q-2 1-2 4" {NONE} {SW}/><circle cx="24" cy="30" r="1.6" {FILL}/>',
    "i-who-where": f'<path d="M5 12h38M5 24h38M5 36h38" {NONE} stroke="currentColor" stroke-width="3" stroke-linecap="round" opacity=".55"/>'
                   f'<path d="M14 18q6-6 13 0-7 6-13 0z" {FILL}/><path d="M27 18l5-4v8z" {FILL}/><path d="M34 26v12M29 33l5 5 5-5" {NONE} {SW}/>',
    "i-net": f'<ellipse cx="18" cy="16" rx="11" ry="8" {NONE} {SW}/><path d="M8 18q2 16 10 20 8-4 10-20" {NONE} {SW}/><path d="M12 24l12 8M24 24l-12 8M18 22v14" {NONE} stroke="currentColor" stroke-width="2" opacity=".7"/><path d="M28 13l14-7" {NONE} stroke="currentColor" stroke-width="4" stroke-linecap="round"/>',
    "i-lamp": f'<rect x="8" y="17" width="16" height="14" rx="4" {FILL} {SW}/><path d="M24 20l4-2v12l-4-2" {FILL} {SW}/><path d="M33 16l8-5M34 24h9M33 32l8 5" {NONE} {SW}/>',
    "i-look-only": f'<circle cx="24" cy="24" r="19" {NONE} {SW}/><path d="M17 30V18a2.5 2.5 0 0 1 5 0v6-9a2.5 2.5 0 0 1 5 0v9-7a2.5 2.5 0 0 1 5 0v12q0 8-7 8h-2q-4 0-6-3l-4-6q-1-2 1-3t3 1z" {FILL} stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>',
    "i-eye": f'<path d="M4 24q10-13 20-13t20 13q-10 13-20 13T4 24z" {NONE} {SW}/><circle cx="24" cy="24" r="6" {FILL}/>',
    "i-air": f'<path d="M24 26v-8M18 20q-5-6-2-12M30 20q5-6 2-12M24 16q0-6 0-10" {NONE} {SW}/><path d="M6 40q6-10 18-10t18 10z" {FILL} {SW}/>',
    "i-depth": f'<rect x="18" y="5" width="12" height="38" rx="6" {NONE} {SW}/><path d="M30 14h5M30 24h5M30 34h5" {NONE} {SW}/><circle cx="24" cy="30" r="3.5" {FILL}/>',
    "i-size": f'<path d="M5 30h38v9H5z" {NONE} {SW}/><path d="M11 30v4M17 30v6M23 30v4M29 30v6M35 30v4" {NONE} stroke="currentColor" stroke-width="2.4"/><circle cx="14" cy="17" r="5" {FILL}/><path d="M28 22q6-10 15-2-8 7-15 2z" {FILL}/>',
    "i-turtle": f'<path d="M10 28q2-12 14-12t14 12z" {FILL} {SW}/><circle cx="41" cy="24" r="4" {FILL}/><path d="M14 28l-4 6M32 28l4 6M6 26l4 2" {NONE} {SW}/>',
    "i-level-1": f'<path d="M8 22q0-8 8-8h16q8 0 8 8v2q0 6-6 6h-5l-3-4-3 4h-5q-6 0-6-6z" {FILL} {SW}/><circle cx="36" cy="8" r="3" {NONE} stroke="currentColor" stroke-width="2.6"/>',
    "i-level-2": f'<path d="M8 22q0-8 8-8h16q8 0 8 8v2q0 6-6 6h-5l-3-4-3 4h-5q-6 0-6-6z" {FILL} {SW}/><circle cx="36" cy="8" r="3" {NONE} stroke="currentColor" stroke-width="2.6"/><circle cx="42" cy="3" r="2" {NONE} stroke="currentColor" stroke-width="2.4"/><path d="M12 36l-4 8h10l-2-8M32 36l2 8h10l-4-8" {FILL}/>',
    # ---- group badges (silhouettes, shape-first)
    "i-grp-ryba": f'<path d="M8 24q10-14 26-4l8-7v22l-8-7Q18 38 8 24z" {FILL}/><circle cx="15" cy="22" r="2" fill="#fff"/>',
    "i-grp-savec": f'<path d="M6 30q4-12 20-12 10 0 16 6l-4 1q-2 9-12 9-8 0-12-3l-4 4-1-4z" {FILL}/><path d="M28 13q0-5 3-8M28 13q-4-3-5-7M28 13q4-2 8-2" {NONE} stroke="currentColor" stroke-width="2.6" stroke-linecap="round"/><circle cx="34" cy="24" r="1.8" fill="#fff"/>',
    "i-grp-plaz": f'<path d="M9 30q2-14 15-14t15 14z" {FILL}/><circle cx="42" cy="25" r="4.5" {FILL}/><path d="M13 30l-5 7M33 30l5 7M8 27l-4 2" {NONE} {SW}/><path d="M16 26l4-6 8 0 4 6" {NONE} stroke="#fff" stroke-width="2" opacity=".7"/>',
    "i-grp-korys": f'<ellipse cx="24" cy="28" rx="13" ry="8" {FILL}/><path d="M11 26q-5-4-4-12M37 26q5-4 4-12" {NONE} {SW}/><path d="M4 13q3-6 8-2-3 4-8 2zM44 13q-3-6-8-2 3 4 8 2z" {FILL}/><path d="M13 32l-6 6M17 35l-4 6M35 32l6 6M31 35l4 6" {NONE} {SW}/>',
    "i-grp-mekkys": f'<path d="M12 22q0-14 12-14t12 14q0 6-3 8H15q-3-2-3-8z" {FILL}/><path d="M15 30q-4 6-9 6M20 31q-2 7-5 10M28 31q2 7 5 10M33 30q4 6 9 6M24 31v10" {NONE} {SW}/>',
    "i-grp-ostnokozec": f'<path d="M24 5l5 12 13 1-10 8 4 13-12-7-12 7 4-13-10-8 13-1z" {FILL} stroke="currentColor" stroke-width="3" stroke-linejoin="round"/>',
    "i-grp-zahavec": f'<path d="M8 22q0-14 16-14t16 14q-8 3-16 3T8 22z" {FILL}/><path d="M13 25q-2 7 1 14M19 26q2 8-1 15M29 26q-2 8 1 15M35 25q2 7-1 14" {NONE} {SW}/>',
    # ---- zones
    "i-zone-utes": f'<path d="M24 42V26M24 30l-8-8M16 22v-8M16 22l-6-4M24 26l8-9M32 17v-7M32 17l6-3" {NONE} stroke="currentColor" stroke-width="4" stroke-linecap="round"/><path d="M6 42h36" {NONE} {SW}/>',
    "i-zone-chaluhy": f'<path d="M18 42q-4-14 2-22t0-16M30 42q4-12-2-20t2-18" {NONE} {SW}/><path d="M20 30q-8-2-10-8 7-1 10 4M19 18q8-1 10-7-7-1-10 3M28 34q8-2 10-8-7-1-10 4M30 20q-8-1-10-7 7-1 10 3" {FILL}/>',
    "i-zone-sire-more": f'<path d="M4 12q5-5 10 0t10 0 10 0 10 0" {NONE} {SW}/><path d="M10 30q8-9 18-3l6-5v14l-6-5q-10 6-18-1z" {FILL}/><circle cx="12" cy="40" r="1.6" {FILL}/><circle cx="38" cy="42" r="1.6" {FILL}/>',
    "i-zone-hlubiny": f'<path d="M8 34q0-14 14-14 12 0 16 10-4 10-16 10Q8 40 8 34z" {FILL}/><path d="M24 20q4-10 12-10" {NONE} {SW}/><circle cx="37" cy="10" r="4" {FILL}/><path d="M42 5l2-2M43 12h3M37 3V1" {NONE} stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/>',
    # ---- what it eats
    "i-eats-plankton": f'<circle cx="14" cy="16" r="3.5" {FILL}/><circle cx="30" cy="12" r="2.5" {FILL}/><circle cx="24" cy="26" r="4" {FILL}/><circle cx="36" cy="30" r="3" {FILL}/><circle cx="12" cy="34" r="2.5" {FILL}/><circle cx="26" cy="40" r="2" {FILL}/>',
    "i-eats-algae": f'<path d="M14 44q-4-10 2-18t0-20M26 44q4-12-2-20t2-18M36 44q-2-8 2-14" {NONE} {SW}/>',
    "i-eats-fish": f'<path d="M6 24q10-12 24-4l9-7v22l-9-7Q16 36 6 24z" {FILL}/>',
    "i-eats-shellfish": f'<path d="M8 34Q6 14 24 10q18 4 16 24z" {FILL} {SW}/><path d="M24 34V14M16 34l4-18M32 34l-4-18" {NONE} stroke="#fff" stroke-width="2" opacity=".75"/>',
    "i-eats-jellyfish": f'<path d="M10 22q0-12 14-12t14 12q-7 3-14 3t-14-3z" {FILL}/><path d="M15 25q-2 7 1 13M24 26v14M33 25q2 7-1 13" {NONE} {SW}/>',
    "i-eats-squid": f'<path d="M24 4l9 14v10H15V18z" {FILL}/><path d="M17 28q-3 8-7 12M21 28v14M27 28v14M31 28q3 8 7 12" {NONE} {SW}/>',
    "i-eats-seagrass": f'<path d="M12 44q0-18 6-30M20 44q2-16 0-34M28 44q-2-14 4-28M36 44q-2-12 2-22" {NONE} {SW}/>',
    "i-eats-krill": f'<path d="M8 30q2-14 18-14 10 0 14 6-6 4-14 4-8 0-10 8z" {FILL}/><path d="M38 20q4-8 8-10M36 20q2-10 4-14M14 32l-2 6M20 30l-1 7M26 28v7" {NONE} stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/>',
    # ---- size comparisons for the card („Jsem velký jako …“)
    "i-cmp-dlan": f'<path d="M15 44V24l-5-7q-2-4 2-5t5 3l3 5V9a2.5 2.5 0 0 1 5 0v12-14a2.5 2.5 0 0 1 5 0v14-11a2.5 2.5 0 0 1 5 0v13-8a2.5 2.5 0 0 1 5 0v15q0 12-10 17z" {FILL} stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>',
    "i-cmp-kocka": f'<path d="M10 42V22l-3-12 9 6h14l9-6-3 12v20z" {FILL}/><circle cx="18" cy="26" r="2" fill="#fff"/><circle cx="30" cy="26" r="2" fill="#fff"/><path d="M38 40q8 0 6-10" {NONE} {SW}/>',
    "i-cmp-postel": f'<path d="M5 14v28M43 26v16M5 34h38M5 26h38v8H5z" {NONE} {SW}/><rect x="8" y="18" width="10" height="7" rx="3" {FILL}/>',
    "i-cmp-auto": f'<path d="M4 32v-7l5-1 5-9h18l6 9 6 2v6z" {FILL} {SW}/><circle cx="13" cy="34" r="5" fill="#fff" {SW}/><circle cx="35" cy="34" r="5" fill="#fff" {SW}/>',
    "i-cmp-autobus": f'<rect x="3" y="12" width="42" height="22" rx="4" {FILL} {SW}/><path d="M8 17h7v7H8zM19 17h7v7h-7zM30 17h7v7h-7z" fill="#fff"/><circle cx="12" cy="36" r="4.5" fill="#fff" {SW}/><circle cx="36" cy="36" r="4.5" fill="#fff" {SW}/>',
    "i-cmp-dum": f'<path d="M6 22L24 7l18 15v20H6z" {FILL} {SW}/><rect x="20" y="28" width="8" height="14" fill="#fff"/><rect x="11" y="24" width="6" height="6" fill="#fff"/><rect x="31" y="24" width="6" height="6" fill="#fff"/>',
    "i-eats-mixed": f'<path d="M4 18q6-8 15-3l5-4v14l-5-4Q10 26 4 18z" {FILL}/><path d="M24 42q-1-12 10-14 11 2 10 14z" {FILL}/><circle cx="14" cy="38" r="4" {FILL}/>',
}

FLAGS = {
    "i-flag-cs": '<rect x="2" y="9" width="44" height="30" rx="4" fill="#fff" stroke="#33243a" stroke-width="2"/>'
                 '<path d="M3 24h42v11a3 3 0 0 1-3 3H6a3 3 0 0 1-3-3z" fill="#d7141a"/><path d="M3 12a3 3 0 0 1 3-2l20 14L6 38a3 3 0 0 1-3-3z" fill="#11457e"/>'
                 '<rect x="2" y="9" width="44" height="30" rx="4" fill="none" stroke="#33243a" stroke-width="2"/>',
    "i-flag-en": '<clipPath id="fl-en"><rect x="2" y="9" width="44" height="30" rx="4"/></clipPath><g clip-path="url(#fl-en)"><rect x="2" y="9" width="44" height="30" fill="#012169"/>'
                 '<path d="M2 9l44 30M46 9L2 39" stroke="#fff" stroke-width="7"/><path d="M2 9l44 30M46 9L2 39" stroke="#c8102e" stroke-width="2.6"/>'
                 '<path d="M24 9v30M2 24h44" stroke="#fff" stroke-width="10"/><path d="M24 9v30M2 24h44" stroke="#c8102e" stroke-width="6"/></g>'
                 '<rect x="2" y="9" width="44" height="30" rx="4" fill="none" stroke="#33243a" stroke-width="2"/>',
}


def icons():
    body = "".join(f'<symbol id="{k}" viewBox="0 0 48 48">{v}</symbol>' for k, v in {**ICONS, **FLAGS}.items())
    with open(os.path.join(ART, "ui-icons.svg"), "w") as fh:
        fh.write(f'<svg xmlns="http://www.w3.org/2000/svg" style="display:none" aria-hidden="true">{body}</svg>\n')
    return list(ICONS) + list(FLAGS)


# ================================================================== the sitting diver (home + end screens)
SUIT = "var(--suit, #ef6f6c)"
HAIR = "var(--hair, #6b4226)"
SKIN = "var(--skin, #f6c9a5)"


def tube(pts, w, col_style):
    d = smooth(pts, closed=False, t=.2)
    return (f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="{f(w + 6)}" stroke-linecap="round" stroke-linejoin="round"/>'
            f'<path d="{d}" fill="none" style="stroke:{col_style}" stroke-width="{f(w)}" stroke-linecap="round" stroke-linejoin="round"/>')


def diver_sitting(a, x, y, s=1.0):
    """Girl sitting on the bow, mask pushed up on her forehead, fins dangling. (x,y) = seat point."""
    over = a.linear("dso", [(0, "#ffffff", .25), (.5, "#ffffff", 0), (1, "#1e1430", .28)], 0, y - 90, 0, y + 10)
    legs = (tube([(x - 6, y), (x + 20, y + 6), (x + 30, y + 52)], 26, SUIT) + tube([(x + 6, y - 4), (x + 34, y), (x + 48, y + 44)], 24, SUIT))
    fins = (f'<path d="M{x + 18} {y + 50}l-6 46 34 -6 -8 -40z" fill="#ffd25a" stroke="{INK}" stroke-width="3" stroke-linejoin="round"/>'
            f'<path d="M{x + 38} {y + 42}l2 46 32 -12 -18 -36z" fill="#e8b830" stroke="{INK}" stroke-width="3" stroke-linejoin="round"/>')
    tank = f'<rect x="{x - 40}" y="{y - 92}" width="26" height="70" rx="12" fill="#ffd25a" stroke="{INK}" stroke-width="3"/>' \
           f'<path d="M{x - 32} {y - 84}v52" stroke="#fff" stroke-width="3" opacity=".7" stroke-linecap="round"/>'
    torso_d = smooth([(x - 22, y + 4), (x - 26, y - 50), (x - 14, y - 88), (x + 14, y - 90), (x + 24, y - 54), (x + 20, y + 6)], t=.18)
    cl = a.clip("dst", torso_d)
    torso = (f'<path d="{torso_d}" style="fill:{SUIT}"/><g clip-path="{cl}"><rect x="{x - 40}" y="{y - 100}" width="80" height="110" fill="{over}"/>'
             f'<path d="M{x - 2} {y - 86}V{y}" stroke="#fff" stroke-width="4" opacity=".55"/></g>'
             f'<path d="{torso_d}" fill="none" stroke="{INK}" stroke-width="3" stroke-linejoin="round"/>')
    arm_back = tube([(x - 18, y - 78), (x - 30, y - 40), (x - 26, y - 8)], 18, SUIT)
    arm_front = tube([(x + 16, y - 78), (x + 34, y - 46), (x + 44, y - 20)], 19, SUIT) + \
        f'<circle cx="{x + 46}" cy="{y - 16}" r="9" style="fill:{SKIN}" stroke="{INK}" stroke-width="2.8"/>'
    hx, hy = x + 2, y - 128
    head = f'<circle cx="{hx}" cy="{hy}" r="40" style="fill:{SKIN}" stroke="{INK}" stroke-width="3"/>'
    hair = smooth([(hx - 42, hy + 10), (hx - 40, hy - 22), (hx - 16, hy - 42), (hx + 18, hy - 42), (hx + 40, hy - 22), (hx + 42, hy + 2),
                   (hx + 28, hy - 18), (hx + 6, hy - 22), (hx - 18, hy - 16), (hx - 30, hy + 4)], t=.18)
    pony = smooth([(hx - 30, hy - 30), (hx - 58, hy - 40), (hx - 76, hy - 26), (hx - 70, hy - 4), (hx - 56, hy + 8), (hx - 60, hy - 14), (hx - 40, hy - 14)], t=.2)
    hair_svg = (f'<path d="{pony}" style="fill:{HAIR}" stroke="{INK}" stroke-width="2.8" stroke-linejoin="round"/>'
                f'<path d="{hair}" style="fill:{HAIR}" stroke="{INK}" stroke-width="2.8" stroke-linejoin="round"/>'
                f'<ellipse cx="{hx - 34}" cy="{hy - 26}" rx="6" ry="8" fill="#ffd25a" stroke="{INK}" stroke-width="2.4"/>')
    # mask pushed up onto the forehead, snorkel at the side
    mask = (f'<path d="M{hx - 26} {hy - 26}q26 -10 52 0v14q-26 8 -52 0z" fill="#bff0ff" fill-opacity=".6" stroke="#eef7fa" stroke-width="6" stroke-linejoin="round"/>'
            f'<path d="M{hx - 26} {hy - 26}q26 -10 52 0v14q-26 8 -52 0z" fill="none" stroke="{INK}" stroke-width="2.6" stroke-linejoin="round"/>'
            f'<path d="M{hx - 40} {hy - 18}h14M{hx + 26} {hy - 18}h14" stroke="#3d4f6a" stroke-width="6" stroke-linecap="round"/>'
            f'<path d="M{hx + 42} {hy - 4}q6 -30 0 -56" fill="none" stroke="{INK}" stroke-width="12" stroke-linecap="round"/>'
            f'<path d="M{hx + 42} {hy - 4}q6 -30 0 -56" fill="none" stroke="#ffd25a" stroke-width="7" stroke-linecap="round"/>')
    face = (eye(hx - 14, hy + 4, 7.5, look=(.1, .1)) + eye(hx + 14, hy + 4, 7.5, look=(.1, .1)) + blush(hx - 24, hy + 18, 7, 4) + blush(hx + 24, hy + 18, 7, 4)
            + f'<path d="M{hx - 9} {hy + 20}Q{hx} {hy + 30} {hx + 9} {hy + 20}" fill="#8a2f3c" stroke="{INK}" stroke-width="2.4" stroke-linejoin="round"/>'
            + f'<path d="M{hx - 2} {hy + 12}q2 2 4 0" fill="none" stroke="{INK}" stroke-width="2.2" stroke-linecap="round"/>')
    lids = lid(hx - 14, hy + 4, 7.5, "#f6c9a5") + lid(hx + 14, hy + 4, 7.5, "#f6c9a5")
    net = (f'<path d="M{x - 24} {y - 6}q-6 18 6 26q12 -6 8 -24z" fill="#e9fbff" fill-opacity=".4" stroke="{INK}" stroke-width="2"/>'
           f'<ellipse cx="{x - 18}" cy="{y - 6}" rx="9" ry="3.5" fill="none" stroke="#d39a1f" stroke-width="3"/>')
    inner = (tank + arm_back + legs + fins + torso + net + arm_front + head + hair_svg + face + grp("lids", lids, (hx, hy + 4), ' opacity="0"') + mask)
    return grp("diver-sit", inner, (x, y), f' transform="translate({f(x)} {f(y)}) scale({s}) translate({f(-x)} {f(-y)})"')


# ================================================================== home (surface + boat)
def boat(a, x, y, w=420):
    """Little rowing boat; (x, y) = waterline centre."""
    hull = smooth([(x - w / 2, y - 46), (x + w / 2 + 20, y - 52), (x + w / 2 - 10, y + 6), (x + w * .3, y + 30), (x - w * .3, y + 30), (x - w / 2 + 14, y + 4)], t=.16)
    hg = a.linear("hull", [(0, "#ff9a7a"), (.5, "#e9724f"), (1, "#b5503a")], 0, y - 52, 0, y + 30)
    out = f'<path d="{hull}" fill="{hg}" stroke="{INK}" stroke-width="3.2" stroke-linejoin="round"/>'
    out += f'<path d="M{f(x - w / 2 + 6)} {f(y - 26)}Q{f(x)} {f(y - 18)} {f(x + w / 2 + 6)} {f(y - 30)}" fill="none" stroke="#ffffff" stroke-width="7" stroke-linecap="round"/>'
    out += f'<path d="M{f(x - w / 2 - 4)} {f(y - 48)}L{f(x + w / 2 + 24)} {f(y - 54)}" stroke="{INK}" stroke-width="13" stroke-linecap="round"/>'
    out += f'<path d="M{f(x - w / 2 - 4)} {f(y - 48)}L{f(x + w / 2 + 24)} {f(y - 54)}" stroke="#d9a464" stroke-width="8" stroke-linecap="round"/>'
    # oar resting across
    out += f'<path d="M{f(x - w * .2)} {f(y - 60)}L{f(x - w * .62)} {f(y + 20)}" stroke="{INK}" stroke-width="10" stroke-linecap="round"/><path d="M{f(x - w * .2)} {f(y - 60)}L{f(x - w * .62)} {f(y + 20)}" stroke="#d9a464" stroke-width="5" stroke-linecap="round"/>'
    out += f'<ellipse cx="{f(x - w * .62)}" cy="{f(y + 22)}" rx="12" ry="24" transform="rotate(30 {f(x - w * .62)} {f(y + 22)})" fill="#d9a464" stroke="{INK}" stroke-width="3"/>'
    # diver-down flag on a little mast (red with a white diagonal — the real signal)
    mx = x - w * .32
    out += f'<path d="M{f(mx)} {f(y - 50)}V{f(y - 190)}" stroke="{INK}" stroke-width="7" stroke-linecap="round"/><path d="M{f(mx)} {f(y - 50)}V{f(y - 190)}" stroke="#d9a464" stroke-width="3.5" stroke-linecap="round"/>'
    fl = f"M{f(mx + 2)} {f(y - 188)}h58q-6 18 0 38h-58z"
    out += (f'<path d="{fl}" fill="#e0453a" stroke="{INK}" stroke-width="2.8" stroke-linejoin="round"/>'
            f'<path d="M{f(mx + 4)} {f(y - 186)}L{f(mx + 58)} {f(y - 152)}" stroke="#ffffff" stroke-width="8"/>'
            f'<path d="{fl}" fill="none" stroke="{INK}" stroke-width="2.8" stroke-linejoin="round"/>')
    return out


def waves_band(y, amp, wl, col, W=1600, H=1000, ph=0.0):
    pts = [(x, y + amp * math.sin(2 * math.pi * x / wl + ph)) for x in range(-20, W + 21, 10)]
    return "M" + " L".join(f"{f(px)} {f(py)}" for px, py in pts) + f" L{W + 20} {H} L-20 {H}Z"


def home():
    a = Art("home", seed=301)
    W, H = 1600, 1000
    WL = 470      # waterline
    sky = a.linear("sky", [(0, "#9fd6e8"), (.6, "#d3eef1"), (1, "#ffeccc")], 0, 0, 0, WL)
    sea_g = a.linear("sea", [(0, "#8fe3dc"), (.35, "#3fc0c4"), (1, "#1d8aa3")], 0, WL, 0, H)
    sun = a.radial("sun", [(0, "#fff7de", 1), (.25, "#ffe39a", .9), (.6, "#fff7de", .25), (1, "#fff7de", 0)], user=(1060, 160, 220))
    body = f'<rect width="{W}" height="{WL + 20}" fill="{sky}"/><circle cx="1060" cy="160" r="220" fill="{sun}"/>'
    body += f'<circle cx="1060" cy="160" r="58" fill="#ffe9a8" stroke="#ffd25a" stroke-width="5"/>'
    for cx_, cy_, s_ in ((300, 130, 1.0), (760, 80, .7), (1000, 230, .55)):
        cl = smooth([(cx_ - 90 * s_, cy_ + 20 * s_), (cx_ - 70 * s_, cy_ - 14 * s_), (cx_ - 20 * s_, cy_ - 34 * s_), (cx_ + 30 * s_, cy_ - 26 * s_),
                     (cx_ + 80 * s_, cy_ - 4 * s_), (cx_ + 96 * s_, cy_ + 20 * s_)], t=.2)
        body += f'<path d="{cl}" fill="#ffffff" opacity=".9"/>'
    # distant island
    body += f'<path d="M60 {WL}Q160 {WL - 70} 280 {WL - 60}Q360 {WL - 90} 440 {WL}Z" fill="#7fbfa8" opacity=".8"/>'
    # underwater
    body += f'<path d="{waves_band(WL, 6, 160, None)}" fill="{sea_g}"/>'
    # light rays underwater
    for i, (x, w) in enumerate(((380, 90), (620, 60), (980, 120), (1260, 70))):
        g = a.linear("ur", [(0, "#ffffff", .45), (1, "#ffffff", 0)], 0, WL, 0, H)
        body += f'<path d="M{x - w / 2} {WL}L{x + w / 2} {WL}L{x + w * .2 - 140} {H}L{x - w - 140} {H}Z" fill="{g}"/>'
    # reef at the bottom (inked, bright — the promise of the dive)
    reef = ""
    floor_pts = [(x, 905 + 22 * math.sin(x / 140) + 10 * math.sin(x / 47)) for x in range(-20, W + 21, 20)]
    reef += f'<path d="M{" L".join(f"{f(x)} {f(y)}" for x, y in floor_pts)} L{W + 20} {H} L-20 {H}Z" fill="#f1d9a6" stroke="{INK}" stroke-width="3"/>'
    reef += sea.brain_coral(a, 300, 915, 60, sea.CORAL["yellow"]) + sea.branch_coral(a, 420, 915, 150, sea.CORAL["violet"], 5, 3)
    reef += sea.fan_coral(a, 1180, 905, 170, sea.CORAL["red"]) + sea.table_coral(a, 1360, 905, 170, sea.CORAL["teal"])
    reef += sea.tube_sponge(a, 1020, 915, 90, sea.CORAL["orange"]) + sea.seagrass(a, 560, 920, 70, 7, sway_cls="sway") + sea.seagrass(a, 1460, 915, 70, 6, sway_cls="sway")
    reef += sea.brain_coral(a, 1500, 920, 48, sea.CORAL["pink"]) + sea.branch_coral(a, 130, 920, 120, sea.CORAL["pink"], 4, 9)
    body += grp("reef", reef)
    # surface glitter
    rng = random.Random(3)
    glit = "".join(f'<path d="M{f(x)} {f(y)}q12 -5 24 0" fill="none" stroke="#ffffff" stroke-width="3" stroke-linecap="round" opacity=".8"/>'
                   for x, y in [(rng.uniform(0, W), WL + rng.uniform(8, 40)) for _ in range(40)])
    body += glit
    # boat + sitting diver (she sits on the bow, fins over the water)
    bx = 700
    body += grp("boat", boat(a, bx, WL + 6, 440) + diver_sitting(a, bx + 210, WL - 54, 1.0), (bx, WL + 6))
    # front wave lip over the hull bottom
    lip = "".join(f" L{f(x)} {f(WL + 10 + 5 * math.sin(2 * math.pi * x / 120 + 1.3))}" for x in range(-10, W + 21, 10))
    lip_back = "".join(f" L{f(x)} {f(WL + 34 + 4 * math.sin(2 * math.pi * x / 90))}" for x in range(W + 20, -21, -10))
    body += f'<path d="M-20 {WL + 10}{lip}{lip_back}Z" fill="#8fe3dc" opacity=".6"/>'
    body += f'<path d="M-20 {WL + 10}' + "".join(f" L{f(x)} {f(WL + 10 + 5 * math.sin(2 * math.pi * x / 120 + 1.3))}" for x in range(-10, W + 21, 10)) + '" fill="none" stroke="#e9fbff" stroke-width="4"/>'
    s = (f'<svg xmlns="http://www.w3.org/2000/svg" class="scene" viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMid slice" '
         f'data-waterline="{WL}" data-turtle="1010 {WL + 4}" role="img" aria-label="Loďka na hladině"><defs>{"".join(a.defs)}</defs>{body}</svg>\n')
    open(os.path.join(ART, "home.svg"), "w").write(s)


# ================================================================== Můj kousek moře
def my_sea(night=False):
    """v2: a little reef garden framed on both sides, open in the middle for her animals."""
    a = Art("mysea-n" if night else "mysea-d", seed=311)
    W, H = 1600, 1000
    FY = 780
    dk = (lambda c: mix(c, "#0d1a3a", .58)) if night else (lambda c: c)
    tc = lambda col: tuple(dk(c) for c in col)
    if night:
        water = a.linear("w", [(0, "#1d3f78"), (.5, "#12305d"), (1, "#0a1a36")], 0, 0, 0, H)
    else:
        water = a.linear("w", [(0, "#a6ece4"), (.4, "#5fd0cc"), (1, "#2aa3b3")], 0, 0, 0, H)
    body = f'<rect width="{W}" height="{H}" fill="{water}"/>'
    if night:
        moon = a.radial("m", [(0, "#f3f0ff", .9), (.2, "#cfd8ff", .45), (1, "#cfd8ff", 0)], user=(1150, 0, 460))
        body += f'<rect width="{W}" height="{H}" fill="{moon}"/>'
    else:
        for x, y, rx, ry, op in ((420, 120, 420, 150, .22), (1180, 90, 460, 160, .2)):
            g = a.radial("lp", [(0, "#ffffff", op), (1, "#ffffff", 0)], cx="50%", cy="50%", r="50%")
            body += f'<ellipse cx="{x}" cy="{y}" rx="{rx}" ry="{ry}" fill="{g}"/>'
        for x, w in ((300, 120), (700, 80), (1100, 150), (1450, 90)):
            g = a.linear("r", [(0, "#fffce1", .5), (1, "#fffce1", 0)], 0, 0, 0, FY)
            body += grp("ray", f'<path d="M{x - w / 2} 0L{x + w / 2} 0L{x + w * .3 - 160} {FY + 40}L{x - w - 160} {FY + 40}Z" fill="{g}"/>', (x, 0))
    surf = "".join(f" L{f(x)} {f(30 + 8 * math.sin(x / 60))}" for x in range(W, -1, -20))
    body += f'<path d="M0 0H{W}{surf}Z" fill="{"#2a4f8c" if night else "#d3f4ff"}" opacity=".7"/>'
    # hazy far reef planes (no ink)
    far1, far2 = (dk(mix("#3fc0c4", "#8fe3dc", .4)), dk(mix("#3fc0c4", "#239fb0", .5)))
    for y0, col, op, sd in ((690, far1, .5, 3), (735, far2, .7, 4)):
        rng = random.Random(sd)
        pts = [(x, y0 + 18 * math.sin(x / 170 + sd)) for x in range(-20, W + 21, 20)]
        body += f'<path d="M{" L".join(f"{f(x)} {f(y)}" for x, y in pts)} L{W + 20} {H} L-20 {H}Z" fill="{col}" opacity="{op}"/>'
        for x in range(60, W, 150):
            xx, hh = x + rng.uniform(-30, 30), rng.uniform(50, 120)
            yy = y0 + 18 * math.sin(xx / 170 + sd) + 6
            body += "".join(f'<path d="M{f(xx)} {f(yy)}Q{f(xx + math.cos(math.radians(60 + k * 15)) * hh * .3)} {f(yy - hh * .5)} {f(xx + math.cos(math.radians(60 + k * 15)) * hh * .9)} {f(yy - math.sin(math.radians(60 + k * 15)) * hh)}" fill="none" stroke="{col}" stroke-width="{f(hh * .1)}" stroke-linecap="round" opacity="{op}"/>' for k in range(5))
    # sand: textured, ripples, pebbles, shells
    floor_pts = [(x, FY + 26 * math.sin(x / 260 + .6) + 8 * math.sin(x / 70)) for x in range(-20, W + 21, 20)]
    yat = lambda x: FY + 26 * math.sin(x / 260 + .6) + 8 * math.sin(x / 70)
    sand = tc(("#f1d9a6", "#fbecc8", "#d8b77a"))
    g = a.linear("s", [(0, sand[1]), (.08, sand[0]), (1, sand[2])], 0, FY - 30, 0, H)
    fd = f'M{" L".join(f"{f(x)} {f(y)}" for x, y in floor_pts)} L{W + 20} {H} L-20 {H}Z'
    body += f'<path d="{fd}" fill="{g}"/>'
    rng = random.Random(9)
    body += sea.speckle(a, fd, (0, FY - 40, W, H), 700, (sand[1], sand[2], dk("#ffffff")), (.9, 2.4), 9, .55)
    body += f'<path d="M{" L".join(f"{f(x)} {f(y + 9)}" for x, y in floor_pts)}" fill="none" stroke="{dk("#fff6dc")}" stroke-width="14" opacity=".6"/>'
    body += f'<path d="M{" L".join(f"{f(x)} {f(y)}" for x, y in floor_pts)}" fill="none" stroke="{INK}" stroke-width="3"/>'
    for _ in range(26):
        x = rng.uniform(40, W - 40)
        y = yat(x) + rng.uniform(24, 180)
        w = rng.uniform(30, 70)
        body += f'<path d="M{f(x - w / 2)} {f(y)}q{f(w / 4)} -6 {f(w / 2)} 0t{f(w / 2)} 0" fill="none" stroke="{sand[2]}" stroke-width="2.6" stroke-linecap="round" opacity=".8"/>'
    for _ in range(26):
        x = rng.uniform(20, W - 20)
        y = yat(x) + rng.uniform(10, 200)
        r = rng.uniform(4, 10)
        body += f'<ellipse cx="{f(x)}" cy="{f(y)}" rx="{f(r)}" ry="{f(r * .62)}" fill="{dk(rng.choice(("#c9b48c", "#a9967a", "#e3d2ad")))}" stroke="{INK}" stroke-width="1.3"/>'
    # coral garden, left edge
    deco = sea.fan_coral(a, 90, yat(90) + 6, 260, tc(sea.CORAL["violet"]))
    deco += sea.rock(a, 300, yat(300) + 44, 420, 230, tc((sea.ROCK, sea.ROCK_L, sea.ROCK_D)), crust=dk("#e98fa6"))
    deco += sea.zoanthids(a, 300, yat(300) - 168, 8, tc(("#7fe0b0", "#e8fff2", "#3a9a70")))
    deco += sea.brain_coral(a, 230, yat(230) - 120, 56, tc(sea.CORAL["yellow"]))
    deco += sea.branch_coral(a, 520, yat(520) + 6, 170, tc(sea.CORAL["pink"]), 5, 4)
    deco += sea.soft_coral(a, 610, yat(610) + 6, 86, tc(("#f7b26a", "#ffe0b0", "#cf7b3a")))
    deco += sea.kelp(a, 150, yat(150) + 10, 300, 40, col=tc((sea.KELP, sea.KELP_L, sea.KELP_D)), segs=3, cls="sway")
    # meadow (centre-left) and a few shells, the middle stays open
    deco += sea.seagrass(a, 820, yat(820) + 12, 74, 10, col=dk("#6aa04a"), light=dk("#9cc96e"), sway_cls="sway")
    deco += sea.seagrass(a, 900, yat(900) + 16, 56, 8, col=dk("#6aa04a"), light=dk("#9cc96e"), sway_cls="sway")
    deco += sea.shell(a, 760, yat(760) + 50, 1.4, dk("#ffd9c0")) + sea.snail_shell(a, 1040, yat(1040) + 70, 1.4, dk("#f6c9a0"))
    deco += sea.shell(a, 1180, yat(1180) + 80, 1.1, dk("#ffe6b0"))
    # coral garden, right edge
    deco += sea.table_coral(a, 1230, yat(1230) + 8, 200, tc(sea.CORAL["teal"]))
    deco += sea.rock(a, 1400, yat(1400) + 36, 300, 140, tc((sea.ROCK, sea.ROCK_L, sea.ROCK_D)), crust=dk("#c58cf0"))
    deco += sea.tube_sponge(a, 1330, yat(1330) + 6, 110, tc(sea.CORAL["orange"]))
    deco += sea.sea_whip(a, 1500, yat(1500) + 6, 200, tc(("#ff7f6a", "#ffd0c4", "#c94f3f")))
    deco += sea.fan_coral(a, 1560, yat(1560) + 6, 230, tc(sea.CORAL["red"]))
    deco += sea.kelp(a, 1460, yat(1460) + 10, 320, 43, col=tc((sea.KELP, sea.KELP_L, sea.KELP_D)), segs=3, cls="sway")
    body += deco
    if night:
        rng = random.Random(7)
        gl = ""
        for _ in range(80):
            x, y = rng.uniform(0, W), rng.uniform(40, FY + 120)
            c = rng.choice(("#6ff3ff", "#b9a1ff", "#9dffc8"))
            gl += f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(rng.uniform(1.6, 3.4))}" fill="{c}" opacity=".8"/>'
        for x in (300, 1400, 600, 1250):
            y = yat(x) - rng.uniform(60, 160)
            gl += "".join(f'<circle cx="{f(x + rng.uniform(-60, 60))}" cy="{f(y + rng.uniform(-40, 40))}" r="2.6" fill="#9dffc8"/>' for _ in range(6))
        body += grp("glow", gl)
    s = (f'<svg xmlns="http://www.w3.org/2000/svg" class="scene my-sea" data-mode="{"night" if night else "day"}" viewBox="0 0 {W} {H}" '
         f'preserveAspectRatio="xMidYMax slice" data-floor-y="{FY}" role="img" aria-label="Můj kousek moře"><defs>{"".join(a.defs)}</defs>{body}</svg>\n')
    open(os.path.join(ART, f"my-sea-{'night' if night else 'day'}.svg"), "w").write(s)


# ================================================================== Kdo kde bydlí? — cross-section
def cross_section():
    a = Art("xsec", seed=321)
    W, H = 1600, 1000
    SKY = 110
    bands = [("utes", SKY, 330, ("#8fe3dc", "#3fc0c4")), ("chaluhy", 330, 540, ("#6fc3b4", "#237479")),
             ("sire-more", 540, 760, ("#3a9fd6", "#164f8c")), ("hlubiny", 760, H, ("#12305d", "#08142e"))]
    sky = a.linear("sky", [(0, "#9fd6e8"), (1, "#ffeccc")], 0, 0, 0, SKY)
    body = f'<rect width="{W}" height="{SKY + 10}" fill="{sky}"/><circle cx="1460" cy="50" r="30" fill="#fff3c4" stroke="#ffd25a" stroke-width="4"/>'
    for z, y0, y1, (c0, c1) in bands:
        g = a.linear(z, [(0, c0), (1, c1)], 0, y0, 0, y1)
        body += grp("band", f'<rect x="0" y="{y0}" width="{W}" height="{y1 - y0}" fill="{g}"/>', None, f' data-zone="{z}" data-y0="{y0}" data-y1="{y1}"')
    # band dividers: soft dashed lines (the "floors" of the sea)
    for _, y0, _, _ in bands[1:]:
        body += f'<path d="M0 {y0}H{W}" stroke="#ffffff" stroke-width="3" stroke-dasharray="14 12" opacity=".5"/>'
    # the seabed: coast top-left sloping down to the abyssal plain
    slope = [(0, SKY + 40), (180, 260), (330, 330), (420, 470), (520, 540), (600, 760), (700, 900), (900, 940), (1200, 930), (1600, 950)]
    d = smooth(slope + [(1640, H + 40), (-40, H + 40)], t=.15)
    sg = a.linear("bed", [(0, "#f1d9a6"), (.25, "#b0aa96"), (.5, "#5b5a52"), (.8, "#2b2f52"), (1, "#151833")], 0, SKY, 0, H)
    body += f'<path d="{d}" fill="{sg}" stroke="{INK}" stroke-width="3"/>'
    body += sea.brain_coral(a, 150, 250, 34, sea.CORAL["yellow"]) + sea.branch_coral(a, 250, 290, 80, sea.CORAL["pink"], 4, 2)
    body += sea.fan_coral(a, 320, 330, 70, sea.CORAL["violet"])
    body += sea.kelp(a, 380, 410, 160, 51, segs=3) + sea.kelp(a, 460, 500, 190, 52, segs=3)
    o, gl = sea.sea_pen(a, 980, 938, 60)
    o2, gl2 = sea.sea_pen(a, 1300, 932, 50)
    body += o + o2 + gl + gl2 + sea.glass_sponge(a, 1120, 938, 60)
    # surface line + little boat
    body += f'<path d="M0 {SKY}' + "".join(f" L{x} {f(SKY + 4 * math.sin(x / 40))}" for x in range(0, W + 1, 20)) + '" fill="none" stroke="#e9fbff" stroke-width="5"/>'
    body += f'<g transform="translate(1180 {SKY + 4}) scale(.36) translate(-1180 {-(SKY + 4)})">{boat(a, 1180, SKY + 4, 440)}</g>'
    s = (f'<svg xmlns="http://www.w3.org/2000/svg" class="scene cross-section" viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMid slice" '
         f'role="img" aria-label="Řez mořem: útes, chaluhy, širé moře, hlubiny"><defs>{"".join(a.defs)}</defs>{body}</svg>\n')
    open(os.path.join(ART, "cross-section.svg"), "w").write(s)


# ================================================================== app icon source
def app_icon():
    a = Art("appicon", seed=331)
    S = 1024
    g = a.linear("bg", [(0, "#8fe3dc"), (.55, "#3fc0c4"), (1, "#1d6f9a")], 0, 0, 0, S)
    body = f'<rect width="{S}" height="{S}" fill="{g}"/>'
    for x, w in ((260, 120), (560, 90), (820, 140)):
        rg = a.linear("r", [(0, "#ffffff", .45), (1, "#ffffff", 0)], 0, 0, 0, S)
        body += f'<path d="M{x - w / 2} 0L{x + w / 2} 0L{x + w * .3 - 200} {S}L{x - w - 200} {S}Z" fill="{rg}"/>'
    diver = open(os.path.join(ART, "diver.svg")).read()
    inner = re.sub(r'^<svg[^>]*>', '', diver).replace('</svg>', '').replace('class="lamp"', 'class="lamp" display="none"')
    inner = re.sub(r'<g class="anchors".*?</g>', '', inner, flags=re.S)
    body += f'<svg x="40" y="170" width="980" height="700" viewBox="196 10 290 205">{inner}</svg>'
    for cx_, cy_, r in ((830, 240, 34), (880, 150, 22), (850, 80, 14)):
        body += f'<circle cx="{cx_}" cy="{cy_}" r="{r}" fill="#ffffff" fill-opacity=".25" stroke="#ffffff" stroke-width="6"/>'
    s = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {S} {S}" role="img" aria-label="Mořský svět"><defs>{"".join(a.defs)}</defs>{body}</svg>\n')
    open(os.path.join(ART, "app-icon.svg"), "w").write(s)


if __name__ == "__main__":
    n = icons()
    # home() is v1 — art/home.svg is now written by build_v2.py (run build_v2 after build_ui)
    my_sea(False)
    my_sea(True)
    cross_section()
    app_icon()
    print("ui ok", len(n), "icons")
