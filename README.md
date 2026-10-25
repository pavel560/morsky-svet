# Mořský svět

Hra pro děti před první třídou: malá potápěčka plave mořem, moře kolem ní žije a ona poznává, kdo kde bydlí, česky i anglicky a s předčítáním nahlas. Sesterská hra Houbiček. Statický web bez instalace, na Macu stačí Python 3.

**Pod vodu se potápíme jen s dospělým. Na zvířátka nesaháme, jen se díváme.**

## Co ve hře je

- **Loďka** (úvod): hladina, loďka, potápěčka a želvička. První klepnutí na „Začneme?“ zapne zvuk (iPad to vyžaduje). Velké tlačítko **Ponořit se!**, pod ním tři dveře: Můj kousek moře, Kvíz a Kdo kde bydlí?
- **Ponor** (jádro hry): pohled z boku, potápěčka plave zleva doprava a dno klesá přes čtyři patra moře: korálový útes, chaluhový les, širé moře a hlubiny.
  - Klepnutí do vody: potápěčka tam připlave. Prstem se dá i vést. Velká šipka **Plav dál**: podržením plave dopředu, klepnutím doplave k dalšímu zajímavému místu. Malá šipka vlevo dole vrací zpět. Na notebooku fungují i šipky na klávesnici.
  - Nahoře je lišta se siluetami obyvatel patra. Klepnutí na zvíře: zvíře se otočí a vypustí bublinky, řekne své jméno, potápěčka k němu připlave (nikdy se ho nedotkne) a otevře se kartička. Silueta se vybarví. Po třech nalezených želvička řekne „Poplaveme hlouběji?“ a proud na konci patra zmizí.
  - Odpadky (lahev, sáček, plechovka, síť) jdou do síťky. Místo se rozzáří a připlave hejno rybek. Želvička řekne, proč odpadky do moře nepatří.
  - Hloubkoměr vlevo ukazuje metry (0 až 4000 m). V hlubinách se setmí, rozsvítí se čelovka a hlubinní tvorové světélkují.
  - Šipka nahoru vlevo nahoře ukončí ponor: vynořování, přehled, koho jsme potkaly a kolik odpadků jsme uklidily, bezpečnostní věta a nabídka „Vypustit kamarády“.
- **Kartička**: kresba s očíslovanými znaky (klepnutím je hra přečte), skupina (ryba, savec „dýchá vzduch jako my“, plaz…), kde zvíře bydlí a v jaké hloubce, co jí, pruh „Jak jsem velký“ (zvíře a potápěčka 115 cm ve stejném měřítku), „Víš, že…?“, u žahavých a pichlavých druhů značka „jen se díváme“. Tlačítko s fotoaparátem otočí kartičku na skutečnou fotku s autorem a licencí.
- **Můj kousek moře**: objevená zvířata jsou v šuplíku dole (neobjevená jako siluety). Přetažením, nebo klepnutím na zvíře a pak do vody, je dítě vypustí a ona tam plavou podle svého druhu (krab bokem po dně, medúza pulzuje). Den a noc: v noci hlubinná zvířata svítí. Klepnutí na zvíře = řekne jméno, podržení = kartička. Rozmístění se ukládá.
- **Kvíz „Kdo jsem?“**: pět otázek, hlas řekne jméno nebo hádanku, dítě vybírá ze tří zvířat. Na úrovni 2 přibydou otázky „Je to ryba?“ a „Kdo je větší?“. Po první chybě vlídná nápověda, po druhé se výběr zúží. Body ani „špatně“ nejsou.
- **Kdo kde bydlí?**: řez mořem se čtyřmi patry, dítě přesune šest zvířat do jejich patra (přetažením i klepnutím).
- **Koutek pro rodiče**: otevře se podržením ikony vlevo nahoře na 3 sekundy. Bezpečnostní věty, úroveň, jazyk, rychlost hlasu, zvuky, jméno želvičky (jen se zobrazuje, hlas ho neříká), barva vlasů, neoprenu a pleti potápěčky, stav „Připraveno na cestu“ (offline), autoři fotek, záloha a obnova postupu a smazání postupu.

Po zhruba 15 minutách hraní želvička zívne a navrhne pauzu, ale až po dokončení rozdělané činnosti. Na iPadu na výšku se zobrazí výzva „Otoč iPad na šířku“. Při zapnutém omezení pohybu v systému se nic nepohupuje a pozadí se neposouvá v různých rychlostech.

## Úrovně

| Úroveň | Název | Zvířata | Kvíz |
|---|---|---|---|
| 1 | Malá potápěčka | v každém patře zvířata úrovně 1 (`"level": 1` v `data/species.json`), doplněná do tří | jméno nebo hádanka, výběr ze tří |
| 2 | Potápěčka | všechna | navíc „Je to ryba?“ a „Kdo je větší?“ |

Úroveň 2 se zapne sama po objevení 10 zvířat (želvička to oslaví). Rodič ji může přepnout ručně.

## Spuštění na Macu

**Dvojklikem:** ve Finderu dvakrát klikněte na `start.command`. Otevře se Terminál se serverem a prohlížeč s hrou. Když se macOS zeptá, zda smí Python přijímat příchozí spojení, zvolte **Povolit** (jinak se iPad nepřipojí). Pokud macOS soubor odmítne otevřít, povolte ho v **Nastavení systému → Soukromí a zabezpečení → Přesto otevřít**, nebo jednou v Terminálu spusťte `xattr -d com.apple.quarantine start.command`.

**Z Terminálu:**

