#!/usr/bin/env python3
"""Mořský svět — DEV-ONLY stand-ins (never deployed: pages.yml drops dev/).

Writes dev/placeholders/: species.json / zones.json / trash.json (shape = BRIEF §6, texts are obvious placeholders
until the researcher's data/*.json lands), ui-icons.svg (simple symbol sprite until art/ui-icons.svg lands) and
trash-<id>.svg. The app loads art/ and data/ first and only falls back to these.
"""
import json, os
HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "placeholders")
os.makedirs(HERE, exist_ok=True)
T = [  # id, cs, en, zone, level, group, motion, sizeCm, eats, touch
 ("klaun","Klaun očkatý","Clownfish","utes",1,"ryba","swim",11,"plankton","look"),
 ("sasanka","Sasanka","Sea anemone","utes",2,"žahavec","sway",30,"plankton","sting"),
 ("konik","Koníček mořský","Seahorse","utes",1,"ryba","hover",15,"plankton","look"),
 ("hvezdice","Hvězdice","Starfish","utes",1,"ostnokožec","crawl",25,"shellfish","look"),
 ("krab","Krab","Crab","utes",1,"korýš","crawl-side",20,"mixed","pinch"),
 ("chobotnice","Chobotnice pobřežní","Octopus","utes",1,"měkkýš","jet",60,"shellfish","look"),
 ("papousek","Ploskozubec","Parrotfish","utes",2,"ryba","swim",50,"algae","look"),
 ("vydra","Vydra mořská","Sea otter","chaluhy",2,"savec","surface",120,"shellfish","look"),
 ("tulen","Tuleň obecný","Harbour seal","chaluhy",2,"savec","swim",160,"fish","look"),
 ("jezovka","Ježovka","Sea urchin","chaluhy",2,"ostnokožec","crawl",10,"algae","spines"),
 ("meduza","Talířovka ušatá","Moon jellyfish","chaluhy",1,"žahavec","pulse",30,"plankton","sting"),
 ("delfin","Delfín skákavý","Bottlenose dolphin","sire-more",1,"savec","swim + jump",300,"fish","look"),
 ("zelva","Kareta obecná","Loggerhead turtle","sire-more",1,"plaz","glide",90,"jellyfish","look"),
 ("keporkak","Keporkak","Humpback whale","sire-more",1,"savec","glide",1500,"krill","look"),
 ("zralok","Žralok velrybí","Whale shark","sire-more",1,"ryba","glide",1200,"plankton","look"),
 ("manta","Manta obrovská","Giant manta ray","sire-more",2,"ryba","glide",500,"plankton","look"),
 ("sardinky","Sardinky","Sardines","sire-more",2,"ryba","school",20,"plankton","look"),
 ("das","Ďas","Anglerfish","hlubiny",1,"ryba","hover",20,"fish","look"),
 ("dumbo","Chobotnice dumbo","Dumbo octopus","hlubiny",2,"měkkýš","flap",20,"shellfish","look"),
 ("svetluska","Světlonoška","Lanternfish","hlubiny",2,"ryba","school",8,"plankton","look"),
]
sp = []
for (i, cs, en, z, lv, g, m, cm, eats, touch) in T:
    o = {"id": i, "zone": z, "level": lv, "group": g, "name": {"cs": cs, "en": en},
         "short": {"cs": cs.split()[0].lower() if i not in ("chobotnice", "sardinky") else {"chobotnice": "chobotnice", "sardinky": "sardinka"}[i], "en": en.split()[-1].lower()},
         "latin": "Placeholder placeholder", "sizeCm": cm,
         "sizeSay": {"cs": "[zástupný text] Jsem malý.", "en": "[placeholder] I am small."},
         "depthM": [1, 20], "eats": eats, "eatsSay": {"cs": "[zástupný text] Jím plankton.", "en": "[placeholder] I eat plankton."},
         "lookFor": [{"cs": f"[znak {k+1}]", "en": f"[feature {k+1}]"} for k in range(3)],
         "fact": {"cs": "[zástupný text] Zajímavost doplní výzkumník.", "en": "[placeholder] The researcher adds the fact."},
         "breathesAir": g in ("savec", "plaz"), "touch": touch,
         "riddle": {"cs": f"[hádanka] Kdo jsem? Jsem {cs.lower()}.", "en": f"[riddle] Who am I? I am a {en.lower()}."},
         "motion": m, "sources": []}
    if touch != "look":
        o["safety"] = {"cs": "[zástupný text] Pozor, jen se díváme.", "en": "[placeholder] Careful, we only look."}
    sp.append(o)
