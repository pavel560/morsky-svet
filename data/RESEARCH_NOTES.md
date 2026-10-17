# Mořský svět — poznámky výzkumníka

Stav k 17. 10. 2026. Soubory: `data/species.json` (21 druhů; kapustňák přidán 17. 10. na přání rodiče), `data/zones.json` (4 patra),
`data/trash.json` (4 odpadky), `photos/manifest.json` (20 fotek + náhradní). Úprava tabulky v `BRIEF.md` § 5.

## 1. Rozhodnutí v kostce

- **Žádný druh nebyl vyměněn.** Všech 20 id z briefu platí; jen jsem ke každému id určil konkrétní druh
  (latinské jméno), aby šla fakta ověřit (velikost, hloubka, potrava se liší druh od druhu).
- **`zralok` = žralok obrovský (*Rhincodon typus*), anglicky whale shark.** Pozor na češtinu: „žralok obrovský“
  je v AQUATABu i na české Wikipedii právě žralok velrybí; žralok veliký (*Cetorhinus maximus*) je jiný druh
  (basking shark). Proč tento: tropický planktonožravec, pro děti nejvlídnější vzhled (bílé tečky), velmi dobře
  zdokumentovaný, má na Commons fotku ve statusu Featured, a je to „největší ryba na světě“ — silný fakt.
- **`svetluska` = medúza atolla (*Atolla wyvillei*), skupina žahavec, pohyb `pulse`.** Proč ne světlonoska
  (lampovník, Myctophidae): volné fotky světlonosek na Commons jsou téměř výhradně mrtvé kusy z vlečných sítí
  nebo z trhu (porušuje zásadu „žádná uhynulá zvířata“), kdežto atolla má živou fotku NOAA. Atolla je vizuálně
  nejkouzelnější (temně červený zvon, modrý světelný „poplach“), fakta má z MBARI, Monterey Bay Aquarium, NOAA
  i Smithsonianu, a hlubiny tím mají tři různé skupiny (ryba, měkkýš, žahavec). Id `svetluska` zůstává jako
  kontrakt, i když zvíře není světluška ani světlonoska.
- **Úrovně:** původní tabulka porušovala vlastní pravidlo „v každé zóně aspoň 3 druhy úrovně 1“ (chaluhy a
  hlubiny měly po jednom). Do úrovně 1 jsem přesunul vydru, tuleně, chobotnici dumbo a atollu. Úroveň 1 má teď
  15 druhů, s kapustňákem 16 (útes 5 + kapustňák, chaluhy 3, širé moře 4, hlubiny 3), úroveň 2 přidává 5 (sasanka, ploskozubec, ježovka,
  manta, sardinky). Brief říká „~10 nejznámějších“ — kompromis je nutný kvůli pravidlu „najdi 3“ v každém patře.
- **Nová hodnota `eats` nebyla potřeba.** Chobotnice dumbo má `shellfish` (drobní korýši a červi ze dna),
  atolla `plankton` (drobní korýši), sasanka, hvězdice a krab `mixed`.

## 2. České názvy a jak byly ověřeny

BioLib.cz zapnul ochranu proti robotům (stránka „Bezpečnostní kontrola“), ochranu jsem neobcházel. Názvy jsem
proto ověřil v české Wikipedii (API), v databázi AQUATAB (český taxonomický katalog ryb, J. Plíštil), v českém
tezauru MeSH Národní lékařské knihovny a platnost latinských jmen ve WoRMS.

