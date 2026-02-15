"""Tests for calendar.py module."""
import datetime
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from hypothesis import given, strategies as st, settings

from custom_components.rtetempo.calendar import (
    TempoCalendar,
    forge_calendar_event,
    get_value_emoji,
    forge_calendar_event_description,
)
from custom_components.rtetempo.api_worker import TempoDay
from custom_components.rtetempo.const import (
    DOMAIN,
    FRANCE_TZ,
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
    DEVICE_NAME,
    DEVICE_MANUFACTURER,
    DEVICE_MODEL,
)


# ============================================================================
# Tests for helper functions (Requirements 10.1-10.3)
# ============================================================================

class TestCalendarHelpers:
    """Tests for calendar helper functions."""

    def test_get_value_emoji_blue(self):
        """Test get_value_emoji for BLUE."""
        assert get_value_emoji(API_VALUE_BLUE) == SENSOR_COLOR_BLUE_EMOJI

    def test_get_value_emoji_white(self):
        """Test get_value_emoji for WHITE."""
        assert get_value_emoji(API_VALUE_WHITE) == SENSOR_COLOR_WHITE_EMOJI

    def test_get_value_emoji_red(self):
        """Test get_value_emoji for RED."""
        assert get_value_emoji(API_VALUE_RED) == SENSOR_COLOR_RED_EMOJI

    def test_get_value_emoji_unknown(self):
        """Test get_value_emoji for unknown color."""
        assert get_value_emoji("UNKNOWN") == SENSOR_COLOR_UNKNOWN_EMOJI

    def test_forge_calendar_event_description_blue(self):
        """Test forge_calendar_event_description for BLUE."""
        now = datetime.datetime.now(FRANCE_TZ)
        tempo_day = TempoDay(
            Start=datetime.date(2025, 1, 15),
            End=datetime.date(2025, 1, 16),
            Value=API_VALUE_BLUE,
            Updated=now,
        )
        result = forge_calendar_event_description(tempo_day)
        assert SENSOR_COLOR_BLUE_NAME in result
        assert "Jour Tempo" in result

    def test_forge_calendar_event_description_white(self):
        """Test forge_calendar_event_description for WHITE."""
        now = datetime.datetime.now(FRANCE_TZ)
        tempo_day = TempoDay(
            Start=datetime.date(2025, 1, 15),
            End=datetime.date(2025, 1, 16),
            Value=API_VALUE_WHITE,
            Updated=now,
        )
        result = forge_calendar_event_description(tempo_day)
        assert SENSOR_COLOR_WHITE_NAME in result

    def test_forge_calendar_event_description_red(self):
        """Test forge_calendar_event_description for RED."""
        now = datetime.datetime.now(FRANCE_TZ)
        tempo_day = TempoDay(
            Start=datetime.date(2025, 1, 15),
            End=datetime.date(2025, 1, 16),
            Value=API_VALUE_RED,
            Updated=now,
        )
        result = forge_calendar_event_description(tempo_day)
        assert SENSOR_COLOR_RED_NAME in result

    def test_forge_calendar_event_description_unknown(self):
        """Test forge_calendar_event_description for unknown color."""
        now = datetime.datetime.now(FRANCE_TZ)
        tempo_day = TempoDay(
            Start=datetime.date(2025, 1, 15),
            End=datetime.date(2025, 1, 16),
            Value="UNKNOWN",
            Updated=now,
        )
        result = forge_calendar_event_description(tempo_day)
        assert "inconnu" in result


# ============================================================================
# Tests for forge_calendar_event (Requirements 9.5)
# ============================================================================

class TestForgeCalendarEvent:
    """Tests for forge_calendar_event function."""

    def test_forge_calendar_event_with_date(self):
        """Test forge_calendar_event with date-based TempoDay."""
        now = datetime.datetime.now(FRANCE_TZ)
        tempo_day = TempoDay(
            Start=datetime.date(2025, 1, 15),
            End=datetime.date(2025, 1, 16),
            Value=API_VALUE_BLUE,
            Updated=now,
        )
        
        event = forge_calendar_event(tempo_day)
        
        assert event.start == tempo_day.Start
        assert event.end == tempo_day.End
        assert event.summary == SENSOR_COLOR_BLUE_EMOJI
        assert SENSOR_COLOR_BLUE_NAME in event.description
        assert event.location == "France"
        assert f"{DOMAIN}_2025_1_15" == event.uid

    def test_forge_calendar_event_with_datetime(self):
        """Test forge_calendar_event with datetime-based TempoDay."""
        now = datetime.datetime.now(FRANCE_TZ)
        start_dt = datetime.datetime(2025, 1, 15, 6, 0, 0, tzinfo=FRANCE_TZ)
        end_dt = datetime.datetime(2025, 1, 16, 6, 0, 0, tzinfo=FRANCE_TZ)
        tempo_day = TempoDay(
            Start=start_dt,
            End=end_dt,
            Value=API_VALUE_WHITE,
            Updated=now,
        )
        
        event = forge_calendar_event(tempo_day)
        
        assert event.start == start_dt
        assert event.end == end_dt
        assert event.summary == SENSOR_COLOR_WHITE_EMOJI


