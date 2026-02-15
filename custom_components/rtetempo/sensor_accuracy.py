"""Sensor for Tempo forecast accuracy.

This module provides a sensor that displays the accuracy of Tempo forecasts
by comparing predictions to actual colors.

Note:
    This sensor requires the Open DPE forecast option to be enabled in the
    integration options. The accuracy sensor analyzes historical data from
    the forecast sensors (J+2 to J+7), so it will only be created when
    forecasts are enabled. Without forecast history, there is no data to
    analyze.
    
    The AccuracyAnalyzer class contains the core business logic and is
    thoroughly tested in tests/test_accuracy.py. This sensor class is a
    thin wrapper that exposes the analyzer results as a Home Assistant
    sensor entity.
"""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.components.sensor import SensorEntity

from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo

from .accuracy import AccuracyAnalyzer
from .const import (
    DEVICE_MANUFACTURER,
    DEVICE_MODEL,
    DEVICE_NAME,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(hours=1)


class TempoAccuracySensor(SensorEntity):
    """Sensor showing forecast accuracy percentage.
    
    This sensor compares forecast predictions (J+2) to actual colors
    and calculates the accuracy percentage. Sundays and French holidays
    are excluded from the calculation.
    
    Attributes:
        state: Accuracy percentage for last 30 days
        accuracy_7d: Accuracy percentage for last 7 days
        accuracy_30d: Accuracy percentage for last 30 days
        accuracy_j2..j7: Accuracy percentage per horizon
        total_days: Total number of days analyzed
        correct_predictions: Number of correct predictions
        incorrect_predictions: Number of incorrect predictions
        excluded_predictions: Number of excluded days (Sundays/holidays)
        past_matrix: Matrix of past comparison results
        future_matrix: Matrix of upcoming forecast comparison results
    """
    
    _attr_has_entity_name = True
    _attr_name = "Forecast Accuracy"
    _attr_native_unit_of_measurement = "%"
    _attr_icon = "mdi:chart-donut"
    
    def __init__(self, hass: HomeAssistant, config_id: str) -> None:
        """Initialize the accuracy sensor.
        
        Args:
            hass: Home Assistant instance
            config_id: Config entry ID for unique identification
        """
        self.hass = hass
        self._config_id = config_id
        self._attr_unique_id = f"{DOMAIN}_{config_id}_forecast_accuracy"
        self._analyzer = AccuracyAnalyzer(hass)
        self._data: dict[str, Any] = {}
    
    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, self._config_id)},
            name=DEVICE_NAME,
            manufacturer=DEVICE_MANUFACTURER,
            model=DEVICE_MODEL,
        )
    
    @property
    def native_value(self) -> float | None:
        """Return the accuracy percentage."""
        return self._data.get("accuracy_30d")
    
    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        return self._data
    
    async def async_update(self) -> None:
        """Update accuracy data from history."""
        try:
            self._data = await self._analyzer.analyze(days=30)
            self._attr_available = True
        except Exception as err:
            _LOGGER.error("Error analyzing forecast accuracy: %s", err)
            self._data = {}
            self._attr_available = False
