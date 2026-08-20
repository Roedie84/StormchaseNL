# StormchaseNL

Een Home Assistant integratie die een afgeleide laag bouwt bovenop een
bestaande [Blitzortung](https://github.com/mrk-its/homeassistant-blitzortung)
integratie: naderingssnelheid, geschatte aankomsttijd, afstandsringen en
onweersparameters uit Open-Meteo.

De locatie komt uit je Home Assistant configuratie. Er hoeven geen
coördinaten of API-sleutels ingevuld te worden.

## Waarom geen eigen bliksemdetectie

De Blitzortung-integratie praat al via MQTT met de servers van
blitzortung.org. Die verbinding nog een keer opzetten levert alleen een
tweede afhankelijkheid en meer onderhoud op. Stormchase leest de bestaande
sensoren uit en rekent daar bovenop.

## Wat je krijgt

### Sensoren

| Entiteit | Beschrijving |
|---|---|
| `sensor.stormchase_naderingssnelheid` | km/u, **positief = komt dichterbij**. Lineaire regressie over 15 minuten, niet eerste-tegen-laatste, omdat losse inslagen flink springen. |
| `sensor.stormchase_aankomst` | Geschatte minuten tot aankomst. Niet beschikbaar als het onweer niet nadert. |
| `sensor.stormchase_trend` | `nadert snel` · `nadert` · `stabiel` · `trekt weg` · `trekt snel weg` |
| `sensor.stormchase_inslagen_binnen_X_km` | Drie ringen, standaard 10 / 25 / 50 km. |
| `sensor.stormchase_actieve_markers` | Totaal aantal actieve `geo_location` markers. |
| `sensor.stormchase_cape` | Beschikbare energie voor opstijgende lucht (J/kg). |
| `sensor.stormchase_cape_piek_12_uur` | Hoogste CAPE in de komende 12 uur. |
| `sensor.stormchase_lifted_index` | Stabiliteit; negatief is onstabiel. |
| `sensor.stormchase_convectieve_remming` | CIN, de deksel op de atmosfeer. |
| `sensor.stormchase_chase_potentie` | Score 0-100. Zie hieronder. |
| `sensor.stormchase_actieve_locatie` | Diagnostisch: welke locatie nu gebruikt wordt, met de coördinaten als attribuut. |

### Binary sensors

| Entiteit | Beschrijving |
|---|---|
| `binary_sensor.stormchase_onweer_nabij` | Aan binnen de ingestelde waarschuwingsafstand. |
| `binary_sensor.stormchase_onweer_nadert` | Aan bij structureel afnemende afstand. |

Beide hebben attributen met afstand, azimut, snelheid en aankomsttijd, zodat
je automatiseringen niet meerdere entiteiten hoeven uit te lezen.

### Over de chase potentie

Een hulpmiddel, geen verwachting. De opbouw staat in de attributen:

- CAPE-piek levert maximaal 50 punten (schaal tot 2500 J/kg)
- Lifted Index levert maximaal 30 punten (schaal tot -8)
- Inslagen in de buitenste ring leveren maximaal 20 punten

Een hoge score betekent dat de ingrediënten aanwezig zijn, niet dat er
daadwerkelijk iets gebeurt. Convectieve remming kan alles tegenhouden.
Gebruik het als eerste signaal, niet als beslissing.

## Installatie

### Via HACS

1. HACS → Integraties → menu rechtsboven → Aangepaste repositories
2. Voeg `https://github.com/Roedie84/StormchaseNL` toe als categorie *Integratie*
3. Installeer Stormchase en herstart Home Assistant
4. Instellingen → Apparaten & Diensten → Integratie toevoegen → Stormchase

### Handmatig

Kopieer `custom_components/stormchase` naar je `config/custom_components/`
map en herstart.

## Instellen

De config flow raadt je Blitzortung-sensoren op basis van hun achtervoegsel
(`_lightning_distance`, `_lightning_azimuth`, `_lightning_counter`). Klopt de
gok niet, kies ze dan handmatig.

**Patroon in geo_location entity-id** bepaalt welke markers meetellen voor de
afstandsringen. Standaard `lightning_strike`. Staan je ringen op 0 terwijl er
wel onweer is, kijk dan onder Ontwikkelhulpmiddelen → Statussen met filter
`geo_location.` welk patroon jouw entiteiten hebben.

Alle instellingen zijn achteraf aan te passen via de knop *Configureren* bij
de integratie. Wijzigingen worden direct doorgevoerd.

## Locatie

Standaard gebruikt de integratie de thuislocatie uit je Home Assistant
configuratie. Bij het instellen kun je kiezen uit vier bronnen:

| Modus | Wanneer |
|---|---|
| **Thuislocatie** | Standaard. Verhuis je, dan verhuist de integratie mee. |
| **Een zone** | Bijvoorbeeld een vakantiehuis dat je als zone hebt aangemaakt. |
| **Volg een apparaat of persoon** | Kiest de GPS-positie van je telefoon of `person`-entiteit. Op vakantie krijg je de onweersparameters van waar je op dat moment bent. |
| **Handmatige coördinaten** | Prik een punt op de kaart. |

Ontbreekt bij een zone of tracker de GPS-positie, dan valt de integratie
terug op je thuislocatie. Liever weerdata van thuis dan helemaal niets.

Verplaats je meer dan 15 km, dan worden de weerparameters direct opnieuw
opgehaald in plaats van te wachten op het volgende halfuur.

**Let op:** dit verandert alleen waar de *weerparameters* vandaan komen. De
afstand tot de blikseminslagen komt van de Blitzortung-integratie, en die
heeft zijn eigen locatie-instelling. Neem je die mee op reis, pas hem dan
daar ook aan.

## Meldingen

De integratie stuurt zelf geen berichten, maar vuurt events af waar je
automatiseringen op kunt bouwen:

| Event | Wanneer |
|---|---|
| `stormchase_nearby` | De afstand komt binnen de waarschuwingsafstand. |
| `stormchase_approaching` | De afstand neemt structureel af. |
| `stormchase_cleared` | De afstand is weer boven anderhalf keer de waarschuwingsafstand. |

Events vuren bij een *overgang*, niet bij elke update. Je krijgt dus één
melding per onweersgebied in plaats van bij elke inslag opnieuw.

Elk event draagt dezelfde gegevens: `afstand`, `azimut`, `snelheid`,
`aankomst_minuten`, `trend`, `inslagen` (per ring) en `locatie_bron`.

### Blueprint

`blueprints/automation/stormchase/onweersmelding.yaml` bevat een kant-en-klare
automatisering. Kopieer het bestand naar `config/blueprints/automation/` en
maak er een automatisering van, of importeer hem via de URL.

Instelbaar: de notify-service, maximale afstand, of je ook bij nadering wil
melden, een wachttijd tegen herhaling, een optioneel stiltevenster en extra
voorwaarden. De titel is vrij in te vullen, dus Achterhoeks mag.

## Dashboard

Vereist via HACS: `card-mod`, `mushroom`, `apexcharts-card`, `compass-card`.

### Aanbevolen: de strategie

De integratie levert een dashboardstrategie mee die de view bij elke
paginalading opnieuw opbouwt uit de entiteiten die op dat moment bestaan.
Komt er bij een update een sensor bij, dan verschijnt de tegel vanzelf — je
hoeft niets over te typen.

Maak een nieuw dashboard aan, open de onbewerkte configuratie-editor en zet
er dit in:

```yaml
strategy:
  type: custom:stormchase
```

Dat is alles — de integratie registreert het benodigde script zelf als
Lovelace-bron.

Krijg je toch *Timeout waiting for strategy element*, dan draait Lovelace
waarschijnlijk in YAML-modus en moet je de bron handmatig toevoegen onder
Instellingen → Dashboards → Bronnen: URL `/stormchase/stormchase-strategy.js`,
type JavaScript-module. Ververs daarna één keer hard met Ctrl+Shift+R.

Wil je alleen een losse view binnen een bestaand dashboard:

```yaml
views:
  - strategy:
      type: custom:stormchase
    title: Stormchase
```

De strategie past zich aan je installatie aan: ringtegels verschijnen voor
elke ring die je hebt ingesteld, hoeveel het er ook zijn. Ontbreken de
Open-Meteo-waarden, dan blijft die sectie weg in plaats van lege tegels te
tonen. De locatietegel verschijnt alleen als je niet thuis bent, en de
kaarten centreren op je actieve locatie in plaats van op je thuisadres.

Opties, allemaal optioneel:

```yaml
strategy:
  type: custom:stormchase
  title: Onweer                      # kop van de view
  distance_entity: sensor.x          # anders automatisch gedetecteerd
  azimuth_entity: sensor.y
  counter_entity: sensor.z
  latitude: 52.10                    # anders de actieve locatie
  longitude: 6.63
  iradar_url: https://iradar.app/... # je eigen embed-URL
  maps:
    iradar: true
    blitzortung: true
    buienradar: true
    windy: false
```

### Alternatief: statische YAML

`dashboards/stormchase.yaml` bevat dezelfde view als gewone YAML, voor als je
liever zelf aan de kaarten sleutelt. Nadeel: die moet je bij elke update van
de integratie handmatig bijwerken.

De iframes staan daar op vaste coördinaten die je moet aanpassen. Voor iRadar
genereer je een eigen embed-URL via Menu → Functies → Insluiten op pagina; zet
daar ook de ESTOFEX-laag aan voor de onweersverwachting over je radarbeeld.

## Voorbeeldautomatisering

```yaml
- alias: Onweer nadert
  mode: single
  trigger:
    - platform: state
      entity_id: binary_sensor.stormchase_onweer_nadert
      to: "on"
  condition:
    - condition: numeric_state
      entity_id: sensor.onweer_detectie_lightning_distance
      below: 30
  action:
    - service: notify.mobile_app_telefoon
      data:
        title: "⚡ Onweer op komst"
        message: >-
          {{ states('sensor.onweer_detectie_lightning_distance') }} km,
          {{ states('sensor.stormchase_trend') }}
          {%- if has_value('sensor.stormchase_aankomst') %},
          hier over ongeveer {{ states('sensor.stormchase_aankomst') }} minuten
          {%- endif %}.
```

## Beperkingen

- De naderingssnelheid is gebaseerd op de *laatste* inslag, niet op een
  gevolgde cel. Bij twee onweersgebieden tegelijk springt de afstand tussen
  beide en wordt de trend onbetrouwbaar. iRadar's celdetectie is daar beter
  in; deze integratie vervangt dat niet.
- De aankomsttijd gaat uit van een rechte lijn en constante snelheid. Cellen
  buigen af en bouwen op of vallen uit.
- Open-Meteo levert modelwaarden per uur, geen metingen.
- De locatie-instelling geldt alleen voor de weerparameters, niet voor de
  bliksemdetectie zelf.

## Nieuwe versie uitbrengen

Releases worden automatisch aangemaakt. De workflow in
`.github/workflows/release.yml` kijkt bij elke push naar `main` of de versie
in `manifest.json` al een tag heeft. Zo niet, dan maakt hij die aan, publiceert
een release en hangt er een zip van de integratie aan.

De releasenotities komen uit `CHANGELOG.md`: de workflow pakt het blok tussen
de kop van die versie en de volgende. Dus:

1. Hoog `version` op in `custom_components/stormchase/manifest.json`
2. Voeg een `## [x.y.z] — datum` sectie toe bovenaan `CHANGELOG.md`
3. Push naar `main`

Meer is het niet. Vergeet je de changelog-sectie, dan komt er een release met
een verwijzing naar het bestand in plaats van notities — vervelend, maar niet
kapot.

## Licentie

MIT

## Iconen en logo

Entity-iconen zitten in `custom_components/stormchase/icons.json` en lopen via
de translation keys. De binary sensors wisselen van icoon op basis van hun
status: `mdi:flash-alert` bij onweer nabij, `mdi:arrow-down-bold` bij nadering.

Het integratielogo staat in `brands/`. Home Assistant haalt logo's **niet** uit
je eigen repo — die komen uit
[home-assistant/brands](https://github.com/home-assistant/brands). Zonder die
stap krijgt de integratie het standaard puzzelstukje.

Om het logo zichtbaar te maken:

1. Fork `home-assistant/brands`
2. Maak `custom_integrations/stormchase/` aan
3. Kopieer daarin `icon.png` (256×256) en `icon@2x.png` (512×512) uit `brands/`
4. Optioneel `logo.png` en `logo@2x.png` voor de bredere weergave
5. Open een pull request

De bestanden voldoen aan de eisen: PNG met transparantie, vierkant voor het
icoon, en de `@2x` varianten precies op dubbele resolutie. `icon.svg` en
`logo.svg` zitten erbij als bron, mocht je willen bijstellen.
