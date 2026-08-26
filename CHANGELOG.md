# Changelog

Alle noemenswaardige wijzigingen aan dit project staan hier.

Het formaat volgt [Keep a Changelog](https://keepachangelog.com/nl/1.1.0/),
en het project gebruikt [semantische versienummers](https://semver.org/lang/nl/).

## [0.35.0] — 2026-08-26

### Toegevoegd

- **Radar van de Duitse weerdienst als alternatieve bron.** Die publiceert
  zijn radarcompositie als open kaartdienst zonder sleutel, en actueler dan
  de wereldwijde verzameling van RainViewer. Te kiezen met de instelling
  Radarbron.
- Gebruikt dezelfde machinerie als de wolkenlaag: een gebiedsverzoek en
  dezelfde herprojectie van plat naar webmercator. Dat scheelde bouwwerk en
  betekent dat beide lagen op dezelfde manier getest zijn.
- De laag is aan te passen, bijvoorbeeld naar de bliksemdichtheid die
  diezelfde dienst publiceert.
- Komt er niets terug van die dienst, dan valt hij terug op RainViewer in
  plaats van een leeg beeld te tonen.

### Afweging

RainViewer blijft de standaard. De Duitse dienst is actueler maar de dekking
houdt op bij de landsgrens en de directe omgeving; RainViewer werkt overal.
Voor jouw omgeving in de Achterhoek en de Eifel zou de Duitse bron beter
moeten uitpakken, verder weg niet.

### Nog ongetest

Zowel deze laag als de wolkenlaag uit 0.34.0 zijn gebouwd op de catalogus van
de aanbieder, niet op een geslaagd verzoek. Komt er niets, kijk dan bij
`sensor.stormchase_bronstatus`.

## [0.34.0] — 2026-08-26

### Gewijzigd

- **De bewolking komt nu van EUMETSAT in plaats van infrarood.** Infrarood
  meet wolktoptemperatuur: hoge bewolking is ijskoud en steekt scherp af,
  maar lage en middelhoge bewolking heeft een top die nauwelijks kouder is
  dan de grond eronder en verdween daardoor vrijwel volledig uit beeld.
  Precies de bewolking die op een chase-dag telt.
- Er wordt nu het wolkenmasker van Meteosat gebruikt, dat elk beeldpunt
  indeelt als helder of bewolkt, ongeacht de hoogte van de wolk.
- **Met herprojectie.** De kaartdienst levert een plat beeld op
  breedtegraad, terwijl het radarbeeld in webmercator staat. Zonder
  omrekening zou de bewolking er tientallen kilometers naast liggen: in het
  midden van het beeld scheelt dat elf pixels, ongeveer acht kilometer. Het
  beeld wordt daarom rij voor rij opnieuw opgebouwd.
- De laag is met een instelling te wisselen, bijvoorbeeld naar
  `msg_fes:cth` voor wolktophoogte.

### Toegevoegd

- Zestien tests op de grenzen, het verzoek en de herprojectie. Een daarvan
  bewaakt de volgorde van de hoeken: bij EPSG:4326 komt de breedtegraad
  eerst, en met de verkeerde volgorde komt er een leeg beeld terug zonder
  foutmelding.

### Nog open

Een actuelere radar voor Nederland en Duitsland. De Duitse weerdienst
publiceert die met vijf minuten resolutie, maar of dat als kaartdienst
bereikbaar is heb ik nog niet nagegaan.

## [0.33.1] — 2026-08-26

### Gewijzigd

- **De wolkenlaag was te dicht.** Infrarood toont alle bewolking, ook hoge
  sluierbewolking, en dat legde op volle sterkte een grijze waas over de hele
  kaart waardoor plaatsnamen niet meer te lezen waren. De laag wordt nu op
  vijfenveertig procent getekend, genoeg om te zien waar bewolking zit zonder
  de kaart eronder dicht te smeren.

## [0.33.0] — 2026-08-26

Celtracking zoals op professionele stormkaarten.

### Toegevoegd

- **Alle cellen worden nu gevolgd**, niet alleen de dichtstbijzijnde. Elke
  cel houdt een eigen spoor bij; een nieuw zwaartepunt wordt gekoppeld aan
  het spoor waarvan het laatste punt het dichtst ligt.
- **Kleur naar activiteit**: geel voor een gewone bui, oranje vanaf acht
  inslagen, rood vanaf vijfentwintig. De ring wordt bovendien groter naarmate
  er meer inslagen in de cel zitten.
- **Koerslijn met streepjes per kwartier**, een uur vooruit. Elk streepje is
  waar de cel dan ligt als hij zijn koers houdt, dus je leest er direct de
  aankomsttijd uit af.
- Alle gevolgde cellen staan als attribuut op `sensor.stormchase_celrichting`,
  met per cel de afstand, richting, snelheid, activiteit en passage.

### Opmerking

De sensoren blijven de dichtstbijzijnde cel volgen; de kaart toont ze
allemaal. Dat onderscheid is bewust: een melding over de bui op honderd
kilometer helpt niet, maar op de kaart wil je hem wel zien liggen.

## [0.32.1] — 2026-08-26

### Toegevoegd

- **Tijdstip linksonder op het radarbeeld**, met hoe oud het is: "Radar 15:11
  · 2 minuten oud". Zonder dat weet je niet of je naar iets van net kijkt
  of naar een beeld dat al een kwartier stilstaat omdat de bron hapert.
- Bewust het tijdstip van de opname en niet van het ophalen. Die twee lopen
  uiteen: het overzicht kan vers zijn terwijl het beeld zelf ouder is.
- De ouderdom staat ook als attribuut op de entiteit, zodat je er een
  automatisering op kunt bouwen.

## [0.32.0] — 2026-08-26

### Toegevoegd

- **Wolken op het radarbeeld.** De infraroodlaag van RainViewer ligt nu
  tussen de kaart en de neerslag. Daarmee zie je bewolking waar nog geen
  neerslag valt, en dus opbouwende cumulus voordat de radar iets oppikt. Uit
  te zetten met een schakelaar in de instellingen.
- **De onweerscel wordt getekend.** Het spoor van zwaartepunten laat zien
  waar de bui vandaan komt, de ring waar hij nu zit, en de pijl waar hij over
  een half uur ligt als hij zijn koers houdt.
- De pijl staat op schaal: vijftig kilometer per uur levert een pijl op die
  precies de vijfentwintig kilometer beslaat die de cel in dat half uur
  aflegt. Bij een hoger zoomniveau wordt hij evenredig langer.

### Gerepareerd

- Bij het toevoegen van de wolkenschakelaar belandde er opnieuw een
  constantnaam in het formulier. De structuurcontrole meldde het meteen.

## [0.31.1] — 2026-08-26

### Gerepareerd

- **Een mislukte registratie herstelde zichzelf nooit.** Zodra de
  dashboardstrategie een keer geregistreerd leek, werd het bij elke volgende
  start overgeslagen. Ging het de eerste keer mis, dan bleef het dashboard
  leeg met "Timeout waiting for strategy element", ook na herstarten. Beide
  routes worden nu bij elke start opnieuw geprobeerd.
- Het registreren van het bestandspad kan bij een herlaad van de integratie
  melden dat het pad al bestaat. Dat is geen fout meer en houdt de rest niet
  langer tegen.

### Gewijzigd

- Lukt het vastleggen als bron niet, dan staat dat nu als waarschuwing in het
  logboek met de URL erbij, in plaats van als debugregel die je alleen ziet
  als je ernaar zoekt. Lukt het wel, dan staat de URL er ook, zodat te
  controleren valt of het versienummer klopt.
- `lovelace` is als voorafgaande afhankelijkheid opgegeven, zodat de
  integratie niet eerder laadt dan het onderdeel waar de bron in moet.

### Als het dashboard leeg blijft

Voeg `/stormchase/stormchase-strategy.js` handmatig toe onder Instellingen,
Dashboards, driepuntsmenu, Bronnen, als type JavaScript-module. Dat is
dezelfde route die de kaarten uit HACS gebruiken.

## [0.31.0] — 2026-08-26

### Toegevoegd

- **Blikseminslagen op het radarbeeld.** De inslagen van het laatste kwartier
  worden op hun eigen positie getekend, waarbij verse inslagen fel wit zijn
  en oudere naar oranje uitdoven. Daarmee zie je in een oogopslag welke kant
  de activiteit op schuift, iets wat de radar alleen niet laat zien.
- **Je eigen positie** staat als witte ring in het midden, anders zegt de
  rest van het beeld weinig.
- Het beeld ververst nu ook wanneer er inslagen bijkomen, niet alleen bij een
  nieuw radarbeeld.

### Gewijzigd

- **Het radaroverzicht wordt elke minuut opgehaald** in plaats van elke vijf.
  RainViewer publiceert ongeveer elke vijf minuten een nieuw beeld, maar niet
  op vaste tijden; vaker kijken betekent dat je het eerder ziet. Het
  overzicht is klein, dus dat kost weinig. Instelbaar van dertig seconden tot
  tien minuten.

### Gerepareerd

- Bij het toevoegen van die instelling belandde er opnieuw een constantnaam
  in het formulier. De structuurcontrole meldde het binnen tien seconden, met
  regelnummer.

## [0.30.1] — 2026-08-26

### Gerepareerd

- **"API KEY REQUIRED" dwars over het radarbeeld.** CARTO heeft zijn donkere
  kaart achter een sleutel gezet. De ondergrond komt nu van OpenStreetMap,
  dat geen sleutel vereist.
- De donkere varianten van andere aanbieders zijn de laatste jaren allemaal
  achter een sleutel verdwenen, dus de gewone kaart wordt nu zelf gedempt:
  donker genoeg om de neerslag te laten opvallen, licht genoeg om
  plaatsnamen te kunnen lezen.
- Het dempen gebeurt voordat de radar erover gaat, anders zou die mee
  verduisteren en onzichtbaar worden.
- Bij het ophalen wordt een herkenbare naam meegestuurd, zoals hun
  gebruiksvoorwaarden vragen.

### Toegevoegd

- Vier tests op de ondergrond, waaronder een die controleert dat er geen
  sleutel in de URL staat.

## [0.30.0] — 2026-08-26

Vier reparaties uit een diagnostiek en drie screenshots.

### Gerepareerd

- **Het radarbeeld had geen ondergrond.** RainViewer levert alleen de
  neerslaglaag, als doorzichtige overlay. Zonder kaart eronder zweefden er
  vlekken in het niets. De radar wordt nu over een donkere kaart gelegd en
  rond je positie uitgesneden.
- **Het ensemble gaf zeshonderd keer een 404.** Die API draait op een eigen
  subdomein; het gedeelde eindpunt kent hem niet. Daarom stond de
  onweerskans acht rondes lang op onbekend.
- **De Lifted Index kwam wel binnen maar bereikte de sensor niet.** In de
  teruggegeven gegevens werd het hoofdmodel opnieuw bevraagd in plaats van de
  opgeloste waarde door te geven. De verwachting rekende dus met de juiste
  waarde terwijl de sensor leeg bleef. In het antwoord zaten achtenveertig
  waarden; dat het diagnosebestand dat telt maakte het verschil zichtbaar.
- **Blitzortung en Meteox weigeren insluiten** en toonden een blokkade-icoon.
  Beide staan nu standaard uit. Aanzetten kan met `maps: {blitzortung: true}`
  of `{satelliet: true}`.

### Toegevoegd

- Zestien tests op de tegelberekening, waaronder de datumgrens en de polen.

### Opmerking

De integratie heeft nu Pillow nodig voor het samenstellen van het
radarbeeld. Dat pakket zit al in Home Assistant, dus er wordt niets extra
geinstalleerd.

## [0.29.1] — 2026-08-22

Drie verdwaalde importregels, met uiteenlopende gevolgen.

### Gerepareerd

- **De weerparameters haalden niets meer op.** Vier constantnamen waren in
  het verzoek om de Lifted Index beland, waardoor dat verzoek zes argumenten
  meekreeg in plaats van een. De hele ophaalronde liep daarop stuk, en
  daarmee viel de integratie om. Dat het dashboard vervolgens meldde dat de
  strategie niet geregistreerd was, was een gevolg en niet de oorzaak.
- **Weersituaties vuurden onder een verkeerde naam af.** De eventnaam was
  verschoven, waardoor sneeuw, ijzel, mist, hitte en vorst afgingen als
  `outlook_level` in plaats van `stormchase_weather`. De notifier luisterde
  op de juiste naam en hoorde dus nooit iets. Dit was de werkelijke reden dat
  er geen weermeldingen kwamen; de reparatie in 0.24.1 loste een tweede
  probleem op maar niet dit.
- **De windmelding zou bij de eerste harde windstoot zijn gecrasht**, om
  dezelfde reden.

### Toegevoegd

- Drie structuurcontroles die precies dit patroon vangen: geen constantnamen
  op importniveau binnen een functie, `async_fire` met hoogstens twee
  argumenten, en verzoeken met precies een URL. Op de fouten van vanavond
  losgelaten melden ze meteen het regelnummer.

### Waarom dit drie keer kon gebeuren

Bewerkingen aan importlijsten grepen ook verderop in het bestand. Dat
compileert prima en valt statisch niet op: een aanroep krijgt gewoon meer
argumenten dan bedoeld, of de eerste parameter wordt vervangen door iets
anders. De bestaande controle keek alleen naar formuliervelden en zag deze
gevallen niet.

## [0.29.0] — 2026-08-22

### Toegevoegd

- **Radarbeeld dat je locatie volgt**, als entiteit `image.stormchase_radar`.
  RainViewer heeft een eindpunt dat op coordinaten centreert in plaats van op
  kaarttegels, waardoor het beeld meeschuift met de locatie die de integratie
  gebruikt.
- Geen ingesloten webpagina meer nodig: geen cookiemelding, geen
  advertenties, en het laadt sneller dan de kaarten eronder. Wereldwijde
  dekking uit meer dan duizend radars, elke vijf minuten ververst, zonder
  sleutel.
- Het zoomniveau is instelbaar van 1 tot 7; hoger bestaat er niet.
- Het beeld wordt pas opgehaald wanneer iemand ernaar kijkt. Alleen het
  overzicht met beschikbare beelden wordt elke vijf minuten bijgewerkt.

### Gerepareerd

- Bij het toevoegen van de zoominstelling belandde een constantnaam opnieuw
  in het meldingsformulier in plaats van in de importlijst, precies de fout
  uit 0.23.0. Deze keer ving de structuurtest hem meteen af.

## [0.28.0] — 2026-08-22

### Toegevoegd

- **Onweerskans uit ensembleleden.** Een ensemble draait hetzelfde model
  twintig tot eenendertig keer met licht verschillende beginwaarden. Dat
  levert geen enkele uitkomst maar een kans: veertien van de twintig leden
  boven de drempel is zeventig procent.
- Gebruikt ICON-D2-EPS, het ensemble van twee kilometer dat Midden-Europa
  dekt, met GEFS als wereldwijde terugval.
- Per lid wordt de hoogste waarde over de komende twaalf uur genomen. Een
  momentopname zegt weinig over een dag, want convectie piekt vaak maar een
  paar uur.
- Twee drempels: vijfhonderd voor onweer, vijftienhonderd voor zwaar weer.
- De kans staat op het dashboard en in het dagelijkse weerbericht.

### Waarom dit meer zegt dan de mediaan

Een mediaan van 1200 J/kg ziet eruit als een prima onweersdag. Zitten er
leden bij van 150 en van 2400, dan zegt dat getal vooral dat het alle kanten
op kan. De kans maakt dat zichtbaar; een enkele uitkomst verbergt het.

### Over I'm Weather

Dat is een modellenviewer zonder API, dus als databron niet te gebruiken. De
ensembleleden waar die site op wijst zijn wel gratis op te halen, en dat is
nu gebeurd.

## [0.27.0] — 2026-08-22

Bestand tegen storingen, en voor het eerst echte metingen.

### Toegevoegd

- **Metingen van het dichtstbijzijnde weerstation** via Bright Sky, de open
  API op de data van de Duitse weerdienst. Gratis, zonder sleutel. Alles wat
  de integratie verder toont is voorspeld; dit is wat er daadwerkelijk
  gemeten is, met de stationsnaam en de afstand erbij.
- **`sensor.stormchase_bronstatus`** laat zien welke bronnen het doen en
  welke haperen, met per bron het slaagpercentage en de laatste foutmelding.
- Op het dashboard verschijnt een tegel zodra een bron hapert, met de
  waarschuwing dat getoonde waarden verouderd kunnen zijn.

### Gewijzigd

- **Een bron die eruit ligt maakt het dashboard niet meer leeg.** Standaard
  maakt Home Assistant alle entiteiten van een coordinator onbeschikbaar
  zodra een ophaalronde faalt. Voor weergegevens is dat de verkeerde keuze:
  midden in een onweer wil je geen blanco scherm omdat een server hikt. De
  laatst bekende waarden blijven nu staan, met het aantal minuten ouderdom
  erbij, tot drie uur. Daarboven wordt de sensor alsnog onbeschikbaar, want
  dan is leeg eerlijker dan verkeerd.
- Dit geldt voor de weerparameters, de neerslag, de waarschuwingen en de
  metingen. Elke bron staat los: valt er een weg, dan werken de andere door.
- **De satellietkaart wijst nu naar Meteox**, de opvolger van SAT24.

### Over Kachelmann

Hun API is betaald en vereist minstens een Plus-abonnement. Wat je ervoor
krijgt is serieus: multimodel-verwachtingen, een eigen model van 1x1
kilometer en tienduizenden stationsmetingen. Heb je dat abonnement, dan is
ondersteuning inbouwen zinvol; zonder abonnement niet.

## [0.26.1] — 2026-08-22

### Toegevoegd

- **Satellietkaart van SAT24** met bliksemlaag, in de kaartenkolom. Satelliet
  laat opbouwende convectie zien voordat de radar neerslag oppikt: torenende
  cumulus en overshooting tops. Dat is het moment waarop je besluit of je
  gaat rijden.
- Uit te zetten met `maps: {satelliet: false}`, of te vervangen met
  `satelliet_url`.

### Opmerking

SAT24 is van eigenaar gewisseld en de widgets zijn verhuisd. Blijft het vlak
leeg, dan blokkeert de site het insluiten en is `satelliet_url` de weg naar
een andere bron.

### Over Breezy Weather

Dat is een Android-app, geen Home Assistant-integratie, dus er valt niets te
koppelen. De makers zetten radar zelfs expliciet op hun lijst van dingen die
ze niet gaan bouwen. Hun bronnenlijst is wel interessant voor later: naast
modellen gebruiken ze Bright Sky en KNMI, en dat zijn metingen van
weerstations in plaats van modelwaarden.

## [0.26.0] — 2026-08-22

### Toegevoegd

- **Modelovereenstemming.** Dezelfde grootheid wordt nu bij acht modellen
  opgevraagd: ECMWF, ICON-EU, ICON-D2, GFS, UKMO, GEM, MET Norway en
  Meteo-France. `sensor.stormchase_modelovereenstemming` zegt of ze het eens
  zijn, wat afwijken of verdeeld zijn, met de mediaan en het bereik erbij.
- Een enkel getal uit een enkel model leest als zekerheid, en dat is het
  niet. Zes modellen die allemaal rond 2000 J/kg zitten is een dag om vrij te
  houden; een schatting die uiteenloopt van 200 tot 2600 zegt vooral dat je
  op de volgende modelrun moet wachten.
- De mediaan in plaats van het gemiddelde, want bij convectie zit er
  regelmatig een model ver naast en dat trekt een gemiddelde scheef.
- De spreiding wordt afgezet tegen een ondergrens van 200 J/kg. Zonder dat
  zou elke rustige dag als verdeeld gelden: van 0 naar 60 J/kg is
  verhoudingsgewijs enorm maar praktisch betekenisloos.
- Zijn de modellen het oneens, dan staat dat in het dagelijkse weerbericht.
- Modellen die de locatie niet dekken of het veld niet leveren komen leeg
  terug en tellen niet mee. Onder de drie bruikbare modellen komt er geen
  oordeel.

### Waarom niet BeerWeer

Die dienst bouwt op hetzelfde idee, maar levert alleen algemene velden:
temperatuur, wind, neerslag, druk en UV. Geen CAPE, geen bliksempotentie,
geen windschering, dus voor onweersanalyse voegt het niets toe. Bovendien
komt het uit dezelfde bron die deze integratie al rechtstreeks bevraagt. Het
idee erachter was wel de moeite waard, en dat is nu toegepast waar het
verschil maakt.

## [0.25.3] — 2026-08-22

### Gerepareerd

- **Waarden werden alleen op een exact uur opgezocht.** Niet elk model levert
  per uur: GRAPES geeft stappen van drie uur. Het verzoek slaagde
  drieentwintig van de drieentwintig keer, maar er werd nooit een tijdstip
  gevonden dat precies aansloot, dus bleef de Lifted Index leeg. Er wordt nu
  gezocht naar het dichtstbijzijnde tijdstip binnen anderhalf uur.
- Lege waarden worden overgeslagen bij dat zoeken, zodat een bruikbare waarde
  iets verderop niet verdrongen wordt door een lege ernaast.

### Toegevoegd

- De opzoeklogica staat in een eigen module zonder Home Assistant-imports en
  is daardoor getest: uurstappen, stappen van drie uur, lege waarden, reeksen
  zonder tijdzone en tijdstippen buiten de marge. Vijftien tests.
- De diagnostiek telt hoeveel waarden het model daadwerkelijk teruggaf voor de
  Lifted Index. Daarmee is te onderscheiden of een model het veld niet levert
  of dat het opzoeken ernaast greep. Dat verschil kostte twee reparatierondes.

### Opmerking

De schering over 0-1 en 0-3 km waren in de vorige meting toevallig gelijk;
inmiddels staan ze op 20,4 en 3,7 km/u. Daar was dus niets mis mee.

## [0.25.2] — 2026-08-22

### Gerepareerd

- **De Lifted Index komt nu van het juiste model.** Open-Meteo levert dat
  veld niet bij GFS: het verzoek slaagde zestig van de zestig keer en gaf
  toch lege waarden terug. Het staat wel als eigen veld in het GRAPES-model,
  wereldwijd op vijftien kilometer. Dat de bron nu als aparte teller in de
  statistieken staat maakte dit verschil zichtbaar; anders was het opnieuw
  gissen geweest tussen een fout verzoek en een ontbrekend veld.

## [0.25.1] — 2026-08-22

### Gerepareerd

- **Windschering over 0-3 km bleef leeg.** De wind op 700 hPa werd wel in de
  berekening gebruikt maar nergens opgevraagd. Dat niveau is nu toegevoegd,
  waarmee ook de draaiing met hoogte op vier niveaus rekent in plaats van
  drie.
- **De Lifted Index werd bij het gedeelde eindpunt opgevraagd met een
  modelkeuze erbij.** Dat leverde niets op. Het verzoek gaat nu naar het
  eigen GFS-eindpunt.

### Toegevoegd

- ICON-D2 en GFS tellen nu mee als aparte bronnen in de statistieken, met
  slaagpercentage en foutmelding. Die verzoeken faalden stil, waardoor niet
  te zien was of een lege waarde aan het model lag of aan een fout verzoek.
- De diagnostiek toont de nieuwe velden: bliksempotentie, opwaartse stroming,
  wolkentop, alle drie de scheringen, de draaiing en of er kwartierdata is.

## [0.25.0] — 2026-08-22

Modelvelden die er wel waren maar niet werden opgehaald.

### Toegevoegd

- **Bliksempotentie (LPI)** uit ICON-D2, een verticale integraal van de
  gekwadrateerde opwaartse snelheid gewogen met de graupelconcentratie. Dat
  is een bliksemverwachting uit het model zelf, in plaats van iets wat ik uit
  losse velden afleid.
- **Opwaartse stroming**, de maximale verticale snelheid tussen grond en tien
  kilometer. Vanaf ongeveer twintig meter per seconde kan een bui hagelstenen
  lang genoeg omhoog houden om ze fors te laten worden.
- **Wolkentop en wolkenbasis** van de convectie, zodat je ziet hoe hoog een
  bui reikt.
- **Windschering over 0-3 km** naast 0-1 en 0-6.
- **Draaiing met hoogte**: rechtsdraaiend, linksdraaiend of nauwelijks. Dat is
  de kern van wat een hodograaf laat zien, zonder dat je hem hoeft te kunnen
  lezen. Rechtsdraaiend hoort bij een omgeving waarin supercellen zich kunnen
  organiseren.

### Gewijzigd

- **CAPE en vriesniveau komen nu van kwartierwaarden** waar die beschikbaar
  zijn, in plaats van uurwaarden. Bij opbouwende convectie scheelt dat
  merkbaar in actualiteit.
- **De onweersverwachting weegt de modelvelden zwaarder** dan mijn afgeleide
  drempels. Meldt het model zeer actief onweer, dan is dat noodweer, ongeacht
  wat CAPE en schering zeggen. Komen die velden niet binnen, dan gelden de
  oude drempels gewoon.
- **De Lifted Index wordt nu bij GFS opgehaald.** Het is een GFS-veld dat
  ICON niet publiceert, en in Midden-Europa kiest Open-Meteo standaard ICON.
  Daarom bleef die waarde vijf diagnostieken lang leeg.

### Opmerking

Deze velden komen alleen van ICON-D2, dat Midden-Europa dekt met een
resolutie van twee kilometer. Daarbuiten blijven ze leeg en werkt de rest
gewoon door. De extra verzoeken staan los van het hoofdverzoek, zodat een
storing daarin de rest niet meesleept.

## [0.24.3] — 2026-08-22

### Gerepareerd

- **Validatiegegevens overleven nu een herstart.** De uitkomsten stonden
  alleen in het geheugen, waardoor twaalf uur aan metingen verdween zodra
  Home Assistant opnieuw opstartte. Ze worden nu bewaard en bij het opstarten
  teruggehaald, zodat de zelfcontrole daadwerkelijk kan opbouwen.
- Bewaren gebeurt met vertraging, zodat een reeks afrondingen kort na elkaar
  tot een schrijfactie leidt in plaats van tot tien.

## [0.24.2] — 2026-08-22

### Gerepareerd

- **Het dashboardscript bevat geen niet-ASCII tekens meer.** Het middelpunt
  dat als scheidingsteken werd gebruikt kwam er bij een gebruiker als `Â·`
  uit, doordat het bestand ergens door een editor met de verkeerde codering
  was gehaald. Alles staat nu als escape in de broncode, wat visueel niets
  verandert maar het bestand bestand maakt tegen zo'n bewerking.

### Toegevoegd

- Vier tests op het strategiebestand zelf: alleen ASCII, niet afgekapt,
  haakjes in balans, en beide strategieen worden geregistreerd. Een
  syntaxfout in dat bestand levert namelijk alleen "Timeout waiting for
  strategy element" op, wat lastig te herleiden is naar de oorzaak.

### Bij problemen met het dashboard

Krijg je die timeout, open dan `/stormchase/stormchase-strategy.js` in je
browser en controleer of het bestand eindigt op `);` en of er `Â·` of `â€"`
in staat. Zo ja, dan is het bestand onderweg beschadigd en moet het opnieuw
uit de release worden geplaatst.

## [0.24.1] — 2026-08-22

Eerste versie die op echte validatiegegevens is bijgesteld.

### Gerepareerd

- **Weersituaties werden gedetecteerd maar nooit gemeld.** De coordinator
  viel terug op de standaardlijst met situaties, de notifier op een lege
  lijst. Zolang je die instelling niet handmatig had opgeslagen werd elke
  sneeuw-, ijzel-, mist-, hitte- of vorstsituatie herkend en daarna
  weggegooid. In twaalf uur draaien werden er twee gedetecteerd en nul
  gemeld.

### Gewijzigd

- **Validatie splitst nu op horizon**: tot 15 minuten, 15 tot 45, en verder.
  De eerste metingen lieten zien waarom dat nodig is: twaalf minuten vooruit
  zat de regenvoorspelling er 7 minuten naast, 57 minuten vooruit 33 minuten.
  Dat samen middelen tot 20 minuten verbergt precies wat je wil weten.
- **Aankomstvoorspellingen worden alleen nog vastgelegd tot een uur vooruit.**
  De eerste meting gaf een aankomst van 86 minuten die er nooit kwam. Boven
  het uur is het geen voorspelling maar extrapolatie van een afstandstrend
  over een kwartier.

## [0.24.0] — 2026-08-21

Testsuite en zelfcontrole.

### Toegevoegd

- **Testsuite met 115 tests**, te draaien met `python -m pytest tests -q` en
  automatisch bij elke push. Dekt de vertaling, de onweersindices, de
  celtracking en de validatie.
- **Structuurtests** die de fouten vangen die eerder pas bij een gebruiker
  opdoken: formuliervelden met te veel argumenten, kale constantnamen als
  dictsleutel, losse namen als statement, en stappen zonder vertaling. Op de
  fout uit 0.23.0 losgelaten meldt de test meteen
  `config_flow.py:312 heeft 3 argumenten`.
- **Validatie van voorspellingen.** De integratie legt vast wat ze voorspelt
  en kijkt het later na:
  - Regen: begon het regenen wanneer we dachten?
  - Aankomst: kwam het onweer binnen de waarschuwingsafstand op het verwachte
    moment?
  - Passage: klopte de voorspelde afstand waarop een cel zou langskomen?
- Per soort komt er een samenvatting in de diagnostiek met het aantal
  voorspellingen, hoeveel er uitkwamen, en de gemiddelde en grootste
  afwijking. Daarmee zijn de drempels bij te stellen op echte metingen in
  plaats van op aannames.
- Voorspellingen die ruim over tijd zijn tellen als niet uitgekomen, zodat
  een misser niet stilzwijgend verdwijnt.

### Gewijzigd

- De modules `cel.py`, `indices.py`, `taal.py` en `validatie.py` bevatten
  bewust geen Home Assistant-imports, zodat ze los te testen zijn. Een test
  bewaakt die scheiding.

## [0.23.2] — 2026-08-21

### Gewijzigd

- **Hoofdletters kloppen nu overal.** Waarschuwingsmeldingen begonnen met een
  kleine letter, omdat het soort waarschuwing rechtstreeks uit de feed komt.
  Ook de toelichting onder de onweersverwachting en de trend achter de
  nadering begonnen klein.
- Er wordt niet langer `capitalize` gebruikt, want dat verlaagt de rest van de
  tekst: "CAPE loopt op" werd daarmee "Cape loopt op". Alleen de eerste letter
  gaat omhoog.
- De ij wordt als een letter behandeld, zoals het in het Nederlands hoort:
  "IJzel" en niet "Ijzel". Dat geldt zowel in de meldingen als op het
  dashboard.
- Midden in een zin blijft alles gewoon klein: "waarschuwing code oranje voor
  zwaar onweer met zware regen".

## [0.23.1] — 2026-08-21

### Gerepareerd

- **"Unknown error occurred" bij het instellen van de locatie.** In het
  configuratiescherm waren op drie plekken constantnamen op de verkeerde
  regel terechtgekomen, waardoor velden meerdere argumenten meekregen waar er
  een verwacht werd. Het ergste geval zat in de trackerkeuze zelf, wat precies
  de stap is waar de fout opdook.
- Twee instellingen ontbraken daardoor in het formulier: het tijdvenster voor
  de ringen en de keuze welke weersituaties gemeld worden. Ze werkten wel via
  hun standaardwaarden, maar waren niet aan te passen.
- Het verversingsinterval werd gewist zodra je terugschakelde naar de
  thuislocatie.

### Gewijzigd

- Het meldingsformulier is opnieuw opgezet en gegroepeerd: waarheen, onweer,
  regen, wind, weersituaties, vooruitzicht, wanneer, en de vorm van de
  melding.

## [0.23.0] — 2026-08-21

Vier toevoegingen voor het chasen zelf.

### Celtracking

- De inslagen worden geclusterd tot cellen en het zwaartepunt van de
  dichtstbijzijnde wordt over tijd gevolgd. Daaruit volgt de richting waarheen
  de bui trekt, de snelheid, en waar en wanneer hij je passeert.
- Nieuwe sensoren: `celrichting`, `celsnelheid`, `passageafstand` en
  `passage_over`.
- Dit lost op dat de afstand tot de dichtstbijzijnde inslag van bui naar bui
  springt. Een cel die 15 km ten zuiden langsschampt levert nu die 15 km op,
  in plaats van een afstand die heen en weer stuitert.
- Clusteren gebeurt op een raster van een kwart graad met samenvoeging van
  buurvakjes, zodat een cel die net over een rasterlijn valt niet in tweeen
  wordt geknipt. Dat scheelt een berekening van elke inslag tegen elke
  andere, wat bij honderden inslagen per minuut telt.
- Verspringt het zwaartepunt meer dan veertig kilometer, dan is er een andere
  cel dichterbij gekomen en begint het spoor opnieuw.

### Inslagfrequentie

- `sensor.stormchase_inslagfrequentie` telt de inslagen per minuut, met in
  het attribuut `trend` of het toeneemt of afneemt. Een cel die aantrekt
  verraadt zich in de flitsfrequentie voordat de afstand iets doet.

### 30/30-regel

- `binary_sensor.stormchase_schuilen` gaat aan zodra er onweer binnen tien
  kilometer is, wat overeenkomt met dertig seconden tussen flits en donder,
  en blijft aan tot dertig minuten na de laatste inslag binnen die afstand.
  Juist de eerste en laatste inslagen van een bui slaan het verst van de kern
  in.
- `sensor.stormchase_veilig_over` telt af. Er komt een melding bij het ingaan
  en bij het aflopen, en op het dashboard een rode banner bovenaan.

### Meldingen

- Elke melding krijgt een knop naar het dashboard.
- Optioneel gaan meldingen over gevaar door de stille modus heen, als critical
  alert. Dat werkt alleen als je de companion-app daar toestemming voor hebt
  gegeven. Staat standaard uit.
- Onweersmeldingen noemen nu wat de cel doet: "Cel trekt naar het NO met 47
  km/u en passeert over 18 minuten op 6 km. 8 inslagen per minuut."

## [0.22.1] — 2026-08-21

### Gerepareerd

- **Samengestelde waarschuwingen werden half vertaald.** Een waarschuwing
  noemt vaak meer dan een verschijnsel tegelijk, zoals "heavy thunderstorms
  with heavy rain". De vertaler pakte een enkel trefwoord en liet de rest
  weg; dat wordt nu "zwaar onweer met zware regen". Bij drie onderdelen:
  "zwaar onweer met hagel en harde wind".
- Overlappende treffers tellen niet dubbel, dus "heavy rain" wordt niet
  daarna nog eens als "rain" meegenomen.
- Extra termen toegevoegd voor zwaar en lokaal onweer.

## [0.22.0] — 2026-08-21

### Toegevoegd

- **Melding zodra het vooruitzicht opschaalt.** Gaat de verwachting van kans
  op onweer naar kans op zwaar onweer, of naar noodweer, dan krijg je
  bericht met de toelichting erbij: "Kans op zwaar onweer in de komende uren.
  Veel energie, onstabiel, schering sterk."
- Alleen omhoog en alleen over de ingestelde drempel heen. Zakt het weer, dan
  kan een volgende opschaling opnieuw gemeld worden. Instelbaar vanaf kans op
  onweer, zwaar onweer of noodweer; standaard vanaf zwaar onweer.
- Deze melding komt ook door tijdens het rijden. Hij gaat over de komende
  uren en over de hele omgeving, en juist onderweg wil je weten dat de dag
  omslaat.

### Gewijzigd

- **Het dagelijkse weerbericht toont het oordeel** in plaats van de ruwe
  CAPE-waarde. Bij rustig weer een korte regel, anders met toelichting en de
  kansen op rotatie en hagel als die noemenswaardig zijn.
- `sensor.stormchase_onweersverwachting` draagt de ernst als attribuut
  `verwachting_rang`, van 0 voor geen onweer tot 4 voor noodweer.

## [0.21.0] — 2026-08-21

Getallen kregen betekenis.

### Toegevoegd

- **`sensor.stormchase_onweersverwachting`** vat de hele situatie samen in
  een oordeel: geen onweer verwacht, kleine kans op onweer, kans op onweer,
  kans op zwaar onweer, of kans op noodweer. Met een toelichting erbij die
  zegt waarom.
- Het oordeel kijkt naar de combinatie, niet naar een enkel getal. Energie
  zonder onstabiliteit levert niets op, en energie zonder windschering
  hooguit een losse bui die zichzelf binnen een uur opruimt.
- De losse waarden op het dashboard tonen nu hun betekenis groot en het getal
  klein: "Sterk" met daaronder "Schering 0-6 km · 61 km/u", en "Stabiel" met
  "Stabiliteit · Total Totals 41,3".
- In de attributen staat per onderdeel de duiding: energie, stabiliteit,
  windschering en vriesniveau.

### Gebruikte drempels

- Energie: nauwelijks tot 150, weinig tot 500, matig tot 1500, veel tot 2500,
  daarboven zeer veel.
- Stabiliteit op de Lifted Index, of op Total Totals als die ontbreekt:
  stabiel onder 44, licht onstabiel tot 50, onstabiel tot 56, daarboven
  sterk onstabiel.
- Schering: zwak tot 25, matig tot 50, sterk tot 72, daarboven
  supercelwaardig.

## [0.20.3] — 2026-08-21

### Gerepareerd

- **Chase-potentie kwam structureel te laag uit.** Open-Meteo levert de
  Lifted Index niet voor elke locatie of elk model; bij een lege waarde viel
  dat onderdeel weg en misten er dertig punten. Ontbreekt hij, dan wordt nu
  de Total Totals index gebruikt, die ongeveer hetzelfde zegt over de
  stabiliteit. Het attribuut `stabiliteit_via` laat zien welke van de twee
  gebruikt is.
- Een vlakke afstandsreeks leverde `-0,0 km/u` op. Dat is nu gewoon nul.

### Toegevoegd

- De diagnostiek bevat een steekproef van de gebiedsnamen zoals MeteoAlarm ze
  schrijft, in het veld `gebieden_in_land`. Daarmee valt na te gaan of het
  regiofilter niets vindt omdat er niets is, of omdat de namen niet op elkaar
  aansluiten.

## [0.20.2] — 2026-08-21

### Toegevoegd

- **Zichtbaar wanneer het regiofilter waarschuwingen weglaat.** Zijn er wel
  waarschuwingen in het land maar geen voor jouw omgeving, dan verschijnt er
  een grijze tegel met het aantal en de namen waarop is gefilterd. Zonder dat
  lijkt een leeg waarschuwingsblok alsof er niets speelt, terwijl er net tien
  kunnen zijn weggelaten.
- `sensor.stormchase_waarschuwingsniveau` draagt nu ook de attributen
  `aantal_in_land` en `gefilterd_op`.

## [0.20.1] — 2026-08-21

### Gewijzigd

- **Het soort waarschuwing wordt vertaald.** MeteoAlarm levert dat als vrije
  Engelse tekst, waardoor er in een verder Nederlands bericht ineens
  "heavy rain" stond. Dat is nu "zware regen".
- De vertaling gebeurt bij de bron, dus zowel het weerbericht, de melding als
  het dashboard tonen Nederlands. De oorspronkelijke term blijft bewaard in
  het attribuut `soort_origineel`.
- Herkenning gaat op trefwoord en van specifiek naar algemeen, want de
  formulering verschilt per land: het ene instituut schrijft "heavy rain",
  het andere "rain-flood" of "severe thunderstorms". Zo wordt
  "freezing rain" ijzel en niet regen.
- Wordt een term niet herkend, dan blijft de oorspronkelijke tekst staan.
  Liever een Engelse term die klopt dan een Nederlandse die de lading niet
  dekt.

## [0.20.0] — 2026-08-21

### Toegevoegd

- **Dagelijks weerbericht**, standaard om 07:00 en 13:00. Beide tijden zijn
  instelbaar en het geheel is uit te zetten. Zet je ze gelijk, dan hou je er
  een over.
- Het bericht bundelt wat de integratie al weet: officiele waarschuwingen,
  het weer nu, de verwachting voor vandaag, de neerslag voor de komende twee
  uur en onweer of de kans daarop. Ben je niet thuis, dan staat je adres
  eronder.
- Regels die niets toevoegen worden weggelaten. Bij rustig weer hou je drie
  regels over; bij onweer wordt het vanzelf uitgebreider.
- Nieuwe service `stormchase.send_briefing` om het bericht nu te sturen, los
  van het schema.

### Opmerking

Het weerbericht gaat langs de wachttijd en de stilstandcontrole heen: je hebt
er zelf om gevraagd op een vast tijdstip, dus dan hoort het te komen. Het
stiltevenster geldt er ook niet voor, dus zet de ochtendtijd niet vroeger dan
je wakker wil worden.

## [0.19.0] — 2026-08-21

Meldingen voor vijf extra weersituaties.

### Toegevoegd

- **Sneeuw**, met temperatuur, hoeveelheid per uur en windstoten erbij als er
  sprake is van sneeuwjacht.
- **IJzel en onderkoelde regen**, met de waarschuwing dat wegen glad kunnen
  worden.
- **Dichte mist**, met de luchtvochtigheid.
- **Hitte**, standaard vanaf 30 graden, met de gevoelstemperatuur als die
  noemenswaardig afwijkt.
- **Vorst**, standaard vanaf 0 graden, idem.
- Alle vijf zijn per stuk aan en uit te zetten, en de drempels voor hitte en
  vorst zijn instelbaar.

### Hoe ze zich gedragen

- Elke situatie meldt bij het **intreden**, niet zolang hij duurt. Bij vorst
  zou je anders elk half uur bericht krijgen tot de dooi invalt.
- Elke situatie houdt een **eigen wachttijd** bij, zodat sneeuw geen
  vorstmelding kan tegenhouden.
- IJzel, sneeuw en mist komen ook door **tijdens het rijden**, want die gaan
  over gevaar onderweg. Hitte en vorst wachten tot je ergens bent, net als
  regen.
- Bij een herstart wordt de eerste ronde alleen vastgelegd, zodat je geen
  bericht krijgt over iets dat al liep.

### Gewijzigd

- Alleen onweersmeldingen delen nog de hoofdwachttijd. Regen, wind en de
  weersituaties hebben elk hun eigen teller, zodat ze elkaar niet blokkeren.

## [0.18.1] — 2026-08-21

### Gerepareerd

- **"Regen over X min" terwijl het regende.** De huidige intensiteit werd
  bepaald uit een enkel tijdvak van vijf minuten. Viel dat net in een dipje
  tussen twee buien, dan gold het als droog terwijl je nat werd. Er wordt nu
  gekeken naar het zwaarste tijdvak in de tien minuten rond dit moment.

### Toegevoegd

- Het dashboardscript logt zijn eigen versie in de browserconsole:
  `STORMCHASE strategie geladen · v0.18.1`. Zo is meteen te zien of je het
  nieuwe script hebt of nog een oude uit de cache, in plaats van dat je dat
  moet afleiden uit gewijzigde labels op het dashboard.

## [0.18.0] — 2026-08-21

### Gewijzigd

- **De radar staat nu bovenaan over de volle breedte.** In een kolom van
  halve breedte werd de kaart laag, terwijl het bij celdetectie juist om
  oppervlak gaat: je wil de bui zien liggen ten opzichte van waar je bent.
  Op een breed scherm wordt hij daardoor ongeveer anderhalf keer zo hoog.
- De overige kaarten, Blitzortung, Buienradar en Windy, blijven in de
  rechterkolom.
- Nieuwe strategie-opties: `radar_boven: false` zet de radar terug in de
  kolom, en `radar_ratio` legt de verhouding vast.

## [0.17.1] — 2026-08-21

### Gerepareerd

- **Browser bleef het oude dashboardscript gebruiken.** De URL van het script
  droeg alleen het versienummer, en bij een update via HACS bleef de oude URL
  soms in de bronnenlijst staan. De browser haalde dan netjes het bestand uit
  zijn cache, met als gevolg dat reparaties aan het dashboard onzichtbaar
  bleven tot je handmatig hard ververste.
- De URL bevat nu ook de starttijd van Home Assistant, dus na elke herstart
  is hij anders en moet de browser het script opnieuw ophalen. De
  bronnenlijst wordt daarbij bijgewerkt in plaats van dat er een tweede regel
  bij komt.

### Wat dit niet oplost

Tussen twee herstarts door blijft de URL gelijk, want die staat vast in de
bronnenlijst. Wijzig je het dashboard zonder te herstarten, dan is een harde
ververs nog steeds nodig.

## [0.17.0] — 2026-08-21

### Gewijzigd

- **De ronde loopt nu elke tien seconden in plaats van elke dertig.** Afstand,
  richting, ringen, trend en de stilstandbepaling volgen daardoor sneller.
  Die ronde leest alleen lokale toestanden en rekent wat door, dus er gaan
  geen extra verzoeken naar buiten.
- Nieuwe instelling **Verversingsinterval**, van vijf tot honderdtwintig
  seconden.
- De bewaarde reeksen zijn meegegroeid, zodat ze bij tien seconden nog steeds
  ruim een uur aan locatiepunten en een halfuur aan afstandsmetingen dekken.

### Ongewijzigd

De externe bronnen houden hun eigen ritme: weerparameters elk half uur,
neerslag elke vijf minuten, waarschuwingen elk kwartier. Die vaker bevragen
levert niets op, want ze verversen zelf niet sneller.

## [0.16.0] — 2026-08-21

Eerste versie die tijdens een echt onweer is nagelopen.

### Gerepareerd

- **Het dashboard mengde twee maatstaven.** De afstandstegel toonde de waarde
  van de Blitzortung-sensor, gemeten vanaf het vaste punt daar, terwijl de
  aankomsttijd rekende met de herberekende afstand vanaf jouw positie. Bij
  een verschil van 274 kilometer tussen die twee punten leverde dat een
  onweer op 44 km met een aankomsttijd van drie uur op.
- Nieuwe sensoren `sensor.stormchase_afstand` en `sensor.stormchase_azimut`
  met de herberekende waarden. Het dashboard gebruikt die nu, en valt alleen
  terug op de bronsensor als ze er niet zijn. Het attribuut `gemeten_via`
  laat zien welke van de twee je ziet.
- De tegel met het aantal inslagen toont nu onze eigen telling in plaats van
  de teller van de bron, zodat hij bij de afstanden ernaast hoort.
- **De neerslaggrafiek toonde 24 uur terug in plaats van 2 uur vooruit.**
  Apexcharts kijkt standaard achteruit, terwijl deze reeks in de toekomst
  ligt. Venster en startpunt staan nu goed.
- De aankomsttijd is een heel getal in plaats van 184.0, en boven de
  anderhalf uur wordt hij in uren getoond.

### Wat er tijdens het onweer goed ging

De herberekening werkte: 110 geo_location entiteiten, afstand en richting
bepaald vanaf de tracker in plaats van vanaf het vaste punt van Blitzortung.
De stilstanddetectie klopte, de regenmelding is verstuurd en alle bronnen
bleven foutloos.

## [0.15.0] — 2026-08-21

### Toegevoegd

- **Adres op het dashboard.** Een optionele adressensor, zoals de
  `geocoded_location` van de companion-app, wordt overgenomen als attribuut
  `adres` op `sensor.stormchase_actieve_locatie` en getoond op het dashboard.
  Coordinaten zeggen weinig; een plaatsnaam maakt in een oogopslag duidelijk
  waar de integratie naar kijkt.
- De config flow raadt de sensor op het achtervoegsel `_geocoded_location`,
  dus meestal hoef je niets in te vullen.
- De locatietegel verschijnt nu ook als je thuis bent, mits er een adres
  bekend is. Zonder adres blijft hij weg zolang je thuis bent, want dan voegt
  hij niets toe.

## [0.14.1] — 2026-08-21

### Gerepareerd

- **Onzinnige reissnelheid na het opstarten.** Zolang een device_tracker nog
  niet geladen is valt de locatie terug op je thuisadres. Zodra de tracker
  daarna verschijnt springt de positie, en die sprong werd als beweging
  gelezen: in de praktijk waarden van tienduizenden kilometers per uur, met
  als gevolg dat je onterecht als onderweg gold en geen meldingen kreeg.
  - Bij een wisseling van locatiebron wordt de reeks nu gewist.
  - Snelheden boven 400 km/u worden genegeerd, want die komen van een
    verspringende positie en niet van beweging. Vangt ook een foutieve
    GPS-fix midden in een sessie af.
- **Stilstaan vanaf het opstarten gold tien minuten als onderweg.** De
  nalooptijd is bedoeld om het stoplicht af te vangen na echt rijden. Ben je
  sinds de start nooit boven de drempel geweest, dan sta je gewoon stil.
- **Waarschuwingen bleven een kwartier op het verkeerde land staan.** De
  landbepaling werd bij het opstarten met de thuislocatie gedaan en pas bij
  de volgende ronde gecorrigeerd. Zodra de locatie bruikbaar wordt of meer
  dan een halve graad verschuift, wordt nu meteen opnieuw bepaald.

## [0.14.0] — 2026-08-21

### Gewijzigd

- **Onderweg wordt nu op snelheid bepaald, niet op afstand.** De vorige
  aanpak keek of je binnen een kilometer van je vorige positie bleef. Dat
  ging twee kanten op mis: stilstaan in de file telde als ter plaatse,
  terwijl een wandelaar die een blokje van iets meer dan een kilometer om
  ging als onderweg gold. Boven de ingestelde snelheid, standaard 30 km/u,
  ben je onderweg.
- Je telt pas weer als ter plaatse zodra je die drempel een tijd lang niet
  meer gehaald hebt, standaard tien minuten. Zo krijg je niet bij elk
  stoplicht een reeks meldingen.
- Levert je tracker zelf een snelheid, zoals de companion-app doet, dan
  wordt die gebruikt. Anders wordt de snelheid afgeleid uit de
  locatiepunten van de laatste drie minuten.
- Nieuwe instelling **Onderweg vanaf snelheid**.
- `binary_sensor.stormchase_onderweg` krijgt het attribuut `snelheid_kmh`,
  en de dashboardtegel toont die snelheid.

### Getest gedrag

Wandelen op 5 km/u en fietsen op 22 km/u tellen als ter plaatse. Rijden op
100 km/u niet, en na het parkeren duurt het precies tien minuten voordat de
meldingen weer doorkomen. Stilstaan in de file blijft onderweg.

## [0.13.0] — 2026-08-21

### Toegevoegd

- **Bliksemafstanden worden herberekend vanaf je eigen positie.** De
  Blitzortung-integratie rekent vanaf een vast punt dat je daar instelt; ben
  je ergens anders, dan klopt die afstand niet voor jou. De coordinaten in de
  attributen van de `geo_location` entiteiten zijn wel absoluut, dus daaruit
  wordt de juiste afstand en richting afgeleid.
  - Afstand, azimut, de drie ringen en het aantal markers komen dan allemaal
    uit die herberekening.
  - De naderingssnelheid rekent mee met dezelfde maatstaf, zodat de trend
    niet verspringt bij het omschakelen.
- Het attribuut `afstand_via` op `sensor.stormchase_actieve_locatie` laat
  zien welke bron actief is: `herberekend` of `sensor`.
- De waarschuwing over een afwijkend meetpunt verdwijnt zodra de
  herberekening actief is, want dan is het probleem opgelost.

### Waarom dit uitmaakt

Meet Blitzortung vanaf Lochem terwijl jij bij Trier staat, dan meldt de bron
onweer op 207 kilometer terwijl er een inslag op 6 kilometer ligt, en blijven
alle drie de ringen op nul staan.

### Voorwaarde

Dit werkt alleen als je Blitzortung-integratie `geo_location` entiteiten
aanmaakt met coordinaten in de attributen. Doet hij dat niet, dan blijft de
oude werkwijze gelden en blijven de afstanden gebonden aan het vaste punt.

## [0.12.1] — 2026-08-21

### Toegevoegd

- **Controle of beide integraties vanaf hetzelfde punt meten.** De
  Blitzortung-integratie heeft geen entiteit die haar positie toont, waardoor
  niet te zien was of de bliksemafstanden bij het getoonde weer horen. De
  instellingen van die integratie worden nu uitgelezen en de posities
  vergeleken.
- `sensor.stormchase_actieve_locatie` krijgt de attributen
  `blitzortung_meet_vanaf` en `afwijking_km`. Bij meer dan vijf kilometer
  verschil komt er een `let_op` bij en verschijnt er een tegel op het
  dashboard.
- Ook zichtbaar in de diagnostiek.

### Waarom dit ertoe doet

Volgt Stormchase je telefoon en Blitzortung nog je thuisadres, dan zie je
onweer op zeven kilometer terwijl dat zeven kilometer van huis is en niet van
waar je staat. Beide integraties moeten dezelfde locatiebron gebruiken.

## [0.12.0] — 2026-08-21

### Toegevoegd

- **Afstandsringen werken nu ook zonder geo_location.** Niet elke
  Blitzortung-installatie maakt per inslag een `geo_location` entiteit aan,
  en zonder die entiteiten bleven de drie ringen permanent op nul staan. De
  integratie houdt de inslagen nu zelf bij: elke keer dat de afstandssensor
  verspringt is dat een nieuwe inslag, en die worden geteld binnen een
  instelbaar tijdvenster.
- De telling gebeurt via een luisteraar op de afstandssensor in plaats van
  via de ophaalronde van dertig seconden, want bij een actieve bui komen er
  meerdere inslagen per minuut binnen.
- Nieuwe instelling **Tijdvenster voor de ringen**, standaard 120 minuten,
  zodat het aansluit op het venster van je Blitzortung-integratie.
- Elke ringsensor draagt het attribuut `telling_via`: `geo_location` als die
  entiteiten er zijn, `afstandssensor` bij de terugval, `geen` als er niets
  te tellen valt.

### Opmerking

`geo_location` blijft nauwkeuriger, want dat kent alle inslagen binnen de
radius. De terugval ziet alleen wat de afstandssensor toont, en die springt
naar de dichtstbijzijnde inslag; twee inslagen op vrijwel dezelfde afstand
tellen dan als een. Het geeft een goed beeld van de activiteit, maar geen
exact aantal.

## [0.11.0] — 2026-08-21

Meldingen over het weer op je eigen plek.

### Toegevoegd

- **Windmelding.** Bericht zodra de windstoten op je locatie boven de
  ingestelde drempel komen, standaard 60 km/u. De tekst schaalt mee: harde,
  krachtige of zware windstoten. Alleen bij de overgang, dus niet elk half
  uur opnieuw zolang het waait.
- `sensor.stormchase_windstoten` met de actuele windstoten.
- **Stilstanddetectie.** `binary_sensor.stormchase_onderweg` staat aan zolang
  je in beweging bent, en uit zodra je langer dan de ingestelde tijd binnen
  een kilometer van dezelfde plek blijft. Het attribuut
  `stil_sinds_minuten` laat zien hoe lang dat al zo is.
- **Meldingen over regen en wind wachten tot je ergens bent.** Standaard aan,
  met een venster van tien minuten. Tijdens het rijden is een bericht over
  regen hier alweer achterhaald voor je het leest.
- Op het dashboard een tegel met de windstoten en een die laat zien of je
  onderweg bent of ter plaatse, met de tijd erbij.

### Bewust niet gefilterd

Onweer binnen de waarschuwingsafstand en officiele weerwaarschuwingen komen
altijd door, ook onderweg. Die gaan over gevaar, en juist in de auto wil je
weten dat er onweer voor je ligt.

## [0.10.1] — 2026-08-21

### Gerepareerd

- **Dashboard vond de helft van de entiteiten niet.** Entiteiten die in
  verschillende versies zijn aangemaakt kunnen door elkaar lopen: de oudere
  zonder ruimtenaam in de entity-id, de nieuwere met. De strategie leidde een
  enkel voorvoegsel af en paste dat op alles toe, waardoor precies die ene
  groep wegviel. De vertaling gaat nu per entiteit, zonder gedeelde aanname.
  Langere namen worden eerst vervangen, zodat `stormchase_cape` niet het
  begin van `stormchase_cape_piek_12_uur` opeet.
- **Waarschuwingen bleven op het thuisland staan.** Bij het opstarten is een
  device_tracker soms nog niet geladen; de landbepaling viel dan terug op de
  thuislocatie en onthield dat. Zo'n voorlopige uitkomst wordt nu niet meer
  bewaard.

## [0.10.0] — 2026-08-21

### Gewijzigd

- **Kaarten passen zich aan de schermbreedte aan.** De strategie draait in de
  browser en leest de breedte uit. Onder de 700 pixels krijgen de kaarten een
  staande verhouding, waarbij de iRadar-kaart anderhalf keer zo hoog wordt als
  breed in plaats van een strookje. De kaartenkolom pakt op een telefoon
  bovendien de volle breedte.
- **Het zwaarweerblok staat er nu altijd**, ook bij nul. Juist het oplopen
  van rotatie- en hagelkans is wat je wil zien aankomen. Grijze iconen maken
  duidelijk dat er niets speelt.
- Windschering over 0-1 km en de Total Totals index staan er nu ook bij; het
  vriesniveau kleurt groen binnen het gunstige venster voor hagel.

### Toegevoegd

- **Blok "Alle waarden"** onderaan met elke entiteit die de integratie
  levert. Vangnet voor alles zonder eigen tegel, en nieuwe sensoren in een
  volgende versie verschijnen er vanzelf in. Uit te zetten met
  `alle_waarden: false` in de strategie-opties.
- Strategie-optie `map_ratio` om de verhouding van de kaarten zelf vast te
  zetten, ongeacht schermbreedte.

## [0.9.0] — 2026-08-21

Rotatie- en hagelkans.

### Wat dit wel en niet is

Rotatie en hagel worden **niet gedetecteerd**. Rotatie vaststellen vraagt
dopplerradar en hagel vraagt dual-polarisatie; die ruwe data publiceert geen
enkele vrij beschikbare bron. Wat hier is toegevoegd berekent of de
*omgeving* rotatie en hagel toelaat, zoals een stormjager dat 's ochtends uit
een sondering afleidt. Een hoge score betekent dat buien die zich vormen zich
zo kunnen gedragen, niet dat er nu iets draait.

### Toegevoegd

- `sensor.stormchase_rotatiekans`, het product van CAPE en de windschering
  over 0-6 km. Beide zijn nodig: zonder energie gebeurt er niets, zonder
  schering roteert een bui niet.
- `sensor.stormchase_hagelkans`, het product van CAPE, windschering en de
  hoogte van het vriesniveau. Ligt dat te hoog, dan smelt hagel voor hij de
  grond haalt; ligt het te laag, dan is de bui meestal te zwak.
- `sensor.stormchase_windschering_0_6_km` en `_0_1_km`, berekend als
  vectorverschil tussen de wind aan de grond en op 500 respectievelijk 850
  hPa. Draaiende wind levert schering op, ook bij gelijke snelheid, en dat
  draaien is wat een bui aan het roteren brengt.
- `sensor.stormchase_vriesniveau` en `sensor.stormchase_total_totals_index`.
- Beide kansen dragen hun opbouw als attribuut, zodat je kunt zien waar een
  getal vandaan komt.
- Op het dashboard verschijnt een blok met rotatie, hagel, schering en
  vriesniveau, maar alleen als er iets te melden valt.

### Gebruikte drempels

- Windschering 72 km/u over 0-6 km: klassieke grens waarboven supercellen
  mogelijk worden.
- CAPE 2000 J/kg voor rotatie, 2500 voor hagel.
- Vriesniveau tussen 2000 en 3500 meter is het gunstige venster voor hagel.
- Meldt het model zelf onweer met hagel, WMO-code 96 of 99, dan komt de
  hagelkans op minimaal 60 procent.

## [0.8.0] — 2026-08-21

### Toegevoegd

- **Diagnostiek.** Bij de integratie staat nu een knop *Diagnostische
  gegevens downloaden*. Het bestand bevat de instellingen, de actuele
  waarden van alle onderdelen en statistieken over hoe de externe bronnen
  zich hebben gedragen. Bedoeld om te delen bij een probleem.
- **Statistieken** die vanaf het opstarten worden bijgehouden:
  - Per bron het aantal geslaagde en mislukte ophaalrondes, het
    slaagpercentage, en de laatste foutmelding met tijdstip.
  - Welke neerslagbron er is gebruikt, Buienradar of Open-Meteo, en hoe
    vaak. Zo zie je of de terugval vaker aanslaat dan bedoeld.
  - Hoeveel events er zijn afgevuurd en hoeveel meldingen er zijn verstuurd
    of mislukt.
  - Bij de waarschuwingen: hoeveel er landelijk actief waren, hoeveel er na
    filtering overbleven en op welke namen is gefilterd.
  - De laatste zestig afstandsmetingen met de berekende naderingssnelheid,
    om achteraf te kunnen beoordelen of de trend klopte.
- Het diagnosebestand telt hoeveel `geo_location` markers er zijn en hoeveel
  daarvan bij het ingestelde patroon passen. Draaien er twee
  Blitzortung-integraties naast elkaar, dan is dat hier meteen zichtbaar.

### Privacy

Coordinaten worden afgerond tot twee decimalen, ongeveer een kilometer.
De gevolgde device_tracker, handmatige coordinaten en de namen van je
meldingsdiensten worden weggelaten.

## [0.7.1] — 2026-08-21

### Gerepareerd

- **Dashboard bleef leeg bij een apparaat in een ruimte.** Home Assistant zet
  de ruimtenaam voor de entity-id zodra je het apparaat aan een ruimte
  toewijst: `sensor.woonkamer_stormchase_cape` in plaats van
  `sensor.stormchase_cape`. De strategie ging uit van het tweede en vond
  daardoor niets. Het voorvoegsel wordt nu herkend en overal toegepast.
- **Waarschuwingen waren landelijk in plaats van lokaal.** Zonder regiofilter
  kwamen alle waarschuwingen van een heel land binnen, veertig stuks in het
  geval van Duitsland, en die konden over een gebied duizend kilometer
  verderop gaan. De landbepaling haalt nu ook de namen van je stad, streek en
  provincie op, en filtert de feed daarop terug naar je eigen omgeving. Een
  handmatig ingevuld regiofilter gaat nog steeds voor.
- Twee nieuwe attributen op `sensor.stormchase_waarschuwingsniveau`:
  `gefilterd_op` laat zien welke namen zijn gebruikt en `aantal_in_land`
  hoeveel er in het hele land actief zijn.

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

[0.35.0]: https://github.com/Roedie84/StormchaseNL/releases/tag/v0.35.0
[0.34.0]: https://github.com/Roedie84/StormchaseNL/releases/tag/v0.34.0
[0.33.1]: https://github.com/Roedie84/StormchaseNL/releases/tag/v0.33.1
[0.33.0]: https://github.com/Roedie84/StormchaseNL/releases/tag/v0.33.0
[0.32.1]: https://github.com/Roedie84/StormchaseNL/releases/tag/v0.32.1
[0.32.0]: https://github.com/Roedie84/StormchaseNL/releases/tag/v0.32.0
[0.31.1]: https://github.com/Roedie84/StormchaseNL/releases/tag/v0.31.1
[0.31.0]: https://github.com/Roedie84/StormchaseNL/releases/tag/v0.31.0
[0.30.1]: https://github.com/Roedie84/StormchaseNL/releases/tag/v0.30.1
[0.30.0]: https://github.com/Roedie84/StormchaseNL/releases/tag/v0.30.0
[0.29.1]: https://github.com/Roedie84/StormchaseNL/releases/tag/v0.29.1
[0.29.0]: https://github.com/Roedie84/StormchaseNL/releases/tag/v0.29.0
[0.28.0]: https://github.com/Roedie84/StormchaseNL/releases/tag/v0.28.0
[0.27.0]: https://github.com/Roedie84/StormchaseNL/releases/tag/v0.27.0
[0.26.1]: https://github.com/Roedie84/StormchaseNL/releases/tag/v0.26.1
[0.26.0]: https://github.com/Roedie84/StormchaseNL/releases/tag/v0.26.0
[0.25.3]: https://github.com/Roedie84/StormchaseNL/releases/tag/v0.25.3
[0.25.2]: https://github.com/Roedie84/StormchaseNL/releases/tag/v0.25.2
[0.25.1]: https://github.com/Roedie84/StormchaseNL/releases/tag/v0.25.1
[0.25.0]: https://github.com/Roedie84/StormchaseNL/releases/tag/v0.25.0
[0.24.3]: https://github.com/Roedie84/StormchaseNL/releases/tag/v0.24.3
[0.24.2]: https://github.com/Roedie84/StormchaseNL/releases/tag/v0.24.2
[0.24.1]: https://github.com/Roedie84/StormchaseNL/releases/tag/v0.24.1
[0.24.0]: https://github.com/Roedie84/StormchaseNL/releases/tag/v0.24.0
[0.23.2]: https://github.com/Roedie84/StormchaseNL/releases/tag/v0.23.2
[0.23.1]: https://github.com/Roedie84/StormchaseNL/releases/tag/v0.23.1
[0.23.0]: https://github.com/Roedie84/StormchaseNL/releases/tag/v0.23.0
[0.22.1]: https://github.com/Roedie84/StormchaseNL/releases/tag/v0.22.1
[0.22.0]: https://github.com/Roedie84/StormchaseNL/releases/tag/v0.22.0
[0.21.0]: https://github.com/Roedie84/StormchaseNL/releases/tag/v0.21.0
[0.20.3]: https://github.com/Roedie84/StormchaseNL/releases/tag/v0.20.3
[0.20.2]: https://github.com/Roedie84/StormchaseNL/releases/tag/v0.20.2
[0.20.1]: https://github.com/Roedie84/StormchaseNL/releases/tag/v0.20.1
[0.20.0]: https://github.com/Roedie84/StormchaseNL/releases/tag/v0.20.0
[0.19.0]: https://github.com/Roedie84/StormchaseNL/releases/tag/v0.19.0
[0.18.1]: https://github.com/Roedie84/StormchaseNL/releases/tag/v0.18.1
[0.18.0]: https://github.com/Roedie84/StormchaseNL/releases/tag/v0.18.0
[0.17.1]: https://github.com/Roedie84/StormchaseNL/releases/tag/v0.17.1
[0.17.0]: https://github.com/Roedie84/StormchaseNL/releases/tag/v0.17.0
[0.16.0]: https://github.com/Roedie84/StormchaseNL/releases/tag/v0.16.0
[0.15.0]: https://github.com/Roedie84/StormchaseNL/releases/tag/v0.15.0
[0.14.1]: https://github.com/Roedie84/StormchaseNL/releases/tag/v0.14.1
[0.14.0]: https://github.com/Roedie84/StormchaseNL/releases/tag/v0.14.0
[0.13.0]: https://github.com/Roedie84/StormchaseNL/releases/tag/v0.13.0
[0.12.1]: https://github.com/Roedie84/StormchaseNL/releases/tag/v0.12.1
[0.12.0]: https://github.com/Roedie84/StormchaseNL/releases/tag/v0.12.0
[0.11.0]: https://github.com/Roedie84/StormchaseNL/releases/tag/v0.11.0
[0.10.1]: https://github.com/Roedie84/StormchaseNL/releases/tag/v0.10.1
[0.10.0]: https://github.com/Roedie84/StormchaseNL/releases/tag/v0.10.0
[0.9.0]: https://github.com/Roedie84/StormchaseNL/releases/tag/v0.9.0
[0.8.0]: https://github.com/Roedie84/StormchaseNL/releases/tag/v0.8.0
[0.7.1]: https://github.com/Roedie84/StormchaseNL/releases/tag/v0.7.1
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
