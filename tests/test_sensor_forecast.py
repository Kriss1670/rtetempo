"""Tests for sensor_forecast.py module.

Tests cover helper functions, sensor availability, state updates, and attributes.
"""
from __future__ import annotations

import datetime
from typing import Optional, List
from unittest.mock import MagicMock

import pytest

# Import real modules for coverage
from custom_components.rtetempo.forecast import ForecastDay
from custom_components.rtetempo.sensor_forecast import (
    get_color_emoji,
    get_color_name,
    get_color_icon,
)
from custom_components.rtetempo.const import (
    DOMAIN,
    DEVICE_MANUFACTURER,
    DEVICE_MODEL,
    SENSOR_COLOR_BLUE_NAME,
    SENSOR_COLOR_BLUE_EMOJI,
    SENSOR_COLOR_WHITE_NAME,
    SENSOR_COLOR_WHITE_EMOJI,
    SENSOR_COLOR_RED_NAME,
    SENSOR_COLOR_RED_EMOJI,
    SENSOR_COLOR_UNKNOWN_NAME,
    SENSOR_COLOR_UNKNOWN_EMOJI,
)


# ============================================================================
# Mock Coordinator
# ============================================================================

class MockCoordinator:
    """Mock ForecastCoordinator for testing."""
    
    def __init__(self, data: List[ForecastDay] = None):
        self.data = data
        self._listeners = {}
    
    def async_add_listener(self, callback):
        """Add a listener."""
        pass


# ============================================================================
# Real Sensor with mocked HA dependencies
# ============================================================================

# We'll use the real OpenDPEForecastSensor class with mocked HA dependencies
# to get proper coverage on the sensor_forecast.py module

from unittest.mock import patch

# Mock the HA base classes before importing the sensor
with patch('custom_components.rtetempo.sensor_forecast.CoordinatorEntity'):
    with patch('custom_components.rtetempo.sensor_forecast.SensorEntity'):
        # Import after mocking
        pass


# For tests that need the mock sensor behavior, we keep a simplified version
class MockOpenDPEForecastSensor:
    """Simplified sensor for testing (mirrors real sensor behavior)."""
    
    def __init__(self, coordinator: MockCoordinator, index: int, visual: bool):
        self.coordinator = coordinator
        self.index = index
        self.visual = visual
        
        if visual:
            self._attr_name = f"OpenDPE J{index + 1} (visuel)"
            self._attr_unique_id = f"{DOMAIN}_forecast_opendpe_j{index + 1}_emoji"
            self._attr_options = [
                SENSOR_COLOR_BLUE_EMOJI,
                SENSOR_COLOR_WHITE_EMOJI,
                SENSOR_COLOR_RED_EMOJI,
                SENSOR_COLOR_UNKNOWN_EMOJI,
            ]
            self._attr_icon = "mdi:palette"
        else:
            self._attr_name = f"OpenDPE J{index + 1}"
            self._attr_unique_id = f"{DOMAIN}_forecast_opendpe_j{index + 1}"
            self._attr_options = [
                SENSOR_COLOR_BLUE_NAME,
                SENSOR_COLOR_WHITE_NAME,
                SENSOR_COLOR_RED_NAME,
                SENSOR_COLOR_UNKNOWN_NAME,
            ]
            self._attr_icon = "mdi:calendar"
        
        self._attr_native_value: Optional[str] = None
        self._attr_extra_state_attributes = {}
    
    @property
    def available(self) -> bool:
        """Return if sensor is available."""
        data = self.coordinator.data
        return data is not None and len(data) > self.index
    
    def _handle_coordinator_update(self) -> None:
        """Handle coordinator data update."""
        data = self.coordinator.data
        
        if not data or len(data) <= self.index:
            self._attr_native_value = None
            self._attr_extra_state_attributes = {}
            return
        
        forecast: ForecastDay = data[self.index]
        color = forecast.color.lower()
        
        if color not in ["bleu", "blanc", "rouge"]:
            color = "inconnu"
        
        if self.visual:
            self._attr_native_value = get_color_emoji(color)
            self._attr_icon = get_color_icon(color)
        else:
            self._attr_native_value = get_color_name(color)
        
        if forecast.indicator:
            self._attr_extra_state_attributes = {
                "date": forecast.date.isoformat(),
                "indicator": forecast.indicator,
                "attribution": "Données Tempo : Open DPE (https://open-dpe.fr)",
            }
        else:
            self._attr_extra_state_attributes = {
                "date": forecast.date.isoformat(),
                "probability": forecast.probability,
                "attribution": "Données Tempo : Open DPE (https://open-dpe.fr)",
            }


