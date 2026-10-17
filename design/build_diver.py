#!/usr/bin/env python3
"""Mořský svět — the girl diver (art/diver.svg). Deterministic, stdlib only.

Generic little diver, profile swimming to the RIGHT, head in a friendly 3/4 turn so both eyes show
through one mask lens. Hair and suit colours come from CSS: var(--hair), var(--suit) (and var(--skin)).
Shading on those parts is a neutral overlay, so ANY parent-chosen colour keeps its volume.

Contract (DESIGN.md §6.2):
  svg.diver viewBox 0 0 480 240
    g.leg-back[data-pivot]   far leg + fin (behind)        kick: rotate ±14° at --t-kick, anti-phase
    g.arm-back[data-pivot]   far arm (behind the torso)
    g.body[data-pivot]       torso, tank, belt
      g.net[data-pivot]      net at the waist (swings)
    g.leg-front[data-pivot]  near leg + fin
    g.head[data-pivot]       head, face, mask
      g.hair[data-pivot]     ponytail (wave at --t-hair)
      g.lids                 blink (opacity 0 by default)
      g.lamp                 headlamp glow + beam (opacity 0; on in the deep)
    g.arm-front[data-pivot]  near arm
    circle.anchor-bubbles / anchor-lamp / anchor-hand / anchor-net
"""
import math
import os

from svgkit import INK, Art, f, grp, smooth, eye, lid, blush, mix

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "art")

SUIT = "var(--suit, #ef6f6c)"
HAIR = "var(--hair, #6b4226)"
SKIN = "var(--skin, #f6c9a5)"
SKIN_HEX = "#f6c9a5"
GEAR = "#ffd25a"
GEAR_D = "#d39a1f"
GEAR_L = "#ffeaa0"
STRAP = "#3d4f6a"


def limb(pts, w, col_style, hi=True, dark_overlay=0.0):
    """Ink-outlined tube along a polyline. col_style is a CSS colour (may be var())."""
    d = smooth(pts, closed=False, t=.2)
    out = (f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="{f(w + 6)}" stroke-linecap="round" stroke-linejoin="round"/>'
           f'<path d="{d}" fill="none" style="stroke:{col_style}" stroke-width="{f(w)}" stroke-linecap="round" stroke-linejoin="round"/>')
    if dark_overlay:
        out += f'<path d="{d}" fill="none" stroke="#1e1430" stroke-opacity="{dark_overlay}" stroke-width="{f(w)}" stroke-linecap="round"/>'
    if hi:
        hp = [(x, y - w * .22) for x, y in pts]
        out += (f'<path d="{smooth(hp, closed=False, t=.2)}" fill="none" stroke="#fff" stroke-opacity=".28" '
                f'stroke-width="{f(w * .3)}" stroke-linecap="round"/>')
    return out


def fin(a, ankle, tip_top, tip_bot, back=False):
    ax, ay = ankle
    pts = [(ax + 6, ay - 9), (tip_top[0] + 30, tip_top[1] + 4), tip_top, (tip_top[0] - 6, (tip_top[1] + tip_bot[1]) / 2),
           tip_bot, (tip_bot[0] + 30, tip_bot[1] - 3), (ax + 6, ay + 10)]
    d = smooth(pts, t=.14)
    col = mix(GEAR, "#7a6a50", .35) if back else GEAR
    dk = mix(GEAR_D, "#5a4a30", .35) if back else GEAR_D
    g = a.linear("fin", [(0, GEAR_L if not back else mix(GEAR_L, "#7a6a50", .35)), (.5, col), (1, dk)], 0, tip_top[1], 0, tip_bot[1])
    out = f'<path d="{d}" fill="{g}" stroke="{INK}" stroke-width="3" stroke-linejoin="round"/>'
    # ribs
    for k in (.3, .62):
        y0 = ay + (k - .5) * 10
        y1 = tip_top[1] + (tip_bot[1] - tip_top[1]) * k
        out += f'<path d="M{f(ax - 4)} {f(y0)}Q{f((ax + tip_top[0]) / 2)} {f((y0 + y1) / 2 + 3)} {f(tip_top[0] + 14)} {f(y1)}" fill="none" stroke="{dk}" stroke-width="2.4" stroke-linecap="round"/>'
    # foot pocket
    out += f'<ellipse cx="{f(ax - 2)}" cy="{f(ay)}" rx="15" ry="12" fill="{dk}" stroke="{INK}" stroke-width="2.6"/>'
    return out


