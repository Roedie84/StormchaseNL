# Leerlog StormchaseNL

Doorlopende leerronde (elke 4 uur). Alleen gemeten getallen; KPI's in KPI.csv.

## 07-10 23:15 · tussenronde (eerste ronde, baseline uit ~10 dagen historie)
- Gebeurtenis 07-10 21:15-22:37: inslagen op 95 → 69 km (max 25 inslagen in de reeks), nooit binnen 50 km. `onweer_nadert` 4× aan (~49 min samen); aankomst voorspeld tot 41 min (21:22). Niet uitgekomen → 1 valse aankomst, 4 nadert-perioden zonder aankomst.
- Aankomst schommelt zonder nieuwe inslag: 45 → 1214 min in 12 min (22:24-22:36), 4168 → 167 min (21:54-22:12). Zaagtand elk ~15 min.
- Hypothese H-SC-1 (getoetst, bevestigd): `_speed_from_history` krijgt elke 10 s een punt met dezelfde afstand; de 15-min-regressie wordt daardoor eerst steil en daarna vlak. Replay met de echte reeks (94,6 km → 83,2 km): huidige code geeft 201, 49, 41 … 161, 300 min (gelijk aan wat HA toonde); alleen nieuwe afstanden meenemen geeft stabiel 36 min. → voorstel L-SC-001.
- 28/29-09 23:51-01:21 ook 4× nadert zonder inslag binnen 50 km.
- Waarschuwingsniveau: 04-10 oranje (meteoalarm) 04:37-10:22, verder groen.
- Bronnen 10 d: radar 15× kort (1-2 min), open_meteo 16× (30-09 22:07 - 01-10 11:12 om en om 30 min, 07-10 16:45-17:15), buienradar 5×. Radarbeeld nu 2 min oud.
- Niet gemeten: hits/misses tegen Blitzortung binnen 25/10 km (geen onweer dichtbij in 10 d); lead-time (geen aankomst). Validatie-tellers van de integratie zelf nog niet uitgelezen (diagnostics) → volgende ronde.
- Geen release (tussenronde; L-SC-001 raakt meldtekst/nadert → voorstel).

laatste ronde: 07-10 23:15, gemeten t/m 07-10 23:10

## 07-10 23:40 · tussenronde (handmatig gestart)
- Correctie: de vorige ronde was om 23:15, niet 23:30 (tijdstempels aangepast).
- Sinds 23:15 geen nieuwe gebeurtenis om te meten; geen release.

laatste ronde: 07-10 23:40, gemeten t/m 07-10 23:40

## 07-10 23:45 · tussenronde
- Validatie-tellers van de integratie uitgelezen (diagnostics, sinds ~31-08): aankomst ≤15 min 0/3 uitgekomen, aankomst >45 min 1/3 (afwijking 47 min) → aankomst samen 1/6 (17%). Passage ≤15 min 13/13 en 15-45 min 8/8 uitgekomen, maar afstandsfout gem. 18,5-18,8 km. Regen ≤15 min 4/4 (7,7 min), 15-45 min 6/11 (12,8 min), >45 min 11/15 (16,9 min).
- Steunt H-SC-1/L-SC-001: de aankomsttijd is de zwakste voorspelling (1/6); de zaagtand uit de 10-s herhalingen is een plausibele oorzaak. Na bouw meten met deze zelfde tellers.
- Bronnen sinds herstart 21:04 UTC (0,7 u): alle 100% (radar 39/39, buienradar 8/8, open_meteo 2/2). Meetbaarheid: bronstatistiek begint bij elke herstart opnieuw (10 releases/herstarts vandaag) → betrouwbaarheid per bron over dagen alleen uit de recorder (bronstatus). Kandidaat: tellers bewaren over herstarts (zelf bouwen, meetbaarheid).
- Nu: regen 1,9 mm/u (buienradar), geen onweer (CAPE 70, ensemble 0%), geen waarschuwing. Geen nieuwe onweersgebeurtenis sinds 22:37.
- Geen release.

laatste ronde: 07-10 23:45, gemeten t/m 07-10 23:44