# ============================================================================
# Tests: Helper Functions
# ============================================================================

class TestColorHelperFunctions:
    """Tests for color helper functions. Validates: Requirements 7.1-7.4"""
    
    # --- get_color_emoji tests ---
    
    def test_get_color_emoji_bleu(self):
        """Test emoji for bleu. Validates: Requirement 7.1"""
        assert get_color_emoji("bleu") == "🔵"
    
    def test_get_color_emoji_blanc(self):
        """Test emoji for blanc. Validates: Requirement 7.1"""
        assert get_color_emoji("blanc") == "⚪"
    
    def test_get_color_emoji_rouge(self):
        """Test emoji for rouge. Validates: Requirement 7.1"""
        assert get_color_emoji("rouge") == "🔴"
    
    def test_get_color_emoji_unknown(self):
        """Test emoji for unknown color. Validates: Requirement 7.4"""
        assert get_color_emoji("invalid") == "❓"
        assert get_color_emoji("") == "❓"
        assert get_color_emoji("BLEU") == "❓"  # Case sensitive
    
    # --- get_color_name tests ---
    
    def test_get_color_name_bleu(self):
        """Test name for bleu. Validates: Requirement 7.2"""
        assert get_color_name("bleu") == "Bleu"
    
    def test_get_color_name_blanc(self):
        """Test name for blanc. Validates: Requirement 7.2"""
        assert get_color_name("blanc") == "Blanc"
    
    def test_get_color_name_rouge(self):
        """Test name for rouge. Validates: Requirement 7.2"""
        assert get_color_name("rouge") == "Rouge"
    
    def test_get_color_name_unknown(self):
        """Test name for unknown color. Validates: Requirement 7.4"""
        assert get_color_name("invalid") == "inconnu"
        assert get_color_name("") == "inconnu"
    
    # --- get_color_icon tests ---
    
    def test_get_color_icon_bleu(self):
        """Test icon for bleu. Validates: Requirement 7.3"""
        assert get_color_icon("bleu") == "mdi:check-bold"
    
    def test_get_color_icon_blanc(self):
        """Test icon for blanc. Validates: Requirement 7.3"""
        assert get_color_icon("blanc") == "mdi:information-outline"
    
    def test_get_color_icon_rouge(self):
        """Test icon for rouge. Validates: Requirement 7.3"""
        assert get_color_icon("rouge") == "mdi:alert"
    
    def test_get_color_icon_unknown(self):
        """Test icon for unknown color. Validates: Requirement 7.4"""
        assert get_color_icon("invalid") == "mdi:palette"
        assert get_color_icon("") == "mdi:palette"


# ============================================================================
# Tests: Sensor Availability
# ============================================================================

class TestSensorAvailability:
    """Tests for sensor availability. Validates: Requirements 5.1-5.3"""
    
    def test_unavailable_when_data_is_none(self):
        """Test sensor unavailable when data is None. Validates: Requirement 5.1"""
        coordinator = MockCoordinator(data=None)
        sensor = MockOpenDPEForecastSensor(coordinator, index=0, visual=False)
        
        assert sensor.available is False
    
    def test_unavailable_when_index_exceeds_data(self):
        """Test sensor unavailable when index > len(data). Validates: Requirement 5.2"""
        forecasts = [
            ForecastDay(date=datetime.date(2025, 1, 15), color="bleu", probability=0.85)
        ]
        coordinator = MockCoordinator(data=forecasts)
        sensor = MockOpenDPEForecastSensor(coordinator, index=5, visual=False)
        
        assert sensor.available is False
    
    def test_available_when_data_sufficient(self):
        """Test sensor available when data is sufficient. Validates: Requirement 5.3"""
        forecasts = [
            ForecastDay(date=datetime.date(2025, 1, 15), color="bleu", probability=0.85),
            ForecastDay(date=datetime.date(2025, 1, 16), color="blanc", probability=0.72),
        ]
        coordinator = MockCoordinator(data=forecasts)
        sensor = MockOpenDPEForecastSensor(coordinator, index=1, visual=False)
        
        assert sensor.available is True
    
    def test_available_with_empty_list(self):
        """Test sensor unavailable with empty list."""
        coordinator = MockCoordinator(data=[])
        sensor = MockOpenDPEForecastSensor(coordinator, index=0, visual=False)
        
        assert sensor.available is False


