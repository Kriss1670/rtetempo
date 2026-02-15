"""Tests for binary_sensor.py module."""
import datetime
import pytest
from unittest.mock import MagicMock, patch
from hypothesis import given, strategies as st, settings

from custom_components.rtetempo.binary_sensor import OffPeakHours
from custom_components.rtetempo.const import (
    DOMAIN,
    FRANCE_TZ,
    HOUR_OF_CHANGE,
    OFF_PEAK_START,
    DEVICE_NAME,
    DEVICE_MANUFACTURER,
    DEVICE_MODEL,
)


# ============================================================================
# Tests for OffPeakHours (Requirements 8.1-8.4)
# ============================================================================

class TestOffPeakHours:
    """Tests for OffPeakHours binary sensor."""

    def test_init(self):
        """Test OffPeakHours initialization."""
        sensor = OffPeakHours("test_config_id")
        assert sensor._attr_unique_id == f"{DOMAIN}_test_config_id_off_peak"
        assert sensor._attr_name == "Heures Creuses"
        assert sensor._attr_has_entity_name is True
        assert sensor._attr_should_poll is True
        assert sensor._attr_icon == "mdi:cash-clock"

    def test_device_info(self):
        """Test device_info property."""
        sensor = OffPeakHours("test_config_id")
        device_info = sensor.device_info
        
        assert (DOMAIN, "test_config_id") in device_info["identifiers"]
        assert device_info["name"] == DEVICE_NAME
        assert device_info["manufacturer"] == DEVICE_MANUFACTURER
        assert device_info["model"] == DEVICE_MODEL

    def test_update_off_peak_hours_night(self):
        """Test update during off-peak hours (night, after 22h)."""
        sensor = OffPeakHours("test_config_id")
        
        # Mock datetime to return 23:00
        mock_now = datetime.datetime(2025, 1, 15, 23, 0, 0, tzinfo=FRANCE_TZ)
        with patch('custom_components.rtetempo.binary_sensor.datetime') as mock_datetime:
            mock_datetime.datetime.now.return_value = mock_now
            sensor.update()
        
        assert sensor._attr_is_on is True

    def test_update_off_peak_hours_early_morning(self):
        """Test update during off-peak hours (early morning, before 6h)."""
        sensor = OffPeakHours("test_config_id")
        
        # Mock datetime to return 5:00
        mock_now = datetime.datetime(2025, 1, 15, 5, 0, 0, tzinfo=FRANCE_TZ)
        with patch('custom_components.rtetempo.binary_sensor.datetime') as mock_datetime:
            mock_datetime.datetime.now.return_value = mock_now
            sensor.update()
        
        assert sensor._attr_is_on is True

    def test_update_peak_hours_morning(self):
        """Test update during peak hours (morning)."""
        sensor = OffPeakHours("test_config_id")
        
        # Mock datetime to return 10:00
        mock_now = datetime.datetime(2025, 1, 15, 10, 0, 0, tzinfo=FRANCE_TZ)
        with patch('custom_components.rtetempo.binary_sensor.datetime') as mock_datetime:
            mock_datetime.datetime.now.return_value = mock_now
            sensor.update()
        
        assert sensor._attr_is_on is False

    def test_update_peak_hours_afternoon(self):
        """Test update during peak hours (afternoon)."""
        sensor = OffPeakHours("test_config_id")
        
        # Mock datetime to return 15:00
        mock_now = datetime.datetime(2025, 1, 15, 15, 0, 0, tzinfo=FRANCE_TZ)
        with patch('custom_components.rtetempo.binary_sensor.datetime') as mock_datetime:
            mock_datetime.datetime.now.return_value = mock_now
            sensor.update()
        
        assert sensor._attr_is_on is False

    def test_update_boundary_6h(self):
        """Test update at exactly 6h (start of peak hours)."""
        sensor = OffPeakHours("test_config_id")
        
        # Mock datetime to return exactly 6:00
        mock_now = datetime.datetime(2025, 1, 15, 6, 0, 0, tzinfo=FRANCE_TZ)
        with patch('custom_components.rtetempo.binary_sensor.datetime') as mock_datetime:
            mock_datetime.datetime.now.return_value = mock_now
            sensor.update()
        
        # At 6h, we're in peak hours (6 <= hour < 22)
        assert sensor._attr_is_on is False

    def test_update_boundary_22h(self):
        """Test update at exactly 22h (start of off-peak hours)."""
        sensor = OffPeakHours("test_config_id")
        
        # Mock datetime to return exactly 22:00
        mock_now = datetime.datetime(2025, 1, 15, 22, 0, 0, tzinfo=FRANCE_TZ)
        with patch('custom_components.rtetempo.binary_sensor.datetime') as mock_datetime:
            mock_datetime.datetime.now.return_value = mock_now
            sensor.update()
        
        # At 22h, we're in off-peak hours (hour >= 22)
        assert sensor._attr_is_on is True


# ============================================================================
# Property Test for Off-Peak Hours (Property 2)
# ============================================================================

class TestProperty2OffPeakHours:
    """Property test for Off-Peak Hours binary classification."""

    # Feature: remaining-test-coverage, Property 2: Off-Peak Hours Binary Classification
    @given(st.integers(min_value=0, max_value=23))
    @settings(max_examples=100)
    def test_off_peak_hours_classification(self, hour):
        """For any hour, is_on should be True iff hour >= OFF_PEAK_START or hour < HOUR_OF_CHANGE."""
        sensor = OffPeakHours("test_config_id")
        
        mock_now = datetime.datetime(2025, 1, 15, hour, 30, 0, tzinfo=FRANCE_TZ)
        with patch('custom_components.rtetempo.binary_sensor.datetime') as mock_datetime:
            mock_datetime.datetime.now.return_value = mock_now
            sensor.update()
        
        expected_is_on = (hour >= OFF_PEAK_START or hour < HOUR_OF_CHANGE)
        assert sensor._attr_is_on == expected_is_on, f"Hour {hour}: expected {expected_is_on}, got {sensor._attr_is_on}"
