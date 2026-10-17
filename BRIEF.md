# Mořský svět — společný brief (kontrakt mezi agenty)

Veřejný repozitář (`pavel560/morsky-svet`, GitHub Pages `https://pavel560.github.io/morsky-svet/`):
**žádná jména, e-maily ani odkazy na soukromé repozitáře.** Hráč = „dítě (5,5–6 let, před 1. třídou,
čeština doma, angličtina ve škole, zatím nečte)“. Hraje se hlavně na iPadu na šířku (Safari, přidáno na
plochu), také na notebooku.

Sesterská hra: **Houbičky** (`https://pavel560.github.io/houbicky/`). Referenční kód je
v repozitáři `pavel560/houbicky`
(README, `design/DESIGN.md`, `design/DESIGN-v2.md`, `js/`, `sw.js`, `serve.py`, `fetch_photos.py`,
`make_voice.py`, `.github/workflows/`, `dev/e2e.mjs`, `tests/`). **Co jde převzít, převezmi** (předčítání,
zvuky, ukládání postupu, PWA a offline, rodičovský koutek, stahovač fotek, workflow Pages, e2e). Kvalita
kresby a pocitu ze hry má být minimálně na úrovni Houbiček (viz `design/comp-vyprava.png`).

## 1. Myšlenka hry

**Malá potápěčka pluje mořem, moře kolem ní žije, ona plave pořád dál a hlouběji a poznává, kdo tam bydlí.**

Jedna věta pro všechny: *moře se pod ní otevírá jako obrázková kniha — každé ponoření je o kousek hlubší,
tmavší a tajemnější, a co najde, to si odnese do svého vlastního kousku moře.*

Vzdělávací cíle (v tomto pořadí):
1. **Poznat a pojmenovat** ~20 mořských živočichů česky (a anglicky), podle 2–3 znaků.
2. **Moře má patra:** u hladiny je světlo a teplo, čím hlouběji, tím tma a zima; kdo bydlí kde
   (korálový útes → chaluhový les → širé moře → hlubiny). Hloubkoměr ukazuje metry.
3. **Kdo je ryba a kdo ne:** delfín, velryba, tuleň a vydra jsou savci a dýchají vzduch jako my (musí se
   vynořit); želva je plaz; chobotnice, krab, hvězdice, medúza nejsou ryby.
4. **Velikost:** od malého krabíka po velrybu větší než autobus — porovnání s potápěčkou.
5. **Ohleduplnost:** na zvířátka nesaháme, jen se díváme; odpadky do moře nepatří.

## 2. Zásady (nepřekročitelné)

- **„Pod vodu se potápíme jen s dospělým.“** Věta je v koutku pro rodiče, na konci každého ponoru a na
  úvodní obrazovce (jako „Houby sbíráme jen s dospělým“ v Houbičkách).
- **„Na zvířátka nesaháme, jen se díváme.“** Potápěčka zvířata nikdy nebere, nechytá, nekrmí. Ťuknutí na
  zvíře = podívat se zblízka (kartička), ne ho vzít. Žahavé a pichlavé druhy (medúza, sasanka, ježovka…)
  mají na kartičce značku „Pozor, žahá / píchá — jen se díváme“.
- **Jediné, co potápěčka bere do síťky, jsou odpadky** (lahev, sáček, plechovka, síť). Uklizené místo
  ožije (korál se rozzáří barvami, připlavou rybky). Nikdy smutné ani strašidelné (žádná uhynulá zvířata).
- **Nic děsivého.** Žraloci a ďas jsou přátelští a zvídaví, žádné cenění zubů, žádný útok, žádná krev.
  Hlubiny jsou tajemné a krásné (světélkování), ne strašidelné. Nic nebliká rychleji než 1× za sekundu.
- **Fakta ověřená z ≥ 2 seriózních zdrojů** (BioLib.cz / česká Wikipedie pro názvy; NOAA, Britannica,
  National Geographic, Smithsonian Ocean, Monterey Bay Aquarium, MarineBio pro fakta). Žádné mýty.
- **Prohrát nejde.** Žádné body, žádný odpočet času, žádné „špatně“. Chyba = vlídná nápověda, po druhé
  chybě se zúží výběr („ukaž mi“), ne že se rozsvítí správná odpověď.
