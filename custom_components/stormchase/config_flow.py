"""Config flow voor Stormchase."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    ALERT_COUNTRIES,
    ALERT_LEVEL_CHOICES,
    CONF_ALERT_COUNTRY,
    CONF_ALERT_MIN_LEVEL,
    CONF_ALERT_NOTIFY,
    CONF_ALERT_REGION,
    CONF_AZIMUTH_SENSOR,
    DEFAULT_ALERT_COUNTRY,
    DEFAULT_ALERT_MIN_LEVEL,
    CONF_NOTIFY_COOLDOWN,
    CONF_NOTIFY_MAX_DISTANCE,
    CONF_NOTIFY_ON_APPROACH,
    CONF_NOTIFY_ON_CLEARED,
    CONF_NOTIFY_SERVICES,
    CONF_NOTIFY_TITLE,
    CONF_QUIET_FROM,
    CONF_QUIET_TO,
    CONF_ONLY_STATIONARY,
    CONF_RAIN_LEAD,
    CONF_RAIN_NOTIFY,
    CONF_RAIN_THRESHOLD,
    CONF_STATIONARY_MINUTES,
    CONF_WIND_NOTIFY,
    CONF_WIND_THRESHOLD,
    DEFAULT_STATIONARY_MINUTES,
    DEFAULT_WIND_THRESHOLD,
    DEFAULT_RAIN_LEAD,
    DEFAULT_RAIN_THRESHOLD,
    DEFAULT_NOTIFY_COOLDOWN,
    DEFAULT_NOTIFY_MAX_DISTANCE,
    DEFAULT_NOTIFY_TITLE,
    DEFAULT_QUIET,
    CONF_COUNTER_SENSOR,
    CONF_DISTANCE_SENSOR,
    CONF_GEO_PATTERN,
    CONF_LOCATION_MODE,
    CONF_MANUAL_LOCATION,
    CONF_RING_FAR,
    CONF_RING_MID,
    CONF_RING_NEAR,
    CONF_RING_WINDOW,
    CONF_TRACKER_ENTITY,
    CONF_WARN_DISTANCE,
    CONF_ZONE_ENTITY,
    DEFAULT_GEO_PATTERN,
    DEFAULT_RING_FAR,
    DEFAULT_RING_MID,
    DEFAULT_RING_NEAR,
    DEFAULT_RING_WINDOW,
    DEFAULT_WARN_DISTANCE,
    DOMAIN,
    LOCATION_MODES,
    MODE_HOME,
    MODE_MANUAL,
    MODE_TRACKER,
    MODE_ZONE,
)

SENSOR_SELECTOR = selector.EntitySelector(
    selector.EntitySelectorConfig(domain="sensor")
)


def _km(maximum: int) -> selector.NumberSelector:
    """Getalveld in kilometers."""
    return selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=1,
            max=maximum,
            step=1,
            unit_of_measurement="km",
            mode=selector.NumberSelectorMode.BOX,
        )
    )


def _guess(hass, suffix: str) -> str | None:
    """Raad de Blitzortung-sensor op basis van het achtervoegsel.

    De entity-namen krijgen de naam van de config-entry mee, dus
    sensor.onweer_detectie_lightning_distance komt net zo goed voor als
    sensor.blitzortung_lightning_distance.
    """
    for state in hass.states.async_all("sensor"):
        if state.entity_id.endswith(suffix):
            return state.entity_id
    return None


def _base_schema(hass, defaults: dict[str, Any]) -> vol.Schema:
    """Bronsensoren en afstanden."""
    return vol.Schema(
        {
            vol.Required(
                CONF_DISTANCE_SENSOR,
                default=defaults.get(CONF_DISTANCE_SENSOR)
                or _guess(hass, "_lightning_distance"),
            ): SENSOR_SELECTOR,
            vol.Required(
                CONF_AZIMUTH_SENSOR,
                default=defaults.get(CONF_AZIMUTH_SENSOR)
                or _guess(hass, "_lightning_azimuth"),
            ): SENSOR_SELECTOR,
            vol.Optional(
                CONF_COUNTER_SENSOR,
                default=defaults.get(CONF_COUNTER_SENSOR)
                or _guess(hass, "_lightning_counter"),
            ): SENSOR_SELECTOR,
            vol.Required(
                CONF_GEO_PATTERN,
                default=defaults.get(CONF_GEO_PATTERN, DEFAULT_GEO_PATTERN),
            ): str,
            vol.Required(
                CONF_WARN_DISTANCE,
                default=defaults.get(CONF_WARN_DISTANCE, DEFAULT_WARN_DISTANCE),
            ): _km(100),
            vol.Required(
                CONF_RING_NEAR,
    CONF_RING_WINDOW,
                default=defaults.get(CONF_RING_NEAR, DEFAULT_RING_NEAR),
            ): _km(100),
            vol.Required(
                CONF_RING_MID,
                default=defaults.get(CONF_RING_MID, DEFAULT_RING_MID),
            ): _km(200),
            vol.Required(
                CONF_RING_FAR,
                default=defaults.get(CONF_RING_FAR, DEFAULT_RING_FAR),
            ): _km(500),
            vol.Required(
                CONF_RING_WINDOW,
                default=defaults.get(CONF_RING_WINDOW, DEFAULT_RING_WINDOW),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=15, max=360, step=15, unit_of_measurement="min",
                    mode=selector.NumberSelectorMode.BOX,
                )
            ),
            vol.Required(
                CONF_LOCATION_MODE,
                default=defaults.get(CONF_LOCATION_MODE, MODE_HOME),
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=LOCATION_MODES,
                    translation_key="location_mode",
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
        }
    )


def _location_schema(mode: str, defaults: dict[str, Any]) -> vol.Schema:
    """Vervolgvraag die hoort bij de gekozen locatiemodus."""
    if mode == MODE_ZONE:
        return vol.Schema(
            {
                vol.Required(
                    CONF_ZONE_ENTITY, default=defaults.get(CONF_ZONE_ENTITY)
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="zone")
                )
            }
        )

    if mode == MODE_TRACKER:
        return vol.Schema(
            {
                vol.Required(
                    CONF_TRACKER_ENTITY, default=defaults.get(CONF_TRACKER_ENTITY)
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain=["device_tracker", "person"]
                    )
                )
            }
        )

    return vol.Schema(
        {
            vol.Required(
                CONF_MANUAL_LOCATION, default=defaults.get(CONF_MANUAL_LOCATION)
            ): selector.LocationSelector()
        }
    )


def _notify_schema(hass, defaults: dict[str, Any]) -> vol.Schema:
    """Instellingen voor de meldingen."""
    # De beschikbare notify-diensten opzoeken, zodat de gebruiker kan kiezen
    # in plaats van een servicenaam te moeten intikken.
    diensten = sorted(hass.services.async_services().get("notify", {}))
    opties = [
        selector.SelectOptionDict(value=naam, label=f"notify.{naam}")
        for naam in diensten
    ]

    return vol.Schema(
        {
            vol.Optional(
                CONF_NOTIFY_SERVICES,
                default=defaults.get(CONF_NOTIFY_SERVICES, []),
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=opties,
                    multiple=True,
                    custom_value=True,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Required(
                CONF_NOTIFY_MAX_DISTANCE,
                default=defaults.get(
                    CONF_NOTIFY_MAX_DISTANCE, DEFAULT_NOTIFY_MAX_DISTANCE
                ),
            ): _km(200),
            vol.Required(
                CONF_NOTIFY_ON_APPROACH,
                default=defaults.get(CONF_NOTIFY_ON_APPROACH, True),
            ): selector.BooleanSelector(),
            vol.Required(
                CONF_NOTIFY_ON_CLEARED,
                default=defaults.get(CONF_NOTIFY_ON_CLEARED, False),
            ): selector.BooleanSelector(),
            vol.Required(
                CONF_NOTIFY_TITLE,
                default=defaults.get(CONF_NOTIFY_TITLE, DEFAULT_NOTIFY_TITLE),
            ): str,
            vol.Required(
                CONF_NOTIFY_COOLDOWN,
                default=defaults.get(CONF_NOTIFY_COOLDOWN, DEFAULT_NOTIFY_COOLDOWN),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0, max=180, step=5, unit_of_measurement="min",
                    mode=selector.NumberSelectorMode.BOX,
                )
            ),
            vol.Required(
                CONF_RAIN_NOTIFY,
                default=defaults.get(CONF_RAIN_NOTIFY, True),
            ): selector.BooleanSelector(),
            vol.Required(
                CONF_RAIN_LEAD,
                default=defaults.get(CONF_RAIN_LEAD, DEFAULT_RAIN_LEAD),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=5, max=120, step=5, unit_of_measurement="min",
                    mode=selector.NumberSelectorMode.BOX,
                )
            ),
            vol.Required(
                CONF_RAIN_THRESHOLD,
                default=defaults.get(CONF_RAIN_THRESHOLD, DEFAULT_RAIN_THRESHOLD),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0.1, max=5, step=0.1, unit_of_measurement="mm/h",
                    mode=selector.NumberSelectorMode.BOX,
                )
            ),
            vol.Required(
                CONF_WIND_NOTIFY,
                default=defaults.get(CONF_WIND_NOTIFY, True),
            ): selector.BooleanSelector(),
            vol.Required(
                CONF_WIND_THRESHOLD,
                default=defaults.get(CONF_WIND_THRESHOLD, DEFAULT_WIND_THRESHOLD),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=30, max=150, step=5, unit_of_measurement="km/h",
                    mode=selector.NumberSelectorMode.BOX,
                )
            ),
            vol.Required(
                CONF_ONLY_STATIONARY,
                default=defaults.get(CONF_ONLY_STATIONARY, True),
            ): selector.BooleanSelector(),
            vol.Required(
                CONF_STATIONARY_MINUTES,
                default=defaults.get(
                    CONF_STATIONARY_MINUTES, DEFAULT_STATIONARY_MINUTES
                ),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=5, max=60, step=5, unit_of_measurement="min",
                    mode=selector.NumberSelectorMode.BOX,
                )
            ),
            vol.Required(
                CONF_QUIET_FROM,
                default=defaults.get(CONF_QUIET_FROM, DEFAULT_QUIET),
            ): selector.TimeSelector(),
            vol.Required(
                CONF_QUIET_TO,
                default=defaults.get(CONF_QUIET_TO, DEFAULT_QUIET),
            ): selector.TimeSelector(),
        }
    )


def _alert_schema(defaults: dict[str, Any]) -> vol.Schema:
    """Instellingen voor de officiele weerwaarschuwingen."""
    return vol.Schema(
        {
            vol.Required(
                CONF_ALERT_COUNTRY,
                default=defaults.get(CONF_ALERT_COUNTRY, DEFAULT_ALERT_COUNTRY),
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=ALERT_COUNTRIES,
                    translation_key="alert_country",
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Optional(
                CONF_ALERT_REGION,
                default=defaults.get(CONF_ALERT_REGION, ""),
            ): str,
            vol.Required(
                CONF_ALERT_MIN_LEVEL,
                default=defaults.get(CONF_ALERT_MIN_LEVEL, DEFAULT_ALERT_MIN_LEVEL),
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=ALERT_LEVEL_CHOICES,
                    translation_key="alert_level",
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Required(
                CONF_ALERT_NOTIFY,
                default=defaults.get(CONF_ALERT_NOTIFY, True),
            ): selector.BooleanSelector(),
        }
    )


def _validate_rings(user_input: dict[str, Any]) -> str | None:
    """Controleer of de ringen oplopend en verschillend zijn."""
    rings = [
        user_input[CONF_RING_NEAR],
        user_input[CONF_RING_MID],
        user_input[CONF_RING_FAR],
    ]
    if rings != sorted(rings) or len(set(rings)) != 3:
        return "rings_not_ascending"
    return None


class StormchaseConfigFlow(ConfigFlow, domain=DOMAIN):
    """Eerste installatie van de integratie."""

    VERSION = 1

    def __init__(self) -> None:
        """Bewaar de tussenstand tussen de stappen."""
        self._data: dict[str, Any] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Vraag de bronsensoren, afstanden en locatiemodus."""
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        errors: dict[str, str] = {}

        if user_input is not None:
            error = _validate_rings(user_input)
            if error:
                errors["base"] = error
            else:
                self._data = user_input
                if user_input[CONF_LOCATION_MODE] == MODE_HOME:
                    return await self.async_step_notify()
                return await self.async_step_location()

        return self.async_show_form(
            step_id="user",
            data_schema=_base_schema(self.hass, user_input or {}),
            errors=errors,
            description_placeholders={
                "latitude": f"{self.hass.config.latitude:.4f}",
                "longitude": f"{self.hass.config.longitude:.4f}",
            },
        )

    async def async_step_location(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Vraag de zone, tracker of coordinaten."""
        mode = self._data[CONF_LOCATION_MODE]

        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_notify()

        return self.async_show_form(
            step_id="location",
            data_schema=_location_schema(mode, self._data),
            description_placeholders={"mode": mode},
        )

    async def async_step_notify(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Vraag hoe en wanneer er gemeld moet worden."""
        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_alerts()

        return self.async_show_form(
            step_id="notify",
            data_schema=_notify_schema(self.hass, self._data),
        )

    async def async_step_alerts(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Vraag de instellingen voor officiele waarschuwingen."""
        if user_input is not None:
            self._data.update(user_input)
            return self.async_create_entry(title="Stormchase", data=self._data)

        return self.async_show_form(
            step_id="alerts", data_schema=_alert_schema(self._data)
        )

    @staticmethod
    @callback
    def async_get_options_flow(entry: ConfigEntry) -> StormchaseOptionsFlow:
        """Koppel de options flow."""
        return StormchaseOptionsFlow()


class StormchaseOptionsFlow(OptionsFlow):
    """Achteraf aanpassen van dezelfde instellingen."""

    def __init__(self) -> None:
        """Bewaar de tussenstand tussen de stappen."""
        self._data: dict[str, Any] = {}

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Toon hetzelfde formulier met de huidige waarden."""
        current = {**self.config_entry.data, **self.config_entry.options}
        errors: dict[str, str] = {}

        if user_input is not None:
            error = _validate_rings(user_input)
            if error:
                errors["base"] = error
            else:
                self._data = {**current, **user_input}
                if user_input[CONF_LOCATION_MODE] == MODE_HOME:
                    # Oude locatiegegevens opruimen, anders blijven ze
                    # rondslingeren in de opties.
                    for key in (
                        CONF_ZONE_ENTITY,
                        CONF_TRACKER_ENTITY,
                        CONF_MANUAL_LOCATION,
                    ):
                        self._data.pop(key, None)
                    return await self.async_step_notify()
                return await self.async_step_location()

        return self.async_show_form(
            step_id="init",
            data_schema=_base_schema(self.hass, current),
            errors=errors,
        )

    async def async_step_location(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Vraag de zone, tracker of coordinaten."""
        mode = self._data[CONF_LOCATION_MODE]

        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_notify()

        return self.async_show_form(
            step_id="location",
            data_schema=_location_schema(mode, self._data),
            description_placeholders={"mode": mode},
        )

    async def async_step_notify(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Vraag hoe en wanneer er gemeld moet worden."""
        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_alerts()

        return self.async_show_form(
            step_id="notify",
            data_schema=_notify_schema(self.hass, self._data),
        )

    async def async_step_alerts(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Vraag de instellingen voor officiele waarschuwingen."""
        if user_input is not None:
            self._data.update(user_input)
            return self.async_create_entry(title="", data=self._data)

        return self.async_show_form(
            step_id="alerts", data_schema=_alert_schema(self._data)
        )
