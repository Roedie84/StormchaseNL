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
- Status: **geverifieerd 09-10 03:40** (gebouwd 0.44.0, geïnstalleerd 08-10 06:23): `per_dag` 08-10 (1686 rondes over 20 herstarts) en 09-10 apart, `aantal_dagen` 2.
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
- Status: **gebouwd 0.46.0**, geïnstalleerd 10:55 — eerste meetpunt 08-10 15:39: regent, `stopt_over` 20, `volgende_bui` true, sensor 105 min. Nog: aantal regenmeldingen per dag gelijk aan baseline (dagafsluiting)
- Onderbouwing: 08-10 08:10: regen stopt over 16 min, nieuwe bui vanaf +91 min in de reeks, maar `sensor.stormchase_regen_begint_over` bleef unknown (begint_over alleen bij droog).
- Bouw: nieuwe module `buienreeks.py` (`lees_reeks`, `begin_weergave`); veld `volgende_bui_over` = eerste minuut na `stopt_over` boven de drempel. Sensor toont dat als het regent; attributen `volgende_bui` (true/false) en `volgende_bui_over`. `begint_over` zelf ongewijzigd → meldingen, `regen_verwacht`, briefing en regenvalidatie gedragen zich als voorheen. Tests in `tests/test_release_0460.py`.
- Meten na bouw: bij regen met droog gat toont de sensor een waarde met `volgende_bui: true`; geen extra regenmeldingen (aantal regen-events per dag gelijk aan baseline).

## L-SC-005 · regen "nu": niet vooruitkijken (−10..0 in plaats van −10..+10 min)
- Status: **afgewezen 08-10 21:13 (Ruud)** — niet opnieuw voorstellen; de meting mag als KPI doorlopen.
- 08-10 19:40: onderbouwing sterker — 10 bekende regenuitkomsten, 9 negatief (mediaan −10,6 min, tekentoets p 0,02); op ≤15 min alle drie −7,9/−8/−8 min = het vooruitkijkvenster.
- Onderbouwing: `buienreeks.lees_reeks` neemt als intensiteit van nu het maximum over −10..+10 min (bewust: een bui met een dipje mag niet droog heten). 08-10 15:39: reeks minuut 0 = 1,33 mm/u, minuut +10 = 6,04 → neerslagintensiteit 6,04 en (sinds 0.48.0) `weather.stormchase` `pouring`, tot 10 min te vroeg. Regenvalidatie: bekende uitkomsten −22, −18,9, −7,9, +7, −8, −13, −25,7 min (mediaan −13, n=7): regen "begint" vrijwel altijd eerder dan voorspeld; de +10 min vooruitkijken in `regent` telt mee, de voorspelling `begint_over` (eerste minuut > 0) niet.
- Voorstel: venster terugkijkend maken (−10..0) voor `regent`/intensiteit, of alleen voor de weerconditie en de validatie (dan blijft meldgedrag gelijk). Eerst offline toetsen: de bewaarde regenuitkomsten en een replay van de buienradar-reeksen van 08-10 (recorder) met beide vensters.
- Verwacht effect: weerconditie `pouring`/`rainy` niet meer tot 10 min te vroeg; regenafwijking in de validatie ~5-10 min dichter bij 0.
- Meten na bouw: mediaan afwijking regenvalidatie (basis −13 min, n=7) en aantal `pouring`-perioden waarbij minuut 0 < 4 mm/u (basis: 1 op 08-10).


## L-SC-006 · validatie: bewaarvenster per soort in plaats van 60 over alles
- Status: **geverifieerd 09-10 19:40** (0.50.2 geïnstalleerd: aankomst 3 / passage 20 / regen 40, samen 63 > 60 zonder verdringing; regenuitkomsten dragen `bron`). Eerder: **gebouwd 0.50.2** (09-10 15:46, tussenronde: acuut — elke regenuitkomst wiste een onweersuitkomst; 3 verloren tussen 11:45 en 15:40). Venster 60 per soort, bron per regenvoorspelling, diagnostiek `regen_per_bron`/`aantal_per_soort`/`max_per_soort`. Wacht op installatie. Meten na installatie: passage/aankomst in `aantal_per_soort` dalen niet meer; regen max 60; nieuwe regenuitkomsten dragen `bron`. (eerder: **gepland (zelf bouwen: meetfout; raakt geen drempels of meldgedrag)** — 0.50.1 geïnstalleerd 09-10 06:57 → bouwen in de dagafsluiting van 10-10. Uitbreiding 09-10 07:40: per regenvoorspelling de bron (knmi / buienradar / open-meteo) vastleggen en de samenvatting ook per bron tonen; KNMI-nowcast is sinds 0.49.0 (geïnstalleerd 06:02) de eerste bron.)
- Onderbouwing: `validatie.py` `MAX_UITKOMSTEN = 60` geldt voor alle soorten samen (`del self.uitkomsten[:-60]`). 09-10 03:40: venster vol met 34 regen, 21 passage, 5 aankomst; passage was 24 (08-10 11:45), aankomst 6 (07-10). Regenuitkomsten (8-10 per regendag) verdringen zo de zeldzame onweersuitkomsten waarmee L-SC-001 en L-SC-003 getoetst worden.
- Bouw: per soort de laatste 60 bewaren (regen, aankomst, passage elk eigen venster); `afgerond` blijft het totaal; diagnostics toont per soort het aantal en de oudste datum. Test: 100 regenuitkomsten na 5 aankomst-uitkomsten → aankomst blijft 5.
- Meten na bouw: aantal aankomst/passage-uitkomsten daalt nooit meer door regen; na een regendag passage/aankomst gelijk.