- **Odměna je svět, který se mění** (z rodinného memu o hrách, revize Astry): ne konfety po každém klepnutí.
  Okamžitá odezva je lokální (zvíře se otočí, zamává ploutví, vypustí bublinky; 100–180 ms), oslava
  600–900 ms jen na konci ponoru. Samolepky nejsou trofeje v mřížce, ale **zvířátka, která si dítě samo
  vypustí do svého kousku moře** (viz § 4.4), kde pak plavou.
- **Hlas všude + krátký viditelný popisek.** Všechno, co hra říká, je v pevném katalogu vět `js/phrases.js`.
  Trvalé tlačítko „zopakuj“. Průvodkyně nepřekrývá plochu úlohy.
- **Ovládání:** aspoň 64 CSS px, hlavní akce 88 px, mezery ≥ 12 px. Přetahování vždy i jako „ťukni na
  předmět, pak na cíl“. iPad na výšku → výzva „Otoč iPad na šířku“.
- **Délka:** jeden ponor 3–5 minut. Po ~15 minutách hraní průvodkyně zívne a navrhne konec (až po
  dokončení rozdělané činnosti).
- `prefers-reduced-motion`: bez pohupování a bez rychlé paralaxy; zvířata se hýbou pomalu.

## 3. Postavy

- **Potápěčka** (hráčka): malá holčička v neoprenu s maskou, šnorchlem, ploutvemi a malou bombou na zádech,
  čelovkou na masce (rozsvítí se v hlubinách) a síťkou na odpadky u pasu. **Generická**, nepodobá se nikomu
  konkrétnímu. Vlasy v culíku, který se ve vodě vlní. Barvu vlasů a neoprenu si lze vybrat v koutku pro
  rodiče (CSS proměnné `--hair`, `--suit`, výchozí hnědé vlasy, korálově růžový neopren). Z pusy/šnorchlu
  stoupají bublinky. Plave z profilu (hlavou doprava), kope ploutvemi, při zastavení se vznáší a rozhlíží.
- **Průvodkyně: mořská želvička** (kareta), jako ježek v Houbičkách. Plave kousek za potápěčkou, mluví,
  napovídá, chválí, na konci ponoru projde, co jsme našli. Jméno jí dá dítě (rodič ho zapíše v koutku;
  výchozí oslovení „želvička“). Je zároveň druhem `zelva` ve sbírce (ťuknutí na ni otevře kartičku).

## 4. Obrazovky a hra

### 4.1 Úvod — „Loďka“ (domov)
Hladina moře se slunečním světlem, malá loďka, potápěčka sedí na okraji, želvička vykukuje z vody.
Velké tlačítko **„Ponořit se!“** (88 px+). Dále tři menší dveře: **Můj kousek moře** (sbírka), **Kvíz**,
**Kdo kde bydlí?** (pokud se stihne, jinak zamčené/skryté), ikona rodičů (viditelná, s rodičovskou zábranou:
podržet 3 s). První ťuknutí odemyká zvuk na iPadu (jako „Začneme?“).

### 4.2 Ponor — jádro hry (hlavní pozornost designu i programování)
Boční pohled (2D, „jako Mario“, jako Výprava do lesa), **potápěčka plave zleva doprava a mořské dno
postupně klesá**, takže čím dál pluje, tím je hlouběji. Svět je rozdělený do **4 pater (zón)**, každé má
vlastní kulisu, světlo a obyvatele:

| zóna id | název CZ / EN | hloubka (orientačně, výzkumník upřesní) | nálada |
|---|---|---|---|
| `utes` | Korálový útes / Coral reef | 0–20 m | sluníčko, tyrkysová voda, barevné korály, sluneční paprsky, třpyt na dně |
| `chaluhy` | Chaluhový les / Kelp forest | 5–30 m | vysoké zlatohnědé chaluhy, které se vlní, skály, zelenomodrá voda, tuleň a vydra u hladiny |
| `sire-more` | Širé moře / Open ocean | 0–200 m | hluboká modrá, žádné dno, paprsky shora, velcí plavci (velryba, žralok obrovský, manta), hejna |
| `hlubiny` | Hlubiny / The deep | 200–4000 m | skoro tma, rozsvítí se čelovka (kužel světla kolem potápěčky), světélkující tvorové, sníh z mořského „sněhu“ |

