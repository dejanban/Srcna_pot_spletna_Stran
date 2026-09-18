# Ribja pot – Srčna pot Svibnik

Odzivna, statična spletna stran v slovenščini, angleščini, nemščini in španščini. Za delovanje ne potrebuje Node.js, sestavljanja ali podatkovne baze.

Spletna stran: [Ribja pot – Srčna pot Svibnik](https://dejanban.github.io/Srcna_pot_spletna_Stran/)

## Lokalni zagon

V korenski mapi projekta zaženite:

```bash
python3 -m http.server 8000 --bind 127.0.0.1
```

Odprite **http://127.0.0.1:8000**. Za objavo na statičnem gostovanju potrebujete `index.html`, `styles.css`, `app.js`, `translations.js` in celotno mapo `assets/`.

## Vsebina

- Razdelek »Oznake ob poti« prikazuje oznako društva, smerni tablici Ribje poti za levo in desno ter tablo za kotičke za sproščanje. Pojasnila in nadomestna besedila slik so v vseh štirih jezikih.
- Privzeti jezik je slovenščina. Izbira v zgornjem desnem kotu se shrani v brskalniku; parameter `?lang=sl|en|de|es` ima prednost.
- Celoten opis z informacijske table, vse njene oštevilčene točke, originalna tabla, tri priložene spletne povezave in vseh šest logotipov sodelujočih.
- Interaktivni zemljevid Leaflet z obema izvirnima trasama GPX, povečavo, pomanjšavo, prikazom celotne poti in prenosi GPX.
- Višinski profil s prikazom položaja na zemljevidu. Drsnik podpira tipkovnico in dotik.
- Štiristranski PDF brošure, vdelan pregledovalnik PDF, slikovni prikaz vseh strani in neposreden prenos. Izvirna brošura in imena organizacij ostajajo slovenska; spletni opisi in uporabniški vmesnik so prevedeni.
- Izvirne fotografije in grafike so iz priloženih slik. Zaradi ločljivosti izvirne table so fotografije pri večjih povečavah mehkejše.

## Struktura

```text
index.html                 struktura strani
styles.css                 odzivna zasnova in barve
app.js                     jeziki, zemljevid, graf in pregledovalnik
translations.js            vsi štirje jeziki
assets/
  data/routes.js           izračunane višine in vse točke GPX
  documents/               štiristranski PDF brošure
  fonts/                   lokalne pisave in licence OFL
  gpx/                     izvirni GPX, preimenovan brez presledkov
  images/                  spletne slike, izrezi fotografij in logotipov
  vendor/leaflet/           Leaflet 1.9.4 in licenca
source/
  images/                  izvirni JPG, brez sprememb
  notes/                   izvirni prompt, prepis, povezave in barve
scripts/prepare_assets.py  ponovljiva priprava slik, PDF in podatkov GPX
tests/browser_check.py     funkcionalno preverjanje v brskalniku
```

## Podatki o poti

Razdalja je izračunana s Haversinovo formulo med zaporednimi točkami v vsakem segmentu. Med ločenimi segmenti se razdalja ne prišteva. Višina je prevzeta iz elementov `<ele>` v GPX.

| Trasa | Razdalja GPX | Najnižja–najvišja višina | Seštevek vzpona / spusta |
| --- | --- | --- | --- |
| Ribja pot | 4,633 km | 143,6–183,1 m | +125 / −133 m |
| Učna pot | 12,272 km | 139,9–167,5 m | +219 / −229 m |

Vzpon in spust sta **neglajena seštevka** razlik višin. Šum in kakovost GPX lahko povzročita precenjene vrednosti; zato sta na strani izrecno označena kot okvirna. Višinski razpon ni enak skupnemu vzponu. Tabla navaja 32 m višinske razlike za krajšo pot; priloženi GPX kaže približno 40 m. Čas 1 h 15 min in ocena »lahka pot« izvirata iz table in veljata za krajšo pot. Težavnost in čas daljše poti nista izmišljena.

GPX ne vsebuje koordinat 11 zanimivosti, zato zemljevid označuje začetek dejanskega zapisa, seznam zanimivosti pa ohranja številke iz table. Za širino poti, ovire in dostopnost z vozičkom ali hojico ni podatkov.

Zemljevid uporablja spletne ploščice OpenStreetMap in njihovo vidno navedbo avtorstva. Zemljevidna podlaga in zunanje povezave potrebujejo internet. Vsi drugi viri so lokalni, trasa GPX in profil ostaneta na voljo tudi, če ploščic ni mogoče naložiti. Pri javni objavi upoštevajte [pravila uporabe ploščic OSM](https://operations.osmfoundation.org/policies/tiles/).

## Obnova spletnih gradiv

Skripta potrebuje Python in Pillow. Ko zamenjate izvirni sliki ali datoteki GPX:

```bash
python3 scripts/prepare_assets.py
```

PDF je slikovna pretvorba štirih izvirnih panelov, ne besedilni ali označeni PDF. Izrezi so določeni za priloženi datoteki; pri drugačnih predlogah prilagodite koordinate v skripti. Spletna stran je že pripravljena in za običajen zagon Pillow ni potreben.

## Preverjanje

Za razvojne teste namestite Playwright v virtualno okolje in njegov Chromium. Med testom naj strežnik teče na vratih 4173:

```bash
python3 -m venv .venv
.venv/bin/pip install playwright
.venv/bin/playwright install chromium
python3 -m http.server 4173 --bind 127.0.0.1
# V drugem terminalu:
.venv/bin/python tests/browser_check.py
```

Naslov testnega strežnika lahko spremenite z okoljsko spremenljivko `TEST_URL`. Testi preverijo vse jezike pri štirih širinah, shranjevanje jezika, oba GPX, višinski profil, prenose, PDF, tipkovnico, lokalne vire in odpoved zemljevidne podlage. Sliki za ročni pregled se shranita v `/tmp/tabla-desktop-final.png` in `/tmp/tabla-mobile-final.png`.