# ============================================================================
# Tests: Sensor State Update
# ============================================================================

class TestSensorStateUpdate:
    """Tests for sensor state updates. Validates: Requirements 4.1-4.5, 5.4"""
    
    def test_update_with_bleu_text(self):
        """Test update with bleu color (text). Validates: Requirement 4.1"""
        forecasts = [
            ForecastDay(date=datetime.date(2025, 1, 15), color="bleu", probability=0.85)
        ]
        coordinator = MockCoordinator(data=forecasts)
        sensor = MockOpenDPEForecastSensor(coordinator, index=0, visual=False)
        
        sensor._handle_coordinator_update()
        
        assert sensor._attr_native_value == "Bleu"
    
    def test_update_with_bleu_visual(self):
        """Test update with bleu color (visual). Validates: Requirement 4.1"""
        forecasts = [
            ForecastDay(date=datetime.date(2025, 1, 15), color="bleu", probability=0.85)
        ]
        coordinator = MockCoordinator(data=forecasts)
        sensor = MockOpenDPEForecastSensor(coordinator, index=0, visual=True)
        
        sensor._handle_coordinator_update()
        
        assert sensor._attr_native_value == "🔵"
        assert sensor._attr_icon == "mdi:check-bold"
    
    def test_update_with_blanc_text(self):
        """Test update with blanc color (text). Validates: Requirement 4.2"""
        forecasts = [
            ForecastDay(date=datetime.date(2025, 1, 15), color="blanc", probability=0.72)
        ]
        coordinator = MockCoordinator(data=forecasts)
        sensor = MockOpenDPEForecastSensor(coordinator, index=0, visual=False)
        
        sensor._handle_coordinator_update()
        
        assert sensor._attr_native_value == "Blanc"
    
    def test_update_with_blanc_visual(self):
        """Test update with blanc color (visual). Validates: Requirement 4.2"""
        forecasts = [
            ForecastDay(date=datetime.date(2025, 1, 15), color="blanc", probability=0.72)
        ]
        coordinator = MockCoordinator(data=forecasts)
        sensor = MockOpenDPEForecastSensor(coordinator, index=0, visual=True)
        
        sensor._handle_coordinator_update()
        
        assert sensor._attr_native_value == "⚪"
        assert sensor._attr_icon == "mdi:information-outline"
    
    def test_update_with_rouge_text(self):
        """Test update with rouge color (text). Validates: Requirement 4.3"""
        forecasts = [
            ForecastDay(date=datetime.date(2025, 1, 15), color="rouge", probability=0.45)
        ]
        coordinator = MockCoordinator(data=forecasts)
        sensor = MockOpenDPEForecastSensor(coordinator, index=0, visual=False)
        
        sensor._handle_coordinator_update()
        
        assert sensor._attr_native_value == "Rouge"
    
    def test_update_with_rouge_visual(self):
        """Test update with rouge color (visual). Validates: Requirement 4.3"""
        forecasts = [
            ForecastDay(date=datetime.date(2025, 1, 15), color="rouge", probability=0.45)
        ]
        coordinator = MockCoordinator(data=forecasts)
        sensor = MockOpenDPEForecastSensor(coordinator, index=0, visual=True)
        
        sensor._handle_coordinator_update()
        
        assert sensor._attr_native_value == "🔴"
        assert sensor._attr_icon == "mdi:alert"
    
    def test_update_with_unknown_color(self):
        """Test update with unknown color. Validates: Requirement 4.4"""
        forecasts = [
            ForecastDay(date=datetime.date(2025, 1, 15), color="invalid", probability=0.5)
        ]
        coordinator = MockCoordinator(data=forecasts)
        sensor_text = MockOpenDPEForecastSensor(coordinator, index=0, visual=False)
        sensor_visual = MockOpenDPEForecastSensor(coordinator, index=0, visual=True)
        
        sensor_text._handle_coordinator_update()
        sensor_visual._handle_coordinator_update()
        
        assert sensor_text._attr_native_value == "inconnu"
        assert sensor_visual._attr_native_value == "❓"
    
    def test_update_with_indicator_d(self):
        """Test update with indicator D (Sunday). Validates: Requirement 4.5"""
        forecasts = [
            ForecastDay(
                date=datetime.date(2025, 1, 19),  # Sunday
                color="bleu",
                probability=None,
                indicator="D"
            )
        ]
        coordinator = MockCoordinator(data=forecasts)
        sensor = MockOpenDPEForecastSensor(coordinator, index=0, visual=False)
        
        sensor._handle_coordinator_update()
        
        assert sensor._attr_extra_state_attributes["indicator"] == "D"
        assert "probability" not in sensor._attr_extra_state_attributes
    
    def test_update_with_indicator_f(self):
        """Test update with indicator F (Holiday). Validates: Requirement 4.5"""
        forecasts = [
            ForecastDay(
                date=datetime.date(2025, 1, 1),  # New Year
                color="bleu",
                probability=None,
                indicator="F"
            )
        ]
        coordinator = MockCoordinator(data=forecasts)
        sensor = MockOpenDPEForecastSensor(coordinator, index=0, visual=False)
        
        sensor._handle_coordinator_update()
        
        assert sensor._attr_extra_state_attributes["indicator"] == "F"
        assert "probability" not in sensor._attr_extra_state_attributes
    
    def test_update_clears_state_when_no_data(self):
        """Test update clears state when no data. Validates: Requirement 5.4"""
        coordinator = MockCoordinator(data=None)
        sensor = MockOpenDPEForecastSensor(coordinator, index=0, visual=False)
        
        sensor._handle_coordinator_update()
        
        assert sensor._attr_native_value is None
        assert sensor._attr_extra_state_attributes == {}


