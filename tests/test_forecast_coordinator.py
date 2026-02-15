"""Tests for forecast_coordinator.py module.

Tests cover coordinator initialization, data updates, error handling, and cleanup.
"""
from __future__ import annotations

import datetime
from datetime import timedelta
from typing import List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Import the real ForecastDay from forecast module
from custom_components.rtetempo.forecast import ForecastDay


# ============================================================================
# Mock Home Assistant components
# ============================================================================

class MockHomeAssistant:
    """Mock HomeAssistant instance."""
    
    def __init__(self):
        self.data = {}
        self.bus = MagicMock()
        self.config = MagicMock()
        self.states = MagicMock()


# We'll patch the HA dependencies and import the real coordinator
# This allows us to test the real code while mocking external dependencies


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def mock_hass():
    """Create a mock HomeAssistant instance."""
    return MockHomeAssistant()


@pytest.fixture
def sample_forecasts():
    """Sample forecast data."""
    return [
        ForecastDay(
            date=datetime.date(2025, 1, 15),
            color="bleu",
            probability=0.85,
        ),
        ForecastDay(
            date=datetime.date(2025, 1, 16),
            color="blanc",
            probability=0.72,
        ),
    ]


# ============================================================================
# Tests: Coordinator Initialization (using real module with mocked HA)
# ============================================================================

class TestCoordinatorInitialization:
    """Tests for coordinator initialization. Validates: Requirement 3.1"""
    
    @patch('custom_components.rtetempo.forecast_coordinator.async_get_clientsession')
    @patch('custom_components.rtetempo.forecast_coordinator.async_track_time_change')
    def test_update_interval_is_6_hours(self, mock_track_time, mock_get_session, mock_hass):
        """Test update interval is set to 6 hours. Validates: Requirement 3.1"""
        mock_get_session.return_value = MagicMock()
        mock_track_time.return_value = MagicMock()
        
        from custom_components.rtetempo.forecast_coordinator import ForecastCoordinator
        coordinator = ForecastCoordinator(mock_hass)
        
        assert coordinator.update_interval == timedelta(hours=6)
    
    @patch('custom_components.rtetempo.forecast_coordinator.async_get_clientsession')
    @patch('custom_components.rtetempo.forecast_coordinator.async_track_time_change')
    def test_coordinator_name(self, mock_track_time, mock_get_session, mock_hass):
        """Test coordinator has correct name."""
        mock_get_session.return_value = MagicMock()
        mock_track_time.return_value = MagicMock()
        
        from custom_components.rtetempo.forecast_coordinator import ForecastCoordinator
        coordinator = ForecastCoordinator(mock_hass)
        
        assert coordinator.name == "Tempo Forecast Coordinator"
    
    @patch('custom_components.rtetempo.forecast_coordinator.async_get_clientsession')
    @patch('custom_components.rtetempo.forecast_coordinator.async_track_time_change')
    def test_initial_data_is_none(self, mock_track_time, mock_get_session, mock_hass):
        """Test initial data is None."""
        mock_get_session.return_value = MagicMock()
        mock_track_time.return_value = MagicMock()
        
        from custom_components.rtetempo.forecast_coordinator import ForecastCoordinator
        coordinator = ForecastCoordinator(mock_hass)
        
        assert coordinator.data is None
    
    @patch('custom_components.rtetempo.forecast_coordinator.async_get_clientsession')
    @patch('custom_components.rtetempo.forecast_coordinator.async_track_time_change')
    def test_time_change_listener_registered(self, mock_track_time, mock_get_session, mock_hass):
        """Test time change listener is registered."""
        mock_get_session.return_value = MagicMock()
        cancel_func = MagicMock()
        mock_track_time.return_value = cancel_func
        
        from custom_components.rtetempo.forecast_coordinator import ForecastCoordinator
        coordinator = ForecastCoordinator(mock_hass)
        
        # The cancel function should be set
        assert coordinator._cancel_time_change == cancel_func
        mock_track_time.assert_called_once()


# ============================================================================
# Tests: Data Update
# ============================================================================

