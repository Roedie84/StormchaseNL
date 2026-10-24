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

## 10-10 23:40 · tussenronde
- Geïnstalleerd 0.52.0. HA-herstarts 19:48, 20:26 (EMS-releases). Locatie tracker iPhone. Bronstatus "alles in orde" heel de periode; logboek 0 Stormchase-fouten.
- **Onweer op afstand (gebeurtenis):** 20:34-20:59 cel op 93 → 74 km (markers tot 59), weg om 22:59; **0 inslagen binnen 50 km**, niveau groen → geen vals alarm, geen miss. `onweer_nadert` aan 20:38-21:06, aankomst eerst 62 → 44 min (20:41), daarna 68 → 142; validatie: aankomst (44 min) en passage (7 min, 88 km) niet uitgekomen.
- **Naderingssnelheid (L-SC-001, derde meetpunt):** wijzigde alleen bij nieuwe inslagen (alle 14 wijzigingen vallen samen met markerwijzigingen) → werkt zoals gebouwd. Wel: eerste schatting 83-108 km/u (20:38-20:41) tegen werkelijk ~57 km/u (93 → 74 km in 20 min), daalde naar 31 om 20:59. Samen met 16:28 (9,5 tegen ~32) → **H-SC-6 (nieuw):** de naderingssnelheid uit de eerste minuten van een cel is onbetrouwbaar in beide richtingen (n=2); volgen bij de volgende cellen, nog geen voorstel.
- **Windstoten (0.52.0):** 19:54-23:33 n=23: bias **−2,3 km/u**, MAE 5,0 (mediaan −3,6). Gemeten ≥ 28 km/u (n=4, 19:54-20:14) **−8,6**; < 28 (n=19) −1,0 → H-SC-5 (verhouding stijgt bij harde stoten) opnieuw gesteund; L-SC-008 blijft open.
- **Regen KNMI (H-SC-3):** `regen_per_bron.knmi` 19 voorspellingen, 16 uitgekomen, **mediaan −7 min, 12 te vroeg / 4 te laat** (vorige ronde 11 / mediaan −2,4). Deze periode −7,3 (20:12), +3,1 (21:02), −10,0 (22:12, voorspeld 12, kwam na 2). De bui komt stelselmatig eerder dan KNMI zegt; met `rain_lead` 10 min blijft er dan ~3 min over. Bij n ≥ 20 uitgekomen (dagafsluiting) toetsen per horizon → mogelijk voorstel (meldgedrag = Ruud).
- Hypotheses: H-SC-3 (KNMI regen te laat voorspeld), H-SC-5 (windverhouding bij harde stoten), H-SC-6 (vroege naderingsschatting). Geen release.

laatste ronde: 10-10 23:40, gemeten t/m 10-10 23:45

