/**
 * Stormchase dashboard: het chase-commandocentrum.
 *
 * Dit bestand levert twee dingen:
 *
 *  1. De dashboardstrategie (custom:stormchase). Die bouwt bij elke
 *     paginalading een panel-view met daarin een enkele kaart, plus een tab
 *     met kaarten van derden en een tab met alle waarden.
 *  2. De kaart zelf: <stormchase-hud-card>. Een eigen element met Shadow DOM
 *     en eigen opmaak, zonder HACS-kaarten en zonder externe bestanden. Het
 *     zoekt de entiteiten zelf op (via het entiteitenregister, met de nette
 *     entity-id's als terugval) en tekent alleen het paneel opnieuw waarvan
 *     een relevante waarde veranderde.
 *
 * Gebruik in de onbewerkte configuratie van een dashboard:
 *
 *   strategy:
 *     type: custom:stormchase
 *
 * Alle opties zijn optioneel; zonder opties wordt alles automatisch bepaald.
 *
 * Let op: dit bestand bevat alleen ASCII. Bijzondere tekens staan als escape
 * in de broncode, omdat een editor met de verkeerde codering ze anders
 * verminkt en de module dan niets meer registreert.
 */

/* ------------------------------------------------------------------ */
/* Versie                                                              */
/* ------------------------------------------------------------------ */

/**
 * De versie waarmee dit script geladen is.
 *
 * Die zit in de query van de URL waarmee de browser het bestand ophaalde
 * (frontend.py zet er ?v=<versie>&t=<starttijd> achter). Zo is in de console
 * en onderaan het dashboard te zien of je het nieuwe script draait of nog
 * een oude uit de cache.
 */
const eigenVersie = () => {
  try {
    const tag = document.querySelector('script[src*="stormchase-strategy"]');
    if (tag) {
      const v = new URL(tag.src, location.href).searchParams.get("v");
      if (v) return v;
    }
    const bronnen = performance.getEntriesByType("resource") || [];
    for (const item of bronnen) {
      if (String(item.name).includes("stormchase-strategy")) {
        const v = new URL(item.name).searchParams.get("v");
        if (v) return v;
      }
    }
  } catch (e) {
    /* geen versie te achterhalen; geen reden om te stoppen */
  }
  return "onbekend";
};

const VERSIE = eigenVersie();

/* ------------------------------------------------------------------ */
/* Entiteiten                                                          */
/* ------------------------------------------------------------------ */

/**
 * Alle entiteiten die het dashboard kent.
 *
 * Per sleutel: domein, translation_key in het register en de nette
 * entity-id zoals die in een Nederlandstalige installatie ontstaat. Het
 * register gaat voor; dat werkt ook als de entity-id's Engels zijn of als
 * Home Assistant er een ruimtenaam voor zette.
 */
const ENTITEITEN = {
  afstand: ["sensor", "distance", "stormchase_afstand"],
  azimut: ["sensor", "azimuth", "stormchase_azimut"],
  nadering: ["sensor", "approach_speed", "stormchase_naderingssnelheid"],
  aankomst: ["sensor", "eta", "stormchase_aankomst"],
  celrichting: ["sensor", "cell_direction", "stormchase_celrichting"],
  celsnelheid: ["sensor", "cell_speed", "stormchase_celsnelheid"],
  passageafstand: ["sensor", "pass_distance", "stormchase_passageafstand"],
  passage: ["sensor", "pass_time", "stormchase_passage_over"],
  frequentie: ["sensor", "flash_rate", "stormchase_inslagfrequentie"],
  veilig: ["sensor", "safe_in", "stormchase_veilig_over"],
  trend: ["sensor", "trend", "stormchase_trend"],
  markers: ["sensor", "markers", "stormchase_actieve_markers"],
  cape: ["sensor", "cape", "stormchase_cape"],
  capePiek: ["sensor", "cape_peak", "stormchase_cape_piek_12_uur"],
  li: ["sensor", "lifted_index", "stormchase_lifted_index"],
  cin: ["sensor", "cin", "stormchase_convectieve_remming"],
  windstoten: ["sensor", "wind_gusts", "stormchase_windstoten"],
  schering6: ["sensor", "wind_shear_6km", "stormchase_windschering_0_6_km"],
  schering3: ["sensor", "wind_shear_3km", "stormchase_windschering_0_3_km"],
  schering1: ["sensor", "wind_shear_1km", "stormchase_windschering_0_1_km"],
  lpi: ["sensor", "lightning_potential", "stormchase_bliksempotentie"],
  updraft: ["sensor", "updraft", "stormchase_opwaartse_stroming"],
  wolkentop: ["sensor", "cloud_top", "stormchase_wolkentop"],
  hodograaf: ["sensor", "hodograph", "stormchase_draaiing_met_hoogte"],
  vriesniveau: ["sensor", "freezing_level", "stormchase_vriesniveau"],
  tt: ["sensor", "total_totals", "stormchase_total_totals_index"],
  regenStart: ["sensor", "rain_starts", "stormchase_regen_begint_over"],
  regenStopt: ["sensor", "rain_stops", "stormchase_regen_stopt_over"],
  regenBeeld: ["sensor", "rain_summary", "stormchase_regenbeeld"],
  regenIntensiteit: ["sensor", "rain_intensity", "stormchase_neerslagintensiteit"],
  regenPiek: ["sensor", "rain_peak", "stormchase_neerslagpiek_2_uur"],
  stoten: ["sensor", "meting_windstoten", "stormchase_windstoten_gemeten"],
  druk: ["sensor", "meting_luchtdruk", "stormchase_luchtdruk_gemeten"],
  druk1: ["sensor", "meting_druk_1u", "stormchase_luchtdrukverandering_per_uur"],
  druk3: ["sensor", "meting_druk_3u", "stormchase_luchtdrukverandering_per_3_uur"],
  meting: ["sensor", "meting", "stormchase_meting_weerstation"],
  potentie: ["sensor", "chase_potential", "stormchase_chase_potentie"],
  locatie: ["sensor", "location", "stormchase_actieve_locatie"],
  niveau: ["sensor", "alert_level", "stormchase_waarschuwingsniveau"],
  verwachting: ["sensor", "forecast", "stormchase_onweersverwachting"],
  overeenstemming: ["sensor", "model_agreement", "stormchase_modelovereenstemming"],
  bronstatus: ["sensor", "bronstatus", "stormchase_bronstatus"],
  ensemble: ["sensor", "ensemble", "stormchase_onweerskans_ensemble"],
  rotatie: ["sensor", "rotation", "stormchase_rotatiekans"],
  hagel: ["sensor", "hail", "stormchase_hagelkans"],
  nabij: ["binary_sensor", "nearby", "stormchase_onweer_nabij"],
  nadert: ["binary_sensor", "approaching", "stormchase_onweer_nadert"],
  regenVerwacht: ["binary_sensor", "rain_expected", "stormchase_regen_verwacht"],
  waarschuwing: ["binary_sensor", "alert_active", "stormchase_weerwaarschuwing"],
  onderweg: ["binary_sensor", "moving", "stormchase_onderweg"],
  schuilen: ["binary_sensor", "shelter", "stormchase_schuilen"],
  onweerGemeten: ["binary_sensor", "meting_onweer", "stormchase_onweer_gemeten_bij_station"],
  hagelGemeten: ["binary_sensor", "meting_hagel", "stormchase_hagel_gemeten_bij_station"],
  meldingen: ["switch", "notifications", "stormchase_meldingen"],
  radar: ["image", "radar", "stormchase_radar"],
  vooruitblik: ["image", "radar_vooruitblik", "stormchase_radar_vooruitblik"],
  weer: ["weather", null, "stormchase"],
};

const DOMEINEN = ["sensor", "binary_sensor", "switch", "weather", "image"];
const ONBRUIKBAAR = ["unknown", "unavailable", "none", ""];

/**
 * Zoek bij elke sleutel de echte entity-id.
 *
 * Eerst het register (platform stormchase plus translation_key), dan de
 * nette id, dan dezelfde id met iets ervoor (een ruimtenaam). De ringsensoren
 * hebben geen translation_key; die worden op hun id herkend.
 */
const zoekEntiteiten = (hass, config) => {
  const ids = {};
  const ringen = [];
  const register = hass.entities || {};
  const perSleutel = {};

  for (const item of Object.values(register)) {
    if (!item || item.platform !== "stormchase") continue;
    const id = item.entity_id;
    const domein = id.slice(0, id.indexOf("."));
    if (item.translation_key) {
      perSleutel[`${domein}|${item.translation_key}`] = id;
    } else if (domein === "weather") {
      perSleutel["weather|"] = id;
    }
  }

  // Nette id's naar echte, voor als het register ontbreekt of onvolledig is
  const netjes = {};
  for (const id of Object.keys(hass.states)) {
    const punt = id.indexOf(".");
    const domein = id.slice(0, punt);
    if (!DOMEINEN.includes(domein)) continue;
    const naam = id.slice(punt + 1);
    const positie = naam.indexOf("stormchase");
    if (positie === -1) continue;
    const net = `${domein}.${naam.slice(positie)}`;
    if (!netjes[net]) netjes[net] = id;

    const ring = /inslagen_binnen_(\d+)/.exec(naam);
    if (domein === "sensor" && ring) {
      ringen.push({ id, km: parseInt(ring[1], 10) || 0 });
    }
  }

  for (const [sleutel, [domein, tk, net]] of Object.entries(ENTITEITEN)) {
    const viaRegister = perSleutel[`${domein}|${tk || ""}`];
    if (viaRegister && hass.states[viaRegister]) {
      ids[sleutel] = viaRegister;
      continue;
    }
    const nette = `${domein}.${net}`;
    if (hass.states[nette]) ids[sleutel] = nette;
    else if (netjes[nette]) ids[sleutel] = netjes[nette];
  }

  // Afstand en richting: onze eigen waarden gaan voor, want die zijn
  // herberekend vanaf jouw positie. Anders die van Blitzortung zelf.
  const raad = (domein, achtervoegsel) =>
    Object.keys(hass.states).find(
      (id) => id.startsWith(`${domein}.`) && id.endsWith(achtervoegsel)
    );
  if (config.distance_entity) ids.afstand = config.distance_entity;
  else if (!bruikbaar(hass.states[ids.afstand])) {
    ids.afstand = raad("sensor", "_lightning_distance") || ids.afstand;
  }
  if (config.azimuth_entity) ids.azimut = config.azimuth_entity;
  else if (!bruikbaar(hass.states[ids.azimut])) {
    ids.azimut = raad("sensor", "_lightning_azimuth") || ids.azimut;
  }
  if (config.counter_entity) ids.markers = config.counter_entity;

  ringen.sort((a, b) => a.km - b.km);
  return { ids, ringen };
};

/* ------------------------------------------------------------------ */
/* Kleine hulpjes                                                      */
/* ------------------------------------------------------------------ */

const bruikbaar = (s) => !!s && !ONBRUIKBAAR.includes(String(s.state));
const onbeschikbaar = (s) => !!s && s.state === "unavailable";

const getal = (s) => {
  if (!bruikbaar(s)) return null;
  const v = parseFloat(s.state);
  return Number.isFinite(v) ? v : null;
};

const attr = (s, naam) => (s && s.attributes ? s.attributes[naam] : undefined);

const esc = (tekst) =>
  String(tekst == null ? "" : tekst)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");

/* ---- rustig scrollen (0.51.1) ----
   Op mobiel (vooral iOS, dat geen scroll anchoring kent) verspringt de pagina
   als een paneel tijdens het scrollen opnieuw wordt opgebouwd en daarbij een
   fractie van hoogte verandert. Daarom: tijdens aanraken en scrollen niets
   tekenen, en pas kort na het loslaten bijwerken. */
const SCROLL = { tot: 0, aan: false, klaar: false };
const volgScroll = () => {
  if (SCROLL.klaar || typeof window === "undefined") return;
  SCROLL.klaar = true;
  const opt = { passive: true, capture: true };
  const rust = (ms) => () => {
    SCROLL.tot = Math.max(SCROLL.tot, Date.now() + ms);
  };
  window.addEventListener("scroll", rust(400), opt);
  window.addEventListener("wheel", rust(400), opt);
  window.addEventListener("touchmove", rust(400), opt);
  window.addEventListener("touchstart", () => {
    SCROLL.aan = true;
    rust(400)();
  }, opt);
  const los = () => {
    SCROLL.aan = false;
    rust(500)();
  };
  window.addEventListener("touchend", los, opt);
  window.addEventListener("touchcancel", los, opt);
};
const scrolltNog = () => SCROLL.aan || Date.now() < SCROLL.tot;

const MIN = "\u2212";
const STREEP = "\u2014";
const PUNT = " \u00b7 ";

/** Getal op z'n Nederlands, met een echte min. */
const fmt = (v, dec = 0) => {
  if (v == null || v === "" || !Number.isFinite(Number(v))) return STREEP;
  let n = Number(v);
  if (Math.abs(n) < 0.5 * Math.pow(10, -dec)) n = 0;
  return n
    .toLocaleString("nl-NL", {
      minimumFractionDigits: dec,
      maximumFractionDigits: dec,
    })
    .replace("-", MIN);
};

/** Met teken ervoor: +1,2 of -1,8. */
const fmtTeken = (v, dec = 0) => {
  if (v == null || !Number.isFinite(Number(v))) return STREEP;
  const n = Number(v);
  const tekst = fmt(Math.abs(n), dec);
  if (tekst === fmt(0, dec)) return tekst;
  return (n > 0 ? "+" : MIN) + tekst;
};

/** Eerste letter hoofdletter, ook bij "ij". */
const hoofd = (tekst) => {
  const t = String(tekst || "");
  if (!t) return "";
  if (t.slice(0, 2).toLowerCase() === "ij") return "IJ" + t.slice(2);
  return t[0].toUpperCase() + t.slice(1);
};

const KOMPASROOS = [
  "N", "NNO", "NO", "ONO", "O", "OZO", "ZO", "ZZO",
  "Z", "ZZW", "ZW", "WZW", "W", "WNW", "NW", "NNW",
];
const kompas = (graden) =>
  graden == null || !Number.isFinite(Number(graden))
    ? null
    : KOMPASROOS[Math.round((((Number(graden) % 360) + 360) % 360) / 22.5) % 16];

const alsDatum = (waarde) => {
  if (waarde == null || waarde === "") return null;
  const d =
    typeof waarde === "number"
      ? new Date(waarde < 1e12 ? waarde * 1000 : waarde)
      : new Date(waarde);
  return Number.isNaN(d.getTime()) ? null : d;
};

const klokTijd = (waarde) => {
  const d = alsDatum(waarde);
  return d
    ? d.toLocaleTimeString("nl-NL", { hour: "2-digit", minute: "2-digit" })
    : null;
};

/** "3 min geleden", "2 u geleden". */
const geleden = (waarde) => {
  const d = alsDatum(waarde);
  if (!d) return null;
  const min = Math.max(0, Math.round((Date.now() - d.getTime()) / 60000));
  if (min < 1) return "zojuist";
  if (min < 60) return `${min} min geleden`;
  const uur = Math.round(min / 60);
  if (uur < 48) return `${uur} u geleden`;
  return `${Math.round(uur / 24)} d geleden`;
};

/** "nog 3 u 20 min", voor een eindtijd. */
const nogTijd = (waarde) => {
  const d = alsDatum(waarde);
  if (!d) return "";
  const min = Math.round((d.getTime() - Date.now()) / 60000);
  if (min <= 0) return "verlopen";
  if (min < 60) return `nog ${min} min`;
  return `nog ${Math.floor(min / 60)} u${min % 60 ? " " + (min % 60) + " min" : ""}`;
};

/** "begonnen" of "begint over 40 min", voor een begintijd. */
const beginTekst = (waarde) => {
  const d = alsDatum(waarde);
  if (!d) return "";
  if (d.getTime() <= Date.now()) return "begonnen";
  return "begint " + nogTijd(waarde).replace("nog ", "over ");
};