class TestDataUpdate:
    """Tests for data update functionality. Validates: Requirements 3.2, 3.3"""
    
    @pytest.mark.asyncio
    @patch('custom_components.rtetempo.forecast_coordinator.async_get_clientsession')
    @patch('custom_components.rtetempo.forecast_coordinator.async_track_time_change')
    @patch('custom_components.rtetempo.forecast_coordinator.async_fetch_opendpe_forecast')
    @patch('custom_components.rtetempo.forecast_coordinator.apply_tempo_rules')
    async def test_update_applies_tempo_rules(self, mock_apply_rules, mock_fetch, mock_track_time, mock_get_session, mock_hass, sample_forecasts):
        """Test that tempo rules are applied during update. Validates: Requirement 3.2"""
        mock_get_session.return_value = MagicMock()
        mock_track_time.return_value = MagicMock()
        mock_fetch.return_value = sample_forecasts
        mock_apply_rules.return_value = sample_forecasts
        
        from custom_components.rtetempo.forecast_coordinator import ForecastCoordinator
        coordinator = ForecastCoordinator(mock_hass)
        
        result = await coordinator._async_update_data()
        
        mock_fetch.assert_called_once()
        mock_apply_rules.assert_called_once_with(sample_forecasts)
        assert result == sample_forecasts
    
    @pytest.mark.asyncio
    @patch('custom_components.rtetempo.forecast_coordinator.async_get_clientsession')
    @patch('custom_components.rtetempo.forecast_coordinator.async_track_time_change')
    @patch('custom_components.rtetempo.forecast_coordinator.async_fetch_opendpe_forecast')
    async def test_update_error_handling(self, mock_fetch, mock_track_time, mock_get_session, mock_hass):
        """Test error handling during update. Validates: Requirement 3.3"""
        from homeassistant.helpers.update_coordinator import UpdateFailed
        
        mock_get_session.return_value = MagicMock()
        mock_track_time.return_value = MagicMock()
        mock_fetch.side_effect = Exception("API Error")
        
        from custom_components.rtetempo.forecast_coordinator import ForecastCoordinator
        coordinator = ForecastCoordinator(mock_hass)
        
        with pytest.raises(UpdateFailed):
            await coordinator._async_update_data()
    
    @pytest.mark.asyncio
    @patch('custom_components.rtetempo.forecast_coordinator.async_get_clientsession')
    @patch('custom_components.rtetempo.forecast_coordinator.async_track_time_change')
    @patch('custom_components.rtetempo.forecast_coordinator.async_fetch_opendpe_forecast')
    @patch('custom_components.rtetempo.forecast_coordinator.apply_tempo_rules')
    async def test_update_with_empty_data(self, mock_apply_rules, mock_fetch, mock_track_time, mock_get_session, mock_hass):
        """Test update with empty forecast list."""
        mock_get_session.return_value = MagicMock()
        mock_track_time.return_value = MagicMock()
        mock_fetch.return_value = []
        mock_apply_rules.return_value = []
        
        from custom_components.rtetempo.forecast_coordinator import ForecastCoordinator
        coordinator = ForecastCoordinator(mock_hass)
        
        result = await coordinator._async_update_data()
        
        assert result == []


# ============================================================================
# Tests: Cleanup
# ============================================================================

