"""Tests for sensor.py module."""
import datetime
import pytest
from unittest.mock import patch
from hypothesis import given, strategies as st, settings

from custom_components.rtetempo.sensor import (
    CurrentColor,
    NextColor,
    NextColorTime,
    NextCycleTime,
    OffPeakChangeTime,
    DaysLeft,
    DaysUsed,
    get_color_emoji,
    get_color_name,
    get_color_icon,
)
from custom_components.rtetempo.api_worker import TempoDay
from custom_components.rtetempo.const import (
    DOMAIN,
    FRANCE_TZ,
    HOUR_OF_CHANGE,
    OFF_PEAK_START,
    CYCLE_START_MONTH,
    CYCLE_START_DAY,
    API_VALUE_BLUE,
    API_VALUE_WHITE,
    API_VALUE_RED,
    SENSOR_COLOR_BLUE_EMOJI,
    SENSOR_COLOR_WHITE_EMOJI,
    SENSOR_COLOR_RED_EMOJI,
    SENSOR_COLOR_UNKNOWN_EMOJI,
    SENSOR_COLOR_BLUE_NAME,
    SENSOR_COLOR_WHITE_NAME,
    SENSOR_COLOR_RED_NAME,
    SENSOR_COLOR_UNKNOWN_NAME,
    DEVICE_NAME,
    DEVICE_MANUFACTURER,
    DEVICE_MODEL,
)


# ============================================================================
# Tests for helper functions (Requirements 17.1-17.4)
# ============================================================================

class TestSensorHelpers:
    """Tests for sensor helper functions."""

    def test_get_color_emoji_blue(self):
        """Test get_color_emoji for BLUE."""
        assert get_color_emoji(API_VALUE_BLUE) == SENSOR_COLOR_BLUE_EMOJI

    def test_get_color_emoji_white(self):
        """Test get_color_emoji for WHITE."""
        assert get_color_emoji(API_VALUE_WHITE) == SENSOR_COLOR_WHITE_EMOJI

    def test_get_color_emoji_red(self):
        """Test get_color_emoji for RED."""
        assert get_color_emoji(API_VALUE_RED) == SENSOR_COLOR_RED_EMOJI

    def test_get_color_emoji_unknown(self):
        """Test get_color_emoji for unknown color."""
        assert get_color_emoji("UNKNOWN") == SENSOR_COLOR_UNKNOWN_EMOJI

    def test_get_color_name_blue(self):
        """Test get_color_name for BLUE."""
        assert get_color_name(API_VALUE_BLUE) == SENSOR_COLOR_BLUE_NAME

    def test_get_color_name_white(self):
        """Test get_color_name for WHITE."""
        assert get_color_name(API_VALUE_WHITE) == SENSOR_COLOR_WHITE_NAME

    def test_get_color_name_red(self):
        """Test get_color_name for RED."""
        assert get_color_name(API_VALUE_RED) == SENSOR_COLOR_RED_NAME

    def test_get_color_name_unknown(self):
        """Test get_color_name for unknown color."""
        assert get_color_name("UNKNOWN") == SENSOR_COLOR_UNKNOWN_NAME

    def test_get_color_icon_blue(self):
        """Test get_color_icon for BLUE."""
        assert get_color_icon(API_VALUE_BLUE) == "mdi:check-bold"

    def test_get_color_icon_white(self):
        """Test get_color_icon for WHITE."""
        assert get_color_icon(API_VALUE_WHITE) == "mdi:information-outline"

    def test_get_color_icon_red(self):
        """Test get_color_icon for RED."""
        assert get_color_icon(API_VALUE_RED) == "mdi:alert"

    def test_get_color_icon_unknown(self):
        """Test get_color_icon for unknown color."""
        assert get_color_icon("UNKNOWN") == "mdi:palette"


# ============================================================================
# Tests for CurrentColor (Requirements 13.1-13.4)
# ============================================================================