/* Kleuren per waarschuwingsniveau, overal hetzelfde. */
const NIVEAU_KLEUR = {
  groen: "var(--groen)",
  geel: "var(--geel)",
  oranje: "var(--oranje)",
  rood: "var(--rood)",
};
const niveauKleur = (n) => NIVEAU_KLEUR[n] || "var(--tekst3)";

/** Kleur bij oplopende drempels: [geel, oranje, rood]. */
const drempelNiveau = (v, [geel, oranje, rood]) => {
  if (v == null) return "geen";
  if (v >= rood) return "rood";
  if (v >= oranje) return "oranje";
  if (v >= geel) return "geel";
  return "groen";
};

/** Beaufort uit m/s, voor als de bron hem niet meelevert. */
const BFT_GRENZEN = [0.3, 1.6, 3.4, 5.5, 8.0, 10.8, 13.9, 17.2, 20.8, 24.5, 28.5, 32.7];
const beaufort = (ms) => {
  if (ms == null || !Number.isFinite(Number(ms))) return null;
  let b = 0;
  while (b < BFT_GRENZEN.length && Number(ms) >= BFT_GRENZEN[b]) b += 1;
  return b;
};

/* ------------------------------------------------------------------ */
/* Iconen: eigen SVG, geen externe bestanden                           */
/* ------------------------------------------------------------------ */

const ICOON = {
  flits: '<path d="M13 2 4 14h6l-1 8 9-12h-6z"/>',
  radar:
    '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/>' +
    '<path d="M12 12 18.5 5.5"/><circle cx="12" cy="12" r="1.2" fill="currentColor"/>',
  meter:
    '<path d="M4 17a8 8 0 1 1 16 0"/><path d="M12 17l4.5-6"/>' +
    '<path d="M4 20h16"/>',
  waarschuwing:
    '<path d="M12 3 2 20h20z"/><path d="M12 10v4.5"/><path d="M12 17.2v.3"/>',
  station:
    '<path d="M12 3v18"/><path d="M8 21h8"/><path d="M12 6l6 2-6 2"/>' +
    '<path d="M12 12h4"/>',
  druppel: '<path d="M12 3c-3.5 5-6 8.2-6 11a6 6 0 0 0 12 0c0-2.8-2.5-6-6-11z"/>',
  klok: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3.5 2"/>',
  server:
    '<rect x="4" y="4" width="16" height="6" rx="1.5"/>' +
    '<rect x="4" y="14" width="16" height="6" rx="1.5"/>' +
    '<path d="M8 7h.01M8 17h.01"/>',
  pin: '<path d="M12 21s-6.5-6.1-6.5-11a6.5 6.5 0 0 1 13 0c0 4.9-6.5 11-6.5 11z"/><circle cx="12" cy="10" r="2.3"/>',
  auto:
    '<path d="M4 16v-4l2-5h12l2 5v4"/><path d="M3 16h18v3H3z"/>' +
    '<circle cx="7.5" cy="16" r="1.2"/><circle cx="16.5" cy="16" r="1.2"/>',
  bel: '<path d="M6 16V11a6 6 0 0 1 12 0v5l2 2H4z"/><path d="M10 20a2 2 0 0 0 4 0"/>',
  huis: '<path d="M3 11 12 4l9 7"/><path d="M5 10v10h14V10"/><path d="M10 20v-5h4v5"/>',
};

const icoon = (naam, klasse = "ic") =>
  `<svg class="${klasse}" viewBox="0 0 24 24" fill="none" stroke="currentColor" ` +
  `stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">` +
  `${ICOON[naam] || ""}</svg>`;

/* Weersymbolen voor de uurstrip, eveneens zelf getekend. */
const WOLK =
  '<path d="M9.5 23h13a5 5 0 0 0 .7-9.95A7 7 0 0 0 10.4 12a5.5 5.5 0 0 0-.9 11z" ' +
  'fill="#9aa6c9" stroke="none"/>';
const ZON_KLEIN =
  '<circle cx="11" cy="11" r="4.5" fill="#ffc94d" stroke="none"/>' +
  '<path d="M11 2.5v2M11 17.5v2M2.5 11h2M17.5 11h2M5 5l1.4 1.4M15.6 15.6 17 17M5 17l1.4-1.4M15.6 6.4 17 5" stroke="#ffc94d"/>';
const DRUPPELS = (n) => {
  let uit = "";
  for (let i = 0; i < n; i += 1) {
    const x = 11 + i * (12 / Math.max(n - 1, 1));
    uit += `<path d="M${x} 25.5l-1.4 3.5" stroke="#5aa9ff"/>`;
  }
  return uit;
};
const BOUT = '<path d="M17.5 19 13.5 25h3.2l-1.4 5 5.4-7h-3.3l1.6-4z" fill="#ffd43b" stroke="none"/>';

const WEERICOON = {
  sunny:
    '<circle cx="16" cy="16" r="6" fill="#ffc94d" stroke="none"/>' +
    '<path d="M16 3.5v3M16 25.5v3M3.5 16h3M25.5 16h3M7.2 7.2l2.1 2.1M22.7 22.7l2.1 2.1M7.2 24.8l2.1-2.1M22.7 9.3l2.1-2.1" stroke="#ffc94d"/>',
  "clear-night":
    '<path d="M20.5 5.5a10 10 0 1 0 6 15.6A8.5 8.5 0 0 1 20.5 5.5z" fill="#c9d3ff" stroke="none"/>',
  partlycloudy: ZON_KLEIN + WOLK,
  cloudy: WOLK,
  rainy: WOLK + DRUPPELS(3),
  pouring: WOLK + DRUPPELS(5),
  lightning: WOLK + BOUT,
  "lightning-rainy": WOLK + BOUT + '<path d="M11 25.5l-1.4 3.5M24 25.5l-1.4 3.5" stroke="#5aa9ff"/>',
  fog: '<path d="M6 12h20M4 17h24M7 22h18" stroke="#9aa6c9"/>',
  hail: WOLK + '<circle cx="12" cy="27" r="1.3" fill="#dfe8ff"/><circle cx="17" cy="29" r="1.3" fill="#dfe8ff"/><circle cx="22" cy="27" r="1.3" fill="#dfe8ff"/>',
  snowy: WOLK + '<path d="M12 26v3M10.6 27.5h2.8M20 26v3M18.6 27.5h2.8" stroke="#dfe8ff"/>',
  "snowy-rainy": WOLK + '<path d="M12 26v3M10.6 27.5h2.8" stroke="#dfe8ff"/><path d="M21 25.5l-1.4 3.5" stroke="#5aa9ff"/>',
  windy: '<path d="M4 12h15a3.5 3.5 0 1 0-3.5-3.5M4 17h21a3.5 3.5 0 1 1-3.5 3.5M4 22h10" stroke="#9aa6c9"/>',
  exceptional: '<path d="M16 4 3 27h26z" fill="#ff922b" stroke="none"/><path d="M16 12v7M16 22.5v.5" stroke="#1a1a2e"/>',
};
WEERICOON["windy-variant"] = WEERICOON.windy;

const weerIcoon = (conditie) =>
  `<svg class="weer-ic" viewBox="0 0 32 32" fill="none" stroke-width="1.8" ` +
  `stroke-linecap="round" aria-hidden="true">${WEERICOON[conditie] || WOLK}</svg>`;

const CONDITIE_TEKST = {
  sunny: "Zonnig",
  "clear-night": "Helder",
  partlycloudy: "Half bewolkt",
  cloudy: "Bewolkt",
  rainy: "Regen",
  pouring: "Zware regen",
  lightning: "Onweer",
  "lightning-rainy": "Onweer met regen",
  fog: "Mist",
  hail: "Hagel",
  snowy: "Sneeuw",
  "snowy-rainy": "Natte sneeuw",
  windy: "Winderig",
  "windy-variant": "Winderig",
  exceptional: "Uitzonderlijk",
};

/* ------------------------------------------------------------------ */
/* Bouwstenen                                                          */
/* ------------------------------------------------------------------ */

/** Paneelkop met titel en eventueel kenmerken rechts. */
const paneelKop = (ic, titel, rechts = "") =>
  `<div class="ph">${icoon(ic)}<h2>${esc(titel)}</h2>` +
  `<div class="ph-r">${rechts}</div></div>`;

const chip = (tekst, klasse = "") =>
  tekst ? `<span class="chip ${klasse}">${tekst}</span>` : "";

/** Waarde, of een streepje; gedimd als de entiteit onbeschikbaar is. */
const waardeHtml = (s, dec = 0, eenheid = "") => {
  const v = getal(s);
  if (v == null) {
    const titel = onbeschikbaar(s) ? "niet beschikbaar" : "nog geen waarde";
    return `<span class="leeg" title="${titel}">${STREEP}</span>`;
  }
  return `${fmt(v, dec)}${eenheid ? `<small>${eenheid}</small>` : ""}`;
};

/**
 * Horizontale balk met drempelstreepjes.
 *
 * min/max bepalen de schaal; omgekeerd betekent dat lagere waarden meer
 * vullen (Lifted Index). De streepjes laten zien waar het spannend wordt.
 */
const balk = ({ v, min, max, drempels = [], kleur, omgekeerd = false }) => {
  let deel = 0;
  if (v != null) {
    deel = omgekeerd ? (max - v) / (max - min) : (v - min) / (max - min);
  }
  deel = Math.max(0, Math.min(1, deel));
  const streepjes = drempels
    .map((d) => {
      const p = omgekeerd ? (max - d) / (max - min) : (d - min) / (max - min);
      return `<i style="left:${(Math.max(0, Math.min(1, p)) * 100).toFixed(1)}%"></i>`;
    })
    .join("");
  return (
    `<div class="balk" role="presentation"><b style="width:${(deel * 100).toFixed(1)}%;` +
    `background:${kleur}"></b>${streepjes}</div>`
  );
};

/** Ronde meter voor percentages. */
const ring = (pct, kleur, grootte = 92) => {
  const r = 38;
  const omtrek = 2 * Math.PI * r;
  const deel = Math.max(0, Math.min(100, pct || 0)) / 100;
  return (
    `<svg class="ring" width="${grootte}" height="${grootte}" viewBox="0 0 92 92" role="img" ` +
    `aria-label="${pct == null ? "onbekend" : Math.round(pct) + " procent"}">` +
    `<circle cx="46" cy="46" r="${r}" fill="none" stroke="rgba(255,255,255,.08)" stroke-width="8"/>` +
    `<circle cx="46" cy="46" r="${r}" fill="none" stroke="${kleur}" stroke-width="8" ` +
    `stroke-linecap="round" stroke-dasharray="${(omtrek * deel).toFixed(1)} ${omtrek.toFixed(1)}" ` +
    `transform="rotate(-90 46 46)"/>` +
    `<text x="46" y="52" text-anchor="middle" class="ring-t">${pct == null ? STREEP : Math.round(pct)}` +
    `<tspan class="ring-p">%</tspan></text></svg>`
  );
};

/**
 * Kompasroos met de afstandsringen en de dichtstbijzijnde inslag.
 *
 * Ligt de inslag buiten de buitenste ring, dan staat hij op de rand met een
 * open rondje. De pijl bij de inslag wijst waar de cel heen trekt.
 */
const kompasroos = ({ az, km, ringen, celGraden, kleur }) => {
  const c = 110;
  const R = 84;
  const kms = ringen.length ? ringen.map((r) => r.km) : [10, 25, 50];
  const maxKm = Math.max(...kms, 1);
  let uit =
    `<svg class="kompas" viewBox="0 0 220 220" role="img" aria-label="Richting en afstand van de dichtstbijzijnde inslag">` +
    `<defs><radialGradient id="kg" cx="50%" cy="50%" r="50%">` +
    `<stop offset="0%" stop-color="rgba(90,110,255,.18)"/><stop offset="100%" stop-color="rgba(90,110,255,0)"/>` +
    `</radialGradient></defs>` +
    `<circle cx="${c}" cy="${c}" r="${R + 14}" fill="url(#kg)"/>`;

  for (const k of kms) {
    const r = R * Math.sqrt(k / maxKm);
    uit +=
      `<circle cx="${c}" cy="${c}" r="${r.toFixed(1)}" fill="none" stroke="rgba(170,185,255,.22)" ` +
      `stroke-dasharray="${k === maxKm ? "none" : "2 4"}"/>` +
      `<text x="${c + 3}" y="${(c - r + 11).toFixed(1)}" class="k-ring">${k}</text>`;
  }
  for (let g = 0; g < 360; g += 15) {
    const lang = g % 90 === 0 ? 9 : g % 45 === 0 ? 6 : 3;
    const a = (g * Math.PI) / 180;
    const x1 = c + Math.sin(a) * (R + 4);
    const y1 = c - Math.cos(a) * (R + 4);
    const x2 = c + Math.sin(a) * (R + 4 + lang);
    const y2 = c - Math.cos(a) * (R + 4 + lang);
    uit += `<line x1="${x1.toFixed(1)}" y1="${y1.toFixed(1)}" x2="${x2.toFixed(1)}" y2="${y2.toFixed(1)}" stroke="rgba(200,210,255,.45)"/>`;
  }
  const letters = [["N", 0], ["O", 90], ["Z", 180], ["W", 270]];
  for (const [l, g] of letters) {
    const a = (g * Math.PI) / 180;
    const x = c + Math.sin(a) * (R + 22);
    const y = c - Math.cos(a) * (R + 22) + 4;
    uit += `<text x="${x.toFixed(1)}" y="${y.toFixed(1)}" text-anchor="middle" class="k-l${l === "N" ? " k-n" : ""}">${l}</text>`;
  }
  uit += `<circle cx="${c}" cy="${c}" r="3.5" fill="#e7eaff"/>`;

  if (az != null && km != null) {
    const buiten = km > maxKm;
    const r = Math.sqrt(Math.min(km / maxKm, 1)) * R;
    const a = (az * Math.PI) / 180;
    const x = c + Math.sin(a) * r;
    const y = c - Math.cos(a) * r;
    uit +=
      `<line x1="${c}" y1="${c}" x2="${x.toFixed(1)}" y2="${y.toFixed(1)}" stroke="${kleur}" stroke-width="1.5" stroke-dasharray="3 3"/>`;
    if (celGraden != null) {
      const b = (celGraden * Math.PI) / 180;
      const x2 = x + Math.sin(b) * 26;
      const y2 = y - Math.cos(b) * 26;
      const px = Math.sin(b);
      const py = -Math.cos(b);
      const kx1 = x2 - px * 7 + py * 4;
      const ky1 = y2 - py * 7 - px * 4;
      const kx2 = x2 - px * 7 - py * 4;
      const ky2 = y2 - py * 7 + px * 4;
      uit +=
        `<line x1="${x.toFixed(1)}" y1="${y.toFixed(1)}" x2="${x2.toFixed(1)}" y2="${y2.toFixed(1)}" stroke="#e7eaff" stroke-width="2"/>` +
        `<path d="M${x2.toFixed(1)} ${y2.toFixed(1)}L${kx1.toFixed(1)} ${ky1.toFixed(1)}L${kx2.toFixed(1)} ${ky2.toFixed(1)}z" fill="#e7eaff"/>`;
    }
    uit +=
      `<circle class="puls" cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="9" fill="none" stroke="${kleur}"/>` +
      `<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="5.5" fill="${buiten ? "none" : kleur}" stroke="${kleur}" stroke-width="2"/>`;
  }
  return uit + "</svg>";
};

/** Kleur bij neerslagintensiteit, zoals op een radarbeeld. */
const regenKleur = (mm) => {
  if (mm >= 10) return "#ff4d5e";
  if (mm >= 5) return "#ff922b";
  if (mm >= 2) return "#ffd43b";
  if (mm >= 0.5) return "#3d8bff";
  return "#7cc4ff";
};

/**
 * Staafgrafiek van de neerslag in de komende twee uur.
 *
 * De SVG rekt mee met de breedte (preserveAspectRatio none); de labels staan
 * daarom als HTML ernaast, anders worden ze op een telefoon platgedrukt.
 */
