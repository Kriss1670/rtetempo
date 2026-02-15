from __future__ import annotations

import logging
from datetime import timedelta
from typing import List

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.event import async_track_time_change

from .forecast import ForecastDay, async_fetch_opendpe_forecast
from .tempo_rules import apply_tempo_rules

_LOGGER = logging.getLogger(__name__)


class ForecastCoordinator(DataUpdateCoordinator[List[ForecastDay]]):
    """Coordinator in charge of fetching Open-DPE forecasts."""

    def __init__(self, hass: HomeAssistant):
        """Initializing the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="Tempo Forecast Coordinator",
            update_interval=timedelta(hours=6),  # refresh every 6 hours
        )

        self.hass = hass
        self.session = async_get_clientsession(hass)

        # Daily update after midnight then every 6 hours (JSON is updated around 06:00)
        # Store the cancel function to allow proper cleanup on unload
        self._cancel_time_change = async_track_time_change(
            hass,
            self._scheduled_refresh,
            hour=7,
            minute=0,
            second=0,
        )

        _LOGGER.debug(
            "ForecastCoordinator initialisé : refresh quotidien programmé à 07:00 + intervalle 6h"
        )

    def async_unload(self) -> None:
        """Cleanup when the coordinator is unloaded."""
        if self._cancel_time_change is not None:
            self._cancel_time_change()
            self._cancel_time_change = None
            _LOGGER.debug("ForecastCoordinator: time change listener cancelled")

    async def _scheduled_refresh(self, now):
        """Update at 07:00 every day."""
        _LOGGER.debug("Open DPE: lancement du refresh programmé à 07:00")
        await self.async_request_refresh()

    async def _async_update_data(self) -> List[ForecastDay]:
        """Open DPE data recovery."""
        try:
            forecasts = await async_fetch_opendpe_forecast(self.session)
            adjusted_forecasts = apply_tempo_rules(forecasts)
            _LOGGER.debug("Open DPE: %s jours récupérés et ajustés", len(adjusted_forecasts))
            return adjusted_forecasts

        except Exception as exc:
            _LOGGER.error("Open DPE: erreur lors de la mise à jour: %s", exc)
            raise UpdateFailed(f"Erreur mise à jour des prévisions Open DPE: {exc}")