## 08-10 03:40 · dagafsluiting 07-10
- Onweer 07-10: dichtstbij 68,7 km (n=27 afstanden), 0 inslagen <50 km, niveau groen. `onweer_nadert` 4× aan (48,9 min, 8 wissels) → 4 valse alarmen, 0 hits, 0 misses; lead-time niet meetbaar. Sinds 23:44 geen onweer.
- H-SC-1 extra steun: 3 van de 4 nadert-perioden duurden 14,8-15,0 min = `TREND_WINDOW`; past bij één nieuw punt dat 15 min in de regressie blijft hangen. L-SC-001 blijft open.
- Bronnen over 16 herstarts (recorder): 2242/2248 = 99,73%; zwakst open_meteo 98,2% (DNS 16:45, 30 min hapert). Na 0.43.0 (actief 21:39) 0 fouten → herkansing nog onbewezen.
- Locatie: vóór 0.42.0 8× kort "thuis" bij herstart, daarna 0× (8× "laatst bekend") → 0.42.0 geverifieerd.
- Bug gevonden en gebouwd: radarbeeld ververste niet bij een nieuw frame (kenmerk las `data["path"]` i.p.v. `data["radar"]`); `image_last_updated` 4,7 u stil.
- Gebouwd **0.44.0**: die fix + L-SC-002 (bronstatistiek per dag, 30 d, over herstarts, in diagnostics). 376 tests groen, workflow groen, HACS ververst.
- Validatietellers ongewijzigd (aankomst 1/6, passage 21/21 met 18,6 km, regen 21/30).
- Meetbaarheid: Blitzortung elke nacht ~02:00 onbeschikbaar (21 en 11 min) — blinde vlek, externe bron. Stormchase-logs van vóór 22:48 weg door herstarts.

laatste ronde: 08-10 04:40, gemeten t/m 08-10 03:46

## 08-10 07:40 · tussenronde
- Geïnstalleerd: 0.44.0 (06:23) en 0.45.0 (07:03). Geen onweer (ensemble 0%, CAPE 10), niveau groen → alleen beschikbaarheid gemeten.
- **0.44.0 radarfix geverifieerd:** sinds 06:23 16 beeldwissels, grootste gat 10 min (was 4,7 u stil).
- **L-SC-002 eerste bewijs:** `bronnen_per_dag` 08-10 radar 80 gelukt tegen 40 sinds de herstart van 07:03 → tellers lopen over de herstart door. Alle bronnen 100% (n=130). Verifiëren over een dag­grens.
- Locatie bij 2 herstarts: 10-13 s "laatst bekend", 0× "thuis".
- **H-SC-2 (nieuw):** de validatie telt een passage als "uitgekomen" zodra er een afstand gemeten is (`validatie.py` `passage_afgerond`: `uitgekomen = werkelijke_afstand is not None`). Daardoor is "passage 21/21" geen trefkans. Uit de 12 bewaarde passage-uitkomsten: binnen 10 km 5/12 (42%), binnen 20 km 7/12; uitschieters −56, −31, −31, −25 km. Kandidaat L-SC-003 (zelf bouwen, rapportage).
- L-SC-001 (0.45.0) actief; wacht op onweer.
- Geen release (tussenronde, niets acuut).

laatste ronde: 08-10 07:40, gemeten t/m 08-10 07:43

## 08-10 10:05 · bouw (chatsessie)
- Gebouwd **0.46.0**: L-SC-003 (passage-trefkans op afstand: raak ≤10 km, apart ≤20 km, mediane/grootste afwijking; baseline uit bewaarde uitkomsten 5/12 en 7/12) + L-SC-004 (nieuw: `regen_begint_over` toont tijdens regen het begin van de volgende bui, gezien 08:10 stopt +16, nieuwe bui +91). Geen drempels of meldgedrag gewijzigd. 413 tests groen, workflow groen, HACS ververst.

laatste ronde: 08-10 07:40, gemeten t/m 08-10 07:43

## 08-10 11:45 · tussenronde
- Geïnstalleerd: 0.46.0 (herstart 10:55). Geen onweer sinds 07:43 (0 inslagen <50 km, nadert 0×, ensemble 0%, CAPE 110) → alleen beschikbaarheid gemeten.
- Bronnen 08-10 (over herstarts 08:55 en 10:55): 100% (n=508; radar 319, buienradar 66, meteoalarm 29). **L-SC-002:** `bronnen_per_dag` telt over 3 herstarts door; daggrens nog toetsen.
- Locatie bij 2 herstarts: 10-11 s "laatst bekend", 0× "thuis".
- **L-SC-003 eerste meetpunt gehaald:** diagnostics toont per passagehorizon raak/binnen 10/20 km. Over alle bewaarde uitkomsten (n=24, niet alleen de 20 zichtbare): binnen 10 km 9/24 (38%), binnen 20 km 12/24 (50%); ≤15 min 6/13, 15-45 min 3/8, >45 min 0/3. De baseline 5/12 · 7/12 van 07:40 telde alleen de laatste 20 uitkomsten → baseline herzien.
- Regen: nu droog; `regen_begint_over` 19 min (0,21-0,93 mm/u), `volgende_bui` false (terecht: het regent niet). L-SC-004 wacht op regen met droog gat. `regen_verwacht` off bij 19 min (aanloop 10 min) → verwacht.
- Geen release.

