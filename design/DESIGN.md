# Mořský svět — design spec

Designer · 2026-10-17 · Personal family surface, **outside the fleet registers** (no ph.json, no LIVE_REGISTER
row, no design-baseline compile, no ia_lint — per brief). Tokens-only discipline inside the app: every colour,
size and duration in `js/` and `css/app.css` comes from `design/tokens.css`. The art bakes its own hex values
(except the diver's `var(--hair)` / `var(--suit)` / `var(--skin)`).

**Verdict.** The sea is a picture book that gets deeper, darker and more magical page by page. Colour is the
depth gauge: sunlit turquoise → kelp gold-green → open blue → midnight with living light. Same craft as Houbičky
(warm ink, gouache volume, storybook faces), new light: rays, caustics, bubbles, marine snow, and in the deep a
warm headlamp against cold bioluminescence. Start with `comp-ponor-utes.png`, then `comp-ponor-hlubiny.png`
and `comp-card-keporkak.png`.

| File | What it is |
|---|---|
| `tokens.css` | palette by depth, group + look-only language, type, sizes, motion, reduced motion |
| `svgkit.py` | shared drawing kit (outline smoothing, gouache volume recipe, eyes, lids, smiles) |
| `build_creatures.py` | 20 creatures + `guide-turtle.svg` → `art/<id>.svg` |
| `build_diver.py` | the diver → `art/diver.svg` |
| `build_sea.py` | Ponor world, overlays, particles, trash, cleanup patches → `art/ponor/*`, `art/trash-*` |
| `build_ui.py` | icon sprite, app icon, home, Můj kousek moře (day/night), cross-section → `art/*` |
| `build_comps.py` + `shoot.py` | comps composed from the real art the way the engine should → `comp-*.png`, `contact-sheet.png`; HTML sources in `comps/` |

Rebuild everything: `cd design && python3 build_diver.py && python3 build_creatures.py && python3 build_sea.py && python3 build_ui.py && python3 build_comps.py`
(deterministic, stdlib only; `build_comps.py` needs Google Chrome for the screenshots).

---

## 0. Kontrakt pro programátora — změny

Everything in BRIEF §6 „Kresba“ holds exactly (class names, `data-pivot`, anchors, creatures face right, diver
parts, `var(--hair)` / `var(--suit)`). The following are **additions** — nothing was removed or renamed.

1. **Pivots are in viewBox units and nest.** Animatable groups are nested (`g.tail` is inside `g.body`), so a body
   bob carries the tail. Use `transform-box: view-box; transform-origin: <x>px <y>px` from `data-pivot`. The art
   must be **inlined** (not `<img>`) for CSS variables, classes and glow clones to work.
2. **`g.lids` is hidden by default** (`opacity="0"` attribute — any CSS rule wins). Blink = `opacity: 1` for `--t-blink`.
3. **`g.glow`**: hidden (`opacity="0"`) wherever it would be unwanted; **visible** (`opacity="1"`) on `das` (lure)
   and `svetluska` (rim lights). Breathe .55 ↔ 1 at `--t-glow` (≥ 1600 ms per cycle, never faster than 1 Hz).
   `dumbo` has no glow (it is not bioluminescent — fact, not omission).
4. **Root data attributes on creatures:** `data-span="x0 x1"` (nose-to-tail extent in viewBox units = real length,
   for size relations and the card's size bar), `data-floor="y"` on bottom-dwellers (`sasanka`, `hvezdice`, `krab`,
   `jezovka`: put this y on the seabed), `data-motion` (mirror of species.json, convenience only).
5. **Crab claws:** `krab` has `g.claw` (near/right) and `g.claw-2` (far/left) with pivots, plus `g.legs`. Wave a claw on tap.
6. **Sardinky:** one file, three fish. The main fish is in `g.body`; the two smaller ones are `g.fin-2` (bob them
   with a phase offset). Schools in Ponor use `art/ponor/school-fish.svg` (single fish), not this file.
7. **Guide turtle:** `art/guide-turtle.svg`, root `class="creature guide" data-id="zelva"` (tap → `zelva` card).
   Extra `g.mouth` (closed) and `g.mouth-talk` (`opacity="0"`): swap while she speaks (a mouth, not a flash).
8. **Diver:** one rig, two poses by transform (§6.2). Extra kotvy `circle.anchor-net` and `circle.anchor-center`.
   `g.lamp` (warm halo + beam) is `opacity="0"`; class `lamp-on` on any ancestor → `.lamp-on .lamp { opacity: 1 }`.
9. **Ponor tiles** carry stitch metadata (`data-in`, `data-out`, `data-floor-y`, `data-fill`), see §6.4.
   Transition tiles use `data-zone="utes/chaluhy"` (a `/`, never `>` — `>` inside an attribute breaks naive parsers).
10. **Near layer items** are `g.near-item` groups. Rule: **fade a near item to opacity .4 while its box overlaps the
    diver or any tappable target** (creature, trash). Near layers never take pointer events. (Shown in
    `comp-ponor-utes.png` over the bottle and `comp-ponor-chaluhy.png` over the diver.)
11. **Cleanup:** `art/ponor/patch-<zone>.svg` (utes, chaluhy, hlubiny) contain `g.bright` under `g.dull`. Cleanup =
    fade `g.dull` to 0 over `--t-cleanup` (opacity only, no CSS filter on large areas). Open ocean has no patch:
    cleanup there = a school of `school-fish.svg` arrives.
12. **Trash:** `art/trash-<id>.svg` (`lahev`, `sacek`, `plechovka`, `sit`), root `class="trash" data-id`, `g.body[data-pivot]`,
    `circle.anchor-center`. Trash never has a face.
13. **Scenes:** `home.svg` (`data-waterline`, `data-turtle="x y"` = where the guide peeks out), `my-sea-day.svg` /
    `my-sea-night.svg` (`data-floor-y` = crawl line), `cross-section.svg` (`g.band[data-zone][data-y0][data-y1]` =
    drop targets in viewBox units). All 1600 × 1000; home/cross-section use `xMidYMid slice`, my-sea `xMidYMax slice`.
    Sway groups in scenes are `g.sway[data-pivot]` (and `g.kelp` / `g.kelp-seg`).

## 1. Concept: „Obrázková kniha pod hladinou“

- **One idea:** *the deeper you swim, the more the light changes* — the page colour is the lesson „čím hlouběji, tím
  tma a zima“, felt before it is said.
- **Lineage** *[designer's choice]*: the same Czech storybook warmth as Houbičky (flat-but-painterly colour fields,
  inked shapes), moved under water. Underwater light comes from above, so every volume is **top-lit** (light top,
  cool shadow band at the bottom = bounce light from the water).
- **Ink:** warm aubergine `--ink #33243a` (cooler than Houbičky's umber so it sits on blue without going muddy),
  3 units on a ~240-unit character. Mid-plane art uses a water-tinted ink; far planes have no ink (atmospheric depth).
- **Faces:** every animal is a friend — round eyes with two highlights, a small closed smile, cheek blush. Nobody
  shows teeth: the anglerfish has a big *closed* smile, the parrotfish a smooth beak, sharks a soft closed mouth.
- **Restraint where it matters:** red is never used for a mistake and never for danger marks. Stinging/spiny/pinching
  animals get a calm amber hand („jen se díváme“). Glows are reserved for the deep and for living things.

## 2. Safety rules in the drawing (non-negotiable)

1. **Nothing scary.** No teeth, no attack poses, no dead animals, no blood, no wrecks. The deep is magical (glows,
   warm lamp), never threatening: outside the lamp circle you still see glows and silhouettes, never pitch black
   (`--deep-dim` is .86, not 1).
2. **Look, don't touch.** The diver's hand never reaches *onto* an animal; `anchor-hand` is for trash only.
   `touch != look` in species.json → the card shows the amber look-only box (`i-look-only`) with
   „Pozor, žahá / píchá / štípe — jen se díváme.“ (sasanka, medúza: žahá · ježovka: píchá · krab: štípe).
3. **Trash is clearly trash.** No faces, man-made colours (plastic blue cap, red can band, orange rope). Living
   things that might look like mesh were redrawn: the deep-sea glass sponges were first drawn with a lattice and read
   like the ghost net next to them, so they are now smooth vases (see §8).
4. **Nothing flashes faster than 1 Hz.** Bioluminescence breathes at `--t-glow` 2400 ms; reduced motion keeps glows
   steady.
5. **The adult line** „Pod vodu se potápíme jen s dospělým.“ sits on home (bottom-left pill with the parents icon)
   and on the end-of-dive screen (same pill).

## 3. Palette by depth (tokens.css)

| Zone | Water stops | Light | Signature |
|---|---|---|---|
| `utes` 0–30 m | `--utes-top #8fe3dc` → `--utes-low #239fb0` | rays .9, caustics .13 on the sand | coral pink/orange/violet/yellow/teal, sand |
| `chaluhy` 5–40 m | `--chaluhy-top #6fc3b4` → `--chaluhy-low #237479` | rays .6, no caustics | kelp gold `--kelp #c49a2c`, sand-grey rock, pink coralline |
| `sire-more` 0–200 m | `--sire-top #3a9fd6` → `--sire-low #164f8c` | rays .55 | no floor; whale far, school swirl, drifting plankton |
| `hlubiny` 200–4000 m | `--hlubiny-top #12305d` → `--hlubiny-low #08142e` | lamp only | `--glow-cyan/-violet/-green`, warm `--lamp` |

Zone identity colours (`--zone-*`) colour the depth-gauge bands, zone icons and chips. Group badges (`--grp-*`) pair
each colour with a silhouette glyph (shape first): ryba blue fish · savec orange whale with a spout („dýchá vzduch jako
my“) · plaz green turtle · korýš coral crab · měkkýš violet octopus · ostnokožec gold star · žahavec pink jelly.

## 4. Screens — light IA pass + layouts (1024 × 768 reference, verified also for 1180 × 820 and 16:10 by slice/anchoring)

Light IA (non-fleet, `ia_lint` not run, per brief). **App map (max depth 2):**
```
Loďka (home) ─► Ponor (core)  ─tap animal─► Kartička (overlay; flip = photo)
            ├─► Můj kousek moře ─hold animal─► Kartička
            ├─► Kvíz „Kdo jsem?“
            ├─► Kdo kde bydlí?   (lower priority; locked/hidden if not built)
            └─► Koutek pro rodiče (hold 3 s)
```
| Screen | Hero (one thing the eye lands on) | JTBD tier 1 / tier 2 | Named demotions |
|---|---|---|---|
| Loďka `comp-home` | the diver on the boat + „Ponořit se!“ pill | dive / open my sea, quiz, who-where | title is decoration; parents icon small and quiet |
| Ponor `comp-ponor-*` | the diver mid-screen | tap an animal or trash / swim on | HUD in a top band; depth gauge narrow at the left |
| Kartička `comp-card-*` | the big animal with pins 1–3 | hear the name, find the 3 features / size, photo, fact | Latin + EN small under the name; fact text short |
| Můj kousek moře `comp-my-sea-*` | her own animals swimming | drag/tap from the drawer / day–night | undiscovered = silhouettes, no counters |
| Kvíz `comp-quiz` | three big choice cards | answer by tapping / replay the riddle | progress = 5 bubbles, no score |
| Kdo kde bydlí? `comp-kdo-kde-bydli` | the 4-floor cross-section | drag animal → floor | zone names as small labels |

**Ponor HUD** (all from tokens): home 64 px top-left · silhouette bar centred (zone icon + 4–6 chips 64 px; found = full
colour + `--halo-found`, not found = black silhouette at .55) · speaker 88 px top-right · depth gauge 20 px wide at the
left (4 equal bands in `--zone-*`, a mask marker + „8 m“ pill) · back 64 px and net counter 64 px bottom-left · „Plav dál“
104 px bottom-right with the label under it · guide bubble near the turtle, never over the diver or the floor targets.
Gaps ≥ 12 px everywhere. The guide's speech bubble is a caption of what the voice says, with a speaker glyph.

**Card:** left — the animal fitted to 430 × 400 with numbered pins at `circle.anchor[data-look]`; under it the size box
(diver 115 cm and the animal in **one scale**, fitted by length *and* height; when the diver would be < 34 px she is
drawn tiny with a `--suit`-coloured ring so she can be found next to the whale) with the comparison icon
(`i-cmp-dlan/kocka/postel/auto/autobus/dum`, picked from `sizeSay`) and the „Víš, že…?“ fact. Right — name (hero size,
title size when longer than 11 characters), EN + Latin, three chips (group, zone, food), look-only box *or* the quiet
„Na zvířátka nesaháme, jen se díváme.“ line, „Poznáš mě podle…“ + the three lookFor rows. Buttons bottom-right:
speaker 88, photo 88, close 64.

## 5. Type

**Grandstander** (display 700/800) + **Andika** (text 400/700), self-hosted woff2 (@fontsource 5.3.0, SIL OFL 1.1,
licences in `fonts/`), `css/fonts.css`. Reused from Houbičky on purpose: (1) Andika's single-storey *a/g* are the
letterforms she will learn to read in Year 1 — the strongest reason, and it does not depend on the theme; (2) Czech
coverage of both was verified glyph by glyph there (č ď ě ň ř š ť ů ž, also in caps); (3) the sister games read as one
family. A rounder "aquatic" display face (Fredoka, Baloo 2) was considered and rejected: rounder is also more generic
kids-app, and the water is already carried by colour and light. (Downloading new fonts was not available in this
session either.) Sizes: `--fs-hero / -title / -label / -body / -small` (fluid, iPad-anchored).

## 6. Art contract (detail)

### 6.1 Creatures `art/<id>.svg`
```
svg.creature[data-id][data-span][data-motion][data-floor?] viewBox="0 0 W H"   (faces RIGHT)
  title, defs
  g.body[data-pivot]                     whole animal: bob / turn / squash
    g.fin-2[data-pivot]                  far fin / far arms / far wing (behind)          optional
    g.tail[data-pivot]                   tail, fluke, rear flippers                       optional
    g.tentacles[data-pivot]              tentacles, oral arms, webbed skirt               optional
    g.legs[data-pivot]                   legs (crab), tube feet (urchin), hind feet (otter) optional
    g.claw / g.claw-2[data-pivot]        crab only
    … body, markings, face …
    g.fin[data-pivot]                    near fin / flipper / wing / ears (dumbo)         optional
    g.lids[data-pivot] opacity=0
    g.glow[data-pivot] opacity=0|1
  g.anchors fill=none: circle.anchor[data-look=0|1|2] (pins = lookFor order), circle.anchor-center
```
Never `scale(-1)` an inner group; mirror the root only. ViewBoxes differ per animal (240–420 wide); in the scene the
game decides display sizes. Comp sizes (px at 1024 × 768) as a starting point: small 70–120 (klaun, koník, krab,
hvězdice, ježovka, ďas, dumbo, atolla) · medium 110–190 (chobotnice, ploskozubec, medúza, sasanka, želva, vydra) ·
large 230–560 (manta, tuleň, delfín, žralok; keporkak 560 in the far plane at opacity .55).

**21st species — `kapustnak` (kapustňák / manatee), added 2026-10-17 on the parent's request:** zone `utes`, level 1,
savec, `glide`. Round wrinkly grey-brown „mořská kráva“ with faint algae, `g.tail` (round paddle), `g.fin` / `g.fin-2`
(front flippers with three nails), `g.lids`, `data-span="4 344"`, `data-floor="172"` (rests on the seagrass). Pins:
0 = round paddle tail, 1 = whiskery snout / big upper lip, 2 = front flipper with nails. Its grazing spot: a seagrass
meadow (`g.sway.meadow`, mořská tráva) added to `utes-floor.svg` around x 1060–1200.

**Pins reconciled with `data/species.json` (2026-10-17):** every `data-look` sits on the feature its lookFor sentence
names — e.g. krab 2 = saw-toothed shell edge, dumbo 2 = bell-shaped body, vydra 2 = white whiskers, atolla 1 = the one
long tentacle, 2 = blue rim lights. Researcher decisions drawn as specified: *Linckia laevigata* (blue, sausage arms),
*Carcinus maenas* (green, toothed shell), *Hippocampus guttulatus* (mane filaments, white dots), *Heteractis magnifica*
(pale round tips, purple column), *Rhincodon typus*, *Atolla wyvillei* for `svetluska`.

### 6.2 Diver `art/diver.svg`
viewBox 0 0 480 240, swims to the right, head in a 3/4 turn (both eyes behind one mask lens), generic face, ponytail.
```
svg.diver[data-pivot="250 130"]
  g.leg-back[data-pivot]  g.arm-back[data-pivot]  g.body[data-pivot] > g.net[data-pivot]
  g.leg-front[data-pivot] g.head[data-pivot] > (g.hair[data-pivot], g.lids, g.lamp)   g.arm-front[data-pivot]
  g.anchors: anchor-bubbles (mouth), anchor-lamp, anchor-hand, anchor-net, anchor-center
```
**Skin tone (proposal, parent decides):** `--skin-options` = `#f6c9a5` light (default) · `#e8b48c` warm · `#c68863` tan ·
`#8d5a3f` deep. The diver's face and hands read `var(--skin)`; the cheek blush and ink stay the same on all four.
Colours: `style="fill:var(--suit, #ef6f6c)"`, `var(--hair, #6b4226)`, `var(--skin, #f6c9a5)`; shading is a neutral
white/aubergine overlay, so any colour from `--hair-options` / `--suit-options` keeps volume (checked in coral, blue,
violet; see §8). **Poses by transform (starting values, tune in the engine):**
- *Plave:* root rotate −4°…0°; `leg-front` and `leg-back` rotate −12° ↔ +14° in anti-phase at `--t-kick`; arms ±4°;
  `hair` ±6° at `--t-hair`; bubbles from `anchor-bubbles` every ~1.2 s.
- *Vznáší se:* root rotate −18°; legs +16° (dangling) with a lazy ±6° kick at `--t-kick-hover`; `arm-front` −20°
  (reaching forward); `head` looks around ±6° every 3–5 s.
- *Bere odpadek:* `arm-front` −35° toward the trash, the item tweens to `anchor-net` and the net swings (`g.net` ±10°).

### 6.3 Guide turtle `art/guide-turtle.svg`
Same contract as 6.1 (+ `g.mouth`, `g.mouth-talk`). Same species art as `zelva.svg` (she *is* the kareta in the album).

### 6.4 Ponor world `art/ponor/`
**Two kinds of layer.**
- **Screen layers** — `<zone>-far.svg`, `-mid.svg`, `-near.svg`: 2048 × 768, transparent, **seamless left/right**
  (items crossing an edge are drawn on both sides). Render at viewport height (width = 2048 × vh/768), repeat
  horizontally, offset `x = −camX × k mod W` with k = `--parallax-far .25 / -mid .55 / -near 1.25`. Vertically they
  are **anchored to the screen bottom** (the seabed slope lives in the floor plane, not here). Far = no ink, hazy;
  mid = water-tinted ink; near = sparse, bottom ~16 % (utes) / up to ~50 % (chaluhy kelp), `g.near-item` + fade rule.
- **Floor plane (world space)** — `<zone>-floor.svg` 2048 × 1024 and transitions. Stitch rule:
  `tile[k].x = k × 2048`, `tile[k+1].top = tile[k].top + tile[k].dataOut − tile[k+1].dataIn`. `data-floor-y` = 17
  samples of the floor line every 128 units (interpolate for crawlers, the diver's lowest y and trash placement). Below a
  tile, fill with `data-fill` (or nothing when `none`).

| Tile | in → out | Notes |
|---|---|---|
| `utes-floor.svg` | 560 → 680 | sand, ripples, corals, seagrass (`g.sway`), shells |
| `trans-utes-chaluhy.svg` | 560 → 820 | sand blends to rock, first kelp |
| `chaluhy-floor.svg` | 560 → 720 | rock, kelp stalks (`g.kelp` > `g.kelp-seg` nested sway), coralline |
| `trans-chaluhy-sire-more.svg` (2048 × 2048) | 560 → 980 | the reef wall drop-off; floor visible until x 1000, then falls into blue |
| `sire-more-floor.svg` | 560 → 780 | **empty**, `data-floor="none"`: a virtual descent line only |
| `trans-sire-more-hlubiny.svg` (2048 × 1536) | 560 → 680 | the deep floor rises into view from below |
| `hlubiny-floor.svg` | 560 → 650 | ooze, sea pens (`g.glow`), smooth glass-sponge vases, rocks, glowing specks |

Suggested run: utes ×3 · trans · chaluhy ×3 · trans · sire ×3 · trans · hlubiny ×3 (≈ 3–5 min at swim speed).
World y = 0 is the surface: place `surface-under.svg` (2048 × 220, `data-surface-y="110"`) with its top at y −110,
repeated. Kelp stalks to place freely: `kelp-1/2/3.svg` (root `data-pivot` = holdfast).

**Water + light.** Background = `linear-gradient(var(--<z>-top), var(--<z>-mid) 55%, var(--<z>-low))`, cross-faded over
`--t-zone-shift` when the camera centre passes the middle of a transition tile. `rays.svg` = screen overlay (1024 × 768,
each `g.ray` sways slowly at `--t-ray`), opacity utes .9 · chaluhy .6 · sire .55 · hlubiny 0. `caustics.svg` = 512
seamless tile: utes only, `background-size: 300px`, opacity .13, masked to the lower ~40 % of the screen, two copies
drifting at different speeds (`--t-caustic`).

**The deep.** Add `lamp-on` to the diver (`--t-lamp-on` fade). Darkness = one screen layer at `--z-dark`:
`radial-gradient(circle at <anchor-lamp + 60 px forward>, transparent 0, transparent calc(var(--lamp-radius) * .55),
var(--deep-dim) var(--lamp-radius))`. Living light stays visible above the darkness: render a **glow clone** of each
glowing thing above `--z-dark` (same transform; CSS hides everything in the clone except `.glow`) — the far layer
(entirely `g.glow`), `.glow` in mid/floor/near, creature `.glow`, the diver's `.lamp`. That is exactly how
`comp-ponor-hlubiny.png` is built (`build_comps.py`, `glowclone`). Marine snow = `snow.svg` particles drifting down.

**Particles:** `bubble.svg` (64), `plankton.svg`, `snow.svg`, `school-fish.svg` (60 × 27, faces right, `g.body`) —
canvas `drawImage` is fine.

### 6.5 Other art
`ui-icons.svg` — 60 symbols, 48 × 48, line glyphs in `currentColor` (flags coloured): navigation (`i-home`, `i-speaker`
= `i-repeat`, `i-close`, `i-swim-on`, `i-back`, `i-down`, `i-up`, `i-play`, `i-check`, `i-flip`, `i-photo`, `i-rotate`,
`i-hold`, `i-lock`, `i-lock-open`, `i-day`, `i-night`), doors (`i-collection`, `i-quiz`, `i-who-where`, `i-parents`),
game (`i-net`, `i-lamp`, `i-look-only`, `i-eye`, `i-air`, `i-depth`, `i-size`, `i-turtle`, `i-level-1/2`), groups
`i-grp-*`, zones `i-zone-*`, food `i-eats-*` (all nine `eats` values), size comparisons `i-cmp-*`, `i-flag-cs/en`.
`app-icon.svg` (1024 source: the diver over sunlit water). Scenes in §0.13.

## 7. Motion + reduced motion

Local response on tap 100–180 ms (`--t-react`): the animal turns toward her, waves its `fin`/`claw`/`tentacles`, puffs
3 bubbles. Celebration only at the end of a dive (`--t-celebrate` 800 ms). Idle loops all use `--ease-swim` with random
phase per instance: kelp/anemone/seagrass sway ±3–5° at `--t-sway-kelp` (each `kelp-seg` +1.5° more than its parent, 0.4 s
later), jellyfish bell squash 1 ↔ .9 at `--t-pulse-jelly`, octopus colour change (body opacity cross-fade to a sand-tinted
copy, 900 ms, then hides behind a rock), crab walks sideways along `data-floor-y`, seahorse hovers ±4 px, dumbo flaps
`fin`/`fin-2` ±12°, manta wings ±10° skewY, whale glides slowly in far *or* near plane, dolphin jumps at the surface
(arc over 1.4 s, splash = bubbles), glows breathe at `--t-glow`.

**Reduced motion** (`prefers-reduced-motion: reduce`, the tokens already switch): no parallax (all layers move as one
plane), no sway / rays / caustic drift / hair wave (`0ms` = do not loop), the diver glides without bobbing and kicks slowly
(`--t-kick` 2400 ms), animals move at half speed along their paths, jellyfish pulse at 4 s, glows steady, lamp and
zone colour change instantly, card and transitions without spring. Camera moves in short eased steps rather than
continuous follow.

## 8. Verification (sight loop, headless Chrome, 1024 × 768 @2×)

Each comp is composed from the real art files by `build_comps.py` (engine-equivalent placement) and was looked at.
What the screenshots showed and what was changed:
- **Diver:** first pass had adult proportions (long legs) and a surfboard-like tank → shorter legs, chunkier tank,
  fuller ponytail, arms reach forward-down. Checked in coral/brown, blue/blonde, violet/black + lamp on, blink, hover pose.
- **Creatures:** jellyfish rings first rendered as pretzels, then only two showed → four clear horseshoes; humpback was
  shark-thin with a stick fin → chunkier body, broad scalloped fin; anglerfish fin covered the mouth → moved back;
  otter read as lying on its belly → pale belly up, raised paws with the pebble; crab legs clipped the viewBox → wider
  canvas, legs fanned; manta had a seam band → wings meet the body without a stroke. Batch 1 then re-drawn to the
  researcher's species (blue *Linckia*, green shore crab with toothed shell, maned seahorse, ball urchin, white whiskers).
- **Ponor utes:** foreground coral hid the crab and the bottle → near layer lowered to the bottom ~16 % + fade rule;
  caustics read as a hex net → 300 px, .13, lower 40 % only; bubble moved off the diver and the floor.
- **Ponor chaluhy:** first camera put the diver *inside* the seabed → camera re-derived from the stitch rule; kelp blades
  read as bamboo leaves → long wavy ribbons with floats; mid kelp too dense → sparser and water-tinted; floor muddy →
  warm sand-grey with ripples; caustics removed (dark rock).
- **Ponor hlubiny:** sea-pen glow dots read as lupins → small dots + one soft halo; glass sponges read as mesh bins,
  confusable with the ghost-net trash → smooth vases; turtle moved into the lamp circle.
- **Home:** a full-height "wave lip" washed out everything under the waterline → a thin band; door row collided with the
  adult line → right-hand door column with paper labels; sun moved out from under the speaker.
- **Card:** the size bar had no height limit (diver 400 px, jellyfish invisible) → one scale fitted by length *and*
  height + tiny-diver ring; buttons overlapped pin 3 → fact moved left, long names at title size.
- **Cross-section:** `preserveAspectRatio="none"` distorted the art and the small boat broke → slice + scaled boat group.
- verified against screenshot at `design/comp-home.png`
- verified against screenshot at `design/comp-ponor-utes.png`
- verified against screenshot at `design/comp-ponor-chaluhy.png`
- verified against screenshot at `design/comp-ponor-sire-more.png`
- verified against screenshot at `design/comp-ponor-hlubiny.png`
- verified against screenshot at `design/comp-card-meduza.png`
- verified against screenshot at `design/comp-card-keporkak.png`
- verified against screenshot at `design/comp-my-sea-day.png`
- verified against screenshot at `design/comp-my-sea-night.png`
- verified against screenshot at `design/comp-quiz.png`
- verified against screenshot at `design/comp-kdo-kde-bydli.png`
- verified against screenshot at `design/contact-sheet.png` (incl. `kapustnak`; first pass was seal-slim → rounder body, bigger eye, broader nailed flipper)

**Not verified (unverified, stated):** motion (no real-time capture — comps are static states), the 1180 × 820 and
16:10 sizes as screenshots (layout relies on slice scenes + edge-anchored HUD; the programmer's e2e should shoot them),
and on-device iPad performance of the glow-clone approach.

## 9. Open questions
1. **Glow clones on iPad** (fallback approved by the coordinator): if cloning glowing groups above the darkness costs too much, fallback = put the three deep
   species and the floor glow group above `--z-dark` and give their bodies a dark tint while outside the lamp circle.
2. **Diver skin tone:** answered — yes; four swatches proposed in §6.2 (`--skin-options`), parent picks.
3. **Kdo kde bydlí?** art and comp exist; build only if time allows (brief §4.6).