# ============================================================================
# Tests: Sensor Attributes
# ============================================================================

class TestSensorAttributes:
    """Tests for sensor extra state attributes. Validates: Requirements 6.1-6.4"""
    
    def test_attributes_include_date(self):
        """Test attributes include date in ISO format. Validates: Requirement 6.1"""
        forecasts = [
            ForecastDay(date=datetime.date(2025, 1, 15), color="bleu", probability=0.85)
        ]
        coordinator = MockCoordinator(data=forecasts)
        sensor = MockOpenDPEForecastSensor(coordinator, index=0, visual=False)
        
        sensor._handle_coordinator_update()
        
        assert "date" in sensor._attr_extra_state_attributes
        assert sensor._attr_extra_state_attributes["date"] == "2025-01-15"
    
    def test_attributes_include_probability(self):
        """Test attributes include probability when no indicator. Validates: Requirement 6.2"""
        forecasts = [
            ForecastDay(date=datetime.date(2025, 1, 15), color="bleu", probability=0.85)
        ]
        coordinator = MockCoordinator(data=forecasts)
        sensor = MockOpenDPEForecastSensor(coordinator, index=0, visual=False)
        
        sensor._handle_coordinator_update()
        
        assert "probability" in sensor._attr_extra_state_attributes
        assert sensor._attr_extra_state_attributes["probability"] == 0.85
    
    def test_attributes_include_indicator_instead_of_probability(self):
        """Test attributes include indicator instead of probability. Validates: Requirement 6.3"""
        forecasts = [
            ForecastDay(
                date=datetime.date(2025, 1, 19),
                color="bleu",
                probability=None,
                indicator="D"
            )
        ]
        coordinator = MockCoordinator(data=forecasts)
        sensor = MockOpenDPEForecastSensor(coordinator, index=0, visual=False)
        
        sensor._handle_coordinator_update()
        
        assert "indicator" in sensor._attr_extra_state_attributes
        assert "probability" not in sensor._attr_extra_state_attributes
    
    def test_attributes_always_include_attribution(self):
        """Test attributes always include attribution. Validates: Requirement 6.4"""
        forecasts = [
            ForecastDay(date=datetime.date(2025, 1, 15), color="bleu", probability=0.85)
        ]
        coordinator = MockCoordinator(data=forecasts)
        sensor = MockOpenDPEForecastSensor(coordinator, index=0, visual=False)
        
        sensor._handle_coordinator_update()
        
        assert "attribution" in sensor._attr_extra_state_attributes
        assert "Open DPE" in sensor._attr_extra_state_attributes["attribution"]
    
    def test_attributes_with_none_probability(self):
        """Test attributes with None probability (no indicator)."""
        forecasts = [
            ForecastDay(date=datetime.date(2025, 1, 15), color="bleu", probability=None)
        ]
        coordinator = MockCoordinator(data=forecasts)
        sensor = MockOpenDPEForecastSensor(coordinator, index=0, visual=False)
        
        sensor._handle_coordinator_update()
        
        assert "probability" in sensor._attr_extra_state_attributes
        assert sensor._attr_extra_state_attributes["probability"] is None


