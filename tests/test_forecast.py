"""Tests for forecast.py module.

Tests cover API data fetching, JSON parsing, and error handling.
"""
from __future__ import annotations

import datetime
from typing import Any, List

import pytest
import aiohttp

# Import the real module to get coverage
from custom_components.rtetempo.forecast import (
    ForecastDay,
    async_fetch_opendpe_forecast,
    OPEN_DPE_URL,
)


# ============================================================================
# Mock aiohttp components
# ============================================================================

class MockResponse:
    """Mock aiohttp response."""
    
    def __init__(
        self,
        status: int = 200,
        json_data: Any = None,
        raise_on_json: Exception = None,
    ):
        self.status = status
        self._json_data = json_data
        self._raise_on_json = raise_on_json
    
    async def json(self):
        if self._raise_on_json:
            raise self._raise_on_json
        return self._json_data
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, *args):
        pass


class MockSession:
    """Mock aiohttp ClientSession."""
    
    def __init__(self, response: MockResponse = None, raise_on_get: Exception = None):
        self._response = response
        self._raise_on_get = raise_on_get
    
    def get(self, url: str, **kwargs):
        if self._raise_on_get:
            raise self._raise_on_get
        return self._response


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def valid_api_response():
    """Valid API response with multiple entries."""
    return [
        {"date": "2025-01-15", "couleur": "BLEU", "probability": 0.85},
        {"date": "2025-01-16", "couleur": "blanc", "probability": 0.72},
        {"date": "2025-01-17", "couleur": "Rouge", "probability": 0.45},
    ]


@pytest.fixture
def response_with_missing_probability():
    """API response with missing probability."""
    return [
        {"date": "2025-01-15", "couleur": "bleu"},
        {"date": "2025-01-16", "couleur": "blanc", "probability": None},
    ]


@pytest.fixture
def response_with_malformed_entry():
    """API response with one malformed entry."""
    return [
        {"date": "2025-01-15", "couleur": "bleu", "probability": 0.85},
        {"date": "invalid-date", "couleur": "blanc"},  # Malformed
        {"date": "2025-01-17", "couleur": "rouge", "probability": 0.45},
    ]


# ============================================================================
# Tests: Valid JSON Parsing
# ============================================================================

class TestValidJsonParsing:
    """Tests for parsing valid JSON responses. Validates: Requirements 1.1-1.5"""
    
    @pytest.mark.asyncio
    async def test_parse_valid_json_complete(self, valid_api_response):
        """Test parsing complete valid JSON with all fields."""
        session = MockSession(MockResponse(200, valid_api_response))
        
        result = await async_fetch_opendpe_forecast(session)
        
        assert len(result) == 3
        assert result[0].date == datetime.date(2025, 1, 15)
        assert result[0].color == "bleu"  # Normalized to lowercase
        assert result[0].probability == 0.85
        assert result[0].source == "open_dpe"
    
    @pytest.mark.asyncio
    async def test_parse_date_conversion(self, valid_api_response):
        """Test date string is converted to datetime.date. Validates: Requirement 1.2"""
        session = MockSession(MockResponse(200, valid_api_response))
        
        result = await async_fetch_opendpe_forecast(session)
        
        assert isinstance(result[0].date, datetime.date)
        assert result[0].date.year == 2025
        assert result[0].date.month == 1
        assert result[0].date.day == 15
    
    @pytest.mark.asyncio
    async def test_color_normalization_uppercase(self, valid_api_response):
        """Test color is normalized to lowercase. Validates: Requirement 1.3"""
        session = MockSession(MockResponse(200, valid_api_response))
        
        result = await async_fetch_opendpe_forecast(session)
        
        # "BLEU" should become "bleu"
        assert result[0].color == "bleu"
        # "blanc" stays "blanc"
        assert result[1].color == "blanc"
        # "Rouge" should become "rouge"
        assert result[2].color == "rouge"
    
    @pytest.mark.asyncio
    async def test_probability_stored_as_float(self, valid_api_response):
        """Test probability is stored as float. Validates: Requirement 1.4"""
        session = MockSession(MockResponse(200, valid_api_response))
        
        result = await async_fetch_opendpe_forecast(session)
        
        assert isinstance(result[0].probability, float)
        assert result[0].probability == 0.85
    
    @pytest.mark.asyncio
    async def test_missing_probability_is_none(self, response_with_missing_probability):
        """Test missing probability is stored as None. Validates: Requirement 1.5"""
        session = MockSession(MockResponse(200, response_with_missing_probability))
        
        result = await async_fetch_opendpe_forecast(session)
        
        assert len(result) == 2
        assert result[0].probability is None
        assert result[1].probability is None