| id | název v datech | zdroj názvu | poznámka, jiné názvy |
|---|---|---|---|
| klaun | Klaun očkatý | cs Wikipedie, AQUATAB | |
| sasanka | Sasanka velkolepá | cs Wikipedie | WoRMS: platné jméno je nyní *Radianthus magnifica*, *Heteractis magnifica* je synonymum (v datech je nové jméno) |
| konik | Koníček mořský | cs Wikipedie (heslo *H. guttulatus*) | AQUATAB: koníček tečkovaný; též koníček skvrnitý, mořský koník |
| hvezdice | Hvězdice modrá | cs Wikipedie | |
| krab | Krab pobřežní | cs Wikipedie (hesla Zoea, Megalopa, Sacculina), MeSH | EU databáze obchodních názvů: krab obecný |
| chobotnice | Chobotnice pobřežní | cs Wikipedie | |
| papousek | Ploskozubec tupohlavý | cs Wikipedie, AQUATAB | lidově „papouščí ryba“ |
| vydra | Vydra mořská | cs Wikipedie | též kalan |
| tulen | Tuleň obecný | cs Wikipedie | |
| jezovka | Ježovka purpurová | cs Wikipedie (Aristotelova lucerna), MeSH | lidově mořský ježek |
| meduza | Talířovka ušatá | cs Wikipedie (Medúzovci, Rhopalium) | starší název medusa ušatá |
| delfin | Delfín skákavý | cs Wikipedie | |
| zelva | Kareta obecná | cs Wikipedie | |
| keporkak | Keporkak | cs Wikipedie | |
| zralok | Žralok obrovský | AQUATAB, cs Wikipedie | též žralok velrybí, nosozubec obrovský |
| manta | Manta obrovská | cs Wikipedie | AQUATAB uvádí „manta atlantská“; zvolen častější název |
| sardinky | Sardinka obecná | cs Wikipedie, AQUATAB | |
| das | Hlubinný ďas | popisný název | druh *Melanocetus johnsonii* se česky jmenuje velkotlamec Johnsonův (AQUATAB); patří do řádu ďasové (Lophiiformes), proto „ďas“ v širším smyslu. „Ďas“ v užším smyslu (rod *Lophius*) žije u dna a lampičku nemá |
| dumbo | Chobotnice dumbo | ČT24, běžný úzus | rod *Grimpoteuthis* nemá ustálené české jméno |
| svetluska | Medúza atolla | popisný název | rod *Atolla* nemá české jméno; patří do řádu korunovky (Coronatae). Hlas má číst „atola“ |

## 3. Dětské štítky skupin (odznak na kartičce)

| `group` | česky | anglicky |
|---|---|---|
| ryba | Ryba — dýchá pod vodou žábrami | Fish — breathes underwater with gills |
| savec | Savec — dýchá vzduch jako my | Mammal — breathes air like us |
| plaz | Plaz — dýchá vzduch a klade vajíčka | Reptile — breathes air and lays eggs |
| korys | Korýš — má tvrdý krunýř a spoustu nohou | Crustacean — hard shell and lots of legs |
| mekkys | Měkkýš — má měkké tělo bez kostí | Mollusc — soft body with no bones |
| ostnokozec | Ostnokožec — má ostnitou kůži | Echinoderm — spiny skin |
| zahavec | Žahavec — má chapadla, která žahají | Cnidarian — stinging tentacles |

Zjednodušení: žralok a manta jsou v české školní systematice **paryby** (chrupavčité ryby), ne „ryby“
v užším smyslu. Pro dítě je necháváme ve skupině ryba (dýchají žábrami, nikdy se nevynořují pro vzduch);
kvízová otázka „Je to ryba?“ u nich má odpověď ano. Kdyby se rodič ptal, je to vědomé zjednodušení.

## 4. Poznámka pro rodiče: cesta je pohádková, ne jedno skutečné místo

Korálové útesy rostou v teplých tropických mořích (23–29 °C, NOAA), chaluhové (kelpové) lesy ve studených
mořích bohatých na živiny (NOAA). Ve skutečnosti spolu nesousedí. Stejně tak klaun, sasanka, hvězdice modrá a
ploskozubec žijí v Indickém a Tichém oceánu, krab pobřežní, koníček mořský a sardinka u Evropy, vydra mořská a
ježovka purpurová u tichomořského pobřeží Severní Ameriky. Hra je obrázková kniha, která tato místa spojuje do
jedné cesty; patra (světlo nahoře, tma a zima dole) odpovídají skutečnosti. Pro dítě je v zóně chaluh věta
„Teď jsme doplavaly do studenějšího moře.“ (ženský rod: potápěčka a želvička).

