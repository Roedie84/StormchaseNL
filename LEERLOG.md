# Leerlog StormchaseNL

Doorlopende leerronde (elke 4 uur). Alleen gemeten getallen; KPI's in KPI.csv.

## 07-10 · samenvatting dag (3 tussenronden 23:15-23:45, baseline uit ~10 d)
- Gebeurtenis 07-10 21:15-22:37 (95 → 69 km, nooit < 50 km): 4× `onweer_nadert`, aankomst tot 41 min voorspeld, niet uitgekomen. Aankomst zaagtand door 10-s herhalingen in de snelheidsregressie (replay bevestigd, H-SC-1) → L-SC-001.
- Validatie sinds ~31-08: aankomst 1/6, passage 21/21 "uitgekomen" maar afstandsfout ~18,5 km; regen ≤15 min 4/4, 15-45 6/11, >45 11/15.
- Bronnen 10 d: korte storingen radar/open_meteo/buienradar; bronstatistiek begon bij elke herstart opnieuw → later L-SC-002.

## 08-10 · samenvatting dag (7 rondes; ingekort na 14 dagen)
- H-SC-1 extra steun: 3 van de 4 nadert-perioden duurden 14,8-15,0 min = `TREND_WINDOW`; past bij één nieuw punt dat 15 min in de regressie blijft hangen. L-SC-001 blijft open.
- Bug gevonden en gebouwd: radarbeeld ververste niet bij een nieuw frame (kenmerk las `data["path"]` i.p.v. `data["radar"]`); `image_last_updated` 4,7 u stil.
- Gebouwd 0.44.0: die fix + L-SC-002 (bronstatistiek per dag, 30 d, over herstarts, in diagnostics). 376 tests groen, workflow groen, HACS ververst.
- L-SC-002 eerste bewijs: `bronnen_per_dag` 08-10 radar 80 gelukt tegen 40 sinds de herstart van 07:03 → tellers lopen over de herstart door. Alle bronnen 100% (n=130). Verifiëren over een dag­grens.
- H-SC-2 (nieuw): de validatie telt een passage als "uitgekomen" zodra er een afstand gemeten is (`validatie.py` `passage_afgerond`: `uitgekomen = werkelijke_afstand is not None`). Daardoor is "passage 21/21" geen trefkans. Uit…
- L-SC-001 (0.45.0) actief; wacht op onweer.
- Geen release (tussenronde, niets acuut).
- Gebouwd 0.46.0: L-SC-003 (passage-trefkans op afstand: raak ≤10 km, apart ≤20 km, mediane/grootste afwijking; baseline uit bewaarde uitkomsten 5/12 en 7/12) + L-SC-004 (nieuw: `regen_begint_over` toont tijdens regen het begin…

## 09-10 · samenvatting dag (6 rondes; ingekort na 14 dagen)
- L-SC-002 geverifieerd: `bronnen_per_dag` heeft 08-10 en 09-10 apart (2 dagen, totaal opgeteld) → telt over herstarts én daggrens door.
- Meetfout gevonden: `validatie.py` bewaart MAX_UITKOMSTEN = 60 uitkomsten over álle soorten samen; het venster is vol (34 regen + 21 passage + 5 aankomst). Elke afgeronde regenvoorspelling (8-10 per regendag) duwt de oudste ui…
- H-SC-3 ongewijzigd (geen nieuwe afgeronde regenstart met bekende afwijking). L-SC-001 wacht op onweer.
- Geen release.
- Bronwissel regen: sinds 0.49.0 is de KNMI-nowcast de eerste bron; Buienradar alleen terugval (daarom Buienradar laatste succes 06:02). De regenvalidatie legt de bron niet vast → uitkomsten van vóór en na 06:03 lopen door elka…
- Regen: 1 nieuwe afgeronde uitkomst (04:52, nog Buienradar): "over 57 min", kwam na 25 min (−32 min). Afwijkingen nu 11 bekend, 10 negatief (regen eerder dan voorspeld); validatie 24/34. H-SC-3 ongewijzigd; KNMI-nowcast los me…
- L-SC-006 (venster per soort): 0.50.x geïnstalleerd → bouwen in de dagafsluiting van 10-10; onweer nog 21 passage / 5 aankomst in het venster.
- Geen release (tussenronde).

## 10-10 · samenvatting dag (6 rondes; ingekort na 14 dagen)
- Onweer 10-10: cellen op 64-93 km (13:45-15:40, 16:28-18:28, 20:34-22:59), 0 binnen 50 km → niveau groen terecht; aankomst 44 min en passage 88 km niet uitgekomen. L-SC-001: nadering wijzigde alleen bij nieuwe inslagen (3 meetpunten). Eerste snelheidsschatting 9,5 tegen ~32 en 83-108 tegen ~57 km/u → H-SC-6.
- Windstoten 0.51.0: factor startte op de ondergrens 0,50 na één frontpassage (+8,8 tot 01:12, −5,7 erna) → L-SC-007, gebouwd 0.52.0 (12:04): daarna −4,0..+0,7 km/u (MAE 4,3-5,0) tegen kaal model +9,5. Bij harde stoten (≥ 28-33 km/u) −6,5..−8,6 → H-SC-5 / L-SC-008.
- Regen KNMI: 19 voorspellingen, 16 uitgekomen, mediaan −7 min (12 te vroeg / 4 te laat) → H-SC-3.
- Bronnen 09-10 99,93 %, daarna 0 mislukt. Ring 50 km telde 17:31 dubbel (twee Blitzortung-instanties; uuranalyse). Geen release.

## 11-10 · samenvatting dag (6 rondes; ingekort na 14 dagen)
- Onweer 10-10 (afrekening): 3 cellen 46-93 km, 0 < 25 km, niveau terecht groen; 2 valse nadert-perioden zonder melding; validatie aankomst 0/1, passage 0/2. L-SC-001 geverifieerd (aankomst wijzigt alleen bij nieuwe inslagen). Gebouwd 0.52.1 (L-SC-009, afstandsreeks), actief als 0.52.2 vanaf 10:15. ~40 HA-herstarts (supervisor), 0 Stormchase-fouten; bronnen 10-10 100 %.
- Windstoten: dag 10-10 −2,3 (MAE 4,8) tegen kaal +10,9; H-SC-5 verworpen. 11-10 per blok +5,3 (nacht 03:45-07:45) / −1,8 / −3,7 / −2,6 / +1,0; derde nacht op rij +5 km/u → H-SC-7 (één factor voor dag en nacht) sterker → L-SC-008 / L-SC-010.
- Regen KNMI (H-SC-3): n=21 uitgekomen, mediaan −7 min (16 te vroeg / 5 te laat); groot deel is het meetvenster van `regent`.

## 12-10 · samenvatting dag (6 rondes; ingekort na 14 dagen)
- 11-10: 1 vals nadert-alarm (23 min, cel 94 → 69 km); bronnen 100 %. Windstoten 11-10 bias +0,6 (MAE 4,3) tegen kaal model +10,7. L-SC-008/H-SC-7-replay: windsterkte-factor verworpen; tijd-van-de-dag → L-SC-010.
- Release 0.53.0 (L-SC-008c windmelding op max(bijgesteld, station)); andere sessies 0.54.0 (L-SC-010 tijdvakfactor) en 0.54.2 (ensemble werkt).
- 12-10 droog, groen, 0 inslagen < 50 km; bronstatus "alles in orde". Windstoten per blok +0,6/+0,6/−1,6/+1,6/−0,1 km/u (MAE 1,4-2,7); avonddaling 17-19 u en nachtstijging blijven de zwakke plekken.
- Regen KNMI (H-SC-3) cumulatief n=28, mediaan −6,9 min (te vroeg).

## 13-10 11:30 · dagafsluiting 12-10 (uit analyse-bestand, toen niet weggeschreven)
- 12-10: 0 onweer < 50 km, 24 herstarts, bronnen 99,5 %. Windstoten uurgemiddelden +0,56 km/u (vóór 12:38 +0,84; tijdvakfactor +0,22); avond 17-19 u +3,1..+3,3 (windafname loopt achter).

## 21-10 19:40 · inhaalronde (dagafsluiting 13-10 t/m 20-10 + tussenronde 21-10)
- Gat 13-10 11:30 → 21-10: geen leerronden. Nagemeten uit recorder, statistiek en diagnostiek; actief **0.56.0** (sinds 19-10, laatste herstart 21-10 15:44).
- **Onweer 17-10** (enige gebeurtenis): cel 13:17-18:09, dichtstbij 30,5 km (15:17), max 71 inslagen < 50 km. Niveau groen, geen melding (> 30 km) en geen windmelding (max uurstoot 58,4) → terecht. `onweer_nadert` 13:35-14:23 (48 min) bij echte nadering 59,6 → 31 km = terecht.
- **H-SC-6 bevestigd (n=2):** eerste naderingssnelheid 13:35 **222 km/u** bij een celwissel (89,6 → 59,6 km in 8 min = andere cel), werkelijk ~35 km/u; aankomst 16 en 27 min → 0/2 uitgekomen. Zelfde patroon als 11-10 (54 tegen 35-38) → **L-SC-013** (open, Ruud).
- **Meetbaarheid passage:** 3 passages 17-10 (42,4 / 39,2 km voorspeld) zonder gemeten afstand terwijl de inslagen op 36-42 km lagen; afronding zoekt de kleinste afstand van hetzelfde cel-id → bij id-wissel geen meting → **L-SC-012** (zelf bouwen: meetfout).
- Bronnen per dag 99,15-99,96 % (13-10 DNS-storing, 19-10 Open-Meteo 503: extern, hersteld). Radar 20-10: 485 wissels, mediaan 3,0 min, max 7,8. Locatie: 89× 9-13 s "laatst bekend" bij herstarts, 0× thuis.
- **L-SC-010 geverifieerd:** nachtbias 13-20/10 −1,2 km/u gemiddeld (−3,3..+0,8) tegen +2,5..+5,4 vóór 0.54.0; dag −0,7. 8 dagen bias −0,9, MAE 2,7 (uurgemiddelden; winderige week).
- **L-SC-011 (0.56.0) niet actief:** `regencorrectie.vorm` geen; leave-one-out 10,3 → 9,6 (verschuiving, −7 %) / 9,3 min (verhouding, −9,7 %), eis −10 %. KNMI-regen mediaan −7 min (46 uitgekomen, 33× eerder dan voorspeld). Eerste uitkomsten na 0.56.0 (20/21-10): −5, −7, +8, +18. H-SC-3 blijft; geen voorstel tot ≥ 10 nieuwe uitkomsten.
- Hypotheses: H-SC-3 (regenstart te laat voorspeld; correctie net onder de drempel), H-SC-6 (snelheid na celwissel), H-SC-8 nieuw (passage niet gemeten bij cel-id-wissel). Geen release (geen acute fout).

laatste ronde: 21-10 19:40, gemeten t/m 21-10 19:45

## 21-10 23:40 · tussenronde
- Geen onweer (0 inslagen < 50 km, niveau groen, ensemble 0 %); alleen beschikbaarheid gemeten. Actief 0.56.0; 2 herstarts (20:16, 20:58), locatie 10 s "laatst bekend", 0× thuis.
- Bronnen 21-10 t/m 23:43: alle ≥ 99,7 % (knmi_nowcast 1 mislukt, radar 4); KNMI-push verbonden, radarbeeld 2 min oud.
- Windstoten 19-23 u: bias +0,4 km/u, MAE 1,2 (n=4 uur; wind neemt toe 24 → 31 km/u). L-SC-010 houdt ook bij toenemende wind.
- Regen: 0 nieuwe uitkomsten sinds 19:40. Lange horizon (> 45 min, vrijwel altijd "57 min") 16 van 28 uitgekomen (57 %); vandaag 14:52 en 17:27 niet uitgekomen. Geen melding (rain_lead 10 min) → geen vals alarm voor Ruud; alleen KPI. H-SC-3 blijft (4 uitkomsten na 0.56.0, nodig ≥ 10).
- Radarvooruitblik: status "wacht op radarbeeld" met 0 frames sinds de herstart; code: bouwt alleen na bekijken (bewust, scheelt kaartverzoeken). Status-tekst misleidend, geen fout.
- Hypotheses: H-SC-3, H-SC-6, H-SC-8. Geen release; L-SC-012 (meetfout passage) blijft voor de dagafsluiting.

laatste ronde: 21-10 23:40, gemeten t/m 21-10 23:43

## 22-10 03:40 · dagafsluiting 21-10
- Dag 21-10: geen onweer (0 inslagen < 50 km, groen), alleen beschikbaarheid: bronnen 99,82 % (2.710 gelukt, 5 mislukt: knmi_nowcast 1, radar 4). Radarbeeld nu 3 min oud. Actief 0.56.0.
- Windstoten dag (24 uurgemiddelden): bias +0,89 km/u, MAE 2,16; nacht 00-07 +0,52, dag +1,07 → L-SC-010 houdt. Nacht 22-10 00-03: +2,35 (n=3) bij afnemende gemeten stoot (31 → 25) - het model loopt achter bij afname, zoals 12-10 17-19 u. Eén nacht, volgen.
- Regen: geen nieuwe uitkomsten sinds 17:27; L-SC-011 (0.56.0) nog niet actief (4 uitkomsten na 0.56.0, nodig ≥ 10).
- **Gebouwd 0.56.1 (L-SC-012, meetfout):** passage ook na een kenmerkwissel nagemeten via een opvolgercel (≤ 15 km van de laatste plek, ook ketens), uitkomst met `gemeten_via`; afrekenen ook in een ronde zonder cel als er een meting is. Drempels, voorspellingen en meldingen ongewijzigd. Suite 800 groen (7 nieuwe tests), workflow groen, HACS ververst. Effect: aandeel passages met afstand (nu 19/26 = 73 %) ≥ 90 % bij de volgende onweersdag.
- Hypotheses: H-SC-3 (regenstart te laat; correctie nog niet actief), H-SC-6 (snelheid na celwissel; L-SC-013 open), H-SC-8 (passage niet gemeten bij id-wissel → nu gebouwd, toets bij onweer).

laatste ronde: 22-10 03:40, gemeten t/m 22-10 03:45

## 22-10 07:40 · tussenronde
- Geen onweer (0 inslagen < 50 km, groen, ensemble 0 %); alleen beschikbaarheid. Actief **0.56.1** (geïnstalleerd, herstart 07:07); locatie: tracker.
- Bronnen: alle in gebruik ≥ 97 % (buienradar 97 cumulatief, rest ≥ 99 %); sinds 03:45 1× knmi_nowcast (time-out 06:49) en 1× radar (06:04) mislukt, direct hersteld. KNMI-push verbonden.
- Windstoten 03-07 u: bias −0,43 km/u, MAE 1,21 (n=4) bij weer toenemende gemeten stoot (25,8 → 29,4). Nacht 00-03 u was +2,35 bij afname → het model volgt met vertraging: bij afname te hoog, bij toename iets te laag. Wordt **H-SC-9** (traagheid, n=2 perioden); toets bij de volgende sterke toe-/afname.
- Regen: "over 72 min een bui (licht, 0,1 mm/u)" om 07:45 = weer de lange horizon (H-SC-3); uitslag volgende ronde.
- L-SC-012 (0.56.1) geïnstalleerd; toets wacht op een onweersdag.
- Hypotheses: H-SC-3 (regenstart lange horizon), H-SC-6 (snelheid na celwissel; L-SC-013 open), H-SC-8 (passage bij id-wissel; gebouwd, toets bij onweer). H-SC-9 genoteerd als kandidaat (max 3 lopend: vervangt H-SC-8 zodra die getoetst is). Geen release.

laatste ronde: 22-10 07:40, gemeten t/m 22-10 07:45

## 22-10 11:40 · tussenronde
- Geen onweer (0 inslagen < 50 km, groen, ensemble 0 %). Actief **0.57.0** (windvooruitblik, andere sessie 10:54; herstart ~11:03).
- Bronnen: DNS-storing 10:24-10:40 (knmi_nowcast, knmi_edr, meting elk 1× mislukt, direct hersteld). **Buienradar "hapert"**: laatste succes 06:50, 2 op rij mislukt (DNS), 96 % cumulatief; regen liep via KNMI-nowcast → geen gemis. Radar 23 mislukt van 21.849.
- **Regen (1 bui, H-SC-3):** start 09:50 (0,12 mm/u), bui 10:05-11:35 tot 1,56 mm/u. Voorspelde start: 07:40 "77 min" (→ 08:57, **53 min te vroeg**), 08:02 "52" (→ 08:54, 56 te vroeg), 08:47 "32" (→ 09:19, 31 te vroeg), 09:12 "32" (→ 09:44, 6), 09:47 "9" (→ 09:56, −6). Lange horizon dit keer te vróeg, tot nu toe meestal te laat → richting wisselt; ≤ 15 min klopt (± 6). Uitkomsten tellen mee voor L-SC-011 (actief bij ≥ 10).
- **Windstoten (H-SC-9):** uurgemiddelden 07-11 u model 31,1/29,8/34,9/36,9 tegen gemeten 23,3/27,8/31,8/36,5 → bias +7,7/+2,0/+3,1/+0,4 (gem. +3,3, MAE 3,3) bij **toenemende** wind. 03-07 u was −0,4 bij toename → "traag bij toename" niet bevestigd; model ligt vóór op de meting. H-SC-9 blijft kandidaat (wisselend teken, n=3 perioden).
- **Nieuw meetpunt windvooruitblik (0.57.0):** vandaag max 60 km/u om 13:00 (KNMI, klasse 1, gemeld); morgen 53, za 65 (open-meteo). Gemeten max tot nu 39,6 km/u. Toets 15:40: gemeten piek 12-15 u tegen 60.
- Hypotheses: H-SC-3 (regenstart lange horizon), H-SC-6 (snelheid na celwissel; L-SC-013 open), H-SC-8 (passage bij id-wissel; gebouwd 0.56.1, toets bij onweer). Geen release.

laatste ronde: 22-10 11:40, gemeten t/m 22-10 11:45

## 22-10 15:40 · tussenronde
- Actief 0.57.0 (herstarts 14:18, 14:34, 15:27 door installaties elders). **Onweer:** eerste inslagen < 50 km 14:34 (2), vanaf 15:20 snel groeiend tot 372 om 15:45; < 25 km 1 (15:41), < 10 km 0. Locatie tracker. KNMI groen (geen code), ensemble 0 %, onweersverwachting "Geen onweer verwacht" → de modellen misten het (CAPE 110-230).
- `onweer_nadert` aan 14:22 (cel 78 km; 12 min vóór de eerste inslag < 50 km), uit 14:36, aan 14:40-15:00, aan sinds 15:14. Afstand 46,2 (15:21) → 23,7 km (15:41) ≈ 67 km/u radiaal. Aankomst 15:43 "28 min" (→ ~16:11): uitslag volgende ronde.
- **H-SC-6 sterk bevestigd, nu ook voor de celsnelheid:** `celsnelheid` 14:20-15:34 37 % van de tijd > 120 km/u, max 407 (14:58), mediaan 42; `naderingssnelheid` max 137,6 (14:25). Code: zwaartepunt mag 40 km verspringen (`CONTINUITEIT_KM`), regressie al na 2 min → een snel groeiende cel geeft 150-400 km/u. Die waarde gaat de meldtekst in ("Cel trekt … met … km/u") en de passage. → **L-SC-014** (open: meldgedrag).
- Meetfout bij de herstart 15:27:18: `inslagen_binnen_50_km` 28 s lang 486 (ervoor 10, erna 11). n=1; code nalezen in de dagafsluiting.
- **Windvooruitblik (0.57.0), eerste toets:** vandaag 60 km/u om 13:00 voorspeld (KNMI, gemeld) tegen gemeten max 51,8 (12-13 u, Hupsel 2,6 km) → +8 km/u, drempel 60 niet gehaald = 1 vals alarm (n=1). Nu: vandaag 53, morgen 72 (19-24 u), za 67.
- Windstoten 11-15 u: bias +4,4 km/u (MAE 4,4) bij dalende meting (44,6 → 37,7) → past bij "te hoog bij afname" (H-SC-9-kandidaat, 3 van 4 perioden vandaag).
- Bronnen: buienradar hapert sinds 06:50 (5 op rij, DNS), 95 %; KNMI-nowcast dekt; rest ≥ 97 %. Radarbeeld 5 min oud.
- Hypotheses: H-SC-3 (regenstart lange horizon), H-SC-6 (snelheid bij celwissel en groei; L-SC-013 en L-SC-014 open), H-SC-8 (passage bij id-wissel, 0.56.1; uitslag van dit onweer in de dagafsluiting). Geen release.

laatste ronde: 22-10 15:40, gemeten t/m 22-10 15:45

## 22-10 19:40 · tussenronde
- Actief **0.58.2** (andere sessies: 0.57.1 L-SC-014 16:17, 0.58.0 L-SC-013 16:51, 0.58.1/0.58.2 wind). Locatie tracker. Nu groen, 51 inslagen < 50 km (oud), 0 < 25 km.
- **Onweer-uitkomst:** aankomst 15:43 "28 min" (→ 16:11) kwam niet uit: 0 inslagen < 10 km, < 25 km alleen losse inslagen (15:41, 16:00, 16:19, 16:26, 17:23). Aankomst liep 15:45-15:56 op 29 → 932 min en viel weg → de bui trok langs. Passage 15:36 voorspeld 2,2 km, werkelijk > 10 km → H-SC-8 (n=1, fout ≥ 8 km). KNMI-station meldde onweer 16:34-17:43.
- **L-SC-014 werkt:** `celsnelheid` na 16:17 0 % > 120 km/u (n=644, max 119,9) tegen 37 % eerder vandaag.
- **H-SC-6, nieuw restgat (L-SC-015 open):** 17:25-17:32 `naderingssnelheid` −124..−219 km/u bij een afstandsprong ~20 → 90 km zonder celwissel (oude inslag viel uit het venster); 17:44 sprong 45 → 38 km gaf +108 km/u → nadert/geel 17:41-18:00, aankomst 21 min, daarna 0 inslagen < 25 km = vals alarm (n=1). 18:17-18:22 nog 5 min geel met aankomst 326-543 min.
- **Meetfout bronstatus (L-SC-016, gepland):** "buienradar hapert" staat sinds ~10:24 terwijl KNMI-nowcast 100 % werkt; Buienradar is alleen reserve en wordt pas weer gevraagd als KNMI faalt (`rain.py`). Bouwen in de dagafsluiting.
- Windstoten 15-19 u bias +6,4 km/u (MAE 6,4) bij dalende meting 33 → 22 → "te hoog bij afname" nu 4 van 5 perioden (H-SC-9-kandidaat; wacht op vrije plek).
- Hypotheses: H-SC-3 (regenstart lange horizon), H-SC-6 (snelheid bij sprong; L-SC-015 open), H-SC-8 (passage; 1 misser vandaag). Geen release.

laatste ronde: 22-10 19:40, gemeten t/m 22-10 19:45

## 22-10 23:40 · tussenronde
- Actief **0.58.3** (L-SC-015, andere sessie 20:00; herstarts 20:10 en 22:11). Groen; laatste inslag < 50 km viel 20:52 uit het venster; geen onweer → aankomst, passage en L-SC-015 niet toetsbaar.
- Herstart-artefact (15:27: 486 inslagen): herstart 20:10 met 15 inslagen in het venster gaf geen sprong (n=1 schoon); 22:11 zonder inslagen niet toetsbaar.
- **Windstoten 20-24 u:** uurbias +5,0/+8,3/+3,3/+1,9 km/u (gem. +4,6, MAE 4,6). Groot bij dalende meting (15 → 11 km/u), klein bij stijgende (11 → 17) → "te hoog bij afname" nu 5 van 6 perioden vandaag (H-SC-9-kandidaat; wacht op vrije plek).
- **Windvooruitblik:** morgen 79 km/u (KNMI, klasse 2, > 60 van 20:00 tot 24:00; om 15:40 nog 72), za 69 (open-meteo). Toets morgenavond tegen het station.
- Bronnen: "buienradar hapert" staat nog (laatste succes 06:50, 5 op rij) terwijl knmi_nowcast 100 % → L-SC-016 blijft gepland. Zelfde patroon bij `meting` (Bright Sky): laatste succes 10:24, 0 op rij mislukt, "in gebruik" — reservebron die niet gevraagd wordt; meenemen in L-SC-016. Radar 100 %, beeld vers.
- Hypotheses: H-SC-3 (regenstart lange horizon), H-SC-6 (snelheid bij sprong; L-SC-015 gebouwd, toets bij onweer), H-SC-8 (passage). Geen release.

laatste ronde: 22-10 23:40, gemeten t/m 22-10 23:45

## 23-10 03:40 · dagafsluiting 22-10
- Actief 0.58.3 → **0.58.4 gereleased 03:47** (L-SC-016, workflow groen, HACS ververst; wacht op installatie). Geen onweer sinds 20:52; nu regen (KNMI-nowcast), groen.
- **Onweersdag 22-10 (n=1 gebeurtenis):** modellen misten het (KNMI groen, ensemble 0 %, CAPE 110-230); nadert 12 min vóór de eerste inslag < 50 km; aankomst "28 min" miste (bui trok langs, 0 < 10 km); passage-fout ≥ 8 km; 1 vals nadert-alarm na afstandsprong (→ L-SC-015, gebouwd). Celsnelheid > 120 km/u na 0.57.1 0 % (was 37 %). n te klein voor trefkans; elke volgende onweersdag telt.
- **Windstoten dag:** bias +3,57 km/u, MAE 3,86 (24 u). Bij dalende meting +5,47 (n=13), bij stijgende +1,22 (n=10).
- **H-SC-9 getoetst over 10 dagen (12..22-10, n=238 uur):** dalend +1,74, stijgend −1,46 km/u, 13 van 13 dagen dalend > stijgend; model(t) past even goed op gemeten(t−1) als op gemeten(t) (MAE 2,52/2,52) → het model loopt ~een half uur achter (traagheid, geen windsterkte-effect). Backtest "model + ½ × fout van het vorige uur": MAE 2,52 → 2,24 (−11 %), in beide helften beter → **L-SC-017 (open)**: raakt windmelding = meldgedrag → Ruud.
- **L-SC-016 gebouwd 0.58.4:** bronstatus stond 22-10 13,6 u (10:24-24:00) en nu nog steeds onterecht op "buienradar hapert"; meting (Bright Sky) "in gebruik" terwijl KNMI-EDR het werk doet. Effect na installatie meten.
- Windvooruitblik: 22-10 1 vals alarm (60 tegen 51,8 gemeten); vandaag 79 km/u 19-24 u (gemeld) → toets vanavond tegen het station.
- Niet gemeten: bronnen-slaagpercentage per dag (alleen in de diagnostiek, niet via een sensor); regenstart-uitkomsten (validatie niet als attribuut).
- Hypotheses: H-SC-3 (regenstart lange horizon), H-SC-8 (passage), H-SC-9 (windstoten traag → L-SC-017). H-SC-6 → toets L-SC-015 bij het volgende onweer.

laatste ronde: 23-10 03:40, gemeten t/m 23-10 03:50

## 23-10 07:40 · tussenronde
- Actief **0.59.0** (L-SC-017, andere sessie 07:12 na akkoord Ruud; actief na de herstart van 07:39). Groen, geen inslagen < 50 km, lichte regen (KNMI-nowcast).
- **L-SC-016 effect:** bronstatus 07:43 "alles in orde" (was sinds 22-10 10:24 "buienradar hapert") → 0 uur vals "hapert" sinds installatie. Volle dag meten in de dagafsluiting.
- **Windstoten 03-07 u (vóór L-SC-017):** bias −2,6/−1,3/−2,0/−3,8 km/u (gem. −2,4, MAE 2,4) bij stijgende meting 19,7 → 26,3 → zelfde traagheid als H-SC-9 (te laag bij toename). Dit is de laatste ongecorrigeerde reeks; vanaf 07:39 meten wat L-SC-017 doet (MAE/bias per trend, 7 d voor/na).
- Windvooruitblik vandaag 75 km/u (03:40: 79); toets vanavond tegen het station.
- Hypotheses: H-SC-3 (regenstart lange horizon), H-SC-8 (passage), H-SC-9 (windstoten traag → L-SC-017 gebouwd). Geen release.

laatste ronde: 23-10 07:40, gemeten t/m 23-10 07:45

## 23-10 11:40 · tussenronde
- Actief **0.59.0** (geen nieuwe release). 0 Stormchase-logregels. Droog, geen inslagen < 50 km, ensemble 0 %; niveau **geel** sinds 08:39 door de KNMI-weerwaarschuwing (wind), windvooruitblik 75-81 km/u voor vanavond.
- **L-SC-017 eerste effect:** uurgemiddelden 08-11:44 bias −0,6/+0,2/+0,1/−0,2 km/u (MAE **0,28**, n=4) bij sterk aantrekkende wind (28,7 → 36,8), tegen 05-08 u −2,0/−3,8/−3,9 (MAE 2,93) in dezelfde stijgende reeks. Per stationsmeting (10 min) MAE 1,21 (n=23) tegen 4,75 vóór 07:39 (n=8). Kanttekening: de verwachting wordt op dezelfde tijdstippen als de meting bijgesteld → dit meet vooral het "nu"; de vooruitblik (79 km/u vanavond) is de echte toets.
- **L-SC-016:** bronstatus "alles in orde" sinds 07:43 → 0 uur vals "hapert". Statuswissels komen niet in de recorder; volle dag in de dagafsluiting via de bronstatus-attributen.
- Radar-vooruitblik laatst ververst 08:27 (droog sinds ~08:30) — lijkt bedoeld (alleen bij regen); in de dagafsluiting nalezen.
- Hypotheses: H-SC-3 (regenstart lange horizon), H-SC-8 (passage), H-SC-9 (windstoten traag → L-SC-017: eerste 4 uur duidelijk beter). Geen release.

laatste ronde: 23-10 11:40, gemeten t/m 23-10 11:45

## 23-10 15:40 · tussenronde
- Actief **0.59.1** (11:48, andere sessie; dashboardstrategie). 0 Stormchase-logregels. Geen inslagen < 50 km, ensemble 0 %; niveau **geel** (KNMI-wind), windvooruitblik 74-87 (nu 80) voor vanavond.
- **L-SC-017 middag:** per stationsmeting bias −2,12, MAE 2,67 km/u (n=23; ochtend 1,21); uurgemiddelden 11 −0,3, 12 +0,3, 13 −1,8, **14 −2,9, 15 −5,5** bij vlagerige toename 31,5 → 48,8. Vooraf (10 min vooruit) MAE 3,55. Halve correctie haalt een aanhoudende stijging niet bij; vóór L-SC-017 was het patroon hetzelfde (H-SC-9). Dag-MAE 03:40 vergelijken met 22-10 (3,86).
- **Regenstart (H-SC-3), 1 bui:** 13:12 "over 57 min" → regen 14:05 (5 min eerder); 13:37 "over 24" +4, 13:59 "over 11" −5 → ±5 min op 1 uur. Licht (0,1-0,4 mm/u) tot 15:03. Volgende: 15:03 "over 54" (→ 15:57).
- Bronstatus 15:42 "alles in orde" (L-SC-016 houdt).
- Hypotheses: H-SC-3 (regenstart lange horizon: deze bui goed), H-SC-8 (passage), H-SC-9 (windstoten traag → L-SC-017; middag weer −3..−5,5). Geen release.

laatste ronde: 23-10 15:40, gemeten t/m 23-10 15:45

## 23-10 19:40 · tussenronde
- Actief **0.59.1**. 0 Stormchase-logregels. Geen inslagen < 50 km, ensemble 0 %; niveau **geel** (KNMI-wind). Regen sinds 16:08 (piek 6,5 mm/u), nu matig.
- **Windstoten (L-SC-017 / H-SC-9):** per stationsmeting 15:44-19:34 bias **−5,15**, MAE 5,15 km/u (n=22, alle te laag); per uur −2,4/−3,3/−4,9/**−8,2**/−4,2 bij meting 35-50 km/u (geen sterke stijging meer na 17 u). Het is dus niet alleen traagheid: het niveau is vandaag te laag (front, tijdvakfactor 0,58 tegen 24-u 0,67). Halve bijsturing laat de helft van een aanhoudende fout staan. Dagbeeld (en MAE tegen 22-10 3,86) 03:40; nog geen voorstel (n=1 dag).
- **Windvooruitblik** 78-81 km/u (piek 22:00, > 60 vanaf 19:00); gemeten tot 19:34 max 50,5 → toets in de dagafsluiting.
- **Regenstart (H-SC-3), 2 buien (16:08, 17:28):** horizon 15-30 min telkens te vroeg voorspeld, regen +6..+16 min later (n=6, gem. +9); < 5 min +1. Ochtendbui (13-14 u) was ±5 → n=3 buien, nog geen richting.
- **Nieuw (rapportage):** radar-vooruitblik laatst gebouwd 15:50 (geen kijker = bewust), maar attribuut `referentietijd` 19:35 en status "actueel" → dashboardchip noemt een tijd die niet bij het beeld hoort → **L-SC-018** (gepland, dagafsluiting).
- Hypotheses: H-SC-3 (regenstart: 15-30 min te vroeg?), H-SC-8 (passage), H-SC-9 (windstoten: traagheid + vandaag niveaufout bij front). Geen release.

laatste ronde: 23-10 19:40, gemeten t/m 23-10 19:45

## 23-10 23:40 · tussenronde
- Actief **0.59.1**. Geen Stormchase-logregels. Geen inslagen < 50 km; niveau geel → **groen om 23:32** (KNMI-waarschuwing voorbij). Lichte regen.
- **Windstoten (L-SC-017 / H-SC-9):** per stationsmeting 19:44-23:34 bias **−1,92**, MAE 3,61 (n=24; 19:40-ronde −5,15). Per uur −5,0/−5,4/−3,5 bij aantrekkende wind (19-21 u), **+1,0/+2,7** bij afnemende (22-23 u) → past bij traagheid (te laag bij stijgen, te hoog bij dalen), niet bij een vaste niveaufout.
- **Windvooruitblik:** 76-84 km/u (piek schoof 22:00 → 23:00); gemeten max **64,9** (21:24), > 60 vanaf 20:44 (5×) → piek 15 km/u te hoog, starttijd ~1,5 u te vroeg. Open-meteo rekent open veld; het weerstation staat in de tuin. n=1 dag; afrekening in de dagafsluiting (toets 22-10 erbij).
- Radar-vooruitblik: beeld 22:53, `referentietijd` 23:40, status "actueel" (L-SC-018 gepland).
- Hypotheses: H-SC-3 (regenstart; geen nieuwe bui), H-SC-8 (passage), H-SC-9 (windstoten: traagheid bevestigd in de avond). Geen release.

laatste ronde: 23-10 23:40, gemeten t/m 23-10 23:45

## 24-10 03:40 · dagafsluiting 23-10
- Actief 0.59.1 → **release 0.59.2** (03:49, workflow groen, HACS ververst; wacht op installatie): frontterugval windfactor (bug, L-SC-019) + L-SC-018. Geen onweer; niveau geel 08:39-23:32 (KNMI-wind), nu groen.
- **Windstoten dag:** bias −2,17 km/u, MAE **2,50** (22-10 3,86; 10 d 2,52). Stijgend n=16 −2,82, dalend n=7 −0,94. Eerste hele dag met L-SC-017: op een dag met vooral stijgende wind geen winst zichtbaar (n=1); 7-daagse toets loopt.
- **Bug gevonden (03:24):** na ~20 uur doorlopende frontvlag had het 24-uursvenster < 6 uur rustige paren; factor 0,70 viel weg en *Windstoten* sprong 43 → **64,4 km/u** (kaal model) bij 35,3 gemeten; windmelding-waarde ook 64,4 (> drempel 60). Strijdig met de bedoeling van L-SC-007 ("factor mag bij een front niet springen") → gebouwd 0.59.2: tijdens een front de rustige paren van 72 uur, zelfde eisen.
- **H-SC-10 (nieuw):** 136 paren in het 24-uursvenster telden als front of naloop (~22 uur bij 10 min per paar) bij een geleidelijk aantrekkende storm; een front hoort uren te duren, geen dag. Toets: uren frontvlag per dag tegen druk/stootsprong in de historie.
- **Windvooruitblik:** 76-84,6 km/u tegen gemeten max 64,9 → drempel terecht, piek ~20 km/u te hoog (open veld tegen tuinstation; n=1, 22-10 vals alarm 60 tegen 51,8). Nog geen voorstel.
- **L-SC-016 geverifieerd:** 0 uur vals "hapert" (22-10: 13,6 u). Regenstart (H-SC-3): 3 buien, lange horizon 2× te vroeg (+6..+16 min).
- Hypotheses: H-SC-3 (regenstart lange horizon), H-SC-9 (windstoten traagheid; L-SC-017 loopt), H-SC-10 (frontvlag te lang). H-SC-8 (passage) wacht op onweer.

## 24-10 07:40 · tussenronde (niet gemeten)
- HA-MCP kon niet verbinden (502 bij opbouw van de verbinding) → geen history, logs of dashboard; niets gemeten, geen release, dashboardkaart niet bijgewerkt. Volgende ronde meet door vanaf 03:55 (recorder bewaart ~10 d, dus geen verlies).

laatste ronde: 24-10 07:40, gemeten t/m 24-10 03:50

## 24-10 11:40 · tussenronde
- Actief **0.59.2** (sinds herstart 07:41). Geen Stormchase-logregels. Geen onweer, 0 inslagen < 50 km; niveau de hele ronde groen. Bronstatus "alles in orde" (min. 99 %).
- **L-SC-019 geverifieerd:** vóór de installatie (03:54-07:34) gaf het kale model 46,8-64,4 km/u bij 29,6-43,6 gemeten: bias **+19,0** (n=23). Na 07:41: bias **+1,5**, MAE 3,61 (n=24); factor uit het tijdvak van 72 u (0,76).
- **H-SC-10 (frontvlag te lang):** om 11:43 nog `front` true, 139 frontparen tegen 4 rustige in 24 u → ~97 % van het venster "front" bij een gestaag aanwakkerende wind. Steunt de hypothese; toets in de dagafsluiting tegen druk/stootsprong.
- **Windvooruitblik:** vandaag 65 (23-24 u), morgen 69 km/u (10 u > 60); melding vandaag klasse 1 (73). Gemeten max tot 11:40 43,6. 3e toets van "piek te hoog" vannacht (n=2: +8 en +20 km/u).
- **L-SC-018 niet toetsbaar:** na de herstart geen kijker → geen beeld; status blijft "wacht op radarbeeld" met referentie 11:40 beschikbaar. `gebouwde_stand` past alleen "actueel" aan → **L-SC-020** (gepland, dagafsluiting).
- Hypotheses: H-SC-3 (regenstart lange horizon; droog), H-SC-9 (windstoten traagheid; L-SC-017 loopt), H-SC-10 (frontvlag te lang). Geen release.

laatste ronde: 24-10 11:40, gemeten t/m 24-10 11:45

## 24-10 15:40 · tussenronde
- Actief **0.59.2**. Geen Stormchase-logregels. Geen onweer, 0 inslagen < 50 km; niveau groen; bronstatus "alles in orde". Droog.
- **Front voorbij ~12:53** (11:43 nog `front` true, 15:34 false) → H-SC-10: frontvlag besloeg ~24-10 tot het middaguur een groot deel van 24 u (126 frontparen); toets in de dagafsluiting.
- **Bug (L-SC-021):** na het front is het 24-uursvenster nog vol front-/naloopparen (17 rustige, 2,7 u). `factor_tijdens_front` (0.59.2) werkt alleen zolang het laatste paar front is → factor valt weg, kaal model. 12:53:58 sprong 40,3 → **51,8 km/u** bij 39,7 gemeten. Per stationsmeting: 11:43-12:44 bias −0,6 / MAE 2,0 (n=7); 12:53-15:34 **+6,6 / MAE 7,7** (n=16). Met factor 0,82: −2,2 / MAE 5,2. Herstelt vanzelf na ~6 u rustig (~19 u), geen melding geraakt (< 60).
- **Klaargezet (branch `wip/l-sc-021`, suite 917 groen):** L-SC-021 (terugval op 72 u zolang het 24-uursvenster frontparen bevat; meetgat zonder front ongewijzigd) + L-SC-020 (status "nog niet gebouwd (geen kijker)" na een herstart). Release in de dagafsluiting (0.59.3).
- Windvooruitblik 68 km/u; gemeten max 11:45-15:34 51,7.
- Hypotheses: H-SC-3 (regenstart lange horizon; droog), H-SC-9 (windstoten traagheid; L-SC-017 loopt), H-SC-10 (frontvlag te lang). Geen release (tussenronde).

laatste ronde: 24-10 15:40, gemeten t/m 24-10 15:45

## 24-10 19:40 · tussenronde
- Actief **0.59.2**. Geen Stormchase-logregels. Geen onweer, 0 inslagen < 50 km; niveau groen; bronstatus "alles in orde". Droog.
- **L-SC-021 groter dan gedacht:** na het einde van het front (12:53) bleef het kale model staan tot **18:43**; 15:44-18:34 bias **+17,3 km/u** (n=18, model 40-51,5 bij gemeten 24,5-40). Niet vanzelf hersteld: om 18:34 nog maar 5,7 u rustig, daarna een nieuw front. Replay met de tijdvakfactor (0,56, wat L-SC-021 gebruikt): **−3,4 / MAE 3,6**. Geen melding geraakt (< 60). Fix ligt klaar op `wip/l-sc-021` → release 0.59.3 in de dagafsluiting; risico tot dan: na het volgende frontende weer het kale model (vooruitblik 71 km/u).
- **Nieuw front 18:43** (druk −2,8 hPa/3 u): tijdvakfactor 0,53-0,56 + bijsturing → bias **−6,9** (n=7); kaal +6,7. Een factor uit rustige uren is tijdens een front te laag → past bij H-SC-9/H-SC-10, nog geen voorstel (n=7).
- **Regenstart (H-SC-3):** aftelling liep van 64 naar 14 min (18:58) en sprong dan naar 84; geen regen t/m 19:52 → 1× vals (bui verdween/schoof). Nu weer 28 min.
- Hypotheses: H-SC-3 (regenstart lange horizon), H-SC-9 (windstoten traagheid / front), H-SC-10 (frontvlag te lang). Geen release (tussenronde).

laatste ronde: 24-10 19:40, gemeten t/m 24-10 19:50

## 24-10 23:40 · tussenronde
- Actief **0.59.2** (geen herstart sinds 10:16). Geen Stormchase-logregels. Geen onweer, 0 inslagen < 50 km; niveau groen; bronstatus "alles in orde".
- **Regenstart (H-SC-3): treffer.** 19:50 aftelling 28 min → regen vanaf 20:23 (33 min, fout +5); 19:58 24 → 25 min. Regent sindsdien licht (max 3,5 mm/u 21:34). Radar-vooruitblik nog van 08:16Z (L-SC-020 → 0.59.3).
- **Windstoten tijdens het front (18:43-23:44, n=32):** verwachting vóór elke stationsmeting bias **−6,4 / MAE 6,7**. Gemeten/model mediaan 0,81, gebruikte tijdvakfactor 0,51-0,69 (uit rustige uren). Replay met de eerdere frontparen van dit front: +0,5 / MAE 3,4 → **L-SC-022** (open, Ruud; n = één front). Gemeten max **59,6** (23:24), windmelding volgde de stationsmeting (bron station) → geen gemiste melding.
- Hypotheses: H-SC-3 (regenstart; 1 vals 18:58, 1 treffer 20:23), H-SC-9 (windstoten traagheid / front → L-SC-022), H-SC-10 (frontvlag; front loopt nog, `paren_front` 109). Geen release (tussenronde); 0.59.3 (L-SC-020/021) in de dagafsluiting.

laatste ronde: 24-10 23:40, gemeten t/m 24-10 23:45

## 25-10 03:40 · dagafsluiting 24-10
- Actief **0.59.2**; **release 0.59.3** (03:46, L-SC-020 + L-SC-021; suite 917 groen, workflow groen, HACS ververst; wacht op installatie). Geen Stormchase-logregels; de DNS-storing van ~00:45 raakte alleen `knmi_waarschuwingen` 1×. Bronstatus "alles in orde".
- Dag 24-10: geen onweer (0 inslagen < 50 km), niveau groen. Regen: 1 vals (18:58, bui verdween), 1 treffer (20:23, +5 min).
- **Windstoten 24-10 per stationsmeting (n=134): bias +5,6 km/u.** Zonder de twee kale-modelperioden (03:24-07:41 +19,0, n=23; 12:53-18:43 +6,6/+17,3, n=34): **−1,3** (n=77). Beide perioden zijn nu gedekt (0.59.2 en 0.59.3).
- **Front-nacht 23:54-03:44 (n=29): bias −0,0, MAE 4,4** (tijdvakfactor 0,70-0,74 + bijsturing) tegen −6,4 / 6,7 in 18:43-23:44 → L-SC-022 minder overtuigend: het avondtekort trok vannacht bij. Blijft open; ≥ 3 fronten nodig.
- **Windmelding: hit.** 00:54 stationsmeting 65,8 → `windstoten_melding` 65,8 (bron station; verwachting 54,8); vooruitblik stond al op 72-75. Daarna 63,6 (01:24), 60,0 (01:44). Niveau bleef groen (KNMI geen code). Piek 24-10 zelf: gemeten max 59,6 (23:24) tegen vooruitblik 65 → +5,4 te hoog (n=3: +8, +20, +5).
- Radar-vooruitblik nog "wacht op radarbeeld", frames 0, sinds 24-10 10:16 (17,5 u; L-SC-020 → 0.59.3).
- Hypotheses: H-SC-3 (regenstart), H-SC-9 (windstoten traagheid / front → L-SC-022), H-SC-10 (frontvlag te lang: `front` true sinds 18:43, `paren_front` 109). Release 0.59.3.

laatste ronde: 25-10 03:40, gemeten t/m 25-10 03:50

## 25-10 07:40 · tussenronde
- **HA herstart 06:00 CET: 0.59.3 actief.** Geen Stormchase-logregels. Geen onweer, 0 inslagen < 50 km; niveau groen; bronstatus "alles in orde".
- **L-SC-020 geverifieerd:** vooruitblik na de herstart "nog niet gebouwd (geen kijker)", `referentie_beschikbaar` 06:40Z, frames 0 (was "wacht op radarbeeld").
- **L-SC-021 deels:** na de herstart `factor_bron` "tijdvak" (0,78), gecorrigeerd - geen kaal model. Front nog niet voorbij volgens de vlag, dus de echte toets (frontende → 6 u) volgt.
- **Windstoten 03:44-07:34 (n=24): bias +3,3, MAE 5,4.** Wind zakte 61 → 25 km/u: 03:44-05:54 +4,7/6,6 (n=14), 06:04-07:34 +1,4/3,7 (n=10). Bij dalende wind loopt de verwachting achter (te hoog), bij stijgende (24-10 avond) te laag → H-SC-9 (traagheid) consistent. Piek 04:03 gemeten 61,4 tegen verwachting 52,9 (−8,5).
- **H-SC-10:** `front` true sinds 24-10 18:43 (13 u) terwijl de druk al stijgt (+2,4 hPa/3 u) en de wind zakt.
- Regen: droog sinds 05:38 (piek 5,4 mm/u 04:23). Aftelling 07:27 70 min → 07:42 40 min; toets 11:40 (H-SC-3).
- Hypotheses: H-SC-3, H-SC-9 (→ L-SC-022), H-SC-10. Geen release (tussenronde).

laatste ronde: 25-10 07:40, gemeten t/m 25-10 07:45

## 25-10 11:40 · tussenronde
- 0.59.3 actief; vier HA-herstarts (09:29-10:53) zonder Stormchase-logregels. Geen onweer, 0 inslagen < 50 km; niveau groen; bronstatus "alles in orde"; radar 10:42Z vers.
- **H-SC-10:** frontvlag ging om **07:44** uit (aan sinds 24-10 18:43 → 13,0 u). `paren_front` 109 → 84.
- **L-SC-021 geverifieerd:** na het frontende en na elke herstart `factor_bron` "tijdvak" (0,76-0,80), `gecorrigeerd` true - nooit kaal model.
- **Windstoten 07:44-11:43 (n=25): bias +0,2, MAE 3,9 km/u** (was 5,4 in 03:44-07:34). Wind steeg 22 → 50 km/u: 10:03-10:34 4× −2..−6 (achter bij stijging, H-SC-9), uitschieters 08:54 −11,8 (vlaag 40,4) en 11:43 +8,7 (daling 47 → 39). Geen windmelding (max gemeten 50,5 < drempel); vooruitblik 63.
- **Regen (H-SC-3):** aftelling 07:42 "40 min" (→ 08:22) - bui begon 08:42 (0,36 mm/u): treffer, **+20 min te vroeg** voorspeld (08:02 "35" → 08:37: +5 min). Aftellingen 09:42-10:47 (57 → 13 min) **vals** (geen neerslag na 09:07). Nu 32 min (11:42, licht).
- Hypotheses: H-SC-3 (regenstart; 1 treffer, 1 vals), H-SC-9 (traagheid bij stijgende wind → L-SC-022), H-SC-10 (frontvlag 13 u; uitslag gemeten). Geen release.

laatste ronde: 25-10 11:40, gemeten t/m 25-10 11:45

## 25-10 15:40 · tussenronde
- 0.59.3 actief; geen herstart. Bronstatus "alles in orde" (DNS-storing 13:07: Buienradar-reserve en KNMI-nowcast 1× mislukt, opgevangen).
- **Onweer (n=1 gebeurtenis):** eerste inslag 13:36 op 96 km; dichtste **29,2 km NO om 14:10**; 12 binnen 50 km om 14:13, 13e om 15:18; 0 binnen 25 km. Niveau bleef terecht groen (buiten de waarschuwingsafstand), behalve 15:04-15:14.
- **Gemist in de verwachting:** "Geen onweer verwacht", ensemble 0 %, bliksempotentie 0,0, terwijl TT 55,4, LI 1,0, CAPE 70 (koude lucht na het front). Lead-time 0. → **H-SC-11** (n=1; meer gevallen nodig).
- **Vals "nadert" 15:04-15:14** (geel, aankomst 762-1593 min) en **"trekt snel weg" om 14:36** (−6,2 km/u): de dichtste inslag (14:10) lag stil; alleen de tracker verschoof 0,2-0,4 km, en elke nieuwe inslag verder weg gaf een regressiepunt met die verschoven afstand (`Naderingstrend.bij`, sleutel = nieuwste inslag). Replay met de recorderreeksen: oud max +2,3 / min −6,2 km/u, met de fix |v| ≤ 1 → **L-SC-023** (bug, zelf gebouwd, klaargezet op `wip/l-sc-023`, suite 922 groen; release 0.59.4 in de dagafsluiting).
- Meetbaarheid: `afstand` toont de dichtste inslag ongeacht leeftijd (14:10 → nog 29,3 km om 15:44); geen leeftijd van die inslag als attribuut.
- Regen: regent licht (0,8 mm/u), volgende bui over 17 min. Wind gemeten 37,8 / verwachting 42,5 km/u (niet als reeks gemeten deze ronde).
- Hypotheses: H-SC-3 (regenstart), H-SC-9 (windstoten traagheid → L-SC-022), H-SC-11 (koude-lucht-onweer gemist; H-SC-10 frontvlag afgesloten 11:40). Geen release (tussenronde; L-SC-023 wacht op 03:40).

laatste ronde: 25-10 15:40, gemeten t/m 25-10 15:45

## 25-10 19:40 · tussenronde
- 0.59.3 actief; HA herstartte 15:54, 16:09, 17:25 en 18:47 (installaties EMS/Gold Scalper elders) zonder Stormchase-logregels. Bronstatus "alles in orde".
- **Onweer 25-10 afgelopen:** binnen 50 km 13 → 0 (16:10-17:18, vanzelf verouderd); daarna nog een cel op **91-94 km** (17:34-17:49, inslagfrequentie 0,2-2,6/min), na 17:54 geen inslagen meer.
- **Vals alarm 17:43:35-17:54:26 (11 min):** dichtste inslag 93,6 → 91,0 km (echte nieuwe inslag, 2,6 km) → `trend` "nadert snel" 13,8 km/u, aankomst 396-419 min → `onweer_nadert` aan → **waarschuwingsniveau geel, `weerwaarschuwing` aan en verwachting "Onweer in de buurt (gemeten)"** bij 91 km en 6,6 u aankomst. Celsnelheid in die minuten 2-10 km/u. Oorzaak in de code: `gemeten_onweer()` (0.58.0) telt elke nadering, zonder afstands- of aankomstgrens (alleen de pushmelding heeft `notify_max_distance`). L-SC-023 (ruis < 0,5 km) dekt dit niet. Samen met 15:04-15:14 (29 km, aankomst 762-1593 min) **2 valse geel-perioden vandaag** → **L-SC-024** (open: meldgedrag).
- **Windstoten 15:54-19:44 (n=24): bias +1,2, MAE 4,0 km/u.** Dalend 15:54-16:54 (50 → 27): +3,5..+12,6 te hoog; stijgend 17:33-18:03 (33 → 42): −4,2..−7,3 te laag; daarna rustig ±1-4. Patroon gelijk aan H-SC-9 (traagheid in beide richtingen).
- **Regen (H-SC-3):** aftelling 17:17 "67 min" (→ 18:24), bui begon 18:17 (0,24 mm/u) → treffer, **7 min te laat**; 17:37 "37" → +3 min. Aftelling 16:40-16:57 (29 → 12 min) **vals** (droog 16:47-18:17). Nu droog, volgende bui over 77 min (licht).
- Hypotheses: H-SC-3 (regenstart; vandaag 3 treffers, 2 vals), H-SC-9 (windstoten traagheid → L-SC-022), H-SC-11 (koude-lucht-onweer gemist, n=1). Geen release (tussenronde; L-SC-023 wacht op 26-10 03:40).

laatste ronde: 25-10 19:40, gemeten t/m 25-10 19:45

## 25-10 23:40 · tussenronde
- 0.59.3 actief; geen herstart sinds 18:47. Bronstatus "alles in orde" (hele ronde, geen wisseling). Radar vers (22:42Z).
- **Geen onweer:** 0 inslagen < 50 km 19:44-23:44, niveau groen, `weerwaarschuwing` uit; `afstand`/`trend` nu unknown (geen inslagen meer in het venster). Geen valse geel-perioden deze ronde (dag 25-10: 2, zie L-SC-024).
- **Windstoten 19:44-23:34 (n=24): bias −1,0, MAE 1,6 km/u** (laagste MAE van de dag; 15:54-19:44: 4,0). Licht stijgend 22 → 37 km/u: grootste fouten bij de vlagen 21:24 (−4,2; 35,2 gemeten) en 23:34 (−3,8; 37,0) → verwachting loopt achter bij stijging (H-SC-9). Geen windmelding (vooruitblik 43).
- **Regen (H-SC-3):** 3 buien. 21:27 (0,24 mm/u): aftelling 21:22 "12" → 21:34 = treffer, 7 min te laat. 21:47 (0,12 mm/u): aftelling 21:37 "72" → 22:49, om 21:42 weg → **gemist** (lichte bui, 15 min). 23:17 (0,48 mm/u): aftelling 22:22 "57" → 23:19 (+2), 23:02 "22" → 23:24 (+7) = treffer. Vals: 0. Dag 25-10 nu: 5 treffers, 2 vals, 1 gemist.
- Hypotheses: H-SC-3 (regenstart; treffers 2-7 min te laat bij lichte buien), H-SC-9 (windstoten traagheid → L-SC-022), H-SC-11 (koude-lucht-onweer gemist, n=1). L-SC-023 (wip, suite groen) wacht op de dagafsluiting 26-10 03:40. Geen release.

laatste ronde: 25-10 23:40, gemeten t/m 25-10 23:45

## 26-10 03:40 · dagafsluiting 25-10
- **Release 0.59.4** (03:43, L-SC-023: GPS-ruis geeft geen vals nadert/wegtrek meer; suite 922 groen, workflow groen, HACS ververst; wacht op installatie). Actief nog 0.59.3; geen Stormchase-logregels.
- **Dag 25-10 onweer (n=1 gebeurtenis):** 13:36-17:54, dichtste 29,2 km (14:10), max 13 < 50 km, 0 < 25 km → niveau terecht groen, op **2 valse geel-perioden** na (15:04-15:14 ruis bij 29 km → 0.59.4; 17:43-17:54 bij 91 km, aankomst 6,6 u → L-SC-024 open). 21 min vals geel, 0 terecht. Verwachting miste het (ensemble 0 %, lead-time 0; H-SC-11, n=1).
- **Windstoten dag 25-10 (per stationsmeting, n=151): bias +0,7, MAE 3,7 km/u** (24-10 +5,6 / zonder kaal model −1,3). Blokken: nacht 0,0/4,4, ochtend dalend +3,3/5,4, 07:44-11:43 +0,2/3,9, 11:43-15:44 +0,5/2,7 (nieuw gemeten), 15:54-19:44 +1,2/4,0, avond −1,0/1,6. Geen kale-modelperioden meer (L-SC-019/021 houden).
- **Nacht 23:44-03:44 (n=25): +1,2 / MAE 3,1.** Dalend 23:54-01:54 (37 → 15 km/u) **+1,7..+6,3** te hoog, stijgend 02:04-02:54 (19 → 33) **−1,8..−4,8** te laag → H-SC-9 (traagheid in beide richtingen) opnieuw bevestigd; 4e dag op rij.
- **Regen 25-10:** 5 treffers (2-7 min te laat bij lichte buien, 1× 20 min te vroeg), 2 vals, 1 gemist. Nacht 26-10: **2 valse aftellingen** tot 15 en 10 min (00:32-00:47, 01:27-01:52) en één tot 50 min, 0,0 mm/u de hele nacht → H-SC-3: vals bij lichte, uiteenvallende buien.
- **Bronnen:** bronstatus de hele dag "alles in orde" (0 u vals hapert); DNS-storingen 13:07-15:39, 00:12 en 02:34 opgevangen door reserve/herkansing (buienradar 93 %, meting 96 % cumulatief). Radar vers (laatste 03:44).
- Trend 7 d (19..25-10) windstoten-bias −1,4/+0,5/+0,9/+3,6/−2,2/+5,6/+0,7 → gemiddeld +1,1 (zonder 24-10 kaal model +0,3); 30 d n.v.t. (methode wisselde 21-10/24-10).
- Hypotheses: H-SC-3 (regenstart; vals bij lichte buien), H-SC-9 (traagheid → L-SC-022), H-SC-11 (koude-lucht-onweer gemist, n=1). Toets 0.59.4 bij het volgende onweer: 0 nadert-perioden zonder dichtere inslag.

laatste ronde: 26-10 03:40, gemeten t/m 26-10 03:45

## 26-10 07:40 · tussenronde
- HA herstartte 07:12 → **0.59.4 actief** (L-SC-023). **0.60.0** (L-SC-024 + L-SC-022, andere sessie 07:22) is sinds de herstart van **07:47 actief**.
- **Geen onweer:** 0 inslagen < 50 km 03:44-07:44, niveau groen, `onweer_nadert` uit. Bronstatus de hele ronde "alles in orde"; radar vers (06:41Z).
- **Windstoten 03:54-07:34 (n=23): bias +0,5, MAE 3,0 km/u** (nacht 3,1). Wind 17-29 km/u, vlagerig: de twee vlagen van 29,4 (04:24, 06:04) −7,5/−8,1 te laag, na elke vlaag +2,5..+4,9 te hoog → zelfde traagheid als H-SC-9, nu bij losse vlagen, niet bij een trend.
- **Regen (H-SC-3):** 1 lichte bui 04:58-05:22 (0,12-0,24 mm/u). Aftelling 04:47 "10" → 04:57:50 = **raak (< 1 min)**, 04:37 "25" → +4 min, 04:17 "50" → +9 min (tussendoor 2× even weg). **0 vals** (nacht: 2 vals). Om 04:58 nog "6 min" terwijl het al regende (1 ronde).
- Hypotheses: H-SC-3 (regenstart; vals bij lichte, uiteenvallende buien - vanochtend niet), H-SC-9 (traagheid → 0.60.0 frontfactor; toets bij het volgende front), H-SC-11 (koude-lucht-onweer gemist, n=1). Geen release (tussenronde).

laatste ronde: 26-10 07:40, gemeten t/m 26-10 07:45

## 26-10 11:40 · tussenronde
- 0.60.0 actief (herstarts 07:47 en 10:27). Geen Stormchase-logregels.
- **Geen onweer:** 0 inslagen < 50 km 07:44-11:44, niveau groen. Bronstatus de hele ronde "alles in orde"; radar vers (10:37). Geen regen (0,0 mm/u, geen aftelling) → regen niet te toetsen.
- **Windstoten 07:54-11:44 (n=24): bias −0,3, MAE 2,2 km/u** - beste blok sinds de meting per stationsmeting (nacht 3,1, ochtend 3,0). Wind oplopend 21 → 31 km/u; vlagen 26,6 (08:14) en 29,4 (08:54) −4,8/−7,8 te laag, daarna weer ±3. Geen front (`front` false, `factor_bron` tijdvak 0,78, `melding_bron` station) → de 0.60.0-frontfactor is nog niet getoetst.
- Hypotheses: H-SC-3 (regenstart; niets te meten), H-SC-9 (traagheid; losse vlagen blijven −5..−8 te laag, trend zelf goed gevolgd), H-SC-11 (koude-lucht-onweer gemist, n=1). Geen release.

laatste ronde: 26-10 11:40, gemeten t/m 26-10 11:45

## 26-10 15:40 · tussenronde
- 0.60.0 actief (HA-herstarts 13:32, 15:00, 15:13). Geen Stormchase-logregels.
- **Geen onweer:** 0 inslagen < 50 km 11:44-15:44, niveau groen. Bronstatus de hele ronde "alles in orde"; KNMI-push verbonden; radar vers (15:43).
- **Windstoten 11:53-15:34 (n=23): bias +0,5, MAE 1,1 km/u** (vooraf 10 min: +0,5 / MAE 2,1) - beter dan de ochtend (2,2). Wind 21-30 km/u; na 14:44 dalend en dan +1,7..+3,6 te hoog → zelfde traagheidspatroon als H-SC-9 (te hoog bij dalen). Geen front, factor tijdvak 0,73.
- **H-SC-3 (regenstart) eerste toets loopt:** aftelling sinds 14:57 (62 min); voorspelde start schoof 15:59 → 15:54 → 15:59 → 16:04 (licht, ≤ 0,1 mm/u). Nog droog om 15:45. Werkelijke start en lead-time → ronde 19:40.
- Hypotheses: H-SC-3 (regenstart; nu toetsbaar), H-SC-9 (traagheid; bevestigd bij dalende wind), H-SC-11 (koude-lucht-onweer gemist, n=1). Geen release.

laatste ronde: 26-10 15:40, gemeten t/m 26-10 15:45

## 26-10 19:40 · tussenronde
- 0.60.0 actief (HA-herstart 19:15). Geen Stormchase-logregels.
- **Geen onweer:** 0 inslagen < 50 km 15:44-19:44, niveau groen. Bronstatus de ronde "alles in orde", vanaf 19:39 **"knmi_edr hapert"** (1 fout op rij, DNS-storing 19:33 die ook brightsky/radar/Bitvavo/IG raakte; extern). Radar vers (19:42).
- **H-SC-3 regenstart, 2 treffers, 0 vals, 0 gemist.** Bui 1 start **15:52** (0,12 → 0,6 mm/u, regen tot 18:07): aftelling 14:57 "62" → 15:59 (7 min te laat voorspeld), 15:40 "27" → 16:07 (15 te laat), 15:47 "12" → 15:59 (7 te laat); lead-time 55 min. Bui 2 start **18:27**: 18:07 "30" → 18:37 (10 te laat), 18:17 "15" → 18:32 (5), 18:22 "5" → 18:27 (raak). Vandaag kwam de regen 5-15 min **eerder** dan voorspeld bij 15-60 min vooruit, raak bij ≤ 5 min; 25-10 kwamen lichte buien juist 2-7 min later. → richting per bui wisselt; geen vaste verschuiving.
- Tijdens regen toont *Regen begint over* de volgende bui na een droog gat (`volgende_bui`, bewust); de voorspelde gaten (16:17-16:42, 17:08-17:27) kwamen niet: intensiteit bleef 0,12 mm/u. Geen meldfout (regen_verwacht uit tijdens de bui).
- **Windstoten 15:44-19:34 (n=23): bias −0,6, MAE 1,0 km/u** (beste blok; 11:53-15:34 1,1). Vlagen 26,8 (18:24) −3,2 en 27,0 (19:34) −3,1; oplopend 19:04-19:34 (23 → 27) −1,3..−3,1 → H-SC-9 (te laag bij stijging/vlagen). Geen front, factor tijdvak 0,65.
- Hypotheses: H-SC-3 (regenstart; vandaag te laat voorspeld, gisteren te vroeg), H-SC-9 (traagheid; bevestigd bij oplopende wind), H-SC-11 (koude-lucht-onweer gemist, n=1). Geen release.

laatste ronde: 26-10 19:40, gemeten t/m 26-10 19:45

## 26-10 23:40 · tussenronde
- 0.60.0 actief (HA-herstarts 20:06, 20:25, 21:08, 21:52). Geen Stormchase-logregels.
- **Geen onweer:** 0 inslagen < 50 km 19:44-23:44, groen. Bronstatus de hele ronde "alles in orde" (knmi_edr-hapering van 19:39 hersteld); radar vers (23:42). Droog → regen niet te toetsen.
- **Windstoten 19:49-23:44 (n=25): bias −0,6, MAE 1,7 km/u** (stand vóór de meting: −0,6 / 2,9). **Windsprong 20:34-21:24: 22 → 41 km/u** in twee stappen van ~10-13 km/u: vooraf −11,1 (20:43) en −10,8 (21:14). `front` bleef false (sprong < `FRONT_STOOT_SPRONG_KMH` 15 tegen de uurmediaan, druk < 1 hPa/u) → tijdvakfactor 0,70-0,75 terwijl gemeten/model 0,89-1,09 was; de 0.60.0-frontfactor sprong dus niet aan. Na 21:54 weer ±1-2.
- Stilstandcontrole: geen vastzittende functies. Onweerstoetsen (0.58.x-0.60.0) wachten op onweer (laatste 25-10, dichtst 29 km) - weer, geen code. Vooruitblik ververst bewust alleen met een kijker.
- Hypotheses: H-SC-3 (regenstart; vanavond droog), **H-SC-9** (traagheid; nieuw: een stapsgewijze windtoename onder de frontgrens laat de factor achter, n=1 - eerst ≥ 3 gevallen, dan voorstel), H-SC-11 (koude-lucht-onweer gemist, n=1). Geen release.

laatste ronde: 26-10 23:40, gemeten t/m 26-10 23:45

## 27-10 03:40 · dagafsluiting 26-10
- 0.60.0 actief (laatste HA-herstart 21:52). Geen Stormchase-logregels; geen purge/repack in de log. Geen release (niets gepland, niets acuut).
- **Dag 26-10:** geen onweer (0 inslagen < 50 km, groen); onweerstoetsen van 0.58.x-0.60.0 wachten op onweer (laatste 25-10, dichtst 29 km). Bronstatus 1× "knmi_edr hapert" (19:39, DNS-storing, hersteld); radar steeds vers.
- **Regen (H-SC-3) 26-10:** 3 treffers, 0 gemist; 04:58 raak (10 min vooruit), 15:52 en 18:27 kwamen 5-15 min **eerder** dan voorspeld bij 15-60 min vooruit, raak bij ≤ 5 min. Vals: 2 aftellingen in de droge nacht (00:32-00:47, 01:27-01:52). 25-10 kwamen lichte buien juist 2-7 min later → geen vaste verschuiving.
- **Windstoten 26-10** (verwachting vóór de stationsmeting, 5 blokken, n=120): bias **+0,27 km/u, MAE 2,67**. Meetwijze gelijkgetrokken: de blokken van 15:40/19:40/23:40 rekenden eerst met de stand ná de meting (MAE 1,0-1,7) - die waarde volgt de meting zelf en is te gunstig; voortaan alleen 'vooraf'.
- Nacht 23:54-03:44 (n=24): bias −0,72, MAE 3,08; losse vlagen 34,7 (00:54) en 30,3 (03:34) −9,3/−6,3 te laag, verder ±1-5. Droog, geen aftelling.
- H-SC-9: windsprong 20:34-21:24 (22 → 41 km/u) onder de frontgrens, vooraf −11 km/u (n=1; ≥ 3 gevallen voor een voorstel).
- Stilstand: geen vastzittende functies (vooruitblik ververst bewust alleen met een kijker).
- Hypotheses: H-SC-3 (regenstart; richting wisselt per bui), H-SC-9 (traagheid bij vlagen/stappen), H-SC-11 (koude-lucht-onweer gemist, n=1). Geen release.

laatste ronde: 27-10 03:40, gemeten t/m 27-10 03:45

## 27-10 07:40 · tussenronde
- HA herstartte 06:04; **0.60.0 actief**. Geen Stormchase-logregels. Geen release.
- **Geen onweer:** 0 inslagen < 50 km 03:44-07:40, groen. Bronstatus de hele ronde "alles in orde"; radar vers (06:42Z). Vooruitblik-beeld staat op 05:04Z (herstart, geen kijker - bewust).
- **Windstoten 03:53-07:34 (vooraf, n=23): bias −0,87, MAE 2,75 km/u.** 04:14-05:53 vlagen naar 28-33 km/u: verwachting −2..−8 te laag (05:13 32,9 gemeten, 24,5 verwacht); 06:04-07:04 afnemend: +1..+3 te hoog. Zelfde traagheid in beide richtingen als H-SC-9 (geen front, dus 0.60.0-frontfactor niet in het spel).
- **Regen:** droog, geen aftelling → 0 vals, 0 gemist.
- Hypotheses: H-SC-3 (regenstart; vanochtend niets te toetsen), H-SC-9 (traagheid; vanochtend nog een stijgend + dalend stuk, bevestigt het patroon maar is geen 'stap' - teller stappen blijft n=1), H-SC-11 (n=1).

laatste ronde: 27-10 07:40, gemeten t/m 27-10 07:40

## 27-10 11:40 · tussenronde
- Herstarts 08:00 en 11:34; **0.60.0 actief**. Geen Stormchase-logregels. Geen release.
- **Geen onweer:** 0 inslagen < 50 km, groen; bronstatus de hele ronde "alles in orde"; radar vers (10:42Z), vooruitblik 10:34Z (kijker na herstart).
- **Windstoten 07:44-11:34 (vooraf, n=24): bias −0,22, MAE 2,94 km/u.** Vlagerig 24-37 km/u rond een vlak niveau (~31); fouten −6,5..+6,9 wisselen per meting van teken → ruis van losse vlagen, geen traagheid (geen trend, geen stap).
- Regen: droog, geen aftelling → 0 vals, 0 gemist.
- Stilstand: geen vastzittende functies.
- Hypotheses: H-SC-3 (regenstart; niets te toetsen), H-SC-9 (stappen n=1; vandaag vlak niveau, telt niet), H-SC-11 (n=1).

laatste ronde: 27-10 11:40, gemeten t/m 27-10 11:40

## 27-10 15:58 · tussenronde
- Herstart 12:32; **0.60.0 actief**. Geen Stormchase-logregels. Geen release.
- **Geen onweer:** 0 inslagen < 50 km, groen; bronstatus de hele ronde "alles in orde"; radar vers (14:59Z). Vooruitblik staat op 11:32Z (herstart, geen kijker - bewust).
- **Windstoten 11:44-15:54 (vooraf, n=26): bias +0,31, MAE 2,83 km/u.** 12:00-13:45 oplopend naar 39-45 km/u: verwachting meest −2..−9 te laag (13:44 45,5 gemeten, 36,3 verwacht); 15:14-15:54 afnemend naar 18 km/u: +2..+6 te hoog. Zelfde traagheid in beide richtingen (H-SC-9), geen stap.
- **Regen:** aftelling sinds 14:57 (100 min → 15:09 83, 15:14-15:27 unknown, daarna 95 → 32 om 15:59, doel ~16:31). Nog droog → uitslag (vals/raak, fout in min) volgende ronde. Onderbreking van 13 min in de aftelling genoteerd (n=1).
- Stilstand: geen vastzittende functies.
- Hypotheses: H-SC-3 (regenstart; eerste toets vanavond), H-SC-9 (traagheid; vandaag een stijgend + dalend stuk), H-SC-11 (n=1).

laatste ronde: 27-10 15:58, gemeten t/m 27-10 15:59

## 27-10 19:41 · tussenronde
- Geen herstart sinds 12:32; **0.60.0 actief**. Geen Stormchase-logregels. Geen release.
- **Geen onweer:** 0 inslagen < 50 km, groen; bronstatus "alles in orde"; radar vers (18:40Z). Vooruitblik staat nog op 11:32Z (herstart, geen kijker - bewust).
- **Regenstart (H-SC-3, eerste toets, n=3):** aftelling 14:57 → doel ~16:26-16:31 → droog, om 16:27 terug naar 90 min = **1 vals**. Daarna **2 raak**: eerste regen 17:42 (0,12 mm/u; 30 min vooraf voorspeld 17:46 → −4 min) en 18:17/18:22 (0,12 → 0,84; vooraf 18:22 → −5 min). Buien 18:22-19:45 tot 2,4 mm/u. Tijdens regen telt *Regen begint over* door naar de volgende bui (bedoeld, met *Regen stopt over*).
- **Windstoten 15:55-19:44 (vooraf, n=23): bias +0,06, MAE 4,88 km/u.** **Stap** 18:34 met de bui: 19,7 → 39,4 gemeten, verwachting 19,9 (−19,5); daarna te hoog na de terugval (19:14 +14,8). H-SC-9: stappen n=1 → **n=2**.
- Stilstand: geen vastzittende functies.
- Hypotheses: H-SC-3 (regenstart: 2 raak / 1 vals, fout −4/−5 min), H-SC-9 (traagheid; stap n=2), H-SC-11 (n=1).

laatste ronde: 27-10 19:41, gemeten t/m 27-10 19:44

## 27-10 23:41 · tussenronde
- Herstart 21:01; **0.60.0 actief**. Geen Stormchase-logregels. Geen release.
- **Geen onweer:** 0 inslagen < 50 km, groen; bronstatus "alles in orde"; radar vers (23:42). Vooruitblik staat op 21:01 (herstart, geen kijker - bewust).
- **Regenstart (H-SC-3):** bui 21:57 (0,36 mm/u): om 21:22 "35 min" → 21:57 = **0 min fout** (35 min vooraf); 21:32 "30" → +5 min → **raak**. 22:22 "5 min" aan de staart van de bui, daarna droog → **1 vals** (kort). Dag 27-10: **3 raak / 2 vals**, fout raak −5..0 min.
- **Windstoten 19:44-23:34 (vooraf, n=24): bias +4,21, MAE 4,28 km/u.** Na de bui (19:54-20:24) +9..+16 te hoog: de verwachting zakt pas ~40 min na de terugval (19,7 → 4,8 gemeten). Daarna (21:00-23:34) +0..+4. Ondersteunt H-SC-9 (traagheid), nu ook op de afloop; stappen n=2.
- Stilstand: geen vastzittende functies.
- Hypotheses: H-SC-3 (regenstart 3/2; valse alarmen aan begin en staart van een bui), H-SC-9 (traagheid; stap n=2 + afloop n=1), H-SC-11 (n=1).

laatste ronde: 27-10 23:41, gemeten t/m 27-10 23:44

## 28-10 03:40 · dagafsluiting 27-10
- 0.60.0 actief (herstart 21:01). Geen Stormchase-logregels; geen purge/repack in de log. **Release 0.60.1** (L-SC-025, alleen weergave; suite 942 groen, workflow groen, HACS ververst; wacht op installatie).
- **Dag 27-10:** geen onweer (0 inslagen < 50 km, groen); onweerstoetsen 0.58.x-0.60.0 wachten op onweer. Bronstatus in de rondes "alles in orde"; DNS-storing 21:02-21:44 en 28-10 02:33 (1 op rij, hersteld 02:35). Radar vers (02:41Z, 2 min).
- **Windstoten 27-10 (vooraf, 6 blokken, n=144): bias +0,47, MAE 3,45 km/u** (26-10 +0,27 / 2,67). Hogere MAE komt uit de bui: stap 18:34 −19,5 en afloop 19:54-20:24 +9..+16. 7 d +1,33 (zonder 24-10 +0,62). Vooruitblik max 51 tegen gemeten max 45,5 (+5,5).
- **Nacht 23:53-03:34 (n=23): bias +0,10, MAE 1,95**; 02:44-03:34 oplopend 6,8 → 18,4: −2..−5,5 te laag (traagheid, geen stap).
- **Regenstart 27-10:** 3 raak (−5..0 min) / 2 vals / 0 gemist; 24..27-10 samen 12 / 7 / 1. Nacht droog, geen aftelling.
- **Stilstand → bug:** de L-SC-011-attributen (regencorrectie, 0.56.0) verschenen nooit op *Regen begint over* (verkeerde sensorklasse); of de bijstelling actief is was sinds 21-10 niet meetbaar → **L-SC-025 gebouwd 0.60.1**. Verder geen vastzittende functies.
- Hypotheses: H-SC-3 (regenstart; vals aan begin/staart van een bui; na 0.60.1 toetsen tegen `correctie_vorm`/`afwijking_min`), H-SC-9 (traagheid; stappen n=2, nodig ≥ 3 voor een voorstel), H-SC-11 (koude-lucht-onweer gemist, n=1).

laatste ronde: 28-10 03:40, gemeten t/m 28-10 03:44


## 28-10 07:41 · tussenronde
- Herstarts 06:10 en 06:52; **0.60.1 actief**. Geen Stormchase-logregels. Geen release.
- **Geen onweer:** 0 inslagen < 50 km, groen; bronstatus "alles in orde"; radar vers (06:42Z). Droog, geen regenaftelling.
- **L-SC-025 geverifieerd:** *Regen begint over* toont nu de regencorrectie: `gecorrigeerd` true, vorm **verschuiving** (−7 min; > 45 min −4,5), 42 uitkomsten; afwijking zonder correctie 11,0 tegen verschuiving **8,8** en verhouding 9,7 min → de bijstelling is actief en verkleint de fout (~20 %). H-SC-3 kan voortaan per bui tegen `afwijking_min` getoetst worden.
- **Windstoten 03:54-07:34 (vooraf, n=23): bias +0,84, MAE 2,73 km/u.** 03:54-04:54 −4..−5 te laag bij 17-19 km/u, afloop 05:34-06:24 +2..+5,5 te hoog, daarna +2..+2,5 bij 6-8 km/u → zelfde traagheid als H-SC-9 (stijgen te laag, dalen te hoog); geen stap.
- Stilstand: geen vastzittende functies.
- Hypotheses: H-SC-3 (regenstart; nu meetbaar met `afwijking_min`), H-SC-9 (traagheid; stappen n=2, afloop n=2), H-SC-11 (n=1).

laatste ronde: 28-10 07:41, gemeten t/m 28-10 07:45

## 28-10 11:42 · tussenronde
- Herstart 10:25; **0.60.1 actief**. Geen Stormchase-logregels. Geen release.
- **Geen onweer:** 0 inslagen < 50 km, groen; bronstatus "alles in orde" (KNMI-push verbonden); radar vers (10:44Z). Droog, geen regenaftelling. Vooruitblik op 10:25 (herstart, geen kijker - bewust).
- **Windstoten 07:54-11:44 (vooraf, n=23): bias +0,92, MAE 1,73 km/u.** 07:54-08:44 +1,8..+3,9 te hoog bij 8-9 km/u (laag niveau), daarna −2,9..+3,1 bij 11-18 km/u; geen stap. Factor tijdvak 0,78 (24 u 0,64).
- Stilstand: geen vastzittende functies.
- Hypotheses: H-SC-3 (regenstart; meetbaar met `afwijking_min`, wacht op een bui), H-SC-9 (traagheid; stappen n=2), H-SC-11 (n=1).

laatste ronde: 28-10 11:42, gemeten t/m 28-10 11:45

## 28-10 15:43 · tussenronde
- **0.60.1 actief**, geen herstart sinds 10:25. Geen Stormchase-logregels. Geen release.
- **Geen onweer:** 0 inslagen < 50 km, groen, CAPE 10, LI 6,8; bronstatus "alles in orde" (KNMI-push verbonden, 164 meldingen); radar vers (14:45Z). Droog, geen regenaftelling.
- **Windstoten 11:54-15:43 (vooraf, n=22): bias −0,95, MAE 2,19 km/u.** Oplopend 12:24 (−5,5 bij 21,4) en 13:44 (−4,6 bij 27,6), 14:54 −4,8 bij 24,3: pieken te laag, rustiger kwartieren +0,5..+3,6 → zelfde traagheid als H-SC-9; geen stap.
- Stilstand: geen vastzittende functies.
- Hypotheses: H-SC-3 (regenstart; wacht op een bui), H-SC-9 (traagheid; vandaag 3 vensters dezelfde vorm, stappen n=2), H-SC-11 (n=1).

laatste ronde: 28-10 15:43, gemeten t/m 28-10 15:45

## 28-10 19:43 · tussenronde
- **0.60.1 actief** (herstart 19:18). Geen Stormchase-logregels. Geen release.
- **Geen onweer:** 0 inslagen < 50 km, groen, CAPE 0, LI 7,0; bronstatus "alles in orde"; radar vers (18:42Z). Droog.
- **Windstoten 15:54-19:34 (vooraf, n=23): bias +1,91, MAE 2,45 km/u.** Afnemende wind 16:14-17:24 telkens te hoog (+2 tot +7,7; 16:23 14,8 tegen 10,9), piek 15:54-16:04 te laag (−3,0/−1,9 bij 22-23 km/u) → zelfde traagheid als H-SC-9, vandaag 4 vensters dezelfde vorm.
- Stilstand: geen vastzittende functies.
- Hypotheses: H-SC-3 (regenstart; wacht op een bui), H-SC-9 (traagheid; vandaag in alle vensters, dagafsluiting telt op), H-SC-11 (n=1).

laatste ronde: 28-10 19:43, gemeten t/m 28-10 19:45

## 28-10 23:40 · tussenronde
- **0.60.1 actief**, geen herstart sinds 19:18. Geen Stormchase-fouten in de logs. Geen release.
- **Geen onweer:** 0 inslagen < 50 km, groen, CAPE 10, LI 7,6; droog. Bronstatus 23:42 "buienradar hapert": externe DNS-storing (~23:25); KNMI-nowcast faalde ook, dus de reservebron werd terecht gevraagd en faalde - juist gemeld. Radar vers (22:43Z), KNMI-push verbonden.
- **Windstoten 19:53-23:34 (vooraf, n=23): bias −0,15, MAE 1,27 km/u.** Oplopende wind 19:53-22:44 meest te laag (−0,1..−2,2), afname 23:14-23:24 +2,4/+2,9 te hoog → zelfde traagheid als H-SC-9, vandaag 5 vensters dezelfde vorm.
- Stilstand: geen vastzittende functies (unknown-waarden = geen onweer/regen).
- Hypotheses: H-SC-3 (regenstart; wacht op een bui), H-SC-9 (traagheid; dagafsluiting telt 28-10 op), H-SC-11 (n=1).

laatste ronde: 28-10 23:40, gemeten t/m 28-10 23:45

## 29-10 03:40 · dagafsluiting 28-10
- **0.60.1 actief**, geen herstart sinds 19:18, geen purge/repack in de log. Geen Stormchase-fouten. Geen release (niets te bouwen; geen open voorstellen met akkoord).
- **Dag 28-10:** geen onweer (0 inslagen < 50 km, groen, CAPE 0-10); onweerstoetsen 0.58.x-0.60.0 wachten op onweer. Droog: geen regenaftelling, geen vals alarm. Bronstatus 5/6 rondes in orde; 23:42 'buienradar hapert' door de externe DNS-storing (terecht gemeld, hersteld).
- **Windstoten 28-10 (vooraf, 6 blokken, n=137): bias +0,46, MAE 2,05 km/u** (27-10 +0,47 / 3,45). 7 d +1,27 (zonder 24-10 +0,55).
- **Nacht 23:54-03:44 (n=23): bias +0,83, MAE 1,31**; afnemende wind 02:39-03:44 +1,2..+2,2 te hoog.
- **H-SC-9:** 28-10 alle 6 vensters dezelfde vorm (stijgen te laag, dalen te hoog), maar geen stap (> 10 km/u in één meting) → stappen blijven n=2, nodig ≥ 3 voor een voorstel. De traagheid zelf is nu 2 dagen op rij in elk venster zichtbaar; bias over de dag klein (+0,5).
- Stilstand: geen vastzittende functies (unknown = geen onweer/regen).
- Hypotheses: H-SC-3 (regenstart; wacht op een bui), H-SC-9 (traagheid; stappen n=2), H-SC-11 (koude-lucht-onweer gemist, n=1).

laatste ronde: 29-10 03:40, gemeten t/m 29-10 03:55

## 29-10 07:41 · tussenronde
- **0.60.1 actief**, herstart HA 06:40 (EMS-update). Geen Stormchase-fouten in de logs. Geen release.
- **Geen onweer:** 0 inslagen < 50 km, groen, CAPE 0 (piek 12 u 20), LI 8,8; droog. Bronstatus "alles in orde" (externe DNS-storing ~07:35 raakte andere integraties).
- **Windstoten 03:53-07:34 (vooraf, n=23): bias +1,07, MAE 1,47 km/u.** Afnemende wind (11,9 → 6,7) 04:04-05:44 telkens te hoog (+1,3..+3,0) → traagheid H-SC-9, geen stap (> 10 km/u).
- Stilstand: geen vastzittende functies (unknown = geen onweer/regen).
- Hypotheses: H-SC-3 (regenstart; wacht op een bui), H-SC-9 (traagheid; stappen n=2), H-SC-11 (n=1).

laatste ronde: 29-10 07:41, gemeten t/m 29-10 07:45

## 29-10 11:40 · tussenronde
- **0.60.1 actief**, geen Stormchase-fouten. **Release 0.60.2** (acuut, foute data nu: zie onder).
- **Geen onweer:** 0 inslagen < 50 km, groen, CAPE 0 (piek 12 u 20), LI 8,1; droog.
- **Bronstatus "meteoalarm hapert" sinds 11:35:** om 11:32 faalden de KNMI-waarschuwingen één keer (DNS-storing), MeteoAlarm viel in en kreeg een time-out (`laatste_fout` leeg, laatste succes 28-10 23:45 UTC); daarna werkte het KNMI weer (11:35) en wordt MeteoAlarm niet meer gevraagd → status bleef "hapert" tot de volgende KNMI-storing. Zelfde gat als L-SC-016, MeteoAlarm stond niet in `RESERVE_VOOR` → **L-SC-026 gebouwd 0.60.2** (reserve van `knmi_waarschuwingen`; lege fouttekst → `TimeoutError`). Suite 947 groen (+5 tests). Workflow groen, HACS ververst; wacht op installatie.
- **Windstoten 07:54-11:44 (vooraf, n=24): bias +0,26, MAE 1,65 km/u.** Oplopende wind 09:04-09:44 te laag (−2,0..−3,4), daarna afnemend 10:24-11:04 te hoog (+2,5..+3,1) → zelfde traagheid H-SC-9; geen stap > 10 km/u (stappen blijven n=2).
- Stilstand: geen vastzittende functies (unknown = geen onweer/regen).
- Hypotheses: H-SC-3 (regenstart; wacht op een bui), H-SC-9 (traagheid; stappen n=2), H-SC-11 (n=1).

laatste ronde: 29-10 11:40, gemeten t/m 29-10 11:45

## 29-10 15:45 · tussenronde
- **0.60.2 actief** (geïnstalleerd; HA-herstarts ~14:45 en ~15:10), geen Stormchase-fouten. Geen release.
- **Geen onweer:** 0 inslagen < 50 km, groen, CAPE 20 (piek 12 u 30), LI 9,8; droog. Radar vers (15:42).
- **L-SC-026:** bronstatus "alles in orde"; geen KNMI-storing sinds de installatie → het terugvalpad (MeteoAlarm als reserve) is nog niet getoetst; volgt bij de eerstvolgende storing.
- **Windstoten 11:53-15:44 (vooraf, n=23): bias +1,73, MAE 1,84 km/u.** Wind nam af van 10,8 naar 3,2 km/u; 12:43-15:03 telkens te hoog (+1,2..+4,0) → traagheid H-SC-9; geen stap > 10 km/u (stappen blijven n=2). Vandaag: dalende wind steeds te hoog, stijgende te laag.
- Stilstand: geen vastzittende functies (unknown = geen onweer/regen).
- Hypotheses: H-SC-3 (regenstart; wacht op een bui), H-SC-9 (traagheid; stappen n=2), H-SC-11 (n=1).

laatste ronde: 29-10 15:45, gemeten t/m 29-10 15:45

## 29-10 19:40 · tussenronde
- **0.60.2 actief**, geen Stormchase-fouten. Geen release.
- **Geen onweer:** 0 inslagen < 50 km, groen, CAPE 0, LI 12,0; droog. Radar vers (19:41). Bronstatus "alles in orde", KNMI-push verbonden (113 meldingen). L-SC-026 terugvalpad nog niet getoetst (geen KNMI-storing).
- **Windstoten 15:54-19:34 (vooraf, n=23): bias +0,89, MAE 1,39 km/u.** Stap 18:44 (1,6 → 6,9) −3,0 te laag, daarna 19:04-19:14 +2,6/+3,0 te hoog → zelfde traagheid H-SC-9; geen stap > 10 km/u (stappen blijven n=2). Dag 29-10 tot nu: bias steeds positief (+0,26..+1,73).
- Stilstand: geen vastzittende functies (unknown = geen onweer/regen).
- Hypotheses: H-SC-3 (regenstart; wacht op een bui), H-SC-9 (traagheid; stappen n=2), H-SC-11 (n=1).

laatste ronde: 29-10 19:40, gemeten t/m 29-10 19:45

## 29-10 23:40 · tussenronde
- **0.60.2 actief**, geen Stormchase-fouten (MeteoAlarm-fout 22:53 is de HA-kernintegratie `binary_sensor.meteoalarm`, niet Stormchase). Geen release.
- **Geen onweer:** 0 inslagen < 50 km, CAPE 0, LI 12,2; droog. Radar vers (23:42). Bronstatus "alles in orde"; L-SC-026 terugvalpad nog niet getoetst (geen KNMI-storing).
- **Niveau geel sinds 21:57 = terecht:** KNMI code geel dichte mist Gelderland (Weerlive `binary_sensor.knmi_waarschuwing` ook geel). Opgevallen: `vanaf`/`tot` 22:00Z-09:00Z (= 23:00-10:00 lokaal) tegen KNMI-tekst "vanaf 22:00 tot morgen 09:00"; op 23-10 klopte het begin (16Z = 18:00) maar liep het einde 1 u door (tekst 23:00, per uur geel t/m 21Z). Afgeleid uit `alertLevel` per uur in `knmi_verwerk._periode`; n=2 met verschillend patroon → geen conclusie. Toets 30-10: gaat het niveau om 09:00 of pas om 10:00 naar groen?
- **Windstoten 19:53-23:34 (vooraf, n=22): bias +1,68, MAE 2,33 km/u.** Twee grootste fouten direct na een Open-Meteo-verversing: 21:54:09 model 6,8 → 13,3 (waarde 4,3 → 8,5), 22:04 gemeten 1,5 (+7,0); 20:54 waarde → 2,3, 21:03 gemeten 6,3 (−4,0). De L-SC-017-bijsturing houdt tot de volgende stationsmeting de fout tegen de oude modelwaarde (`laatste` = model van het meetmoment). Rest weer traagheid (dalend 22:04-22:24 +4..+5). Onder H-SC-9 genoteerd; dagafsluiting: aandeel fout in het eerste meetinterval na een verversing over 7 dagen.
- Stilstand: geen vastzittende functies (unknown = geen onweer/regen).
- Hypotheses: H-SC-3 (regenstart; wacht op een bui), H-SC-9 (traagheid + modelsprong bij verversing), H-SC-11 (n=1).

laatste ronde: 29-10 23:40, gemeten t/m 29-10 23:45

## 30-10 03:40 · dagafsluiting 29-10
- **0.60.2 actief** (HACS: geen nieuwere), geen purge/repack, geen Stormchase-fouten in de log. Geen release.
- **Dag 29-10:** geen onweer (0 inslagen < 50 km, CAPE 0-20), droog; regencorrectie actief (verschuiving, 42 uitkomsten, 8,8 tegen kaal 11,0 min). Bronstatus 1× vals "meteoalarm hapert" 11:35 → L-SC-026 (0.60.2), sindsdien in orde; terugvalpad nog niet getoetst. Geel 21:57 terecht (KNMI mist).
- **Windstoten 29-10 (vooraf, n=138): bias +1,07, MAE 1,66 km/u** (28-10 +0,46/2,05). **7 d +0,92** (was +1,27; zonder 24-10 +0,13). Nacht 23:43-03:34 (n=24) +0,22 / MAE 1,62; stap 02:24 (4,6 → 9,9) −5,1 te laag.
- **Toets modelsprong (H-SC-9, 23:40):** eerste meting na een Open-Meteo-verversing MAE 1,82 / bias +0,91 (n=57) tegen overige 1,57 / +0,94 (n=105); 7 van 14 fouten ≥ 3 km/u vallen na een verversing (35 % van de metingen). Effect klein, n=1 dag → geen voorstel; blijft onder H-SC-9.
- **Nieuw H-SC-12 (KNMI-periode):** waarschuwing vernieuwd "vanaf 03:00 tot 10:00"; attributen vanaf 02Z (03:00 ✓) tot 10Z (= 11:00), per uur geel t/m slot 09Z. `tot` 1 u later dan de tekst in 3/3 (23-10, 29-10, 30-10); past bij KNMI-uurslots die het einde van het uur labelen (`_periode` telt +1 u, en `vanaf` 29-10 was ook 1 u laat). Toets 30-10: niveau groen om 10:00 of 11:00 en `niveau_per_uur`; bevestigd → zelf bouwen (rapportage) in de dagafsluiting van 31-10.
- Stilstand: geen vastzittende functies (unknown = geen onweer/regen; regencorrectie nu actief).
- Hypotheses: H-SC-3 (regenstart; wacht op een bui), H-SC-9 (traagheid + modelsprong), H-SC-12 (KNMI-eindtijd). H-SC-11 (koude-lucht-onweer, n=1) geparkeerd tot het volgende onweer.

laatste ronde: 30-10 03:40, gemeten t/m 30-10 03:45

## 30-10 07:41 · tussenronde
- **0.60.2 actief** (HACS: geen nieuwere), HA-herstart 07:40, geen Stormchase-fouten. Geen release.
- Geen onweer (0 inslagen < 50 km, CAPE 10, LI 14), droog. Bronstatus "alles in orde"; KNMI-push verbonden; MeteoAlarm/BrightSky/Buienradar in rust/reserve (niet nodig).
- **Geel = KNMI mist Gelderland** (officieel, sinds de herstart 07:40 weer actief). H-SC-12 (eindtijd 1 u te laat) toets 11:40: niveau groen om 10:00 of 11:00.
- **Windstoten 03:40-07:44 (vooraf, n=23): bias +1,31, MAE 1,42 km/u** (lage wind 0-5 km/u, afnemend tot 06:34 → voorspelling liep achter; 05:54-06:34 +2,6..+4,3). Past bij H-SC-9 (traagheid); geen nieuw voorstel.
- Stilstand: geen (unknown = geen onweer/regen).
- Hypotheses: H-SC-3 (regenstart; wacht op een bui), H-SC-9 (traagheid + modelsprong), H-SC-12 (KNMI-eindtijd, toets vandaag).

laatste ronde: 30-10 07:41, gemeten t/m 30-10 07:45

## 30-10 11:41 · tussenronde
- **0.60.2 actief** (HACS: geen nieuwere), geen Stormchase-fouten (MeteoAlarm-fout = HA-kernintegratie `binary_sensor.meteoalarm`). Geen release.
- Geen onweer (0 inslagen < 50 km, CAPE 0, LI 13,9), droog. Bronstatus "alles in orde", radar vers (11:42). Radar-vooruitblik laatst 07:40: bewust (geen kijker, L-SC-020).
- **H-SC-12 getoetst (4/4):** KNMI-mist vernieuwd naar "06:00 tot 10:00" (lokaal); `tot` = 10Z (11:00 lokaal), laatste geel-slot 09Z. Het einde komt dus 4 van 4 keer 1 u te laat uit `_periode` (+1 u op de laatste slot; KNMI markeert het eindtijdstip zelf als slot). Het **niveau** zelf werd groen om 10:55, toen KNMI de waarschuwing introk (uitgifte 10:51), niet door `tot` → alleen de getoonde eindtijd (attribuut/melding) is fout. Status: bevestigd → **L-SC-027** (rapportagefout) bouwen in de dagafsluiting 31-10.
- **Windstoten 07:54-11:34 (vooraf, n=22): bias +0,44, MAE 1,16 km/u.** Eerste meting na een Open-Meteo-verversing MAE **1,52** (n=6) tegen 1,03 (n=16); de twee grootste fouten (+3,3 om 10:13, +3,1 om 10:43) liggen direct na een verversing (6,2 → 9,3; 8,6 → 9,9). Steunt het modelsprong-deel van H-SC-9 (2e dag); dagafsluiting telt 7 dagen.
- Stilstand: geen (unknown = geen onweer/regen).
- Hypotheses: H-SC-3 (regenstart; wacht op een bui), H-SC-9 (traagheid + modelsprong bij verversing), H-SC-12 (bevestigd → L-SC-027).

laatste ronde: 30-10 11:41, gemeten t/m 30-10 11:45

## 30-10 15:56 · tussenronde
- **0.60.2 actief** (HACS: geen nieuwere; HA-herstart 13:03), geen Stormchase-fouten. Geen release.
- Geen onweer (0 inslagen < 50 km, CAPE 0, LI 13,6), droog. Bronstatus "alles in orde", niveau groen.
- **Windstoten 11:44-15:54 (vooraf, n=26): bias −0,84, MAE 1,67 km/u** (wind loopt op tot 20 km/u gemeten). Eerste meting na een Open-Meteo-verversing MAE **2,32** (n=8) tegen 1,38 (n=18); grootste fouten −5,5 (14:33) en −3,4 (13:33) direct na een verversing. **3e waarneming** voor het modelsprong-deel van H-SC-9 (07:41, 11:41, 15:56); dagafsluiting telt 7 dagen en beslist of het een voorstel wordt.
- Stilstand: geen (unknown = geen onweer/regen).
- Hypotheses: H-SC-3 (regenstart; wacht op een bui), H-SC-9 (traagheid + modelsprong bij verversing), H-SC-12 (bevestigd → L-SC-027, bouwen dagafsluiting 31-10).

laatste ronde: 30-10 15:56, gemeten t/m 30-10 15:58

## 30-10 19:40 · tussenronde
- **0.60.2 actief** (HACS: geen nieuwere), geen Stormchase-fouten. Geen release.
- Geen onweer (0 inslagen < 50 km, CAPE 0, LI 12,5), droog. Bronstatus "alles in orde", niveau groen, radar vers (19:42).
- **Windstoten 15:58-19:34 (vooraf, n=21): bias −1,43, MAE 2,07 km/u** (wind 9-15 km/u, voorspelling structureel te laag). Eerste meting na een Open-Meteo-verversing MAE **2,11** (n=7) tegen **2,04** (n=14): in dit venster **geen** modelsprong-effect (eerste tegenwaarneming na 3× vandaag). Grootste fout −6,0 (18:54, vlaag 15,2). H-SC-9 blijft open; dagafsluiting telt 7 dagen per venster.
- Stilstand: geen (unknown = geen onweer/regen).
- Hypotheses: H-SC-3 (regenstart; wacht op een bui), H-SC-9 (traagheid + modelsprong; vanavond niet gezien), H-SC-12 (bevestigd → L-SC-027, bouwen dagafsluiting 31-10).

laatste ronde: 30-10 19:40, gemeten t/m 30-10 19:45

## 30-10 23:40 · tussenronde
- **0.60.2 actief** (HACS: geen nieuwere), geen Stormchase-fouten. Geen release.
- Geen onweer (0 inslagen < 50 km, CAPE 0, LI 11,0), droog. Bronstatus "alles in orde", niveau groen, radar vers (23:42).
- **Windstoten 19:53-23:34 (vooraf, n=23): bias −1,98, MAE 2,43 km/u** (vlagen tot 23,0 om 20:24 en 20,8 om 22:54; voorspelling 10,2 en 6,0 te laag). Eerste meting na een Open-Meteo-verversing MAE **1,93** (n=8) tegen **2,70** (n=15) → 2e tegenwaarneming op rij voor het modelsprong-deel; het traagheidsdeel (achterlopen bij oplopende wind, bias 15:56 −0,84 → 19:40 −1,43 → nu −1,98) wordt sterker. Dagafsluiting telt 7 d en beslist.
- Stilstand: geen (unknown = geen onweer/regen).
- Hypotheses: H-SC-3 (regenstart; wacht op een bui), H-SC-9 (traagheid sterk, modelsprong 3 voor / 2 tegen vandaag), H-SC-12 (bevestigd → L-SC-027, bouwen dagafsluiting 31-10).

laatste ronde: 30-10 23:40, gemeten t/m 30-10 23:45