**Pohyb a ovládání**
- **Ťukni do vody → potápěčka tam připluje** (nahoru/dolů i dopředu; kamera ji sleduje). Velká šipka
  **„Plav dál“** vpravo dole: podržení = plave dopředu, ťuknutí = doplave k dalšímu zajímavému místu. Malá
  šipka zpět vlevo dole. Žádný joystick.
- Svět se kolem pořád hýbe: hejna rybek (jednoduché hejnové chování), chaluhy a sasanky se vlní, bublinky,
  sluneční paprsky a světelné „kaustiky“ na dně, plankton/mořský sníh, velryba v pozadí, delfín vyskočí
  u hladiny, krab chodí bokem po dně, chobotnice změní barvu a schová se, medúza pulzuje, koník se drží
  ocáskem řasy. Paralaxa ve 3–4 vrstvách.
- **Ťuknutí na zvíře:** zvíře zareaguje (otočí se, zamává, vypustí bublinky), řekne své jméno a potápěčka
  k němu připluje; otevře se **kartička** (§ 4.3). Zvířata se nikdy nedotýká.
- **Cíl zóny:** nahoře je lišta se **siluetami** obyvatel zóny (4–6). Najít = ťuknout a otevřít kartičku;
  silueta se vybarví. Když dítě najde aspoň 3, želvička řekne „Poplaveme hlouběji?“ a otevře se cesta dál
  (proud/šipka dolů). Zbylé siluety lze dohledat i později. Žádný časový tlak.
- **Odpadky:** 1–2 v každé zóně (lahev, sáček, plechovka, kus sítě). Ťuknutí → potápěčka je dá do síťky,
  místo se rozzáří (korál ožije, připlave hejno). Želvička: „Děkuju! Sáček vypadá jako medúza a želvy by ho
  mohly spolknout.“ (fakt ověří výzkumník).
- **Hlubiny:** obraz ztmavne, rozsvítí se čelovka (radiální maska kolem potápěčky) a světélkující tvorové
  září sami. Kouzelný moment, ne strach.
- **Hloubkoměr** na levém okraji: svislá stupnice 0 m → 4000 m s figurkou potápěčky a barevnými pásy pater;
  hlas občas řekne „Jsme 10 metrů pod hladinou.“ U zón i krátká věta „Čím hlouběji, tím je větší tma a
  zima.“
- **Konec ponoru:** vynořování (bublinky stoupají, světlo přibývá) zpět k loďce; želvička projde, koho
  jsme potkali (nové objevy se rozsvítí) a kolik odpadků jsme uklidili; věta „Pod vodu se potápíme jen
  s dospělým.“ Pak nabídka „Vypustit nové kamarády do mého kousku moře“.
- Jeden ponor ≈ 3–5 minut. Postup v zónách se pamatuje (další ponor může začít od útesu znovu, zóny jsou
  vždy dostupné od začátku — dítě jen plave dál; odemykání nevyžadujeme kromě „najdi 3“ v rámci ponoru).

### 4.3 Kartička zvířete
Overlay jako v Houbičkách: velká postavička vlevo s **očíslovanými piny** na 3 znacích („Poznáš mě
podle…“), vpravo:
- jméno (CZ velké, pod ním EN + latinsky malé);
- **skupina** (odznak: ryba · savec „dýchá vzduch jako my“ · plaz · korýš · měkkýš · ostnokožec ·
  žahavec — dětskými slovy, výzkumník navrhne přesné dětské pojmenování);
- **Kde bydlím** (ikonka zóny + hloubka) a **Co jím** (ikonka);
- **Jak jsem velký** — pruh s potápěčkou (dítě ~115 cm) a zvířetem ve stejném měřítku (u velryby se
  potápěčka zmenší na tečku, u krabíka zvíře na prst). Hlas: „Jsem velká jako autobus!“;
- **Víš, že…?** — jeden „wow“ fakt (hlasem; zobrazený krátce);
- u žahavých/pichlavých značka „Pozor, žahá — jen se díváme“;
- tlačítka: zopakuj (88 px), otočit na **skutečnou fotku** (Wikimedia Commons s autorem a licencí, jako
  Houbičky), zavřít.

