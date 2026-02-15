"""Tests for api_worker.py module."""
import datetime
import pytest
import requests
from unittest.mock import MagicMock, patch
from hypothesis import given, strategies as st, settings

from custom_components.rtetempo.api_worker import (
    handle_api_errors,
    BadRequest,
    ServerError,
    UnexpectedError,
    parse_rte_api_datetime,
    parse_rte_api_date,
    adjust_tempo_time,
    application_tester,
    APIWorker,
)
from custom_components.rtetempo.const import (
    FRANCE_TZ,
    HOUR_OF_CHANGE,
    CONFIRM_HOUR,
    CONFIRM_MIN,
)


# ============================================================================
# Tests for handle_api_errors (Requirements 5.1-5.8)
# ============================================================================

class TestHandleApiErrors:
    """Tests for handle_api_errors function."""

    def test_status_200_no_exception(self):
        """Test that 200 status does not raise exception."""
        response = MagicMock()
        response.status_code = 200
        # Should not raise
        handle_api_errors(response)

    def test_status_400_raises_bad_request(self):
        """Test that 400 status raises BadRequest."""
        response = MagicMock()
        response.status_code = 400
        response.json.return_value = {
            "error": "invalid_request",
            "error_description": "Bad request details",
        }
        with pytest.raises(BadRequest) as exc_info:
            handle_api_errors(response)
        assert exc_info.value.code == 400
        assert "invalid_request" in str(exc_info.value)

    def test_status_400_json_decode_error(self):
        """Test 400 with JSON decode error."""
        response = MagicMock()
        response.status_code = 400
        response.json.side_effect = requests.JSONDecodeError("msg", "doc", 0)
        response.text = "Invalid JSON"
        with pytest.raises(BadRequest) as exc_info:
            handle_api_errors(response)
        assert exc_info.value.code == 400

    def test_status_401_raises_bad_request_unauthorized(self):
        """Test that 401 status raises BadRequest with Unauthorized."""
        response = MagicMock()
        response.status_code = 401
        with pytest.raises(BadRequest) as exc_info:
            handle_api_errors(response)
        assert exc_info.value.code == 401
        assert "Unauthorized" in str(exc_info.value)

    def test_status_403_raises_bad_request_forbidden(self):
        """Test that 403 status raises BadRequest with Forbidden."""
        response = MagicMock()
        response.status_code = 403
        with pytest.raises(BadRequest) as exc_info:
            handle_api_errors(response)
        assert exc_info.value.code == 403
        assert "Forbidden" in str(exc_info.value)

    def test_status_404_raises_bad_request_not_found(self):
        """Test that 404 status raises BadRequest with Not Found."""
        response = MagicMock()
        response.status_code = 404
        with pytest.raises(BadRequest) as exc_info:
            handle_api_errors(response)
        assert exc_info.value.code == 404
        assert "Not Found" in str(exc_info.value)

    def test_status_408_raises_bad_request_timeout(self):
        """Test that 408 status raises BadRequest with Request Time-out."""
        response = MagicMock()
        response.status_code = 408
        with pytest.raises(BadRequest) as exc_info:
            handle_api_errors(response)
        assert exc_info.value.code == 408
        assert "Time-out" in str(exc_info.value)

    def test_status_413_raises_bad_request(self):
        """Test that 413 status raises BadRequest."""
        response = MagicMock()
        response.status_code = 413
        with pytest.raises(BadRequest) as exc_info:
            handle_api_errors(response)
        assert exc_info.value.code == 413
        assert "Too Large" in str(exc_info.value)

    def test_status_414_raises_bad_request(self):
        """Test that 414 status raises BadRequest."""
        response = MagicMock()
        response.status_code = 414
        with pytest.raises(BadRequest) as exc_info:
            handle_api_errors(response)
        assert exc_info.value.code == 414
        assert "Too Long" in str(exc_info.value)

    def test_status_429_raises_bad_request(self):
        """Test that 429 status raises BadRequest."""
        response = MagicMock()
        response.status_code = 429
        with pytest.raises(BadRequest) as exc_info:
            handle_api_errors(response)
        assert exc_info.value.code == 429
        assert "Too Many Requests" in str(exc_info.value)

    def test_status_500_raises_server_error(self):
        """Test that 500 status raises ServerError."""
        response = MagicMock()
        response.status_code = 500
        response.json.return_value = {
            "error": "internal_error",
            "error_description": "Server error details",
        }
        with pytest.raises(ServerError) as exc_info:
            handle_api_errors(response)
        assert exc_info.value.code == 500
        assert "internal_error" in str(exc_info.value)

    def test_status_500_json_decode_error(self):
        """Test 500 with JSON decode error."""
        response = MagicMock()
        response.status_code = 500
        response.json.side_effect = requests.JSONDecodeError("msg", "doc", 0)
        response.text = "Server Error"
        with pytest.raises(ServerError) as exc_info:
            handle_api_errors(response)
        assert exc_info.value.code == 500

    def test_status_503_raises_server_error(self):
        """Test that 503 status raises ServerError with Service Unavailable."""
        response = MagicMock()
        response.status_code = 503
        with pytest.raises(ServerError) as exc_info:
            handle_api_errors(response)
        assert exc_info.value.code == 503
        assert "Service Unavailable" in str(exc_info.value)

    def test_status_509_raises_server_error(self):
        """Test that 509 status raises ServerError."""
        response = MagicMock()
        response.status_code = 509
        with pytest.raises(ServerError) as exc_info:
            handle_api_errors(response)
        assert exc_info.value.code == 509
        assert "Bandwidth" in str(exc_info.value)

    def test_unexpected_status_raises_unexpected_error(self):
        """Test that unexpected status raises UnexpectedError."""
        response = MagicMock()
        response.status_code = 418  # I'm a teapot
        response.text = "I'm a teapot"
        with pytest.raises(UnexpectedError) as exc_info:
            handle_api_errors(response)
        assert exc_info.value.code == 418