## 11-10 03:40 · dagafsluiting 10-10
- Recorder: eenmalige opschoning 03:00-03:05 klaar; historie 10-10 compleet. Geïnstalleerd 0.52.0; 12 HA-herstarts; locatie tracker iPhone (9× 4-10 s "laatst bekend", 0× thuis). Nacht 00:00-03:45 geen onweer.
- **Onweer 10-10:** 3 cellen (64-70 km 13:45-15:51; 80 → 46 km 16:24-17:31; 93 → 74 km 20:34-20:59), max 8 inslagen < 50 km, 0 < 25 km, niveau heel de dag groen → 0 hits, 0 misses; 2 nadert-perioden (12,0 / 28,1 min) zonder aankomst = 2 valse nadert (07-10: 4), geen melding (buiten 30 km). Validatie aankomst 0/1, passage 0/2. Lead-time/afstandsfout bij aankomst n.v.t.
- Bronnen 10-10 2766/2766 = 100 % (4 d 99,92 %); radarbeeld mediaan 3,0 min, max 7,4; Blitzortung 's nachts 18,2 min (11-10: 11,1) weg.
- **L-SC-001 geverifieerd (mechanisme):** alleen bij nieuwe inslagen, 0 aankomstsprongen zonder inslag, geen 15-min-perioden. Aankomst zelf nog 0/1.
- **Windstoten (L-SC-007):** dag −2,3 km/u (MAE 4,8, n=153) tegen kaal model +10,9; na 0.52.0 −1,9. **H-SC-5 verworpen:** per modelklasse −3,8/−3,2/−4,3/+2,5 (geen oplopende onderschatting); de −8 bij hoge gemeten stoten is selectie op de uitkomst. L-SC-008 → alleen optie (c). **H-SC-7 (nieuw):** 's nachts lagere verhouding (00-04 u 0,53 tegen factor 0,68 → +5,2 km/u, n=22; na 12:04 dag 0,72 / nacht 0,65).
- **H-SC-3 (KNMI regen):** n=19 uitgekomen, mediaan −6,9, 14 te vroeg / 5 te laat (p 0,064). 8 van de 14 zichtbare afwijkingen liggen op −6,8..−7,3 (≤15 min 4/4): dat is het meetvenster van `regent` (−10..+10, L-SC-005 afgewezen), geen KNMI-fout → geen voorstel; volgen.
- **Gebouwd 0.52.1 (L-SC-009):** afstandsreeks alleen bij nieuwe afstand/snelheid en over herstarts (was 180× 73,6 km in 30 min). 737 tests groen, workflow groen, HACS ververst (update zichtbaar). Maakt H-SC-6 toetsbaar.
- Niet meetbaar: lead-time en afstandsfout (geen onweer < 25 km); radarvooruitblik-versheid (alleen op aanvraag).

laatste ronde: 11-10 03:40, gemeten t/m 11-10 03:45

## 11-10 07:40 · tussenronde
- **0.52.1 door HACS gedownload om 04:59, nog niet actief** (geen HA-herstart sinds 10-10 20:26; diagnostiek-manifest 0.52.0). HACS meldde bij die installatie een back-upfout (`/tmp/hacs_backup/stormchase/__pycache__` niet leeg) — HACS-kwestie, update-entiteit staat wel op 0.52.1. Logboek 0 Stormchase-fouten. Locatie tracker iPhone.
- Geen onweer: niveau groen, 0 inslagen < 50 km, `onweer_nadert` uit → alleen beschikbaarheid: bronstatus "alles in orde", radar laatste succes 07:41, KNMI-push verbonden sinds 20:26 (336 meldingen). Buienradar/Bright Sky/MeteoAlarm-velden staan op 09-10: dat zijn terugvalbronnen die bij werkende KNMI niet draaien (code gecontroleerd) — geen meetfout.
- **Windstoten (H-SC-7, tweede nacht):** 03:45-07:45 n=21: bias **+5,3 km/u** (MAE 5,8; mediaan +4,9); 04-06 u +1,9 (n=11), 06-07:45 u **+7,6** (n=8). Factor 0,67 (24 u, 144 paren) tegen verhouding nu ~0,47 (model 33,5, gemeten 14-17) → de stootvoorspelling zit 's nachts/vroeg te hoog, net als 00-04 u op 10-10 (+5,2). n=2 nachten; toets in de dagafsluiting per uur van de dag.
- **Regen KNMI (H-SC-3):** n=21 uitgekomen (was 19), mediaan −7, 16 te vroeg / 5 te laat. Nieuw: 05:57 voorspeld 47 min, kwam na 20 (**−27**, horizon > 45 min, géén meetvensterartefact); 06:32 12 → 5 (−7, meetvenster); 03:37 voorspeld 22 min, niet uitgekomen.
- Hypotheses: H-SC-3 (KNMI regen), H-SC-6 (vroege naderingsschatting; wacht op onweer), H-SC-7 (nachtverhouding wind). Geen release.

laatste ronde: 11-10 07:40, gemeten t/m 11-10 07:45

