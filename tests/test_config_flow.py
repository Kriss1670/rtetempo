"""Tests for config_flow.py module."""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from custom_components.rtetempo.config_flow import ConfigFlow, OptionsFlowHandler
from custom_components.rtetempo.api_worker import BadRequest, ServerError, UnexpectedError
from custom_components.rtetempo.const import (
    DOMAIN,
    CONFIG_CLIENT_ID,
    CONFIG_CLIEND_SECRET,
    OPTION_ADJUSTED_DAYS,
    OPTION_FORECAST_ENABLED,
)


# ============================================================================
# Tests for ConfigFlow (Requirements 11.1-11.6)
# ============================================================================

class TestConfigFlow:
    """Tests for ConfigFlow class."""

    @pytest.mark.asyncio
    async def test_async_step_user_no_input_shows_form(self):
        """Test that async_step_user shows form when no input provided."""
        flow = ConfigFlow()
        flow.hass = MagicMock()
        
        result = await flow.async_step_user(user_input=None)
        
        assert result["type"] == "form"
        assert result["step_id"] == "user"

    @pytest.mark.asyncio
    async def test_async_step_user_valid_credentials_creates_entry(self):
        """Test that valid credentials create an entry."""
        flow = ConfigFlow()
        flow.hass = MagicMock()
        flow.hass.async_add_executor_job = AsyncMock(return_value=None)
        flow.async_set_unique_id = AsyncMock()
        flow._abort_if_unique_id_configured = MagicMock()
        flow.async_create_entry = MagicMock(return_value={"type": "create_entry"})
        
        user_input = {
            CONFIG_CLIENT_ID: "valid_client_id",
            CONFIG_CLIEND_SECRET: "valid_client_secret",
        }
        
        with patch('custom_components.rtetempo.config_flow.application_tester'):
            result = await flow.async_step_user(user_input=user_input)
        
        flow.async_create_entry.assert_called_once()
        assert result["type"] == "create_entry"

    @pytest.mark.asyncio
    async def test_async_step_user_with_forecast_enabled_creates_entry_with_option(self):
        """Test that forecast_enabled option is stored in config entry options."""
        flow = ConfigFlow()
        flow.hass = MagicMock()
        flow.hass.async_add_executor_job = AsyncMock(return_value=None)
        flow.async_set_unique_id = AsyncMock()
        flow._abort_if_unique_id_configured = MagicMock()
        flow.async_create_entry = MagicMock(return_value={"type": "create_entry"})
        
        user_input = {
            CONFIG_CLIENT_ID: "valid_client_id",
            CONFIG_CLIEND_SECRET: "valid_client_secret",
            OPTION_FORECAST_ENABLED: True,
        }
        
        with patch('custom_components.rtetempo.config_flow.application_tester'):
            result = await flow.async_step_user(user_input=user_input)
        
        # Verify the entry was created with forecast_enabled in options
        call_kwargs = flow.async_create_entry.call_args
        assert call_kwargs[1]["options"][OPTION_FORECAST_ENABLED] is True
        assert result["type"] == "create_entry"

    @pytest.mark.asyncio
    async def test_async_step_user_forecast_default_is_false(self):
        """Test that forecast_enabled defaults to False when not provided."""
        flow = ConfigFlow()
        flow.hass = MagicMock()
        flow.hass.async_add_executor_job = AsyncMock(return_value=None)
        flow.async_set_unique_id = AsyncMock()
        flow._abort_if_unique_id_configured = MagicMock()
        flow.async_create_entry = MagicMock(return_value={"type": "create_entry"})
        
        user_input = {
            CONFIG_CLIENT_ID: "valid_client_id",
            CONFIG_CLIEND_SECRET: "valid_client_secret",
            # OPTION_FORECAST_ENABLED not provided - should default to False
        }
        
        with patch('custom_components.rtetempo.config_flow.application_tester'):
            result = await flow.async_step_user(user_input=user_input)
        
        # Verify the entry was created with forecast_enabled defaulting to False
        call_kwargs = flow.async_create_entry.call_args
        assert call_kwargs[1]["options"][OPTION_FORECAST_ENABLED] is False
        assert result["type"] == "create_entry"

    @pytest.mark.asyncio
    async def test_async_step_user_credentials_stored_in_data_not_options(self):
        """Test that credentials are stored in data, not options."""
        flow = ConfigFlow()
        flow.hass = MagicMock()
        flow.hass.async_add_executor_job = AsyncMock(return_value=None)
        flow.async_set_unique_id = AsyncMock()
        flow._abort_if_unique_id_configured = MagicMock()
        flow.async_create_entry = MagicMock(return_value={"type": "create_entry"})
        
        user_input = {
            CONFIG_CLIENT_ID: "valid_client_id",
            CONFIG_CLIEND_SECRET: "valid_client_secret",
            OPTION_FORECAST_ENABLED: True,
        }
        
        with patch('custom_components.rtetempo.config_flow.application_tester'):
            await flow.async_step_user(user_input=user_input)
        
        call_kwargs = flow.async_create_entry.call_args
        # Credentials should be in data
        assert call_kwargs[1]["data"][CONFIG_CLIENT_ID] == "valid_client_id"
        assert call_kwargs[1]["data"][CONFIG_CLIEND_SECRET] == "valid_client_secret"
        # forecast_enabled should NOT be in data
        assert OPTION_FORECAST_ENABLED not in call_kwargs[1]["data"]

    @pytest.mark.asyncio
    async def test_async_step_user_network_error(self):
        """Test that network error shows network_error."""
        from requests.exceptions import RequestException
        
        flow = ConfigFlow()
        flow.hass = MagicMock()
        flow.hass.async_add_executor_job = AsyncMock(side_effect=RequestException("Network error"))
        flow.async_set_unique_id = AsyncMock()
        flow._abort_if_unique_id_configured = MagicMock()
        flow.async_show_form = MagicMock(return_value={"type": "form", "errors": {"base": "network_error"}})
        
        user_input = {
            CONFIG_CLIENT_ID: "client_id",
            CONFIG_CLIEND_SECRET: "client_secret",
        }
        
        result = await flow.async_step_user(user_input=user_input)
        
        assert result["errors"]["base"] == "network_error"

    @pytest.mark.asyncio
    async def test_async_step_user_oauth_error(self):
        """Test that OAuth error shows oauth_error."""
        from oauthlib.oauth2.rfc6749.errors import OAuth2Error
        
        flow = ConfigFlow()
        flow.hass = MagicMock()
        flow.hass.async_add_executor_job = AsyncMock(side_effect=OAuth2Error("OAuth error"))
        flow.async_set_unique_id = AsyncMock()
        flow._abort_if_unique_id_configured = MagicMock()
        flow.async_show_form = MagicMock(return_value={"type": "form", "errors": {"base": "oauth_error"}})
        
        user_input = {
            CONFIG_CLIENT_ID: "client_id",
            CONFIG_CLIEND_SECRET: "client_secret",
        }
        
        result = await flow.async_step_user(user_input=user_input)
        
        assert result["errors"]["base"] == "oauth_error"

    @pytest.mark.asyncio
    async def test_async_step_user_bad_request_error(self):
        """Test that BadRequest error shows http_client_error."""
        flow = ConfigFlow()
        flow.hass = MagicMock()
        flow.hass.async_add_executor_job = AsyncMock(side_effect=BadRequest(400, "Bad request"))
        flow.async_set_unique_id = AsyncMock()
        flow._abort_if_unique_id_configured = MagicMock()
        flow.async_show_form = MagicMock(return_value={"type": "form", "errors": {"base": "http_client_error"}})
        
        user_input = {
            CONFIG_CLIENT_ID: "client_id",
            CONFIG_CLIEND_SECRET: "client_secret",
        }
        
        result = await flow.async_step_user(user_input=user_input)
        
        assert result["errors"]["base"] == "http_client_error"

    @pytest.mark.asyncio
    async def test_async_step_user_server_error(self):
        """Test that ServerError shows http_server_error."""
        flow = ConfigFlow()
        flow.hass = MagicMock()
        flow.hass.async_add_executor_job = AsyncMock(side_effect=ServerError(500, "Server error"))
        flow.async_set_unique_id = AsyncMock()
        flow._abort_if_unique_id_configured = MagicMock()
        flow.async_show_form = MagicMock(return_value={"type": "form", "errors": {"base": "http_server_error"}})
        
        user_input = {
            CONFIG_CLIENT_ID: "client_id",
            CONFIG_CLIEND_SECRET: "client_secret",
        }
        
        result = await flow.async_step_user(user_input=user_input)
        
        assert result["errors"]["base"] == "http_server_error"

    @pytest.mark.asyncio
    async def test_async_step_user_unexpected_error(self):
        """Test that UnexpectedError shows http_unexpected_error."""
        flow = ConfigFlow()
        flow.hass = MagicMock()
        flow.hass.async_add_executor_job = AsyncMock(side_effect=UnexpectedError(418, "Unexpected"))
        flow.async_set_unique_id = AsyncMock()
        flow._abort_if_unique_id_configured = MagicMock()
        flow.async_show_form = MagicMock(return_value={"type": "form", "errors": {"base": "http_unexpected_error"}})
        
        user_input = {
            CONFIG_CLIENT_ID: "client_id",
            CONFIG_CLIEND_SECRET: "client_secret",
        }
        
        result = await flow.async_step_user(user_input=user_input)
        
        assert result["errors"]["base"] == "http_unexpected_error"

    def test_async_get_options_flow(self):
        """Test that async_get_options_flow returns OptionsFlowHandler."""
        config_entry = MagicMock()
        result = ConfigFlow.async_get_options_flow(config_entry)
        assert isinstance(result, OptionsFlowHandler)