## 5. Druhy — zdroje, sporné body, zjednodušení

Každý fakt má aspoň dva nezávislé zdroje; všechny URL jsou v poli `sources`. Stránky FishBase, SeaLifeBase,
NOAA Fisheries, Monterey Bay Aquarium, MBARI, Animal Diversity Web, MarLIN, National Geographic, NOAA Ocean
Service a Aquarium of the Pacific jsem četl přímo. Smithsonian Ocean a Britannica vracejí automatům chybu 403;
jejich tvrzení znám z vyhledávače, proto u nich vždy stojí ještě jiný přímo přečtený zdroj.

- **klaun** — 11 cm a 1–15 m (FishBase; NatGeo 4,3 palce). Sliz chrání před žahnutím (NatGeo); žije mezi
  žahavými chapadly (FishBase). Černé lemy pruhů a ploutví: Wikipedie (u *A. percula* jsou silnější).
- **sasanka** — průměr obvykle 30–50 cm (ADW), v datech 40 cm. Hloubka 1–50 m (ADW). Pomáhají si s klaunem:
  klaun ji čistí a brání (NatGeo), ADW ji vede jako vzájemného partnera *A. ocellaris*. Barevný sloupek:
  Wikipedie; kulaté světlejší špičky chapadel: ADW i Wikipedie.
- **konik** — 15 cm (cs Wikipedie; FishBase dospělí 8,5–18 cm), 0–30 m (FishBase). „Hříva“ z kožních
  výrůstků: FishBase. Tatínek nosí mláďata ve vaku: National Geographic a Wikipedie. Ve skutečnosti mezi
  řasami a mořskou trávou, ne na korálech (viz bod 4).
- **hvezdice** — do 30 cm, 0–60 m, vysouvá žaludek (ADW; Wikipedie 30 cm). Oko na konci každého ramena:
  Garm & Nilsson 2014 (Proc. R. Soc. B) zkoumali právě tento druh, plus National Geographic. Že hvězdice není
  ryba: NOAA Ocean Service.
- **krab** — krunýř do 8 cm, 0–60 m, všežravec, roste svlékáním (MarLIN). Pět párů nohou, první s klepety
  (cs Wikipedie Krabi). Zubatý okraj krunýře (5 zoubků za okem): Wikipedie. Chůze bokem: Britannica.
  Pin „oči na stopkách“ jsem nahradil zubatým okrajem — pro stopkaté oči jsem neměl dva zdroje přímo k druhu.
- **chobotnice** — 30–90 cm i s rameny (NatGeo), v datech 60 cm jako střed rozpětí. Obvykle 0–100 m
  (SeaLifeBase). Tři srdce a modrá krev: Natural History Museum (Londýn) a Wikipedie, Britannica stejně
  pro celou skupinu. Mění barvu: NatGeo.
- **papousek** — až 40 cm, 0–50 m, spásá řasy (FishBase; cs Wikipedie do 40 cm). Písek z korálů: NOAA
  (podcast o písku) a National Geographic. Barvy: pin 2 popisuje dospělého samce (terminální fáze); samice a
  mladí jsou tmaví s bílými tečkami — designér kreslí samce.
- **vydra** — do 1,2 m (Monterey Bay Aquarium). Potravu hledá obvykle do 20–25 m (USFWS), NPS 1,5–18 m.
  Nejhustší srst ze všech zvířat a žádný tuk: MBA (přes milion chlupů na čtvereční palec) a Wikipedie.
  Rozbíjení kamenem: MBA. Mýtus nepoužit: „vydry se při spánku drží za ruce“ — Seattle Aquarium uvádí, že
  se to stává jen zřídka; místo toho by šlo říct, že se zabalí do chaluhy (USFWS, NatGeo).
- **tulen** — 1,5–1,9 m (NOAA, MBA), v datech 170 cm. Většina ponorů do 20 m (ADF&G), v Arktidě průměr 41 m;
  v datech 0–50 m. Nemá ušní boltce: NOAA. Drápky na předních ploutvích: SeaWorld. Vousy cítí stopu ryby ve
  vodě: Natural History Museum a pokus Dehnhardt et al. (2001).