### 4.4 Můj kousek moře (sbírka místo alba)
Scéna dítěte: prázdnější kousek útesu/vody (s pár řasami a kamenem). Objevená zvířata jsou v „šuplíku“
dole; dítě je přetáhne (nebo ťukne + ťukne) do scény, kde **začnou plavat** podle svého druhu (krab po dně,
medúza pulzuje, ryby plavou). Hlubinná zvířata ve scéně potřebují tmu: scénu lze přepnout den/noc
(v noci svítí). Ťuknutí na zvíře ve scéně = řekne jméno, podržení = otevře kartičku. Rozmístění se ukládá.
Nenalezená zvířata jsou v šuplíku jako siluety.

### 4.5 Kvíz „Kdo jsem?“ (mini-hra)
Hlas řekne jméno nebo hádanku („Mám osm chapadel a umím měnit barvu.“), dítě vybírá ze 3 zvířat. Kolo 5
otázek. Od úrovně 2 i otázka „Je to ryba?“ (ano/ne) a „Kdo je větší?“.

### 4.6 Kdo kde bydlí? (mini-hra, nižší priorita — jen pokud zbude čas)
Svislý řez mořem (4 patra). Dítě přetahuje 6 zvířat do správného patra. Chyba se vlídně opraví.

### 4.7 Koutek pro rodiče
Podržení ikony 3 s. Obsahuje: bezpečnostní věty, jazyk CZ/EN, rychlost hlasu, zvuky, jméno želvičky,
barva vlasů a neoprenu potápěčky, úroveň (1/2), autoři fotek, „Připraveno na cestu: X %“ (offline),
smazání postupu. Žádné skóre.

### 4.8 Úrovně
Úroveň 1 „Malá potápěčka“: ~10 nejznámějších zvířat, 3 piny, siluety jako nápověda. Úroveň 2
„Potápěčka“: všech ~20, kvíz s otázkami „Je to ryba?“ a „Kdo je větší?“. Přechod po objevení 10 zvířat
(oslava + želvička), rodič může odemknout ručně. Data: pole `"level": 1|2` v `data/species.json`.

## 5. Druhy — návrh (id jsou kontrakt; výzkumník smí vyměnit max. 3 druhy s písemným zdůvodněním v
`data/RESEARCH_NOTES.md` a hned to nahlásit designérovi i programátorovi úpravou tabulky v tomto souboru)

