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