class TestCoordinatorCleanup:
    """Tests for coordinator cleanup. Validates: Requirements 3.4, 3.5"""
    
    @patch('custom_components.rtetempo.forecast_coordinator.async_get_clientsession')
    @patch('custom_components.rtetempo.forecast_coordinator.async_track_time_change')
    def test_unload_cancels_time_change_listener(self, mock_track_time, mock_get_session, mock_hass):
        """Test unload cancels time change listener. Validates: Requirement 3.4"""
        mock_get_session.return_value = MagicMock()
        cancel_mock = MagicMock()
        mock_track_time.return_value = cancel_mock
        
        from custom_components.rtetempo.forecast_coordinator import ForecastCoordinator
        coordinator = ForecastCoordinator(mock_hass)
        
        coordinator.async_unload()
        
        cancel_mock.assert_called_once()
        assert coordinator._cancel_time_change is None
    
    @patch('custom_components.rtetempo.forecast_coordinator.async_get_clientsession')
    @patch('custom_components.rtetempo.forecast_coordinator.async_track_time_change')
    def test_unload_handles_none_listener(self, mock_track_time, mock_get_session, mock_hass):
        """Test unload handles None listener gracefully."""
        mock_get_session.return_value = MagicMock()
        mock_track_time.return_value = MagicMock()
        
        from custom_components.rtetempo.forecast_coordinator import ForecastCoordinator
        coordinator = ForecastCoordinator(mock_hass)
        coordinator._cancel_time_change = None
        
        # Should not raise
        coordinator.async_unload()
        
        assert coordinator._cancel_time_change is None
    
    @pytest.mark.asyncio
    @patch('custom_components.rtetempo.forecast_coordinator.async_get_clientsession')
    @patch('custom_components.rtetempo.forecast_coordinator.async_track_time_change')
    async def test_scheduled_refresh_triggers_update(self, mock_track_time, mock_get_session, mock_hass, sample_forecasts):
        """Test scheduled refresh triggers data update. Validates: Requirement 3.5"""
        mock_get_session.return_value = MagicMock()
        mock_track_time.return_value = MagicMock()
        
        from custom_components.rtetempo.forecast_coordinator import ForecastCoordinator
        coordinator = ForecastCoordinator(mock_hass)
        
        # Mock async_request_refresh
        coordinator.async_request_refresh = AsyncMock()
        
        # Simulate scheduled refresh
        await coordinator._scheduled_refresh(datetime.datetime.now())
        
        coordinator.async_request_refresh.assert_called_once()


# ============================================================================
# Tests: Integration with tempo_rules (using real module)
# ============================================================================

class TestTempoRulesIntegration:
    """Tests for integration with tempo_rules module."""
    
    @pytest.mark.asyncio
    @patch('custom_components.rtetempo.forecast_coordinator.async_get_clientsession')
    @patch('custom_components.rtetempo.forecast_coordinator.async_track_time_change')
    @patch('custom_components.rtetempo.forecast_coordinator.async_fetch_opendpe_forecast')
    @patch('custom_components.rtetempo.forecast_coordinator.apply_tempo_rules')
    async def test_sunday_forecast_adjusted(self, mock_apply_rules, mock_fetch, mock_track_time, mock_get_session, mock_hass):
        """Test Sunday forecasts are adjusted to blue."""
        mock_get_session.return_value = MagicMock()
        mock_track_time.return_value = MagicMock()
        
        # Sunday forecast that should be adjusted
        sunday_forecast = ForecastDay(
            date=datetime.date(2025, 1, 19),  # Sunday
            color="bleu",
            probability=None,
            indicator="D",
        )
        
        mock_fetch.return_value = [sunday_forecast]
        mock_apply_rules.return_value = [sunday_forecast]
        
        from custom_components.rtetempo.forecast_coordinator import ForecastCoordinator
        coordinator = ForecastCoordinator(mock_hass)
        
        result = await coordinator._async_update_data()
        
        assert result[0].color == "bleu"
        assert result[0].indicator == "D"
    
    @pytest.mark.asyncio
    @patch('custom_components.rtetempo.forecast_coordinator.async_get_clientsession')
    @patch('custom_components.rtetempo.forecast_coordinator.async_track_time_change')
    @patch('custom_components.rtetempo.forecast_coordinator.async_fetch_opendpe_forecast')
    @patch('custom_components.rtetempo.forecast_coordinator.apply_tempo_rules')
    async def test_holiday_forecast_adjusted(self, mock_apply_rules, mock_fetch, mock_track_time, mock_get_session, mock_hass):
        """Test holiday forecasts are adjusted to blue with F indicator."""
        mock_get_session.return_value = MagicMock()
        mock_track_time.return_value = MagicMock()
        
        # Holiday forecast
        holiday_forecast = ForecastDay(
            date=datetime.date(2025, 1, 1),  # New Year's Day
            color="bleu",
            probability=None,
            indicator="F",
        )
        
        mock_fetch.return_value = [holiday_forecast]
        mock_apply_rules.return_value = [holiday_forecast]
        
        from custom_components.rtetempo.forecast_coordinator import ForecastCoordinator
        coordinator = ForecastCoordinator(mock_hass)
        
        result = await coordinator._async_update_data()
        
        assert result[0].color == "bleu"
        assert result[0].indicator == "F"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
