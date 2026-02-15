"""Tests for optional forecast feature."""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from hypothesis import given, strategies as st, settings

from custom_components.rtetempo.const import (
    DOMAIN,
    OPTION_FORECAST_ENABLED,
    OPTION_ADJUSTED_DAYS,
)


# ============================================================================
# Tests for conditional forecast loading (Requirements 4.1, 4.2)
# ============================================================================

class TestConditionalForecastLoading:
    """Tests for conditional forecast sensor loading based on option."""

    @pytest.mark.asyncio
    async def test_forecast_sensors_created_when_enabled(self):
        """Test that forecast sensors are created when forecast_enabled is True."""
        from custom_components.rtetempo.sensor import async_setup_entry
        
        mock_hass = MagicMock()
        mock_hass.data = {DOMAIN: {"test_entry_id": MagicMock()}}
        
        mock_config_entry = MagicMock()
        mock_config_entry.entry_id = "test_entry_id"
        mock_config_entry.options = {OPTION_FORECAST_ENABLED: True}
        mock_config_entry.async_on_unload = MagicMock()
        
        mock_add_entities = MagicMock()
        
        with patch('custom_components.rtetempo.sensor.asyncio.sleep', new_callable=AsyncMock):
            with patch('custom_components.rtetempo.sensor.ForecastCoordinator') as mock_coordinator_class:
                mock_coordinator = MagicMock()
                mock_coordinator.async_config_entry_first_refresh = AsyncMock()
                mock_coordinator.async_unload = MagicMock()
                mock_coordinator_class.return_value = mock_coordinator
                
                await async_setup_entry(mock_hass, mock_config_entry, mock_add_entities)
        
        # Verify ForecastCoordinator was created
        mock_coordinator_class.assert_called_once_with(mock_hass)
        
        # Verify async_add_entities was called twice (once for regular sensors, once for forecast)
        assert mock_add_entities.call_count == 2

    @pytest.mark.asyncio
    async def test_forecast_sensors_not_created_when_disabled(self):
        """Test that forecast sensors are NOT created when forecast_enabled is False."""
        from custom_components.rtetempo.sensor import async_setup_entry
        
        mock_hass = MagicMock()
        mock_hass.data = {DOMAIN: {"test_entry_id": MagicMock()}}
        
        mock_config_entry = MagicMock()
        mock_config_entry.entry_id = "test_entry_id"
        mock_config_entry.options = {OPTION_FORECAST_ENABLED: False}
        mock_config_entry.async_on_unload = MagicMock()
        
        mock_add_entities = MagicMock()
        
        with patch('custom_components.rtetempo.sensor.asyncio.sleep', new_callable=AsyncMock):
            with patch('custom_components.rtetempo.sensor.ForecastCoordinator') as mock_coordinator_class:
                await async_setup_entry(mock_hass, mock_config_entry, mock_add_entities)
        
        # Verify ForecastCoordinator was NOT created
        mock_coordinator_class.assert_not_called()
        
        # Verify async_add_entities was called only once (for regular sensors)
        assert mock_add_entities.call_count == 1

    @pytest.mark.asyncio
    async def test_forecast_default_to_disabled_when_option_missing(self):
        """Test that forecast defaults to disabled when option is not present."""
        from custom_components.rtetempo.sensor import async_setup_entry
        
        mock_hass = MagicMock()
        mock_hass.data = {DOMAIN: {"test_entry_id": MagicMock()}}
        
        mock_config_entry = MagicMock()
        mock_config_entry.entry_id = "test_entry_id"
        # No OPTION_FORECAST_ENABLED in options (simulating old config entry)
        mock_config_entry.options = {OPTION_ADJUSTED_DAYS: False}
        mock_config_entry.async_on_unload = MagicMock()
        
        mock_add_entities = MagicMock()
        
        with patch('custom_components.rtetempo.sensor.asyncio.sleep', new_callable=AsyncMock):
            with patch('custom_components.rtetempo.sensor.ForecastCoordinator') as mock_coordinator_class:
                await async_setup_entry(mock_hass, mock_config_entry, mock_add_entities)
        
        # Verify ForecastCoordinator was NOT created (default is False)
        mock_coordinator_class.assert_not_called()


# ============================================================================
# Property Test: Forecast sensors existence matches option (Property 1)
# ============================================================================

class TestProperty1ForecastSensorsExistence:
    """Property test for forecast sensors existence matching option."""

    # Feature: optional-forecast, Property 1: Forecast sensors existence matches option
    # For any config entry, the forecast sensors SHALL exist if and only if 
    # the forecast_enabled option is True.
    # **Validates: Requirements 4.1, 4.2**
    
    @given(st.booleans())
    @settings(max_examples=100)
    def test_forecast_sensors_existence_matches_option(self, forecast_enabled):
        """For any boolean value of forecast_enabled, sensors exist iff option is True."""
        import asyncio
        from custom_components.rtetempo.sensor import async_setup_entry
        
        mock_hass = MagicMock()
        mock_hass.data = {DOMAIN: {"test_entry_id": MagicMock()}}
        
        mock_config_entry = MagicMock()
        mock_config_entry.entry_id = "test_entry_id"
        mock_config_entry.options = {OPTION_FORECAST_ENABLED: forecast_enabled}
        mock_config_entry.async_on_unload = MagicMock()
        
        mock_add_entities = MagicMock()
        
        with patch('custom_components.rtetempo.sensor.asyncio.sleep', new_callable=AsyncMock):
            with patch('custom_components.rtetempo.sensor.ForecastCoordinator') as mock_coordinator_class:
                mock_coordinator = MagicMock()
                mock_coordinator.async_config_entry_first_refresh = AsyncMock()
                mock_coordinator.async_unload = MagicMock()
                mock_coordinator_class.return_value = mock_coordinator
                
                asyncio.get_event_loop().run_until_complete(
                    async_setup_entry(mock_hass, mock_config_entry, mock_add_entities)
                )
        
        # Property: ForecastCoordinator created iff forecast_enabled is True
        if forecast_enabled:
            mock_coordinator_class.assert_called_once()
            # Two calls to async_add_entities: regular sensors + forecast sensors
            assert mock_add_entities.call_count == 2
        else:
            mock_coordinator_class.assert_not_called()
            # Only one call to async_add_entities: regular sensors only
            assert mock_add_entities.call_count == 1