## 11-10 11:40 · tussenronde
- HA-herstarts 08:40 en 10:15 → **0.52.2 actief** (0.52.1 afstandsreeks + KNMI-push zonder draadfout). Systeemlog na beide herstarts: 0 Stormchase-fouten/draadfouten. KNMI-push verbonden sinds 10:15. Locatie tracker iPhone.
- Geen onweer: niveau groen, 0 inslagen < 50 km, `onweer_nadert` uit → alleen beschikbaarheid: bronstatus "alles in orde", niets haperend.
- **Windstoten overdag (H-SC-7):** 07:44-11:34 n=24: bias **−1,8 km/u** (MAE 2,8; mediaan −1,3); 07:44-09:44 −2,4, 09:44-11:34 −1,1. Overdag licht te laag, 's nachts te hoog (+5,2/+5,3 op twee nachten) → past bij H-SC-7 (één factor voor dag en nacht). Toets per uur van de dag in de dagafsluiting 12-10 (≥ 3 nachten).
- KNMI-regen (H-SC-3): deze ronde niet geteld (`regen_per_bron` alleen in de diagnostiek, niet als attribuut) → bij de dagafsluiting.
- Hypotheses: H-SC-3 (KNMI regen), H-SC-6 (vroege naderingsschatting; wacht op onweer), H-SC-7 (nachtverhouding wind). Geen release.

laatste ronde: 11-10 11:40, gemeten t/m 11-10 11:40

## 11-10 15:40 · tussenronde
- 20 HA-herstarts 11:47-15:33 (supervisor, geen crash); 0.52.2 actief, 0 Stormchase-fouten. Locatie tracker iPhone. Lichte regen ~15:40.
- Geen onweer: niveau groen, 0 inslagen < 50 km, `onweer_nadert` uit → alleen beschikbaarheid: bronstatus "alles in orde"; radarbeeld 15:41 vers.
- **Windstoten (H-SC-7):** 11:43-15:34 n=24: bias **−3,7 km/u** (MAE 3,9; mediaan −3,5), beide helften −3,9/−3,5 bij gemeten 25-36 km/u. Overdag dus structureel te laag (ochtend −1,8), 's nachts te hoog (+5,2/+5,3) → past bij één factor voor dag en nacht. Toets per uur van de dag in de dagafsluiting 12-10 (≥ 3 nachten).
- KNMI-regen (H-SC-3): niet geteld (alleen in de diagnostiek) → dagafsluiting.
- Hypotheses: H-SC-3, H-SC-6 (wacht op onweer), H-SC-7. Geen release.

laatste ronde: 11-10 15:40, gemeten t/m 11-10 15:40

## 11-10 19:40 · tussenronde
- 10 HA-herstarts 15:49-18:09 (supervisor, geen crash), daarna rustig; 0.52.2 actief, 0 Stormchase-fouten. Locatie tracker iPhone.
- Geen onweer: niveau groen, 0 inslagen < 50 km, `onweer_nadert` uit → alleen beschikbaarheid: bronstatus "alles in orde"; radarbeeld 19:42 vers.
- **Windstoten (H-SC-7):** 15:43-19:34 n=24: bias **−2,6 km/u** (MAE 3,5; mediaan −0,8). Daarin 18:04-18:34 −7..−12: Open-Meteo's `current`-stoot zakte van 34,6 naar 16,6 en sprong om 18:39 terug naar 26,6 (factor bleef 0,68) → modelsprong van de bron, geen integratiefout. Zonder dat halfuur −1,3 (n=20, MAE 2,4). Avond 18:43-19:34 **+0,3** (n=6): de overgang naar de nacht, waar H-SC-7 een positieve bias verwacht. Sinds 18:34 frontdetectie aan (`paren_front` 1 → 8, luchtdruk +2,2 hPa/3 u); factor rekent zonder fronten.
- Hypotheses: H-SC-3 (KNMI regen), H-SC-6 (wacht op onweer), H-SC-7 (dag te laag/nacht te hoog; toets per uur in de dagafsluiting 12-10). Geen release.