const neerslagGrafiek = (reeks, startOver) => {
  const B = 600;
  const H = 150;
  const punten = reeks
    .filter((p) => p && Number.isFinite(Number(p.minuten)))
    .filter((p) => Number(p.minuten) >= 0 && Number(p.minuten) <= 120);
  const hoogst = Math.max(0, ...punten.map((p) => Number(p.mm_per_uur) || 0));
  const schaal = hoogst <= 2 ? 2 : hoogst <= 5 ? 5 : hoogst <= 10 ? 10 : Math.ceil(hoogst / 10) * 10;
  const stap = punten.length > 1 ? 120 / (punten.length - 1) : 5;
  const vakken = 120 / stap + 1;
  const vak = B / vakken;
  const bw = vak * 0.72;
  const x = (m) => (m / stap) * vak + vak / 2;
  const y = (mm) => H - (Math.min(mm, schaal) / schaal) * H;

  let svg = `<svg class="grafiek" viewBox="0 0 ${B} ${H}" preserveAspectRatio="none" aria-hidden="true">`;
  for (const f of [0.5, 1]) {
    svg += `<line x1="0" x2="${B}" y1="${(H - f * H).toFixed(1)}" y2="${(H - f * H).toFixed(1)}" class="g-lijn" vector-effect="non-scaling-stroke"/>`;
  }
  for (const p of punten) {
    const mm = Number(p.mm_per_uur) || 0;
    if (mm <= 0) continue;
    const yy = Math.min(y(mm), H - 2);
    svg += `<rect x="${(x(Number(p.minuten)) - bw / 2).toFixed(1)}" y="${yy.toFixed(1)}" width="${bw.toFixed(1)}" height="${(H - yy).toFixed(1)}" fill="${regenKleur(mm)}"/>`;
  }
  let start = "";
  if (startOver != null && startOver > 0 && startOver <= 120) {
    const xs = x(startOver);
    svg += `<line x1="${xs.toFixed(1)}" x2="${xs.toFixed(1)}" y1="0" y2="${H}" class="g-start" vector-effect="non-scaling-stroke"/>`;
    start = `<span class="g-start-t" style="left:${((xs / B) * 100).toFixed(1)}%">start</span>`;
  }
  svg += `<line x1="0" x2="${B}" y1="${H}" y2="${H}" class="g-basis" vector-effect="non-scaling-stroke"/></svg>`;

  const yas = [1, 0.5, 0]
    .map((f) => `<span style="top:${((1 - f) * 100).toFixed(0)}%">${fmt(schaal * f, schaal * f < 1 && f > 0 ? 1 : 0)}</span>`)
    .join("");
  const xas = [0, 30, 60, 90, 120]
    .map((m) => `<span style="left:${((x(m) / B) * 100).toFixed(1)}%">${m === 0 ? "nu" : "+" + m}</span>`)
    .join("");
  return (
    `<div class="gwrap" role="img" aria-label="Neerslag per vijf minuten, komende twee uur, schaal tot ${fmt(schaal)} mm per uur">` +
    `<div class="g-y">${yas}</div><div class="g-plot">${svg}${start}</div>` +
    `<div class="g-x">${xas}</div><div class="g-eenheid">mm/u</div></div>`
  );
};

/* Namen van gegevensbronnen in kenmerken. */
const BRONLABEL = { knmi: "KNMI", buienradar: "Buienradar", open_meteo: "Open-Meteo", "open-meteo": "Open-Meteo" };

/* Vriendelijke namen voor de bronnen in de bronstatus. */
const BRONNAAM = {
  open_meteo: "Open-Meteo",
  buienradar: "Buienradar",
  meteoalarm: "MeteoAlarm",
  geocodering: "Geocodering",
  icon_d2: "ICON-D2",
  lifted_index: "Lifted Index",
  ensemble: "Ensemble",
  ensemble_leden: "Ensembleleden",
  meting: "Weerstation",
  radar: "Radar",
  knmi_waarschuwingen: "KNMI codes",
  knmi_verwachting: "KNMI weer",
  knmi_nowcast: "KNMI nowcast",
  knmi_edr: "KNMI EDR",
  knmi_wms: "KNMI WMS",
};

/** Toestand van een bron: ok, traag, fout of ongebruikt. */
const bronToestand = (naam, info, haperend) => {
  if (haperend.includes(naam)) return "fout";
  if (!info) return "ongebruikt";
  if (!(info.gelukt || info.mislukt)) return "ongebruikt";
  if (info.afgeremd || info.herkansing || (info.op_rij_mislukt || 0) > 0) return "traag";
  return "ok";
};

const pushTekst = (push) => {
  if (!push) return null;
  const status = push.status || "onbekend";
  if (status === "verbonden") return ["live", "ok"];
  if (status === "verbinden") return ["verbinden", "traag"];
  if (status === "niet gestart" || status === "gestopt") return [status, "ongebruikt"];
  return [status, "fout"];
};

/* ------------------------------------------------------------------ */
/* Opmaak                                                              */
/* ------------------------------------------------------------------ */