# ============================================================================
# Tests: Sensor Initialization
# ============================================================================

class TestSensorInitialization:
    """Tests for sensor initialization."""
    
    def test_text_sensor_initialization(self):
        """Test text sensor initialization."""
        coordinator = MockCoordinator(data=[])
        sensor = MockOpenDPEForecastSensor(coordinator, index=0, visual=False)
        
        assert sensor._attr_name == "OpenDPE J1"
        assert sensor._attr_unique_id == "rtetempo_forecast_opendpe_j1"
        assert sensor._attr_icon == "mdi:calendar"
        assert SENSOR_COLOR_BLUE_NAME in sensor._attr_options
    
    def test_visual_sensor_initialization(self):
        """Test visual sensor initialization."""
        coordinator = MockCoordinator(data=[])
        sensor = MockOpenDPEForecastSensor(coordinator, index=2, visual=True)
        
        assert sensor._attr_name == "OpenDPE J3 (visuel)"
        assert sensor._attr_unique_id == "rtetempo_forecast_opendpe_j3_emoji"
        assert sensor._attr_icon == "mdi:palette"
        assert SENSOR_COLOR_BLUE_EMOJI in sensor._attr_options


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


# ============================================================================
# Property-Based Tests
# ============================================================================

from hypothesis import given, settings, strategies as st


# Strategy for valid colors
valid_color_strategy = st.sampled_from(["bleu", "blanc", "rouge"])

# Strategy for dates
date_strategy = st.dates(
    min_value=datetime.date(2020, 1, 1),
    max_value=datetime.date(2030, 12, 31)
)

# Strategy for probability
probability_strategy = st.one_of(
    st.none(),
    st.floats(min_value=0.0, max_value=1.0, allow_nan=False)
)

# Strategy for indicator
indicator_strategy = st.one_of(
    st.none(),
    st.sampled_from(["D", "F"])
)

# Expected mappings
COLOR_TO_EMOJI = {
    "bleu": "🔵",
    "blanc": "⚪",
    "rouge": "🔴",
}

COLOR_TO_NAME = {
    "bleu": "Bleu",
    "blanc": "Blanc",
    "rouge": "Rouge",
}

COLOR_TO_ICON = {
    "bleu": "mdi:check-bold",
    "blanc": "mdi:information-outline",
    "rouge": "mdi:alert",
}


class TestProperty3ColorHelperFunctionsConsistency:
    """
    Property 3: Color Helper Functions Consistency
    
    *For any* valid color ("bleu", "blanc", "rouge"), the helper functions
    SHALL return consistent values:
    - get_color_emoji returns the corresponding emoji
    - get_color_name returns the corresponding French name
    - get_color_icon returns the corresponding MDI icon
    
    **Validates: Requirements 7.1, 7.2, 7.3**
    """
    
    @given(color=valid_color_strategy)
    @settings(max_examples=100)
    def test_color_helper_functions_consistency(self, color):
        """Feature: forecast-test-coverage, Property 3: Color Helper Functions Consistency"""
        # All three functions should return consistent, expected values
        emoji = get_color_emoji(color)
        name = get_color_name(color)
        icon = get_color_icon(color)
        
        # Verify emoji mapping
        assert emoji == COLOR_TO_EMOJI[color], f"Emoji mismatch for {color}"
        
        # Verify name mapping
        assert name == COLOR_TO_NAME[color], f"Name mismatch for {color}"
        
        # Verify icon mapping
        assert icon == COLOR_TO_ICON[color], f"Icon mismatch for {color}"
        
        # Verify consistency: all functions should handle the same color
        assert emoji != SENSOR_COLOR_UNKNOWN_EMOJI
        assert name != SENSOR_COLOR_UNKNOWN_NAME
        assert icon != "mdi:palette"


