# Changelog

Alle noemenswaardige wijzigingen aan dit project staan hier.

Het formaat volgt [Keep a Changelog](https://keepachangelog.com/nl/1.1.0/),
en het project gebruikt [semantische versienummers](https://semver.org/lang/nl/).

## [0.7.0] — 2026-08-21

### Toegevoegd

- **Waarschuwingen volgen nu ook je locatie.** Het land staat standaard op
  automatisch: de integratie zoekt op in welk land je bent en haalt de
  MeteoAlarm-feed van dat land op. Rijd je Duitsland binnen, dan krijg je
  Duitse waarschuwingen. Handmatig een land kiezen kan nog steeds.
- Het gevonden land staat in het attribuut `land` van
  `sensor.stormchase_waarschuwingsniveau`.

### Gewijzigd

- Het land wordt alleen opnieuw opgezocht als je meer dan ongeveer vijftig
  kilometer verplaatst bent, zodat er niet elk kwartier een verzoek uitgaat.
- Voor landen zonder MeteoAlarm-feed blijft de sensor leeg in plaats van een
  fout te geven.

## [0.6.0] — 2026-08-21

Weerbericht en officiele waarschuwingen.

### Toegevoegd

- **Weerentiteit `weather.stormchase`** met de actuele omstandigheden en een
  verwachting per uur en per dag, op de locatie die de integratie gebruikt.
  Volgt de integratie een device_tracker, dan reist het weerbericht mee.
  Bron is Open-Meteo; er is geen API-sleutel nodig.
- **Officiele weerwaarschuwingen via MeteoAlarm**, de Europese koepel waar
  onder meer het KNMI aan levert. Werkt daardoor in heel Europa in plaats van
  alleen in Nederland.
  - `sensor.stormchase_waarschuwingsniveau` toont groen, geel, oranje of
    rood, met alle actieve waarschuwingen als attribuut.
  - `binary_sensor.stormchase_weerwaarschuwing` is aan zolang er een geldt.
  - Instelbaar: het land, een optioneel filter op regionaam, vanaf welk
    niveau je bericht wil en of er gemeld moet worden.
  - Event `stormchase_alert` per nieuwe waarschuwing, elk hoogstens een keer.
- Op het dashboard: een gekleurde banner bovenaan bij een actieve
  waarschuwing, en een weerkaart met uurverwachting.

### Opmerking

Waarschuwingsmeldingen negeren de wachttijd en het stiltevenster. Ze komen
van een nationale weerdienst en gaan over gevaar; elke waarschuwing wordt
bovendien maar een keer gemeld, dus herhaling is geen risico.

## [0.5.0] — 2026-08-21

Neerslagverwachting erbij.

### Toegevoegd

- **Regenmelding.** Je krijgt bericht wanneer er binnen de ingestelde tijd
  regen aankomt, standaard tien minuten vooruit. De melding noemt de zwaarte
  en de piekintensiteit: "Over ongeveer 10 minuten flinke bui, tot 6,2 mm/u."
- **Bron: Buienradar.** De neerslagtekst geeft per vijf minuten een
  verwachting voor de komende twee uur, op exacte coordinaten. Buiten het
  radarbereik valt de integratie automatisch terug op de kwartierwaarden van
  Open-Meteo; welke bron actief is staat in de attributen.
- Nieuwe sensoren: `regen_begint_over`, `neerslagintensiteit` en
  `neerslagpiek_2_uur`. De eerste draagt de volledige verwachting als
  attribuut, zodat je er zelf op kunt bouwen.
- Nieuwe binary sensor `regen_verwacht`, aan bij regen nu of binnenkort.
- Event `stormchase_rain_incoming`, dat alleen bij de overgang van droog naar
  "komt eraan" afgaat.
- Op het dashboard: een neerslagblok met de stand van zaken en een grafiek
  van de komende twee uur, plus een badge met de tijd tot de eerste druppel.
- Instelbaar bij de meldingen: aan of uit, hoeveel minuten vooruit, en vanaf
  welke intensiteit het meetelt zodat motregen geen bericht oplevert.

### Gewijzigd

- Regen en onweer hebben elk hun eigen wachttijd, zodat een regenmelding geen
  onweerswaarschuwing kan tegenhouden.

## [0.4.0] — 2026-08-21

Meldingen zitten nu in de integratie zelf.

### Toegevoegd

- **Ingebouwde meldingen.** Geen losse automatisering of blueprint meer
  nodig: kies bij het instellen een of meer notify-diensten en de integratie
  stuurt zelf berichten bij onweer. Instelbaar zijn de maximale afstand, of
  je ook bij nadering wil melden, of je bericht krijgt als het weer over is,
  de titel, een wachttijd tegen herhaling en een stiltevenster.
- **Schakelaar `switch.stormchase_meldingen`** om de meldingen tijdelijk uit
  te zetten zonder de instellingen aan te raken. De stand blijft bewaard na
  een herstart en staat als kaart op het dashboard.
- **Service `stormchase.test_notification`** die een proefmelding stuurt,
  langs alle drempels en wachttijden heen, om te controleren of de berichten
  aankomen.
- De meldingstekst noemt de windrichting voluit, plus de trend en de
  geschatte aankomsttijd als die bekend zijn.

### Opmerking

De blueprint blijft in de repo staan voor wie meer wil dan de ingebouwde
meldingen bieden, bijvoorbeeld eigen voorwaarden of een ander berichtformaat.
Gebruik ze niet allebei tegelijk, anders krijg je dubbele berichten.

## [0.3.0] — 2026-08-21

Herontwerp van het dashboard.

### Toegevoegd

- **Statusregel bovenaan** die de situatie samenvat: RUSTIG, ACTIEF, NADERT
  of ONWEER NABIJ. Kleur, icoon en toelichting volgen de ernst, zodat een
  rustige avond er anders uitziet dan een naderende cel.
- **Badges** bovenaan de view met afstand, aankomsttijd en chase-potentie.
  Die verschijnen alleen als er waarde in zit.
- Chase-potentie krijgt een tekstuele duiding naast het percentage.

### Gewijzigd

- Sensoren zonder waarde tonen een streepje in plaats van `unknown km`.
- Iconen worden grijs zolang een waarde nul of onbekend is; kleur betekent nu
  dat er daadwerkelijk iets aan de hand is.
- Het kompas verschijnt alleen als er een richting bekend is.
- De azimut-tegel toont de windrichting groot en de graden klein, in plaats
  van andersom.
- Naderingssnelheid staat nu tussen de kerncijfers in plaats van in een
  aparte rij.
- Cijfers gebruiken vaste breedte, zodat de layout niet meer verspringt bij
  elke update.
- Kleiner lettertype en strakkere afstanden in de labels.
- De kaarten in de rechterkolom zijn lager, zodat de kolom beter in beeld
  past.

## [0.2.3] — 2026-08-20

### Gerepareerd

- **CAPE-grafiek gaf een configuratiefout.** De grafiek definieerde twee
  y-assen, maar de CAPE-serie kreeg er geen toegewezen. Apexcharts-card eist
  dat elke serie aan een as hangt zodra er meer dan een as bestaat. Beide
  series krijgen nu expliciet een as.
- Is de chase-potentie niet beschikbaar, dan blijft er een enkele serie over
  en wordt de assen-definitie helemaal weggelaten in plaats van een
  ongebruikte tweede as te laten staan.

## [0.2.2] — 2026-08-20

### Gerepareerd

- **Dashboard gaf 'Timeout waiting for strategy element'.** Het script werd
  wel geserveerd, maar `add_extra_js_url` alleen bleek niet te garanderen
  dat de frontend het op tijd laadt. De integratie registreert het script nu
  ook als Lovelace-bron; die worden geladen op het moment dat een dashboard
  opstart, precies wanneer de strategie nodig is.
- Het script registreert zijn custom elements alleen nog als ze nog niet
  bestaan, zodat dubbel laden via beide routes geen fout meer geeft.

### Gewijzigd

- Bij een versie-update wordt de bestaande Lovelace-bron bijgewerkt met het
  nieuwe versienummer in plaats van dat er een tweede bij komt.
- `lovelace` toegevoegd als afhankelijkheid in het manifest.

### Opmerking

Draait Lovelace in YAML-modus, dan kan de integratie de bron niet zelf
aanmaken. Er verschijnt dan een regel in het logboek met de URL die je
handmatig moet toevoegen.

## [0.2.1] — 2026-08-20

### Gerepareerd

- `hacs.json` teruggebracht tot de velden die actuele HACS-versies kennen.
  `content_in_root` was al de standaardwaarde en `render_readme` is uit
  recente versies verdwenen; onbekende sleutels lieten de validatie
  struikelen met een onleesbare `[object Object]` melding.

### Toegevoegd

- Workflow die releases automatisch aanmaakt. Hoog het versienummer in
  `manifest.json` op, werk de changelog bij en push naar `main` — de tag,
  de release en de notities volgen vanzelf. De releasenotities worden uit
  de bijbehorende changelog-sectie gehaald.

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

[0.7.0]: https://github.com/Roedie84/StormchaseNL/releases/tag/v0.7.0
[0.6.0]: https://github.com/Roedie84/StormchaseNL/releases/tag/v0.6.0
[0.5.0]: https://github.com/Roedie84/StormchaseNL/releases/tag/v0.5.0
[0.4.0]: https://github.com/Roedie84/StormchaseNL/releases/tag/v0.4.0
[0.3.0]: https://github.com/Roedie84/StormchaseNL/releases/tag/v0.3.0
[0.2.3]: https://github.com/Roedie84/StormchaseNL/releases/tag/v0.2.3
[0.2.2]: https://github.com/Roedie84/StormchaseNL/releases/tag/v0.2.2
[0.2.1]: https://github.com/Roedie84/StormchaseNL/releases/tag/v0.2.1
[0.2.0]: https://github.com/Roedie84/StormchaseNL/releases/tag/v0.2.0
[0.1.0]: https://github.com/Roedie84/StormchaseNL/releases/tag/v0.1.0
