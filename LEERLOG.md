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
