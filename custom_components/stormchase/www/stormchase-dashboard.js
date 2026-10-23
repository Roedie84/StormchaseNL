/**
 * Stormchase dashboardstrategie (custom:stormchase).
 *
 * Dit kleine bestand bevat alleen de strategieklassen. De kaarten zelf
 * (<stormchase-hud-card>) staan in stormchase-strategy.js. De frontend van
 * Home Assistant wacht maar een paar seconden tot
 * ll-strategy-dashboard-stormchase geregistreerd is; bij een trage
 * verbinding (Nabu Casa, mobiel) of vlak na een herstart haalde het grote
 * bestand (~110 KB) dat niet altijd. Dit bestand is klein en registreert de
 * strategie direct.
 *
 * De strategie hangt niet af van de kaartklassen: hij geeft alleen
 * config-objecten terug met het kaarttype als tekst. De kaart wordt
 * getekend zodra het grote bestand geladen is.
 *
 * Het blok hieronder is identiek aan het strategieblok in
 * stormchase-strategy.js (dat blijft als terugval voor wie alleen dat
 * bestand als bron heeft). Een test bewaakt dat beide gelijk blijven.
 *
 * Let op: alleen ASCII, zie stormchase-strategy.js.
 */

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

/* Registreer alleen als het nog niet gebeurd is (ook niet door het grote
   bestand of een tweede laadroute). */
const registreer = (naam, klasse) => {
  if (!customElements.get(naam)) {
    customElements.define(naam, klasse);
  }
};

registreer("ll-strategy-view-stormchase", StormchaseViewStrategy);
registreer("ll-strategy-dashboard-stormchase", StormchaseDashboardStrategy);