# ============================================================================
# Tests: Error Handling
# ============================================================================

class TestErrorHandling:
    """Tests for API error handling. Validates: Requirements 2.1-2.5"""
    
    @pytest.mark.asyncio
    async def test_http_404_returns_empty_list(self):
        """Test HTTP 404 returns empty list. Validates: Requirement 2.1"""
        session = MockSession(MockResponse(404))
        
        result = await async_fetch_opendpe_forecast(session)
        
        assert result == []
    
    @pytest.mark.asyncio
    async def test_http_500_returns_empty_list(self):
        """Test HTTP 500 returns empty list. Validates: Requirement 2.1"""
        session = MockSession(MockResponse(500))
        
        result = await async_fetch_opendpe_forecast(session)
        
        assert result == []
    
    @pytest.mark.asyncio
    async def test_timeout_returns_empty_list(self):
        """Test timeout returns empty list. Validates: Requirement 2.2"""
        session = MockSession(raise_on_get=aiohttp.ClientError("Timeout"))
        
        result = await async_fetch_opendpe_forecast(session)
        
        assert result == []
    
    @pytest.mark.asyncio
    async def test_invalid_json_returns_empty_list(self):
        """Test invalid JSON returns empty list. Validates: Requirement 2.3"""
        session = MockSession(MockResponse(200, raise_on_json=ValueError("Invalid JSON")))
        
        result = await async_fetch_opendpe_forecast(session)
        
        assert result == []
    
    @pytest.mark.asyncio
    async def test_malformed_entry_skipped(self, response_with_malformed_entry):
        """Test malformed entry is skipped. Validates: Requirement 2.4"""
        session = MockSession(MockResponse(200, response_with_malformed_entry))
        
        result = await async_fetch_opendpe_forecast(session)
        
        # Should have 2 entries (malformed one skipped)
        assert len(result) == 2
        assert result[0].date == datetime.date(2025, 1, 15)
        assert result[1].date == datetime.date(2025, 1, 17)
    
    @pytest.mark.asyncio
    async def test_network_error_returns_empty_list(self):
        """Test network error returns empty list. Validates: Requirement 2.5"""
        session = MockSession(raise_on_get=aiohttp.ClientError("Network unreachable"))
        
        result = await async_fetch_opendpe_forecast(session)
        
        assert result == []
    
    @pytest.mark.asyncio
    async def test_empty_response_returns_empty_list(self):
        """Test empty JSON array returns empty list."""
        session = MockSession(MockResponse(200, []))
        
        result = await async_fetch_opendpe_forecast(session)
        
        assert result == []


# ============================================================================
# Tests: Edge Cases
# ============================================================================

class TestEdgeCases:
    """Tests for edge cases in forecast parsing."""
    
    @pytest.mark.asyncio
    async def test_empty_color_normalized(self):
        """Test empty color is handled."""
        data = [{"date": "2025-01-15", "couleur": "", "probability": 0.5}]
        session = MockSession(MockResponse(200, data))
        
        result = await async_fetch_opendpe_forecast(session)
        
        assert len(result) == 1
        assert result[0].color == ""
    
    @pytest.mark.asyncio
    async def test_missing_color_key(self):
        """Test missing couleur key defaults to empty string."""
        data = [{"date": "2025-01-15", "probability": 0.5}]
        session = MockSession(MockResponse(200, data))
        
        result = await async_fetch_opendpe_forecast(session)
        
        assert len(result) == 1
        assert result[0].color == ""
    
    @pytest.mark.asyncio
    async def test_probability_zero(self):
        """Test probability of 0.0 is stored correctly."""
        data = [{"date": "2025-01-15", "couleur": "bleu", "probability": 0.0}]
        session = MockSession(MockResponse(200, data))
        
        result = await async_fetch_opendpe_forecast(session)
        
        assert len(result) == 1
        assert result[0].probability == 0.0
    
    @pytest.mark.asyncio
    async def test_probability_one(self):
        """Test probability of 1.0 is stored correctly."""
        data = [{"date": "2025-01-15", "couleur": "bleu", "probability": 1.0}]
        session = MockSession(MockResponse(200, data))
        
        result = await async_fetch_opendpe_forecast(session)
        
        assert len(result) == 1
        assert result[0].probability == 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


# ============================================================================
# Property-Based Tests
# ============================================================================

from hypothesis import given, settings, strategies as st


