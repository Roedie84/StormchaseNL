# Baseline StormchaseNL

| KPI | referentie | periode / n | vastgesteld |
|---|---|---|---|
| Onweersgebeurtenissen binnen 50 km | 0 | 28-09..07-10 | 07-10 23:15 |
| Nadert-aan zonder inslag <50 km | 8 perioden in 2 avonden | 28-09..07-10 | 07-10 23:15 |
| Aankomst-spreiding zonder nieuwe inslag | factor ~27 binnen 12 min | 07-10, n=236 | 07-10 23:15 |
| Haperingen radar / open_meteo / buienradar | 15 / 16 / 5 in 10 d | 28-09..07-10 | 07-10 23:15 |
| Radarbeeld-leeftijd | 4-7 min | momentopnames 08-10 | 08-10 03:40 |
| Validatie aankomst uitgekomen | 1/6 (17%) | integratietellers sinds ~31-08 | 07-10 23:45 |
| Validatie passage uitgekomen · afstandsfout | 21/21 (≤45 min) · 18,6 km | idem | 07-10 23:45 |
| Validatie regen uitgekomen | 21/30 (70%) | idem | 07-10 23:45 |
| Slaagpercentage bronnen per dag | 99,73 % | 07-10, n=2248, over 16 herstarts | 08-10 03:40 |
| Haperingen per dag | 2 | 07-10 | 08-10 03:40 |
| Herstarts per dag | 16 | 07-10 | 08-10 03:40 |
| Valse nadert-alarmen per onweer | 4 | 28/29-09 en 07-10 | 08-10 03:40 |
| Blitzortung nachtelijk onbeschikbaar | 11-21 min | 07-10, 08-10 | 08-10 03:40 |
| Passage binnen 10 / 20 km | 5/12 · 7/12 (alleen laatste 20 uitkomsten; vervangen) | bewaarde uitkomsten t/m 08-10 | 08-10 07:40 |
| Passage binnen 10 / 20 km (alle bewaarde) | 9/24 (38%) · 12/24 (50%) | ≤15 min 6/13, 15-45 3/8, >45 0/3 | 08-10 11:45 |
| Radarbeeld-wissels na fix | max gat 10 min | 08-10 06:23-07:43, n=16 | 08-10 07:40 |
| Regenvalidatie afwijking (mediaan) | −10,6 min, 9/10 negatief; ≤15 min ≈ −8 | 10 uitkomsten t/m 08-10 | 08-10 19:40 |
| Slaagpercentage bronnen per dag | 100 % (n=1686, 20 herstarts) | 08-10 | 09-10 03:40 |
| Validatievenster (alle soorten samen) | 60/60 vol: regen 34, passage 21, aankomst 5 | 09-10 03:47 | 09-10 03:40 |
| Windstoten verwacht − gemeten (model, vóór 0.51.0) | +13,6 km/u (MAE 13,6) | 09-10 06:03-23:33, n=104 | 10-10 03:40 |
| Windstoten na bijstelling | −0,2 km/u (MAE 6,9); laatste 2,5 u −5,7 | 23:34-03:44, n=26 | 10-10 03:40 |
| Slaagpercentage bronnen per dag | 99,93 % (n=2761) | 09-10 | 10-10 03:40 |
| Slaagpercentage bronnen per dag | 100 % (n=2766, 12 herstarts); 4 d 99,92 % | 10-10 | 11-10 03:40 |
| Windstoten na bijstelling (dag) | −2,3 km/u (MAE 4,8) tegen kaal model +10,9 | 10-10, n=153 | 11-10 03:40 |
| Windstoten bias per modelklasse <30/30-38/38-45/≥45 | −3,8 / −3,2 / −4,3 / +2,5 km/u | 10-10, n=53/47/20/33 | 11-10 03:40 |
| Valse nadert-alarmen per dag (na 0.45.0) | 2 bij 3 cellen 46-93 km; geen periode van ~15 min | 10-10 | 11-10 03:40 |
| Radarbeeld-wissels | mediaan 3,0 min, max 7,4 | 09-10 23:57-11-10 03:45, n=559 | 11-10 03:40 |
| Regen KNMI afwijking | mediaan −6,9 min, 14 te vroeg / 5 te laat | regen_per_bron, n=19 | 11-10 03:40 |
| Windstoten na bijstelling (dag) | +0,6 km/u (MAE 4,3); dag 08-20 −2,9, nacht +4,0 | 11-10, n=144 | 12-10 03:40 |
| Windstoten replay-MAE (huidige code) | 4,30 km/u (dag −2,7 / nacht +2,5) | 10-10 06:00-12-10 03:44, n=274 | 12-10 03:40 |
| Slaagpercentage bronnen per dag | 100 % (n=2967, ~40 herstarts); 5 d 99,98 % (n=10608) | 11-10 | 12-10 03:40 |
| Valse nadert-alarmen per dag | 1 (23 min) bij 1 cel 69-94 km | 11-10 | 12-10 03:40 |
| Regen KNMI afwijking | mediaan −6,9 min, 20 te vroeg / 8 te laat | regen_per_bron, n=28 | 12-10 03:40 |
| Windstoten na bijstelling (uurgemiddelden, tijdvakfactor) | −0,9 km/u (MAE 2,7); nacht −1,2 / dag −0,7 | 13..20-10, n=192 u | 21-10 19:40 |
| Slaagpercentage bronnen per dag | 99,15-99,96 % (mediaan 99,9) | 13..20-10, ~2770/dag | 21-10 19:40 |
| Herstarts per dag (proxy 'laatst bekend') | 2-20 (mediaan 11,5) | 13..20-10 | 21-10 19:40 |
| Radarbeeld-wissels | mediaan 3,0 min, max 7,8 | 20-10, n=485 | 21-10 19:40 |
| Regen KNMI afwijking | mediaan −7 min, 33 eerder / 13 later; LOO-correctie −9,7 % (niet actief) | n=46 | 21-10 19:40 |
| Passage met gemeten afstand | 19/26 (73 %); 17-10 0/3 | bewaard t/m 21-10 | 21-10 19:40 |
| Bronnen per dag | 99,82 % (2.715 rondes) | 21-10 | 22-10 03:40 |
| Windstoten bias dag (uurgemiddelden) | +0,89 km/u, MAE 2,16 (nacht +0,52) | 21-10, n=24 | 22-10 03:40 |
| Passages met gemeten afstand | 19/26 (73 %) vóór 0.56.1 | t/m 21-10 | 22-10 03:40 |
| Celsnelheid > 120 km/u (tijdsaandeel tijdens onweer) | 37 %, max 407, mediaan 42 | 22-10 14:20-15:34 | 22-10 15:40 |
| Windstoten bias naar trend meting (uurgemiddelden) | dalend +1,74 · stijgend −1,46 km/u; MAE 2,52 (model+½·fout vorig uur: 2,24) | 12..22-10, n=238 | 23-10 03:40 |
| Bronstatus vals "hapert" (reservebron) | 13,6 u/dag | 22-10 | 23-10 03:40 |
| Windstoten bias dag (uurgemiddelden) | −2,17 km/u, MAE 2,50 (stijgend −2,82, dalend −0,94) | 23-10, n=24 | 24-10 03:40 |
| Bronstatus vals "hapert" (reservebron) | 0 u/dag na 0.58.4 | 23-10 | 24-10 03:40 |
| Windvooruitblik piek tegen gemeten max | +19,7 km/u (84,6 / 64,9) | 23-10, n=1 | 24-10 03:40 |