laatste ronde: 11-10 19:40, gemeten t/m 11-10 19:45

## 11-10 23:40 · tussenronde
- 8 HA-herstarts 21:02-23:31; 0.52.2 actief, 0 Stormchase-fouten. Locatie tracker iPhone. Lichte regen rond 23:40.
- Geen onweer: niveau groen, 0 inslagen < 50 km, `onweer_nadert` uit → alleen beschikbaarheid: bronstatus "alles in orde"; radarbeeld 23:41 vers.
- **Windstoten (H-SC-7):** 19:44-23:34 n=23: bias +1,0 km/u (MAE 3,5). Avond tot 22:00 **−1,9** (n=14), vanaf 22:00 **+5,4** (n=9; model 12-13 tegen gemeten 5-12). Derde nacht met dezelfde orde (+5,2 / +5,3 / +5,4) → H-SC-7 sterker; L-SC-008 (akkoord) bouwen in de dagafsluiting, en daar per uur van de dag toetsen of een windsterkte-afhankelijke verhouding de nachtbias wegneemt.
- Hypotheses: H-SC-3 (KNMI regen), H-SC-6 (wacht op onweer), H-SC-7. Geen release.

laatste ronde: 11-10 23:40, gemeten t/m 11-10 23:45

## 12-10 03:40 · dagafsluiting 11-10
- Geen purge/repack in de log; HA-herstart 03:33. 11-10: ~40 herstarts (supervisor), 0 Stormchase-fouten; bronnen 100 % (n=2967; 5 d 99,98 %). Niveau hele dag groen, 0 inslagen < 50 km.
- **Gemist in de tussenronden:** cel 15:21-16:03 op 94 → 68,8 km (plus 17:26 op 61,9 km); `onweer_nadert` 15:43-16:06 aan ("nadert snel") → 1 vals nadert-alarm (23 min, geen ~15-min-patroon). Eerste snelheid 54 km/u, 8 min later 35-38 (H-SC-6: eerste schatting te hoog, n=1); aankomst 82 → 109-119 min, niet uitgekomen. L-SC-009 **geverifieerd** (afstandsreeks bevat deze cel met snelheden, over ~40 herstarts).
- **Windstoten 11-10 (HA, n=144):** bias +0,6 km/u (MAE 4,3) tegen kaal model +10,7; dag 08-20 −2,9, nacht +4,0; nacht 12-10 00-03:45 +2,2 (n=23). Max gemeten 37,9 → geen stoot ≥ 60.
- **Toets L-SC-008 / H-SC-7 (replay repo-code op recorderreeksen 10-10 06:00-12-10 03:44, n=274; replay-MAE 4,30 ≈ HA 4,25):** windsterkte-afhankelijke factor (klassen, buren ±25 %, Theil-Sen) MAE 4,23-4,56, nacht blijft +2,6..+3,0 → **verworpen**. Tijd-van-de-dag-factor (uur ±2 u over 72 u) MAE 3,77, dag −1,8 / nacht +1,8; dag/nacht 22-08 3,78 → H-SC-7 = tijd-van-de-dag-effect → nieuw voorstel **L-SC-010 (open)**.
- **Release 0.53.0** (L-SC-008 optie c, akkoord): windmelding op max(bijgesteld, stationsmeting ≤ 40 min), stationsmeting direct getoetst, attributen `windstoten_melding`/`melding_bron`. 756 tests groen, workflow groen, HACS ververst.
- Regen KNMI (H-SC-3) 11-10: n=11 uitgekomen, mediaan −6,7, 7 te vroeg / 4 te laat; cumulatief n=28, −6,9, 20/8.
- Hypotheses: H-SC-3 (KNMI regen te vroeg), H-SC-6 (eerste naderingssnelheid te hoog; 1 cel), H-SC-7 (tijd-van-de-dag → L-SC-010).

