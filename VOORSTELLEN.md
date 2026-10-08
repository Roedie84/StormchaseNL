# Voorstellen StormchaseNL

Status: open / akkoord / afgewezen / gebouwd vX / geverifieerd / teruggedraaid. Ruud keurt goed via de chat ("akkoord L-SC-00x").

## L-SC-001 · naderingssnelheid alleen uit nieuwe inslagafstanden (geen 10-s herhalingen)
- Status: **open** (raakt `onweer_nadert`, trend en de aankomsttijd in de melding → Ruud beslist)
- Onderbouwing: 07-10 21:15-22:37 (n=236 aankomstwaarden): aankomst sprong 45 → 1214 min en 4168 → 167 min zonder nieuwe inslag; 4× nadert-aan voor een onweer dat nooit binnen 50 km kwam. Replay van `_speed_from_history` op de echte reeks reproduceert de zaagtand exact; met alleen nieuwe afstanden blijft de schatting stabiel (36 min bij 83 km, 24,8 km/u).
- Voorstel: in `coordinator.py` een punt aan `_history` alleen toevoegen als de afstand (of de nieuwste inslagtijd) veranderd is; MIN_SAMPLES dan op aantal echte metingen (bv. 3). Plus test met de reeks van 07-10.
- Verwacht effect: geen zaagtand meer; minder korte nadert-pulsen; aankomsttijd in meldingen stabiel.
- Extra onderbouwing 08-10: 3 van de 4 nadert-perioden op 07-10 duurden 14,8-15,0 min, precies `TREND_WINDOW` (15 min).
- Extra onderbouwing 07-10 23:45: validatietellers van de integratie zelf: aankomst 1/6 uitgekomen (≤15 min 0/3), terwijl passage 21/21 haalt.
- Meten na bouw: validatieteller aankomst (nu 1/6) en per onweersgebeurtenis het aantal nadert-wissels, spreiding van aankomst zonder nieuwe inslag, en voorspelde tegen werkelijke aankomst (validatie).

## L-SC-002 · bronstatistiek bewaren over herstarts
- Status: **gebouwd 0.44.0** (08-10 04:36) — verifiëren na installatie en ≥2 dagen met een herstart ertussen
- (eerder: gepland, zelf bouwen: meetbaarheid; de code bewaarde het nog niet)
- Onderbouwing: 07-10 23:45: `statistieken.gestart_op` 21:04 UTC, draaitijd 0,7 u; na elke herstart (vandaag ~10) begint gelukt/mislukt per bron opnieuw. Betrouwbaarheid per bron over dagen is zo niet uit de integratie te halen.
- Bouw: tellers per bron per dag in de Store bewaren (rollend 30 d), in diagnostics tonen; test.
- Meten na bouw: diagnostics toont slaagpercentage per bron over ≥2 dagen na een herstart.
