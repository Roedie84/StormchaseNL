/**
 * Stormchase dashboardstrategie.
 *
 * Bouwt de view bij elke paginalading opnieuw op uit de entiteiten die op dat
 * moment bestaan. Komt er bij een update een sensor bij, dan verschijnt de
 * tegel vanzelf. Verdwijnt er een, dan blijft er geen dode kaart achter.
 *
 * Gebruik in de onbewerkte configuratie van een dashboard:
 *
 *   strategy:
 *     type: custom:stormchase
 *
 * Alle opties zijn optioneel; zonder opties wordt alles automatisch bepaald.
 */

const TILE_STYLE = `
  ha-card {
    background: rgba(41,30,74,.55);
    border: 1px solid rgba(255,255,255,.06);
    border-radius: 16px;
  }
  ha-card .primary { font-size: 22px; font-weight: 700; }
  ha-card .secondary { font-size: 11px; letter-spacing: .5px; text-transform: uppercase; }
`;

const PANEL_STYLE = `
  ha-card {
    background: rgba(41,30,74,.55);
    border: 1px solid rgba(255,255,255,.06);
    border-radius: 18px;
  }
`;

const FRAME_STYLE = `
  ha-card {
    border: 1px solid rgba(255,255,255,.06);
    border-radius: 18px;
    overflow: hidden;
  }
`;

const KOMPASROOS = [
  "N", "NNO", "NO", "ONO", "O", "OZO", "ZO", "ZZO",
  "Z", "ZZW", "ZW", "WZW", "W", "WNW", "NW", "NNW",
];

/** Bestaat de entiteit en heeft hij een bruikbare waarde? */
const bruikbaar = (hass, entityId) => {
  if (!entityId) return false;
  const state = hass.states[entityId];
  return !!state && !["unknown", "unavailable"].includes(state.state);
};

/** Zoek een entiteit op achtervoegsel, zoals de config flow dat ook doet. */
const raad = (hass, domein, achtervoegsel) =>
  Object.keys(hass.states).find(
    (id) => id.startsWith(`${domein}.`) && id.endsWith(achtervoegsel)
  );

/** Mushroom-tegel met de standaard opmaak. */
const tegel = (opties) => ({
  type: "custom:mushroom-template-card",
  card_mod: { style: TILE_STYLE },
  ...opties,
});

const kop = (heading, icon, style = "subtitle") => ({
  type: "heading",
  heading,
  heading_style: style,
  icon,
});

class StormchaseStrategy {
  /** Verzamel alles wat de strategie nodig heeft. */
  static verzamel(config, hass) {
    const bron = {
      afstand:
        config.distance_entity || raad(hass, "sensor", "_lightning_distance"),
      azimut:
        config.azimuth_entity || raad(hass, "sensor", "_lightning_azimuth"),
      teller:
        config.counter_entity || raad(hass, "sensor", "_lightning_counter"),
    };

    // Alle ringsensoren, gesorteerd op afstand. Voeg ik er later een toe,
    // dan komt die er hier vanzelf bij.
    const ringen = Object.keys(hass.states)
      .filter((id) => id.startsWith("sensor.stormchase_inslagen_binnen_"))
      .map((id) => ({
        id,
        km: parseInt(id.replace(/\D+/g, ""), 10) || 0,
      }))
      .sort((a, b) => a.km - b.km);

    return { bron, ringen };
  }