laatste ronde: 12-10 03:40, gemeten t/m 12-10 03:45

## 12-10 07:40 · tussenronde
- 2 HA-herstarts (06:14-06:15, 06:47-06:49); **0.53.0 actief**, 0 Stormchase-fouten. Locatie tracker iPhone. Droog.
- Geen onweer: niveau groen, 0 inslagen < 50 km, `onweer_nadert` uit → alleen beschikbaarheid: bronstatus "alles in orde" (geen wisseling), radarbeeld 07:42 vers.
- **L-SC-008c werkt (mechanisme):** `windstoten_melding` 8,1 met `melding_bron` station (stationsmeting 8,1 > bijgesteld 7,9); geen melding (alles < 60).
- **Windstoten (H-SC-7):** 03:45-07:34 n=24: bias **+0,6 km/u** (MAE 1,4); 03:45-06:00 +0,85 (n=14), 06:00-07:34 +0,25 (n=10). Nacht 00-03:45 was +2,2 → deze nacht kleinere nachtbias bij zwakke wind (gemeten 5-14). Factor 0,66 (129 paren, 15 front weggelaten). L-SC-010 blijft open; meer nachten nodig.
- Hypotheses: H-SC-3 (KNMI regen), H-SC-6 (eerste naderingssnelheid te hoog), H-SC-7 (tijd-van-de-dag → L-SC-010). Geen release.

laatste ronde: 12-10 07:40, gemeten t/m 12-10 07:42

## 12-10 11:40 · tussenronde
- 7 HA-herstarts (08:26-10:53, EMS-releases); 0 Stormchase-fouten. **0.54.0** (L-SC-010, chatsessie 11:21) gereleased; HACS toonde hem nog niet → informatie ververst; nog niet geïnstalleerd (actief 0.53.0).
- Droog, groen, 0 inslagen < 50 km → alleen beschikbaarheid: 15 bronnen "alles in orde", 1× 503 Open-Meteo 10:00 (extern, hersteld), KNMI-push verbonden, radarbeeld 11:42.
- **Windstoten (H-SC-7 / basis voor L-SC-010):** 07:44-11:44 n=24, bias +0,6 km/u (MAE 1,7); vóór 10:00 **+1,65** (n=13), vanaf 10:00 **−0,63** (n=11) → hetzelfde dag/nacht-patroon (ochtend boven, middag onder) dat 0.54.0 moet wegnemen. Nulmeting voor de verificatie na installatie.
- L-SC-008c: `windstoten_melding` 12,2 met bron station (meting 12,2 > bijgesteld 10,1); geen melding.
- Hypotheses: H-SC-3 (KNMI regen), H-SC-6 (eerste naderingssnelheid te hoog), H-SC-7 (tijd-van-de-dag, gebouwd 0.54.0 → verifiëren). Geen release.

laatste ronde: 12-10 11:40, gemeten t/m 12-10 11:45

## 12-10 15:40 · tussenronde
- 6 HA-herstarts (12:38-15:43); actief **0.54.2** (0.54.0 sinds 12:38, 0.54.2 sinds 14:45; ensemble-fixes van een andere sessie). 0 Stormchase-fouten. Locatie tracker iPhone.
- Geen onweer: niveau groen, 0 inslagen < 50 km, `onweer_nadert` uit → alleen beschikbaarheid: bronstatus "alles in orde", radarbeeld 15:40 vers, KNMI-push verbonden.
- **Onweerskans ensemble:** `unknown` t/m 14:45, daarna 0 % (icon_eu_eps, 40 leden) → werkt sinds 0.54.2; `ensemble_leden` laatste fout 14:36 (vóór installatie). 24 u volgen.
- **Windstoten / L-SC-010:** 11:44-15:34 n=24 bias −1,6 km/u (MAE 2,7). Vóór 12:38 (24-uursfactor) −3,6 (n=6); met tijdvakfactor 0,72 12:43-14:34 **+0,8** (n=12), daarna **−4,5** (n=6) toen de gemeten stoot opliep naar 17-20 km/u. Eén middag → geen oordeel; dagmeting om 03:40.
- L-SC-008c: `windstoten_melding` 17,0 met bron station (> bijgesteld 13,8); geen melding (< 60).
- Hypotheses: H-SC-3 (KNMI regen te vroeg), H-SC-6 (eerste naderingssnelheid te hoog; wacht op onweer), H-SC-7 (tijd-van-de-dag, 0.54.0 actief → verifiëren). Geen release.