- **jezovka** — do 7 cm (MBA; SeaLifeBase 8,5 cm). Hloubka 0–161 m (SeaLifeBase), většinou do 10 m. Pět zubů
  (Aristotelova lucerna): MBA a cs Wikipedie. Bodá, ale není jedovatá — v `safety` jen „píchám“.
- **meduza** — obvykle 25–40 cm (Wikipedie; MBA až 60 cm, SeaLifeBase až 50 cm), v datech 25 cm. Hloubka:
  SeaLifeBase udává 0–1250 m, ale žije hlavně u hladiny v pobřežních vodách; v datech 0–200 m (sluneční patro).
  Žahnutí je pro člověka slabé (Wikipedie; NatGeo) — proto mírná věta „Žahám jen slabounce, ale stejně se jen
  díváme.“ Nemá mozek, srdce ani krev: NOAA a Natural History Museum (o „kostech“ NOAA nemluví, proto v textu
  nejsou). Čtyři kroužky jsou pohlavní žlázy viditelné přes zvon (Wikipedie, je to vidět i na vybrané fotce).
- **delfin** — 1,8–4 m (NOAA), v datech 300 cm. Běžně se potápí do 3–46 m (SeaWorld). Každý má svůj
  „podpisový“ hvizd jako jméno: PNAS 2006 (Janik, Sayigh, Wells) a PNAS 2013 (oslovování hvizdem).
  Dýchací otvor, krátký zobák, hákovitá hřbetní ploutev: Wikipedie, NOAA (krátký silný zobák).
- **zelva** — krunýř kolem 90 cm (Wikipedie; NOAA celková délka 2,5–3,5 stopy). Většina ponorů do 25 m (USGS,
  Mexický záliv), v datech 0–50 m. Velká hlava, červenohnědý krunýř, louská kraby a mlže: NOAA. Neumí
  schovat hlavu do krunýře: NOAA (10 Tremendous Turtle Facts) a Smithsonian Ocean. Fakt o sáčku je u odpadků.
- **keporkak** — 14–15 m (cs Wikipedie; NOAA až ~18 m). Hloubka: potravu hledá obvykle do ~80 m
  (Wikipedie), v datech 0–100 m. Zpívají samci; jedna píseň 4–33 minut (Wikipedie), zpěv trvá až přes 24 hodin
  (NPS) — proto „opakuje je i celé hodiny“. Hrbolky na hlavě a rýhy pod bradou: Wikipedie; dlouhé ploutve:
  NOAA, NPS (1/4–1/3 délky těla).
- **zralok** — dospělí průměrně 5,5–9,8 m (Georgia Aquarium), FishBase běžně 10 m; v datech 900 cm
  (konzervativně). Obvykle 0–100 m (FishBase). Největší ryba: Georgia Aquarium, Wikipedie, cs Wikipedie.
  Tři podélné hřebeny: Wikipedie; tečky a proužky: FishBase. Pro člověka neškodný (Georgia Aquarium).
- **manta** — `sizeCm` je **šířka** (rozpětí ploutví), ne délka: obvykle 4,5 m, max. 7 m (Wikipedie, NOAA).
  0–200 m (NOAA: potrava do 10 m, ponory 200–450 m). Laloky u tlamy navádějí vodu do pusy: NOAA. Skvrny na
  břiše jsou u každé jiné: NOAA, Manta Trust, Marine Megafauna Foundation. Pozor: manta má na ocase malý
  trn (NOAA „caudal thorn“), proto netvrdíme „nemá bodec“.
- **sardinky** — běžně 20 cm, 10–100 m, plankton (FishBase). Barvy a řada tmavých teček: FAO. Hejno chrání:
  NOAA Fishery Bulletin (Major 1977) a National Geographic (pokusy s virtuální kořistí). Data jsou psaná
  v množném čísle („Kdo jsme?“) kromě velikosti (jedna rybka).