laatste ronde: 08-10 11:45, gemeten t/m 08-10 11:44

## 08-10 15:40 · tussenronde
- Geïnstalleerd: 0.48.0 (0.47.0 en 0.48.0 door chatsessie; HA-herstarts 12:16, 14:19, 14:59, 15:08, 15:25, 15:39). Geen onweer (0 inslagen <50 km, nadert 0×, ensemble 0%, CAPE 30), niveau groen → onweer: alleen beschikbaarheid.
- Bronnen 08-10 over alle herstarts: 100% (n=917; radar 553, buienradar 115, meteoalarm 54). **L-SC-002:** dagteller loopt over 6 herstarts door; daggrens toetsen in de dagafsluiting.
- Regen: 3 buien (11:50-12:21, 13:51-14:24, vanaf 15:23). Regenvalidatie 23/31 (was 21/30); 2 nieuwe: −13 min (15-45) en −25,7 min (>45). Bekende uitkomsten: afwijking −22, −18,9, −7,9, +7, −8, −13, −25,7 → mediaan −13 min: regen "begint" structureel eerder dan voorspeld.
- **L-SC-004 eerste meetpunt gehaald:** 15:39 regent, `stopt_over` 20, `volgende_bui` true, sensor 105 min (bui op +105/+110 in de reeks).
- **0.48.0 (weerentiteit volgt radar):** sinds 14:19 rainy bij elke radarwaarde ≥0,1 (14:19, 15:23), terug naar model bij 0,0 (14:24) → werkt. Maar 15:39: `pouring` en neerslagintensiteit 6,04 terwijl de reeks op minuut 0 1,33 mm/u geeft; 6,04 is minuut +10.
- **H-SC-3 (nieuw):** `lees_reeks` neemt als intensiteit "nu" het maximum over −10..+10 min (bewust, tegen dipjes). Dat verklaart (a) `pouring` tot 10 min te vroeg en (b) waarschijnlijk een deel van de vroege regenstart in de validatie (regent = max tot +10 min, voorspelling = eerste minuut > 0). Toets: regenuitkomsten herrekenen met alleen −10..0 → voorstel L-SC-005 (raakt `regent` en daarmee regenmeldingen: Ruud beslist).
- Geen release (tussenronde, niets acuut).

laatste ronde: 08-10 15:40, gemeten t/m 08-10 15:44

## 08-10 19:40 · tussenronde
- Geïnstalleerd: 0.48.0 (herstarts 16:31, 17:41, 18:36). Geen onweer (0 inslagen <50 km, ensemble 0%, CAPE 0-10), niveau groen → onweer: alleen beschikbaarheid gemeten.
- Bronnen 08-10: 100% (n=1257; radar 791, buienradar 164, meteoalarm 76). **L-SC-002:** dagteller over 9 herstarts door (radar 791 per dag tegen 441 sinds 18:36). Daggrens in de dagafsluiting.
- Regen: validatie 25/33 (was 23/31); 3 nieuwe afgeronde uitkomsten −17,7 (>45 min), −8 (≤15) en −8,1 min (>45). Alle 10 bekende afwijkingen: 9 negatief, 1 positief; mediaan −10,6 min (tekentoets p 0,02, n=10).
- **H-SC-3 sterker:** de drie uitkomsten op ≤15 min zijn −7,9, −8 en −8 min — precies wat het vooruitkijken (−10..+10 min, reeks per 5 min) voorspelt: "regent" slaat aan zodra er over ~10 min regen in de reeks staat. Bij langere horizons komt daar de gewone voorspelfout bij. Ondersteunt L-SC-005 (open, Ruud beslist); offline replay nog niet mogelijk (radarreeksen niet in de recorder).
- Open voorspelling in de validatie: regen over 43 min (0,21 mm/u) van eerder; live 19:41 droog, `regen_begint_over` 113 (0,1 mm/u), `regen_verwacht` off → toetsen.
- Geen release (tussenronde, niets acuut).