const STIJL = `
:host {
  display: block;
  min-height: 100%;
  --bg0: #070914;
  --bg1: #0d1026;
  --bg2: #151937;
  --paneel: rgba(20, 24, 52, .58);
  --paneel2: rgba(12, 14, 34, .66);
  --rand: rgba(165, 180, 255, .13);
  --rand2: rgba(165, 180, 255, .22);
  --tekst: #eef0ff;
  --tekst2: #b3bade;
  --tekst3: #8189b3;
  --groen: #34d399;
  --geel: #facc15;
  --oranje: #fb923c;
  --rood: #fb4d65;
  --blauw: #60a5fa;
  --cyaan: #38d7f0;
  --violet: #a78bfa;
  --r: 16px;
  font-family: system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  color: var(--tekst);
  -webkit-font-smoothing: antialiased;
}
* { box-sizing: border-box; }
.root {
  position: relative;
  isolation: isolate;
  min-height: 100vh;
  overflow: hidden;
  background:
    radial-gradient(1100px 620px at 78% -8%, rgba(84, 64, 196, .38), transparent 62%),
    radial-gradient(900px 560px at -6% 26%, rgba(28, 88, 168, .26), transparent 60%),
    radial-gradient(800px 600px at 50% 110%, rgba(60, 30, 120, .30), transparent 60%),
    linear-gradient(180deg, var(--bg0) 0%, var(--bg1) 42%, var(--bg2) 100%);
}
.bg { position: absolute; inset: 0; z-index: -1; pointer-events: none; overflow: hidden; }
.bg svg { position: absolute; inset: 0; width: 100%; height: 100%; }
.bg .wolken { opacity: .55; mix-blend-mode: screen; }
.bg .raster { opacity: 1; }
.gloed {
  position: absolute; inset: -10% -10% auto -10%; height: 70%;
  background: radial-gradient(60% 55% at 70% 18%, rgba(196, 180, 255, .55), rgba(120, 110, 255, .12) 45%, transparent 70%);
  opacity: 0;
}
.root.flits .gloed { animation: flits 7.5s infinite; }
.root.flits-nabij .gloed { animation: flits 4.2s infinite; }
@keyframes flits {
  0%, 86%, 100% { opacity: 0; }
  87% { opacity: .55; }
  88% { opacity: .08; }
  89.5% { opacity: .75; }
  92% { opacity: 0; }
}
@media (prefers-reduced-motion: reduce) {
  .root.flits .gloed, .root.flits-nabij .gloed { animation: none; opacity: .22; }
  .puls { display: none; }
}
.wrap {
  container-type: inline-size;
  max-width: 1720px;
  margin: 0 auto;
  padding: 20px 24px 28px;
}
.num, .big, .ring-t, .g-as, td, .kv b, .uur b { font-variant-numeric: tabular-nums; font-feature-settings: "tnum"; }
.ic { width: 18px; height: 18px; flex: none; }
small { font-size: .55em; font-weight: 600; color: var(--tekst2); margin-left: 3px; letter-spacing: 0; }
.leeg { color: var(--tekst3); opacity: .7; }
.dim { opacity: .45; }
[hidden] { display: none !important; }

/* ---- kopregel ---- */
.kop {
  display: flex; align-items: center; gap: 18px; flex-wrap: wrap;
  padding: 4px 2px 16px;
}
.merk { display: flex; align-items: center; gap: 12px; min-width: 0; }
.logo {
  width: 42px; height: 42px; border-radius: 12px; display: grid; place-items: center;
  background: linear-gradient(135deg, #4f46e5, #7c3aed 55%, #db2777);
  box-shadow: 0 6px 22px rgba(124, 58, 237, .45), inset 0 1px 0 rgba(255,255,255,.25);
  color: #fff;
}
.logo .ic { width: 24px; height: 24px; fill: #fff; stroke: none; }
.merknaam { font-size: 19px; font-weight: 800; letter-spacing: .14em; line-height: 1.1; }
.merksub { font-size: 12px; color: var(--tekst2); letter-spacing: .04em; margin-top: 2px; }
.kop-mid { display: flex; gap: 8px; flex-wrap: wrap; flex: 1 1 0; min-width: 0; }
.kop-r { display: flex; align-items: center; gap: 18px; margin-left: auto; }
.klok { text-align: right; line-height: 1.1; }
.klok .tijd { font-size: 30px; font-weight: 700; letter-spacing: .02em; font-variant-numeric: tabular-nums; }
.klok .datum { font-size: 12px; color: var(--tekst2); margin-top: 3px; }
.stip { width: 8px; height: 8px; border-radius: 50%; display: inline-block; flex: none; }
.stip.ok { background: var(--groen); box-shadow: 0 0 8px rgba(52, 211, 153, .7); }
.stip.traag { background: var(--geel); box-shadow: 0 0 8px rgba(250, 204, 21, .6); }
.stip.fout { background: var(--rood); box-shadow: 0 0 8px rgba(251, 77, 101, .7); }
.stip.ongebruikt { background: rgba(255,255,255,.18); }
.stippen { display: flex; gap: 5px; align-items: center; padding: 8px 10px; border-radius: 999px; background: var(--paneel2); border: 1px solid var(--rand); }
.stippen .lbl { font-size: 11px; color: var(--tekst2); margin-right: 4px; letter-spacing: .06em; text-transform: uppercase; font-weight: 700; }
.chip {
  display: inline-flex; align-items: center; gap: 6px; white-space: nowrap;
  font-size: 12px; font-weight: 600; color: var(--tekst2);
  padding: 5px 10px; border-radius: 999px;
  background: rgba(255,255,255,.05); border: 1px solid var(--rand);
  max-width: 100%; overflow: hidden; text-overflow: ellipsis;
}
.chip .ic { width: 14px; height: 14px; }
.chip.groot { font-size: 13px; padding: 7px 12px; color: var(--tekst); background: var(--paneel2); }
.chip.ok { color: var(--groen); border-color: rgba(52, 211, 153, .35); }
.chip.let { color: var(--oranje); border-color: rgba(251, 146, 60, .4); }
.chip.gevaar { color: #fff; background: rgba(251, 77, 101, .22); border-color: rgba(251, 77, 101, .55); }
.chip.uit { opacity: .55; }

/* ---- meldingen ---- */
.meldingen { display: grid; gap: 10px; margin-bottom: 14px; }
.meldingen:empty { display: none; }
.melding {
  display: flex; align-items: center; gap: 14px; padding: 14px 18px; border-radius: 14px;
  border: 1px solid var(--rand2); background: var(--paneel);
  backdrop-filter: blur(14px); -webkit-backdrop-filter: blur(14px);
}
.melding .ic { width: 22px; height: 22px; }
.melding b { font-size: 15px; }
.melding span { color: var(--tekst2); font-size: 13px; }
.melding.gevaar {
  background: linear-gradient(90deg, rgba(251, 77, 101, .32), rgba(251, 77, 101, .1));
  border-color: rgba(251, 77, 101, .6); color: #fff;
}
.melding.gevaar span { color: #ffd9de; }
.melding.gevaar b { font-size: 18px; letter-spacing: .04em; text-transform: uppercase; }
.melding.let { border-color: rgba(251, 146, 60, .45); }
.melding.let .ic { color: var(--oranje); }

/* ---- statusrij ---- */
.hero { display: grid; gap: 14px; grid-template-columns: 1fr; margin-bottom: 14px; }
.tegel {
  position: relative; overflow: hidden;
  padding: 16px 18px 16px 20px; border-radius: var(--r);
  background: linear-gradient(160deg, rgba(30, 34, 72, .72), rgba(14, 16, 38, .72));
  border: 1px solid var(--rand);
  backdrop-filter: blur(16px) saturate(130%); -webkit-backdrop-filter: blur(16px) saturate(130%);
  box-shadow: 0 12px 34px rgba(0,0,0,.35), inset 0 1px 0 rgba(255,255,255,.05);
  min-width: 0;
}
.tegel::before {
  content: ""; position: absolute; left: 0; top: 0; bottom: 0; width: 4px;
  background: var(--accent, var(--tekst3));
  box-shadow: 0 0 18px var(--accent, transparent);
}
.tegel::after {
  content: ""; position: absolute; inset: 0; pointer-events: none;
  background: radial-gradient(120% 90% at 0% 0%, var(--accent-zacht, transparent), transparent 55%);
}
.tegel > * { position: relative; z-index: 1; }
.lbl {
  font-size: 11px; font-weight: 700; letter-spacing: .12em; text-transform: uppercase; color: var(--tekst2);
}
.big { font-size: 30px; font-weight: 800; line-height: 1.1; letter-spacing: .01em; margin: 6px 0 4px; }
.big.accent { color: var(--accent); }
.sub { font-size: 13px; color: var(--tekst2); line-height: 1.45; }
.sub b { color: var(--tekst); font-weight: 600; }
.tekst-m { font-size: 18px; font-weight: 700; line-height: 1.3; margin: 8px 0 6px; }
.klem { display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }
.pot { display: flex; gap: 14px; align-items: center; }
.ring-t { font-size: 24px; font-weight: 800; fill: var(--tekst); }
.ring-p { font-size: 12px; fill: var(--tekst2); font-weight: 700; }
.opbouw { display: grid; gap: 4px; font-size: 12px; color: var(--tekst2); min-width: 0; }
.opbouw span { display: flex; justify-content: space-between; gap: 10px; }
.opbouw b { color: var(--tekst); font-variant-numeric: tabular-nums; }

/* ---- raster met panelen ---- */
.raster {
  display: grid; gap: 14px;
  grid-template-columns: minmax(0, 1fr);
  grid-template-areas: "radar" "bliksem" "knmi" "neerslag" "convectie" "waarneming" "verwachting";
}
.paneel {
  min-width: 0; border-radius: var(--r);
  background: linear-gradient(180deg, var(--paneel), var(--paneel2));
  border: 1px solid var(--rand);
  backdrop-filter: blur(16px) saturate(130%); -webkit-backdrop-filter: blur(16px) saturate(130%);
  box-shadow: 0 12px 34px rgba(0,0,0,.35), inset 0 1px 0 rgba(255,255,255,.05);
  padding: 0 0 16px;
  display: flex; flex-direction: column;
}
.p-radar { grid-area: radar; }
.p-bliksem { grid-area: bliksem; }
.p-convectie { grid-area: convectie; }
.p-knmi { grid-area: knmi; }
.p-waarneming { grid-area: waarneming; }
.p-neerslag { grid-area: neerslag; }
.p-verwachting { grid-area: verwachting; }
.ph { display: flex; align-items: center; gap: 9px; padding: 14px 16px 10px; color: var(--tekst2); min-width: 0; flex-wrap: wrap; }
.ph h2 { margin: 0; font-size: 12px; font-weight: 800; letter-spacing: .14em; text-transform: uppercase; color: var(--tekst); }
.ph .ic { color: var(--violet); }
.ph-r { margin-left: auto; display: flex; gap: 6px; flex-wrap: wrap; justify-content: flex-end; min-width: 0; }
.pb { padding: 0 16px; display: grid; grid-template-columns: minmax(0, 1fr); gap: 14px; }
.leegmelding { padding: 6px 16px 0; color: var(--tekst3); font-size: 13px; }

/* ---- radar ---- */
.radarvak {
  position: relative; margin: 0 16px; border-radius: 12px; overflow: hidden;
  background: #0a0d1c; border: 1px solid var(--rand);
  aspect-ratio: 1 / 1; display: grid; place-items: center;
}
.radarvak img { width: 100%; height: 100%; object-fit: contain; display: block; }
.radarvak .geen { color: var(--tekst3); font-size: 13px; padding: 20px; text-align: center; }
.radar-hoek {
  position: absolute; left: 10px; top: 10px; display: flex; gap: 6px; flex-wrap: wrap;
}
.radar-hoek .chip { background: rgba(7, 9, 20, .72); color: var(--tekst); }
.wissel { display: inline-flex; padding: 3px; border-radius: 999px; background: var(--paneel2); border: 1px solid var(--rand); }
.wissel button {
  font: inherit; font-size: 12px; font-weight: 700; color: var(--tekst2);
  background: none; border: 0; padding: 5px 12px; border-radius: 999px; cursor: pointer;
}
.wissel button[aria-pressed="true"] { background: linear-gradient(135deg, #4f46e5, #7c3aed); color: #fff; }
.wissel button:focus-visible { outline: 2px solid var(--cyaan); outline-offset: 1px; }
.legenda { display: flex; align-items: center; gap: 10px; padding: 10px 16px 0; font-size: 11px; color: var(--tekst2); }
.legenda .schaal {
  flex: 1; height: 8px; border-radius: 99px;
  background: linear-gradient(90deg, #7cc4ff, #3d8bff 30%, #ffd43b 55%, #ff922b 75%, #ff4d5e 90%, #d946ef);
}

/* ---- bliksem ---- */
.bl-top { display: grid; justify-items: center; }
.duo3 { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; }
.kompas { width: 100%; max-width: 300px; height: auto; display: block; }
.k-ring { font-size: 9px; fill: var(--tekst3); font-variant-numeric: tabular-nums; }
.k-l { font-size: 12px; font-weight: 700; fill: var(--tekst2); }
.k-n { fill: var(--rood); }
.puls { transform-box: fill-box; transform-origin: center; animation: puls 1.8s ease-out infinite; }
@keyframes puls { 0% { opacity: .9; transform: scale(.6); } 100% { opacity: 0; transform: scale(2.2); } }
.duo { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.mini { padding: 10px 12px; border-radius: 12px; background: rgba(255,255,255,.035); border: 1px solid var(--rand); min-width: 0; }
.mini .lbl { font-size: 10px; }
.mini .w { font-size: 20px; font-weight: 750; margin-top: 3px; font-variant-numeric: tabular-nums; white-space: nowrap; }
.mini .s { font-size: 12px; color: var(--tekst2); margin-top: 1px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.ringen { display: grid; gap: 8px; }
.ringrij { display: grid; grid-template-columns: 64px 1fr 44px; align-items: center; gap: 10px; font-size: 13px; color: var(--tekst2); }
.ringrij b { text-align: right; color: var(--tekst); font-size: 15px; font-variant-numeric: tabular-nums; }
.vlaggen { display: flex; gap: 6px; flex-wrap: wrap; }
.celregel { font-size: 13px; color: var(--tekst2); line-height: 1.5; padding: 10px 12px; border-radius: 12px; background: rgba(255,255,255,.035); border: 1px solid var(--rand); }
.celregel b { color: var(--tekst); }

/* ---- balken ---- */
.meters { display: grid; gap: 13px; }
.meterrij { display: grid; gap: 6px; }
.meterkop { display: flex; justify-content: space-between; align-items: baseline; gap: 2px 10px; flex-wrap: wrap; }
.meters, .meterrij, .ringen, .tijdlijn, .kerncijfers { grid-template-columns: minmax(0, 1fr); }
.meterkop .lbl { font-size: 11px; }
.meterkop .w { font-size: 17px; font-weight: 750; font-variant-numeric: tabular-nums; white-space: nowrap; }
.meterkop .w small { font-size: 11px; }
.balk { position: relative; height: 8px; border-radius: 99px; background: rgba(255,255,255,.07); overflow: hidden; }
.balk b { position: absolute; left: 0; top: 0; bottom: 0; border-radius: 99px; box-shadow: 0 0 12px currentColor; }
.balk i { position: absolute; top: 0; bottom: 0; width: 1px; background: rgba(7, 9, 20, .9); }
.meternoot { font-size: 12px; color: var(--tekst3); }
.bereik { position: relative; height: 18px; }
.bereik .lijn { position: absolute; left: 0; right: 0; top: 8px; height: 2px; background: rgba(255,255,255,.08); border-radius: 2px; }
.bereik .span { position: absolute; top: 5px; height: 8px; border-radius: 99px; background: linear-gradient(90deg, rgba(167, 139, 250, .5), rgba(167, 139, 250, .9)); }
.bereik .med { position: absolute; top: 1px; width: 3px; height: 16px; border-radius: 2px; background: #fff; }
.kv { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px; }
.duiding { display: grid; gap: 6px; font-size: 12.5px; }
.duiding div { display: flex; justify-content: space-between; gap: 12px; padding-bottom: 6px; border-bottom: 1px solid rgba(255,255,255,.05); }
.duiding div:last-child { border-bottom: 0; padding-bottom: 0; }
.duiding span { color: var(--tekst3); white-space: nowrap; }
.duiding b { font-weight: 600; color: var(--tekst); text-align: right; }
.obs .mini .s { white-space: normal; }
.kv > div { padding: 9px 11px; border-radius: 12px; background: rgba(255,255,255,.035); border: 1px solid var(--rand); min-width: 0; }
.kv .lbl { font-size: 10px; letter-spacing: .08em; display: block; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.kv b { display: block; font-size: 16px; margin-top: 3px; white-space: nowrap; }

/* ---- waarschuwingen ---- */
.code { display: flex; align-items: center; gap: 14px; flex-wrap: wrap; }
.codebord {
  padding: 10px 16px; border-radius: 12px; font-weight: 900; font-size: 20px; letter-spacing: .08em;
  text-transform: uppercase; color: #0a0b16; background: var(--accent);
  box-shadow: 0 8px 26px var(--accent-zacht);
}
.codebord.groen { color: #052e1f; }
.codetekst { min-width: 0; flex: 1; }
.codetekst .t { font-size: 17px; font-weight: 700; }
.codetekst .s { font-size: 13px; color: var(--tekst2); margin-top: 2px; }
.omschrijving { font-size: 13px; line-height: 1.5; color: var(--tekst2); }
.omschrijving.klem { -webkit-line-clamp: 4; }
.tijdlijn { display: grid; gap: 6px; }
.tl-balk { display: grid; grid-auto-flow: column; grid-auto-columns: 1fr; gap: 2px; height: 26px; }
.tl-balk span { border-radius: 4px; background: rgba(255,255,255,.06); position: relative; }
.tl-balk span.geel { background: var(--geel); }
.tl-balk span.oranje { background: var(--oranje); }
.tl-balk span.rood { background: var(--rood); }
.tl-balk span.nu { outline: 2px solid #fff; outline-offset: 1px; }
.tl-as { display: grid; grid-auto-flow: column; grid-auto-columns: 1fr; gap: 2px; font-size: 10px; color: var(--tekst3); font-variant-numeric: tabular-nums; }
.tl-as span { white-space: nowrap; overflow: visible; }
.tl-legenda { display: flex; gap: 12px; flex-wrap: wrap; font-size: 11px; color: var(--tekst2); }
.tl-legenda i { display: inline-block; width: 10px; height: 10px; border-radius: 3px; margin-right: 5px; vertical-align: -1px; }

/* ---- waarnemingen ---- */
.station { font-size: 13px; color: var(--tekst2); }
.station b { color: var(--tekst); }
.obs { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }
.obs .mini .w { font-size: 22px; }
.trend { display: inline-flex; align-items: center; gap: 4px; font-weight: 700; }
.trend.daalt { color: var(--oranje); }
.trend.daalt-hard { color: var(--rood); }
.trend.stijgt { color: var(--cyaan); }

/* ---- neerslag ---- */
.ns-kop { display: flex; align-items: baseline; justify-content: space-between; gap: 12px; flex-wrap: wrap; }
.ns-kop .tekst-m { margin: 0; }
.gwrap { position: relative; display: grid; grid-template-columns: 30px 1fr; grid-template-rows: 170px 22px; }
.g-y { position: relative; grid-row: 1; grid-column: 1; }
.g-y span, .g-x span { position: absolute; font-size: 11px; color: var(--tekst3); font-variant-numeric: tabular-nums; white-space: nowrap; }
.g-y span { right: 8px; transform: translateY(-50%); }
.g-plot { position: relative; grid-row: 1; grid-column: 2; }
.grafiek { position: absolute; inset: 0; width: 100%; height: 100%; display: block; overflow: visible; }
.g-x { position: relative; grid-row: 2; grid-column: 2; }
.g-x span { top: 6px; transform: translateX(-50%); }
.g-x span:first-child { transform: none; }
.g-x span:last-child { transform: translateX(-100%); }
.g-eenheid { position: absolute; left: 0; bottom: 4px; font-size: 10px; color: var(--tekst3); }
.g-lijn { stroke: rgba(255,255,255,.08); }
.g-basis { stroke: rgba(255,255,255,.25); }
.g-start { stroke: var(--cyaan); stroke-dasharray: 4 4; }
.g-start-t { position: absolute; top: 0; margin-left: 5px; font-size: 11px; color: var(--cyaan); font-weight: 700; }

/* ---- uurstrip ---- */
.uren { display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); gap: 8px; }
.uur {
  display: grid; justify-items: center; gap: 4px; padding: 10px 4px 9px; border-radius: 12px;
  background: rgba(255,255,255,.035); border: 1px solid var(--rand); min-width: 0;
}
.uur.onweer { border-color: rgba(250, 204, 21, .45); background: rgba(250, 204, 21, .07); }
.uur .h { font-size: 12px; color: var(--tekst2); font-weight: 700; font-variant-numeric: tabular-nums; }
.uur .dag { font-size: 10px; color: var(--violet); font-weight: 800; letter-spacing: .08em; text-transform: uppercase; }
.weer-ic { width: 34px; height: 34px; }
.uur b { font-size: 17px; }
.uur .kans { width: 100%; padding: 0 8px; display: grid; gap: 3px; justify-items: center; font-size: 11px; color: var(--blauw); font-variant-numeric: tabular-nums; }
.uur .kans .balk { width: 100%; height: 4px; }
.uur .wind { font-size: 11px; color: var(--tekst2); font-variant-numeric: tabular-nums; white-space: nowrap; }

/* ---- voet ---- */
.voet { margin-top: 14px; }
.bronnen { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 8px; }
.bron { display: grid; grid-template-columns: auto 1fr auto; align-items: center; gap: 8px; padding: 8px 11px; border-radius: 10px; background: rgba(255,255,255,.03); border: 1px solid var(--rand); font-size: 12px; min-width: 0; }
.bron .n { color: var(--tekst); font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.bron .p { color: var(--tekst2); font-variant-numeric: tabular-nums; white-space: nowrap; }
.bron.ongebruikt { opacity: .45; }
.voetregel { display: flex; justify-content: space-between; gap: 12px; flex-wrap: wrap; font-size: 12px; color: var(--tekst3); padding: 12px 16px 0; }

/* ---- breedtes ---- */
@container (min-width: 560px) {
  .obs { grid-template-columns: repeat(3, minmax(0, 1fr)); }
}
@container (min-width: 760px) {
  .hero { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .raster {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    grid-template-areas:
      "radar radar"
      "bliksem convectie"
      "knmi knmi"
      "neerslag waarneming"
      "verwachting verwachting";
  }
  .radarvak { aspect-ratio: 1 / 1; width: min(100% - 32px, 760px); margin: 0 auto; }
  .uren { grid-template-columns: repeat(12, minmax(0, 1fr)); }
  .obs { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@container (min-width: 1180px) {
  .hero { grid-template-columns: 1.15fr 1.05fr 1.25fr 1fr; }
  .raster {
    grid-template-columns: minmax(0, 1fr) minmax(0, 1.45fr) minmax(0, 1fr);
    grid-template-areas:
      "bliksem radar convectie"
      "knmi neerslag waarneming"
      "verwachting verwachting verwachting";
  }
  .radarvak { aspect-ratio: auto; width: auto; margin: 0 16px; flex: 1; min-height: 560px; }
  .p-radar .legenda { padding-bottom: 0; }
  .obs { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@container (max-width: 1179px) {
  .kop-mid { flex: 1 1 100%; order: 2; }
}
@container (max-width: 520px) {
  .wrap { padding: 14px 12px 20px; }
  .kop { gap: 12px; }
  .kop-r { margin-left: 0; width: 100%; justify-content: space-between; flex-wrap: wrap; gap: 10px; order: 1; }
  .klok { order: -1; text-align: left; }
  .klok .datum { white-space: nowrap; }
  .mini { padding: 9px 10px; }
  .mini .w { font-size: 18px; }
  .klok .tijd { font-size: 26px; }
  .big { font-size: 26px; }
  .kompas { max-width: 260px; }
  .bronnen { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .bron { font-size: 11.5px; padding: 8px 9px; gap: 6px; }
  .uren { grid-template-columns: repeat(4, minmax(0, 1fr)); }

  .stippen .lbl { display: none; }
}
`;

/* De achtergrond: stormnacht met wolkenstructuur en radarraster. */
const ACHTERGROND = `
<div class="bg" aria-hidden="true">
  <svg class="wolken" preserveAspectRatio="xMidYMid slice" viewBox="0 0 1600 1000">
    <defs>
      <filter id="wolk" x="0" y="0" width="100%" height="100%">
        <feTurbulence type="fractalNoise" baseFrequency="0.0026 0.0062" numOctaves="4" seed="7"/>
        <feColorMatrix type="matrix" values="0 0 0 0 0.42  0 0 0 0 0.45  0 0 0 0 0.78  0 0 0 1.25 -0.52"/>
        <feGaussianBlur stdDeviation="1.2"/>
      </filter>
      <linearGradient id="wolkmasker" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stop-color="#fff" stop-opacity=".95"/>
        <stop offset=".55" stop-color="#fff" stop-opacity=".35"/>
        <stop offset="1" stop-color="#fff" stop-opacity=".12"/>
      </linearGradient>
      <mask id="wm"><rect width="1600" height="1000" fill="url(#wolkmasker)"/></mask>
    </defs>
    <rect width="1600" height="1000" filter="url(#wolk)" mask="url(#wm)"/>
  </svg>
  <svg class="raster" preserveAspectRatio="xMidYMin slice" viewBox="0 0 1600 1000">
    <defs>
      <pattern id="ruit" width="48" height="48" patternUnits="userSpaceOnUse">
        <path d="M48 0H0V48" fill="none" stroke="rgba(150,170,255,.035)"/>
      </pattern>
      <radialGradient id="rvervaag" cx="1240" cy="140" r="900" gradientUnits="userSpaceOnUse">
        <stop offset="0" stop-color="#fff" stop-opacity="1"/>
        <stop offset="1" stop-color="#fff" stop-opacity="0"/>
      </radialGradient>
      <mask id="rm"><rect width="1600" height="1000" fill="url(#rvervaag)"/></mask>
    </defs>
    <rect width="1600" height="1000" fill="url(#ruit)"/>
    <g mask="url(#rm)" fill="none" stroke="rgba(140,165,255,.10)">
      <circle cx="1240" cy="140" r="140"/>
      <circle cx="1240" cy="140" r="280"/>
      <circle cx="1240" cy="140" r="420"/>
      <circle cx="1240" cy="140" r="560"/>
      <circle cx="1240" cy="140" r="700"/>
      <path d="M1240 -600V900M500 140H1980M717 -383 1763 663M717 663 1763 -383"/>
    </g>
  </svg>
  <div class="gloed"></div>
</div>`;

