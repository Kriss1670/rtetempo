"""Tests for __init__.py module."""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from custom_components.rtetempo import (
    async_setup_entry,
    async_unload_entry,
    update_listener,
    PLATFORMS,
)
from custom_components.rtetempo.const import (
    DOMAIN,
    CONFIG_CLIENT_ID,
    CONFIG_CLIEND_SECRET,
    OPTION_ADJUSTED_DAYS,
)


# ============================================================================
# Tests for async_setup_entry (Requirements 1.1-1.5)
# ============================================================================

class TestAsyncSetupEntry:
    """Tests for async_setup_entry function."""

    @pytest.mark.asyncio
    async def test_async_setup_entry_creates_api_worker(self, mock_hass, mock_config_entry):
        """Test that async_setup_entry creates an APIWorker."""
        with patch('custom_components.rtetempo.APIWorker') as mock_api_worker_class:
            mock_api_worker = MagicMock()
            mock_api_worker_class.return_value = mock_api_worker
            
            result = await async_setup_entry(mock_hass, mock_config_entry)
            
            mock_api_worker_class.assert_called_once_with(
                client_id=mock_config_entry.data[CONFIG_CLIENT_ID],
                client_secret=mock_config_entry.data[CONFIG_CLIEND_SECRET],
                adjusted_days=mock_config_entry.options.get(OPTION_ADJUSTED_DAYS),
            )

    @pytest.mark.asyncio
    async def test_async_setup_entry_starts_api_worker(self, mock_hass, mock_config_entry):
        """Test that async_setup_entry starts the APIWorker thread."""
        with patch('custom_components.rtetempo.APIWorker') as mock_api_worker_class:
            mock_api_worker = MagicMock()
            mock_api_worker_class.return_value = mock_api_worker
            
            await async_setup_entry(mock_hass, mock_config_entry)
            
            mock_api_worker.start.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_setup_entry_registers_stop_listener(self, mock_hass, mock_config_entry):
        """Test that async_setup_entry registers a stop listener."""
        with patch('custom_components.rtetempo.APIWorker') as mock_api_worker_class:
            mock_api_worker = MagicMock()
            mock_api_worker_class.return_value = mock_api_worker
            
            await async_setup_entry(mock_hass, mock_config_entry)
            
            mock_hass.bus.async_listen_once.assert_called()

    @pytest.mark.asyncio
    async def test_async_setup_entry_forwards_platforms(self, mock_hass, mock_config_entry):
        """Test that async_setup_entry forwards setup to all platforms."""
        with patch('custom_components.rtetempo.APIWorker') as mock_api_worker_class:
            mock_api_worker = MagicMock()
            mock_api_worker_class.return_value = mock_api_worker
            
            await async_setup_entry(mock_hass, mock_config_entry)
            
            mock_hass.config_entries.async_forward_entry_setups.assert_called_once_with(
                mock_config_entry, PLATFORMS
            )

    @pytest.mark.asyncio
    async def test_async_setup_entry_returns_true(self, mock_hass, mock_config_entry):
        """Test that async_setup_entry returns True on success."""
        with patch('custom_components.rtetempo.APIWorker') as mock_api_worker_class:
            mock_api_worker = MagicMock()
            mock_api_worker_class.return_value = mock_api_worker
            
            result = await async_setup_entry(mock_hass, mock_config_entry)
            
            assert result is True

    @pytest.mark.asyncio
    async def test_async_setup_entry_stores_api_worker_in_hass_data(self, mock_hass, mock_config_entry):
        """Test that async_setup_entry stores APIWorker in hass.data."""
        with patch('custom_components.rtetempo.APIWorker') as mock_api_worker_class:
            mock_api_worker = MagicMock()
            mock_api_worker_class.return_value = mock_api_worker
            
            await async_setup_entry(mock_hass, mock_config_entry)
            
            assert mock_config_entry.entry_id in mock_hass.data[DOMAIN]
            assert mock_hass.data[DOMAIN][mock_config_entry.entry_id] == mock_api_worker

    @pytest.mark.asyncio
    async def test_async_setup_entry_creates_domain_dict_if_missing(self, mock_config_entry):
        """Test that async_setup_entry creates DOMAIN dict if missing."""
        mock_hass = MagicMock()
        mock_hass.data = {}  # No DOMAIN key
        mock_hass.bus = MagicMock()
        mock_hass.config_entries = MagicMock()
        mock_hass.config_entries.async_forward_entry_setups = AsyncMock(return_value=True)
        
        with patch('custom_components.rtetempo.APIWorker') as mock_api_worker_class:
            mock_api_worker = MagicMock()
            mock_api_worker_class.return_value = mock_api_worker
            
            await async_setup_entry(mock_hass, mock_config_entry)
            
            assert DOMAIN in mock_hass.data
            assert mock_config_entry.entry_id in mock_hass.data[DOMAIN]