class TestCurrentColor:
    """Tests for CurrentColor sensor."""

    def test_init_visual_false(self, mock_api_worker):
        """Test CurrentColor initialization with visual=False."""
        sensor = CurrentColor("test_config_id", mock_api_worker, False)
        
        assert sensor._attr_name == "Couleur actuelle"
        assert sensor._attr_unique_id == f"{DOMAIN}_test_config_id_current_color"
        assert SENSOR_COLOR_BLUE_NAME in sensor._attr_options

    def test_init_visual_true(self, mock_api_worker):
        """Test CurrentColor initialization with visual=True."""
        sensor = CurrentColor("test_config_id", mock_api_worker, True)
        
        assert sensor._attr_name == "Couleur actuelle (visuel)"
        assert sensor._attr_unique_id == f"{DOMAIN}_test_config_id_current_color_emoji"
        assert SENSOR_COLOR_BLUE_EMOJI in sensor._attr_options

    def test_device_info(self, mock_api_worker):
        """Test device_info property."""
        sensor = CurrentColor("test_config_id", mock_api_worker, False)
        device_info = sensor.device_info
        
        assert (DOMAIN, "test_config_id") in device_info["identifiers"]
        assert device_info["name"] == DEVICE_NAME

    def test_update_with_match_visual_false(self, mock_api_worker):
        """Test update when current time matches a tempo_day (visual=False)."""
        now = datetime.datetime.now(FRANCE_TZ)
        
        # Create tempo day that includes current time
        start_dt = now.replace(hour=6, minute=0, second=0, microsecond=0)
        if now.hour < 6:
            start_dt = start_dt - datetime.timedelta(days=1)
        end_dt = start_dt + datetime.timedelta(days=1)
        
        tempo_days = [
            TempoDay(Start=start_dt, End=end_dt, Value=API_VALUE_BLUE, Updated=now),
        ]
        mock_api_worker.get_adjusted_days.return_value = tempo_days
        
        sensor = CurrentColor("test_config_id", mock_api_worker, False)
        
        with patch('custom_components.rtetempo.sensor.datetime') as mock_datetime:
            mock_datetime.datetime.now.return_value = now
            sensor.update()
        
        assert sensor._attr_available is True
        assert sensor._attr_native_value == SENSOR_COLOR_BLUE_NAME

    def test_update_with_match_visual_true(self, mock_api_worker):
        """Test update when current time matches a tempo_day (visual=True)."""
        now = datetime.datetime.now(FRANCE_TZ)
        
        start_dt = now.replace(hour=6, minute=0, second=0, microsecond=0)
        if now.hour < 6:
            start_dt = start_dt - datetime.timedelta(days=1)
        end_dt = start_dt + datetime.timedelta(days=1)
        
        tempo_days = [
            TempoDay(Start=start_dt, End=end_dt, Value=API_VALUE_WHITE, Updated=now),
        ]
        mock_api_worker.get_adjusted_days.return_value = tempo_days
        
        sensor = CurrentColor("test_config_id", mock_api_worker, True)
        
        with patch('custom_components.rtetempo.sensor.datetime') as mock_datetime:
            mock_datetime.datetime.now.return_value = now
            sensor.update()
        
        assert sensor._attr_available is True
        assert sensor._attr_native_value == SENSOR_COLOR_WHITE_EMOJI
        assert sensor._attr_icon == "mdi:information-outline"

    def test_update_no_match(self, mock_api_worker):
        """Test update when no tempo_day matches."""
        now = datetime.datetime.now(FRANCE_TZ)
        
        # Create tempo day in the past
        past_dt = datetime.datetime(2020, 1, 1, 6, 0, 0, tzinfo=FRANCE_TZ)
        tempo_days = [
            TempoDay(Start=past_dt, End=past_dt + datetime.timedelta(days=1), Value=API_VALUE_BLUE, Updated=now),
        ]
        mock_api_worker.get_adjusted_days.return_value = tempo_days
        
        sensor = CurrentColor("test_config_id", mock_api_worker, False)
        
        with patch('custom_components.rtetempo.sensor.datetime') as mock_datetime:
            mock_datetime.datetime.now.return_value = now
            sensor.update()
        
        assert sensor._attr_available is False
        assert sensor._attr_native_value is None


# ============================================================================
# Tests for NextColor (Requirements 14.1-14.4)
# ============================================================================