# ============================================================================
# Tests for date parsing (Requirements 4.1, 4.2)
# ============================================================================

class TestDateParsing:
    """Tests for date parsing functions."""

    def test_parse_rte_api_datetime_valid(self):
        """Test parsing valid RTE datetime string."""
        date_str = "2025-01-15T00:00:00+01:00"
        result = parse_rte_api_datetime(date_str)
        assert isinstance(result, datetime.datetime)
        assert result.year == 2025
        assert result.month == 1
        assert result.day == 15

    def test_parse_rte_api_datetime_summer_time(self):
        """Test parsing RTE datetime with summer time."""
        date_str = "2025-07-15T00:00:00+02:00"
        result = parse_rte_api_datetime(date_str)
        assert isinstance(result, datetime.datetime)
        assert result.year == 2025
        assert result.month == 7
        assert result.day == 15

    def test_parse_rte_api_date_valid(self):
        """Test parsing valid RTE date string."""
        date_str = "2025-01-15T00:00:00+01:00"
        result = parse_rte_api_date(date_str)
        assert isinstance(result, datetime.date)
        assert result.year == 2025
        assert result.month == 1
        assert result.day == 15


# ============================================================================
# Property Test for Time Adjustment (Property 1)
# ============================================================================

class TestProperty1TimeAdjustment:
    """Property test for adjust_tempo_time function."""

    # Feature: remaining-test-coverage, Property 1: Time Adjustment Invariant
    @given(st.datetimes(
        min_value=datetime.datetime(2020, 1, 1),
        max_value=datetime.datetime(2030, 12, 31),
    ))
    @settings(max_examples=100)
    def test_adjust_tempo_time_adds_hour_of_change(self, dt):
        """For any datetime, adjust_tempo_time adds exactly HOUR_OF_CHANGE hours."""
        dt_with_tz = dt.replace(tzinfo=FRANCE_TZ)
        result = adjust_tempo_time(dt_with_tz)
        expected = dt_with_tz + datetime.timedelta(hours=HOUR_OF_CHANGE)
        assert result == expected