/* ------------------------------------------------------------------ */
/* De kaart                                                            */
/* ------------------------------------------------------------------ */

/* Per paneel de sleutels waar het van afhangt. */
const AFHANKELIJK = {
  kop: ["locatie", "onderweg", "bronstatus", "meldingen", "afstand", "cape", "regenStart", "meting", "niveau"],
  meldingen: ["schuilen", "veilig", "frequentie", "locatie", "bronstatus"],
  hero: ["nabij", "nadert", "schuilen", "afstand", "azimut", "aankomst", "trend", "frequentie",
    "niveau", "waarschuwing", "verwachting", "potentie", "veilig", "nadering"],
  radar: ["radar", "vooruitblik"],
  bliksem: ["afstand", "azimut", "nadering", "aankomst", "frequentie", "markers", "nabij", "nadert",
    "schuilen", "celrichting", "celsnelheid", "passage", "passageafstand", "trend", "veilig"],
  convectie: ["cape", "capePiek", "li", "tt", "schering6", "schering3", "schering1", "ensemble",
    "overeenstemming", "rotatie", "hagel", "lpi", "cin", "vriesniveau", "wolkentop", "updraft"],
  knmi: ["niveau", "waarschuwing"],
  waarneming: ["meting", "stoten", "druk", "druk1", "druk3", "onweerGemeten", "hagelGemeten"],
  neerslag: ["regenStart", "regenIntensiteit", "regenPiek", "regenVerwacht"],
  verwachting: ["weer"],
  voet: ["bronstatus", "meldingen"],
};

const VOORKEUR = "stormchase-hud-radar";

class StormchaseHudCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = {};
    this._vorige = {};
    this._vuil = new Set(Object.keys(AFHANKELIJK));
    this._ids = null;
    this._ringen = [];
    this._register = undefined;
    this._aantalStates = -1;
    this._uurdata = null;
    this._verwachtingFout = false;
    this._abonnement = null;
    this._abonnementOp = null;
    this._gepland = false;
    try {
      this._radarModus = localStorage.getItem(VOORKEUR) === "vooruit" ? "vooruit" : "nu";
    } catch (e) {
      this._radarModus = "nu";
    }
  }

  static getStubConfig() {
    return {};
  }

  setConfig(config) {
    this._config = { ...(config || {}) };
    this._ids = null;
    this._vuil = new Set(Object.keys(AFHANKELIJK));
    this._plan();
  }

  getCardSize() {
    return 24;
  }

  set hass(hass) {
    this._hass = hass;
    if (!this._gebouwd) this._bouw();

    // Opnieuw zoeken alleen als het register of het aantal entiteiten wijzigt
    const aantal = Object.keys(hass.states).length;
    if (!this._ids || hass.entities !== this._register || aantal !== this._aantalStates) {
      const oud = JSON.stringify([this._ids, this._ringen]);
      const { ids, ringen } = zoekEntiteiten(hass, this._config);
      this._ids = ids;
      this._ringen = ringen;
      this._register = hass.entities;
      this._aantalStates = aantal;
      if (JSON.stringify([ids, ringen]) !== oud) {
        for (const p of Object.keys(AFHANKELIJK)) this._vuil.add(p);
      }
    }

    // Welke states zijn er veranderd? State-objecten worden bij elke
    // wijziging vervangen, dus vergelijken op referentie is genoeg.
    const gewijzigd = new Set();
    const kijk = (id) => {
      if (!id) return;
      const s = hass.states[id];
      if (s !== this._vorige[id]) {
        gewijzigd.add(id);
        this._vorige[id] = s;
      }
    };
    for (const id of Object.values(this._ids)) kijk(id);
    for (const r of this._ringen) kijk(r.id);

    if (gewijzigd.size) {
      for (const [paneel, sleutels] of Object.entries(AFHANKELIJK)) {
        if (sleutels.some((k) => gewijzigd.has(this._ids[k]))) this._vuil.add(paneel);
      }
      if (this._ringen.some((r) => gewijzigd.has(r.id))) {
        this._vuil.add("bliksem");
        this._vuil.add("hero");
      }
    }

    this._abonneer();
    if (this._vuil.size) this._plan();
  }

  get hass() {
    return this._hass;
  }

  connectedCallback() {
    if (!this._klok) {
      // Klok en "x min geleden" lopen ook door zonder nieuwe states
      this._klok = setInterval(() => {
        this._vuil.add("kop");
        this._vuil.add("radar");
        this._vuil.add("voet");
        this._plan();
      }, 20000);
    }
    this._abonneer();
  }

  disconnectedCallback() {
    if (this._klok) {
      clearInterval(this._klok);
      this._klok = null;
    }
    this._stopAbonnement();
  }

  /* ---- uurverwachting via de websocket ---- */

  _abonneer() {
    const hass = this._hass;
    const id = this._ids && this._ids.weer;
    if (!hass || !hass.connection || !id || !this.isConnected) return;
    if (this._abonnement && this._abonnementOp === id) return;
    this._stopAbonnement();
    this._abonnementOp = id;
    this._verwachtingFout = false;
    try {
      this._abonnement = hass.connection.subscribeMessage(
        (bericht) => {
          this._uurdata = Array.isArray(bericht && bericht.forecast) ? bericht.forecast : null;
          this._vuil.add("verwachting");
          this._plan();
        },
        { type: "weather/subscribe_forecast", forecast_type: "hourly", entity_id: id }
      );
      Promise.resolve(this._abonnement).catch(() => {
        this._verwachtingFout = true;
        this._abonnement = null;
        this._vuil.add("verwachting");
        this._plan();
      });
    } catch (e) {
      this._verwachtingFout = true;
      this._abonnement = null;
    }
  }

  _stopAbonnement() {
    const lopend = this._abonnement;
    this._abonnement = null;
    this._abonnementOp = null;
    if (lopend) {
      Promise.resolve(lopend)
        .then((stop) => typeof stop === "function" && stop())
        .catch(() => {});
    }
  }

  /* ---- opbouw ---- */

  _bouw() {
    this._gebouwd = true;
    this._html = {};
    volgScroll();
    this.shadowRoot.innerHTML =
      `<style>${STIJL}</style>` +
      `<div class="root">${ACHTERGROND}<div class="wrap">` +
      `<header class="kop" data-p="kop"></header>` +
      `<div class="meldingen" data-p="meldingen"></div>` +
      `<section class="hero" data-p="hero" aria-label="Status"></section>` +
      `<main class="raster">` +
      `<section class="paneel p-radar" data-p="radar">` +
      `<div class="radarkop"></div>` +
      `<div class="radarvak"><img alt="Radarbeeld rond de actieve locatie" hidden>` +
      `<div class="geen" hidden>Geen radarbeeld beschikbaar</div><div class="radar-hoek"></div></div>` +
      `<div class="legenda"><span>licht</span><span class="schaal"></span><span>zwaar</span></div>` +
      `</section>` +
      `<section class="paneel p-bliksem" data-p="bliksem"></section>` +
      `<section class="paneel p-convectie" data-p="convectie"></section>` +
      `<section class="paneel p-knmi" data-p="knmi"></section>` +
      `<section class="paneel p-neerslag" data-p="neerslag"></section>` +
      `<section class="paneel p-waarneming" data-p="waarneming"></section>` +
      `<section class="paneel p-verwachting" data-p="verwachting"></section>` +
      `</main>` +
      `<footer class="paneel voet" data-p="voet"></footer>` +
      `</div></div>`;

    this._el = {};
    for (const el of this.shadowRoot.querySelectorAll("[data-p]")) {
      this._el[el.dataset.p] = el;
    }
    this._root = this.shadowRoot.querySelector(".root");
    this._img = this.shadowRoot.querySelector(".radarvak img");

    this.shadowRoot.addEventListener("click", (ev) => {
      const knop = ev.target.closest && ev.target.closest("[data-modus]");
      if (!knop) return;
      this._radarModus = knop.dataset.modus;
      try {
        localStorage.setItem(VOORKEUR, this._radarModus);
      } catch (e) {
        /* privevenster of geblokkeerde opslag: dan alleen voor nu */
      }
      this._vuil.add("radar");
      this._plan();
    });
  }

  _plan() {
    if (this._gepland || !this._hass || !this._gebouwd) return;
    this._gepland = true;
    const doe = () => {
      if (scrolltNog()) {
        // Pas tekenen als de gebruiker klaar is met scrollen
        setTimeout(doe, 250);
        return;
      }
      this._gepland = false;
      this._teken();
    };
    if (typeof requestAnimationFrame === "function") requestAnimationFrame(doe);
    else setTimeout(doe, 0);
  }

  _s(sleutel) {
    const id = this._ids && this._ids[sleutel];
    return id ? this._hass.states[id] : undefined;
  }

  _teken() {
    const vuil = [...this._vuil];
    this._vuil.clear();
    for (const paneel of vuil) {
      const el = this._el[paneel];
      if (!el) continue;
      try {
        const methode = this[`_${paneel}`];
        const html = methode.call(this, el);
        if (html === undefined) continue; // tekent zelf
        // Vergelijken met de vorige opbouw, niet met innerHTML: de browser
        // schrijft HTML anders terug, waardoor elk paneel bij elke update
        // opnieuw werd opgebouwd.
        if (this._html[paneel] === html) continue;
        this._html[paneel] = html;
        if (html === null) {
          el.hidden = true;
          el.innerHTML = "";
        } else {
          el.hidden = false;
          el.innerHTML = html;
        }
      } catch (err) {
        // Een fout in een paneel mag de rest niet meenemen
        console.warn("Stormchase: paneel", paneel, "kon niet getekend worden", err);
      }
    }
  }

  /* ---- situatie ---- */

  _situatie() {
    const afstand = getal(this._s("afstand"));
    const nabij = this._s("nabij") && this._s("nabij").state === "on";
    const nadert = this._s("nadert") && this._s("nadert").state === "on";
    const schuilen = this._s("schuilen") && this._s("schuilen").state === "on";
    if (schuilen || nabij) return { code: "nabij", tekst: "Onweer nabij", niveau: "rood" };
    if (nadert) return { code: "nadert", tekst: "Onweer nadert", niveau: "oranje" };
    if (afstand != null) return { code: "actief", tekst: "Onweer actief", niveau: "geel" };
    return { code: "rustig", tekst: "Rustig", niveau: "groen" };
  }

  /* ---- kopregel ---- */

  _kop() {
    const nu = new Date();
    const tijd = nu.toLocaleTimeString("nl-NL", { hour: "2-digit", minute: "2-digit" });
    const datum = nu.toLocaleDateString("nl-NL", { weekday: "short", day: "numeric", month: "short" });

    // Laatste update: de jongste van de kernsensoren
    let laatste = null;
    for (const k of ["afstand", "cape", "regenStart", "meting", "niveau", "radar"]) {
      const s = this._s(k);
      const d = s && alsDatum(s.last_updated);
      if (d && (!laatste || d > laatste)) laatste = d;
    }

    const loc = this._s("locatie");
    let locatie = "";
    if (loc) {
      const adres = attr(loc, "adres");
      const la = attr(loc, "latitude");
      const lo = attr(loc, "longitude");
      const plek = adres
        ? esc(adres)
        : Number.isFinite(la) && Number.isFinite(lo)
          ? `${fmt(la, 3)}, ${fmt(lo, 3)}`
          : "Locatie wordt bepaald";
      const thuis = bruikbaar(loc) && loc.state === "thuis";
      const via = bruikbaar(loc) ? `Locatie via ${esc(loc.state)}` : "Actieve locatie";
      locatie = `<span class="chip groot" title="${via}">${icoon(thuis ? "huis" : "pin")}${plek}</span>`;
    }

    const weg = this._s("onderweg");
    let onderweg = "";
    if (weg) {
      const v = attr(weg, "snelheid_kmh");
      const stil = attr(weg, "stil_sinds_minuten");
      if (weg.state === "on") {
        onderweg = chip(`${icoon("auto")}Onderweg${v != null ? PUNT + fmt(v) + " km/u" : ""}`, "groot let");
      } else if (bruikbaar(weg)) {
        onderweg = chip(
          `${icoon("pin")}Ter plaatse${stil != null ? PUNT + fmt(stil) + " min" : ""}`,
          "groot"
        );
      }
    }

    const sw = this._s("meldingen");
    const meldingen = sw
      ? chip(`${icoon("bel")}Meldingen ${sw.state === "on" ? "aan" : "uit"}`, sw.state === "on" ? "groot ok" : "groot uit")
      : "";

    // Bronbolletjes, alleen voor bronnen die echt gebruikt worden
    const bs = this._s("bronstatus");
    let bronnen = "";
    if (bs) {
      const lijst = attr(bs, "bronnen") || {};
      const haperend = attr(bs, "haperend") || [];
      const knmi = attr(bs, "knmi");
      let stippen = "";
      for (const [naam, info] of Object.entries(lijst)) {
        const t = bronToestand(naam, info, haperend);
        if (t === "ongebruikt") continue;
        stippen += `<span class="stip ${t}" title="${esc(BRONNAAM[naam] || naam)}: ${t}"></span>`;
      }
      const push = pushTekst(knmi && knmi.push);
      bronnen =
        `<div class="stippen" title="${esc(bs.state)}"><span class="lbl">Bronnen</span>${stippen}</div>` +
        (push ? chip(`<span class="stip ${push[1]}"></span>KNMI push ${esc(push[0])}`, push[1] === "ok" ? "ok" : "") : "");
    }

    return (
      `<div class="merk"><div class="logo">${icoon("flits")}</div>` +
      `<div><div class="merknaam">STORMCHASE</div>` +
      `<div class="merksub">${esc(this._config.title || "Chase-commandocentrum")}</div></div></div>` +
      `<div class="kop-mid">${locatie}${onderweg}${meldingen}</div>` +
      `<div class="kop-r">${bronnen}<div class="klok"><div class="tijd">${tijd}</div>` +
      `<div class="datum">${esc(datum)}${laatste ? PUNT + "bijgewerkt " + klokTijd(laatste) : ""}</div></div></div>`
    );
  }

  /* ---- meldingen bovenaan ---- */

  _meldingen() {
    let uit = "";
    const schuilen = this._s("schuilen");
    if (schuilen && schuilen.state === "on") {
      const veilig = getal(this._s("veilig"));
      const freq = getal(this._s("frequentie"));
      // Het onweer is er al: een aankomsttijd zegt dan niets meer
      uit +=
        `<div class="melding gevaar" role="alert">${icoon("huis")}<div><b>Blijf binnen</b><br>` +
        `<span>Onweer binnen 10 km, nu boven je` +
        `${freq != null ? PUNT + fmt(freq) + " inslagen per minuut" : ""}` +
        `${veilig != null ? PUNT + "veilig over " + fmt(veilig) + " min" : ""}</span></div></div>`;
    }

    const loc = this._s("locatie");
    const afwijking = Number(attr(loc, "afwijking_km"));
    const herberekend = attr(loc, "afstand_via") === "herberekend";
    if (Number.isFinite(afwijking) && afwijking > 25 && !herberekend) {
      uit +=
        `<div class="melding let">${icoon("waarschuwing")}<div><b>Blitzortung meet ${fmt(afwijking)} km verderop</b><br>` +
        `<span>Kies daar dezelfde locatiebron, anders horen de bliksemafstanden niet bij dit weerbeeld</span></div></div>`;
    }

    const bs = this._s("bronstatus");
    if (bruikbaar(bs) && bs.state !== "alles in orde") {
      const haperend = (attr(bs, "haperend") || []).map((n) => BRONNAAM[n] || n);
      uit +=
        `<div class="melding let">${icoon("server")}<div><b>${esc(hoofd(bs.state))}</b><br>` +
        `<span>Getoonde waarden kunnen verouderd zijn${haperend.length ? PUNT + esc(haperend.join(", ")) : ""}</span></div></div>`;
    }
    return uit;
  }

  /* ---- statusrij ---- */

  _hero() {
    const sit = this._situatie();
    const s = (k) => this._s(k);

    // Bliksemgloed op de achtergrond bij nabij of naderend onweer
    if (this._root) {
      this._root.classList.toggle("flits-nabij", sit.code === "nabij");
      this._root.classList.toggle("flits", sit.code === "nadert");
    }

    const tegel = (niveau, inhoud) =>
      `<div class="tegel" style="--accent:${niveauKleur(niveau)};--accent-zacht:${zacht(niveau)}">${inhoud}</div>`;
    const zacht = (niveau) =>
      ({
        groen: "rgba(52,211,153,.10)",
        geel: "rgba(250,204,21,.12)",
        oranje: "rgba(251,146,60,.16)",
        rood: "rgba(251,77,101,.20)",
      })[niveau] || "transparent";

    // 1. Situatie
    const afstand = getal(s("afstand"));
    const az = getal(s("azimut"));
    const eta = getal(s("aankomst"));
    const freq = getal(s("frequentie"));
    const trend = bruikbaar(s("trend")) ? s("trend").state : null;
    let regel;
    if (afstand != null) {
      regel = `Dichtstbij <b>${fmt(afstand, 1)} km</b>${kompas(az) ? " in het <b>" + kompas(az) + "</b>" : ""}`;
      if (sit.code === "nabij" && s("schuilen") && s("schuilen").state === "on") {
        regel += `${PUNT}nu boven je${freq != null ? ", " + fmt(freq) + " inslagen per minuut" : ""}`;
      } else if (eta != null) {
        regel += `${PUNT}hier over <b>${fmt(eta)} min</b>`;
      } else if (trend) {
        regel += PUNT + esc(trend);
      }
    } else {
      regel = "Geen blikseminslagen binnen bereik";
    }
    const situatie = tegel(
      sit.niveau,
      `<div class="lbl">Situatie</div><div class="big accent">${sit.tekst.toUpperCase()}</div>` +
        `<div class="sub">${regel}</div>`
    );

    // 2. Waarschuwing
    let waarschuwing = "";
    const nv = s("niveau");
    if (nv) {
      const niveau = bruikbaar(nv) ? nv.state : null;
      const bron = attr(nv, "bron") === "knmi" ? "KNMI" : attr(nv, "bron") ? "MeteoAlarm" : "Waarschuwing";
      const lijst = attr(nv, "waarschuwingen") || [];
      const eerste = lijst[0] || {};
      const actief = niveau && niveau !== "groen";
      const soort = attr(nv, "soort") || eerste.soort;
      const gebied = attr(nv, "gebied") || eerste.gebied;
      const tot = klokTijd(eerste.tot);
      waarschuwing = tegel(
        actief ? niveau : "groen",
        `<div class="lbl">${esc(bron)}-waarschuwing</div>` +
          `<div class="big accent">${actief ? "CODE " + esc(niveau.toUpperCase()) : "GEEN CODE"}</div>` +
          `<div class="sub">${
            actief
              ? `<b>${esc(hoofd(soort || "weerwaarschuwing"))}</b>${gebied ? PUNT + esc(gebied) : ""}${tot ? PUNT + "tot " + tot : ""}`
              : niveau
                ? "Geen waarschuwing voor jouw regio"
                : "Nog geen gegevens"
          }</div>`
      );
    }

    // 3. Onweersverwachting
    let verwachting = "";
    const vw = s("verwachting");
    if (vw) {
      const tekst = bruikbaar(vw) ? vw.state : null;
      const toel = attr(vw, "toelichting");
      const l = (tekst || "").toLowerCase();
      const niveau = l.includes("noodweer")
        ? "rood"
        : l.includes("zwaar")
          ? "oranje"
          : l.includes("kans op onweer")
            ? "geel"
            : l.includes("kleine")
              ? "geel"
              : "groen";
      verwachting = tegel(
        tekst ? niveau : "groen",
        `<div class="lbl">Onweersverwachting</div>` +
          `<div class="tekst-m">${tekst ? esc(hoofd(tekst)) : `<span class="leeg">${STREEP}</span>`}</div>` +
          (toel ? `<div class="sub klem">${esc(hoofd(toel))}</div>` : "")
      );
    }

    // 4. Chase-potentie
    let potentie = "";
    const pt = s("potentie");
    if (pt) {
      const p = getal(pt);
      const niveau = drempelNiveau(p, [20, 40, 70]);
      const deel = (naam, max, label) => {
        const v = attr(pt, naam);
        return v == null ? "" : `<span>${label}<b>${fmt(v)}/${max}</b></span>`;
      };
      const oordeel =
        p == null ? "" : p > 70 ? "Alle ingredi\u00ebnten aanwezig" : p > 40 ? "Kans op onweer aanwezig" : p > 20 ? "Beperkte kans" : "Weinig te verwachten";
      potentie = tegel(
        p == null ? "groen" : niveau,
        `<div class="lbl">Chase-potentie</div><div class="pot">${ring(p, niveauKleur(p == null ? "" : niveau), 88)}` +
          `<div class="opbouw"><div class="sub"><b>${esc(oordeel)}</b></div>` +
          deel("cape_bijdrage", 50, "CAPE") +
          deel("stabiliteit_bijdrage", 30, "Stabiliteit") +
          deel("inslagen_bijdrage", 20, "Inslagen") +
          `</div></div>`
      );
    }

    return situatie + waarschuwing + verwachting + potentie;
  }

  /* ---- radar ---- */

  _radar(el) {
    const radar = this._s("radar");
    const vooruit = this._s("vooruitblik");
    const heeftVooruit = !!vooruit && !onbeschikbaar(vooruit);
    if (!radar && !heeftVooruit) {
      el.hidden = true;
      return undefined;
    }
    el.hidden = false;

    const modus = this._radarModus === "vooruit" && heeftVooruit ? "vooruit" : radar ? "nu" : "vooruit";
    const bron = modus === "vooruit" ? vooruit : radar;

    // Kop met bron, leeftijd en de schakelaar
    const radarbron = attr(radar, "radarbron");
    let leeftijd = attr(radar, "beeld_leeftijd_minuten");
    const beeldTijd = attr(radar, "beeld_tijd");
    if (beeldTijd) {
      const d = alsDatum(beeldTijd);
      if (d) leeftijd = Math.max(0, Math.round((Date.now() - d.getTime()) / 60000));
    }
    const chips =
      (modus === "nu" && radarbron ? chip(esc(String(radarbron).toUpperCase().replace("_", " "))) : "") +
      (modus === "nu" && leeftijd != null
        ? chip(`${icoon("klok")}${fmt(leeftijd)} min oud`, leeftijd > 15 ? "let" : "")
        : "") +
      (modus === "vooruit"
        ? chip(`${fmt(Math.abs(attr(vooruit, "van_minuten") || 60))} min terug tot +${fmt(attr(vooruit, "tot_minuten") || 120)} min`)
        : "");
    const wissel = heeftVooruit && radar
      ? `<div class="wissel" role="group" aria-label="Radarweergave">` +
        `<button data-modus="nu" aria-pressed="${modus === "nu"}">Nu</button>` +
        `<button data-modus="vooruit" aria-pressed="${modus === "vooruit"}">Vooruitblik</button></div>`
      : "";
    const kop = paneelKop("radar", modus === "vooruit" ? "Radar vooruitblik" : "Radar", chips + wissel);
    const kopEl = el.querySelector(".radarkop");
    if (this._html.radarkop !== kop) {
      this._html.radarkop = kop;
      kopEl.innerHTML = kop;
    }

    const hoek = el.querySelector(".radar-hoek");
    const tijd = modus === "nu" ? klokTijd(beeldTijd) : klokTijd(attr(vooruit, "referentietijd"));
    const hoekHtml = tijd ? chip(`${modus === "nu" ? "Beeld" : "Referentie"} ${tijd}`) : "";
    if (this._html.radarhoek !== hoekHtml) {
      this._html.radarhoek = hoekHtml;
      hoek.innerHTML = hoekHtml;
    }

    // Het beeld zelf: alleen wisselen als de URL echt verandert, en pas
    // als het nieuwe beeld binnen is, zodat er niets knippert.
    const geen = el.querySelector(".geen");
    const plaatje = bron && attr(bron, "entity_picture");
    if (!plaatje || onbeschikbaar(bron)) {
      this._img.hidden = true;
      geen.hidden = false;
      this._radarUrl = null;
      return undefined;
    }
    let url = this._hass.hassUrl ? this._hass.hassUrl(plaatje) : plaatje;
    if (!/^(data|blob):/.test(url)) {
      url += (url.includes("?") ? "&" : "?") + "v=" + encodeURIComponent(bron.state);
    }
    if (url !== this._radarUrl) {
      this._radarUrl = url;
      const laad = new Image();
      laad.onload = () => {
        if (this._radarUrl !== url) return;
        this._img.src = url;
        this._img.hidden = false;
        geen.hidden = true;
      };
      laad.onerror = () => {
        if (this._radarUrl !== url) return;
        if (!this._img.getAttribute("src")) {
          this._img.hidden = true;
          geen.hidden = false;
        }
      };
      laad.src = url;
    }
    return undefined;
  }

  /* ---- bliksem ---- */

  _bliksem() {
    const s = (k) => this._s(k);
    const heeftIets =
      s("afstand") || s("azimut") || s("nabij") || s("nadert") || this._ringen.length;
    if (!heeftIets) return null;

    const sit = this._situatie();
    const kleur = niveauKleur(sit.niveau);
    const afstand = getal(s("afstand"));
    const az = getal(s("azimut"));
    const cel = s("celrichting");
    const celGraden = Number.isFinite(Number(attr(cel, "graden"))) && attr(cel, "graden") != null ? Number(attr(cel, "graden")) : null;

    const roos = kompasroos({ az, km: afstand, ringen: this._ringen, celGraden, kleur });

    const nadering = getal(s("nadering"));
    const eta = getal(s("aankomst"));
    const freq = getal(s("frequentie"));
    let naderingTekst = STREEP;
    let naderingSub = "";
    if (nadering != null) {
      naderingTekst = `${fmtTeken(nadering)}<small>km/u</small>`;
      naderingSub = nadering > 1 ? "nadert" : nadering < -1 ? "trekt weg" : "staat stil";
    }
    const schuilen = s("schuilen") && s("schuilen").state === "on";

    const kern =
      `<div class="duo3">` +
      `<div class="mini"><div class="lbl">Dichtstbij</div>` +
      `<div class="w" style="color:${afstand != null ? kleur : "inherit"}">${afstand != null ? fmt(afstand, 1) + "<small>km</small>" : `<span class="leeg">${STREEP}</span>`}</div>` +
      `<div class="s">${az != null ? `${kompas(az)}${PUNT}${fmt(az)}\u00b0` : "geen richting"}</div></div>` +
      (s("nadering")
        ? `<div class="mini"><div class="lbl">Nadering</div><div class="w">${naderingTekst}</div><div class="s">${naderingSub || STREEP}</div></div>`
        : "") +
      (s("aankomst") || schuilen
        ? `<div class="mini"><div class="lbl">Aankomst</div><div class="w">${
            schuilen ? "nu" : eta != null ? fmt(eta) + "<small>min</small>" : `<span class="leeg">${STREEP}</span>`
          }</div><div class="s">${schuilen ? "nu boven je" : eta != null ? "rond " + klokTijd(Date.now() + eta * 60000) : "geen nadering"}</div></div>`
        : "") +
      `</div>`;

    // Inslagen per ring
    let ringen = "";
    if (this._ringen.length) {
      const waarden = this._ringen.map((r) => ({ km: r.km, v: getal(this._hass.states[r.id]), s: this._hass.states[r.id] }));
      const hoogst = Math.max(1, ...waarden.map((w) => w.v || 0));
      const kleuren = ["var(--rood)", "var(--oranje)", "var(--geel)", "var(--violet)"];
      ringen =
        `<div class="ringen">` +
        waarden
          .map(
            (w, i) =>
              `<div class="ringrij${onbeschikbaar(w.s) ? " dim" : ""}"><span>\u2264 ${w.km} km</span>` +
              balk({ v: w.v || 0, min: 0, max: hoogst, kleur: (w.v || 0) > 0 ? kleuren[Math.min(i, 3)] : "transparent" }) +
              `<b>${w.v != null ? fmt(w.v) : STREEP}</b></div>`
          )
          .join("") +
        `</div>`;
    }

    const minis = [];
    if (s("frequentie")) {
      const t = attr(s("frequentie"), "trend");
      minis.push(
        `<div class="mini"><div class="lbl">Inslagfrequentie</div><div class="w">${waardeHtml(s("frequentie"), 0, "/min")}</div>` +
          `<div class="s">${t ? esc(t) : STREEP}</div></div>`
      );
    }
    if (s("markers")) {
      minis.push(
        `<div class="mini"><div class="lbl">Inslagen in bereik</div><div class="w">${waardeHtml(s("markers"))}</div>` +
          `<div class="s">${bruikbaar(s("trend")) ? esc(s("trend").state) : STREEP}</div></div>`
      );
    }

    // Cel als geheel: waar trekt hij heen en komt hij hier langs?
    let celregel = "";
    if (bruikbaar(cel)) {
      const snelheid = getal(s("celsnelheid"));
      const over = getal(s("passage"));
      const passeer = getal(s("passageafstand"));
      const aantal = attr(cel, "aantal_cellen");
      celregel =
        `<div class="celregel">Cel trekt naar het <b>${esc(cel.state)}</b>` +
        `${snelheid != null ? " met <b>" + fmt(snelheid) + " km/u</b>" : ""}<br>` +
        (over != null
          ? `Passeert over <b>${fmt(over)} min</b>${passeer != null ? " op <b>" + fmt(passeer, 1) + " km</b>" : ""}`
          : "Trekt weg of staat stil") +
        `${aantal > 1 ? PUNT + fmt(aantal) + " cellen gevolgd" : ""}</div>`;
    }

    const vlag = (sleutel, aan, uit) => {
      const st = s(sleutel);
      if (!st) return "";
      return st.state === "on" ? chip(aan, "gevaar") : chip(uit, onbeschikbaar(st) ? "uit" : "");
    };
    const vlaggen =
      vlag("nabij", "Onweer nabij", "Niet nabij") +
      vlag("nadert", "Onweer nadert", "Nadert niet") +
      vlag("schuilen", "Schuilen", "Geen schuilplicht");

    return (
      paneelKop("flits", "Bliksem", chip(sit.tekst, sit.code === "rustig" ? "ok" : sit.code === "nabij" ? "gevaar" : "let")) +
      `<div class="pb"><div class="bl-top">${roos}</div>${kern}` +
      ringen +
      (minis.length ? `<div class="duo">${minis.join("")}</div>` : "") +
      celregel +
      (vlaggen ? `<div class="vlaggen">${vlaggen}</div>` : "") +
      `</div>`
    );
  }

  /* ---- convectie ---- */

  _convectie() {
    const s = (k) => this._s(k);
    const rijen = [];

    const meter = (sleutel, label, opties) => {
      const st = s(sleutel);
      if (!st) return;
      const v = getal(st);
      const niveau = opties.niveau(v);
      rijen.push(
        `<div class="meterrij${onbeschikbaar(st) ? " dim" : ""}"><div class="meterkop"><span class="lbl">${label}</span>` +
          `<span class="w" style="color:${v == null ? "inherit" : niveauKleur(niveau)}">${waardeHtml(st, opties.dec || 0, opties.eenheid)}</span></div>` +
          balk({
            v,
            min: opties.min,
            max: opties.max,
            drempels: opties.drempels,
            kleur: niveauKleur(niveau),
            omgekeerd: opties.omgekeerd,
          }) +
          (opties.noot ? `<div class="meternoot">${opties.noot}</div>` : "") +
          `</div>`
      );
    };

    const capeNiveau = (v) => drempelNiveau(v, [300, 1000, 2500]);
    meter("cape", "CAPE nu", { min: 0, max: 3000, drempels: [300, 1000, 2500], eenheid: "J/kg", niveau: capeNiveau });
    meter("capePiek", "CAPE piek 12 uur", { min: 0, max: 3000, drempels: [300, 1000, 2500], eenheid: "J/kg", niveau: capeNiveau });
    meter("li", "Lifted Index", {
      min: -10,
      max: 6,
      omgekeerd: true,
      dec: 1,
      drempels: [0, -3, -6],
      niveau: (v) => (v == null ? "geen" : v < -6 ? "rood" : v < -3 ? "oranje" : v < 0 ? "geel" : "groen"),
    });
    meter("schering6", "Windschering 0\u20136 km", {
      min: 0,
      max: 100,
      drempels: [30, 50, 72],
      eenheid: "km/u",
      niveau: (v) => drempelNiveau(v, [30, 50, 72]),
      noot: (() => {
        const d = attr(s("verwachting"), "windschering");
        return d ? esc(hoofd(d)) : "";
      })(),
    });

    const ens = s("ensemble");
    if (ens) {
      const zwaar = attr(ens, "kans_zwaar");
      const leden = attr(ens, "leden");
      const duiding = attr(ens, "duiding");
      meter("ensemble", "Onweerskans ensemble", {
        min: 0,
        max: 100,
        drempels: [10, 30, 60],
        eenheid: "%",
        niveau: (v) => drempelNiveau(v, [10, 30, 60]),
        noot: [
          duiding && duiding !== "onbekend" ? esc(hoofd(duiding)) : "",
          zwaar != null ? `${fmt(zwaar)}% kans op zwaar` : "",
          leden ? `${fmt(leden)} leden` : "",
        ]
          .filter(Boolean)
          .join(PUNT),
      });
    }

    // Modelovereenstemming: het oordeel plus de bandbreedte van de CAPE
    const ov = s("overeenstemming");
    if (ov) {
      const laag = attr(ov, "laagste");
      const hoog = attr(ov, "hoogste");
      const med = attr(ov, "mediaan");
      const n = attr(ov, "aantal_modellen");
      const o = bruikbaar(ov) ? ov.state : "";
      const niveau = o.includes("eens") ? "groen" : o.includes("wat af") ? "oranje" : o.includes("verdeeld") ? "rood" : "geen";
      let bereik = "";
      if (Number.isFinite(laag) && Number.isFinite(hoog)) {
        const max = Math.max(3000, hoog);
        const p = (v) => ((Math.max(0, v) / max) * 100).toFixed(1);
        bereik =
          `<div class="bereik" title="Laagste tot hoogste CAPE over de modellen"><div class="lijn"></div>` +
          `<div class="span" style="left:${p(laag)}%;width:${Math.max(0.8, p(hoog) - p(laag)).toFixed(1)}%"></div>` +
          (Number.isFinite(med) ? `<div class="med" style="left:calc(${p(med)}% - 1px)"></div>` : "") +
          `</div><div class="meternoot">CAPE ${fmt(laag)}\u2013${fmt(hoog)} J/kg${Number.isFinite(med) ? PUNT + "mediaan " + fmt(med) : ""}${n ? PUNT + fmt(n) + " modellen" : ""}</div>`;
      }
      rijen.push(
        `<div class="meterrij${onbeschikbaar(ov) ? " dim" : ""}"><div class="meterkop"><span class="lbl">Modelovereenstemming</span>` +
          `<span class="w" style="font-size:14px;color:${niveauKleur(niveau)}">${o ? esc(hoofd(o)) : STREEP}</span></div>${bereik}</div>`
      );
    }

    // De rest compact in een raster
    const kv = [];
    const vak = (sleutel, label, dec, eenheid, kleurFn) => {
      const st = s(sleutel);
      if (!st) return;
      const v = getal(st);
      const kleur = kleurFn && v != null ? `style="color:${niveauKleur(kleurFn(v))}"` : "";
      kv.push(
        `<div class="${onbeschikbaar(st) ? "dim" : ""}"><span class="lbl">${label}</span><b ${kleur}>${waardeHtml(st, dec, eenheid)}</b></div>`
      );
    };
    vak("rotatie", "Rotatie", 0, "%", (v) => drempelNiveau(v, [10, 30, 60]));
    vak("hagel", "Hagel", 0, "%", (v) => drempelNiveau(v, [10, 30, 60]));
    vak("schering1", "Schering 0\u20131", 0, "km/u", (v) => drempelNiveau(v, [15, 30, 45]));
    vak("tt", "Total Totals", 0, "", (v) => drempelNiveau(v, [44, 50, 56]));
    vak("lpi", "LPI", 1, "J/kg", (v) => drempelNiveau(v, [1, 5, 20]));
    vak("wolkentop", "Wolkentop", 0, "m", (v) => drempelNiveau(v, [4000, 8000, 11000]));
    vak("vriesniveau", "Vriesniveau", 0, "m");
    vak("cin", "CIN", 0, "J/kg");
    vak("updraft", "Updraft", 0, "m/s", (v) => drempelNiveau(v, [5, 10, 20]));

    // De duiding in gewone taal, uit de onweersverwachting
    const vw = s("verwachting");
    const duidingen = [
      ["Energie", attr(vw, "energie")],
      ["Stabiliteit", attr(vw, "stabiliteit")],
      ["Opwaartse stroming", attr(vw, "opwaartse_stroming")],
      ["Wolkentop", attr(vw, "wolkentop")],
      ["Draaiing met hoogte", bruikbaar(s("hodograaf")) ? s("hodograaf").state : null],
    ].filter(([, t]) => t && t !== "onbekend");
    const duiding = duidingen.length
      ? `<div class="duiding">${duidingen.map(([l, t]) => `<div><span>${l}</span><b>${esc(hoofd(t))}</b></div>`).join("")}</div>`
      : "";

    if (!rijen.length && !kv.length) return null;

    const pt = s("potentie");
    const p = getal(pt);
    return (
      paneelKop("meter", "Convectie", p != null ? chip(`Potentie ${fmt(p)}%`, p > 40 ? "let" : "") : "") +
      `<div class="pb"><div class="meters">${rijen.join("")}</div>` +
      (kv.length ? `<div class="kv">${kv.join("")}</div>` : "") +
      duiding +
      `</div>`
    );
  }

  /* ---- waarschuwingen ---- */

  _knmi() {
    const nv = this._s("niveau");
    if (!nv) return null;
    const niveau = bruikbaar(nv) ? nv.state : null;
    const bron = attr(nv, "bron") === "knmi" ? "KNMI" : attr(nv, "bron") ? "MeteoAlarm" : null;
    const lijst = attr(nv, "waarschuwingen") || [];
    const eerste = lijst[0] || null;
    const actief = !!niveau && niveau !== "groen";
    const kleur = niveauKleur(actief ? niveau : "groen");
    const zacht = {
      geel: "rgba(250,204,21,.35)",
      oranje: "rgba(251,146,60,.4)",
      rood: "rgba(251,77,101,.45)",
    }[niveau] || "rgba(52,211,153,.25)";

    let inhoud;
    if (actief) {
      const soort = attr(nv, "soort") || (eerste && eerste.soort);
      const gebied = attr(nv, "gebied") || (eerste && eerste.gebied);
      const van = eerste && klokTijd(eerste.vanaf);
      const tot = eerste && klokTijd(eerste.tot);
      const aantal = Number(attr(nv, "aantal") || lijst.length || 0);
      inhoud =
        `<div class="code" style="--accent:${kleur};--accent-zacht:${zacht}">` +
        `<div class="codebord">Code ${esc(niveau)}</div><div class="codetekst">` +
        `<div class="t">${esc(hoofd(soort || "weerwaarschuwing"))}</div>` +
        `<div class="s">${[gebied ? esc(gebied) : "", van && tot ? `${van}\u2013${tot}` : tot ? "tot " + tot : "", aantal > 1 ? `${aantal} waarschuwingen` : ""].filter(Boolean).join(PUNT)}</div>` +
        `</div></div>` +
        (eerste && eerste.omschrijving ? `<div class="omschrijving klem">${esc(eerste.omschrijving)}</div>` : "");
      const inLand = Number(attr(nv, "aantal_in_land") || 0);
      const elders = Math.max(0, inLand - aantal);
      const vakjes = [
        van ? `<div class="mini"><div class="lbl">Vanaf</div><div class="w">${van}</div><div class="s">${esc(beginTekst(eerste.vanaf))}</div></div>` : "",
        tot ? `<div class="mini"><div class="lbl">Tot</div><div class="w">${tot}</div><div class="s">${esc(nogTijd(eerste.tot))}</div></div>` : "",
        attr(nv, "aantal_in_land") != null
          ? `<div class="mini"><div class="lbl">Landelijk</div><div class="w">${fmt(elders)}</div><div class="s">elders actief</div></div>`
          : "",
      ].filter(Boolean);
      if (vakjes.length) inhoud += `<div class="duo3">${vakjes.join("")}</div>`;
    } else {
      const inLand = Number(attr(nv, "aantal_in_land") || 0);
      inhoud =
        `<div class="code" style="--accent:${kleur};--accent-zacht:${zacht}">` +
        `<div class="codebord groen">Geen code</div><div class="codetekst">` +
        `<div class="t">${niveau ? "Geen waarschuwing voor jouw regio" : "Nog geen gegevens"}</div>` +
        `<div class="s">${[attr(nv, "gebied") ? esc(attr(nv, "gebied")) : "", inLand > 0 ? `${inLand} waarschuwing${inLand === 1 ? "" : "en"} elders in het land` : ""].filter(Boolean).join(PUNT)}</div>` +
        `</div></div>`;
    }

    // Tijdlijn van de komende 24 uur
    let tijdlijn = "";
    const perUur = attr(nv, "niveau_per_uur");
    if (Array.isArray(perUur) && perUur.length) {
      const uren = perUur.slice(0, 24);
      const blokken = uren
        .map((u, i) => {
          const t = klokTijd(u.tijd) || "";
          const n = ["geel", "oranje", "rood"].includes(u.niveau) ? u.niveau : "";
          return `<span class="${n}${i === 0 ? " nu" : ""}" title="${t}: ${esc(u.niveau || "geen")}"></span>`;
        })
        .join("");
      const as = uren
        .map((u, i) => {
          const d = alsDatum(u.tijd);
          return `<span>${d && i % 3 === 0 ? String(d.getHours()).padStart(2, "0") : ""}</span>`;
        })
        .join("");
      tijdlijn =
        `<div class="tijdlijn"><div class="lbl">Komende ${uren.length} uur</div>` +
        `<div class="tl-balk">${blokken}</div><div class="tl-as">${as}</div>` +
        `<div class="tl-legenda"><span><i style="background:rgba(255,255,255,.12)"></i>geen</span>` +
        `<span><i style="background:var(--geel)"></i>geel</span><span><i style="background:var(--oranje)"></i>oranje</span>` +
        `<span><i style="background:var(--rood)"></i>rood</span></div></div>`;
    }

    const regio = attr(nv, "regio");
    return (
      paneelKop(
        "waarschuwing",
        bron === "KNMI" ? "KNMI-waarschuwingen" : "Weerwaarschuwingen",
        (bron ? chip(bron) : "") + (regio != null && bron === "KNMI" ? chip(`regio ${esc(regio)}`) : "")
      ) + `<div class="pb">${inhoud}${tijdlijn}</div>`
    );
  }

  /* ---- waarnemingen ---- */

  _waarneming() {
    const s = (k) => this._s(k);
    const m = s("meting");
    const st = s("stoten");
    const dr = s("druk");
    if (!m && !st && !dr) return null;

    const bronTekst = (b) => (b === "knmi_edr" ? "KNMI" : b === "brightsky" ? "Bright Sky" : b ? String(b) : null);
    const station = attr(m, "station") || attr(st, "windstoten_station") || attr(dr, "luchtdruk_station");
    const stAfstand = attr(m, "station_afstand_km");
    const waargenomen = attr(m, "waargenomen_op") || attr(st, "waargenomen_op");
    const bron = bronTekst(attr(m, "bron") || attr(st, "bron"));

    const vakken = [];

    // Windstoten
    if (st || m) {
      const v = getal(st) != null ? getal(st) : attr(m, "windstoten");
      const bft = attr(st, "windstoten_bft") != null ? attr(st, "windstoten_bft") : beaufort(attr(m, "windstoten_ms"));
      const niveau = v == null ? "geen" : drempelNiveau(v, [50, 75, 100]);
      const stationW = attr(st, "windstoten_station");
      const anders = stationW && station && stationW !== station;
      vakken.push(
        `<div class="mini${onbeschikbaar(st) ? " dim" : ""}"><div class="lbl">Windstoten</div>` +
          `<div class="w" style="color:${v != null ? niveauKleur(niveau) : "inherit"}">${v != null ? fmt(v) + "<small>km/u</small>" : `<span class="leeg">${STREEP}</span>`}</div>` +
          `<div class="s">${bft != null ? "Beaufort " + fmt(bft) : STREEP}${anders ? PUNT + esc(stationW) : ""}</div></div>`
      );
    }

    // Luchtdruk met verloop
    if (dr) {
      const d1 = getal(s("druk1"));
      const d3 = getal(s("druk3"));
      const pijl = (d) => {
        if (d == null) return "";
        const klasse = d <= -2 ? "daalt-hard" : d <= -0.5 ? "daalt" : d >= 0.5 ? "stijgt" : "";
        const teken = d <= -0.5 ? "\u2198" : d >= 0.5 ? "\u2197" : "\u2192";
        return `<span class="trend ${klasse}">${teken} ${fmtTeken(d, 1)}</span>`;
      };
      const tendens = attr(s("druk1"), "druk_tendens_1u") || attr(dr, "druk_tendens_1u");
      vakken.push(
        `<div class="mini${onbeschikbaar(dr) ? " dim" : ""}"><div class="lbl">Luchtdruk</div>` +
          `<div class="w">${waardeHtml(dr, 1, "hPa")}</div>` +
          `<div class="s">${d1 != null ? pijl(d1) + " /u" : ""}${d3 != null ? (d1 != null ? PUNT : "") + pijl(d3) + " /3u" : ""}${d1 == null && d3 == null ? (tendens ? esc(tendens) : STREEP) : ""}</div></div>`
      );
    }

    if (m) {
      const dauw = attr(m, "dauwpunt");
      const rv = attr(m, "luchtvochtigheid");
      vakken.push(
        `<div class="mini${onbeschikbaar(m) ? " dim" : ""}"><div class="lbl">Temperatuur</div>` +
          `<div class="w">${waardeHtml(m, 1, "\u00b0C")}</div>` +
          `<div class="s">${dauw != null ? "Dauwpunt " + fmt(dauw, 1) + "\u00b0" : STREEP}${rv != null ? PUNT + fmt(rv) + "%" : ""}</div></div>`
      );
      const zicht = attr(m, "zicht");
      if (zicht != null) {
        vakken.push(
          `<div class="mini"><div class="lbl">Zicht</div>` +
            `<div class="w">${zicht >= 1000 ? fmt(zicht / 1000, zicht < 10000 ? 1 : 0) + "<small>km</small>" : fmt(zicht) + "<small>m</small>"}</div>` +
            `<div class="s">${zicht < 1000 ? "slecht zicht" : zicht < 5000 ? "matig" : "goed"}</div></div>`
        );
      }
      const basis = attr(m, "wolkenbasis");
      const bew = attr(m, "bewolking");
      if (basis != null || bew != null) {
        vakken.push(
          `<div class="mini"><div class="lbl">Wolkenbasis</div>` +
            `<div class="w">${basis != null ? fmt(basis) + "<small>m</small>" : `<span class="leeg">${STREEP}</span>`}</div>` +
            `<div class="s">${bew != null ? "Bewolking " + fmt(bew) + "%" : STREEP}</div></div>`
        );
      }
      const wind = attr(m, "wind");
      const richting = attr(m, "windrichting");
      if (wind != null) {
        vakken.push(
          `<div class="mini"><div class="lbl">Wind</div>` +
            `<div class="w">${fmt(wind)}<small>km/u</small></div>` +
            `<div class="s">${richting != null ? "uit het " + kompas(richting) + PUNT + fmt(richting) + "\u00b0" : STREEP}</div></div>`
        );
      }
    }

    const badges = [];
    const ow = s("onweerGemeten");
    if (ow) badges.push(ow.state === "on" ? chip(`${icoon("flits")}Onweer gemeten`, "gevaar") : chip("Geen onweer gemeten", onbeschikbaar(ow) ? "uit" : ""));
    const hg = s("hagelGemeten");
    if (hg) badges.push(hg.state === "on" ? chip("Hagel gemeten", "gevaar") : chip("Geen hagel gemeten", onbeschikbaar(hg) ? "uit" : ""));

    const stationsregel = station
      ? `<div class="station"><b>${esc(station)}</b>${stAfstand != null ? PUNT + fmt(stAfstand, 1) + " km" : ""}` +
        `${waargenomen ? PUNT + "gemeten " + klokTijd(waargenomen) : ""}</div>`
      : "";

    return (
      paneelKop("station", "Waarnemingen", bron ? chip(esc(bron)) : "") +
      `<div class="pb">${stationsregel}<div class="obs">${vakken.join("")}</div>` +
      (badges.length ? `<div class="vlaggen">${badges.join("")}</div>` : "") +
      `</div>`
    );
  }

  /* ---- neerslag ---- */

  _neerslag() {
    const s = (k) => this._s(k);
    const start = s("regenStart");
    const intensiteit = s("regenIntensiteit");
    if (!start && !intensiteit) return null;

    const reeks = attr(start, "verwachting");
    const regent = attr(start, "regent");
    const over = getal(start);
    const stopt = attr(start, "stopt_over");
    const piek = getal(s("regenPiek"));
    const totaal = attr(start, "totaal_mm_2u");
    const nu = getal(intensiteit);
    const bronRuw = attr(start, "bron");
    const bron = bronRuw ? BRONLABEL[bronRuw] || hoofd(String(bronRuw).replace("_", " ")) : null;

    let kop;
    let kleur = "var(--tekst)";
    if (regent) {
      const volgende = attr(start, "volgende_bui_over");
      kop = `Het regent${stopt != null ? ", nog ~" + fmt(stopt) + " min" : ""}` +
        (volgende != null ? `${PUNT}volgende bui over ${fmt(volgende)} min` : "");
      kleur = "var(--blauw)";
    } else if (over != null) {
      kop = `Regen over ${fmt(over)} min`;
      kleur = over <= 30 ? "var(--cyaan)" : "var(--tekst)";
    } else if (bruikbaar(start) || Array.isArray(reeks)) {
      kop = "Droog, komende 2 uur";
    } else {
      kop = STREEP;
    }

    const vakje = (label, v, eenheid, sub) =>
      `<div class="mini"><div class="lbl">${label}</div><div class="w"${v != null && v > 0 ? ` style="color:${regenKleur(v)}"` : ""}>` +
      `${v != null ? fmt(v, 1) + `<small>${eenheid}</small>` : `<span class="leeg">${STREEP}</span>`}</div><div class="s">${sub}</div></div>`;
    const vakjes = [
      intensiteit ? vakje("Nu", nu, "mm/u", regent ? "het regent" : "droog") : "",
      s("regenPiek") ? vakje("Piek", piek, "mm/u", "komende 2 uur") : "",
      totaal != null ? vakje("Totaal", Number(totaal), "mm", "komende 2 uur") : "",
    ].filter(Boolean);

    const grafiek = Array.isArray(reeks) && reeks.length
      ? neerslagGrafiek(reeks, regent ? null : over)
      : `<div class="leegmelding">Geen reeks per vijf minuten beschikbaar</div>`;

    return (
      paneelKop("druppel", "Neerslag komende 2 uur", bron ? chip(esc(bron)) : "") +
      `<div class="pb"><div class="ns-kop"><div class="tekst-m" style="color:${kleur}">${kop}</div></div>` +
      `${grafiek}${vakjes.length ? `<div class="duo3">${vakjes.join("")}</div>` : ""}</div>`
    );
  }

  /* ---- uurverwachting ---- */

  _verwachting() {
    const weer = this._s("weer");
    if (!weer) return null;
    const uren = (this._uurdata || [])
      .filter((u) => {
        const d = alsDatum(u.datetime);
        return d && d.getTime() > Date.now() - 3600000;
      })
      .slice(0, 12);

    const nuTemp = attr(weer, "temperature");
    const conditie = bruikbaar(weer) ? weer.state : null;
    const rechts =
      (conditie ? chip(esc(CONDITIE_TEKST[conditie] || conditie)) : "") +
      (nuTemp != null ? chip(`nu ${fmt(nuTemp, 1)}\u00b0C`) : "") +
      (attr(weer, "verwachting_bron") ? chip(attr(weer, "verwachting_bron") === "knmi" ? "KNMI" : "Open-Meteo") : "");

    if (!uren.length) {
      const tekst = this._verwachtingFout
        ? "Uurverwachting niet beschikbaar"
        : "Uurverwachting wordt geladen\u2026";
      return paneelKop("klok", "Verwachting per uur", rechts) + `<div class="leegmelding">${tekst}</div>`;
    }

    let vorigeDag = new Date().getDate();
    const kolommen = uren
      .map((u) => {
        const d = alsDatum(u.datetime);
        const dag = d.getDate() !== vorigeDag ? d.toLocaleDateString("nl-NL", { weekday: "short" }) : "";
        vorigeDag = d.getDate();
        const kans = u.precipitation_probability;
        const stoten = u.wind_gust_speed != null ? u.wind_gust_speed : u.wind_speed;
        const onweer = String(u.condition || "").startsWith("lightning");
        return (
          `<div class="uur${onweer ? " onweer" : ""}" title="${esc(CONDITIE_TEKST[u.condition] || u.condition || "")}">` +
          `<div class="h">${dag ? `<span class="dag">${esc(dag)}</span> ` : ""}${String(d.getHours()).padStart(2, "0")}:00</div>` +
          weerIcoon(u.condition) +
          `<b>${u.temperature != null ? fmt(u.temperature) + "\u00b0" : STREEP}</b>` +
          `<div class="kans">${kans != null ? fmt(kans) + "%" : STREEP}${balk({ v: kans || 0, min: 0, max: 100, kleur: "var(--blauw)" })}</div>` +
          `<div class="wind">${stoten != null ? fmt(stoten) + " km/u" : STREEP}</div></div>`
        );
      })
      .join("");

    return (
      paneelKop("klok", "Verwachting per uur", rechts) +
      `<div class="pb"><div class="uren">${kolommen}</div>` +
      `<div class="meternoot">Per uur: temperatuur, neerslagkans en windstoten</div></div>`
    );
  }

  /* ---- voet ---- */

  _voet() {
    const bs = this._s("bronstatus");
    let bronnen = "";
    if (bs) {
      const lijst = attr(bs, "bronnen") || {};
      const haperend = attr(bs, "haperend") || [];
      const knmi = attr(bs, "knmi");
      const regels = Object.entries(lijst)
        .map(([naam, info]) => {
          const t = bronToestand(naam, info, haperend);
          const pct = info && info.slaagpercentage != null ? `${fmt(info.slaagpercentage)}%` : "";
          const laatst = info && info.laatste_succes ? klokTijd(info.laatste_succes) : "";
          const titel = [
            BRONNAAM[naam] || naam,
            info && info.laatste_succes ? "laatst gelukt " + laatst + " (" + geleden(info.laatste_succes) + ")" : "",
            info && info.laatste_fout ? "laatste fout: " + info.laatste_fout : "",
          ]
            .filter(Boolean)
            .join(PUNT);
          return {
            t,
            html:
              `<div class="bron ${t}" title="${esc(titel)}"><span class="stip ${t}"></span>` +
              `<span class="n">${esc(BRONNAAM[naam] || naam)}</span>` +
              `<span class="p">${t === "ongebruikt" ? "ongebruikt" : pct || laatst || STREEP}</span></div>`,
          };
        })
        // Gebruikte bronnen eerst
        .sort((a, b) => (a.t === "ongebruikt") - (b.t === "ongebruikt"))
        .map((r) => r.html);
      const push = pushTekst(knmi && knmi.push);
      if (push) {
        regels.unshift(
          `<div class="bron ${push[1]}"><span class="stip ${push[1]}"></span><span class="n">KNMI push</span>` +
            `<span class="p">${esc(push[0])}${knmi.push.meldingen ? PUNT + fmt(knmi.push.meldingen) : ""}</span></div>`
        );
      }
      bronnen = `<div class="pb"><div class="bronnen">${regels.join("")}</div></div>`;
    }

    return (
      paneelKop(
        "server",
        "Bronstatus",
        bs ? chip(esc(hoofd(bs.state)), bs.state === "alles in orde" ? "ok" : "let") : ""
      ) +
      bronnen +
      `<div class="voetregel"><span>StormchaseNL${VERSIE !== "onbekend" ? " v" + esc(VERSIE) : ""}` +
      `${PUNT}Blitzortung, KNMI, Open-Meteo, Buienradar</span>` +
      `<span>Hulpmiddel, geen veiligheidsadvies. Bij onweer: schuil binnen.</span></div>`
    );
  }
}