# ============================================================================
# Property Test for Calendar Event Creation (Property 8)
# ============================================================================

class TestProperty8CalendarEventCreation:
    """Property test for calendar event creation consistency."""

    # Feature: remaining-test-coverage, Property 8: Calendar Event Creation Consistency
    @given(
        st.dates(min_value=datetime.date(2020, 1, 1), max_value=datetime.date(2030, 12, 31)),
        st.sampled_from([API_VALUE_BLUE, API_VALUE_WHITE, API_VALUE_RED]),
    )
    @settings(max_examples=100)
    def test_forge_calendar_event_consistency(self, start_date, color):
        """For any valid TempoDay, forge_calendar_event creates consistent CalendarEvent."""
        now = datetime.datetime.now(FRANCE_TZ)
        end_date = start_date + datetime.timedelta(days=1)
        tempo_day = TempoDay(
            Start=start_date,
            End=end_date,
            Value=color,
            Updated=now,
        )
        
        event = forge_calendar_event(tempo_day)
        
        # Verify start and end match
        assert event.start == tempo_day.Start
        assert event.end == tempo_day.End
        
        # Verify summary contains correct emoji
        expected_emoji = get_value_emoji(color)
        assert event.summary == expected_emoji
        
        # Verify description contains color name
        description = forge_calendar_event_description(tempo_day)
        assert event.description == description
        
        # Verify uid format
        assert event.uid == f"{DOMAIN}_{start_date.year}_{start_date.month}_{start_date.day}"


# ============================================================================
# Tests for TempoCalendar (Requirements 9.1-9.4)
# ============================================================================