laatste ronde: 08-10 19:40, gemeten t/m 08-10 19:44

## 08-10 23:40 · tussenronde
- Geïnstalleerd: 0.48.1 (app-icoon, chatsessie). **0.49.0** (officiële KNMI-bronnen; chatsessie 23:26) staat klaar in HACS, nog niet geïnstalleerd → geen eigen release erbovenop. Na installatie meten: bronstatus van de nieuwe KNMI-bronnen (slaag%, latentie) naast radar/buienradar.
- Geen onweer (0 inslagen <50 km, ensemble 0%, CAPE 0, LI 14,6), niveau groen → onweer: alleen beschikbaarheid gemeten.
- Bronnen sinds herstart 22:02: alle 10 bronnen 100% (radar 677, buienradar 142, meteoalarm 68, open-meteo 31), 0× haperend. Locatie: tracker iPhone.
- Regen: 2 nieuwe valse regenvoorspellingen (18:36 regen over 43 min, 20:44 over 60 min, beide licht; niet uitgekomen). Validatie nu 24/34 (≤15 min 5/5, 15-45 6/11, >45 13/18): korte horizon blijft betrouwbaar, lange horizon geeft ~1 op 3 vals. Open: regen over 57 min (piek 1,07 mm/u); live 23:41 droog, `regen_verwacht` off.
- H-SC-3 ongewijzigd (geen nieuwe afgeronde regenstart); L-SC-005 afgewezen door Ruud (21:13), meting loopt als KPI door.
- Geen release.

laatste ronde: 08-10 23:40, gemeten t/m 08-10 23:44

## 09-10 03:40 · dagafsluiting 08-10
- Onweer 08-10: 0 inslagen <50 km, niveau groen, nadert 0×, ensemble 0% → hits/misses/lead-time niet meetbaar (geen gebeurtenis). Alleen beschikbaarheid gemeten.
- Bronnen 08-10 (lokale dag, over 20 herstarts): 1686/1686 = 100% (radar 1044, buienradar 217, meteoalarm 100, meting 80, overige 45). Radarbeeld 22:00-03:41 elke 10-11 min. Locatie: tracker iPhone.
- **L-SC-002 geverifieerd:** `bronnen_per_dag` heeft 08-10 en 09-10 apart (2 dagen, totaal opgeteld) → telt over herstarts én daggrens door.
- Regen: avond/nacht 4 valse lichte regenvoorspellingen (18:36 +43, 20:44 +60, 22:52 +57, 00:37 +42 min); korte horizon blijft 5/5. Validatie 24/34.
- **Meetfout gevonden:** `validatie.py` bewaart MAX_UITKOMSTEN = 60 uitkomsten over álle soorten samen; het venster is vol (34 regen + 21 passage + 5 aankomst). Elke afgeronde regenvoorspelling (8-10 per regendag) duwt de oudste uitkomst eruit — nu onweersuitkomsten uit augustus: passage 24 → 21, aankomst 6 → 5 sinds 08-10. De zeldzame onweersvalidatie (het lange geheugen voor L-SC-001) slijt zo weg. Voorstel L-SC-006 (zelf bouwen: venster per soort). Niet nu uitgebracht: 0.49.0 en 0.50.0 staan nog niet geïnstalleerd (0.48.1 draait) → niet erbovenop stapelen; bouwen in de eerste dagafsluiting na installatie.
- H-SC-3 ongewijzigd (geen nieuwe afgeronde regenstart met bekende afwijking). L-SC-001 wacht op onweer.
- Geen release.

laatste ronde: 09-10 03:40, gemeten t/m 09-10 03:47