| Windstoten bias per stationsmeting | +5,6 km/u (n=134); zonder kale-modelperioden −1,3 (n=77) | 24-10 | 25-10 03:40 |
| Windstoten tijdens een front (tijdvakfactor + bijsturing) | avond −6,4 / MAE 6,7 (n=32) · nacht −0,0 / MAE 4,4 (n=29) | 24/25-10 | 25-10 03:40 |
| Windvooruitblik piek tegen gemeten max | +5,4 km/u (65 / 59,6) | 24-10, n=1 | 25-10 03:40 |
| Windstoten bias per stationsmeting (dag) | +0,7 km/u, MAE 3,7 (n=151); geen kale-modelperioden | 25-10 | 26-10 03:40 |
| Windstoten bias 7 d (dagwaarden) | +1,1 km/u (zonder 24-10 kaal model +0,3) | 19..25-10 | 26-10 03:40 |
| Valse geel-perioden per onweersdag | 2 (21 min; 29 km ruis + 91 km ver weg) | 25-10, n=1 dag | 26-10 03:40 |
| Regenstart per dag | 5 treffers / 2 vals / 1 gemist | 25-10 | 26-10 03:40 |
| Windstoten verwachting vóór stationsmeting (dag) | bias +0,27 km/u · MAE 2,67 (n=120, 5 blokken) | 26-10 | 27-10 03:40 |
| Regenstart (dag) | 3 treffers / 0 gemist / 2 valse aftellingen | 26-10 | 27-10 03:40 |
| Windstoten verwachting vóór stationsmeting (dag) | bias +0,47 km/u · MAE 3,45 (n=144, 6 blokken; bui-stap −19,5) | 27-10 | 28-10 03:40 |
| Windstoten bias 7 d (dagwaarden) | +1,33 km/u (zonder 24-10 kaal model +0,62) | 21..27-10 | 28-10 03:40 |
| Regenstart (4 d) | 12 raak / 7 vals / 1 gemist | 24..27-10 | 28-10 03:40 |