class TestProperty4SensorAvailabilityCorrectness:
    """
    Property 4: Sensor Availability Correctness
    
    *For any* coordinator state, the sensor availability SHALL be:
    - False if coordinator.data is None
    - False if len(coordinator.data) <= sensor.index
    - True otherwise
    
    **Validates: Requirements 5.1, 5.2, 5.3**
    """
    
    @given(
        num_forecasts=st.integers(min_value=0, max_value=10),
        sensor_index=st.integers(min_value=0, max_value=9),
    )
    @settings(max_examples=100)
    def test_sensor_availability_correctness(self, num_forecasts, sensor_index):
        """Feature: forecast-test-coverage, Property 4: Sensor Availability Correctness"""
        # Create forecasts
        forecasts = [
            ForecastDay(
                date=datetime.date(2025, 1, 15) + datetime.timedelta(days=i),
                color="bleu",
                probability=0.5,
            )
            for i in range(num_forecasts)
        ]
        
        coordinator = MockCoordinator(data=forecasts if num_forecasts > 0 else [])
        sensor = MockOpenDPEForecastSensor(coordinator, index=sensor_index, visual=False)
        
        # Verify availability logic
        expected_available = num_forecasts > sensor_index
        assert sensor.available == expected_available, \
            f"Expected available={expected_available} for {num_forecasts} forecasts and index {sensor_index}"
    
    @given(sensor_index=st.integers(min_value=0, max_value=9))
    @settings(max_examples=50)
    def test_sensor_unavailable_when_data_none(self, sensor_index):
        """Feature: forecast-test-coverage, Property 4: Sensor unavailable when data is None"""
        coordinator = MockCoordinator(data=None)
        sensor = MockOpenDPEForecastSensor(coordinator, index=sensor_index, visual=False)
        
        assert sensor.available is False


class TestProperty5SensorAttributesCompleteness:
    """
    Property 5: Sensor Attributes Completeness
    
    *For any* forecast update, the sensor extra_state_attributes SHALL always contain:
    - "date" with the forecast date in ISO format
    - "attribution" with the Open DPE attribution
    - Either "probability" or "indicator" (mutually exclusive)
    
    **Validates: Requirements 6.1, 6.2, 6.3, 6.4**
    """
    
    @given(
        date=date_strategy,
        color=valid_color_strategy,
        probability=probability_strategy,
        indicator=indicator_strategy,
        visual=st.booleans(),
    )
    @settings(max_examples=100)
    def test_sensor_attributes_completeness(self, date, color, probability, indicator, visual):
        """Feature: forecast-test-coverage, Property 5: Sensor Attributes Completeness"""
        forecast = ForecastDay(
            date=date,
            color=color,
            probability=probability,
            indicator=indicator,
        )
        
        coordinator = MockCoordinator(data=[forecast])
        sensor = MockOpenDPEForecastSensor(coordinator, index=0, visual=visual)
        
        sensor._handle_coordinator_update()
        
        attrs = sensor._attr_extra_state_attributes
        
        # Date should always be present in ISO format
        assert "date" in attrs, "date attribute missing"
        assert attrs["date"] == date.isoformat(), "date not in ISO format"
        
        # Attribution should always be present
        assert "attribution" in attrs, "attribution attribute missing"
        assert "Open DPE" in attrs["attribution"], "attribution should mention Open DPE"
        
        # Either probability or indicator, but not both
        if indicator:
            assert "indicator" in attrs, "indicator attribute missing when indicator is set"
            assert "probability" not in attrs, "probability should not be present when indicator is set"
            assert attrs["indicator"] == indicator
        else:
            assert "probability" in attrs, "probability attribute missing when no indicator"
            assert "indicator" not in attrs, "indicator should not be present when not set"
            assert attrs["probability"] == probability


# ============================================================================
# Tests: Real OpenDPEForecastSensor with mocked HA dependencies
# ============================================================================