class TestNextColor:
    """Tests for NextColor sensor."""

    def test_init_visual_false(self, mock_api_worker):
        """Test NextColor initialization with visual=False."""
        sensor = NextColor("test_config_id", mock_api_worker, False)
        
        assert sensor._attr_name == "Prochaine couleur"
        assert sensor._attr_unique_id == f"{DOMAIN}_test_config_id_next_color"

    def test_init_visual_true(self, mock_api_worker):
        """Test NextColor initialization with visual=True."""
        sensor = NextColor("test_config_id", mock_api_worker, True)
        
        assert sensor._attr_name == "Prochaine couleur (visuel)"
        assert sensor._attr_unique_id == f"{DOMAIN}_test_config_id_next_color_emoji"

    def test_update_with_future_day(self, mock_api_worker):
        """Test update when a future tempo_day exists."""
        now = datetime.datetime.now(FRANCE_TZ)
        
        # Create tempo day in the future
        future_dt = now + datetime.timedelta(days=1)
        future_dt = future_dt.replace(hour=6, minute=0, second=0, microsecond=0)
        
        tempo_days = [
            TempoDay(Start=future_dt, End=future_dt + datetime.timedelta(days=1), Value=API_VALUE_RED, Updated=now),
        ]
        mock_api_worker.get_adjusted_days.return_value = tempo_days
        
        sensor = NextColor("test_config_id", mock_api_worker, False)
        
        with patch('custom_components.rtetempo.sensor.datetime') as mock_datetime:
            mock_datetime.datetime.now.return_value = now
            sensor.update()
        
        assert sensor._attr_available is True
        assert sensor._attr_native_value == SENSOR_COLOR_RED_NAME

    def test_update_no_future_day_visual_true(self, mock_api_worker):
        """Test update when no future tempo_day exists (visual=True shows unknown emoji)."""
        now = datetime.datetime.now(FRANCE_TZ)
        
        # Create tempo day in the past
        past_dt = datetime.datetime(2020, 1, 1, 6, 0, 0, tzinfo=FRANCE_TZ)
        tempo_days = [
            TempoDay(Start=past_dt, End=past_dt + datetime.timedelta(days=1), Value=API_VALUE_BLUE, Updated=now),
        ]
        mock_api_worker.get_adjusted_days.return_value = tempo_days
        
        sensor = NextColor("test_config_id", mock_api_worker, True)
        
        with patch('custom_components.rtetempo.sensor.datetime') as mock_datetime:
            mock_datetime.datetime.now.return_value = now
            sensor.update()
        
        # Visual mode shows unknown emoji when no future day
        assert sensor._attr_available is True
        assert sensor._attr_native_value == SENSOR_COLOR_UNKNOWN_EMOJI

    def test_update_no_future_day_visual_false(self, mock_api_worker):
        """Test update when no future tempo_day exists (visual=False is unavailable)."""
        now = datetime.datetime.now(FRANCE_TZ)
        
        # Create tempo day in the past
        past_dt = datetime.datetime(2020, 1, 1, 6, 0, 0, tzinfo=FRANCE_TZ)
        tempo_days = [
            TempoDay(Start=past_dt, End=past_dt + datetime.timedelta(days=1), Value=API_VALUE_BLUE, Updated=now),
        ]
        mock_api_worker.get_adjusted_days.return_value = tempo_days
        
        sensor = NextColor("test_config_id", mock_api_worker, False)
        
        with patch('custom_components.rtetempo.sensor.datetime') as mock_datetime:
            mock_datetime.datetime.now.return_value = now
            sensor.update()
        
        # Non-visual mode is unavailable when no future day
        assert sensor._attr_available is False
        assert sensor._attr_native_value is None


# ============================================================================
# Property Test for NextColorTime (Property 4)
# ============================================================================

class TestProperty4NextColorTime:
    """Property test for NextColorTime calculation."""

    # Feature: remaining-test-coverage, Property 4: Next Color Time Calculation
    @given(st.integers(min_value=0, max_value=23))
    @settings(max_examples=100)
    def test_next_color_time_calculation(self, hour):
        """For any hour, NextColorTime returns the next 6h boundary."""
        sensor = NextColorTime("test_config_id")
        
        mock_now = datetime.datetime(2025, 1, 15, hour, 30, 0, tzinfo=FRANCE_TZ)
        
        with patch('custom_components.rtetempo.sensor.datetime') as mock_datetime:
            mock_datetime.datetime.now.return_value = mock_now
            mock_datetime.datetime.side_effect = datetime.datetime
            mock_datetime.timedelta = datetime.timedelta
            sensor.update()
        
        result = sensor._attr_native_value
        
        # Should be at HOUR_OF_CHANGE (6h)
        assert result.hour == HOUR_OF_CHANGE
        assert result.minute == 0
        
        # Should be today if before 6h, tomorrow if after
        if hour >= HOUR_OF_CHANGE:
            assert result.day == mock_now.day + 1 or (result.day == 1 and mock_now.day >= 28)
        else:
            assert result.day == mock_now.day