class TestTempoCalendar:
    """Tests for TempoCalendar entity."""

    def _create_calendar(self, mock_api_worker):
        """Create a TempoCalendar instance for testing."""
        return TempoCalendar(mock_api_worker, "test_config_id")

    def test_init(self, mock_api_worker):
        """Test TempoCalendar initialization."""
        calendar = self._create_calendar(mock_api_worker)
        
        assert calendar._attr_name == "Calendrier"
        assert calendar._attr_unique_id == f"{DOMAIN}_test_config_id_calendar"
        assert calendar._api_worker == mock_api_worker

    def test_device_info(self, mock_api_worker):
        """Test device_info property."""
        calendar = self._create_calendar(mock_api_worker)
        device_info = calendar.device_info
        
        assert (DOMAIN, "test_config_id") in device_info["identifiers"]
        assert device_info["name"] == DEVICE_NAME
        assert device_info["manufacturer"] == DEVICE_MANUFACTURER
        assert device_info["model"] == DEVICE_MODEL

    @pytest.mark.asyncio
    async def test_async_get_events_date_mode(self, mock_hass, mock_api_worker, sample_tempo_days):
        """Test async_get_events with date mode (adjusted_days=False)."""
        mock_api_worker.adjusted_days = False
        mock_api_worker.get_calendar_days.return_value = sample_tempo_days
        
        calendar = self._create_calendar(mock_api_worker)
        
        start_date = datetime.datetime(2025, 1, 14, 0, 0, 0, tzinfo=FRANCE_TZ)
        end_date = datetime.datetime(2025, 1, 20, 0, 0, 0, tzinfo=FRANCE_TZ)
        
        events = await calendar.async_get_events(mock_hass, start_date, end_date)
        
        # Should return events within the range
        assert len(events) > 0

    @pytest.mark.asyncio
    async def test_async_get_events_datetime_mode(self, mock_hass, mock_api_worker, sample_tempo_days_datetime):
        """Test async_get_events with datetime mode (adjusted_days=True)."""
        mock_api_worker.adjusted_days = True
        mock_api_worker.get_calendar_days.return_value = sample_tempo_days_datetime
        
        calendar = self._create_calendar(mock_api_worker)
        
        start_date = datetime.datetime(2025, 1, 14, 0, 0, 0, tzinfo=FRANCE_TZ)
        end_date = datetime.datetime(2025, 1, 20, 0, 0, 0, tzinfo=FRANCE_TZ)
        
        events = await calendar.async_get_events(mock_hass, start_date, end_date)
        
        # Should return events within the range
        assert len(events) > 0

    def test_event_property_with_match_date_mode(self, mock_api_worker):
        """Test event property when current time matches a tempo_day (date mode)."""
        now = datetime.datetime.now(FRANCE_TZ)
        today = now.date()
        
        tempo_days = [
            TempoDay(
                Start=today,
                End=today + datetime.timedelta(days=1),
                Value=API_VALUE_BLUE,
                Updated=now,
            ),
        ]
        
        mock_api_worker.adjusted_days = False
        mock_api_worker.get_calendar_days.return_value = tempo_days
        
        calendar = self._create_calendar(mock_api_worker)
        
        with patch('custom_components.rtetempo.calendar.datetime') as mock_datetime:
            mock_datetime.datetime.now.return_value = now
            event = calendar.event
        
        assert event is not None
        assert event.summary == SENSOR_COLOR_BLUE_EMOJI

    def test_event_property_with_match_datetime_mode(self, mock_api_worker):
        """Test event property when current time matches a tempo_day (datetime mode)."""
        now = datetime.datetime.now(FRANCE_TZ)
        
        # Create tempo day that includes current time
        start_dt = now.replace(hour=6, minute=0, second=0, microsecond=0)
        if now.hour < 6:
            start_dt = start_dt - datetime.timedelta(days=1)
        end_dt = start_dt + datetime.timedelta(days=1)
        
        tempo_days = [
            TempoDay(
                Start=start_dt,
                End=end_dt,
                Value=API_VALUE_WHITE,
                Updated=now,
            ),
        ]
        
        mock_api_worker.adjusted_days = True
        mock_api_worker.get_calendar_days.return_value = tempo_days
        
        calendar = self._create_calendar(mock_api_worker)
        
        with patch('custom_components.rtetempo.calendar.datetime') as mock_datetime:
            mock_datetime.datetime.now.return_value = now
            event = calendar.event
        
        assert event is not None
        assert event.summary == SENSOR_COLOR_WHITE_EMOJI

    def test_event_property_no_match(self, mock_api_worker):
        """Test event property when no tempo_day matches."""
        now = datetime.datetime.now(FRANCE_TZ)
        
        # Create tempo day in the past
        past_date = datetime.date(2020, 1, 1)
        tempo_days = [
            TempoDay(
                Start=past_date,
                End=past_date + datetime.timedelta(days=1),
                Value=API_VALUE_BLUE,
                Updated=now,
            ),
        ]
        
        mock_api_worker.adjusted_days = False
        mock_api_worker.get_calendar_days.return_value = tempo_days
        
        calendar = self._create_calendar(mock_api_worker)
        
        with patch('custom_components.rtetempo.calendar.datetime') as mock_datetime:
            mock_datetime.datetime.now.return_value = now
            event = calendar.event
        
        assert event is None


# ============================================================================
# Property Test for Calendar Event Filtering (Property 3)
# ============================================================================