```bash
git clone https://github.com/pavel560/morsky-svet ~/morsky-svet-hra   # jen poprvé
cd ~/morsky-svet-hra
python3 fetch_photos.py     # jen poprvé: stáhne fotky z Wikimedia Commons
python3 serve.py            # port 8642
python3 serve.py --port 9000 --open
```

Server vypíše adresu pro tento počítač (`http://localhost:8642/`) a adresu pro iPad ve stejné Wi-Fi (například `http://192.168.1.23:8642/`). Přes obyčejné `http://` z jiného zařízení hra funguje, ale offline režim (service worker) prohlížeč povolí jen na `https://` nebo `localhost`.

**Nejjednodušší je hrát z webu:** https://pavel560.github.io/morsky-svet/. Na iPadu v Safari: Sdílet → Přidat na plochu. Po prvním načtení počkejte v Koutku pro rodiče na „Připraveno na cestu: 100 %“, pak hra funguje i bez internetu (třeba v autě).

## Hlas

Každá věta, kterou hra říká, je v pevném katalogu `js/phrases.js` (česky i anglicky). Hra přehrává nahrávky z `voice/` a kde nahrávka chybí, použije hlas prohlížeče. Bez hlasu prohlížeče se věta aspoň zobrazí v bublině dole.

Nahrávky smějí pocházet jen ze služeb, které dovolují komerční užití. Hlas pro každý jazyk určuje `voice/config.json`:

- `"provider": "elevenlabs"` (čeština, hlas „Candy - Young and Sweet“ z knihovny hlasů ElevenLabs): nahrává se jen na placeném tarifu. Klíč je v tajemství repozitáře `ELEVENLABS_API_KEY` (celý klíč `sk_…`).
- `"provider": "azure"` (angličtina, hlas `en-GB-MaisieNeural` z Azure AI Speech): klíč je v tajemství `AZURE_SPEECH_KEY`, oblast v proměnné repozitáře `AZURE_SPEECH_REGION` (například `westeurope`).

Bezplatné hlasy Microsoft Edge (edge-tts) se nepoužívají, protože je Microsoft pro komerční užití nelicencuje.

**Evidence licence:** `voice/index.json` u každé nahrávky uvádí službu (`provider`), licenci (`licence`) a čas nahrání (`recorded`, UTC); `voice/config.json` u jazyka uvádí tarif a začátek licence (`licence.since`). Příkaz `python3 make_voice.py --audit` vypíše, které věty ještě nejsou nahrané licencovanou službou a kolik znaků by přenahrání stálo. Spouští ho workflow „Record voices“ (bez nálezu skončí zeleně) i nasazení stránky (jen upozorní). Doklad o tarifu (fakturu) vede provozovatel mimo tento veřejný repozitář.

**Přenahrání:** Actions → Record voices → Run workflow. Volba `force` přenahraje celý jazyk i bez změny (`en`, `cs`, `all`); bez ní se nahrají jen nové, změněné a nelicencované věty. Workflow nahrávky commitne a stránku znovu nasadí. Jazyk se přepne jen tehdy, když se podaří nahrát všechny jeho věty, takže se ve hře nikdy nemíchají dva hlasy. U ElevenLabs workflow předem ověří, že zbývá dost kreditů; jinak nenahraje nic. Jazyk, kterému chybí klíč, se nenahrává a jeho stávající nahrávky zůstanou.

Na počítači: `node dev/export_phrases.mjs` a `python3 make_voice.py` (s proměnnými prostředí uvedenými výše).

## Fotky

`photos/manifest.json` (soubor z Wikimedia Commons pro každý druh) připravuje výzkumník. Fotky stahuje `fetch_photos.py` při každém nasazení na GitHub Pages; do gitu se necommitují. Autor a licence se zobrazují na kartičce a v Koutku pro rodiče.

## Licence a autoři

- **Fotky:** Wikimedia Commons, licence CC BY, CC BY-SA a volné dílo. Autor, licence a odkaz na zdroj jsou u každé fotky v `photos/manifest.json` a ve hře v koutku pro rodiče. Fotky jsou zmenšené a ve hře oříznuté; jiné úpravy nemají.
- **Písma:** Andika a Grandstander, SIL Open Font License 1.1 (`fonts/LICENSE-*.txt`).
- **Hlasy:** vytvořené umělou inteligencí (ElevenLabs, Azure AI Speech), podrobnosti v části o hlasech.

## Pro vývojáře

- Struktura: `index.html`, `js/` (ES moduly bez buildu; `js/dive/` = Ponor), `css/app.css` (jen tokeny z `design/tokens.css`), `sw.js` (offline), `data/` (výzkumník), `art/` a `design/` (designér).
- Svět Ponoru se skládá z dlaždic dna `art/ponor/*-floor.svg` a přechodů `trans-*.svg` podle jejich `data-in`, `data-out` a `data-floor-y` (`js/dive/world.js`, `DESIGN.md` §6.4). Když dlaždice chybí, dno se dopočítá.
- Při změně souborů aplikace zvyšte `VERSION` v `sw.js`.
- Testy:

```bash
for t in tests/*.test.mjs; do node "$t"; done        # svět, věty, záloha, hry, service worker, hlasové adresy
python3 -m unittest discover -s tests -t .            # server, stahování fotek, nahrávání hlasu
PLAYWRIGHT=<cesta k playwright/index.mjs> CHROME=<Chromium> node dev/e2e.mjs   # celá hra, snímky do dev/screens/
```

`dev/placeholders/` obsahuje dočasné zástupné soubory pro vývoj (nikdy se nenasazují). `dev/make_icons.mjs` vyrobí ikony z `art/app-icon.svg`.
