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
| `sensor.stormchase_naderingssnelheid` | km/u, **positief = komt dichterbij**. Lineaire regressie over 15 minuten, niet eerste-tegen-laatste, omdat losse inslagen flink springen. Alleen nieuwe inslagafstanden tellen (minstens 3 in het venster); zonder nieuwe inslag blijft de waarde staan en vervalt ze zodra er te weinig metingen in het venster over zijn. |
| `sensor.stormchase_aankomst` | Geschatte minuten tot aankomst. Niet beschikbaar als het onweer niet nadert. |
| `sensor.stormchase_trend` | `nadert snel` · `nadert` · `stabiel` · `trekt weg` · `trekt snel weg` |
| `sensor.stormchase_inslagen_binnen_X_km` | Drie ringen, standaard 10 / 25 / 50 km. |
| `sensor.stormchase_actieve_markers` | Totaal aantal actieve `geo_location` markers. |
| `sensor.stormchase_cape` | Beschikbare energie voor opstijgende lucht (J/kg). |
| `sensor.stormchase_cape_piek_12_uur` | Hoogste CAPE in de komende 12 uur. |
| `sensor.stormchase_lifted_index` | Stabiliteit; negatief is onstabiel. |
| `sensor.stormchase_convectieve_remming` | CIN, de deksel op de atmosfeer. |
| `sensor.stormchase_chase_potentie` | Score 0-100. Zie hieronder. |
| `sensor.stormchase_windstoten` | Verwachte windstoot in km/u (Open-Meteo), bijgesteld met de mediane verhouding gemeten/model van het dichtstbijzijnde station over 24 uur (factor 0,5-1,3; vanaf 6 metingen over een uur). Attributen `model`, `correctiefactor`, `gecorrigeerd`, `paren_24u`. De windmelding gebruikt de bijgestelde waarde. |
| `sensor.stormchase_regen_begint_over` | Minuten tot de eerste regen. Regent het al, dan het begin van de volgende bui na het droge stuk (attribuut `volgende_bui: true`), anders onbekend. Draagt de volledige verwachting per 5 minuten als attribuut. |
| `sensor.stormchase_regen_stopt_over` | Minuten tot de bui van nu ophoudt; onbekend als het droog is. |
| `sensor.stormchase_regenbeeld` | Het regenbeeld in één zin, bijvoorbeeld "Regent nu, zwaar (13,7 mm/u), droog over 47 min; volgende bui over 82 min (licht, tot 1,6 mm/u)." |
| `sensor.stormchase_neerslagintensiteit` | Wat er nu valt, in mm/u. |
| `sensor.stormchase_neerslagpiek_2_uur` | Zwaarste bui in de komende twee uur. |
| `sensor.stormchase_actieve_locatie` | Welke locatie in gebruik is. Attributen: coordinaten, adres, en of Blitzortung vanaf hetzelfde punt meet. |

### Onweersverwachting

`sensor.stormchase_onweersverwachting` zet de losse parameters om in een
oordeel: geen onweer verwacht, kleine kans, kans op onweer, kans op zwaar
onweer of kans op noodweer. De attributen bevatten de duiding per onderdeel
en een toelichting waarom het oordeel zo uitvalt.

Het gaat om de combinatie. CAPE van 2500 bij stabiele lucht levert niets op,
en veel energie zonder windschering hooguit een losse bui die zichzelf binnen
een uur opruimt. `indices.py` bevat de gebruikte drempels met uitleg.

### Radar op je eigen positie

`image.stormchase_radar` toont het meest recente radarbeeld, gecentreerd op de
locatie die de integratie gebruikt. Geen ingesloten webpagina, dus geen
cookiemelding en geen advertenties, en het schuift mee als je onderweg bent.

Op het beeld liggen vier lagen over elkaar: de kaart, de bewolking uit
infrarood, de neerslag, en daarbovenop de gevolgde onweerscellen.

Elke cel krijgt een ring, gekleurd naar activiteit: geel voor een gewone bui,
oranje vanaf acht inslagen, rood vanaf vijfentwintig. De ring groeit mee met
het aantal inslagen. De lijn vooruit is de koers voor het komende uur, met een
streepje per kwartier, zodat je de aankomsttijd direct afleest.