/* ------------------------------------------------------------------ */
/* De strategie                                                        */
/* ------------------------------------------------------------------ */

const KAART = "stormchase-hud-card";

/* Opties die de kaart zelf gebruikt; de rest is voor de strategie. */
const KAARTOPTIES = ["title", "distance_entity", "azimuth_entity", "counter_entity"];

const FRAME_STYLE = `
  ha-card {
    border: 1px solid rgba(255, 255, 255, .07);
    border-radius: 18px;
    overflow: hidden;
  }
`;

class StormchaseStrategy {
  /** De hoofdview: het commandocentrum over de volle breedte. */
  static hoofdView(config) {
    const kaart = { type: `custom:${KAART}` };
    for (const sleutel of KAARTOPTIES) {
      if (config[sleutel] != null) kaart[sleutel] = config[sleutel];
    }
    return { type: "panel", cards: [kaart] };
  }

  /** Kaarten van derden in een eigen tab (ingebouwde iframe-kaart). */
  static kaartenView(config, hass) {
    const kaarten = config.maps || {};
    const smal = typeof window !== "undefined" && window.innerWidth > 0 && window.innerWidth < 700;
    const verhouding = (breed, mobiel) => config.map_ratio || (smal ? mobiel : breed);
    const actief = Object.values(hass.states).find(
      (s) => /^sensor\.(.+_)?stormchase_(actieve_locatie|location)$/.test(s.entity_id)
    );
    const lat = Number(config.latitude ?? actief?.attributes?.latitude ?? hass.config.latitude).toFixed(2);
    const lon = Number(config.longitude ?? actief?.attributes?.longitude ?? hass.config.longitude).toFixed(2);

    const kop = (heading, icon) => ({ type: "heading", heading, heading_style: "title", icon });
    const sectie = (titel, icon, url, ratio) => ({
      type: "grid",
      cards: [kop(titel, icon), { type: "iframe", url, aspect_ratio: ratio, card_mod: { style: FRAME_STYLE } }],
    });
    const secties = [];

    if (kaarten.iradar !== false) {
      secties.push({
        ...sectie("iRadar \u00b7 radar & celdetectie", "mdi:radar", config.iradar_url || "https://iradar.app/", config.radar_ratio || verhouding("62%", "150%")),
        column_span: 2,
      });
    }
    if (kaarten.buienradar !== false) {
      secties.push(
        sectie(
          "Buienradar \u00b7 neerslag 2 uur",
          "mdi:weather-pouring",
          `https://gadgets.buienradar.nl/gadget/zoommap/?lat=${lat}&lng=${lon}&overname=2&zoom=10&size=3&voor=1`,
          verhouding("78%", "115%")
        )
      );
    }
    if (kaarten.windy !== false) {
      secties.push(
        sectie(
          "Windy \u00b7 CAPE",
          "mdi:weather-lightning-rainy",
          `https://embed.windy.com/embed2.html?lat=${lat}&lon=${lon}&zoom=9` +
            "&overlay=cape&type=map&metricWind=km%2Fh&metricTemp=%C2%B0C" +
            "&menu=&message=&marker=&calendar=&pressure=&location=coordinates" +
            "&detail=&radarRange=-1",
          verhouding("75%", "120%")
        )
      );
    }
    // Blitzortung blokkeerde het insluiten in augustus 2026; alleen op verzoek
    if (kaarten.blitzortung === true) {
      secties.push(
        sectie(
          "Blitzortung \u00b7 live inslagen",
          "mdi:flash-outline",
          "https://map.blitzortung.org/index.php?interactive=1&NavigationControl=1" +
            "&FullScreenControl=0&Cookies=0&InfoDiv=0&MenuButtonDiv=0&ScaleControl=1" +
            `&Advertisment=0&MapStyle=1&MapStyleRangeValue=3#8/${lat}/${lon}`,
          verhouding("75%", "120%")
        )
      );
    }
    if (kaarten.satelliet === true) {
      secties.push(
        sectie(
          "Satelliet en bliksem",
          "mdi:satellite-variant",
          config.satelliet_url || "https://www.meteox.com/nl-nl/satellite",
          verhouding("75%", "120%")
        )
      );
    }
    if (!secties.length) return null;
    return { type: "sections", max_columns: 2, sections: secties };
  }

