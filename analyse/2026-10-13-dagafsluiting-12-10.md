# Dagafsluiting 12-10 · StormchaseNL (ronde gestart 03:40, afgerond 11:30)

LEERLOG.md/KPI.csv niet zelf bijgewerkt: git-netwerkacties en lokale python werden in deze sessie door de toestemmingscontrole geweigerd. De volgende ronde neemt deze regels over (KPI.csv type DAG, datum 2026-10-12) en verwijdert dit bestand.

## KPI's dag 12-10
- sc_onweer_gebeurtenissen_50km 0 (niveau hele dag groen; 0 inslagen < 50 km; `onweer_nadert` niet aan volgens de tussenrondes)
- sc_herstarts 24 (som tussenrondes: 03:33, 06:14, 06:47, 7× 08:26-10:53, 6× 12:38-15:43, 16:12, 18:35, 6× 21:10-23:17); 0 Stormchase-fouten
- sc_bronnen: "alles in orde" in alle rondes; 1× 503 Open-Meteo 10:00 (extern, hersteld); onweerskans-ensemble `unknown` t/m 14:45, daarna 0 % (0.54.2)
- sc_windstoten_bias_kmh +0.56 (n=24 uurgemiddelden, bijgesteld − gemeten; MAE op uurgemiddelden 1.70 — NIET vergelijkbaar met de eerdere MAE op 10-min-standen 4.3)
  - vóór 12:38 (24-uursfactor, 0.53.0) uren 00-12: +0.84 (MAE 1.52, n=13)
  - met tijdvakfactor (0.54.x) uren 13-23: +0.22 (MAE 1.91, n=11)
  - dag 08-20 +0.26 (n=12), nacht 20-08 +0.86 (n=12); avond 17-19 u +3.3/+3.1 (windafname rond zonsondergang loopt achter), 22-24 u −1.4/−2.2
- Meetbaarheid: uurgemiddelden uit de statistiek zijn het enige wat zonder python te rekenen was; de volgende ronde moet de 10-min-reeks (n≈144) opnieuw rekenen voor een vergelijkbare MAE.

## Geleerd
- L-SC-010 (tijdvakfactor, actief sinds 12-10 12:38): eerste halve dag bias +0.2 km/u; eerste nacht (22-24 u) −1.4..−2.2 i.p.v. +2.5..+5.4 met de 24-uursfactor. Steun, n=1 → status blijft "gebouwd", verifiëren na ≥ 3 dagen (dagafsluiting 15-10).
- H-SC-7 nieuw deelpunt: de resterende avondfout zit in de vertraging bij snelle windafname 17-19 u (verwachting ververst per half uur), niet in de factor.
- H-SC-3 (KNMI regen te vroeg) en H-SC-6 (eerste naderingssnelheid te hoog): geen nieuwe gebeurtenis op 12-10.

## Release
Geen.

laatste ronde: 13-10 11:30 (dagafsluiting 12-10), gemeten t/m 12-10 24:00