# ============================================================================
# Property Test for NextCycleTime (Property 5)
# ============================================================================

class TestProperty5NextCycleTime:
    """Property test for NextCycleTime calculation."""

    # Feature: remaining-test-coverage, Property 5: Next Cycle Time Calculation
    @given(
        st.integers(min_value=1, max_value=12),
        st.integers(min_value=1, max_value=28),
    )
    @settings(max_examples=100)
    def test_next_cycle_time_calculation(self, month, day):
        """For any date, NextCycleTime returns the next September 1st."""
        sensor = NextCycleTime("test_config_id")
        
        mock_now = datetime.datetime(2025, month, day, 12, 0, 0, tzinfo=FRANCE_TZ)
        
        with patch('custom_components.rtetempo.sensor.datetime') as mock_datetime:
            mock_datetime.datetime.now.return_value = mock_now
            mock_datetime.datetime.side_effect = datetime.datetime
            sensor.update()
        
        result = sensor._attr_native_value
        
        # Should be September 1st
        assert result.month == CYCLE_START_MONTH
        assert result.day == CYCLE_START_DAY
        assert result.hour == HOUR_OF_CHANGE
        
        # Should be this year if before Sept 1, next year if after
        if month > CYCLE_START_MONTH or (month == CYCLE_START_MONTH and day >= CYCLE_START_DAY):
            assert result.year == mock_now.year + 1
        else:
            assert result.year == mock_now.year


# ============================================================================
# Property Test for OffPeakChangeTime (Property 6)
# ============================================================================

class TestProperty6OffPeakChangeTime:
    """Property test for OffPeakChangeTime calculation."""

    # Feature: remaining-test-coverage, Property 6: Off-Peak Change Time Calculation
    @given(st.integers(min_value=0, max_value=23))
    @settings(max_examples=100)
    def test_off_peak_change_time_calculation(self, hour):
        """For any hour, OffPeakChangeTime returns the next transition (6h or 22h)."""
        sensor = OffPeakChangeTime("test_config_id")
        
        mock_now = datetime.datetime(2025, 1, 15, hour, 30, 0, tzinfo=FRANCE_TZ)
        
        with patch('custom_components.rtetempo.sensor.datetime') as mock_datetime:
            mock_datetime.datetime.now.return_value = mock_now
            mock_datetime.datetime.side_effect = datetime.datetime
            mock_datetime.timedelta = datetime.timedelta
            sensor.update()
        
        result = sensor._attr_native_value
        
        # Determine expected next transition
        if hour < HOUR_OF_CHANGE:
            # Before 6h -> next is 6h today
            assert result.hour == HOUR_OF_CHANGE
            assert result.day == mock_now.day
        elif hour < OFF_PEAK_START:
            # Between 6h and 22h -> next is 22h today
            assert result.hour == OFF_PEAK_START
            assert result.day == mock_now.day
        else:
            # After 22h -> next is 6h tomorrow
            assert result.hour == HOUR_OF_CHANGE
            assert result.day == mock_now.day + 1 or (result.day == 1 and mock_now.day >= 28)


# ============================================================================
# Tests for DaysLeft and DaysUsed (Requirements 16.1-16.4)
# ============================================================================