## 09-10 07:40 · tussenronde
- Geïnstalleerd: **0.50.0** om 06:02 en **0.50.1** om 06:57 (0.49.0 KNMI-bronnen zit erin). Herstarts sinds 03:47: 4 (06:03, 06:57, 07:02, 07:42). Locatie: tracker iPhone.
- Geen onweer (0 inslagen <50 km, ensemble 0%, CAPE 0, LI 9,3), niveau groen → onweer: alleen beschikbaarheid gemeten. Het regent licht (1,2 mm/u, `regen_verwacht` aan).
- Bronnen: "alles in orde", 0 haperend, 15 bronnen 100% (radar 1168 vandaag). Nieuwe KNMI-bronnen sinds 06:03 alle 100%: nowcast 34, edr 22, waarschuwingen 19, wms 15, verwachting 8; push verbonden.
- **Bronwissel regen:** sinds 0.49.0 is de KNMI-nowcast de eerste bron; Buienradar alleen terugval (daarom Buienradar laatste succes 06:02). De regenvalidatie legt de bron niet vast → uitkomsten van vóór en na 06:03 lopen door elkaar. Scheiden op `gemaakt_op` ≥ 09-10 06:03 kan nog; daarna nodig: bron per voorspelling → toegevoegd aan L-SC-006.
- Regen: 1 nieuwe afgeronde uitkomst (04:52, nog Buienradar): "over 57 min", kwam na 25 min (−32 min). Afwijkingen nu 11 bekend, 10 negatief (regen eerder dan voorspeld); validatie 24/34. H-SC-3 ongewijzigd; KNMI-nowcast los meten vanaf nu.
- L-SC-006 (venster per soort): 0.50.x geïnstalleerd → bouwen in de dagafsluiting van 10-10; onweer nog 21 passage / 5 aankomst in het venster.
- Geen release (tussenronde).

laatste ronde: 09-10 07:40, gemeten t/m 09-10 07:45

## 09-10 11:40 · tussenronde
- Geïnstalleerd: 0.50.1 (geen nieuwe release). HA-herstarts sinds 07:45: 2 (10:09, 10:40). Locatie: tracker iPhone. Geen onweer (0 inslagen <50 km, CAPE 0, LI 4, ensemble 0 %), niveau groen → onweer: alleen beschikbaarheid gemeten.
- Bronnen 09-10 t/m 11:44: 15 bronnen, 0 mislukt (radar 740, KNMI-nowcast 107, EDR 71, waarschuwingen 38, WMS 25); push verbonden (34 meldingen). Buienradar sinds 06:02 alleen terugval, niet nodig geweest.
- Regen: het regent licht (0,12 mm/u, `stopt_over` 1, volgende bui +16 → sensor 16). **Eerste afgeronde uitkomst met KNMI-nowcast als bron:** 08:53 "over 41 min", kwam na 19 min (−21,6). Bekende afwijkingen nu 12, 11 negatief → het vroege patroon blijft ook met de nieuwe bron (n=1 KNMI, geen conclusie). Validatie 24/34; venster: regen 34, passage 21, aankomst 5 — dit keer verdrong regen geen onweersuitkomst.
- Radarvooruitblik (0.49.0): beeld alleen ververst bij herstarts (07:42, 10:09, 10:41). Code: bouwt bewust alleen als iemand in de laatste 15 min keek (`KIJKER_GELDIG`) → geen versheids-KPI voor dit beeld; het gewone radarbeeld is vers (KNMI 11:40).
- H-SC-3 loopt als KPI (L-SC-005 afgewezen). L-SC-006 (venster per soort + bron per voorspelling) bouwen in de dagafsluiting van 10-10. Geen release.

laatste ronde: 09-10 11:40, gemeten t/m 09-10 11:45

## 09-10 15:40 · tussenronde
- Geïnstalleerd: 0.50.1. HA-herstarts sinds 11:45: 6 (12:11-14:43). Locatie: tracker iPhone. Geen onweer (0 inslagen <50 km, CAPE 0 / piek 12 u 140, LI 2,8, ensemble 0 %; wel windschering ~62 km/u, stoten 52 km/u verwacht), niveau groen → onweer: alleen beschikbaarheid.
- Bronnen: 15 bronnen 0 mislukt (radar 1693, KNMI-nowcast 178, EDR 118, waarschuwingen 61); push verbonden. Buienradar en Bright Sky (`meting`) alleen terugval (laatste succes 06:02/06:18) — zo ontworpen.
- Regen (KNMI-nowcast): 4 nieuwe afgeronde uitkomsten 12:40-14:12: −9,6 / **+13,1 / +20,6 / +8,0 min** → met KNMI nu vaker te LAAT (3 van 5 KNMI-uitkomsten), tot 0.49.0 bijna altijd te vroeg (11/12). H-SC-3 bijgesteld: patroon is bronafhankelijk; goed scheiden kan pas met de bron per uitkomst.
- **L-SC-006 acuut gebouwd (0.50.2):** venster nu regen 37 / passage 20 / aankomst 3 — sinds 11:45 nog eens 3 onweersuitkomsten verdrongen (passage 21→20, aankomst 5→3), onherstelbaar. Daarom in een tussenronde: venster 60 per soort + bron per regenvoorspelling + `regen_per_bron`/`aantal_per_soort` in de diagnostiek. 10 tests, 691 groen, workflow groen, HACS ververst. Wacht op installatie.

