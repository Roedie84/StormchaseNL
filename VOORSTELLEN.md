# Voorstellen StormchaseNL

Status: open / akkoord / afgewezen / gebouwd vX / geverifieerd / teruggedraaid. Ruud keurt goed via de chat ("akkoord L-SC-00x").

## L-SC-001 · naderingssnelheid alleen uit nieuwe inslagafstanden (geen 10-s herhalingen)
- Status: **akkoord 08-10 → gebouwd 0.45.0** (08-10; release v0.45.0, workflow groen, HACS ververst), geïnstalleerd 07:03 — verifiëren bij ≥1 onweersgebeurtenis
- Bouw: nieuwe module `nadering.py` (`Naderingstrend`): punt alleen bij nieuwe inslagtijd (of ≥0,5 km afstandsverschil, verplaatsing); snelheid alleen bij een nieuw punt berekend en vastgehouden; vervalt zodra <3 metingen (MIN_SAMPLES 4 → 3) in het venster van 15 min liggen. 16 tests in `tests/test_nadering.py` (suite 392 groen).
- Replay 07-10 met recorderreeksen (oude code reproduceert HA exact: 201, 111, 81 … 41 min; perioden 15,0/15,0/4,2/15,0 min): nieuw → nadert 2× (4,2 + 7,7 = 11,8 min i.p.v. 49,2), 0 aankomstwijzigingen zonder nieuwe inslag (was 244), aankomst 159 → 122 → 41 min (bereik oud 41-4925), geen periode meer van ~15 min.
- Effect meten: per onweersgebeurtenis aantal nadert-wissels en duur (geen perioden van precies 15 min), aankomstwijzigingen zonder nieuwe inslag (= 0 verwacht), validatieteller aankomst (basis 1/6, ≤15 min 0/3) en voorspelde tegen werkelijke aankomst; vergelijken met de replay-cijfers hierboven.
- Onderbouwing: 07-10 21:15-22:37 (n=236 aankomstwaarden): aankomst sprong 45 → 1214 min en 4168 → 167 min zonder nieuwe inslag; 4× nadert-aan voor een onweer dat nooit binnen 50 km kwam. Replay van `_speed_from_history` op de echte reeks reproduceert de zaagtand exact; met alleen nieuwe afstanden blijft de schatting stabiel (36 min bij 83 km, 24,8 km/u).
- Voorstel: in `coordinator.py` een punt aan `_history` alleen toevoegen als de afstand (of de nieuwste inslagtijd) veranderd is; MIN_SAMPLES dan op aantal echte metingen (bv. 3). Plus test met de reeks van 07-10.
- Verwacht effect: geen zaagtand meer; minder korte nadert-pulsen; aankomsttijd in meldingen stabiel.
- Extra onderbouwing 08-10: 3 van de 4 nadert-perioden op 07-10 duurden 14,8-15,0 min, precies `TREND_WINDOW` (15 min).
- Extra onderbouwing 07-10 23:45: validatietellers van de integratie zelf: aankomst 1/6 uitgekomen (≤15 min 0/3), terwijl passage 21/21 haalt.
- Meten na bouw: validatieteller aankomst (nu 1/6) en per onweersgebeurtenis het aantal nadert-wissels, spreiding van aankomst zonder nieuwe inslag, en voorspelde tegen werkelijke aankomst (validatie).

## L-SC-002 · bronstatistiek bewaren over herstarts
- Status: **gebouwd 0.44.0** (08-10 04:36), geïnstalleerd 06:23 — eerste bewijs 07:40: per dag radar 80 tegen 40 sinds herstart 07:03 (telt over herstart door). Nog: over een daggrens (≥2 dagen).
- (eerder: gepland, zelf bouwen: meetbaarheid; de code bewaarde het nog niet)
- Onderbouwing: 07-10 23:45: `statistieken.gestart_op` 21:04 UTC, draaitijd 0,7 u; na elke herstart (vandaag ~10) begint gelukt/mislukt per bron opnieuw. Betrouwbaarheid per bron over dagen is zo niet uit de integratie te halen.
- Bouw: tellers per bron per dag in de Store bewaren (rollend 30 d), in diagnostics tonen; test.
- Meten na bouw: diagnostics toont slaagpercentage per bron over ≥2 dagen na een herstart.

## L-SC-003 · passage-validatie: trefkans op afstand, niet "er was een afstand"
- Status: **geverifieerd 08-10 11:45** (gebouwd 0.46.0, geïnstalleerd 10:55): diagnostics toont raak/binnen 10/20 km per horizon; over alle 24 bewaarde passages 9/24 · 12/24 (baseline 5/12 · 7/12 telde alleen de laatste 20)
- Bouw: per passage-uitkomst `raak` (≤10 km), `binnen_10_km`, `binnen_20_km` naast `afwijking_km`; samenvatting per horizon `binnen_10_km`, `binnen_20_km`, `trefkans_10_km_pct`, `trefkans_20_km_pct`, `mediane_afwijking_km`, `grootste_afwijking_km`, berekend uit `afwijking_km` (dus ook over bewaarde uitkomsten). `uitgekomen` blijft = afstand gemeten. Aankomst ongewijzigd (was al: raak bij onweer binnen waarschuwingsafstand). Tests `tests/test_release_0460.py`.
- (eerder: gepland, zelf bouwen: rapportage/classificatie; raakt geen drempels of meldgedrag — dagafsluiting)
- Onderbouwing: `validatie.py` `passage_afgerond` zet `uitgekomen = werkelijke_afstand is not None` → passage altijd 100% (21/21). Bewaarde uitkomsten (n=12): |afwijking| ≤10 km 5/12, ≤20 km 7/12, max 56 km.
- Bouw: in de samenvatting per horizon `binnen_10_km`, `binnen_20_km` en mediane afwijking toevoegen (bestaande `uitgekomen` blijft bestaan voor vergelijkbaarheid, met toelichting "afstand gemeten"). Test.
- Meten na bouw: diagnostics toont per passagehorizon het aandeel binnen 10/20 km; baseline 5/12 en 7/12.

## L-SC-004 · `regen_begint_over` toont de volgende bui terwijl het regent
- Status: **gebouwd 0.46.0**, geïnstalleerd 10:55 — 11:41 droog: `volgende_bui` false, `begint_over` 19 (ongewijzigd gedrag); wacht op regen met droog gat
- Onderbouwing: 08-10 08:10: regen stopt over 16 min, nieuwe bui vanaf +91 min in de reeks, maar `sensor.stormchase_regen_begint_over` bleef unknown (begint_over alleen bij droog).
- Bouw: nieuwe module `buienreeks.py` (`lees_reeks`, `begin_weergave`); veld `volgende_bui_over` = eerste minuut na `stopt_over` boven de drempel. Sensor toont dat als het regent; attributen `volgende_bui` (true/false) en `volgende_bui_over`. `begint_over` zelf ongewijzigd → meldingen, `regen_verwacht`, briefing en regenvalidatie gedragen zich als voorheen. Tests in `tests/test_release_0460.py`.
- Meten na bouw: bij regen met droog gat toont de sensor een waarde met `volgende_bui: true`; geen extra regenmeldingen (aantal regen-events per dag gelijk aan baseline).
