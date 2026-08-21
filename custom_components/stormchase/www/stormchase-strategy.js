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

/* Kleuren, op een plek zodat het geheel samenhangt. */
const KLEUR = {
  paneel: "rgba(30, 22, 52, .62)",
  rand: "rgba(255, 255, 255, .07)",
  gevaar: "#ff5c6c",
  alert: "#f5b731",
  rustig: "#4ade80",
  gedempt: "#8a7fd0",
};

/* Cijfers met vaste breedte, anders springt de layout bij elke update. */
const CIJFERS = 'font-variant-numeric: tabular-nums; font-feature-settings: "tnum";';

const TILE_STYLE = `
  ha-card {
    background: ${KLEUR.paneel};
    border: 1px solid ${KLEUR.rand};
    border-radius: 14px;
  }
  ha-card .primary {
    font-size: 21px;
    font-weight: 700;
    ${CIJFERS}
  }
  ha-card .secondary {
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 1.1px;
    text-transform: uppercase;
    opacity: .55;
  }
`;

const PANEL_STYLE = `
  ha-card {
    background: ${KLEUR.paneel};
    border: 1px solid ${KLEUR.rand};
    border-radius: 18px;
  }
`;

const FRAME_STYLE = `
  ha-card {
    border: 1px solid ${KLEUR.rand};
    border-radius: 18px;
    overflow: hidden;
  }
`;

/* De statusregel bovenaan: kleur volgt de ernst van de situatie. */
const heroStyle = (accent) => `
  ha-card {
    background: linear-gradient(135deg, rgba(30,22,52,.9), rgba(18,13,34,.9));
    border: 1px solid ${accent}55;
    border-left: 3px solid ${accent};
    border-radius: 18px;
  }
  ha-card .primary {
    font-size: 25px;
    font-weight: 800;
    letter-spacing: -.3px;
    color: ${accent} !important;
    ${CIJFERS}
  }
  ha-card .secondary {
    font-size: 12px;
    opacity: .7;
    ${CIJFERS}
  }
`;

const KOMPASROOS = [
  "N", "NNO", "NO", "ONO", "O", "OZO", "ZO", "ZZO",
  "Z", "ZZW", "ZW", "WZW", "W", "WNW", "NW", "NNW",
];

/**
 * Draait dit op een smal scherm?
 *
 * De strategie wordt in de browser uitgevoerd, dus de schermbreedte is
 * gewoon beschikbaar. Op een telefoon vallen de secties onder elkaar en is
 * een kaart met een brede verhouding onbruikbaar klein.
 */
const isSmal = () =>
  typeof window !== "undefined" && window.innerWidth > 0 && window.innerWidth < 700;

/** Bestaat de entiteit en heeft hij een bruikbare waarde? */
const bruikbaar = (hass, entityId) => {
  if (!entityId) return false;
  const state = hass.states[entityId];
  return !!state && !["unknown", "unavailable"].includes(state.state);
};

/**
 * Bouw een vertaaltabel van "nette" naar echte entity-id's.
 *
 * Home Assistant zet de ruimtenaam voor de entity-id als het apparaat aan een
 * ruimte is toegewezen: sensor.woonkamer_stormchase_cape in plaats van
 * sensor.stormchase_cape. De kaarten hieronder gebruiken de nette vorm; deze
 * tabel zet ze om naar wat er daadwerkelijk bestaat.
 */
const bouwVertaaltabel = (hass) => {
  const tabel = {};
  let voorvoegsel = "";

  for (const id of Object.keys(hass.states)) {
    const punt = id.indexOf(".");
    const domein = id.slice(0, punt);
    const naam = id.slice(punt + 1);

    const positie = naam.indexOf("stormchase");
    if (positie === -1) continue;

    // Het voorvoegsel is voor alle entiteiten van de integratie gelijk;
    // eenmaal gevonden geldt het ook voor entiteiten die nu niet bestaan.
    if (positie > 0) voorvoegsel = naam.slice(0, positie);

    const net = `${domein}.${naam.slice(positie)}`;
    if (net !== id) tabel[net] = id;
  }

  return { tabel, voorvoegsel };
};