# ============================================================================
# Tests for _compute_wait_time (Requirements 6.1-6.5)
# ============================================================================

class TestComputeWaitTime:
    """Tests for APIWorker._compute_wait_time method."""

    def _create_worker(self):
        """Create an APIWorker instance for testing."""
        with patch('custom_components.rtetempo.api_worker.OAuth2Session'):
            worker = APIWorker("test_id", "test_secret", False)
        return worker

    def test_compute_wait_time_none_data_end(self):
        """Test that None data_end returns 10 minutes."""
        worker = self._create_worker()
        localized_now = datetime.datetime.now(FRANCE_TZ)
        result = worker._compute_wait_time(localized_now, None)
        assert result == datetime.timedelta(minutes=10)

    def test_compute_wait_time_has_next_day_past_confirmation(self):
        """Test wait time when we have next day color and past confirmation hour."""
        worker = self._create_worker()
        # Set time to after confirmation hour (e.g., 11:00)
        localized_now = datetime.datetime(2025, 1, 15, 11, 0, 0, tzinfo=FRANCE_TZ)
        # data_end is 2 days ahead (we have next day color)
        data_end = datetime.datetime(2025, 1, 17, 0, 0, 0, tzinfo=FRANCE_TZ)
        
        result = worker._compute_wait_time(localized_now, data_end)
        # Should wait until tomorrow at HOUR_OF_CHANGE
        assert result.total_seconds() > 0

    def test_compute_wait_time_has_next_day_before_confirmation(self):
        """Test wait time when we have next day color but before confirmation hour."""
        worker = self._create_worker()
        # Set time to before confirmation hour (e.g., 9:00)
        localized_now = datetime.datetime(2025, 1, 15, 9, 0, 0, tzinfo=FRANCE_TZ)
        # data_end is 2 days ahead (we have next day color)
        data_end = datetime.datetime(2025, 1, 17, 0, 0, 0, tzinfo=FRANCE_TZ)
        
        result = worker._compute_wait_time(localized_now, data_end)
        # Should wait until confirmation check
        assert result.total_seconds() > 0

    def test_compute_wait_time_no_next_day_before_6h(self):
        """Test wait time when no next day color and before 6h."""
        worker = self._create_worker()
        # Set time to before HOUR_OF_CHANGE (e.g., 5:00)
        localized_now = datetime.datetime(2025, 1, 15, 5, 0, 0, tzinfo=FRANCE_TZ)
        # data_end is 1 day ahead (no next day color)
        data_end = datetime.datetime(2025, 1, 16, 0, 0, 0, tzinfo=FRANCE_TZ)
        
        result = worker._compute_wait_time(localized_now, data_end)
        # Should wait until HOUR_OF_CHANGE
        assert result.total_seconds() > 0
        assert result.total_seconds() < 3600 * 2  # Less than 2 hours

    def test_compute_wait_time_no_next_day_after_6h(self):
        """Test wait time when no next day color and after 6h."""
        worker = self._create_worker()
        # Set time to after HOUR_OF_CHANGE (e.g., 10:00)
        localized_now = datetime.datetime(2025, 1, 15, 10, 0, 0, tzinfo=FRANCE_TZ)
        # data_end is 1 day ahead (no next day color)
        data_end = datetime.datetime(2025, 1, 16, 0, 0, 0, tzinfo=FRANCE_TZ)
        
        result = worker._compute_wait_time(localized_now, data_end)
        # Should retry in ~30 minutes
        assert result.total_seconds() > 0
        assert result.total_seconds() < 3600  # Less than 1 hour


# ============================================================================
# Tests for application_tester (Requirements 7.1-7.3)
# ============================================================================

