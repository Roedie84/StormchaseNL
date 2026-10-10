# Tests

Draaien met `python -m pytest tests -q` vanuit de hoofdmap.

De modules `cel.py`, `indices.py`, `taal.py` en `validatie.py` bevatten
bewust geen Home Assistant-imports. Daardoor zijn ze zonder die hele
installatie te testen en draait de suite in een fractie van een seconde, snel
genoeg om bij elke wijziging aan te zetten. Een van de tests bewaakt die
scheiding.

## Wat er getest wordt

| Bestand | Onderwerp |
|---|---|
| `test_taal.py` | Vertaling van MeteoAlarm-termen, samengestelde waarschuwingen, hoofdletters inclusief de ij |
| `test_indices.py` | Windschering, peiling, stabiliteit, rotatie- en hagelkans, het samenvattend oordeel |
| `test_cel.py` | Clusteren van inslagen, richting en snelheid van een cel, passageberekening, inslagfrequentie |
| `test_validatie.py` | Voorspellingen vastleggen, nakijken, verlopen en samenvatten |
| `test_tijd.py` | Waarden opzoeken bij modellen met verschillende tijdstappen |
| `test_spreiding.py` | Mediaan, spreiding en modelovereenstemming |
| `test_verouderd.py` | Terugval op oude gegevens bij een storing |
| `test_radar.py` | Opbouw van de radar-URL's |
| `test_wolken.py` | Kaartdienstverzoek en herprojectie van de wolkenlaag |
| `test_bronhistorie.py` | Gelukt/mislukt per bron per dag, bewaard over herstarts (L-SC-002) |
| `test_release_0470.py` | Herstartbestendigheid: validatie, schuilregel, cellen, nadering, waarschuwingen, wachttijden en tellers over een herstart |
| `test_release_0480.py` | Huidige weerconditie volgt de radar bij regen: rainy, pouring, lightning-rainy, nacht en verouderde radarwaarden |
| `test_release_0490.py` | KNMI-bronnen: rastercellen tegen pyproj-referentiewaarden, NL-grens en waarschuwingsregio, waarschuwingen, nowcast, EDR-metingen, drukverloop, verwachting, fouten/429/403 en afremmen, pushmeldingen, radarvooruitblik, terugval en privacy van de sleutels |
| `test_release_0510.py` | Windstoten bijgesteld met de stationsmeting (leren, grenzen, herstart) en het regenbeeld in één zin |
| `test_release_0520.py` | Windstootcorrectie pas na zes uur, frontdetectie (onweer, druksprong, stootsprong, naloop) en oude opslag uit 0.51.x |
| `test_release_0500.py` | Dashboard als commandocentrum: eigen element geregistreerd, geen externe bestanden of HACS-kaarten, alle entiteiten bekend, zuinig hertekenen, cachebust met versie, en (met Node.js) de uitvoer van de strategie |
| `test_structuur.py` | Controles op de code zelf |

## Waarom er structuurtests zijn

Bij het bewerken van importlijsten zijn ooit constantnamen op de verkeerde
regel terechtgekomen. Dat compileerde prima en sloeg pas toe toen het
configuratiescherm werd geopend, met als enige melding "Unknown error
occurred". `test_structuur.py` vangt precies dat soort fouten:

- elk formulierveld krijgt precies een sleutel mee
- geen kale constantnamen als sleutel in een dict
- geen regels die alleen uit een naam bestaan
- elke stap in de config flow heeft een vertaling in beide talen