laatste ronde: 12-10 15:40, gemeten t/m 12-10 15:45

## 12-10 19:40 · tussenronde
- 2 HA-herstarts (16:12, 18:35); actief **0.54.2**, 0 Stormchase-fouten. Locatie tracker iPhone. Droog, helder.
- Geen onweer: niveau groen, 0 inslagen < 50 km, `onweer_nadert` uit → alleen beschikbaarheid: bronstatus "alles in orde" (15 bronnen, Open-Meteo 1 fout 10:00), radarbeeld 19:41 vers, KNMI-push verbonden. Ensemble 0 % (icon_eu_eps, 40 leden) → werkt door na de herstarts.
- **Windstoten / L-SC-010** (tijdvakfactor 0,70, 45 paren; 24-uursfactor 0,59): 15:44-19:34 n=24 bias **+1,6 km/u** (MAE 2,7). Tot 17:15 −0,4 (n=10); **17:15-18:35 +4,5** (n=8: gemeten zakte in 20 min van 12-16 naar 7-8 km/u, de verwachting volgde pas bij de half-uursverversingen 17:42/18:12/18:35); na 18:35 +1,2 (n=6). De avondfout is vooral de vertraging bij de windafname rond zonsondergang, niet de factor.
- L-SC-008c: `melding_bron` verwachting (7,6 > gemeten 7,3); geen windmelding (< 60).
- Hypotheses: H-SC-3 (KNMI regen te vroeg), H-SC-6 (eerste naderingssnelheid te hoog; wacht op onweer), H-SC-7 (tijd-van-de-dag, 0.54.0 actief → verifiëren in de dagafsluiting; let op de avondovergang 17-19 u). Geen release.

laatste ronde: 12-10 19:40, gemeten t/m 12-10 19:46

## 12-10 23:40 · tussenronde
- 6 HA-herstarts (21:10-23:17); actief **0.54.2**, 0 Stormchase-fouten. Locatie tracker iPhone. Droog, helder.
- Geen onweer: groen, 0 inslagen < 50 km → alleen beschikbaarheid: "alles in orde", radar 23:43 vers, KNMI-push verbonden (11 meldingen). Ensemble 0 %.
- **Windstoten / L-SC-010** (tijdvakfactor 0,60, 60 paren; 24-uursfactor 0,63): 19:44-23:33 n=24 bias **−0,1 km/u** (MAE 1,6). Tot 22:00 +1,1 (n=14, avonddaling); **na 22:00 −1,7** (n=10) bij oplopende gemeten stoot 10,6 → 13,8. Vorige nachten zat het 24-uursmodel 's nachts +2,5..+5,2 te hoog → eerste nacht met tijdvakfactor zonder overschatting (n=1, en de wind nam toe). H-SC-7: eerste steun; dagmeting 03:40.
- L-SC-008c: `windstoten_melding` 13,8 met bron station; geen windmelding (< 60).
- Hypotheses: H-SC-3 (KNMI regen te vroeg), H-SC-6 (eerste naderingssnelheid te hoog; wacht op onweer), H-SC-7 (tijd-van-de-dag; nacht nu −1,7 i.p.v. +2,5..+5,2). Geen release.

laatste ronde: 12-10 23:40, gemeten t/m 12-10 23:43

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

laatste ronde: 24-10 03:40, gemeten t/m 24-10 03:50
