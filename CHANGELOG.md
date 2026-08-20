# Changelog

Alle noemenswaardige wijzigingen aan dit project staan hier.

Het formaat volgt [Keep a Changelog](https://keepachangelog.com/nl/1.1.0/),
en het project gebruikt [semantische versienummers](https://semver.org/lang/nl/).

## [0.2.0] — 2026-08-20

### Toegevoegd

- **Dashboardstrategie.** Een nieuw dashboard met `strategy: {type: custom:stormchase}`
  bouwt zichzelf op uit de entiteiten die op dat moment bestaan. Nieuwe
  sensoren in een volgende versie verschijnen vanzelf op het dashboard; je
  hoeft geen YAML meer over te typen.
  - Ringtegels worden gegenereerd voor elke ingestelde ring, ongeacht het
    aantal.
  - Secties waarvan de sensoren ontbreken of niet beschikbaar zijn worden
    weggelaten in plaats van als lege tegel getoond.
  - De locatietegel verschijnt alleen als je niet thuis bent.
  - De kaarten centreren op de actieve locatie in plaats van op de
    thuislocatie, dus op vakantie kijken ze naar de juiste plek.
  - Instelbaar via de strategie-opties: titel, bronsensoren, coördinaten,
    eigen iRadar-embed en welke kaarten je wil zien.

### Gewijzigd

- Het JavaScript-bestand wordt geserveerd met het versienummer in de URL,
  zodat browsers na een update de nieuwe versie ophalen in plaats van een
  oude uit de cache.
- `http` en `frontend` toegevoegd als afhankelijkheden in het manifest.

### Opmerking

De statische `dashboards/stormchase.yaml` blijft bestaan voor wie liever
zelf aan de kaarten sleutelt, maar die moet je bij elke update handmatig
bijwerken. De strategie niet.

## [0.1.0] — 2026-08-20

Eerste release.

### Toegevoegd

**Afgeleide bliksemgegevens**

- Naderingssnelheid in km/u, berekend via lineaire regressie over een venster
  van 15 minuten. Positief betekent dat het onweer dichterbij komt. Regressie
  in plaats van eerste-tegen-laatste, omdat losse inslagen tientallen
  kilometers kunnen springen.
- Geschatte aankomsttijd in minuten, alleen beschikbaar bij daadwerkelijke
  nadering.
- Trendsensor met leesbare tekst: nadert snel, nadert, stabiel, trekt weg,
  trekt snel weg.
- Drie instelbare afstandsringen, standaard 10 / 25 / 50 km, die de
  `geo_location` markers tellen.
- Teller voor het totaal aantal actieve markers.

**Onweersparameters via Open-Meteo**

- CAPE, CAPE-piek over de komende 12 uur, Lifted Index en convectieve
  remming. Geen API-sleutel nodig.
- Samengestelde chase-potentie van 0 tot 100, met in de attributen de
  opbouw per onderdeel zodat de score navolgbaar blijft.

**Locatie**

- Vier bronnen: de thuislocatie van Home Assistant, een zone, een gevolgd
  apparaat of persoon, of handmatige coördinaten.
- Diagnostische sensor die laat zien welke bron actief is, met de
  coördinaten als attribuut.
- Bij een verplaatsing van meer dan 15 km worden de weerparameters direct
  opnieuw opgehaald in plaats van te wachten op het volgende halfuur.
- Valt terug op de thuislocatie zodra een zone of tracker geen GPS-positie
  heeft.

**Binary sensors**

- Onweer nabij, op basis van de instelbare waarschuwingsafstand.
- Onweer nadert, op basis van een structureel afnemende afstand.
- Beide dragen afstand, azimut, snelheid en aankomsttijd als attributen,
  zodat automatiseringen niet meerdere entiteiten hoeven uit te lezen.

**Meldingen**

- Drie events: `stormchase_nearby`, `stormchase_approaching` en
  `stormchase_cleared`. Deze vuren bij een overgang, niet bij elke update,
  dus je krijgt één melding per onweersgebied.
- Blueprint met instelbare notify-service, maximale afstand, wachttijd tegen
  herhaling, optioneel stiltevenster en extra voorwaarden.

**Overig**

- Config flow en options flow, beide volledig achteraf aanpasbaar.
- Nederlandse en Engelse vertalingen.
- Entity-iconen via `icons.json`, inclusief statusafhankelijke iconen voor
  de binary sensors.
- Dashboard-YAML met twee secties: sensoren links, kaarten rechts.
- Logo en icoon in `brands/`, klaar voor een pull request naar
  home-assistant/brands.

### Bekende beperkingen

- De naderingssnelheid volgt de laatste inslag, niet een specifieke cel. Bij
  twee onweersgebieden tegelijk springt de afstand tussen beide en wordt de
  trend onbetrouwbaar.
- De aankomsttijd gaat uit van een rechte lijn en constante snelheid.
- De locatie-instelling geldt alleen voor de weerparameters. De afstand tot
  de inslagen komt van de Blitzortung-integratie, die zijn eigen locatie
  heeft.
- De blueprint wordt niet meegeïnstalleerd door HACS.
- Bij een herstart van Home Assistant vuurt de eerste meting bewust geen
  event af, zodat je niet bij elke herstart tijdens onweer opnieuw een
  melding krijgt.

[0.2.0]: https://github.com/Roedie84/StormchaseNL/releases/tag/v0.2.0
[0.1.0]: https://github.com/Roedie84/StormchaseNL/releases/tag/v0.1.0