laatste ronde: 09-10 15:40, gemeten t/m 09-10 15:45

## 09-10 19:40 · tussenronde
- Geïnstalleerd: **0.50.2** (L-SC-006). HA-herstarts sinds 15:45: 7 (16:16-19:29). Locatie: tracker iPhone. Geen onweer (0 inslagen <50 km, CAPE 0 / piek 12 u 140, LI 2,3, ensemble 0 %; windschering 0-6 km 73 km/u, stoten verwacht 47 / gemeten 32 km/u), niveau groen → onweer: alleen beschikbaarheid.
- Bronnen: alles in orde; 1× 503 bij Open-Meteo (icon_d2 + ensemble, 18:03, volgende ronde weer gelukt) → 99 %; radar 1949, KNMI-nowcast 251, EDR 170 zonder fout; push verbonden.
- **L-SC-006 geverifieerd:** `aantal_per_soort` aankomst 3 / passage 20 / regen 40 (samen 63 > 60): onweersuitkomsten niet meer verdrongen sinds 15:45; nieuwe regenuitkomsten dragen `bron` (knmi 2×).
- Regen KNMI-nowcast: 2 nieuwe uitkomsten +25,6 min (57 min, kwam na 83) en +2,8 min. Alle KNMI-uitkomsten sinds 0.49.0 (n=7): mediaan +8 min, 5 van 7 te laat (Buienradar-tijdperk: 21 van 27 bekende te vroeg). H-SC-3: bron bepaalt het teken; n te klein voor een correctievoorstel (≥ 20 KNMI-uitkomsten).
- Geen release (tussenronde).

laatste ronde: 09-10 19:40, gemeten t/m 09-10 19:45

## 09-10 23:40 · tussenronde
- Geïnstalleerd: **0.51.0** (windstoten bijgesteld met de stationsmeting, regenbeeld, regen stopt over; chatsessie 22:40). HA-herstarts sinds 19:45: 3 (19:48, 20:53, 22:43). Locatie: tracker iPhone. Geen onweer (0 inslagen <50 km, CAPE 100 / piek 12 u 180, LI 2,2, ensemble 0 %), niveau groen → onweer: alleen beschikbaarheid.
- Bronnen sinds 22:43: 15 bronnen 0 mislukt (radar 2218, KNMI-nowcast 325, EDR 216); dag 09-10 2 mislukt (503 Open-Meteo 18:03). Push verbonden. Buienradar/meteoalarm alleen terugval.
- Regen KNMI-nowcast: 4 nieuwe uitkomsten −1,9 / +2,9 / −14,8 / −6,9 min. Alle KNMI sinds 0.49.0 **n=11: mediaan +2,8 min, gem. +1,7, gem. absolute fout 11,6 min, 6 te laat / 5 te vroeg**; Buienradar-tijdperk mediaan −8 (21/27 te vroeg). **H-SC-3 bijgesteld:** KNMI heeft vrijwel geen bias maar wel ±12 min spreiding → een vaste correctie helpt niet; het voordeel zit in de bronwissel zelf. Volgen tot n ≥ 20.
- 0.51.0 windstoten: verwacht 28,6 km/u tegen gemeten 16,1 (Hupsel, 3,4 km) — 1 meetpunt; effect van de bijstelling meten in de dagafsluiting (verwacht − gemeten per uur).
- Validatie: aankomst 3 / passage 20 / regen 44 (L-SC-006 houdt: geen verdringing). L-SC-001 wacht op onweer. Geen release.

laatste ronde: 09-10 23:40, gemeten t/m 09-10 23:50