| id | česky (ověřeno; latinsky) | zóna | level | skupina | pohyb (`motion`) | piny `lookFor` 0 / 1 / 2 (pořadí je kontrakt) |
|---|---|---|---|---|---|---|
| `klaun` | Klaun očkatý (*Amphiprion ocellaris*) | utes | 1 | ryba | swim (drží se u sasanky) | oranžové tělo / tři bílé pruhy / černé lemy na ploutvích |
| `sasanka` | Sasanka velkolepá (*Radianthus magnifica*, dříve *Heteractis magnifica*) | utes | 2 | žahavec | sway (přisedlá) | spousta chapadel jako prstíky / světlejší kulaté špičky chapadel / pestrá nožka (sloupek), třeba fialová nebo modrá |
| `konik` | Koníček mořský (*Hippocampus guttulatus*) | utes | 1 | ryba | hover (svisle, ocásek kolem řasy) | hlava jako koník s trubičkovým čumáčkem / stočený ocásek / střapatá „hříva“ na hlavě a zádech |
| `hvezdice` | Hvězdice modrá (*Linckia laevigata*) | utes | 1 | ostnokožec | crawl (velmi pomalu po dně) | pět ramen / celá sytě modrá / ramena dlouhá a kulatá jako párečky |
| `krab` | Krab pobřežní (*Carcinus maenas*) | utes | 1 | korýš | crawl-side (bokem po dně) | dvě klepeta / kromě klepet osm nohou na chození / zubatý okraj krunýře jako pilka |
| `chobotnice` | Chobotnice pobřežní (*Octopus vulgaris*) | utes | 1 | měkkýš | jet (změna barvy, schová se) | osm chapadel / přísavky na chapadlech / měkké tělo jako balónek |
| `papousek` | Ploskozubec tupohlavý (*Chlorurus sordidus*) — „papouščí ryba“ | utes | 2 | ryba | swim | zobáček jako papoušek / velké šupiny s modrým lemem / dospělý sameček pestře zelenomodrý |
| `vydra` | Vydra mořská (*Enhydra lutris*) | chaluhy | **1** | savec | surface (plave na zádech u hladiny) | plave na zádech / hustý hnědý kožich / dlouhé bílé vousky |
| `tulen` | Tuleň obecný (*Phoca vitulina*) | chaluhy | **1** | savec | swim (vynořuje se nadechnout) | kulatá hlava bez ušních boltců / šedý kožich s tmavými skvrnkami / krátké přední ploutve s drápky |
| `jezovka` | Ježovka purpurová (*Strongylocentrotus purpuratus*) | chaluhy | 2 | ostnokožec | crawl | kulatá jako míček / ostny všude kolem / fialová barva |
| `meduza` | Talířovka ušatá (*Aurelia aurita*) | chaluhy | 1 | žahavec | pulse (drift) | průhledný zvon jako talíř / čtyři kroužky uvnitř jako čtyřlístek / krátká třásnitá chapadélka po okraji |
| `delfin` | Delfín skákavý (*Tursiops truncatus*) | sire-more | 1 | savec | swim + jump (u hladiny) | krátký zobáček / zahnutá ploutev na zádech / dýchací otvor na temeni |
| `zelva` | Kareta obecná (*Caretta caretta*) — průvodkyně | sire-more | 1 | plaz | glide | velká hlava / červenohnědý krunýř / ploutve místo nohou |
| `keporkak` | Keporkak (*Megaptera novaeangliae*) | sire-more | 1 | savec | glide (velmi pomalu, v pozadí i popředí) | obrovské dlouhé prsní ploutve / hrbolky na hlavě / dlouhé rýhy pod bradou |
| `zralok` | Žralok obrovský, též žralok velrybí (*Rhincodon typus*) | sire-more | 1 | ryba | glide | bílé tečky a proužky na tmavých zádech / široká tlama úplně vpředu / podélné hřebeny na bocích |
| `manta` | Manta obrovská (*Mobula birostris*) | sire-more | 2 | ryba | glide (mávání „křídly“) | ploutve jako trojúhelníková křídla / dva laloky u pusy jako rohy / tmavý hřbet se dvěma bílými skvrnami |
| `sardinky` | Sardinka obecná (*Sardina pilchardus*), hejno | sire-more | 2 | ryba | school | stříbřitě lesklé boky a bříško / zelenkavá záda / řada tmavých teček na boku |
| `das` | Hlubinný ďas (*Melanocetus johnsonii*, česky velkotlamec Johnsonův) | hlubiny | 1 | ryba | hover (svítící návnada) | svítící lampička nad pusou / velká pusa (bez cenění zubů) / kulaté tmavé tělo |
| `dumbo` | Chobotnice dumbo (rod *Grimpoteuthis*) | hlubiny | **1** | měkkýš | flap (ploutvičky jako uši) | dvě ploutvičky jako uši / chapadla spojená blánou jako sukýnka / měkké kulaté tělo jako zvoneček |
| `svetluska` | **Medúza atolla** (*Atolla wyvillei*) — hlubinná svítící medúza | hlubiny | **1** | žahavec | pulse (světélkuje) | tmavě červený zvon / jedno chapadlo mnohem delší než ostatní / modrá světýlka po okraji zvonu (`g.glow`) |
| `kapustnak` | Kapustňák širokonosý (*Trichechus manatus*) — přidán 17. 10. na přání rodiče | utes (teplé mělčiny s mořskou trávou, ne přímo útes) | 1 | savec | glide (velmi pomalu, vynořuje se nadechnout) | kulatý placatý ocas jako pádlo / štětinaté vousky na velkém horním pysku / malé nehty na předních ploutvích |

**Rozhodnutí výzkumníka (2026-10-17, zdůvodnění v `data/RESEARCH_NOTES.md`):** `zralok` = žralok obrovský
(*Rhincodon typus*) — pozor, česky je „žralok obrovský“ právě žralok velrybí; žralok veliký (*Cetorhinus*) je jiný
druh. `svetluska` = medúza atolla (žahavec, `pulse`), ne světlonoska: má volné živé fotky (NOAA), světelný
„poplach“ a dává hlubinám třetí skupinu (ryba · měkkýš · žahavec). Žádný druh nebyl vyměněn (všechny id platí),
jen upřesněny konkrétní druhy. Texty pinů platí doslovně tak, jak jsou v `data/species.json` (tabulka je jejich zkratka).