def build():
    a = Art("diver", seed=7)
    W, H = 480, 240

    # ------------------------------------------------------------- legs
    hip_b, knee_b, ank_b = (186, 128), (146, 122), (110, 128)
    leg_back = limb([hip_b, knee_b, ank_b], 27, SUIT, dark_overlay=.28)
    leg_back = fin(a, ank_b, (42, 104), (48, 146), back=True) + leg_back
    hip_f, knee_f, ank_f = (180, 142), (140, 152), (102, 154)
    leg_front = limb([hip_f, knee_f, ank_f], 29, SUIT)
    leg_front = fin(a, ank_f, (32, 138), (40, 182)) + leg_front
    # knee stripe (neoprene panel)
    leg_front += f'<path d="M{f(142)} {f(139)}Q{f(136)} {f(152)} {f(141)} {f(166)}" fill="none" stroke="#fff" stroke-opacity=".55" stroke-width="3" stroke-linecap="round"/>'

    # ------------------------------------------------------------- arms
    sh_b = (300, 118)
    arm_back = limb([sh_b, (322, 150), (350, 170)], 21, SUIT, dark_overlay=.28)
    arm_back += f'<circle cx="357" cy="174" r="10" style="fill:{SKIN}" stroke="{INK}" stroke-width="2.8"/>'
    arm_back += f'<circle cx="357" cy="174" r="10" fill="#1e1430" opacity=".18"/>'
    sh_f = (288, 126)
    arm_front = limb([sh_f, (300, 166), (330, 188)], 23, SUIT)
    # cuff + hand (open, friendly)
    arm_front += (f'<path d="M334 180Q348 176 355 186Q357 197 345 200Q333 200 330 191Z" style="fill:{SKIN}" stroke="{INK}" stroke-width="2.8" stroke-linejoin="round"/>'
                  f'<path d="M350 180q6 -4 9 2" fill="none" stroke="{INK}" stroke-width="2.4" stroke-linecap="round"/>')
    arm_front += f'<path d="M318 184q6 4 4 12" fill="none" stroke="#fff" stroke-opacity=".6" stroke-width="3" stroke-linecap="round"/>'

    # ------------------------------------------------------------- body (torso, tank)
    torso_pts = [(304, 102), (320, 120), (314, 152), (276, 164), (222, 160), (174, 154), (160, 134), (172, 114), (222, 104), (268, 100)]
    td = smooth(a.jit(torso_pts, .4))
    tclip = a.clip("torso", td)
    over = a.linear("tov", [(0, "#ffffff", .28), (.45, "#ffffff", 0), (1, "#1e1430", .3)], 0, 100, 0, 164)
    body = f'<path d="{td}" style="fill:{SUIT}"/>'
    body += (f'<g clip-path="{tclip}"><rect x="150" y="90" width="180" height="80" fill="{over}"/>'
             # white side panel (neoprene stripe) along the flank
             f'<path d="M168 138Q230 128 316 134" fill="none" stroke="#fff" stroke-opacity=".6" stroke-width="5" stroke-linecap="round"/>'
             f'<path d="M160 156Q230 150 320 160" fill="none" stroke="#1e1430" stroke-opacity=".18" stroke-width="12"/></g>')
    body += f'<path d="{td}" fill="none" stroke="{INK}" stroke-width="3" stroke-linejoin="round"/>'
    # tank on the back
    tank_d = smooth([(206, 78), (272, 74), (290, 88), (276, 106), (210, 110), (194, 94)], t=.18)
    tg = a.linear("tank", [(0, GEAR_L), (.5, GEAR), (1, GEAR_D)], 0, 74, 0, 110)
    tank = f'<path d="{tank_d}" fill="{tg}" stroke="{INK}" stroke-width="3" stroke-linejoin="round"/>'
    tank += f'<path d="M214 84Q240 80 266 81" fill="none" stroke="#fff" stroke-opacity=".7" stroke-width="3.5" stroke-linecap="round"/>'
    tank += f'<path d="M288 84l10 -4" stroke="{INK}" stroke-width="3" stroke-linecap="round"/><circle cx="301" cy="78" r="5" fill="#9aa3b5" stroke="{INK}" stroke-width="2.4"/>'
    # straps + belt
    straps = (f'<path d="M266 104Q276 130 268 160" fill="none" stroke="{STRAP}" stroke-width="7" stroke-linecap="round"/>'
              f'<path d="M190 112Q196 134 192 156" fill="none" stroke="{STRAP}" stroke-width="8" stroke-linecap="round"/>'
              f'<rect x="185" y="128" width="13" height="12" rx="3" fill="#c9ced8" stroke="{INK}" stroke-width="2"/>')
    # net at the waist (hangs below the hip)
    net_mesh = a.pattern("mesh", 7, 7, '<path d="M0 0L7 7M7 0L0 7" stroke="#3d4f6a" stroke-width="1.1" opacity=".75"/>')
    bag = smooth([(190, 166), (226, 166), (222, 186), (210, 202), (198, 196)], t=.2)
    net = (f'<path d="M206 156L208 166" stroke="{INK}" stroke-width="3" stroke-linecap="round"/>'
           f'<path d="{bag}" fill="#e9fbff" fill-opacity=".35"/><path d="{bag}" fill="{net_mesh}"/>'
           f'<path d="{bag}" fill="none" stroke="{INK}" stroke-width="2.2" stroke-linejoin="round"/>'
           f'<ellipse cx="208" cy="166" rx="19" ry="5.5" fill="none" stroke="{GEAR_D}" stroke-width="4"/>'
           f'<ellipse cx="208" cy="166" rx="19" ry="5.5" fill="none" stroke="{INK}" stroke-width="1.4"/>')
    body = tank + body + straps + grp("net", net, (207, 158))

    # ------------------------------------------------------------- head
    hc = (346, 96)
    hr = 47
    head_d = smooth([(hc[0] + hr * math.cos(t) * (1.04 if math.cos(t) > 0 else 1), hc[1] + hr * math.sin(t) * (1.0 if math.sin(t) < 0 else .96))
                     for t in [2 * math.pi * i / 20 for i in range(20)]])
    skin_g = a.radial("skin", [(0, "#ffe2cc"), (.6, SKIN_HEX), (1, "#e7a986")], cx="62%", cy="38%", r="70%")
    head = f'<path d="{head_d}" style="fill:{SKIN}"/><path d="{head_d}" fill="{skin_g}" opacity=".55"/>'
    # hair cap (back + top), bangs at the front
    cap_pts = [(296, 108), (298, 78), (316, 56), (346, 47), (374, 52), (392, 66), (388, 72), (370, 66), (352, 70),
               (336, 70), (326, 82), (318, 104), (306, 120)]
    cap_d = smooth(a.jit(cap_pts, .5), t=.18)
    hclip = a.clip("hair", cap_d)
    hover = a.linear("hov", [(0, "#ffffff", .22), (.5, "#ffffff", 0), (1, "#140c1c", .35)], 0, 46, 0, 120)
    hair_cap = (f'<path d="{cap_d}" style="fill:{HAIR}"/><g clip-path="{hclip}"><rect x="290" y="40" width="110" height="90" fill="{hover}"/>'
                f'<path d="M310 66Q332 52 362 54" fill="none" stroke="#fff" stroke-opacity=".3" stroke-width="5" stroke-linecap="round"/>'
                f'<path d="M318 92Q322 74 340 64M330 100Q330 82 350 70" fill="none" stroke="#140c1c" stroke-opacity=".25" stroke-width="2" stroke-linecap="round"/></g>'
                f'<path d="{cap_d}" fill="none" stroke="{INK}" stroke-width="2.8" stroke-linejoin="round"/>')
    # ear (near side) under the strap
    ear = (f'<ellipse cx="322" cy="104" rx="9" ry="11" style="fill:{SKIN}" stroke="{INK}" stroke-width="2.6"/>'
           f'<path d="M320 99q5 4 1 10" fill="none" stroke="{INK}" stroke-width="1.8" stroke-linecap="round" opacity=".7"/>')
    # ponytail: tie at the back of the head, streams back over the tank, wavy
    pt = [(302, 66), (284, 54), (262, 56), (244, 46), (226, 40), (214, 46), (228, 56), (240, 70), (258, 78), (276, 80), (292, 86)]
    pt_d = smooth(a.jit(pt, .4), t=.2)
    pclip = a.clip("pony", pt_d)
    ponytail = (f'<path d="{pt_d}" style="fill:{HAIR}"/><g clip-path="{pclip}"><rect x="205" y="30" width="105" height="62" fill="{hover}"/>'
                f'<path d="M294 70Q268 60 236 48" fill="none" stroke="#fff" stroke-opacity=".28" stroke-width="3" stroke-linecap="round"/></g>'
                f'<path d="{pt_d}" fill="none" stroke="{INK}" stroke-width="2.8" stroke-linejoin="round"/>'
                f'<path d="M266 72Q248 64 232 52" fill="none" stroke="{INK}" stroke-width="1.6" stroke-linecap="round" opacity=".55"/>'
                f'<ellipse cx="301" cy="77" rx="6" ry="8.5" fill="{GEAR}" stroke="{INK}" stroke-width="2.4"/>')
    # mask strap over the hair
    strap = f'<path d="M318 86Q312 80 300 86" fill="none" stroke="{STRAP}" stroke-width="7" stroke-linecap="round"/>'
    strap += f'<path d="M332 82Q326 78 316 84" fill="none" stroke="{STRAP}" stroke-width="7" stroke-linecap="round"/>'
    # face: eyes behind the lens, nose, smile, blush
    e_near, e_far = (356, 94), (383, 92)
    eyes = eye(e_near[0], e_near[1], 8.2, look=(.3, .06)) + eye(e_far[0], e_far[1], 6.8, look=(.3, .06))
    lids = lid(e_near[0], e_near[1], 8.2, SKIN_HEX) + lid(e_far[0], e_far[1], 6.8, SKIN_HEX)
    face = (blush(350, 118, 8, 4.6, .55) + blush(389, 116, 5, 3.4, .45) +
            f'<path d="M376 116q4 2 6 0" fill="none" stroke="{INK}" stroke-width="2.4" stroke-linecap="round"/>'
            f'<path d="M362 125Q371 132 381 126" fill="none" stroke="{INK}" stroke-width="2.6" stroke-linecap="round"/>')
    # nose bump on the profile edge
    nose = f'<path d="M391 101Q398 106 392 112" style="fill:{SKIN}" stroke="{INK}" stroke-width="2.4" stroke-linecap="round"/>'
    # mask: one lens over both eyes, frame
    lens = smooth([(336, 80), (366, 76), (396, 79), (401, 92), (396, 106), (370, 108), (340, 106), (333, 94)], t=.18)
    mask = (f'<path d="{lens}" fill="#bff0ff" fill-opacity=".38"/>'
            f'<path d="{lens}" fill="none" stroke="#eef7fa" stroke-width="7" stroke-linejoin="round"/>'
            f'<path d="{lens}" fill="none" stroke="{INK}" stroke-width="2.6" stroke-linejoin="round"/>'
            f'<path d="M343 84Q350 81 358 81" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" opacity=".9"/>'
            f'<path d="M390 84l4 6" stroke="#fff" stroke-width="2.4" stroke-linecap="round" opacity=".8"/>')
    # snorkel: mouthpiece at the corner of the mouth, tube rises behind the head
    snorkel_back = (f'<path d="M332 60Q330 40 338 22" fill="none" stroke="{INK}" stroke-width="13" stroke-linecap="round"/>'
                    f'<path d="M332 60Q330 40 338 22" fill="none" stroke="{GEAR}" stroke-width="8" stroke-linecap="round"/>'
                    f'<path d="M334 24l7 -4" stroke="{INK}" stroke-width="12" stroke-linecap="round"/><path d="M334 24l7 -4" stroke="#ff9f4a" stroke-width="7" stroke-linecap="round"/>')
    # headlamp on the strap, above the lens
    lamp_body = (f'<rect x="352" y="60" width="22" height="13" rx="5" fill="{GEAR}" stroke="{INK}" stroke-width="2.6"/>'
                 f'<ellipse cx="374" cy="66.5" rx="3.6" ry="5.4" fill="#fff8d8" stroke="{INK}" stroke-width="2"/>')
    lamp_g = a.radial("lampg", [(0, "#fff3c4", .95), (.35, "#fff3c4", .5), (1, "#fff3c4", 0)], user=(376, 66, 60))
    beam_g = a.linear("beam", [(0, "#fff3c4", .55), (1, "#fff3c4", 0)], 376, 66, 478, 66)
    lamp = (f'<path d="M376 62L478 18L478 128L376 72Z" fill="{beam_g}"/>'
            f'<circle cx="376" cy="66" r="60" fill="{lamp_g}"/>')

    head_inner = (snorkel_back + grp("hair", ponytail, (300, 77)) + head +
                  f'<path d="{head_d}" fill="none" stroke="{INK}" stroke-width="3"/>' +
                  face + nose + hair_cap + ear + strap + eyes + grp("lids", lids, (370, 93), ' opacity="0"') +
                  mask + lamp_body)
    head_grp = grp("head", head_inner + grp("lamp", lamp, (376, 66), ' opacity="0"'), (314, 120))

    # ------------------------------------------------------------- assemble
    anchors = ('<circle class="anchor-bubbles" cx="383" cy="128" r="4"/>'
               '<circle class="anchor-lamp" cx="376" cy="66" r="4"/>'
               '<circle class="anchor-hand" cx="346" cy="190" r="4"/>'
               '<circle class="anchor-net" cx="208" cy="168" r="4"/>'
               '<circle class="anchor-center" cx="250" cy="130" r="4"/>')
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" class="diver" viewBox="0 0 {W} {H}" data-pivot="250 130" '
           f'role="img" aria-label="Potápěčka"><title>Potápěčka</title><defs>{"".join(a.defs)}</defs>'
           + grp("leg-back", leg_back, hip_b)
           + grp("arm-back", arm_back, sh_b)
           + grp("body", body, (240, 132))
           + grp("leg-front", leg_front, hip_f)
           + head_grp
           + grp("arm-front", arm_front, sh_f)
           + f'<g class="anchors" fill="none" stroke="none">{anchors}</g></svg>\n')
    with open(os.path.join(OUT, "diver.svg"), "w") as fh:
        fh.write(svg)
    print("diver.svg", len(svg))


if __name__ == "__main__":
    build()