## 10-10 03:40 · dagafsluiting 09-10
- Onweer 09-10: 0 inslagen <50 km, niveau groen, nadert 0×, ensemble 0 % → hits/misses/lead-time niet meetbaar; alleen beschikbaarheid. Locatie: tracker iPhone.
- Bronnen 09-10: 2759/2761 = 99,93 % (2× 503 Open-Meteo 18:03); radar 1535, KNMI-nowcast 328, EDR 218. Na 00:00 15 bronnen 0 mislukt. Push verbonden (153 meldingen sinds 22:43).
- **Windstoten (0.51.0) eerste meting:** vóór de bijstelling (06:03-23:33, n=104) verwacht − gemeten **+13,6 km/u** (MAE 13,6). Erna (23:34-03:44, n=26) bias −0,2 / MAE 6,9, maar in twee helften: +8,8 tot 01:12, **−5,7 sinds 01:13** (verwacht 12,6-14,9 tegen gemeten 18-24). Oorzaak: de factor startte om 23:34 op de **ondergrens 0,50** met 7 paren uit één frontpassage (model 55 km/u, station al 14-29) en staat nu op 0,54; het kale model zit nu dichter bij de meting (25,2 tegen 22,6) dan de bijgestelde waarde (13,6). Gevolg: zolang de factor ~0,5 is, ziet de windmelding (60 km/u) een modelwaarde van 120 km/u als 60 → **H-SC-4 → voorstel L-SC-007** (meldgedrag: Ruud beslist). De 24-uursmediaan herstelt vanzelf als de frontparen uit het venster vallen (~23:30 vandaag).
- Regen: KNMI-uitkomsten met bron (n=6) mediaan +0,4 min, 3 te vroeg / 3 te laat; H-SC-3 loopt (≥ 20 nodig). Validatievenster: aankomst 3 / passage 20 / regen 44 — geen verdringing.
- Lopend: L-SC-001 wacht op onweer. Geen release (geen gepland punt, geen acute bug; windstoten = meldgedrag → voorstel).

laatste ronde: 10-10 03:40, gemeten t/m 10-10 03:46

## 10-10 07:40 · tussenronde
- Geïnstalleerd 0.51.0; geen HA-herstarts sinds 03:46. Locatie tracker iPhone. Geen onweer (0 inslagen <50 km, CAPE 0 / piek 250, LI 5,7, ensemble 0 %), niveau groen, droog → onweer/regen: alleen beschikbaarheid.
- Bronnen 03:46-07:44: 15 bronnen 0 mislukt (radar 2741, KNMI-nowcast 463, EDR 300 sinds 22:43); push verbonden.
- **Windstoten (H-SC-4) bijgesteld beeld:** 03:50-07:44 bijgesteld −1,8 km/u (MAE 2,8; laatste 2 u 0,0 / 1,4) tegen kaal model **+10,0** (MAE 10,0); factor 0,55 (53 paren). De −5,7 van 01-04 u was een overgang na de front; bij rustig weer klopt ~0,55. L-SC-007 aangevuld: (a)/(b) (niet starten op één front) blijven zinvol, optie (c) met vloer 0,7 zou nu slechter zijn. Zware-stormgedrag nog niet gemeten (geen stoten > 35 km/u).
- Lopend: L-SC-001 wacht op onweer; L-SC-007 open (Ruud). Geen release.

laatste ronde: 10-10 07:40, gemeten t/m 10-10 07:44

## 10-10 11:40 · tussenronde
- Geïnstalleerd **0.51.1** (cockpit-scroll); 0.52.0 (L-SC-007, chatsessie 11:12) nog niet. HA-herstarts 08:20, 08:44, 09:18, 10:52. Locatie tracker iPhone. Geen onweer (0 inslagen < 50 km, CAPE 100, LI 3,1, ensemble 0 %), niveau groen → onweer: alleen beschikbaarheid.
- Bronnen 07:44-11:44: 15 bronnen 0 mislukt (radar 3008, KNMI-nowcast 540, EDR 351); push verbonden sinds 10:52. Regen: droog, bui over 92 min (licht) — uitkomst in de volgende ronde.
- **Windstoten (H-SC-4 → H-SC-5):** wind trok aan (Hupsel 14 → 39 km/u). Bijgesteld −4,8 km/u (MAE 4,9, n=24) tegen kaal model +7,7. Gesplitst: model < 28 km/u −2,2 (verhouding gemeten/model 0,59), model ≥ 31 km/u **−8,6** (verhouding 0,84; laatste: model 37, bijgesteld 23, gemeten 39). De 24-uursfactor (0,63) volgt een hogere windklasse niet → **L-SC-008** (factor per windklasse; Ruud beslist). L-SC-007 is gebouwd in 0.52.0 maar dekt dit niet.
- Hypotheses: H-SC-3 (KNMI regenaankomst, n ≥ 20 nodig), H-SC-5 (verhouding stijgt met windsterkte; n=1 dag). L-SC-001 wacht op onweer. Geen release (geen acute bug; windmelding = meldgedrag).

