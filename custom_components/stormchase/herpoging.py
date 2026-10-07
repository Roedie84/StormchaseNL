"""Een mislukte bron snel opnieuw proberen (0.43.0).

Zonder dit wacht een bron na een storing gewoon het hele interval af. Bij
Open-Meteo is dat een half uur: tijdens een DNS-storing op 7 oktober om
16:45 bleven CAPE, Lifted Index en windschering daardoor een uur oud, terwijl
de storing na een paar minuten al voorbij was.

Na een mislukte ronde komt er nu een herkansing na 2 minuten, daarna na 5
minuten, en daarna weer het gewone interval. Zo blijft het bij hooguit twee
extra verzoeken per storing en wordt geen enkele API bestookt. Een bron die
"te veel verzoeken" (429) meldt, krijgt geen herkansing: dan wachten we het
gewone interval af, of langer als de bron dat via Retry-After vraagt.

Bewust vrij van Home Assistant-imports, zodat het zonder HA te testen is.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

# De wachttijden na de eerste en tweede mislukte ronde op rij. Daarna geldt
# weer het gewone interval, tot de bron een keer slaagt.
HERPOGINGEN = (timedelta(minutes=2), timedelta(minutes=5))

# Een Retry-After langer dan dit nemen we niet over; dan is er iets vreemds
# aan de hand en is het gewone interval verstandiger dan uren stil liggen.
MAX_RETRY_AFTER = timedelta(hours=2)


def is_beperkt(fout) -> bool:
    """Of de bron ons afremt (HTTP 429, te veel verzoeken)."""
    return getattr(fout, "status", None) == 429


def retry_after(fout) -> timedelta | None:
    """De wachttijd die de bron zelf opgeeft, in seconden (Retry-After)."""
    headers = getattr(fout, "headers", None)
    if not headers:
        return None
    try:
        waarde = headers.get("Retry-After")
    except AttributeError:
        return None
    if waarde is None:
        return None
    try:
        seconden = int(str(waarde).strip())
    except ValueError:
        return None  # een datum als Retry-After komt zelden voor; negeren
    if seconden <= 0:
        return None
    return min(timedelta(seconds=seconden), MAX_RETRY_AFTER)


def volgende_interval(
    normaal: timedelta,
    poging: int,
    beperkt: bool = False,
    wacht: timedelta | None = None,
) -> timedelta:
    """Hoe lang tot de volgende ronde.

    poging is het aantal mislukte rondes op rij (0 = laatste ronde ging
    goed). Bij afremming nooit eerder dan het gewone interval, en nooit
    eerder dan de bron zelf vraagt. Een herkansing is ook nooit langer dan
    het gewone interval: een bron die elke 5 minuten ophaalt, krijgt na een
    storing hooguit één vervroegde poging.
    """
    if beperkt:
        return max(normaal, wacht or normaal)
    if poging <= 0 or poging > len(HERPOGINGEN):
        return normaal
    return min(HERPOGINGEN[poging - 1], normaal)


class HerpogingMixin:
    """Plant na een mislukte ronde een herkansing in.

    Een coordinator noemt in _herpoging_bronnen welke bronnen in de
    statistieken bij hem horen, en zet zijn ophaalronde in _haal_op in
    plaats van _async_update_data. Na elke ronde kijkt de mixin of een van
    die bronnen faalde en past het interval van de volgende ronde aan.
    """

    _herpoging_bronnen: tuple[str, ...] = ()
    _herpoging_nr = 0
    _normaal_interval: timedelta | None = None

    async def _async_update_data(self):
        """De ophaalronde, met daarna het plannen van de volgende."""
        stats = getattr(self, "stats", None)
        voor = self._mislukt_tellers(stats)
        try:
            return await self._haal_op()
        finally:
            self._plan_volgende(stats, voor)

    def _mislukt_tellers(self, stats) -> dict[str, int]:
        if stats is None:
            return {}
        return {
            naam: stats.bronnen[naam].mislukt
            for naam in self._herpoging_bronnen
            if naam in stats.bronnen
        }

    def _plan_volgende(
        self, stats, voor: dict[str, int], nu: datetime | None = None
    ) -> timedelta | None:
        """Zet het interval voor de volgende ronde en noteer het per bron."""
        if stats is None:
            return None
        if self._normaal_interval is None:
            self._normaal_interval = self.update_interval
        normaal = self._normaal_interval
        if normaal is None:
            return None

        bronnen = [stats.bronnen[n] for n in voor]
        # Gefaald: deze ronde een fout erbij, en de laatste poging mislukte.
        # Lukt het ensemble pas bij het tweede model, dan is er niets mis.
        gefaald = [
            b
            for n, b in zip(voor, bronnen)
            if b.mislukt > voor[n] and b.op_rij_mislukt > 0
        ]
        if gefaald:
            self._herpoging_nr += 1
        else:
            self._herpoging_nr = 0

        # Eén afgeremde bron remt de hele ronde: een ronde haalt alle
        # bronnen van deze coordinator op, vaak bij dezelfde aanbieder.
        afgeremd = [b for b in gefaald if b.beperkt]
        wacht = max((b.retry_after for b in afgeremd if b.retry_after), default=None)
        interval = volgende_interval(normaal, self._herpoging_nr, bool(afgeremd), wacht)
        self.update_interval = interval

        nu = nu or datetime.now(timezone.utc)
        moment = nu + interval
        for bron in bronnen:
            bron.volgende_poging = moment
            bron.herkansing = interval < normaal and any(bron is g for g in gefaald)
        return interval