# Strategy for valid dates
date_strategy = st.dates(
    min_value=datetime.date(2020, 1, 1),
    max_value=datetime.date(2030, 12, 31)
)

# Strategy for colors (various cases)
color_strategy = st.sampled_from([
    "bleu", "blanc", "rouge",
    "BLEU", "BLANC", "ROUGE",
    "Bleu", "Blanc", "Rouge",
])

# Strategy for probability
probability_strategy = st.one_of(
    st.none(),
    st.floats(min_value=0.0, max_value=1.0, allow_nan=False)
)


class TestProperty1JsonParsingConsistency:
    """
    Property 1: JSON Parsing Consistency
    
    *For any* valid JSON entry with date, color, and optional probability,
    parsing SHALL produce a ForecastDay with:
    - date converted to datetime.date
    - color normalized to lowercase
    - probability as float or None
    
    **Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5**
    """
    
    @given(
        date=date_strategy,
        color=color_strategy,
        probability=probability_strategy,
    )
    @settings(max_examples=100)
    @pytest.mark.asyncio
    async def test_json_parsing_consistency(self, date, color, probability):
        """Feature: forecast-test-coverage, Property 1: JSON Parsing Consistency"""
        # Build API response
        entry = {
            "date": date.strftime("%Y-%m-%d"),
            "couleur": color,
        }
        if probability is not None:
            entry["probability"] = probability
        
        session = MockSession(MockResponse(200, [entry]))
        
        result = await async_fetch_opendpe_forecast(session)
        
        # Should parse successfully
        assert len(result) == 1
        forecast = result[0]
        
        # Date should be converted to datetime.date
        assert isinstance(forecast.date, datetime.date)
        assert forecast.date == date
        
        # Color should be normalized to lowercase
        assert forecast.color == color.lower()
        
        # Probability should be float or None
        if probability is not None:
            assert isinstance(forecast.probability, float)
            assert forecast.probability == probability
        else:
            assert forecast.probability is None
        
        # Source should always be "open_dpe"
        assert forecast.source == "open_dpe"


class TestProperty2ErrorHandlingReturnsEmptyList:
    """
    Property 2: Error Handling Returns Empty List
    
    *For any* API error (HTTP error, timeout, invalid JSON, network error),
    the fetch function SHALL return an empty list without raising an exception.
    
    **Validates: Requirements 2.1, 2.2, 2.3, 2.5**
    """
    
    @given(status_code=st.integers(min_value=400, max_value=599))
    @settings(max_examples=100)
    @pytest.mark.asyncio
    async def test_http_errors_return_empty_list(self, status_code):
        """Feature: forecast-test-coverage, Property 2: HTTP errors return empty list
        
        Validates: Requirement 2.1
        """
        session = MockSession(MockResponse(status_code))
        
        result = await async_fetch_opendpe_forecast(session)
        
        assert result == []
        assert isinstance(result, list)
    
    @given(error_message=st.text(min_size=1, max_size=100))
    @settings(max_examples=50)
    @pytest.mark.asyncio
    async def test_network_errors_return_empty_list(self, error_message):
        """Feature: forecast-test-coverage, Property 2: Network errors return empty list
        
        Validates: Requirement 2.5
        """
        session = MockSession(raise_on_get=aiohttp.ClientError(error_message))
        
        result = await async_fetch_opendpe_forecast(session)
        
        assert result == []
        assert isinstance(result, list)
    
    @given(timeout_value=st.floats(min_value=0.001, max_value=10.0, allow_nan=False))
    @settings(max_examples=50)
    @pytest.mark.asyncio
    async def test_timeout_errors_return_empty_list(self, timeout_value):
        """Feature: forecast-test-coverage, Property 2: Timeout errors return empty list
        
        Validates: Requirement 2.2
        """
        session = MockSession(raise_on_get=aiohttp.ServerTimeoutError(f"Timeout after {timeout_value}s"))
        
        result = await async_fetch_opendpe_forecast(session)
        
        assert result == []
        assert isinstance(result, list)
    
    @given(invalid_json=st.text(min_size=1, max_size=50))
    @settings(max_examples=50)
    @pytest.mark.asyncio
    async def test_invalid_json_returns_empty_list(self, invalid_json):
        """Feature: forecast-test-coverage, Property 2: Invalid JSON returns empty list
        
        Validates: Requirement 2.3
        """
        session = MockSession(MockResponse(200, raise_on_json=ValueError(f"Invalid JSON: {invalid_json}")))
        
        result = await async_fetch_opendpe_forecast(session)
        
        assert result == []
        assert isinstance(result, list)