/**
 * Vervang de nette id's door de echte, overal in de opgebouwde kaarten.
 * Werkt met het gevonden voorvoegsel, zodat ook verwijzingen naar entiteiten
 * die op dit moment geen waarde hebben goed terechtkomen.
 */
const pasVertaaltabelToe = (waarde, voorvoegsel) => {
  if (!voorvoegsel) return waarde;

  if (typeof waarde === "string") {
    return waarde.replace(
      /\b(sensor|binary_sensor|switch|weather)\.stormchase/g,
      `$1.${voorvoegsel}stormchase`
    );
  }
  if (Array.isArray(waarde)) {
    return waarde.map((item) => pasVertaaltabelToe(item, voorvoegsel));
  }
  if (waarde && typeof waarde === "object") {
    const uit = {};
    for (const [sleutel, inhoud] of Object.entries(waarde)) {
      uit[sleutel] = pasVertaaltabelToe(inhoud, voorvoegsel);
    }
    return uit;
  }
  return waarde;
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

/**
 * Toon een waarde, of een streepje als de sensor niets weet.
 * Zonder dit staat er letterlijk "unknown km" op het dashboard zodra het
 * een tijdje rustig is geweest.
 */
const waarde = (entityId, suffix = "") =>
  `{% if has_value('${entityId}') %}{{ states('${entityId}') }}${suffix}` +
  `{% else %}\u2014{% endif %}`;

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
    const heeftAfstand = bruikbaar(hass, bron.afstand);

    cards.push(kop(config.title || "Stormchase", "mdi:flash", "title"));

    // ---- Officiele weerwaarschuwing, alleen als er een geldt ----
    if (hass.states["binary_sensor.stormchase_weerwaarschuwing"]) {
      cards.push({
        type: "conditional",
        conditions: [
          {
            condition: "state",
            entity: "binary_sensor.stormchase_weerwaarschuwing",
            state: "on",
          },
        ],
        card: {
          type: "custom:mushroom-template-card",
          icon: "mdi:alert-decagram",
          icon_color:
            "{% set n = states('sensor.stormchase_waarschuwingsniveau') %}" +
            "{{ 'red' if n == 'rood' else 'orange' if n == 'oranje' else 'yellow' }}",
          primary:
            "Code {{ states('sensor.stormchase_waarschuwingsniveau') }}" +
            "{% set s = state_attr('sensor.stormchase_waarschuwingsniveau','soort') %}" +
            "{% if s %} \u00b7 {{ s }}{% endif %}",
          secondary:
            "{% set g = state_attr('sensor.stormchase_waarschuwingsniveau','gebied') %}" +
            "{% set n = state_attr('sensor.stormchase_waarschuwingsniveau','aantal') | int(0) %}" +
            "{% if g %}{{ g }}{% endif %}" +
            "{% if n > 1 %} \u00b7 {{ n }} waarschuwingen actief{% endif %}",
          multiline_secondary: true,
          card_mod: {
            style:
              "{% set n = states('sensor.stormchase_waarschuwingsniveau') %}" +
              "{% set c = '#ff5c6c' if n == 'rood' else '#ff9f43' if n == 'oranje' else '#f5d431' %}" +
              `
              ha-card {
                background: rgba(255, 180, 40, .10);
                border: 1px solid {{ c }};
                border-left: 3px solid {{ c }};
                border-radius: 16px;
              }
              ha-card .primary { color: {{ c }} !important; font-weight: 700; }
            `,
          },
        },
      });
    }

    // ---- Statusregel: vat in een oogopslag samen wat er speelt ----
    // De kleur en tekst volgen de ernst, zodat je bij rustig weer niet
    // hetzelfde beeld krijgt als wanneer er iets aankomt.
    const nabij = "binary_sensor.stormchase_onweer_nabij";
    const nadert = "binary_sensor.stormchase_onweer_nadert";

    const status = [
      `{% set d = states('${bron.afstand || "sensor.none"}') %}`,
      `{% set nabij = is_state('${nabij}','on') %}`,
      `{% set nadert = is_state('${nadert}','on') %}`,
      "{% set actief = d not in ['unknown','unavailable','none'] %}",
    ].join("");

    cards.push({
      type: "custom:mushroom-template-card",
      icon: `${status}{% if nabij %}mdi:flash-alert{% elif nadert %}mdi:radar` +
        "{% elif actief %}mdi:weather-lightning{% else %}mdi:weather-night{% endif %}",
      icon_color:
        `${status}{% if nabij %}red{% elif nadert %}orange` +
        "{% elif actief %}amber{% else %}green{% endif %}",
      primary:
        `${status}{% if nabij %}ONWEER NABIJ` +
        "{% elif nadert %}NADERT{% elif actief %}ACTIEF{% else %}RUSTIG{% endif %}",
      secondary:
        status +
        "{% if actief %}" +
        "Laatste inslag {{ d }} km" +
        `{% if has_value('${bron.azimut || "sensor.none"}') %}` +
        ` in het {% set a = states('${bron.azimut}') | float(0) %}` +
        `{{ ${JSON.stringify(KOMPASROOS)}[((a / 22.5) | round(0) | int) % 16] }}` +
        "{% endif %}" +
        "{% if has_value('sensor.stormchase_aankomst') %}" +
        " \u00b7 hier over {{ states('sensor.stormchase_aankomst') }} min" +
        "{% elif has_value('sensor.stormchase_trend') %}" +
        " \u00b7 {{ states('sensor.stormchase_trend') }}" +
        "{% endif %}" +
        "{% else %}Geen blikseminslagen binnen bereik{% endif %}",
      multiline_secondary: true,
      card_mod: {
        style:
          `{% set nabij = is_state('${nabij}','on') %}` +
          `{% set nadert = is_state('${nadert}','on') %}` +
          `{% set d = states('${bron.afstand || "sensor.none"}') %}` +
          "{% set actief = d not in ['unknown','unavailable','none'] %}" +
          "{% if nabij %}" + heroStyle(KLEUR.gevaar) +
          "{% elif nadert or actief %}" + heroStyle(KLEUR.alert) +
          "{% else %}" + heroStyle(KLEUR.rustig) + "{% endif %}",
      },
    });

    // ---- Kerncijfers ----
    const basis = [];
    if (bron.afstand) {
      basis.push(
        tegel({
          icon: "mdi:flash",
          icon_color: heeftAfstand ? "red" : "disabled",
          primary: waarde(bron.afstand, " km"),
          secondary: "Afstand",
        })
      );
    }
    if (bron.azimut) {
      basis.push(
        tegel({
          icon: "mdi:compass-outline",
          icon_color: bruikbaar(hass, bron.azimut) ? "blue" : "disabled",
          primary:
            `{% if has_value('${bron.azimut}') %}` +
            `{% set a = states('${bron.azimut}') | float(0) %}` +
            `{{ ${JSON.stringify(KOMPASROOS)}[((a / 22.5) | round(0) | int) % 16] }}` +
            "{% else %}\u2014{% endif %}",
          secondary:
            `{% if has_value('${bron.azimut}') %}` +
            `{{ states('${bron.azimut}') | round(0) }}\u00b0 richting` +
            "{% else %}Richting{% endif %}",
        })
      );
    }
    if (bruikbaar(hass, "sensor.stormchase_naderingssnelheid")) {
      basis.push(
        tegel({
          icon:
            "{% set v = states('sensor.stormchase_naderingssnelheid') | float(0) %}" +
            "{{ 'mdi:arrow-down-bold' if v > 1 else 'mdi:arrow-up-bold' if v < -1 else 'mdi:minus' }}",
          icon_color:
            "{% set v = states('sensor.stormchase_naderingssnelheid') | float(0) %}" +
            "{{ 'red' if v > 3 else 'orange' if v > 1 else 'green' if v < -1 else 'disabled' }}",
          primary:
            "{% if has_value('sensor.stormchase_naderingssnelheid') %}" +
            "{{ states('sensor.stormchase_naderingssnelheid') | float(0) | abs | round(0) }} km/u" +
            "{% else %}\u2014{% endif %}",
          secondary: "{{ states('sensor.stormchase_trend') }}",
        })
      );
    }
    if (bron.teller) {
      basis.push(
        tegel({
          icon: "mdi:counter",
          icon_color: bruikbaar(hass, bron.teller) ? "amber" : "disabled",
          primary: waarde(bron.teller),
          secondary: "Inslagen totaal",
        })
      );
    }
    if (basis.length) {
      cards.push({ type: "grid", columns: 2, square: false, cards: basis });
    }

    // ---- Locatie, alleen als je niet thuis bent ----
    const locatie = hass.states["sensor.stormchase_actieve_locatie"];
    if (locatie && locatie.state !== "thuis") {
      cards.push(
        tegel({
          icon: "mdi:crosshairs-gps",
          icon_color: "orange",
          primary: "{{ states('sensor.stormchase_actieve_locatie') }}",
          secondary:
            "Meetpunt \u00b7 " +
            "{{ state_attr('sensor.stormchase_actieve_locatie','latitude') | round(3) }}, " +
            "{{ state_attr('sensor.stormchase_actieve_locatie','longitude') | round(3) }}",
        })
      );
    }

    // ---- Neerslag ----
    if (bruikbaar(hass, "sensor.stormchase_neerslagintensiteit")) {
      cards.push(kop("Neerslag", "mdi:weather-pouring"));

      cards.push({
        type: "custom:mushroom-template-card",
        icon:
          "{% if is_state('binary_sensor.stormchase_regen_verwacht','on') %}" +
          "mdi:weather-pouring{% else %}mdi:weather-partly-cloudy{% endif %}",
        icon_color:
          "{% if is_state('binary_sensor.stormchase_regen_verwacht','on') %}" +
          "blue{% else %}disabled{% endif %}",
        primary:
          "{% set r = state_attr('sensor.stormchase_regen_begint_over','regent') %}" +
          "{% set start = states('sensor.stormchase_regen_begint_over') %}" +
          "{% if r %}Het regent" +
          "{% elif start not in ['unknown','unavailable','none'] %}" +
          "Regen over {{ start }} min" +
          "{% else %}Droog{% endif %}",
        secondary:
          "{% set r = state_attr('sensor.stormchase_regen_begint_over','regent') %}" +
          "{% set stop = state_attr('sensor.stormchase_regen_begint_over','stopt_over') %}" +
          "{% set piek = states('sensor.stormchase_neerslagpiek_2_uur') | float(0) %}" +
          "{% if r and stop %}Nog ongeveer {{ stop }} min \u00b7 " +
          "{{ states('sensor.stormchase_neerslagintensiteit') }} mm/u" +
          "{% elif r %}{{ states('sensor.stormchase_neerslagintensiteit') }} mm/u" +
          "{% elif piek > 0 %}Piek {{ piek }} mm/u komende 2 uur" +
          "{% else %}Niets verwacht de komende 2 uur{% endif %}",
        multiline_secondary: true,
        card_mod: { style: TILE_STYLE },
      });

      // Verwachting per 5 minuten, uit de attributen van de startsensor
      cards.push({
        type: "custom:apexcharts-card",
        header: {
          show: true,
          title: "Neerslag \u00b7 komende 2 uur",
          show_states: false,
        },
        series: [
          {
            entity: "sensor.stormchase_regen_begint_over",
            name: "mm/u",
            color: "#5eb3f5",
            type: "area",
            opacity: 0.3,
            stroke_width: 2,
            curve: "smooth",
            data_generator: `
              const nu = Date.now();
              const reeks = entity.attributes.verwachting || [];
              return reeks.map((p) => [nu + p.minuten * 60000, p.mm_per_uur]);
            `,
          },
        ],
        apex_config: {
          chart: { height: 180, background: "transparent" },
          grid: { borderColor: "rgba(255,255,255,.06)" },
          yaxis: { min: 0, forceNiceScale: true },
          xaxis: { type: "datetime" },
        },
        card_mod: { style: PANEL_STYLE },
      });
    }

    // ---- Weer op de actieve locatie ----
    if (hass.states["weather.stormchase"]) {
      cards.push(kop("Weer op locatie", "mdi:weather-partly-cloudy"));
      cards.push({
        type: "weather-forecast",
        entity: "weather.stormchase",
        forecast_type: "hourly",
        show_current: true,
        show_forecast: true,
        card_mod: { style: PANEL_STYLE },
      });
    }

    // ---- Afstandsringen ----
    if (ringen.length) {
      cards.push(kop("Inslagen per ring", "mdi:target"));
      cards.push({
        type: "grid",
        columns: Math.min(ringen.length, 3),
        square: false,
        cards: ringen.map((ring, i) =>
          tegel({
            icon: i === 0 ? "mdi:flash-alert" : "mdi:flash-outline",
            // Grijs zolang er niets is; kleur pas als het telt.
            icon_color:
              `{{ '${["red", "orange", "amber"][Math.min(i, 2)]}'` +
              ` if states('${ring.id}') | int(0) > 0 else 'disabled' }}`,
            primary: waarde(ring.id),
            secondary: `Binnen ${ring.km} km`,
          })
        ),
      });
    }

    // ---- Onweersparameters ----
    const parameters = [
      {
        id: "sensor.stormchase_cape",
        icon: "mdi:arrow-up-bold-box",
        label: "CAPE",
        kleur:
          "{% set c = states('sensor.stormchase_cape') | float(0) %}" +
          "{{ 'red' if c > 2500 else 'orange' if c > 1000 else 'amber' if c > 300 else 'disabled' }}",
      },
      {
        id: "sensor.stormchase_cape_piek_12_uur",
        icon: "mdi:chart-bell-curve",
        label: "Piek 12u",
        kleur:
          "{% set c = states('sensor.stormchase_cape_piek_12_uur') | float(0) %}" +
          "{{ 'purple' if c > 300 else 'disabled' }}",
      },
      {
        id: "sensor.stormchase_lifted_index",
        icon: "mdi:thermometer-chevron-down",
        label: "Lifted index",
        kleur:
          "{% set li = states('sensor.stormchase_lifted_index') | float(99) %}" +
          "{{ 'red' if li < -6 else 'orange' if li < -3 else 'amber' if li < 0 else 'disabled' }}",
      },
      {
        id: "sensor.stormchase_convectieve_remming",
        icon: "mdi:lock-outline",
        label: "Remming",
        kleur: "blue",
      },
    ].filter((p) => bruikbaar(hass, p.id));

    const heeftPotentie = bruikbaar(hass, "sensor.stormchase_chase_potentie");

    if (parameters.length || heeftPotentie) {
      cards.push(kop("Onweersparameters", "mdi:weather-lightning"));
    }

    if (heeftPotentie) {
      cards.push({
        type: "custom:mushroom-template-card",
        icon: "mdi:radar",
        icon_color:
          "{% set p = states('sensor.stormchase_chase_potentie') | float(0) %}" +
          "{{ 'red' if p > 70 else 'orange' if p > 40 else 'amber' if p > 20 else 'disabled' }}",
        primary: "{{ states('sensor.stormchase_chase_potentie') }}% chase potentie",
        secondary:
          "{% set p = states('sensor.stormchase_chase_potentie') | float(0) %}" +
          "{% if p > 70 %}Alle ingredienten aanwezig" +
          "{% elif p > 40 %}Kans op onweer aanwezig" +
          "{% elif p > 20 %}Beperkte kans" +
          "{% else %}Weinig te verwachten{% endif %}" +
          " \u00b7 CAPE {{ state_attr('sensor.stormchase_chase_potentie','cape_bijdrage') }}" +
          " \u00b7 LI {{ state_attr('sensor.stormchase_chase_potentie','lifted_index_bijdrage') }}" +
          " \u00b7 inslagen {{ state_attr('sensor.stormchase_chase_potentie','inslagen_bijdrage') }}",
        multiline_secondary: true,
        card_mod: { style: TILE_STYLE },
      });
    }

    if (parameters.length) {
      cards.push({
        type: "grid",
        columns: Math.min(parameters.length, 2),
        square: false,
        cards: parameters.map((p) =>
          tegel({
            icon: p.icon,
            icon_color: p.kleur,
            primary: waarde(p.id),
            secondary: p.label,
          })
        ),
      });
    }

    // ---- Zwaar weer: rotatie, hagel en de ingredienten ----
    // Altijd tonen, ook bij nul. Juist het verloop naar boven is wat je wil
    // zien aankomen, en grijze iconen maken duidelijk dat er niets speelt.
    if (bruikbaar(hass, "sensor.stormchase_rotatiekans")) {
      cards.push(
        kop("Zwaar weer \u00b7 kans op basis van omgeving", "mdi:alert-rhombus")
      );

      cards.push({
        type: "grid",
        columns: 2,
        square: false,
        cards: [
          tegel({
            icon: "mdi:rotate-3d-variant",
            icon_color:
              "{% set r = states('sensor.stormchase_rotatiekans') | float(0) %}" +
              "{{ 'red' if r > 60 else 'orange' if r > 30 else 'amber' if r > 10 else 'disabled' }}",
            primary: "{{ states('sensor.stormchase_rotatiekans') }}%",
            secondary: "Rotatiekans",
          }),
          tegel({
            icon: "mdi:weather-hail",
            icon_color:
              "{% set h = states('sensor.stormchase_hagelkans') | float(0) %}" +
              "{{ 'red' if h > 60 else 'orange' if h > 30 else 'amber' if h > 10 else 'disabled' }}",
            primary: "{{ states('sensor.stormchase_hagelkans') }}%",
            secondary: "Hagelkans",
          }),
        ],
      });

      cards.push({
        type: "grid",
        columns: 2,
        square: false,
        cards: [
          tegel({
            icon: "mdi:weather-windy",
            icon_color:
              "{% set s = states('sensor.stormchase_windschering_0_6_km') | float(0) %}" +
              "{{ 'red' if s > 72 else 'orange' if s > 50 else 'amber' if s > 30 else 'disabled' }}",
            primary: waarde("sensor.stormchase_windschering_0_6_km", " km/u"),
            secondary: "Schering 0-6 km",
          }),
          tegel({
            icon: "mdi:weather-windy-variant",
            icon_color:
              "{% set s = states('sensor.stormchase_windschering_0_1_km') | float(0) %}" +
              "{{ 'orange' if s > 30 else 'amber' if s > 15 else 'disabled' }}",
            primary: waarde("sensor.stormchase_windschering_0_1_km", " km/u"),
            secondary: "Schering 0-1 km",
          }),
          tegel({
            icon: "mdi:snowflake-thermometer",
            icon_color:
              "{% set v = states('sensor.stormchase_vriesniveau') | float(0) %}" +
              "{{ 'green' if 2000 <= v <= 3500 else 'disabled' }}",
            primary: waarde("sensor.stormchase_vriesniveau", " m"),
            secondary: "Vriesniveau",
          }),
          tegel({
            icon: "mdi:sigma",
            icon_color:
              "{% set t = states('sensor.stormchase_total_totals_index') | float(0) %}" +
              "{{ 'red' if t > 56 else 'orange' if t > 50 else 'amber' if t > 44 else 'disabled' }}",
            primary: waarde("sensor.stormchase_total_totals_index"),
            secondary: "Total Totals",
          }),
        ],
      });
    }

    // ---- Kompas, alleen zinvol als er richting is ----
    if (bron.azimut && bruikbaar(hass, bron.azimut)) {
      cards.push({
        type: "custom:compass-card",
        name: "Richting laatste inslag",
        indicator_sensors: [
          {
            sensor: bron.azimut,
            indicator: { image: "arrow_outward", color: KLEUR.gevaar },
          },
        ],
        value_sensors: [{ sensor: bron.azimut }],
        card_mod: { style: PANEL_STYLE },
      });
    }

    // ---- Verloopgrafiek met de ringen als referentielijnen ----
    if (bron.afstand) {
      const grenzen = ringen.length
        ? [ringen[0].km, ringen[ringen.length - 1].km]
        : [15, 50];
      cards.push({
        type: "custom:apexcharts-card",
        graph_span: "2h",
        header: {
          show: true,
          title: "Afstand \u00b7 laatste 2 uur",
          show_states: false,
        },
        series: [
          {
            entity: bron.afstand,
            name: "Afstand (km)",
            color: KLEUR.alert,
            type: "line",
            curve: "stepline",
            stroke_width: 2,
            group_by: { func: "min", duration: "1min" },
          },
        ],
        apex_config: {
          chart: { height: 220, background: "transparent" },
          grid: { borderColor: "rgba(255,255,255,.06)" },
          yaxis: { min: 0 },
          annotations: {
            yaxis: [
              {
                y: grenzen[0],
                borderColor: KLEUR.gevaar,
                strokeDashArray: 6,
                label: {
                  text: `${grenzen[0]} km`,
                  style: { background: KLEUR.gevaar, color: "#fff" },
                },
              },
              {
                y: grenzen[1],
                borderColor: KLEUR.gedempt,
                strokeDashArray: 4,
                label: {
                  text: `${grenzen[1]} km`,
                  style: { background: KLEUR.gedempt, color: "#fff" },
                },
              },
            ],
          },
        },
        card_mod: { style: PANEL_STYLE },
      });
    }

    // ---- CAPE-verloop, eventueel met de potentie op een tweede as ----
    if (bruikbaar(hass, "sensor.stormchase_cape")) {
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
      if (heeftPotentie) capeSerie.yaxis_id = "cape";

      const grafiek = {
        type: "custom:apexcharts-card",
        graph_span: "24h",
        header: {
          show: true,
          title: "Instabiliteit \u00b7 24 uur",
          show_states: false,
        },
        series: [capeSerie],
        apex_config: {
          chart: { height: 200, background: "transparent" },
          grid: { borderColor: "rgba(255,255,255,.06)" },
        },
        card_mod: { style: PANEL_STYLE },
      };

      if (heeftPotentie) {
        grafiek.series.push({
          entity: "sensor.stormchase_chase_potentie",
          name: "Potentie (%)",
          color: KLEUR.alert,
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

    // ---- Alle waarden ----
    // Vangnet: wat hierboven geen eigen tegel heeft, staat hier alsnog.
    // Voegt de integratie later een sensor toe, dan verschijnt die vanzelf.
    if (config.alle_waarden !== false && (config._alle || []).length) {
      cards.push(kop("Alle waarden", "mdi:format-list-bulleted"));
      cards.push({
        type: "entities",
        entities: config._alle,
        card_mod: { style: PANEL_STYLE },
      });
    }

    // ---- Meldingen aan/uit ----
    if (hass.states["switch.stormchase_meldingen"]) {
      cards.push({
        type: "custom:mushroom-entity-card",
        entity: "switch.stormchase_meldingen",
        name: "Onweersmeldingen",
        secondary_info: "state",
        tap_action: { action: "toggle" },
        card_mod: { style: TILE_STYLE },
      });
    }

    return { type: "grid", column_span: 1, cards };
  }

  /** De rechterkolom: de kaarten. */
  static kaartenSectie(config, hass) {
    const kaarten = config.maps || {};
    const smal = isSmal();

    // Op een telefoon krijgt een kaart de volle breedte van een smalle
    // kolom; een brede verhouding levert dan een strookje op. Hoger maken
    // dus, zodat je er daadwerkelijk iets op ziet.
    const verhouding = (breed, mobiel) =>
      config.map_ratio || (smal ? mobiel : breed);

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
        aspect_ratio: verhouding("62%", "150%"),
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
        aspect_ratio: verhouding("75%", "120%"),
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
        aspect_ratio: verhouding("78%", "115%"),
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
        aspect_ratio: verhouding("75%", "120%"),
        card_mod: { style: FRAME_STYLE },
      });
    }

    return { type: "grid", column_span: smal ? 2 : 1, cards };
  }

  /** Badges bovenaan: de cijfers die je tijdens een chase wil zien. */
  static badges(config, hass) {
    const { bron } = this.verzamel(config, hass);
    const lijst = [];

    if (bron.afstand) {
      lijst.push({
        type: "entity",
        entity: bron.afstand,
        name: "Afstand",
        color:
          `{% set d = states('${bron.afstand}') | float(999) %}` +
          "{{ 'red' if d < 15 else 'orange' if d < 30 else 'grey' }}",
      });
    }
    if (bruikbaar(hass, "sensor.stormchase_aankomst")) {
      lijst.push({
        type: "entity",
        entity: "sensor.stormchase_aankomst",
        name: "Aankomst",
        color: "red",
      });
    }
    if (bruikbaar(hass, "sensor.stormchase_regen_begint_over")) {
      lijst.push({
        type: "entity",
        entity: "sensor.stormchase_regen_begint_over",
        name: "Regen over",
        color: "blue",
      });
    }
    if (bruikbaar(hass, "sensor.stormchase_chase_potentie")) {
      lijst.push({
        type: "entity",
        entity: "sensor.stormchase_chase_potentie",
        name: "Potentie",
        color:
          "{% set p = states('sensor.stormchase_chase_potentie') | float(0) %}" +
          "{{ 'red' if p > 70 else 'orange' if p > 40 else 'grey' }}",
      });
    }

    return lijst;
  }

  static async bouwView(config, hass) {
    // Werk intern met de nette id's, ook als ze in werkelijkheid anders
    // heten. Zo blijven de kaarten leesbaar en werkt het bij iedereen.
    const { tabel, voorvoegsel } = bouwVertaaltabel(hass);

    const aliassen = { ...hass.states };
    for (const [net, echt] of Object.entries(tabel)) {
      aliassen[net] = hass.states[echt];
    }
    const hulp = { ...hass, states: aliassen };

    // De echte entity-id's van de integratie, gesorteerd. Bewust hier
    // verzameld en niet uit de aliassen, anders komt alles dubbel.
    const alle = Object.keys(hass.states)
      .filter(
        (id) =>
          /^(sensor|binary_sensor|switch|weather)\./.test(id) &&
          id.includes("stormchase")
      )
      .sort();

    const uitgebreid = { ...config, _alle: alle };

    const view = {
      type: "sections",
      max_columns: 2,
      badges: this.badges(uitgebreid, hulp),
      sections: [
        this.statusSectie(uitgebreid, hulp),
        this.kaartenSectie(uitgebreid, hulp),
      ],
    };

    return pasVertaaltabelToe(view, voorvoegsel);
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
