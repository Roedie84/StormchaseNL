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