Úroveň 1 = 16 druhů (klaun, konik, hvezdice, krab, chobotnice, kapustnak, vydra, tulen, meduza, delfin, zelva,
keporkak, zralok, das, dumbo, svetluska); celkem 21 druhů. Rozložení do zón: v každé zóně aspoň 3 druhy úrovně 1 (útes 6, chaluhy 3,
širé moře 4, hlubiny 3) — původní návrh pravidlo porušoval (chaluhy i hlubiny měly jen 1), proto vydra, tuleň,
dumbo a atolla přešly do úrovně 1. Úroveň 2 přidá sasanku, ploskozubce, ježovku, mantu a sardinky.

Odpadky (id): `lahev`, `sacek`, `plechovka`, `sit`.

## 6. Datový kontrakt

### `data/species.json` (VÝZKUMNÍK)
Pole objektů, pořadí = pořadí v tabulce:
```json
{
  "id": "klaun",
  "zone": "utes",
  "level": 1,
  "group": "ryba",
  "name": {"cs": "Klaun očkatý", "en": "Clownfish"},
  "short": {"cs": "klaun", "en": "clownfish"},
  "latin": "Amphiprion ocellaris",
  "sizeCm": 11,
  "sizeSay": {"cs": "Jsem velký jako tvoje dlaň.", "en": "I am as big as your hand."},
  "depthM": [1, 15],
  "eats": "plankton|algae|fish|shellfish|jellyfish|squid|seagrass|krill|mixed",
  "eatsSay": {"cs": "…", "en": "…"},
  "lookFor": [{"cs": "…", "en": "…"}, {"cs": "…", "en": "…"}, {"cs": "…", "en": "…"}],
  "fact": {"cs": "…", "en": "…"},
  "breathesAir": false,
  "touch": "look|sting|spines|pinch",
  "safety": {"cs": "…", "en": "…"},
  "riddle": {"cs": "…", "en": "…"},
  "motion": "swim",
  "sources": ["https://…", "https://…"]
}
```
- Věty pro pětileté dítě: krátké (≤ 12 slov), konkrétní, srovnání s věcmi, které dítě zná (dlaň, kočka,
  postel, auto, autobus, dům). `lookFor[i]` odpovídá pinu `i` v kresbě (pořadí je kontrakt s designérem —
  výzkumník napíše znaky, designér je nakreslí; pokud výzkumník znaky změní, upraví i tento brief).
- `safety` jen u `touch != look`.
- Navíc `data/zones.json`: id, název CZ/EN, rozsah hloubky, 2 věty o zóně (světlo, teplota), sources.
- `data/trash.json`: id, název CZ/EN, věta želvičky CZ/EN (ověřený fakt), sources.
- `data/RESEARCH_NOTES.md`: zdroje, sporné body, co bylo zjednodušeno pro dítě a proč.
- `photos/manifest.json` ve formátu Houbiček (viz `fetch_photos.py` a `photos/manifest.json` v referenčním
  klonu): pro každý druh jeden dobrý, ostrý, dětsky vhodný snímek z Wikimedia Commons s volnou licencí
  (název souboru Commons + `alt`).

### Kresba (DESIGNÉR) — kontrakt pro programátora
- Generátory jako v Houbičkách: deterministický Python (stdlib) v `design/build_*.py` → `art/*.svg`.
- `art/<id>.svg` pro každý druh. Kořen `<svg class="creature" data-id="<id>" viewBox="…">`, zvíře
  **hledí doprava** (programátor zrcadlí `scaleX(-1)` pro plavání doleva). Pojmenované skupiny pro animaci:
  `g.body`, volitelně `g.tail`, `g.fin`, `g.fin-2`, `g.tentacles`, `g.legs`, `g.lids` (mrkání),
  `g.glow` (světélkování, jen hlubiny), každá animovatelná skupina má `data-pivot="x y"` (bod otáčení
  ve viewBox souřadnicích). Neviditelné kotvy: `circle.anchor[data-look="0|1|2"]` (piny, pořadí =
  `lookFor`), `circle.anchor-center`. Obličej: přátelské oči s odleskem, žádné cenění zubů.