  /** De linkerkolom: status, sensoren en parameters. */
  static statusSectie(config, hass) {
    const { bron, ringen } = this.verzamel(config, hass);
    const cards = [];

    cards.push(kop(config.title || "Stormchase", "mdi:flash", "title"));

    // Waarschuwingsbanner
    if (bruikbaar(hass, "binary_sensor.stormchase_onweer_nabij")) {
      cards.push({
        type: "conditional",
        conditions: [
          {
            condition: "state",
            entity: "binary_sensor.stormchase_onweer_nabij",
            state: "on",
          },
        ],
        card: {
          type: "custom:mushroom-template-card",
          icon: "mdi:flash-alert",
          icon_color: "red",
          primary: bron.afstand
            ? `Onweer op {{ states('${bron.afstand}') }} km — voorzichtig!`
            : "Onweer in de buurt — voorzichtig!",
          secondary:
            "{{ states('sensor.stormchase_trend') }}" +
            "{% if has_value('sensor.stormchase_aankomst') %}" +
            " · hier over ongeveer {{ states('sensor.stormchase_aankomst') }} min" +
            "{% endif %}",
          multiline_secondary: true,
          card_mod: {
            style: `
              ha-card {
                background: rgba(255, 60, 90, .10);
                border: 1px solid rgba(255, 92, 108, .55);
                border-radius: 16px;
              }
              ha-card .primary { color: #ff5c6c !important; font-weight: 600; }
            `,
          },
        },
      });
    }

    // Basistegels, alleen wat daadwerkelijk bestaat
    const basis = [];
    if (bron.afstand) {
      basis.push(
        tegel({
          icon: "mdi:flash",
          icon_color: "red",
          primary: `{{ states('${bron.afstand}') }} km`,
          secondary: "AFSTAND · laatste inslag",
        })
      );
    }
    if (bron.azimut) {
      basis.push(
        tegel({
          icon: "mdi:compass-outline",
          icon_color: "blue",
          primary: `{{ states('${bron.azimut}') }}°`,
          secondary:
            `AZIMUT · {% set a = states('${bron.azimut}') | float(0) %}` +
            `{{ ${JSON.stringify(KOMPASROOS)}[((a / 22.5) | round(0) | int) % 16] }}`,
        })
      );
    }
    if (bron.teller) {
      basis.push(
        tegel({
          icon: "mdi:counter",
          icon_color: "amber",
          primary: `{{ states('${bron.teller}') }}`,
          secondary: "AANTAL · tijdvenster",
        })
      );
    }
    if (bruikbaar(hass, "sensor.stormchase_actieve_markers")) {
      basis.push(
        tegel({
          icon: "mdi:map-marker-multiple",
          icon_color: "purple",
          primary: "{{ states('sensor.stormchase_actieve_markers') }}",
          secondary: "ACTIEVE MARKERS",
        })
      );
    }
    if (basis.length) {
      cards.push({ type: "grid", columns: 2, square: false, cards: basis });
    }

    // Locatie alleen tonen als je niet thuis zit; anders is het ruis
    const locatie = hass.states["sensor.stormchase_actieve_locatie"];
    if (locatie && locatie.state !== "thuis") {
      cards.push(
        tegel({
          icon: "mdi:crosshairs-gps",
          icon_color: "orange",
          primary: "Locatie: {{ states('sensor.stormchase_actieve_locatie') }}",
          secondary:
            "{{ state_attr('sensor.stormchase_actieve_locatie','latitude') | round(3) }}, " +
            "{{ state_attr('sensor.stormchase_actieve_locatie','longitude') | round(3) }}",
        })
      );
    }

    // Nadering en aankomst
    if (bruikbaar(hass, "sensor.stormchase_naderingssnelheid")) {
      cards.push({
        type: "grid",
        columns: 2,
        square: false,
        cards: [
          tegel({
            icon:
              "{% set v = states('sensor.stormchase_naderingssnelheid') | float(0) %}" +
              "{{ 'mdi:arrow-down-bold' if v > 1 else 'mdi:arrow-up-bold' if v < -1 else 'mdi:minus' }}",
            icon_color:
              "{% set v = states('sensor.stormchase_naderingssnelheid') | float(0) %}" +
              "{{ 'red' if v > 3 else 'orange' if v > 1 else 'green' if v < -1 else 'grey' }}",
            primary:
              "{{ states('sensor.stormchase_naderingssnelheid') | float(0) | abs | round(0) }} km/u",
            secondary: "NADERING · {{ states('sensor.stormchase_trend') }}",
          }),
          tegel({
            icon: "mdi:timer-sand",
            icon_color: "red",
            primary:
              "{% if has_value('sensor.stormchase_aankomst') %}" +
              "{{ states('sensor.stormchase_aankomst') }} min{% else %}—{% endif %}",
            secondary: "AANKOMST · geschat",
          }),
        ],
      });
    }

    // Afstandsringen, hoeveel het er ook zijn
    if (ringen.length) {
      const kleuren = ["red", "orange", "amber", "yellow", "grey"];
      cards.push(kop("Inslagen per ring", "mdi:target"));
      cards.push({
        type: "grid",
        columns: Math.min(ringen.length, 3),
        square: false,
        cards: ringen.map((ring, i) =>
          tegel({
            icon: i === 0 ? "mdi:flash-alert" : "mdi:flash-outline",
            icon_color: kleuren[Math.min(i, kleuren.length - 1)],
            primary: `{{ states('${ring.id}') }}`,
            secondary: `< ${ring.km} KM`,
          })
        ),
      });
    }

    // Onweersparameters
    const parameters = [
      {
        id: "sensor.stormchase_cape",
        icon: "mdi:arrow-up-bold-box",
        label: "CAPE · J/KG",
        kleur:
          "{% set c = states('sensor.stormchase_cape') | float(0) %}" +
          "{{ 'red' if c > 2500 else 'orange' if c > 1000 else 'amber' if c > 300 else 'grey' }}",
      },
      {
        id: "sensor.stormchase_cape_piek_12_uur",
        icon: "mdi:chart-bell-curve",
        label: "PIEK · 12U",
        kleur: "purple",
      },
      {
        id: "sensor.stormchase_lifted_index",
        icon: "mdi:thermometer-chevron-down",
        label: "LIFTED INDEX",
        kleur:
          "{% set li = states('sensor.stormchase_lifted_index') | float(0) %}" +
          "{{ 'red' if li < -6 else 'orange' if li < -3 else 'amber' if li < 0 else 'grey' }}",
      },
      {
        id: "sensor.stormchase_convectieve_remming",
        icon: "mdi:lock-outline",
        label: "REMMING · J/KG",
        kleur: "blue",
      },
    ].filter((p) => bruikbaar(hass, p.id));

    if (parameters.length || bruikbaar(hass, "sensor.stormchase_chase_potentie")) {
      cards.push(kop("Onweersparameters", "mdi:weather-lightning"));
    }

    if (bruikbaar(hass, "sensor.stormchase_chase_potentie")) {
      cards.push(
        tegel({
          icon: "mdi:radar",
          icon_color:
            "{% set p = states('sensor.stormchase_chase_potentie') | float(0) %}" +
            "{{ 'red' if p > 70 else 'orange' if p > 40 else 'amber' if p > 20 else 'grey' }}",
          primary:
            "Chase potentie: {{ states('sensor.stormchase_chase_potentie') }}%",
          secondary:
            "CAPE {{ state_attr('sensor.stormchase_chase_potentie','cape_bijdrage') }} · " +
            "LI {{ state_attr('sensor.stormchase_chase_potentie','lifted_index_bijdrage') }} · " +
            "inslagen {{ state_attr('sensor.stormchase_chase_potentie','inslagen_bijdrage') }}",
          multiline_secondary: true,
        })
      );
    }

    if (parameters.length) {
      cards.push({
        type: "grid",
        columns: Math.min(parameters.length, 3),
        square: false,
        cards: parameters.map((p) =>
          tegel({
            icon: p.icon,
            icon_color: p.kleur,
            primary: `{{ states('${p.id}') }}`,
            secondary: p.label,
          })
        ),
      });
    }

    // Grote afstandkaart
    if (bron.afstand) {
      cards.push({
        type: "custom:mushroom-template-card",
        icon: "mdi:map-marker-distance",
        icon_color: "red",
        primary: `{{ states('${bron.afstand}') }} km`,
        secondary:
          (bron.azimut ? `Richting {{ states('${bron.azimut}') }}° · ` : "") +
          "{{ states('sensor.stormchase_trend') }} · " +
          "{{ states('sensor.stormchase_actieve_markers') }} actieve markers",
        multiline_secondary: true,
        card_mod: {
          style: `
            ha-card {
              background: rgba(41,30,74,.55);
              border: 1px solid rgba(255,92,108,.35);
              border-radius: 18px;
            }
            ha-card .primary { font-size: 46px; font-weight: 800; color: #ff5c6c !important; }
          `,
        },
      });
    }

    // Kompas
    if (bron.azimut) {
      cards.push({
        type: "custom:compass-card",
        name: "RICHTING",
        indicator_sensors: [
          {
            sensor: bron.azimut,
            indicator: { image: "arrow_outward", color: "#ff5c6c" },
          },
        ],
        value_sensors: [{ sensor: bron.azimut }],
        card_mod: { style: PANEL_STYLE },
      });
    }

    // Verloopgrafiek met de ringen als referentielijnen
    if (bron.afstand) {
      const grenzen = ringen.length
        ? [ringen[0].km, ringen[ringen.length - 1].km]
        : [15, 50];
      cards.push({
        type: "custom:apexcharts-card",
        graph_span: "2h",
        header: { show: true, title: "AFSTAND · LAATSTE 2 UUR", show_states: false },
        series: [
          {
            entity: bron.afstand,
            name: "Afstand (km)",
            color: "#f5b731",
            type: "line",
            curve: "stepline",
            stroke_width: 2,
            group_by: { func: "min", duration: "1min" },
          },
        ],
        apex_config: {
          chart: { height: 240, background: "transparent" },
          grid: { borderColor: "rgba(255,255,255,.06)" },
          yaxis: { min: 0 },
          annotations: {
            yaxis: [
              {
                y: grenzen[0],
                borderColor: "#ff5c6c",
                strokeDashArray: 6,
                label: {
                  text: `${grenzen[0]} km`,
                  style: { background: "#ff5c6c", color: "#fff" },
                },
              },
              {
                y: grenzen[1],
                borderColor: "#8a7fd0",
                strokeDashArray: 4,
                label: {
                  text: `${grenzen[1]} km`,
                  style: { background: "#8a7fd0", color: "#fff" },
                },
              },
            ],
          },
        },
        card_mod: { style: PANEL_STYLE },
      });
    }

    // CAPE-verloop, eventueel met de potentie op een tweede as
    if (bruikbaar(hass, "sensor.stormchase_cape")) {
      const tweeAssen = bruikbaar(hass, "sensor.stormchase_chase_potentie");

      const capeSerie = {
        entity: "sensor.stormchase_cape",
        name: "CAPE (J/kg)",
        color: "#a78bfa",
        type: "area",
        opacity: 0.25,
        stroke_width: 2,
      };

      // Apexcharts-card eist dat elke serie een as heeft zodra er meer dan
      // een as gedefinieerd is. Bij een enkele serie laten we yaxis weg.
      if (tweeAssen) capeSerie.yaxis_id = "cape";

      const grafiek = {
        type: "custom:apexcharts-card",
        graph_span: "24h",
        header: { show: true, title: "CAPE \u00b7 24 UUR", show_states: false },
        series: [capeSerie],
        apex_config: {
          chart: { height: 220, background: "transparent" },
          grid: { borderColor: "rgba(255,255,255,.06)" },
        },
        card_mod: { style: PANEL_STYLE },
      };

      if (tweeAssen) {
        grafiek.series.push({
          entity: "sensor.stormchase_chase_potentie",
          name: "Potentie (%)",
          color: "#f5b731",
          type: "line",
          stroke_width: 2,
          yaxis_id: "pct",
        });
        grafiek.yaxis = [
          { id: "cape", min: 0 },
          { id: "pct", opposite: true, min: 0, max: 100 },
        ];
      } else {
        grafiek.apex_config.yaxis = { min: 0 };
      }

      cards.push(grafiek);
    }

    return { type: "grid", column_span: 1, cards };
  }

