# Voorstellen StormchaseNL

Status: open / akkoord / afgewezen / gebouwd vX / geverifieerd / teruggedraaid. Ruud keurt goed via de chat ("akkoord L-SC-00x").

## L-SC-001 · naderingssnelheid alleen uit nieuwe inslagafstanden (geen 10-s herhalingen)
- Status: **open** (raakt `onweer_nadert`, trend en de aankomsttijd in de melding → Ruud beslist)
- Onderbouwing: 07-10 21:15-22:37 (n=236 aankomstwaarden): aankomst sprong 45 → 1214 min en 4168 → 167 min zonder nieuwe inslag; 4× nadert-aan voor een onweer dat nooit binnen 50 km kwam. Replay van `_speed_from_history` op de echte reeks reproduceert de zaagtand exact; met alleen nieuwe afstanden blijft de schatting stabiel (36 min bij 83 km, 24,8 km/u).
- Voorstel: in `coordinator.py` een punt aan `_history` alleen toevoegen als de afstand (of de nieuwste inslagtijd) veranderd is; MIN_SAMPLES dan op aantal echte metingen (bv. 3). Plus test met de reeks van 07-10.
- Verwacht effect: geen zaagtand meer; minder korte nadert-pulsen; aankomsttijd in meldingen stabiel.
- Meten na bouw: per onweersgebeurtenis het aantal nadert-wissels, spreiding van aankomst zonder nieuwe inslag, en voorspelde tegen werkelijke aankomst (validatie).
