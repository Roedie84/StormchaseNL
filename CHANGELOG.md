# Changelog

Alle noemenswaardige wijzigingen aan dit project staan hier.

Het formaat volgt [Keep a Changelog](https://keepachangelog.com/nl/1.1.0/),
en het project gebruikt [semantische versienummers](https://semver.org/lang/nl/).

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
