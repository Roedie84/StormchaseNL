Dashboard dat zichzelf bijwerkt.

## Wat er nieuw is

De integratie levert nu een **dashboardstrategie** mee. Maak een dashboard
aan, zet er dit in en je bent klaar:

```yaml
strategy:
  type: custom:stormchase
```

De view wordt bij elke paginalading opnieuw opgebouwd uit de entiteiten die
op dat moment bestaan. Voeg ik in een volgende versie een sensor toe, dan
staat de tegel er na de update vanzelf — geen YAML meer overtypen.

Verder past de strategie zich aan je installatie aan: ringtegels voor elke
ring die je hebt ingesteld, geen lege parametertegels als Open-Meteo eruit
ligt, de locatietegel alleen als je niet thuis bent, en kaarten die op je
actieve locatie centreren in plaats van op je thuisadres.

Alles is te overrulen via de strategie-opties: titel, bronsensoren,
coördinaten, je eigen iRadar-embed en welke kaarten je wil zien. Zie de
README.

## Upgraden vanaf 0.1.0

Niets verplicht. Gebruik je de statische `dashboards/stormchase.yaml`, dan
blijft die gewoon werken. Wil je overstappen: vervang de inhoud van je
dashboard door de twee regels hierboven.

Na de update één keer je browser hard verversen als het dashboard niet
meteen laadt. Het versienummer zit in de URL van het script, dus normaal
gesproken pikt de browser het vanzelf op.

Volledige lijst met wijzigingen: zie CHANGELOG.md.
