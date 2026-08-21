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
| `sensor.stormchase_afstand` | Afstand tot de dichtstbijzijnde inslag, herberekend vanaf je eigen positie. Attribuut `gemeten_via` toont of dat gelukt is. |
| `sensor.stormchase_azimut` | Richting van die inslag. |
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
| `sensor.stormchase_regen_begint_over` | Minuten tot de eerste regen. Draagt de volledige verwachting per 5 minuten als attribuut. |
| `sensor.stormchase_neerslagintensiteit` | Wat er nu valt, in mm/u. |
| `sensor.stormchase_neerslagpiek_2_uur` | Zwaarste bui in de komende twee uur. |
| `sensor.stormchase_actieve_locatie` | Welke locatie in gebruik is. Attributen: coordinaten, adres, en of Blitzortung vanaf hetzelfde punt meet. |

### Rotatie en hagel

`sensor.stormchase_rotatiekans` en `sensor.stormchase_hagelkans` geven een
score van 0 tot 100.

**Dit is geen detectie.** Of een bui daadwerkelijk roteert, stel je alleen
vast met dopplerradar; hagel vraagt dual-polarisatie. Die ruwe data is niet
vrij beschikbaar. Wat deze sensoren berekenen is of de atmosfeer rotatie en
hagel toelaat, uit CAPE, windschering en de hoogte van het vriesniveau. Voor
het echte beeld tijdens een bui blijf je aangewezen op iRadar of een andere
app met celdetectie.

De opbouw van beide scores staat in de attributen. `indices.py` bevat de
gebruikte drempels met uitleg erbij.

### Weer

`weather.stormchase` geeft de actuele omstandigheden en een verwachting per
uur en per dag op de actieve locatie, via Open-Meteo. Bruikbaar in elke
standaard weerkaart van Home Assistant.

### Waarschuwingen

`sensor.stormchase_waarschuwingsniveau` staat op groen, geel, oranje of rood.
De bron is MeteoAlarm, de Europese koepel waar nationale weerdiensten hun
waarschuwingen aan leveren, waaronder het KNMI. Daardoor werkt het ook buiten
Nederland.

Waarschuwingen worden gefilterd op je eigen omgeving. Bij de landbepaling
haalt de integratie ook de namen van je stad, streek en provincie op, en houdt
alleen de waarschuwingen over waarvan de gebiedsomschrijving daarop aansluit.
Zonder dat filter zou je alle waarschuwingen van een heel land krijgen.

Het land staat standaard op automatisch: de integratie zoekt op in welk land
je bent en haalt de bijbehorende feed op. Rijd je een grens over, dan
verschuiven de waarschuwingen mee. Handmatig kiezen kan ook. Het regioveld is een tekstfilter op de
gebiedsnaam uit de feed: vul bijvoorbeeld `Gelderland` in om alleen die
provincie te volgen, of laat het leeg voor het hele land.

Waarschuwingsmeldingen negeren de wachttijd en het stiltevenster, omdat ze
over gevaar gaan. Elke waarschuwing wordt maar een keer gemeld.

### Binary sensors

| Entiteit | Beschrijving |
|---|---|
| `binary_sensor.stormchase_onweer_nabij` | Aan binnen de ingestelde waarschuwingsafstand. |
| `binary_sensor.stormchase_onweer_nadert` | Aan bij structureel afnemende afstand. |
| `binary_sensor.stormchase_regen_verwacht` | Aan bij regen nu of binnen de ingestelde tijd. |
| `binary_sensor.stormchase_weerwaarschuwing` | Aan bij een actieve officiele waarschuwing. |

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

**Adressensor** is optioneel. Wijs hem naar de `geocoded_location` sensor van
de companion-app, dan staat je adres op het dashboard in plaats van
coordinaten. De config flow raadt hem meestal goed.

**Patroon in geo_location entity-id** bepaalt welke markers meetellen voor de
afstandsringen. Standaard `lightning_strike`.

Maakt jouw Blitzortung-integratie geen `geo_location` entiteiten aan, dan
telt de integratie zelf de sprongen van de afstandssensor binnen het
ingestelde tijdvenster. Het attribuut `telling_via` op elke ringsensor laat
zien welke van de twee actief is. `geo_location` is nauwkeuriger, want dat
kent alle inslagen; de terugval ziet alleen de dichtstbijzijnde per moment.

Alle instellingen zijn achteraf aan te passen via de knop *Configureren* bij
de integratie. Wijzigingen worden direct doorgevoerd.

## Locatie

Alles wat de integratie ophaalt hangt aan één locatie-instelling: het
weerbericht, de onweersparameters, de neerslagverwachting, de kaarten op het
dashboard en sinds 0.7.0 ook het land voor de waarschuwingen.

Wat er **niet** aan hangt: de afstand tot de blikseminslagen. Die komt van de
Blitzortung-integratie, en die heeft zijn eigen locatie-instelling. Zorg dat
je daar dezelfde bron kiest.

Maakt die integratie `geo_location` entiteiten aan, dan herberekent
Stormchase de afstand en richting van elke inslag vanaf jouw positie. Het
vaste punt van Blitzortung doet er dan niet meer toe. Het attribuut
`afstand_via` laat zien of dat lukt.

Die integratie toont haar positie niet als entiteit, dus Stormchase leest de
instellingen uit en vergelijkt ze. Het attribuut `afwijking_km` op
`sensor.stormchase_actieve_locatie` laat zien hoe ver de twee uit elkaar
liggen; boven de vijf kilometer verschijnt er een waarschuwing op het
dashboard.

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