class TestRealOpenDPEForecastSensor:
    """Tests using the real OpenDPEForecastSensor class with mocked HA dependencies."""
    
    @patch('custom_components.rtetempo.sensor_forecast.CoordinatorEntity.__init__', return_value=None)
    def test_real_sensor_text_initialization(self, mock_coordinator_entity):
        """Test real sensor initialization (text version)."""
        from custom_components.rtetempo.sensor_forecast import OpenDPEForecastSensor
        
        coordinator = MockCoordinator(data=[])
        sensor = OpenDPEForecastSensor(coordinator, index=0, visual=False)
        sensor.coordinator = coordinator  # Set coordinator manually since we mocked __init__
        
        assert sensor._attr_name == "OpenDPE J1"
        assert sensor._attr_unique_id == "rtetempo_forecast_opendpe_j1"
        assert sensor._attr_icon == "mdi:calendar"
        assert SENSOR_COLOR_BLUE_NAME in sensor._attr_options
    
    @patch('custom_components.rtetempo.sensor_forecast.CoordinatorEntity.__init__', return_value=None)
    def test_real_sensor_visual_initialization(self, mock_coordinator_entity):
        """Test real sensor initialization (visual version)."""
        from custom_components.rtetempo.sensor_forecast import OpenDPEForecastSensor
        
        coordinator = MockCoordinator(data=[])
        sensor = OpenDPEForecastSensor(coordinator, index=2, visual=True)
        sensor.coordinator = coordinator  # Set coordinator manually since we mocked __init__
        
        assert sensor._attr_name == "OpenDPE J3 (visuel)"
        assert sensor._attr_unique_id == "rtetempo_forecast_opendpe_j3_emoji"
        assert sensor._attr_icon == "mdi:palette"
        assert SENSOR_COLOR_BLUE_EMOJI in sensor._attr_options
    
    @patch('custom_components.rtetempo.sensor_forecast.CoordinatorEntity.__init__', return_value=None)
    def test_real_sensor_availability_with_data(self, mock_coordinator_entity):
        """Test real sensor availability when data is present."""
        from custom_components.rtetempo.sensor_forecast import OpenDPEForecastSensor
        
        forecasts = [
            ForecastDay(date=datetime.date(2025, 1, 15), color="bleu", probability=0.85)
        ]
        coordinator = MockCoordinator(data=forecasts)
        sensor = OpenDPEForecastSensor(coordinator, index=0, visual=False)
        sensor.coordinator = coordinator  # Set coordinator manually since we mocked __init__
        
        assert sensor.available is True
    
    @patch('custom_components.rtetempo.sensor_forecast.CoordinatorEntity.__init__', return_value=None)
    def test_real_sensor_availability_without_data(self, mock_coordinator_entity):
        """Test real sensor availability when data is None."""
        from custom_components.rtetempo.sensor_forecast import OpenDPEForecastSensor
        
        coordinator = MockCoordinator(data=None)
        sensor = OpenDPEForecastSensor(coordinator, index=0, visual=False)
        sensor.coordinator = coordinator  # Set coordinator manually since we mocked __init__
        
        assert sensor.available is False
    
    @patch('custom_components.rtetempo.sensor_forecast.CoordinatorEntity.__init__', return_value=None)
    def test_real_sensor_availability_index_out_of_range(self, mock_coordinator_entity):
        """Test real sensor availability when index exceeds data length."""
        from custom_components.rtetempo.sensor_forecast import OpenDPEForecastSensor
        
        forecasts = [
            ForecastDay(date=datetime.date(2025, 1, 15), color="bleu", probability=0.85)
        ]
        coordinator = MockCoordinator(data=forecasts)
        sensor = OpenDPEForecastSensor(coordinator, index=5, visual=False)
        sensor.coordinator = coordinator  # Set coordinator manually since we mocked __init__
        
        assert sensor.available is False
    
    @patch('custom_components.rtetempo.sensor_forecast.CoordinatorEntity.__init__', return_value=None)
    def test_real_sensor_device_info(self, mock_coordinator_entity):
        """Test real sensor device info."""
        from custom_components.rtetempo.sensor_forecast import OpenDPEForecastSensor
        
        coordinator = MockCoordinator(data=[])
        sensor = OpenDPEForecastSensor(coordinator, index=0, visual=False)
        sensor.coordinator = coordinator  # Set coordinator manually since we mocked __init__
        
        device_info = sensor.device_info
        assert device_info is not None
        assert (DOMAIN, "forecast") in device_info["identifiers"]
        assert device_info["name"] == "RTE Tempo Forecast"
        assert device_info["manufacturer"] == DEVICE_MANUFACTURER
        assert device_info["model"] == DEVICE_MODEL
    
    @patch('custom_components.rtetempo.sensor_forecast.CoordinatorEntity.__init__', return_value=None)
    def test_real_sensor_update_text_bleu(self, mock_coordinator_entity):
        """Test real sensor update with bleu color (text version)."""
        from custom_components.rtetempo.sensor_forecast import OpenDPEForecastSensor
        
        forecasts = [
            ForecastDay(date=datetime.date(2025, 1, 15), color="bleu", probability=0.85)
        ]
        coordinator = MockCoordinator(data=forecasts)
        sensor = OpenDPEForecastSensor(coordinator, index=0, visual=False)
        sensor.coordinator = coordinator  # Set coordinator manually since we mocked __init__
        sensor.async_write_ha_state = MagicMock()
        
        sensor._handle_coordinator_update()
        
        assert sensor._attr_native_value == "Bleu"
        assert sensor._attr_extra_state_attributes["date"] == "2025-01-15"
        assert sensor._attr_extra_state_attributes["probability"] == 0.85
        assert "Open DPE" in sensor._attr_extra_state_attributes["attribution"]
    
    @patch('custom_components.rtetempo.sensor_forecast.CoordinatorEntity.__init__', return_value=None)
    def test_real_sensor_update_visual_rouge(self, mock_coordinator_entity):
        """Test real sensor update with rouge color (visual version)."""
        from custom_components.rtetempo.sensor_forecast import OpenDPEForecastSensor
        
        forecasts = [
            ForecastDay(date=datetime.date(2025, 1, 15), color="rouge", probability=0.45)
        ]
        coordinator = MockCoordinator(data=forecasts)
        sensor = OpenDPEForecastSensor(coordinator, index=0, visual=True)
        sensor.coordinator = coordinator  # Set coordinator manually since we mocked __init__
        sensor.async_write_ha_state = MagicMock()
        
        sensor._handle_coordinator_update()
        
        assert sensor._attr_native_value == "🔴"
        assert sensor._attr_icon == "mdi:alert"
    
    @patch('custom_components.rtetempo.sensor_forecast.CoordinatorEntity.__init__', return_value=None)
    def test_real_sensor_update_with_indicator(self, mock_coordinator_entity):
        """Test real sensor update with indicator."""
        from custom_components.rtetempo.sensor_forecast import OpenDPEForecastSensor
        
        forecasts = [
            ForecastDay(
                date=datetime.date(2025, 1, 19),
                color="bleu",
                probability=None,
                indicator="D"
            )
        ]
        coordinator = MockCoordinator(data=forecasts)
        sensor = OpenDPEForecastSensor(coordinator, index=0, visual=False)
        sensor.coordinator = coordinator  # Set coordinator manually since we mocked __init__
        sensor.async_write_ha_state = MagicMock()
        
        sensor._handle_coordinator_update()
        
        assert sensor._attr_extra_state_attributes["indicator"] == "D"
        assert "probability" not in sensor._attr_extra_state_attributes
    
    @patch('custom_components.rtetempo.sensor_forecast.CoordinatorEntity.__init__', return_value=None)
    def test_real_sensor_update_unknown_color(self, mock_coordinator_entity):
        """Test real sensor update with unknown color."""
        from custom_components.rtetempo.sensor_forecast import OpenDPEForecastSensor
        
        forecasts = [
            ForecastDay(date=datetime.date(2025, 1, 15), color="invalid", probability=0.5)
        ]
        coordinator = MockCoordinator(data=forecasts)
        sensor = OpenDPEForecastSensor(coordinator, index=0, visual=False)
        sensor.coordinator = coordinator  # Set coordinator manually since we mocked __init__
        sensor.async_write_ha_state = MagicMock()
        
        sensor._handle_coordinator_update()
        
        assert sensor._attr_native_value == "inconnu"
    
    @patch('custom_components.rtetempo.sensor_forecast.CoordinatorEntity.__init__', return_value=None)
    def test_real_sensor_update_no_data(self, mock_coordinator_entity):
        """Test real sensor update when no data available."""
        from custom_components.rtetempo.sensor_forecast import OpenDPEForecastSensor
        
        coordinator = MockCoordinator(data=None)
        sensor = OpenDPEForecastSensor(coordinator, index=0, visual=False)
        sensor.coordinator = coordinator  # Set coordinator manually since we mocked __init__
        sensor.async_write_ha_state = MagicMock()
        
        sensor._handle_coordinator_update()
        
        assert sensor._attr_native_value is None
        assert sensor._attr_extra_state_attributes == {}
    
    @patch('custom_components.rtetempo.sensor_forecast.CoordinatorEntity.__init__', return_value=None)
    def test_real_sensor_update_index_out_of_range(self, mock_coordinator_entity):
        """Test real sensor update when index exceeds data length."""
        from custom_components.rtetempo.sensor_forecast import OpenDPEForecastSensor
        
        forecasts = [
            ForecastDay(date=datetime.date(2025, 1, 15), color="bleu", probability=0.85)
        ]
        coordinator = MockCoordinator(data=forecasts)
        sensor = OpenDPEForecastSensor(coordinator, index=5, visual=False)
        sensor.coordinator = coordinator  # Set coordinator manually since we mocked __init__
        sensor.async_write_ha_state = MagicMock()
        
        sensor._handle_coordinator_update()
        
        assert sensor._attr_native_value is None
        assert sensor._attr_extra_state_attributes == {}