# ============================================================================
# Tests for async_unload_entry (Requirements 2.1-2.4)
# ============================================================================

class TestAsyncUnloadEntry:
    """Tests for async_unload_entry function."""

    @pytest.mark.asyncio
    async def test_async_unload_entry_unloads_platforms(self, mock_hass, mock_config_entry):
        """Test that async_unload_entry unloads all platforms."""
        mock_hass.data[DOMAIN][mock_config_entry.entry_id] = MagicMock()
        
        await async_unload_entry(mock_hass, mock_config_entry)
        
        mock_hass.config_entries.async_unload_platforms.assert_called_once_with(
            mock_config_entry, PLATFORMS
        )

    @pytest.mark.asyncio
    async def test_async_unload_entry_removes_entry_from_data(self, mock_hass, mock_config_entry):
        """Test that async_unload_entry removes entry from hass.data."""
        mock_hass.data[DOMAIN][mock_config_entry.entry_id] = MagicMock()
        
        await async_unload_entry(mock_hass, mock_config_entry)
        
        assert mock_config_entry.entry_id not in mock_hass.data[DOMAIN]

    @pytest.mark.asyncio
    async def test_async_unload_entry_returns_true_on_success(self, mock_hass, mock_config_entry):
        """Test that async_unload_entry returns True on success."""
        mock_hass.data[DOMAIN][mock_config_entry.entry_id] = MagicMock()
        mock_hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)
        
        result = await async_unload_entry(mock_hass, mock_config_entry)
        
        assert result is True

    @pytest.mark.asyncio
    async def test_async_unload_entry_returns_false_on_failure(self, mock_hass, mock_config_entry):
        """Test that async_unload_entry returns False on failure."""
        mock_hass.data[DOMAIN][mock_config_entry.entry_id] = MagicMock()
        mock_hass.config_entries.async_unload_platforms = AsyncMock(return_value=False)
        
        result = await async_unload_entry(mock_hass, mock_config_entry)
        
        assert result is False


# ============================================================================
# Tests for update_listener (Requirements 3.1-3.3)
# ============================================================================

class TestUpdateListener:
    """Tests for update_listener function."""

    @pytest.mark.asyncio
    async def test_update_listener_calls_async_reload(self, mock_hass, mock_config_entry):
        """Test that update_listener calls async_reload to apply changes."""
        mock_hass.config_entries.async_reload = AsyncMock()
        
        await update_listener(mock_hass, mock_config_entry)
        
        mock_hass.config_entries.async_reload.assert_called_once_with(mock_config_entry.entry_id)

    @pytest.mark.asyncio
    async def test_update_listener_reloads_on_option_change(self, mock_hass, mock_config_entry):
        """Test that update_listener reloads integration when options change."""
        mock_hass.config_entries.async_reload = AsyncMock()
        mock_config_entry.options = {OPTION_ADJUSTED_DAYS: True}
        
        await update_listener(mock_hass, mock_config_entry)
        
        # Reload should be called regardless of which option changed
        mock_hass.config_entries.async_reload.assert_called_once()