- **das** — samice do 18 cm, samci jen do 3 cm (FishBase); obvykle 100–1500 m. Lampičku mají jen samice;
  světlo dělají bakterie v návnadě: Smithsonian Ocean, MBARI, studie v PMC (genom symbiontů). Zjednodušení:
  texty jsou v mužském rodě („ďas“), ač mluví samice; dítěti to nevadí, rodiči to říkám tady.
- **dumbo** — většina druhů 20–30 cm (Aquarium of the Pacific; NatGeo kolem 20 cm). Obvykle 1000–4000 m
  (hloubkoměr hry končí na 4000 m), rekord 6957 m v Jávském příkopu 2020 (ČT24, Wikipedie). Nejhlouběji
  žijící chobotnice: Aquarium of the Pacific a Wikipedie. Polyká kořist celou: AoP. Pin „velké oči“ jsem
  vyřadil — zdroje se rozcházejí (AoP: „téměř slepé oči“).
- **svetluska (atolla)** — zvon do 15 cm, 500–5000 m (MBARI; MBA 200–4000 m), v datech 500–4000 m. Červená
  barva je v hlubinách neviditelná (MBARI). Jedno dlouhé chapadlo až 6× delší než průměr zvonu (MBARI,
  Wikipedie). Modrý „poplach“: MBARI, Smithsonian, NOAA (podle něj vznikla návnada e-jelly, která v roce 2012
  přilákala krakatici obrovskou). Že tím „volá o pomoc“, je **hypotéza** vědců — proto věta „Vědci si myslí,
  že volám o pomoc.“ Nebezpečnost pro člověka nikde uvedena není, `touch` je `look`.

- **kapustnak (přidán 17. 10.)** — kapustňák širokonosý (*Trichechus manatus*; název cs Wikipedie, WoRMS
  platné jméno). **Nežije na korálovém útesu**, ale v teplých mělčinách, lagunách, ústích řek a v řekách
  s mořskou trávou (USFWS: mořské, brakické i sladké vody; pod ~20 °C dlouho nevydrží). Ve hře patří k útesu
  jen jako „teplá mělčina“ — stejné pohádkové zjednodušení jako v bodě 4. Délka obvykle 2,7–3 m (USFWS
  9–10 stop), v datech 300 cm. Hloubka 1–5 m: nejraději 1–2 m, ponory zřídka přes 5 m (Save the Manatee
  Club, USGS). Pádlovitý ocas (USFWS, NOAA), velký chápavý horní pysk s vousky (NOAA; USFWS „štětiny kolem
  čenichu“), 3–4 nehty na ploutvích (NOAA, NPS) — pozor, platí pro kapustňáka širokonosého, kapustňák
  jihoamerický nehty nemá. Přezdívka „mořská kráva“ kvůli spásání (USFWS). Příbuzný slona: NOAA
  („closest living relative is actually the elephant“); Save the Manatee jmenuje i daman — proto
  v datech opatrně „vzdálený příbuzný slona“. Vynořuje se každé 3–5 minut, v klidu vydrží až 20 minut
  (USFWS, NPS, FWC) — využito v hádance. Sní 10–15 % své hmotnosti denně (USFWS do 10 %, NOAA 10–15 %);
  v textu bez čísla.

## 6. Zóny (`data/zones.json`)

Rozsahy: útes 0–30 m (korálům stačí světlo asi do 30 m, NOAA), chaluhy 5–40 m (kelpové lesy zřídka hlouběji
než 15–40 m, NOAA), širé moře 0–200 m (sluneční patro, NOAA), hlubiny 200–4000 m (soumrak 200–1000 m, půlnoční
patro 1000–4000 m, kolem 4 °C — „jako v lednici“, NOAA). Že si většina zvířat v hlubinách svítí sama: NOAA
Ocean Exploration (80 % živočichů mezi 200 a 1000 m). Chaluha za den vyroste až o 45 cm (NOAA) či 60 cm
(Monterey Bay Aquarium) → „umí vyrůst skoro o délku tvé ruky“.