# ============================================================================
# Tests for forecast coordinator cleanup
# ============================================================================

class TestForecastCoordinatorCleanup:
    """Tests for forecast coordinator cleanup on unload."""

    @pytest.mark.asyncio
    async def test_forecast_coordinator_cleanup_registered_when_enabled(self):
        """Test that coordinator cleanup is registered when forecast is enabled."""
        from custom_components.rtetempo.sensor import async_setup_entry
        
        mock_hass = MagicMock()
        mock_hass.data = {DOMAIN: {"test_entry_id": MagicMock()}}
        
        mock_config_entry = MagicMock()
        mock_config_entry.entry_id = "test_entry_id"
        mock_config_entry.options = {OPTION_FORECAST_ENABLED: True}
        mock_config_entry.async_on_unload = MagicMock()
        
        mock_add_entities = MagicMock()
        
        with patch('custom_components.rtetempo.sensor.asyncio.sleep', new_callable=AsyncMock):
            with patch('custom_components.rtetempo.sensor.ForecastCoordinator') as mock_coordinator_class:
                mock_coordinator = MagicMock()
                mock_coordinator.async_config_entry_first_refresh = AsyncMock()
                mock_coordinator.async_unload = MagicMock()
                mock_coordinator_class.return_value = mock_coordinator
                
                await async_setup_entry(mock_hass, mock_config_entry, mock_add_entities)
        
        # Verify async_on_unload was called twice: once for coordinator, once for data cleanup
        assert mock_config_entry.async_on_unload.call_count == 2
        # First call should be for coordinator cleanup
        calls = mock_config_entry.async_on_unload.call_args_list
        assert calls[0][0][0] == mock_coordinator.async_unload

    @pytest.mark.asyncio
    async def test_forecast_coordinator_stored_in_hass_data(self):
        """Test that coordinator reference is stored in hass.data for cleanup."""
        from custom_components.rtetempo.sensor import async_setup_entry
        
        mock_hass = MagicMock()
        mock_hass.data = {DOMAIN: {"test_entry_id": MagicMock()}}
        
        mock_config_entry = MagicMock()
        mock_config_entry.entry_id = "test_entry_id"
        mock_config_entry.options = {OPTION_FORECAST_ENABLED: True}
        mock_config_entry.async_on_unload = MagicMock()
        
        mock_add_entities = MagicMock()
        
        with patch('custom_components.rtetempo.sensor.asyncio.sleep', new_callable=AsyncMock):
            with patch('custom_components.rtetempo.sensor.ForecastCoordinator') as mock_coordinator_class:
                mock_coordinator = MagicMock()
                mock_coordinator.async_config_entry_first_refresh = AsyncMock()
                mock_coordinator.async_unload = MagicMock()
                mock_coordinator_class.return_value = mock_coordinator
                
                await async_setup_entry(mock_hass, mock_config_entry, mock_add_entities)
        
        # Verify coordinator is stored in hass.data
        assert mock_hass.data[DOMAIN]["test_entry_id_forecast"] == mock_coordinator

    @pytest.mark.asyncio
    async def test_forecast_data_cleanup_removes_reference(self):
        """Test that the cleanup callback removes the forecast reference from hass.data."""
        from custom_components.rtetempo.sensor import async_setup_entry
        
        mock_hass = MagicMock()
        mock_hass.data = {DOMAIN: {"test_entry_id": MagicMock()}}
        
        mock_config_entry = MagicMock()
        mock_config_entry.entry_id = "test_entry_id"
        mock_config_entry.options = {OPTION_FORECAST_ENABLED: True}
        
        # Capture the cleanup callbacks
        cleanup_callbacks = []
        mock_config_entry.async_on_unload = lambda cb: cleanup_callbacks.append(cb)
        
        mock_add_entities = MagicMock()
        
        with patch('custom_components.rtetempo.sensor.asyncio.sleep', new_callable=AsyncMock):
            with patch('custom_components.rtetempo.sensor.ForecastCoordinator') as mock_coordinator_class:
                mock_coordinator = MagicMock()
                mock_coordinator.async_config_entry_first_refresh = AsyncMock()
                mock_coordinator.async_unload = MagicMock()
                mock_coordinator_class.return_value = mock_coordinator
                
                await async_setup_entry(mock_hass, mock_config_entry, mock_add_entities)
        
        # Verify coordinator is stored
        assert "test_entry_id_forecast" in mock_hass.data[DOMAIN]
        
        # Call the data cleanup callback (second one registered)
        data_cleanup = cleanup_callbacks[1]
        data_cleanup()
        
        # Verify reference is removed
        assert "test_entry_id_forecast" not in mock_hass.data[DOMAIN]