  /** Vangnet: alle entiteiten van de integratie onder elkaar. */
  static waardenView(hass) {
    const alle = Object.keys(hass.states)
      .filter((id) => /^(sensor|binary_sensor|switch|weather|image)\./.test(id) && id.includes("stormchase"))
      .sort();
    if (!alle.length) return null;
    return {
      type: "sections",
      max_columns: 2,
      sections: [
        {
          type: "grid",
          column_span: 2,
          cards: [{ type: "entities", title: "Alle waarden", entities: alle }],
        },
      ],
    };
  }

  static async bouwView(config) {
    return this.hoofdView(config);
  }
}

/** Strategie voor een losse view binnen een bestaand dashboard. */
class StormchaseViewStrategy extends HTMLTemplateElement {
  static async generate(config, hass) {
    return StormchaseStrategy.bouwView(config, hass);
  }
}

/** Strategie voor een compleet dashboard. */
class StormchaseDashboardStrategy extends HTMLTemplateElement {
  static async generate(config, hass) {
    const views = [
      {
        title: config.title || "Stormchase",
        path: "stormchase",
        icon: "mdi:flash",
        ...StormchaseStrategy.hoofdView(config),
      },
    ];
    const kaarten = config.maps === false ? null : StormchaseStrategy.kaartenView(config, hass);
    if (kaarten) views.push({ title: "Kaarten", path: "kaarten", icon: "mdi:map", ...kaarten });
    const waarden = config.alle_waarden === false ? null : StormchaseStrategy.waardenView(hass);
    if (waarden) views.push({ title: "Alle waarden", path: "waarden", icon: "mdi:format-list-bulleted", ...waarden });
    return { views };
  }
}

/**
 * Registreer alleen als het nog niet gebeurd is. Het script kan via twee
 * wegen binnenkomen (Lovelace-bron en add_extra_js_url); een tweede define
 * zou anders een fout gooien.
 */
const registreer = (naam, klasse) => {
  if (!customElements.get(naam)) {
    customElements.define(naam, klasse);
  }
};

registreer(KAART, StormchaseHudCard);
registreer("ll-strategy-view-stormchase", StormchaseViewStrategy);
registreer("ll-strategy-dashboard-stormchase", StormchaseDashboardStrategy);

/* In de kaartkiezer van Home Assistant zichtbaar maken */
window.customCards = window.customCards || [];
if (!window.customCards.some((k) => k.type === KAART)) {
  window.customCards.push({
    type: KAART,
    name: "Stormchase commandocentrum",
    description: "Alles voor een onweersjacht in een overzicht: radar, bliksem, convectie, waarschuwingen en waarnemingen.",
    preview: false,
  });
}

console.info(
  `%c STORMCHASE %c commandocentrum geladen \u00b7 v${VERSIE} `,
  "background:#3a2a5e;color:#f5b731;font-weight:700",
  ""
);