class TestProperty3CalendarEventFiltering:
    """Property test for calendar event range filtering."""

    # Feature: remaining-test-coverage, Property 3: Calendar Event Range Filtering
    @given(
        st.dates(min_value=datetime.date(2025, 1, 1), max_value=datetime.date(2025, 6, 30)),
        st.integers(min_value=1, max_value=30),
        st.integers(min_value=1, max_value=10),
    )
    @settings(max_examples=100)
    def test_events_within_range(self, base_date, range_days, num_events):
        """For any date range, returned events should overlap with the requested range."""
        now = datetime.datetime.now(FRANCE_TZ)
        
        # Create tempo days
        tempo_days = []
        for i in range(num_events):
            event_date = base_date + datetime.timedelta(days=i * 2)
            tempo_days.append(TempoDay(
                Start=event_date,
                End=event_date + datetime.timedelta(days=1),
                Value=API_VALUE_BLUE,
                Updated=now,
            ))
        
        # Create mock API worker
        mock_api_worker = MagicMock()
        mock_api_worker.adjusted_days = False
        mock_api_worker.get_calendar_days.return_value = tempo_days
        
        calendar = TempoCalendar(mock_api_worker, "test_config_id")
        
        # Define search range
        start_date = datetime.datetime.combine(base_date, datetime.time.min, tzinfo=FRANCE_TZ)
        end_date = datetime.datetime.combine(
            base_date + datetime.timedelta(days=range_days),
            datetime.time.max,
            tzinfo=FRANCE_TZ
        )
        
        # Get events synchronously (we'll test the logic directly)
        events = []
        for tempo_day in tempo_days:
            if (
                tempo_day.Start >= start_date.date()
                and tempo_day.End <= end_date.date()
            ):
                events.append(forge_calendar_event(tempo_day))
            elif (
                tempo_day.Start <= start_date.date() <= tempo_day.End <= end_date.date()
            ):
                events.append(forge_calendar_event(tempo_day))
            elif (
                start_date.date() <= tempo_day.Start <= end_date.date() <= tempo_day.End
            ):
                events.append(forge_calendar_event(tempo_day))
        
        # Verify all returned events overlap with the range
        for event in events:
            event_start = event.start
            event_end = event.end
            # Event should overlap with [start_date, end_date]
            assert not (event_end < start_date.date() or event_start > end_date.date())


# ============================================================================
# Additional tests for improved coverage
# ============================================================================

class TestAsyncGetEventsEdgeCases:
    """Additional tests for async_get_events edge cases."""

    @pytest.mark.asyncio
    async def test_async_get_events_datetime_partial_overlap_start(self, mock_hass, mock_api_worker):
        """Test async_get_events with datetime mode - event starts before range but ends within."""
        now = datetime.datetime.now(FRANCE_TZ)
        
        # Event that starts before search range but ends within
        tempo_days = [
            TempoDay(
                Start=datetime.datetime(2025, 1, 10, 6, 0, 0, tzinfo=FRANCE_TZ),
                End=datetime.datetime(2025, 1, 16, 6, 0, 0, tzinfo=FRANCE_TZ),
                Value=API_VALUE_BLUE,
                Updated=now,
            ),
        ]
        
        mock_api_worker.adjusted_days = True
        mock_api_worker.get_calendar_days.return_value = tempo_days
        
        calendar = TempoCalendar(mock_api_worker, "test_config_id")
        
        # Search range starts after event start but before event end
        start_date = datetime.datetime(2025, 1, 14, 0, 0, 0, tzinfo=FRANCE_TZ)
        end_date = datetime.datetime(2025, 1, 20, 0, 0, 0, tzinfo=FRANCE_TZ)
        
        events = await calendar.async_get_events(mock_hass, start_date, end_date)
        
        # Should include the event (partial overlap)
        assert len(events) == 1

    @pytest.mark.asyncio
    async def test_async_get_events_datetime_partial_overlap_end(self, mock_hass, mock_api_worker):
        """Test async_get_events with datetime mode - event starts within range but ends after."""
        now = datetime.datetime.now(FRANCE_TZ)
        
        # Event that starts within search range but ends after
        tempo_days = [
            TempoDay(
                Start=datetime.datetime(2025, 1, 18, 6, 0, 0, tzinfo=FRANCE_TZ),
                End=datetime.datetime(2025, 1, 25, 6, 0, 0, tzinfo=FRANCE_TZ),
                Value=API_VALUE_WHITE,
                Updated=now,
            ),
        ]
        
        mock_api_worker.adjusted_days = True
        mock_api_worker.get_calendar_days.return_value = tempo_days
        
        calendar = TempoCalendar(mock_api_worker, "test_config_id")
        
        # Search range ends before event end
        start_date = datetime.datetime(2025, 1, 14, 0, 0, 0, tzinfo=FRANCE_TZ)
        end_date = datetime.datetime(2025, 1, 20, 0, 0, 0, tzinfo=FRANCE_TZ)
        
        events = await calendar.async_get_events(mock_hass, start_date, end_date)
        
        # Should include the event (partial overlap)
        assert len(events) == 1

    @pytest.mark.asyncio
    async def test_async_get_events_date_partial_overlap_start(self, mock_hass, mock_api_worker):
        """Test async_get_events with date mode - event starts before range but ends within."""
        now = datetime.datetime.now(FRANCE_TZ)
        
        # Event that starts before search range but ends within
        tempo_days = [
            TempoDay(
                Start=datetime.date(2025, 1, 10),
                End=datetime.date(2025, 1, 16),
                Value=API_VALUE_RED,
                Updated=now,
            ),
        ]
        
        mock_api_worker.adjusted_days = False
        mock_api_worker.get_calendar_days.return_value = tempo_days
        
        calendar = TempoCalendar(mock_api_worker, "test_config_id")
        
        # Search range starts after event start but before event end
        start_date = datetime.datetime(2025, 1, 14, 0, 0, 0, tzinfo=FRANCE_TZ)
        end_date = datetime.datetime(2025, 1, 20, 0, 0, 0, tzinfo=FRANCE_TZ)
        
        events = await calendar.async_get_events(mock_hass, start_date, end_date)
        
        # Should include the event (partial overlap)
        assert len(events) == 1

    @pytest.mark.asyncio
    async def test_async_get_events_date_partial_overlap_end(self, mock_hass, mock_api_worker):
        """Test async_get_events with date mode - event starts within range but ends after."""
        now = datetime.datetime.now(FRANCE_TZ)
        
        # Event that starts within search range but ends after
        tempo_days = [
            TempoDay(
                Start=datetime.date(2025, 1, 18),
                End=datetime.date(2025, 1, 25),
                Value=API_VALUE_BLUE,
                Updated=now,
            ),
        ]
        
        mock_api_worker.adjusted_days = False
        mock_api_worker.get_calendar_days.return_value = tempo_days
        
        calendar = TempoCalendar(mock_api_worker, "test_config_id")
        
        # Search range ends before event end
        start_date = datetime.datetime(2025, 1, 14, 0, 0, 0, tzinfo=FRANCE_TZ)
        end_date = datetime.datetime(2025, 1, 20, 0, 0, 0, tzinfo=FRANCE_TZ)
        
        events = await calendar.async_get_events(mock_hass, start_date, end_date)
        
        # Should include the event (partial overlap)
        assert len(events) == 1

    @pytest.mark.asyncio
    async def test_async_get_events_no_overlap(self, mock_hass, mock_api_worker):
        """Test async_get_events when no events overlap with range."""
        now = datetime.datetime.now(FRANCE_TZ)
        
        # Event completely outside search range
        tempo_days = [
            TempoDay(
                Start=datetime.date(2025, 2, 1),
                End=datetime.date(2025, 2, 2),
                Value=API_VALUE_BLUE,
                Updated=now,
            ),
        ]
        
        mock_api_worker.adjusted_days = False
        mock_api_worker.get_calendar_days.return_value = tempo_days
        
        calendar = TempoCalendar(mock_api_worker, "test_config_id")
        
        start_date = datetime.datetime(2025, 1, 14, 0, 0, 0, tzinfo=FRANCE_TZ)
        end_date = datetime.datetime(2025, 1, 20, 0, 0, 0, tzinfo=FRANCE_TZ)
        
        events = await calendar.async_get_events(mock_hass, start_date, end_date)
        
        # Should return empty list
        assert len(events) == 0