class TestApplicationTester:
    """Tests for application_tester function."""

    @patch('custom_components.rtetempo.api_worker.OAuth2Session')
    @patch('custom_components.rtetempo.api_worker.HTTPBasicAuth')
    def test_application_tester_success(self, mock_auth, mock_oauth_session):
        """Test successful credential validation."""
        mock_session = MagicMock()
        mock_oauth_session.return_value = mock_session
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_session.get.return_value = mock_response
        
        # Should not raise
        application_tester("valid_id", "valid_secret")
        
        mock_session.fetch_token.assert_called_once()
        mock_session.get.assert_called_once()

    @patch('custom_components.rtetempo.api_worker.OAuth2Session')
    @patch('custom_components.rtetempo.api_worker.HTTPBasicAuth')
    def test_application_tester_oauth_error(self, mock_auth, mock_oauth_session):
        """Test OAuth error during credential validation."""
        from oauthlib.oauth2.rfc6749.errors import OAuth2Error
        
        mock_session = MagicMock()
        mock_oauth_session.return_value = mock_session
        mock_session.fetch_token.side_effect = OAuth2Error("Invalid credentials")
        
        with pytest.raises(OAuth2Error):
            application_tester("invalid_id", "invalid_secret")

    @patch('custom_components.rtetempo.api_worker.OAuth2Session')
    @patch('custom_components.rtetempo.api_worker.HTTPBasicAuth')
    def test_application_tester_api_error(self, mock_auth, mock_oauth_session):
        """Test API error after successful auth."""
        mock_session = MagicMock()
        mock_oauth_session.return_value = mock_session
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.json.return_value = {
            "error": "server_error",
            "error_description": "Internal error",
        }
        mock_session.get.return_value = mock_response
        
        with pytest.raises(ServerError):
            application_tester("valid_id", "valid_secret")


# ============================================================================
# Tests for APIWorker class
# ============================================================================

class TestAPIWorker:
    """Tests for APIWorker class."""

    @patch('custom_components.rtetempo.api_worker.OAuth2Session')
    def test_api_worker_init(self, mock_oauth_session):
        """Test APIWorker initialization."""
        worker = APIWorker("test_id", "test_secret", True)
        assert worker.adjusted_days is True
        assert worker._tempo_days_time == []
        assert worker._tempo_days_date == []

    @patch('custom_components.rtetempo.api_worker.OAuth2Session')
    def test_api_worker_get_calendar_days_adjusted(self, mock_oauth_session):
        """Test get_calendar_days with adjusted_days=True."""
        worker = APIWorker("test_id", "test_secret", True)
        worker._tempo_days_time = ["time_data"]
        worker._tempo_days_date = ["date_data"]
        
        result = worker.get_calendar_days()
        assert result == ["time_data"]

    @patch('custom_components.rtetempo.api_worker.OAuth2Session')
    def test_api_worker_get_calendar_days_not_adjusted(self, mock_oauth_session):
        """Test get_calendar_days with adjusted_days=False."""
        worker = APIWorker("test_id", "test_secret", False)
        worker._tempo_days_time = ["time_data"]
        worker._tempo_days_date = ["date_data"]
        
        result = worker.get_calendar_days()
        assert result == ["date_data"]

    @patch('custom_components.rtetempo.api_worker.OAuth2Session')
    def test_api_worker_update_options(self, mock_oauth_session):
        """Test update_options method."""
        worker = APIWorker("test_id", "test_secret", False)
        assert worker.adjusted_days is False
        
        worker.update_options(True)
        assert worker.adjusted_days is True

    @patch('custom_components.rtetempo.api_worker.OAuth2Session')
    def test_api_worker_signalstop(self, mock_oauth_session):
        """Test signalstop method."""
        worker = APIWorker("test_id", "test_secret", False)
        assert not worker._stopevent.is_set()
        
        worker.signalstop("test_event")
        assert worker._stopevent.is_set()


# ============================================================================
# Additional tests for improved coverage
# ============================================================================