## L-SC-007 · windstoot-bijstelling: niet starten op één frontpassage
- Status: **gebouwd 0.52.0** (10-10 11:12, chatsessie: opties (a) en (b) — pas na 6 uur paren, geen frontparen) — wacht op installatie (0.51.1 geïnstalleerd). Meten na installatie: factor start niet op een front; bias per uur. Zie ook L-SC-008 (wind-afhankelijke verhouding). (eerder: open)
- Onderbouwing: 0.51.0 (geïnstalleerd 22:43) begon om 23:34 te corrigeren met 7 paren uit 22:33-23:34, precies tijdens een frontpassage: model 55-57 km/u, Hupsel al 14-29 → factor direct op de ondergrens 0,50 (CHANGELOG verwachtte 0,70 op de gegevens van 9-10). Om 03:44 factor 0,54 (32 paren): model 25,2, bijgesteld 13,6, gemeten 22,6. Bias na bijstelling 01:13-03:44 −5,7 km/u (n=16); het kale model zat er +2,6 naast. Bij de ondergrens wordt een modelstoot van 120 km/u als 60 getoond en gemeld; de windmelding (drempel 60) kan een zware storm dan pas laat of niet melden.
- Voorstel (één of meer): (a) factor pas toepassen bij paren over ≥ 6 uur (nu ≥ 1 uur); (b) paren weglaten waar het model binnen het koppelvenster (45 min) meer dan ~20 % verandert (front-timing); (c) voor de windmelding de hoogste van model × factor en de laatste stationsmeting nemen, of alleen omlaag bijstellen tot hooguit 0,7. Eerst offline naspelen op de recorderreeksen van 09-10/10-10 (model-attribuut en `windstoten_gemeten`).
- Verwacht effect: geen ondergrens-factor uit één front; MAE na bijstelling < model-MAE in elk deelvenster.
- Meten na bouw: verwacht − gemeten per uur (KPI sc_windstoten_bias_kmh), factor per uur, en of een gemeten stoot ≥ 60 km/u ooit samenvalt met bijgesteld < 60.
- Aanvulling 10-10 07:40: 03:50-07:44 (n=24, per 10 min) bijgesteld −1,8 km/u (MAE 2,8; laatste 2 u 0,0 / 1,4) tegen kaal model **+10,0** (MAE 10,0); factor 0,53 → 0,55 (53 paren), even 0,64 bij 04:30. Bij rustig weer is ~0,55 dus juist: optie (c) met een vloer van 0,7 zou nu slechter zijn. Het probleem blijft de start op één front en wat er bij een zware storm (andere verhouding) gebeurt; (a)/(b) blijven de kern. Niets veranderd aan de status.

## L-SC-008 · windstoot-bijstelling: verhouding hangt af van de windsterkte
- Status: **open** (windmelding = meldgedrag: Ruud beslist)
- Onderbouwing: 10-10 07:44-11:44 (n=24 stationsmetingen Hupsel per 10 min, 0.51.1): bij aantrekkende wind loopt de vaste factor (mediaan gemeten/model over 24 u, 0,55 → 0,63) achter. Model < 28 km/u: verhouding gemeten/model mediaan **0,59** (n=9) — factor klopt (bijgesteld −2,2 km/u, MAE 2,2; kaal model +9,8). Model ≥ 31 km/u (10:00-11:44): verhouding mediaan **0,84** (n=10, 0,72-1,06) — bijgesteld **−8,6 km/u** (MAE 8,6), kaal model +4,7 (MAE 5,1). Laatste paar 11:40: model 37,1, bijgesteld 23,4, gemeten **39,3**. 0.52.0 (L-SC-007) lost dit niet op: ook zonder frontparen blijft het één factor over 24 uur, gedomineerd door rustige uren.
- Voorstel (één of meer): (a) factor per windklasse van het model (bv. < 25 / 25-40 / > 40 km/u), elk met eigen mediaan zodra ≥ 6 paren; (b) boven ~40 km/u model niet omlaag bijstellen (factor ≥ 1,0) zolang er geen paren in die klasse zijn; (c) voor de windmelding de hoogste van bijgesteld en de laatste stationsmeting. Eerst offline naspelen op 09-10/10-10 (attribuut `model` + `windstoten_gemeten`).
- Verwacht effect: bijgestelde stoten bij > 30 km/u binnen ±4 km/u i.p.v. −8,6; geen gemiste windmelding bij een zware storm doordat rustige uren de factor bepalen.
- Meten na bouw: bias/MAE per windklasse (KPI sc_windstoten_bias_kmh_klasse), en of een gemeten stoot ≥ 60 km/u ooit samenvalt met bijgesteld < 60.