class TestDaysLeftAndUsed:
    """Tests for DaysLeft and DaysUsed sensors."""

    def test_days_left_init_blue(self, mock_api_worker):
        """Test DaysLeft initialization for BLUE."""
        sensor = DaysLeft("test_config_id", mock_api_worker, API_VALUE_BLUE)
        assert "Bleu" in sensor._attr_name
        assert sensor._attr_unique_id == f"{DOMAIN}_test_config_id_days_left_blue"

    def test_days_left_init_white(self, mock_api_worker):
        """Test DaysLeft initialization for WHITE."""
        sensor = DaysLeft("test_config_id", mock_api_worker, API_VALUE_WHITE)
        assert "Blanc" in sensor._attr_name
        assert sensor._attr_unique_id == f"{DOMAIN}_test_config_id_days_left_white"

    def test_days_left_init_red(self, mock_api_worker):
        """Test DaysLeft initialization for RED."""
        sensor = DaysLeft("test_config_id", mock_api_worker, API_VALUE_RED)
        assert sensor._attr_unique_id == f"{DOMAIN}_test_config_id_days_left_red"

    def test_days_left_init_invalid_color(self, mock_api_worker):
        """Test DaysLeft initialization with invalid color raises exception."""
        with pytest.raises(Exception) as exc_info:
            DaysLeft("test_config_id", mock_api_worker, "INVALID")
        assert "invalid color" in str(exc_info.value)

    def test_days_used_init_blue(self, mock_api_worker):
        """Test DaysUsed initialization for BLUE."""
        sensor = DaysUsed("test_config_id", mock_api_worker, API_VALUE_BLUE)
        assert "Bleu" in sensor._attr_name
        assert sensor._attr_unique_id == f"{DOMAIN}_test_config_id_days_used_blue"

    def test_days_left_update(self, mock_api_worker):
        """Test DaysLeft update computes remaining days."""
        now = datetime.datetime.now(FRANCE_TZ)
        
        # Create some tempo days in current cycle
        tempo_days = [
            TempoDay(Start=datetime.date(2025, 1, 15), End=datetime.date(2025, 1, 16), Value=API_VALUE_BLUE, Updated=now),
            TempoDay(Start=datetime.date(2025, 1, 14), End=datetime.date(2025, 1, 15), Value=API_VALUE_WHITE, Updated=now),
            TempoDay(Start=datetime.date(2025, 1, 13), End=datetime.date(2025, 1, 14), Value=API_VALUE_RED, Updated=now),
        ]
        mock_api_worker.get_regular_days.return_value = tempo_days
        
        sensor = DaysLeft("test_config_id", mock_api_worker, API_VALUE_RED)
        
        # Mock datetime to be in January 2025 (within cycle starting Sept 2024)
        mock_now = datetime.datetime(2025, 1, 15, 12, 0, 0, tzinfo=FRANCE_TZ)
        with patch('custom_components.rtetempo.sensor.datetime') as mock_datetime:
            mock_datetime.datetime.now.return_value = mock_now
            mock_datetime.date = datetime.date
            sensor.update()
        
        # Should have computed remaining red days (22 total - 1 used = 21)
        assert sensor._attr_native_value is not None
        assert isinstance(sensor._attr_native_value, int)

    def test_days_used_update(self, mock_api_worker):
        """Test DaysUsed update computes used days."""
        now = datetime.datetime.now(FRANCE_TZ)
        
        # Create some tempo days in current cycle
        tempo_days = [
            TempoDay(Start=datetime.date(2025, 1, 15), End=datetime.date(2025, 1, 16), Value=API_VALUE_BLUE, Updated=now),
            TempoDay(Start=datetime.date(2025, 1, 14), End=datetime.date(2025, 1, 15), Value=API_VALUE_BLUE, Updated=now),
            TempoDay(Start=datetime.date(2025, 1, 13), End=datetime.date(2025, 1, 14), Value=API_VALUE_WHITE, Updated=now),
        ]
        mock_api_worker.get_regular_days.return_value = tempo_days
        
        sensor = DaysUsed("test_config_id", mock_api_worker, API_VALUE_BLUE)
        
        mock_now = datetime.datetime(2025, 1, 15, 12, 0, 0, tzinfo=FRANCE_TZ)
        with patch('custom_components.rtetempo.sensor.datetime') as mock_datetime:
            mock_datetime.datetime.now.return_value = mock_now
            mock_datetime.date = datetime.date
            sensor.update()
        
        # Should have counted 2 blue days
        assert sensor._attr_native_value == 2

    def test_days_left_cycle_boundary_before_september(self, mock_api_worker):
        """Test DaysLeft handles cycle boundary correctly (before September)."""
        now = datetime.datetime.now(FRANCE_TZ)
        
        tempo_days = []
        mock_api_worker.get_regular_days.return_value = tempo_days
        
        sensor = DaysLeft("test_config_id", mock_api_worker, API_VALUE_BLUE)
        
        # Mock datetime to be in March (before September, so cycle started previous year)
        mock_now = datetime.datetime(2025, 3, 15, 12, 0, 0, tzinfo=FRANCE_TZ)
        with patch('custom_components.rtetempo.sensor.datetime') as mock_datetime:
            mock_datetime.datetime.now.return_value = mock_now
            mock_datetime.date = datetime.date
            sensor.update()
        
        # Should compute based on cycle starting Sept 2024
        assert sensor._attr_native_value is not None

    def test_days_left_cycle_boundary_after_september(self, mock_api_worker):
        """Test DaysLeft handles cycle boundary correctly (after September)."""
        now = datetime.datetime.now(FRANCE_TZ)
        
        tempo_days = []
        mock_api_worker.get_regular_days.return_value = tempo_days
        
        sensor = DaysLeft("test_config_id", mock_api_worker, API_VALUE_BLUE)
        
        # Mock datetime to be in October (after September, so cycle started this year)
        mock_now = datetime.datetime(2025, 10, 15, 12, 0, 0, tzinfo=FRANCE_TZ)
        with patch('custom_components.rtetempo.sensor.datetime') as mock_datetime:
            mock_datetime.datetime.now.return_value = mock_now
            mock_datetime.date = datetime.date
            sensor.update()
        
        # Should compute based on cycle starting Sept 2025
        assert sensor._attr_native_value is not None


