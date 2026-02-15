"""Pytest fixtures for RTE Tempo tests."""
import datetime
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from hypothesis import strategies as st

from custom_components.rtetempo.forecast import ForecastDay
from custom_components.rtetempo.api_worker import TempoDay
from custom_components.rtetempo.const import (
    DOMAIN,
    CONFIG_CLIENT_ID,
    CONFIG_CLIEND_SECRET,
    OPTION_ADJUSTED_DAYS,
    FRANCE_TZ,
    API_VALUE_BLUE,
    API_VALUE_WHITE,
    API_VALUE_RED,
)


# ============================================================================
# Hypothesis Strategies
# ============================================================================

# Strategy for valid hours (0-23)
hour_strategy = st.integers(min_value=0, max_value=23)

# Strategy for Tempo colors
color_strategy = st.sampled_from([API_VALUE_BLUE, API_VALUE_WHITE, API_VALUE_RED])

# Strategy for datetimes in France timezone
france_datetime_strategy = st.datetimes(
    min_value=datetime.datetime(2020, 1, 1),
    max_value=datetime.datetime(2030, 12, 31),
).map(lambda dt: dt.replace(tzinfo=FRANCE_TZ))

# Strategy for dates
date_strategy = st.dates(
    min_value=datetime.date(2020, 1, 1),
    max_value=datetime.date(2030, 12, 31),
)


# ============================================================================
# Home Assistant Mocks
# ============================================================================

@pytest.fixture
def mock_hass():
    """Create a mock Home Assistant instance."""
    hass = MagicMock()
    hass.data = {DOMAIN: {}}
    hass.states = MagicMock()
    hass.services = MagicMock()
    hass.services.async_call = AsyncMock()
    hass.bus = MagicMock()
    hass.bus.async_listen_once = MagicMock()
    hass.config = MagicMock()
    hass.config_entries = MagicMock()
    hass.config_entries.async_forward_entry_setups = AsyncMock(return_value=True)
    hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)
    hass.async_add_executor_job = AsyncMock()
    return hass


@pytest.fixture
def mock_config_entry():
    """Create a mock ConfigEntry."""
    entry = MagicMock()
    entry.entry_id = "test_entry_id"
    entry.title = "Test RTE Tempo"
    entry.data = {
        CONFIG_CLIENT_ID: "test_client_id",
        CONFIG_CLIEND_SECRET: "test_client_secret",
    }
    entry.options = {OPTION_ADJUSTED_DAYS: False}
    entry.async_on_unload = MagicMock()
    return entry


@pytest.fixture
def mock_api_worker():
    """Create a mock APIWorker with sample data."""
    worker = MagicMock()
    worker.adjusted_days = False
    
    # Create sample TempoDay data
    now = datetime.datetime.now(FRANCE_TZ)
    today = now.date()
    
    # Adjusted days (datetime-based)
    adjusted_days = [
        TempoDay(
            Start=datetime.datetime(today.year, today.month, today.day, 6, tzinfo=FRANCE_TZ),
            End=datetime.datetime(today.year, today.month, today.day, 6, tzinfo=FRANCE_TZ) + datetime.timedelta(days=1),
            Value=API_VALUE_BLUE,
            Updated=now,
        ),
        TempoDay(
            Start=datetime.datetime(today.year, today.month, today.day, 6, tzinfo=FRANCE_TZ) + datetime.timedelta(days=1),
            End=datetime.datetime(today.year, today.month, today.day, 6, tzinfo=FRANCE_TZ) + datetime.timedelta(days=2),
            Value=API_VALUE_WHITE,
            Updated=now,
        ),
    ]
    
    # Regular days (date-based)
    regular_days = [
        TempoDay(
            Start=today,
            End=today + datetime.timedelta(days=1),
            Value=API_VALUE_BLUE,
            Updated=now,
        ),
        TempoDay(
            Start=today + datetime.timedelta(days=1),
            End=today + datetime.timedelta(days=2),
            Value=API_VALUE_WHITE,
            Updated=now,
        ),
    ]
    
    worker.get_adjusted_days.return_value = adjusted_days
    worker.get_regular_days.return_value = regular_days
    worker.get_calendar_days.return_value = regular_days
    worker.start = MagicMock()
    worker.signalstop = MagicMock()
    worker.update_options = MagicMock()
    
    return worker


@pytest.fixture
def mock_add_entities():
    """Create a mock AddEntitiesCallback."""
    return MagicMock()


# ============================================================================
# Forecast Fixtures (existing)
# ============================================================================

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
        ForecastDay(
            date=datetime.date(2025, 1, 17),
            color="rouge",
            probability=0.45,
        ),
    ]


@pytest.fixture
def sunday_forecast():
    """Sunday forecast (should be blue with D indicator)."""
    return ForecastDay(
        date=datetime.date(2025, 1, 19),  # Sunday
        color="bleu",
        probability=None,
        indicator="D",
    )


@pytest.fixture
def holiday_forecast():
    """Holiday forecast (should be blue with F indicator)."""
    return ForecastDay(
        date=datetime.date(2025, 1, 1),  # New Year's Day
        color="bleu",
        probability=None,
        indicator="F",
    )


# ============================================================================
# TempoDay Fixtures
# ============================================================================

@pytest.fixture
def sample_tempo_days():
    """Create sample TempoDay list for testing."""
    now = datetime.datetime.now(FRANCE_TZ)
    base_date = datetime.date(2025, 1, 15)
    
    return [
        TempoDay(
            Start=base_date,
            End=base_date + datetime.timedelta(days=1),
            Value=API_VALUE_BLUE,
            Updated=now,
        ),
        TempoDay(
            Start=base_date + datetime.timedelta(days=1),
            End=base_date + datetime.timedelta(days=2),
            Value=API_VALUE_WHITE,
            Updated=now,
        ),
        TempoDay(
            Start=base_date + datetime.timedelta(days=2),
            End=base_date + datetime.timedelta(days=3),
            Value=API_VALUE_RED,
            Updated=now,
        ),
    ]


@pytest.fixture
def sample_tempo_days_datetime():
    """Create sample TempoDay list with datetime (adjusted) for testing."""
    now = datetime.datetime.now(FRANCE_TZ)
    base_dt = datetime.datetime(2025, 1, 15, 6, 0, 0, tzinfo=FRANCE_TZ)
    
    return [
        TempoDay(
            Start=base_dt,
            End=base_dt + datetime.timedelta(days=1),
            Value=API_VALUE_BLUE,
            Updated=now,
        ),
        TempoDay(
            Start=base_dt + datetime.timedelta(days=1),
            End=base_dt + datetime.timedelta(days=2),
            Value=API_VALUE_WHITE,
            Updated=now,
        ),
        TempoDay(
            Start=base_dt + datetime.timedelta(days=2),
            End=base_dt + datetime.timedelta(days=3),
            Value=API_VALUE_RED,
            Updated=now,
        ),
    ]