- `art/diver.svg` (potápěčka z profilu, hledí doprava): skupiny `g.body`, `g.head`, `g.hair`
  (culík, `data-pivot`), `g.arm-front`, `g.arm-back`, `g.leg-front`, `g.leg-back` (ploutve, kopání),
  `g.lamp` (světlo čelovky, skryté mimo hlubiny), `g.net` (síťka); kotvy `circle.anchor-bubbles`,
  `circle.anchor-lamp`, `circle.anchor-hand`. Barvy vlasů a neoprenu přes `var(--hair)` a `var(--suit)`.
  Póza „vznáší se“ i „plave“ (buď dvě skupiny, nebo animace kopání nohou — designér popíše v DESIGN.md).
- `art/guide-turtle.svg` (želvička průvodkyně, stejný kontrakt jako zvířata: `g.fin`, `g.fin-2`, `g.lids`).
- Kulisy pro Ponor: `art/ponor/<zona>-far.svg`, `-mid.svg`, `-near.svg` (bezešvě navazující dlaždice nebo
  dlouhý pás; designér popíše šířky a jak navazují), dno, sluneční paprsky, kaustiky, bublinka, plankton,
  hejno (jedna rybka), přechod mezi zónami (dno klesá), loďka a hladina pro úvod/konec, scéna „Můj kousek
  moře“ (den i noc), řez mořem pro mini-hru „Kdo kde bydlí?“.
- `art/trash-<id>.svg` a `art/trash-<id>-clean.svg` není potřeba; „ožití“ místa řeší programátor (barvy,
  připlutí hejna), designér dodá jen variantu korálu `coral-dull` vs `coral-bright` (nebo CSS filtr — popíše).
- `art/ui-icons.svg`: sprite symbolů (domů, zopakuj, otočit, zavřít, plav dál, zpět, rodiče, sbírka,
  kvíz, kdo kde bydlí, odznaky skupin, ikony zón, ikony „co jím“, síťka, čelovka, žahá/píchá, zámek, den/noc,
  vlajky CZ/EN).
- `design/tokens.css`: paleta (patra moře od tyrkysové po půlnoční), písmo s plnou českou diakritikou
  (designér zvolí; Houbičky mají Grandstander + Andika ve `fonts/`, licence SIL OFL), velikosti, poloměry,
  stíny, pohyb. **Všechny barvy a rozměry v kódu jen přes tokeny.**
- `design/DESIGN.md` (koncept, IA, specifikace obrazovek a animací, kontrakt kresby) a náhledy
  `design/comp-*.png` v 1024×768 (úvod, ponor v každé zóně, kartička, můj kousek moře, kvíz).

## 7. Vlastnictví souborů (souběžná práce — nikdo nepíše do cizích souborů)
- **VÝZKUMNÍK:** `data/*`, `photos/manifest.json`, případné úpravy § 5 tohoto briefu (jen tabulka druhů).
- **DESIGNÉR:** `design/*`, `art/*`, `fonts/*`, `css/fonts.css`.
- **PROGRAMÁTOR:** vše ostatní: `index.html`, `js/`, `css/app.css`, `sw.js`, `manifest.webmanifest`,
  `icons/`, `serve.py`, `fetch_photos.py`, `make_voice.py`, `voice/`, `.github/workflows/`, `tests/`,
  `dev/`, `README.md`, `.gitignore`, `package.json`.
- **Nikdo necommituje** — commity a push dělá hlavní relace po každé fázi.

## 8. Technika (programátor)
- Statický web bez buildu (ES moduly), PWA, offline přes service worker, GitHub Pages
  (`.github/workflows/pages.yml`; fotky z Wikimedia stahuje CI jako u Houbiček).
- Ponor: SVG/DOM s CSS transformacemi a/nebo canvas 2D pro částice (bublinky, plankton, hejna); žádná 3D
  knihovna; plynulých 60 fps na iPadu (transform/opacity, `will-change`, žádné filtry na velkých plochách
  během pohybu). Kamera sleduje potápěčku.
- Hlas: katalog vět `js/phrases.js`; přehrává nahrávky z `voice/` (až budou), jinak hlas prohlížeče
  (jako `speech.js` v Houbičkách). Workflow pro nahrání hlasů (ElevenLabs, český hlas jako v Houbičkách)
  připravit, ale nahrávky se vytvoří až po přidání tajemství `ELEVENLABS_API_KEY` do repozitáře.
- Postup v `localStorage` (klíč `morsky-svet.v1`), záloha/obnova exportem v koutku pro rodiče.
- Testy: jednotkové (Python/Node) + e2e Playwright celé hry se snímky do `dev/screens/`.