# ============================================================================
# Tests for NextColorTime, NextCycleTime, OffPeakChangeTime unit tests
# ============================================================================

class TestTimeSensors:
    """Unit tests for time-based sensors."""

    def test_next_color_time_init(self):
        """Test NextColorTime initialization."""
        sensor = NextColorTime("test_config_id")
        assert sensor._attr_name == "Prochaine couleur (changement)"
        assert sensor._attr_unique_id == f"{DOMAIN}_test_config_id_next_color_change"

    def test_next_cycle_time_init(self):
        """Test NextCycleTime initialization."""
        sensor = NextCycleTime("test_config_id")
        assert sensor._attr_name == "Cycle Prochaine réinitialisation"
        assert sensor._attr_unique_id == f"{DOMAIN}_test_config_id_next_cycle_reinit"

    def test_off_peak_change_time_init(self):
        """Test OffPeakChangeTime initialization."""
        sensor = OffPeakChangeTime("test_config_id")
        assert sensor._attr_name == "Heures Creuses (changement)"
        assert sensor._attr_unique_id == f"{DOMAIN}_test_config_id_off_peak_change_time"

    def test_next_color_time_device_info(self):
        """Test NextColorTime device_info."""
        sensor = NextColorTime("test_config_id")
        device_info = sensor.device_info
        assert (DOMAIN, "test_config_id") in device_info["identifiers"]


# ============================================================================
# Additional tests for improved coverage
# ============================================================================

class TestCurrentColorNoMatch:
    """Additional tests for CurrentColor when no match is found."""

    def test_update_no_match_visual_true(self, mock_api_worker):
        """Test update when no tempo_day matches (visual=True resets icon)."""
        now = datetime.datetime.now(FRANCE_TZ)
        
        # Create tempo day in the past
        past_dt = datetime.datetime(2020, 1, 1, 6, 0, 0, tzinfo=FRANCE_TZ)
        tempo_days = [
            TempoDay(Start=past_dt, End=past_dt + datetime.timedelta(days=1), Value=API_VALUE_BLUE, Updated=now),
        ]
        mock_api_worker.get_adjusted_days.return_value = tempo_days
        
        sensor = CurrentColor("test_config_id", mock_api_worker, True)
        
        with patch('custom_components.rtetempo.sensor.datetime') as mock_datetime:
            mock_datetime.datetime.now.return_value = now
            sensor.update()
        
        assert sensor._attr_available is False
        assert sensor._attr_native_value is None
        assert sensor._attr_icon == "mdi:palette"


class TestNextColorDeviceInfo:
    """Tests for NextColor device_info."""

    def test_device_info(self, mock_api_worker):
        """Test NextColor device_info property."""
        sensor = NextColor("test_config_id", mock_api_worker, False)
        device_info = sensor.device_info
        
        assert (DOMAIN, "test_config_id") in device_info["identifiers"]
        assert device_info["name"] == DEVICE_NAME
        assert device_info["manufacturer"] == DEVICE_MANUFACTURER
        assert device_info["model"] == DEVICE_MODEL