class TestAPIWorkerAdvanced:
    """Advanced tests for APIWorker to improve coverage."""

    @patch('custom_components.rtetempo.api_worker.OAuth2Session')
    def test_get_adjusted_days(self, mock_oauth_session):
        """Test get_adjusted_days method."""
        worker = APIWorker("test_id", "test_secret", False)
        worker._tempo_days_time = ["adjusted_data"]
        
        result = worker.get_adjusted_days()
        assert result == ["adjusted_data"]

    @patch('custom_components.rtetempo.api_worker.OAuth2Session')
    def test_get_regular_days(self, mock_oauth_session):
        """Test get_regular_days method."""
        worker = APIWorker("test_id", "test_secret", False)
        worker._tempo_days_date = ["regular_data"]
        
        result = worker.get_regular_days()
        assert result == ["regular_data"]

    @patch('custom_components.rtetempo.api_worker.OAuth2Session')
    def test_compute_wait_time_unexpected_diff(self, mock_oauth_session):
        """Test wait time with unexpected diff (fallback case)."""
        worker = APIWorker("test_id", "test_secret", False)
        # Set time to any hour
        localized_now = datetime.datetime(2025, 1, 15, 10, 0, 0, tzinfo=FRANCE_TZ)
        # data_end is 3 days ahead (unexpected case)
        data_end = datetime.datetime(2025, 1, 18, 0, 0, 0, tzinfo=FRANCE_TZ)
        
        result = worker._compute_wait_time(localized_now, data_end)
        # Should return fallback wait time (~1 hour)
        assert result.total_seconds() > 0
        assert result.total_seconds() < 7200  # Less than 2 hours

    @patch('custom_components.rtetempo.api_worker.OAuth2Session')
    def test_get_access_token_oauth_error(self, mock_oauth_session):
        """Test _get_access_token with OAuth error."""
        mock_session = MagicMock()
        mock_oauth_session.return_value = mock_session
        from oauthlib.oauth2.rfc6749.errors import OAuth2Error
        mock_session.fetch_token.side_effect = OAuth2Error("Token error")
        
        worker = APIWorker("test_id", "test_secret", False)
        # Should not raise, just log error
        worker._get_access_token()

    @patch('custom_components.rtetempo.api_worker.OAuth2Session')
    def test_get_access_token_request_error(self, mock_oauth_session):
        """Test _get_access_token with request error."""
        mock_session = MagicMock()
        mock_oauth_session.return_value = mock_session
        mock_session.fetch_token.side_effect = requests.exceptions.RequestException("Network error")
        
        worker = APIWorker("test_id", "test_secret", False)
        # Should not raise, just log error
        worker._get_access_token()

    @patch('custom_components.rtetempo.api_worker.OAuth2Session')
    def test_get_tempo_data_success(self, mock_oauth_session):
        """Test _get_tempo_data successful call."""
        mock_session = MagicMock()
        mock_oauth_session.return_value = mock_session
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_session.get.return_value = mock_response
        
        worker = APIWorker("test_id", "test_secret", False)
        start = datetime.datetime(2025, 1, 1, 0, 0, 0, tzinfo=FRANCE_TZ)
        end = datetime.datetime(2025, 1, 15, 0, 0, 0, tzinfo=FRANCE_TZ)
        
        result = worker._get_tempo_data(start, end)
        assert result == mock_response
        mock_session.get.assert_called_once()

    @patch('custom_components.rtetempo.api_worker.OAuth2Session')
    def test_get_tempo_data_token_expired(self, mock_oauth_session):
        """Test _get_tempo_data with token expired error."""
        from oauthlib.oauth2 import TokenExpiredError
        
        mock_session = MagicMock()
        mock_oauth_session.return_value = mock_session
        mock_response = MagicMock()
        mock_response.status_code = 200
        # First call raises TokenExpiredError, second succeeds
        mock_session.get.side_effect = [TokenExpiredError(), mock_response]
        
        worker = APIWorker("test_id", "test_secret", False)
        start = datetime.datetime(2025, 1, 1, 0, 0, 0, tzinfo=FRANCE_TZ)
        end = datetime.datetime(2025, 1, 15, 0, 0, 0, tzinfo=FRANCE_TZ)
        
        result = worker._get_tempo_data(start, end)
        assert result == mock_response
        assert mock_session.get.call_count == 2

    @patch('custom_components.rtetempo.api_worker.OAuth2Session')
    def test_update_tempo_days_success(self, mock_oauth_session):
        """Test _update_tempo_days with successful API response."""
        mock_session = MagicMock()
        mock_oauth_session.return_value = mock_session
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "tempo_like_calendars": {
                "values": [
                    {
                        "start_date": "2025-01-15T00:00:00+01:00",
                        "end_date": "2025-01-16T00:00:00+01:00",
                        "value": "BLUE",
                        "updated_date": "2025-01-14T10:00:00+01:00",
                    }
                ]
            }
        }
        mock_session.get.return_value = mock_response
        
        worker = APIWorker("test_id", "test_secret", False)
        reftime = datetime.datetime(2025, 1, 15, 10, 0, 0, tzinfo=FRANCE_TZ)
        
        result = worker._update_tempo_days(reftime, start_before_days=1, end_after_days=1)
        
        assert result is not None
        assert len(worker._tempo_days_time) == 1
        assert len(worker._tempo_days_date) == 1

    @patch('custom_components.rtetempo.api_worker.OAuth2Session')
    def test_update_tempo_days_request_error(self, mock_oauth_session):
        """Test _update_tempo_days with request error."""
        mock_session = MagicMock()
        mock_oauth_session.return_value = mock_session
        mock_session.get.side_effect = requests.exceptions.RequestException("Network error")
        
        worker = APIWorker("test_id", "test_secret", False)
        reftime = datetime.datetime(2025, 1, 15, 10, 0, 0, tzinfo=FRANCE_TZ)
        
        result = worker._update_tempo_days(reftime, start_before_days=1, end_after_days=1)
        assert result is None

    @patch('custom_components.rtetempo.api_worker.OAuth2Session')
    def test_update_tempo_days_oauth_error(self, mock_oauth_session):
        """Test _update_tempo_days with OAuth error."""
        from oauthlib.oauth2.rfc6749.errors import OAuth2Error
        
        mock_session = MagicMock()
        mock_oauth_session.return_value = mock_session
        mock_session.get.side_effect = OAuth2Error("OAuth error")
        
        worker = APIWorker("test_id", "test_secret", False)
        reftime = datetime.datetime(2025, 1, 15, 10, 0, 0, tzinfo=FRANCE_TZ)
        
        result = worker._update_tempo_days(reftime, start_before_days=1, end_after_days=1)
        assert result is None

    @patch('custom_components.rtetempo.api_worker.OAuth2Session')
    def test_update_tempo_days_http_error(self, mock_oauth_session):
        """Test _update_tempo_days with HTTP error."""
        mock_session = MagicMock()
        mock_oauth_session.return_value = mock_session
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.json.return_value = {
            "error": "server_error",
            "error_description": "Internal error",
        }
        mock_session.get.return_value = mock_response
        
        worker = APIWorker("test_id", "test_secret", False)
        reftime = datetime.datetime(2025, 1, 15, 10, 0, 0, tzinfo=FRANCE_TZ)
        
        result = worker._update_tempo_days(reftime, start_before_days=1, end_after_days=1)
        assert result is None

    @patch('custom_components.rtetempo.api_worker.OAuth2Session')
    def test_update_tempo_days_json_decode_error(self, mock_oauth_session):
        """Test _update_tempo_days with JSON decode error on 200 response."""
        mock_session = MagicMock()
        mock_oauth_session.return_value = mock_session
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = requests.JSONDecodeError("msg", "doc", 0)
        mock_response.text = "Invalid JSON"
        mock_session.get.return_value = mock_response
        
        worker = APIWorker("test_id", "test_secret", False)
        reftime = datetime.datetime(2025, 1, 15, 10, 0, 0, tzinfo=FRANCE_TZ)
        
        result = worker._update_tempo_days(reftime, start_before_days=1, end_after_days=1)
        assert result is None

    @patch('custom_components.rtetempo.api_worker.OAuth2Session')
    def test_update_tempo_days_empty_results(self, mock_oauth_session):
        """Test _update_tempo_days with empty results."""
        mock_session = MagicMock()
        mock_oauth_session.return_value = mock_session
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "tempo_like_calendars": {
                "values": []
            }
        }
        mock_session.get.return_value = mock_response
        
        worker = APIWorker("test_id", "test_secret", False)
        reftime = datetime.datetime(2025, 1, 15, 10, 0, 0, tzinfo=FRANCE_TZ)
        
        result = worker._update_tempo_days(reftime, start_before_days=1, end_after_days=1)
        assert result is None

    @patch('custom_components.rtetempo.api_worker.OAuth2Session')
    def test_update_tempo_days_key_error_special_date(self, mock_oauth_session):
        """Test _update_tempo_days with KeyError for special date 2022-12-28."""
        mock_session = MagicMock()
        mock_oauth_session.return_value = mock_session
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "tempo_like_calendars": {
                "values": [
                    {
                        "start_date": "2022-12-28T00:00:00+01:00",
                        "end_date": "2022-12-29T00:00:00+01:00",
                        # Missing "value" key - special case handled by code
                        "updated_date": "2022-12-27T10:00:00+01:00",
                    }
                ]
            }
        }
        mock_session.get.return_value = mock_response
        
        worker = APIWorker("test_id", "test_secret", False)
        reftime = datetime.datetime(2022, 12, 28, 10, 0, 0, tzinfo=FRANCE_TZ)
        
        result = worker._update_tempo_days(reftime, start_before_days=1, end_after_days=1)
        # Should handle special date and set it to BLUE
        assert len(worker._tempo_days_time) == 1
        assert worker._tempo_days_time[0].Value == "BLUE"

    @patch('custom_components.rtetempo.api_worker.OAuth2Session')
    def test_update_tempo_days_key_error_other_date(self, mock_oauth_session):
        """Test _update_tempo_days with KeyError for non-special date."""
        mock_session = MagicMock()
        mock_oauth_session.return_value = mock_session
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "tempo_like_calendars": {
                "values": [
                    {
                        "start_date": "2025-01-15T00:00:00+01:00",
                        "end_date": "2025-01-16T00:00:00+01:00",
                        # Missing "value" key
                        "updated_date": "2025-01-14T10:00:00+01:00",
                    }
                ]
            }
        }
        mock_session.get.return_value = mock_response
        
        worker = APIWorker("test_id", "test_secret", False)
        reftime = datetime.datetime(2025, 1, 15, 10, 0, 0, tzinfo=FRANCE_TZ)
        
        result = worker._update_tempo_days(reftime, start_before_days=1, end_after_days=1)
        # Should skip the day with missing value
        assert len(worker._tempo_days_time) == 0


class TestHandleApiErrorsKeyError:
    """Tests for handle_api_errors with KeyError."""

    def test_status_400_key_error(self):
        """Test 400 with missing keys in JSON."""
        response = MagicMock()
        response.status_code = 400
        response.json.return_value = {"other_key": "value"}  # Missing error keys
        response.text = "Missing keys"
        with pytest.raises(BadRequest) as exc_info:
            handle_api_errors(response)
        assert exc_info.value.code == 400

    def test_status_500_key_error(self):
        """Test 500 with missing keys in JSON."""
        response = MagicMock()
        response.status_code = 500
        response.json.return_value = {"other_key": "value"}  # Missing error keys
        response.text = "Missing keys"
        with pytest.raises(ServerError) as exc_info:
            handle_api_errors(response)
        assert exc_info.value.code == 500