Verder staan er de blikseminslagen van het laatste kwartier: vers is
fel wit, ouder dooft uit naar oranje. Daarmee zie je welke kant de activiteit
op schuift. Je eigen positie is de witte ring in het midden.

Het zoomniveau is instelbaar van 1 tot 7, de verversing van dertig seconden
tot tien minuten.

Voor de radar zijn er twee bronnen. RainViewer werkt wereldwijd en is de
standaard. De Duitse weerdienst is actueler maar dekt Duitsland en de directe
omgeving; die is te kiezen met de instelling Radarbron. Komt er niets terug,
dan valt hij terug op RainViewer.

Kaart van OpenStreetMap, bewolking van EUMETSAT.

### Metingen naast voorspellingen

`sensor.stormchase_meting` geeft de waarneming van het dichtstbijzijnde
weerstation via Bright Sky, de open API op de data van de Duitse weerdienst.
Gratis en zonder sleutel, met de stationsnaam en afstand als attribuut. In
Nederland, met een EDR-sleutel, komen de metingen van de KNMI-stations (zie
[KNMI-bronnen](#knmi-bronnen-nederland)).

Alles wat de integratie verder toont is voorspeld. Deze waarde is gemeten, en
het verschil ertussen zegt of je de verwachting van vandaag kunt vertrouwen.

### Als een bron eruit ligt

De laatst bekende waarden blijven staan met het aantal minuten ouderdom
erbij, tot drie uur. Daarboven wordt de sensor alsnog onbeschikbaar, want dan
is leeg eerlijker dan verkeerd. `sensor.stormchase_bronstatus` laat zien welke
bron hapert, en op het dashboard verschijnt een tegel zodra dat gebeurt.

Een mislukte bron wordt niet pas na het hele interval opnieuw geprobeerd,
maar na 2 en daarna 5 minuten; lukt dat niet, dan weer volgens het gewone
interval. Meldt een bron "te veel verzoeken" (429), dan komt er geen
vervroegde poging. Per bron staat `volgende_poging` in de bronstatus.

Elke bron staat los van de andere: valt Buienradar weg, dan werken de
onweersparameters en de waarschuwingen gewoon door.

### Onweerskans uit het ensemble

`sensor.stormchase_onweerskans_ensemble` geeft het percentage ensembleleden
dat boven de onweersdrempel uitkomt, met de kans op zwaar weer als attribuut.

Een ensemble draait hetzelfde model meerdere keren met licht verschillende
beginwaarden. Dat is een ander soort getal dan een mediaan: een mediaan van
1200 J/kg ziet eruit als een prima dag, maar als veertig procent van de leden
onder de drempel zit weet je dat het alle kanten op kan.

### Modelovereenstemming

`sensor.stormchase_modelovereenstemming` vraagt dezelfde grootheid bij acht
modellen op en zegt of ze het eens zijn. Dat verandert wat een getal waard is:
2000 J/kg waar zes modellen het over eens zijn is iets anders dan 2000 J/kg
als mediaan van een reeks die van 200 tot 2600 loopt.

De attributen bevatten de mediaan, het bereik en de waarde per model.

### Wat het model zelf meldt

`sensor.stormchase_bliksempotentie`, `_opwaartse_stroming` en `_wolkentop`
komen uit ICON-D2, het enige model dat die velden publiceert. Ze wegen
zwaarder dan de afgeleide kansen hieronder: het zijn uitkomsten van het
weermodel, geen combinaties die ik zelf maak.

Alleen beschikbaar in Midden-Europa. Daarbuiten blijven ze leeg en vallen de
verwachtingen terug op CAPE, stabiliteit en schering.

`sensor.stormchase_draaiing_met_hoogte` zegt of de wind met de hoogte
rechtsom of linksom draait. Rechtsdraaiend hoort bij een omgeving waarin
supercellen zich kunnen organiseren. Dat is de kern van een hodograaf, zonder
dat je hem hoeft te kunnen lezen.

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
uur en per dag op de actieve locatie, via Open-Meteo; in Nederland sinds
0.49.0 conditie, temperatuur, wind en verwachting van het KNMI (attribuut
`verwachting_bron`). Bruikbaar in elke
standaard weerkaart van Home Assistant.

Sinds 0.48.0 volgt de huidige conditie de radar als het nu regent: vanaf
0,1 mm/u wordt het `rainy`, vanaf 4 mm/u `pouring`, en met onweer binnen de
waarschuwingsafstand `lightning-rainy`. Droog volgens de radar, of is de
radarwaarde ouder dan een kwartier, dan blijft de conditie van Open-Meteo
staan (ook `clear-night`). Sneeuw of hagel van het model blijft staan. De
verwachting per uur en per dag komt onveranderd van Open-Meteo.

### Waarschuwingen

`sensor.stormchase_waarschuwingsniveau` staat op groen, geel, oranje of rood.
In Nederland komen de waarschuwingen sinds 0.49.0 rechtstreeks van het KNMI
(zie [KNMI-bronnen](#knmi-bronnen-nederland)). Daarbuiten, en als terugval, is
de bron MeteoAlarm, de Europese koepel waar nationale weerdiensten hun
waarschuwingen aan leveren. Daardoor werkt het ook buiten Nederland.

Waarschuwingen worden gefilterd op je eigen omgeving. Bij de landbepaling
haalt de integratie ook de namen van je stad, streek en provincie op, en houdt
alleen de waarschuwingen over waarvan de gebiedsomschrijving daarop aansluit.
Zonder dat filter zou je alle waarschuwingen van een heel land krijgen.

Het land staat standaard op automatisch: de integratie zoekt op in welk land
je bent en haalt de bijbehorende feed op. Rijd je een grens over, dan
verschuiven de waarschuwingen mee. Handmatig kiezen kan ook. Het regioveld is een tekstfilter op de
gebiedsnaam uit de feed: vul bijvoorbeeld `Gelderland` in om alleen die
provincie te volgen, of laat het leeg voor het hele land.

Zie je in een weerapp een waarschuwing die hier ontbreekt, kijk dan naar het
attribuut `gefilterd_op` van `sensor.stormchase_waarschuwingsniveau`. Staat de
naam van jouw gebied daar niet bij, vul het regioveld dan handmatig in; dat
gaat voor op de automatische namen. Het dashboard toont een grijze tegel zodra
er waarschuwingen in het land zijn die buiten je filter vallen.

Het soort waarschuwing wordt vertaald naar het Nederlands. MeteoAlarm levert
dat als vrije Engelse tekst die per land verschilt, dus de herkenning gaat op
trefwoord; `taal.py` bevat de lijst. Onbekende termen blijven zoals ze zijn.

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

## KNMI-bronnen (Nederland)

Sinds 0.49.0 gebruikt Stormchase in Nederland de officiële bronnen van het
KNMI, aanvullend op wat er al was. Buiten Nederland (Duitsland, België),
zonder sleutel of bij een storing valt alles automatisch terug op de
bestaande bronnen; er verandert dan niets.

| Onderdeel | In Nederland | Terugval / buiten NL | Sleutel |
|---|---|---|---|
| Waarschuwingen | KNMI-app: code geel/oranje/rood per waarschuwingsregio, met niveau per uur | MeteoAlarm | geen |
| Neerslag per 5 minuten | KNMI-app, per radarcel van 1 km² | Buienradar, daarna Open-Meteo | geen |
| Weersverwachting (`weather.stormchase`) | KNMI-app: conditie, uur- en dagverwachting, windstoten, neerslagkans | Open-Meteo | geen |
| Waarnemingen | KNMI-stations (EDR), per grootheid het dichtstbijzijnde station | Bright Sky | EDR-sleutel |
| Radarkaart en vooruitblik | KNMI-radar (WMS): actueel en tot twee uur vooruit | RainViewer of DWD | WMS-sleutel |
| Snellere verversing | Pushmeldingen (MQTT) bij nieuwe waarnemingen en radar | elke 10 minuten (waarnemingen) en 5 minuten (radar) pollen | Notification Service-sleutel |

CAPE, Lifted Index, windschering en het ensemble blijven van Open-Meteo.

### Sleutels aanmaken

De drie sleutels zijn gratis bij het
[KNMI Data Platform](https://dataplatform.knmi.nl):

1. Maak een account aan via het
   [Developer Portal](https://developer.dataplatform.knmi.nl/register).
2. Vraag in de [API Catalog](https://developer.dataplatform.knmi.nl/apis) een
   sleutel aan voor de **EDR API**, de **Web Map Service (WMS)** en de
   **Notification Service**.
3. Vul ze in via Instellingen → Apparaten & diensten → StormchaseNL →
   Configureren, laatste stap **KNMI (optioneel)**:
   - *KNMI WMS-sleutel (radarkaart)*
   - *KNMI Notification Service-sleutel*
   - *KNMI EDR-sleutel (waarnemingen)*
   - *Radarstijl KNMI* (donker of licht)

Elke sleutel is los te gebruiken; laat een veld leeg om die functie uit te
zetten. De sleutels worden niet gelogd, staan niet in attributen en worden
weggelaten uit het diagnosebestand.

### Waarschuwingsregio

De regio (1 tot 15, zoals in de KNMI-app) volgt de actieve locatie, dus ook
de live tracker. Hij komt uit de omgekeerde geocodering die de integratie al
deed: de provincie, de Waddeneilanden (Texel, Vlieland, Terschelling, Ameland,
Schiermonnikoog) als eigen regio, en IJsselmeer of Waddenzee op het water.
Lukt dat niet, dan geldt de regio met het dichtstbijzijnde middelpunt. Een
ingevuld regiofilter dat een KNMI-regio noemt (bijvoorbeeld `Gelderland`),
gaat voor. De attributen `bron`, `regio` en `niveau_per_uur` (komende 24 uur)
staan op `sensor.stormchase_waarschuwingsniveau`.

### Nieuwe entiteiten

| Entiteit | Beschrijving |
|---|---|
| `sensor.stormchase_windstoten_gemeten` | Gemeten windstoot in km/u, met m/s, Beaufort, station en afstand als attribuut. |
| `sensor.stormchase_luchtdruk_gemeten` | Gemeten luchtdruk (hPa). |
| `sensor.stormchase_luchtdrukverandering_per_uur` | Druk nu min druk een uur geleden (hPa, negatief is dalend), met `druk_tendens_1u`. |
| `sensor.stormchase_luchtdrukverandering_per_3_uur` | Idem over drie uur. |
| `binary_sensor.stormchase_onweer_gemeten_bij_station` | Onweer volgens de weercode van het dichtstbijzijnde KNMI-station met weersensor (WMO 4680: 12, 90-96), met `onweer_afgelopen_uur` (26). |
| `binary_sensor.stormchase_hagel_gemeten_bij_station` | Hagel volgens de weercode (89, 93, 96). |
| `image.stormchase_radar_vooruitblik` | Geanimeerde KNMI-radar van een uur terug tot twee uur vooruit, per tien minuten (alleen met WMS-sleutel). |

De drukverandering houdt de integratie zelf bij, per station, en overleeft
een herstart; ze werkt ook met Bright Sky. Onweer en hagel bij het station
blijven onbekend zonder KNMI-waarnemingen.

`sensor.stormchase_bronstatus` toont de nieuwe bronnen (`knmi_waarschuwingen`,
`knmi_verwachting`, `knmi_nowcast`, `knmi_edr`, `knmi_wms`) en onder `knmi`
welke sleutels er zijn, de status van de pushverbinding en welke KNMI-bron
tijdelijk is afgeremd na een fout. Na een storing wacht een KNMI-bron 2 tot
30 minuten, na een 429 minstens 10 minuten (of de Retry-After), na een
geweigerde sleutel een uur; intussen werkt de terugval.

### Radar

Met een WMS-sleutel staat in Nederland de KNMI-radar op
`image.stormchase_radar`: één kaartverzoek voor het hele beeld, rechtstreeks in
webmercator, over dezelfde kaart, wolken, cellen en inslagen. Lukt dat niet,
dan de ingestelde radarbron (RainViewer of DWD). Het attribuut `radarbron`
zegt welke er op het beeld staat.

De vooruitblik wordt alleen bijgewerkt als iemand er de afgelopen kwartier
naar keek. Frames worden bewaard; bij een nieuwe radarronde komen alleen het
nieuwe beeld en de verwachting erbij (13 verzoeken), nooit meer dan vijf per
seconde.

### Bronvermelding

Gegevens van het KNMI vallen onder [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/);
de weerentiteit noemt het KNMI in de bronvermelding. De opbouw van de
verzoeken aan de KNMI-API's is gebaseerd op
[ha-nl-weather](https://github.com/PaulVanSchayck/ha-nl-weather) van Paul van
Schayck (Apache-2.0); de code in Stormchase is eigen werk. De rasterdefinities
komen uit de open source KNMI-app (KNMI-OSS).

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
| Vooruitzicht | Bericht zodra de verwachting opschaalt naar zwaar onweer of noodweer. |
| Weersituaties | Sneeuw, ijzel, mist, hitte en vorst, per stuk aan of uit. |
| Hitte vanaf | Standaard 30 graden. |
| Vorst vanaf | Standaard 0 graden. |
| Ook bij wind | Bericht bij windstoten boven de drempel, standaard 60 km/u. |
| Alleen ter plaatse | Regen- en windmeldingen wachten tot je ergens bent. |
| Onderweg vanaf snelheid | Boven deze snelheid ben je onderweg, standaard 30 km/u. |
| Zo lang trager | Hoe lang je onder die drempel moet blijven voor je weer als ter plaatse telt. |
| Minuten vooruit | Hoe ver van tevoren, standaard tien minuten. |
| Vanaf intensiteit | Onder deze waarde heet het droog, zodat motregen geen bericht oplevert. |

### Dagelijks weerbericht

Standaard om 07:00 en 13:00 een samenvatting: waarschuwingen, het weer nu, de
verwachting voor vandaag, de neerslag voor de komende twee uur en onweer of de
kans daarop.

```
Waarschuwing code oranje voor heavy rain in Trier-Saarburg, en nog 1 andere.
Nu: Bewolkt, 19,4 °C, wind 14 km/u met stoten tot 38.
Vandaag 27,8 °C, vannacht 15,2 °C, 70 procent kans op neerslag en tot 8,4 mm.
Regen over ongeveer 35 minuten, piek 6,2 mm/u.
Onweer op 44 km, nadert snel, hier over 78 minuten.
```

Regels zonder inhoud vallen weg. Het bericht negeert de wachttijd, de
stilstandcontrole en het stiltevenster, want je hebt zelf een tijdstip
gekozen. Met `stormchase.send_briefing` stuur je hem direct.

### Weersituaties

Naast onweer, regen en wind meldt de integratie sneeuw, ijzel, mist, hitte en
vorst. Elk bericht bevat de bijbehorende cijfers: bij sneeuw de hoeveelheid
per uur en de windstoten, bij mist de luchtvochtigheid, bij hitte en vorst de
gevoelstemperatuur.

Elke situatie meldt bij het intreden en niet zolang hij duurt, en houdt een
eigen wachttijd bij zodat ze elkaar niet blokkeren. IJzel, sneeuw en mist
komen ook door tijdens het rijden; hitte en vorst wachten tot je ergens bent.

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

In Nederland komt de verwachting sinds 0.49.0 eerst van het KNMI (per
radarcel van een vierkante kilometer, met exacte UTC-tijdstempels); daarna van
de neerslagtekst van Buienradar: per vijf minuten, twee uur vooruit, op
exacte coordinaten. Dat is nauwkeuriger dan een
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
| `stormchase_outlook` | Het vooruitzicht schaalt op naar zwaarder weer. |

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

Sinds 0.50.0 is het dashboard een storm-chase-commandocentrum: één scherm
over de volle breedte met alles wat je tijdens een jacht wilt zien, op een
donkere stormnacht-achtergrond met glazen panelen. Geen HACS-kaarten nodig:
de integratie levert de kaart (`custom:stormchase-hud-card`) zelf mee, zonder
externe bestanden.

### Aanbevolen: de strategie

Maak een nieuw dashboard aan, open de onbewerkte configuratie-editor en zet
er dit in:

```yaml
strategy:
  type: custom:stormchase
```

Dat is alles — de integratie registreert het benodigde script zelf als
Lovelace-bron. Je krijgt drie tabbladen:

1. **Stormchase** — het commandocentrum (panel-view):
   - **Statusbalk**: locatie (adres of coördinaten), onderweg/ter plaatse,
     meldingen aan/uit, bronbolletjes per bron, *KNMI push live*, klok en
     laatste update. Daaronder de situatie (rustig / actief / nadert /
     nabij, met afstand, richting en aankomsttijd), de waarschuwingscode
     groot in de kleur van het niveau, de onweersverwachting en de
     chase-potentie als meter met opbouw. Bij schuilen een rode balk
     *Blijf binnen*.
   - **Radar** groot (`image.stormchase_radar`) met radarbron en beeldleeftijd;
     met een KNMI WMS-sleutel een knop *Vooruitblik*
     (`image.stormchase_radar_vooruitblik`).
   - **Bliksem**: kompas met de afstandsringen, de dichtstbijzijnde inslag en
     de trekrichting van de cel; afstand, nadering, aankomst, inslagen per
     ring, frequentie, celpassage en de vlaggen nabij/nadert/schuilen.
   - **Convectie**: CAPE nu en piek 12 uur, Lifted Index, windschering,
     ensemble-onweerskans en modelovereenstemming als balken met drempels,
     plus rotatie, hagel, Total Totals, LPI, wolkentop en de duiding in
     gewone taal.
   - **Waarschuwingen**: actuele code met tekst en periode, en een tijdlijn
     van het niveau per uur voor de komende 24 uur (KNMI).
   - **Waarnemingen** van het dichtstbijzijnde station (KNMI EDR of
     Bright Sky): windstoten met Beaufort, luchtdruk met verandering per uur
     en per 3 uur, temperatuur/dauwpunt, zicht, wolkenbasis, wind, en
     *onweer/hagel gemeten*.
   - **Neerslag komende 2 uur** per vijf minuten, met *regen over …*, piek
     en totaal.
   - **Verwachting per uur** (temperatuur, neerslagkans, windstoten,
     weersymbool) uit `weather.stormchase`.
   - **Bronstatus** per bron met slaagpercentage, en de versie van het script.
2. **Kaarten** — iRadar, Buienradar en Windy (CAPE) als ingebouwde
   iframe-kaarten, gecentreerd op je actieve locatie.
3. **Alle waarden** — vangnet met elke entiteit van de integratie.

Wat ontbreekt blijft weg: geen KNMI-sleutel betekent geen vooruitblikknop,
geen weerstation betekent geen waarnemingenpaneel. Onbekende waarden worden
een streepje, onbeschikbare worden gedimd. Bij naderend of nabij onweer
licht de achtergrond zwak op als bliksem (uit bij *verminder beweging*).
Op een telefoon staat alles in één kolom, op een tablet in twee, op een
breed scherm in drie.

De kaart zoekt de entiteiten zelf op via het entiteitenregister, dus het
werkt ook met Engelse entity-id's of met een ruimtenaam ervoor.

**Na een update: ververs je browser.** De URL van het script bevat het
versienummer en de starttijd van Home Assistant (`?v=0.50.0&t=…`), zodat je
browser na een herstart het nieuwe script ophaalt. Zie je toch het oude
dashboard, ververs dan hard met Ctrl+Shift+R (in de companion-app: de
frontendcache wissen via de instellingen van de app). Onderaan het
dashboard en in de console (F12, regel `STORMCHASE commandocentrum geladen`)
staat welke versie je browser draait.

Krijg je toch *Timeout waiting for strategy element*, dan draait Lovelace
waarschijnlijk in YAML-modus en moet je de bron handmatig toevoegen onder
Instellingen → Dashboards → Bronnen: URL `/stormchase/stormchase-strategy.js`,
type JavaScript-module. Ververs daarna één keer hard met Ctrl+Shift+R.

Wil je alleen het commandocentrum als losse view binnen een bestaand
dashboard:

```yaml
views:
  - strategy:
      type: custom:stormchase
    title: Stormchase
```

Of de kaart los, in een eigen view (bij voorkeur een panel-view):

```yaml
type: custom:stormchase-hud-card
```

Opties, allemaal optioneel:

```yaml
strategy:
  type: custom:stormchase
  title: Onweer                      # titel van de view en ondertitel in de kop
  distance_entity: sensor.x          # anders automatisch gedetecteerd
  azimuth_entity: sensor.y
  counter_entity: sensor.z
  latitude: 52.10                    # kaarten-tab; anders de actieve locatie
  longitude: 6.63
  iradar_url: https://iradar.app/... # je eigen embed-URL
  radar_ratio: "70%"                 # verhouding van iRadar in de kaarten-tab
  map_ratio: "120%"                  # anders automatisch per schermbreedte
  alle_waarden: false                # laat de tab Alle waarden weg
  maps:                              # false laat de hele kaarten-tab weg
    iradar: true
    blitzortung: true
    buienradar: true
    satelliet: true
    windy: false
```

De optie `radar_boven` uit eerdere versies doet niets meer: de eigen radar
staat altijd in het midden van het commandocentrum.

### Alternatief: statische YAML

`dashboards/stormchase.yaml` bevat de klassieke tegelindeling als gewone YAML,
voor als je liever zelf aan de kaarten sleutelt. Die gebruikt wel HACS-kaarten
(`card-mod`, `mushroom`, `apexcharts-card`, `compass-card`). Nadeel: die moet je bij elke update van
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

## Tests

`python -m pytest tests -q` draait de suite; dat gebeurt ook automatisch bij
elke push. Zie `tests/README.md` voor wat er getest wordt en waarom er
structuurtests bij zitten.

## Diagnostiek

Bij een probleem: ga naar Instellingen → Apparaten & Diensten → Stormchase →
driepuntsmenu → **Diagnostische gegevens downloaden**. Dat bestand bevat alles
wat nodig is om mee te kijken.

Sinds 0.24.0 zit er ook een overzicht in van hoe goed de voorspellingen
uitkwamen: begon het regenen wanneer we dachten, kwam het onweer op tijd aan,
en klopte de afstand waarop een cel passeerde. Per soort met de gemiddelde en
grootste afwijking.

Sinds 0.46.0 telt een passage pas als raak wanneer de cel binnen 10 km van de
voorspelde afstand langskwam (`binnen_10_km`, met `binnen_20_km` als ruime
maat, `trefkans_10_km_pct`/`trefkans_20_km_pct` en de mediane afwijking).
`uitgekomen` betekent bij passages alleen "afstand gemeten" en blijft voor
vergelijkbaarheid bestaan. Elke uitkomst draagt de gemeten afwijking in km.

Wat erin zit: de instellingen, de actuele waarden, per bron het aantal
geslaagde en mislukte ophaalrondes met de laatste foutmelding, welke
neerslagbron gebruikt is, hoeveel events en meldingen er zijn geweest, en de
laatste zestig afstandsmetingen met de berekende naderingssnelheid.

Coordinaten staan afgerond tot ongeveer een kilometer. De gevolgde
device_tracker, handmatige coordinaten en de namen van je meldingsdiensten
worden weggelaten.

### Herstarten verandert niets

Sinds 0.47.0 overleeft alles wat de integratie leert of bijhoudt een herstart
of herlaadbeurt: de uitkomsten én de nog open voorspellingen, de tellers per
bron, events en meldingen, de wachttijden tussen meldingen, de al gemelde
officiële waarschuwingen, de 30/30-schuilregel, de celsporen en de
naderingsreeks. Een lopende waarschuwing of schuilperiode wordt na een
herstart dus niet opnieuw gemeld, en "veilig" komt gewoon. Bij ontladen en
afsluiten wordt alles meteen weggeschreven. Cellen, inslagen en
overgangsvlaggen die ouder zijn dan een half uur vallen bij het laden weg.
Mislukt de eerste ophaalronde na een herstart, dan tonen Open-Meteo, regen,
waarschuwingen en metingen de bewaarde waarde (hooguit drie uur oud) in
plaats van onbeschikbaar.

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

MIT. KNMI-gegevens: CC BY 4.0, zie [Bronvermelding](#bronvermelding).

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