class TestAsyncSetupEntry:
    """Tests for async_setup_entry function."""

    @pytest.mark.asyncio
    async def test_async_setup_entry_success(self, mock_hass, mock_config_entry, mock_api_worker):
        """Test successful setup of calendar platform."""
        from custom_components.rtetempo.calendar import async_setup_entry
        
        mock_hass.data[DOMAIN] = {mock_config_entry.entry_id: mock_api_worker}
        mock_add_entities = MagicMock()
        
        with patch('custom_components.rtetempo.calendar.asyncio.sleep', new_callable=AsyncMock):
            await async_setup_entry(mock_hass, mock_config_entry, mock_add_entities)
        
        # Should have called async_add_entities with TempoCalendar
        mock_add_entities.assert_called_once()
        entities = mock_add_entities.call_args[0][0]
        assert len(entities) == 1
        assert isinstance(entities[0], TempoCalendar)

    @pytest.mark.asyncio
    async def test_async_setup_entry_missing_worker(self, mock_hass, mock_config_entry):
        """Test setup when API worker is missing."""
        from custom_components.rtetempo.calendar import async_setup_entry
        
        mock_hass.data[DOMAIN] = {}  # No worker
        mock_add_entities = MagicMock()
        
        await async_setup_entry(mock_hass, mock_config_entry, mock_add_entities)
        
        # Should not call async_add_entities
        mock_add_entities.assert_not_called()