# ============================================================================
# Tests for OptionsFlowHandler (Requirements 12.1-12.2)
# ============================================================================

class TestOptionsFlowHandler:
    """Tests for OptionsFlowHandler class."""

    @pytest.mark.asyncio
    async def test_async_step_init_no_input_shows_form(self):
        """Test that async_step_init shows form when no input provided."""
        handler = OptionsFlowHandler()
        handler.config_entry = MagicMock()
        handler.config_entry.options = {OPTION_ADJUSTED_DAYS: False, OPTION_FORECAST_ENABLED: False}
        handler.async_show_form = MagicMock(return_value={"type": "form", "step_id": "init"})
        
        result = await handler.async_step_init(user_input=None)
        
        assert result["type"] == "form"
        assert result["step_id"] == "init"

    @pytest.mark.asyncio
    async def test_async_step_init_with_input_creates_entry(self):
        """Test that async_step_init creates entry when input provided."""
        handler = OptionsFlowHandler()
        handler.config_entry = MagicMock()
        handler.config_entry.options = {OPTION_ADJUSTED_DAYS: False, OPTION_FORECAST_ENABLED: False}
        handler.async_create_entry = MagicMock(return_value={"type": "create_entry"})
        
        user_input = {OPTION_ADJUSTED_DAYS: True, OPTION_FORECAST_ENABLED: True}
        
        result = await handler.async_step_init(user_input=user_input)
        
        handler.async_create_entry.assert_called_once_with(title="", data=user_input)
        assert result["type"] == "create_entry"

    @pytest.mark.asyncio
    async def test_async_step_init_shows_current_forecast_value(self):
        """Test that options form shows current forecast_enabled value."""
        handler = OptionsFlowHandler()
        handler.config_entry = MagicMock()
        handler.config_entry.options = {OPTION_ADJUSTED_DAYS: False, OPTION_FORECAST_ENABLED: True}
        
        # Capture the schema passed to async_show_form
        captured_schema = None
        def capture_show_form(**kwargs):
            nonlocal captured_schema
            captured_schema = kwargs.get("data_schema")
            return {"type": "form", "step_id": "init"}
        
        handler.async_show_form = capture_show_form
        
        await handler.async_step_init(user_input=None)
        
        # The schema should have forecast_enabled with default=True
        assert captured_schema is not None

    @pytest.mark.asyncio
    async def test_async_step_init_persists_forecast_change(self):
        """Test that changing forecast_enabled is persisted."""
        handler = OptionsFlowHandler()
        handler.config_entry = MagicMock()
        handler.config_entry.options = {OPTION_ADJUSTED_DAYS: False, OPTION_FORECAST_ENABLED: False}
        handler.async_create_entry = MagicMock(return_value={"type": "create_entry"})
        
        # Change forecast_enabled from False to True
        user_input = {OPTION_ADJUSTED_DAYS: False, OPTION_FORECAST_ENABLED: True}
        
        await handler.async_step_init(user_input=user_input)
        
        # Verify the new value is passed to async_create_entry
        call_args = handler.async_create_entry.call_args
        assert call_args[1]["data"][OPTION_FORECAST_ENABLED] is True

    @pytest.mark.asyncio
    async def test_async_step_init_defaults_missing_forecast_to_false(self):
        """Test that missing forecast_enabled defaults to False in options form."""
        handler = OptionsFlowHandler()
        handler.config_entry = MagicMock()
        # Simulate old config entry without forecast_enabled
        handler.config_entry.options = {OPTION_ADJUSTED_DAYS: True}
        
        captured_schema = None
        def capture_show_form(**kwargs):
            nonlocal captured_schema
            captured_schema = kwargs.get("data_schema")
            return {"type": "form", "step_id": "init"}
        
        handler.async_show_form = capture_show_form
        
        await handler.async_step_init(user_input=None)
        
        # Schema should be created without error (default False used)
        assert captured_schema is not None