class TestNextColorVisualUpdate:
    """Additional tests for NextColor visual mode."""

    def test_update_with_future_day_visual_true(self, mock_api_worker):
        """Test update when a future tempo_day exists (visual=True)."""
        now = datetime.datetime.now(FRANCE_TZ)
        
        # Create tempo day in the future
        future_dt = now + datetime.timedelta(days=1)
        future_dt = future_dt.replace(hour=6, minute=0, second=0, microsecond=0)
        
        tempo_days = [
            TempoDay(Start=future_dt, End=future_dt + datetime.timedelta(days=1), Value=API_VALUE_WHITE, Updated=now),
        ]
        mock_api_worker.get_adjusted_days.return_value = tempo_days
        
        sensor = NextColor("test_config_id", mock_api_worker, True)
        
        with patch('custom_components.rtetempo.sensor.datetime') as mock_datetime:
            mock_datetime.datetime.now.return_value = now
            sensor.update()
        
        assert sensor._attr_available is True
        assert sensor._attr_native_value == SENSOR_COLOR_WHITE_EMOJI
        assert sensor._attr_icon == "mdi:information-outline"


class TestDaysLeftDeviceInfo:
    """Tests for DaysLeft device_info."""

    def test_device_info(self, mock_api_worker):
        """Test DaysLeft device_info property."""
        sensor = DaysLeft("test_config_id", mock_api_worker, API_VALUE_BLUE)
        device_info = sensor.device_info
        
        assert (DOMAIN, "test_config_id") in device_info["identifiers"]
        assert device_info["name"] == DEVICE_NAME


class TestDaysUsedDeviceInfo:
    """Tests for DaysUsed device_info."""

    def test_device_info(self, mock_api_worker):
        """Test DaysUsed device_info property."""
        sensor = DaysUsed("test_config_id", mock_api_worker, API_VALUE_WHITE)
        device_info = sensor.device_info
        
        assert (DOMAIN, "test_config_id") in device_info["identifiers"]
        assert device_info["name"] == DEVICE_NAME


class TestDaysUsedInit:
    """Additional tests for DaysUsed initialization."""

    def test_days_used_init_white(self, mock_api_worker):
        """Test DaysUsed initialization for WHITE."""
        sensor = DaysUsed("test_config_id", mock_api_worker, API_VALUE_WHITE)
        assert "Blanc" in sensor._attr_name
        assert sensor._attr_unique_id == f"{DOMAIN}_test_config_id_days_used_white"

    def test_days_used_init_red(self, mock_api_worker):
        """Test DaysUsed initialization for RED."""
        sensor = DaysUsed("test_config_id", mock_api_worker, API_VALUE_RED)
        assert sensor._attr_unique_id == f"{DOMAIN}_test_config_id_days_used_red"

    def test_days_used_init_invalid_color(self, mock_api_worker):
        """Test DaysUsed initialization with invalid color raises exception."""
        with pytest.raises(Exception) as exc_info:
            DaysUsed("test_config_id", mock_api_worker, "INVALID")
        assert "invalid color" in str(exc_info.value)


class TestDaysLeftUpdateInvalidColor:
    """Tests for DaysLeft update with invalid color in data."""

    def test_days_left_update_invalid_color_in_data(self, mock_api_worker):
        """Test DaysLeft update raises exception for invalid color in tempo data."""
        now = datetime.datetime.now(FRANCE_TZ)
        
        # Create tempo day with invalid color
        tempo_days = [
            TempoDay(Start=datetime.date(2025, 1, 15), End=datetime.date(2025, 1, 16), Value="INVALID", Updated=now),
        ]
        mock_api_worker.get_regular_days.return_value = tempo_days
        
        sensor = DaysLeft("test_config_id", mock_api_worker, API_VALUE_BLUE)
        
        mock_now = datetime.datetime(2025, 1, 15, 12, 0, 0, tzinfo=FRANCE_TZ)
        with patch('custom_components.rtetempo.sensor.datetime') as mock_datetime:
            mock_datetime.datetime.now.return_value = mock_now
            mock_datetime.date = datetime.date
            with pytest.raises(Exception) as exc_info:
                sensor.update()
        
        assert "invalid color" in str(exc_info.value)