json.dump({"_note": "DEV PLACEHOLDER — replaced by data/species.json", "species": sp}, open(os.path.join(HERE, "species.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
zones = [{"id": z, "name": {"cs": cs, "en": en}, "depthM": d, "say": [{"cs": "[zástupný text o světle]", "en": "[placeholder about light]"}, {"cs": "[zástupný text o teplotě]", "en": "[placeholder about temperature]"}], "sources": []}
         for z, cs, en, d in [("utes", "Korálový útes", "Coral reef", [0, 20]), ("chaluhy", "Chaluhový les", "Kelp forest", [5, 30]), ("sire-more", "Širé moře", "Open ocean", [0, 200]), ("hlubiny", "Hlubiny", "The deep", [200, 4000])]]
json.dump({"_note": "DEV PLACEHOLDER", "zones": zones}, open(os.path.join(HERE, "zones.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
trash = [{"id": t, "name": {"cs": cs, "en": en}, "turtle": {"cs": f"[zástupný text] Děkuju! {cs} do moře nepatří.", "en": f"[placeholder] Thank you! A {en.lower()} does not belong in the sea."}, "sources": []}
         for t, cs, en in [("lahev", "Lahev", "Bottle"), ("sacek", "Sáček", "Bag"), ("plechovka", "Plechovka", "Can"), ("sit", "Síť", "Net")]]
json.dump({"_note": "DEV PLACEHOLDER", "trash": trash}, open(os.path.join(HERE, "trash.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# trash stand-ins (grey shapes, no colour literals needed beyond neutral greys — dev only)
shapes = {
 "lahev": '<rect x="34" y="20" width="22" height="56" rx="8" fill="#9fc7c9" stroke="#33243a" stroke-width="3"/><rect x="40" y="10" width="10" height="12" rx="2" fill="#7da" stroke="#33243a" stroke-width="3"/>',
 "sacek": '<path d="M25 25 Q45 10 65 25 L60 75 Q45 85 30 75 Z" fill="#eef" fill-opacity=".8" stroke="#33243a" stroke-width="3"/>',
 "plechovka": '<rect x="30" y="28" width="32" height="44" rx="5" fill="#c66" stroke="#33243a" stroke-width="3"/><ellipse cx="46" cy="28" rx="16" ry="5" fill="#ccc" stroke="#33243a" stroke-width="3"/>',
 "sit": '<path d="M15 40 L75 30 L80 70 L20 75 Z" fill="none" stroke="#33243a" stroke-width="3"/><path d="M30 38 L35 73 M47 35 L50 72 M63 32 L66 70 M17 55 L78 50" stroke="#33243a" stroke-width="2"/>',
}
for k, v in shapes.items():
    open(os.path.join(HERE, f"trash-{k}.svg"), "w").write(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 90 90" data-placeholder="1">{v}</svg>\n')

# icon sprite stand-in: 24×24 symbols, currentColor
P = {
 "play": '<path d="M7 4 L20 12 L7 20 Z"/>', "home": '<path d="M3 12 L12 3 L21 12 L18 12 L18 21 L6 21 L6 12 Z"/>',
 "speaker": '<path d="M3 9 H7 L12 4 V20 L7 15 H3 Z"/><path d="M15 8 Q19 12 15 16" fill="none" stroke="currentColor" stroke-width="2"/><path d="M17 5 Q23 12 17 19" fill="none" stroke="currentColor" stroke-width="2"/>',
 "parents": '<circle cx="8" cy="7" r="3"/><circle cx="16" cy="7" r="3"/><path d="M3 21 Q8 10 13 21 Z M11 21 Q16 10 21 21 Z"/>',
 "dive": '<path d="M12 3 V17" stroke="currentColor" stroke-width="3" fill="none"/><path d="M6 13 L12 20 L18 13 Z"/>',
 "collection": '<path d="M2 15 Q12 5 22 15 Q12 25 2 15 Z"/><circle cx="17" cy="13" r="1.5" fill="#fff"/>',
 "quiz": '<path d="M8 8 Q8 3 12 3 Q16 3 16 7 Q16 10 12 12 V15" fill="none" stroke="currentColor" stroke-width="3"/><circle cx="12" cy="20" r="2"/>',
 "habitat": '<rect x="3" y="3" width="18" height="4"/><rect x="3" y="9" width="18" height="4" opacity=".75"/><rect x="3" y="15" width="18" height="6" opacity=".5"/>',
 "rotate": '<rect x="6" y="2" width="12" height="20" rx="2" fill="none" stroke="currentColor" stroke-width="2"/><path d="M20 14 A8 8 0 0 1 12 22" fill="none" stroke="currentColor" stroke-width="2"/>',
 "close": '<path d="M5 5 L19 19 M19 5 L5 19" stroke="currentColor" stroke-width="3"/>',
 "photo": '<rect x="2" y="5" width="20" height="15" rx="2"/><circle cx="12" cy="12.5" r="4" fill="#fff"/>',
 "look-only": '<circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" stroke-width="2"/><path d="M9 17 V8 M12 17 V6 M15 17 V8" stroke="currentColor" stroke-width="2"/>',
 "flag-cs": '<rect x="2" y="5" width="20" height="7" fill="#fff"/><rect x="2" y="12" width="20" height="7" fill="#d7141a"/><path d="M2 5 L11 12 L2 19 Z" fill="#11457e"/>',
 "flag-en": '<rect x="2" y="5" width="20" height="14" fill="#012169"/><path d="M2 5 L22 19 M22 5 L2 19" stroke="#fff" stroke-width="3"/><path d="M12 5 V19 M2 12 H22" stroke="#fff" stroke-width="4"/><path d="M12 5 V19 M2 12 H22" stroke="#c8102e" stroke-width="2"/>',
 "fact": '<circle cx="12" cy="12" r="10"/><path d="M12 7 V13" stroke="#fff" stroke-width="3"/><circle cx="12" cy="17" r="1.6" fill="#fff"/>',
 "surface": '<path d="M12 21 V7" stroke="currentColor" stroke-width="3" fill="none"/><path d="M6 11 L12 4 L18 11 Z"/>',
 "arrow-left": '<path d="M15 4 L7 12 L15 20" fill="none" stroke="currentColor" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>',
 "arrow-right": '<path d="M9 4 L17 12 L9 20" fill="none" stroke="currentColor" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>',
 "arrow-up": '<path d="M4 15 L12 7 L20 15" fill="none" stroke="currentColor" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>',
 "arrow-down": '<path d="M4 9 L12 17 L20 9" fill="none" stroke="currentColor" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>',
 "net": '<path d="M4 4 H20 L17 20 H7 Z" fill="none" stroke="currentColor" stroke-width="2"/><path d="M8 4 L10 20 M16 4 L14 20 M5 10 H19 M6 15 H18" stroke="currentColor"/>',
 "day": '<circle cx="12" cy="12" r="5"/><path d="M12 1 V4 M12 20 V23 M1 12 H4 M20 12 H23 M4 4 L6 6 M18 18 L20 20 M4 20 L6 18 M18 6 L20 4" stroke="currentColor" stroke-width="2"/>',
 "night": '<path d="M15 3 A9 9 0 1 0 21 15 A7 7 0 1 1 15 3 Z"/>',
 "yes": '<circle cx="12" cy="12" r="11"/><path d="M6 12 L10 16 L18 8" fill="none" stroke="#fff" stroke-width="3"/>',
 "no": '<circle cx="12" cy="12" r="11"/><path d="M7 7 L17 17 M17 7 L7 17" stroke="#fff" stroke-width="3"/>',
}
for g in ["ryba", "savec", "plaz", "korys", "mekkys", "ostnokozec", "zahavec"]:
    P[f"grp-{g}"] = '<path d="M2 12 Q11 4 19 12 Q11 20 2 12 Z M19 12 L23 8 L23 16 Z"/>' if g == "ryba" else '<circle cx="12" cy="12" r="9"/>'
for z in ["utes", "chaluhy", "sire-more", "hlubiny"]:
    P[f"zone-{z}"] = '<path d="M2 8 Q7 4 12 8 Q17 12 22 8 V22 H2 Z"/>'
for e in ["plankton", "algae", "fish", "shellfish", "jellyfish", "squid", "seagrass", "krill", "mixed"]:
    P[f"eats-{e}"] = '<circle cx="7" cy="8" r="3"/><circle cx="16" cy="7" r="2"/><circle cx="12" cy="15" r="4"/>'
sym = "".join(f'<symbol id="i-{k}" viewBox="0 0 24 24">{v}</symbol>' for k, v in P.items())
open(os.path.join(HERE, "ui-icons.svg"), "w").write(f'<svg xmlns="http://www.w3.org/2000/svg" data-placeholder="1">{sym}</svg>\n')
print("dev/placeholders:", sorted(os.listdir(HERE)))