laatste ronde: 10-10 11:40, gemeten t/m 10-10 11:50

## 10-10 15:40 · tussenronde
- Geïnstalleerd **0.52.0** (12:04). HA-herstarts 12:04, 13:37, 14:41. Locatie tracker iPhone. Bronstatus "alles in orde".
- **Onweer op afstand:** inslagen op 64-70 km tussen 13:45 en 15:40 (actieve markers 3 → 42; NNO, cel ONO 27 km/u), **0 binnen 50 km** → niveau groen is juist (geen vals alarm, geen miss binnen de ringen). Naderingssnelheid veranderde alleen bij nieuwe inslagen (15:37 −3,7, 15:40 −3,1; geen 10-s-herhalingen) → eerste meetpunt L-SC-001, nog geen naderende cel. Verwachting stond op "geen onweer" / ensemble 0 % (CAPE 280, LI 1,1, TT 52,3) bij inslagen op 65 km: grensgeval, geen hypothese bij n=1.
- **Windstoten na 0.52.0 (L-SC-007):** 7 frontparen weg, factor 0,63 → 0,67 bij de start en 0,70 nu. 11:53-15:34 (n=23) bijgesteld **−4,0 km/u** (MAE 5,0) tegen kaal model +9,5. Per helft: model 37-44 −6,9 (verhouding 0,85), model 43-50 **−0,8** (MAE 2,8; verhouding 0,72). **H-SC-5 verzwakt:** bij de hoogste modelwaarden was de verhouding juist lager; de −8,6 van 11:40 kwam deels van de achterlopende factor. L-SC-008 aangevuld.
- Regen KNMI: 11 voorspellingen, 9 uitgekomen, mediaan −2,4 min (6 te vroeg / 3 te laat); de laatste drie kwamen 2-13 min eerder dan voorspeld. H-SC-3 loopt (≥ 20 nodig).
- Geen release (geen acute bug; windmelding = meldgedrag).

laatste ronde: 10-10 15:40, gemeten t/m 10-10 15:45

## 10-10 19:40 · tussenronde
- Geïnstalleerd 0.52.0. HA-herstarts 16:19, 16:40, 18:07 (EMS-releases). Locatie tracker iPhone. Bronnen: 15 bronnen, sinds 09-10 18:03 0 mislukt; bronstatus "alles in orde". Logboek 0 Stormchase-fouten.
- **Onweer (gebeurtenis):** cel NO (azimut 47-48°). 16:28 op 80 km, `nadert` aan (snel, 9,4-9,6 km/u) tot de herstart van 16:40; 17:31 8 inslagen op 45-47 km (ring 50 km toonde 16: dubbel geteld via twee Blitzortung-instanties, zie uuranalyse), daarna weg (18:28: 0, dichtstbijzijnde 83 km W). 0 binnen 25 km → geen vals alarm, geen miss. Werkelijke nadering 80 → 46 km in 63 min ≈ 32 km/u tegen geschat 9,5 (n=1; 2 punten 10 s uit elkaar, geen hypothese). Na de herstart van 16:40 51 min geen afstand (geen nieuwe inslagen van de bron), na 18:07 bleef de ring op 4 zonder inslagen tot 18:28 (zelfde dubbeltelling/herstart, al gemeld door de uuranalyse).
- L-SC-001: nadering wijzigde alleen bij nieuwe inslagen (16:28:28 / 16:28:38, markers 6 → 9) → tweede meetpunt, nog geen verificatie bij een cel die doorkomt.
- **Windstoten (0.52.0):** 15:54-19:44 n=24: bias **+0,7 km/u**, MAE 4,3 (mediaan +0,2); factor 0,69 (119 paren, 7 frontparen weg). Bij gemeten ≥ 33 km/u (buienlijn 17:34-18:14, n=5) **−6,5** → H-SC-5 (verhouding stijgt bij harde stoten) weer gesteund, nu bij convectieve stoten; L-SC-008 aangevuld.
- Regen: droog, bui over 102 min (licht). Geen nieuwe KNMI-uitkomst; H-SC-3 loopt (≥ 20 nodig). Geen release.

laatste ronde: 10-10 19:40, gemeten t/m 10-10 19:45