class TestDaysUsedUpdateInvalidColor:
    """Tests for DaysUsed update with invalid color in data."""

    def test_days_used_update_invalid_color_in_data(self, mock_api_worker):
        """Test DaysUsed update raises exception for invalid color in tempo data."""
        now = datetime.datetime.now(FRANCE_TZ)
        
        # Create tempo day with invalid color
        tempo_days = [
            TempoDay(Start=datetime.date(2025, 1, 15), End=datetime.date(2025, 1, 16), Value="INVALID", Updated=now),
        ]
        mock_api_worker.get_regular_days.return_value = tempo_days
        
        sensor = DaysUsed("test_config_id", mock_api_worker, API_VALUE_BLUE)
        
        mock_now = datetime.datetime(2025, 1, 15, 12, 0, 0, tzinfo=FRANCE_TZ)
        with patch('custom_components.rtetempo.sensor.datetime') as mock_datetime:
            mock_datetime.datetime.now.return_value = mock_now
            mock_datetime.date = datetime.date
            with pytest.raises(Exception) as exc_info:
                sensor.update()
        
        assert "invalid color" in str(exc_info.value)


class TestDaysLeftUpdateInvalidSensorColor:
    """Tests for DaysLeft update with invalid sensor color."""

    def test_days_left_update_invalid_sensor_color(self, mock_api_worker):
        """Test DaysLeft update raises exception for invalid sensor color."""
        now = datetime.datetime.now(FRANCE_TZ)
        
        tempo_days = []
        mock_api_worker.get_regular_days.return_value = tempo_days
        
        # Create sensor with valid color, then change it to invalid
        sensor = DaysLeft("test_config_id", mock_api_worker, API_VALUE_BLUE)
        sensor._color = "INVALID"  # Manually set invalid color
        
        mock_now = datetime.datetime(2025, 1, 15, 12, 0, 0, tzinfo=FRANCE_TZ)
        with patch('custom_components.rtetempo.sensor.datetime') as mock_datetime:
            mock_datetime.datetime.now.return_value = mock_now
            mock_datetime.date = datetime.date
            with pytest.raises(Exception) as exc_info:
                sensor.update()
        
        assert "invalid color" in str(exc_info.value)


class TestDaysUsedUpdateInvalidSensorColor:
    """Tests for DaysUsed update with invalid sensor color."""

    def test_days_used_update_invalid_sensor_color(self, mock_api_worker):
        """Test DaysUsed update raises exception for invalid sensor color."""
        now = datetime.datetime.now(FRANCE_TZ)
        
        tempo_days = []
        mock_api_worker.get_regular_days.return_value = tempo_days
        
        # Create sensor with valid color, then change it to invalid
        sensor = DaysUsed("test_config_id", mock_api_worker, API_VALUE_BLUE)
        sensor._color = "INVALID"  # Manually set invalid color
        
        mock_now = datetime.datetime(2025, 1, 15, 12, 0, 0, tzinfo=FRANCE_TZ)
        with patch('custom_components.rtetempo.sensor.datetime') as mock_datetime:
            mock_datetime.datetime.now.return_value = mock_now
            mock_datetime.date = datetime.date
            with pytest.raises(Exception) as exc_info:
                sensor.update()
        
        assert "invalid color" in str(exc_info.value)


class TestNextCycleTimeDeviceInfo:
    """Tests for NextCycleTime device_info."""

    def test_device_info(self):
        """Test NextCycleTime device_info property."""
        sensor = NextCycleTime("test_config_id")
        device_info = sensor.device_info
        
        assert (DOMAIN, "test_config_id") in device_info["identifiers"]
        assert device_info["name"] == DEVICE_NAME


class TestOffPeakChangeTimeDeviceInfo:
    """Tests for OffPeakChangeTime device_info."""

    def test_device_info(self):
        """Test OffPeakChangeTime device_info property."""
        sensor = OffPeakChangeTime("test_config_id")
        device_info = sensor.device_info
        
        assert (DOMAIN, "test_config_id") in device_info["identifiers"]
        assert device_info["name"] == DEVICE_NAME
