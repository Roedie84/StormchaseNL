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