Pole navíc proti briefu: `say` (2 věty: světlo, teplota), `who` (kdo tu bydlí), u chaluh `extra` (věta
o růstu), u útesu a hlubin `tempC`. Programátor je může ignorovat.

## 7. Odpadky (`data/trash.json`)

- **sacek** — želvy nejčastěji polykají fólie a sáčky, které připomínají medúzy (NOAA Marine Debris Program,
  NOAA o karetě). Novější výzkum dodává, že želvy láká i vůně obrostlého plastu, takže „podobá se medúze“
  je jen část pravdy — pro dítě postačí.
- **lahev** — plast se v moři rozpadá na mikroplasty a zvířata je mohou spolknout (NOAA). Číslo „450 let“
  záměrně nepoužívám, je to jen odhad.
- **plechovka** — hliník se dá recyklovat znovu a znovu, z plechovky je nová plechovka (Aluminum Association;
  zdroj je oborový svaz, fakt sám je technicky nesporný).
- **sit** — ztracené sítě dál chytají zvířata („ghost fishing“, NOAA). Věta je jemná: „mohla by se zamotat“.

## 8. Fotky (`photos/manifest.json`)

Formát je stejný jako v Houbičkách (`photos[]` s `id`, `commonsFile`, `author`, `license`, `licenseUrl`,
`sourcePage`, `verified`, `evidence`, `alt[]`, `altNote`). Všech 44 souborů (21 hlavních + 23 náhradních) jsem
ověřil přes Commons API. Všechny hlavní fotky jsem prohlédl v náhledu (`verified: true`). Pravidla výběru:
nikdo zvíře nedrží ani se ho nedotýká, žádná mrtvá zvířata, žádné jídlo. Výjimky a slabá místa:
- **das**: živá volná fotka tohoto druhu neexistuje; použit **model** z Natural History Museum v Londýně
  (je vidět pár drobných zoubků). Fotka NOAA je mrtvý kus z vlečné sítě — vyřazena.
- **svetluska**: jediná volná živá fotka má šířku jen 600 px.
- **zralok**: zvolena fotka z Georgia Aquarium (celé zvíře z boku, pod ním siluety lidí, takže je dobře vidět
  velikost); divoká noční fotka s otevřenou tlamou je jen náhradní.

## 9. Co musí vědět designér a programátor

1. **Změněné piny proti původní tabulce:** krab (3. pin je zubatý okraj krunýře, ne stopkaté oči),
   dumbo (3. pin je měkké kulaté tělo, ne velké oči), sardinky (stříbřité boky a bříško, zelenkavá záda),
   manta (dvě bílé skvrny na tmavém hřbetě), ploskozubec (barvy samce). Tabulka v briefu je aktualizovaná.
2. **`species.json` je pole** (podle briefu); `fetch_photos.py` v tomto repozitáři už pole i slovník
   `{"species": [...]}` zvládá (ověřeno 17. 10.).
3. `sizeCm` u manty je šířka; u sasanky průměr; u hvězdice rozpětí; u medúz průměr zvonu.
4. `depthM` u dumba je 1000–4000 (hloubkoměr končí na 4000).
5. Věty jsou ≤ 12 slov na větu (kontrolováno skriptem); `riddle` má dvě věty. Čeština prošla `cz_lint`
   (0 tvrdých nálezů; měkké nálezy jsou latinská a odborná jména).

## 10. Nejistoty, které zůstávají

- „Typická“ velikost a hloubka: kde zdroje dávají jen maximum nebo rozpětí, uvádím konzervativní hodnotu
  a píšu ji výše (chobotnice 60 cm jako střed rozpětí, ploskozubec 40 cm je maximum, žralok 9 m).
- Hloubky savců a želvy jsou „kde je běžně potkáte“, ne rekordy.
- Hřbetní kresba manty obrovské (bílé skvrny ve tvaru T) je podle Wikipedie; NOAA ji popisuje jen jako
  „chevron“ zbarvení — rozdíl je jen v detailu.