  /** De rechterkolom: de kaarten. */
  static kaartenSectie(config, hass) {
    const kaarten = config.maps || {};

    // Volg de actieve locatie van de integratie, zodat de kaarten op
    // vakantie meeverhuizen in plaats van thuis te blijven hangen.
    const actief = hass.states["sensor.stormchase_actieve_locatie"];
    const lat = (
      config.latitude ??
      actief?.attributes?.latitude ??
      hass.config.latitude
    ).toFixed(2);
    const lon = (
      config.longitude ??
      actief?.attributes?.longitude ??
      hass.config.longitude
    ).toFixed(2);
    const cards = [kop("Kaarten", "mdi:map-marker-radius", "title")];

    if (kaarten.iradar !== false) {
      cards.push(kop("iRadar · radar & celdetectie", "mdi:radar"));
      cards.push({
        type: "iframe",
        url: config.iradar_url || "https://iradar.app/",
        aspect_ratio: "56%",
        card_mod: { style: FRAME_STYLE },
      });
    }

    if (kaarten.blitzortung !== false) {
      cards.push(kop("Blitzortung · live inslagen", "mdi:flash-outline"));
      cards.push({
        type: "iframe",
        url:
          "https://map.blitzortung.org/index.php?interactive=1&NavigationControl=1" +
          "&FullScreenControl=0&Cookies=0&InfoDiv=0&MenuButtonDiv=0&ScaleControl=1" +
          `&Advertisment=0&MapStyle=1&MapStyleRangeValue=3#8/${lat}/${lon}`,
        aspect_ratio: "75%",
        card_mod: { style: FRAME_STYLE },
      });
    }

    if (kaarten.buienradar !== false) {
      cards.push(kop("Buienradar · neerslag 2 uur", "mdi:weather-pouring"));
      cards.push({
        type: "iframe",
        url:
          "https://gadgets.buienradar.nl/gadget/zoommap/" +
          `?lat=${lat}&lng=${lon}&overname=2&zoom=10&size=3&voor=1`,
        aspect_ratio: "100%",
        card_mod: { style: FRAME_STYLE },
      });
    }

    if (kaarten.windy !== false) {
      cards.push(kop("Windy · CAPE", "mdi:weather-lightning-rainy"));
      cards.push({
        type: "iframe",
        url:
          `https://embed.windy.com/embed2.html?lat=${lat}&lon=${lon}&zoom=9` +
          "&overlay=cape&type=map&metricWind=km%2Fh&metricTemp=%C2%B0C" +
          "&menu=&message=&marker=&calendar=&pressure=&location=coordinates" +
          "&detail=&radarRange=-1",
        aspect_ratio: "75%",
        card_mod: { style: FRAME_STYLE },
      });
    }

    return { type: "grid", column_span: 1, cards };
  }

  static async bouwView(config, hass) {
    return {
      type: "sections",
      max_columns: 2,
      sections: [
        this.statusSectie(config, hass),
        this.kaartenSectie(config, hass),
      ],
    };
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
    const view = await StormchaseStrategy.bouwView(config, hass);
    return {
      views: [
        {
          title: config.title || "Stormchase",
          path: "stormchase",
          icon: "mdi:flash",
          ...view,
        },
      ],
    };
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

registreer("ll-strategy-view-stormchase", StormchaseViewStrategy);
registreer("ll-strategy-dashboard-stormchase", StormchaseDashboardStrategy);

console.info(
  "%c STORMCHASE %c strategie geladen ",
  "background:#3a2a5e;color:#f5b731;font-weight:700",
  ""
);