De integratie stuurt de meldingen zelf. Bij het instellen kies je een of meer
notify-diensten; daarna komen de berichten binnen zonder dat er een
automatisering aan te pas komt.

| Instelling | Betekenis |
|---|---|
| Meldingsdiensten | Leeg laten zet de meldingen uit. |
| Alleen melden binnen | Verder weg dan dit levert geen bericht op. |
| Ook bij nadering | Een vroeger bericht zodra de afstand structureel afneemt. |
| Melden als het over is | Sein veilig zodra het onweer is weggetrokken. |
| Wachttijd | Voorkomt herhaling bij een grillige cel. |
| Stiltevenster | Twee gelijke tijden betekent: altijd melden. |
| Ook bij regen | Bericht zodra er neerslag aankomt. |
| Ook bij wind | Bericht bij windstoten boven de drempel, standaard 60 km/u. |
| Alleen ter plaatse | Regen- en windmeldingen wachten tot je ergens bent. |
| Onderweg vanaf snelheid | Boven deze snelheid ben je onderweg, standaard 30 km/u. |
| Zo lang trager | Hoe lang je onder die drempel moet blijven voor je weer als ter plaatse telt. |
| Minuten vooruit | Hoe ver van tevoren, standaard tien minuten. |
| Vanaf intensiteit | Onder deze waarde heet het droog, zodat motregen geen bericht oplevert. |

### Onderweg of ter plaatse

`binary_sensor.stormchase_onderweg` staat aan zolang je sneller beweegt dan
de ingestelde drempel, standaard 30 km/u. Je telt pas weer als ter plaatse
zodra je die snelheid tien minuten lang niet meer gehaald hebt.

Snelheid en niet afstand, want stilstaan in de file gebeurt binnen een straal
van nul meter terwijl je wel degelijk onderweg bent, en een wandelaar legt in
tien minuten makkelijk een kilometer af. Wandelen en fietsen tellen dus als
ter plaatse.

Geeft je tracker zelf een snelheid door, zoals de companion-app doet, dan
wordt die gebruikt; anders wordt hij afgeleid uit de locatiepunten van de
laatste drie minuten.

Meldingen over regen en wind wachten daarop, want tijdens het rijden is een
bericht over het weer hier alweer achterhaald voor je het leest. Onweer
binnen de waarschuwingsafstand en officiele waarschuwingen komen wel altijd
door: die gaan over gevaar.

### Neerslag

De verwachting komt van de neerslagtekst van Buienradar: per vijf minuten,
twee uur vooruit, op exacte coordinaten. Dat is nauwkeuriger dan een
uurverwachting en precies wat je nodig hebt voor "over tien minuten regen".

Buiten het radarbereik van Buienradar, dus in de praktijk buiten Nederland en
de directe omgeving, schakelt de integratie automatisch over op de
kwartierwaarden van Open-Meteo. Grover, maar overal beschikbaar. Welke bron
actief is staat in het attribuut `bron` van
`sensor.stormchase_regen_begint_over`.

`switch.stormchase_meldingen` zet ze tijdelijk uit zonder de instellingen aan
te raken. De service `stormchase.test_notification` stuurt een proefbericht
langs alle drempels heen, om te controleren of het aankomt.

### Events

Wil je meer dan de ingebouwde meldingen bieden, dan kun je zelf op de events
reageren:

| Event | Wanneer |
|---|---|
| `stormchase_nearby` | De afstand komt binnen de waarschuwingsafstand. |
| `stormchase_approaching` | De afstand neemt structureel af. |
| `stormchase_cleared` | De afstand is weer boven anderhalf keer de waarschuwingsafstand. |
| `stormchase_rain_incoming` | Er komt regen aan binnen de ingestelde tijd. |
| `stormchase_alert` | Nieuwe officiele weerwaarschuwing. |

Events vuren bij een *overgang*, niet bij elke update. Je krijgt dus één
melding per onweersgebied in plaats van bij elke inslag opnieuw.

Elk event draagt dezelfde gegevens: `afstand`, `azimut`, `snelheid`,
`aankomst_minuten`, `trend`, `inslagen` (per ring) en `locatie_bron`.

### Blueprint

`blueprints/automation/stormchase/onweersmelding.yaml` doet hetzelfde als de
ingebouwde meldingen, maar dan als automatisering die je zelf kunt uitbreiden
met eigen voorwaarden. Alleen nodig als de ingebouwde variant tekortschiet.

**Gebruik ze niet allebei tegelijk**, anders krijg je elk bericht dubbel.

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
  map_ratio: "120%"                  # anders automatisch per schermbreedte
  alle_waarden: false                # laat het vangnet-blok weg
  maps:
    iradar: true
    blitzortung: true
    buienradar: true
    windy: false
```

De kaarten passen hun verhouding aan de schermbreedte aan: op een telefoon
staand, op een breed scherm liggend. Met `map_ratio` zet je dat vast.

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

## Diagnostiek

Bij een probleem: ga naar Instellingen → Apparaten & Diensten → Stormchase →
driepuntsmenu → **Diagnostische gegevens downloaden**. Dat bestand bevat alles
wat nodig is om mee te kijken.

Wat erin zit: de instellingen, de actuele waarden, per bron het aantal
geslaagde en mislukte ophaalrondes met de laatste foutmelding, welke
neerslagbron gebruikt is, hoeveel events en meldingen er zijn geweest, en de
laatste zestig afstandsmetingen met de berekende naderingssnelheid.

Coordinaten staan afgerond tot ongeveer een kilometer. De gevolgde
device_tracker, handmatige coordinaten en de namen van je meldingsdiensten
worden weggelaten.

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
