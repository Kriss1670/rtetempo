"""Tests for the accuracy analysis module.

Tests the AccuracyAnalyzer class with multi-horizon analysis.
Validates forecast history tracking requirements.
"""
from __future__ import annotations

import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.rtetempo.accuracy import (
    AccuracyAnalyzer,
    HorizonForecast,
    FORECAST_SENSORS,
    CURRENT_COLOR_SENSOR,
)


class TestHorizonForecast:
    """Tests for HorizonForecast dataclass."""
    
    def test_default_values(self):
        """Test default values."""
        hf = HorizonForecast()
        assert hf.color is None
        assert hf.result == "-"
    
    def test_with_values(self):
        """Test with explicit values."""
        hf = HorizonForecast(color="bleu", result="✓")
        assert hf.color == "bleu"
        assert hf.result == "✓"
    
    def test_to_dict(self):
        """Test conversion to dict."""
        hf = HorizonForecast(color="rouge", result="✗")
        d = hf.to_dict()
        assert d == {"color": "rouge", "result": "✗"}


class TestAccuracyAnalyzerIsExcluded:
    """Tests for is_excluded method."""
    
    @pytest.fixture
    def analyzer(self):
        """Create analyzer with mock hass."""
        mock_hass = MagicMock()
        return AccuracyAnalyzer(mock_hass)
    
    def test_sunday_excluded(self, analyzer):
        """Sundays should be excluded."""
        # December 29, 2024 is a Sunday
        assert analyzer.is_excluded(datetime.date(2024, 12, 29)) is True
        # January 5, 2025 is a Sunday
        assert analyzer.is_excluded(datetime.date(2025, 1, 5)) is True
    
    def test_fixed_holiday_excluded(self, analyzer):
        """Fixed French holidays should be excluded."""
        # Christmas
        assert analyzer.is_excluded(datetime.date(2024, 12, 25)) is True
        # New Year
        assert analyzer.is_excluded(datetime.date(2025, 1, 1)) is True
        # Bastille Day
        assert analyzer.is_excluded(datetime.date(2025, 7, 14)) is True
    
    def test_movable_holiday_excluded(self, analyzer):
        """Movable French holidays should be excluded."""
        # Easter Monday 2025 (April 21)
        assert analyzer.is_excluded(datetime.date(2025, 4, 21)) is True
        # Ascension 2025 (May 29)
        assert analyzer.is_excluded(datetime.date(2025, 5, 29)) is True
    
    def test_regular_weekday_not_excluded(self, analyzer):
        """Regular weekdays should not be excluded."""
        # Monday December 30, 2024
        assert analyzer.is_excluded(datetime.date(2024, 12, 30)) is False
        # Tuesday December 31, 2024
        assert analyzer.is_excluded(datetime.date(2024, 12, 31)) is False
    
    def test_saturday_not_excluded(self, analyzer):
        """Saturdays (non-holiday) should not be excluded."""
        # December 28, 2024 is a Saturday
        assert analyzer.is_excluded(datetime.date(2024, 12, 28)) is False


class TestAccuracyAnalyzerCompare:
    """Tests for _compare method."""
    
    @pytest.fixture
    def analyzer(self):
        """Create analyzer with mock hass."""
        mock_hass = MagicMock()
        return AccuracyAnalyzer(mock_hass)
    
    def test_correct_prediction(self, analyzer):
        """Test correct prediction returns ✓."""
        result = analyzer._compare("bleu", "bleu", datetime.date(2024, 12, 30))
        assert result == "✓"
    
    def test_incorrect_prediction(self, analyzer):
        """Test incorrect prediction returns ✗."""
        result = analyzer._compare("blanc", "rouge", datetime.date(2024, 12, 30))
        assert result == "✗"
    
    def test_no_prediction(self, analyzer):
        """Test missing prediction returns -."""
        result = analyzer._compare(None, "bleu", datetime.date(2024, 12, 30))
        assert result == "-"
    
    def test_excluded_day(self, analyzer):
        """Test excluded day returns - even if prediction exists."""
        # December 29, 2024 is a Sunday
        result = analyzer._compare("bleu", "bleu", datetime.date(2024, 12, 29))
        assert result == "-"


class TestCalculateHorizonAccuracy:
    """Tests for calculate_horizon_accuracy method."""
    
    @pytest.fixture
    def analyzer(self):
        """Create analyzer with mock hass."""
        mock_hass = MagicMock()
        return AccuracyAnalyzer(mock_hass)
    
    def test_all_correct(self, analyzer):
        """Test 100% accuracy."""
        past_matrix = [
            {"date": "2024-12-30", "j2": {"color": "bleu", "result": "✓"}},
            {"date": "2024-12-31", "j2": {"color": "blanc", "result": "✓"}},
        ]
        accuracy = analyzer.calculate_horizon_accuracy(past_matrix, 2)
        assert accuracy == 100.0
    
    def test_all_incorrect(self, analyzer):
        """Test 0% accuracy."""
        past_matrix = [
            {"date": "2024-12-30", "j2": {"color": "bleu", "result": "✗"}},
            {"date": "2024-12-31", "j2": {"color": "blanc", "result": "✗"}},
        ]
        accuracy = analyzer.calculate_horizon_accuracy(past_matrix, 2)
        assert accuracy == 0.0
    
    def test_mixed_results(self, analyzer):
        """Test 50% accuracy."""
        past_matrix = [
            {"date": "2024-12-30", "j2": {"color": "bleu", "result": "✓"}},
            {"date": "2024-12-31", "j2": {"color": "blanc", "result": "✗"}},
        ]
        accuracy = analyzer.calculate_horizon_accuracy(past_matrix, 2)
        assert accuracy == 50.0
    
    def test_excludes_dashes(self, analyzer):
        """Test that excluded days (result=-) are not counted."""
        past_matrix = [
            {"date": "2024-12-29", "j2": {"color": "rouge", "result": "-"}},  # Sunday
            {"date": "2024-12-30", "j2": {"color": "bleu", "result": "✓"}},
        ]
        accuracy = analyzer.calculate_horizon_accuracy(past_matrix, 2)
        # Only 1 valid result, which is correct
        assert accuracy == 100.0
    
    def test_empty_matrix(self, analyzer):
        """Test empty matrix returns 0."""
        accuracy = analyzer.calculate_horizon_accuracy([], 2)
        assert accuracy == 0.0
    
    def test_only_excluded(self, analyzer):
        """Test only excluded days returns 0."""
        past_matrix = [
            {"date": "2024-12-29", "j2": {"color": "rouge", "result": "-"}},
        ]
        accuracy = analyzer.calculate_horizon_accuracy(past_matrix, 2)
        assert accuracy == 0.0
    
    def test_different_horizons(self, analyzer):
        """Test accuracy calculation for different horizons."""
        past_matrix = [
            {
                "date": "2024-12-30",
                "j7": {"color": "bleu", "result": "✗"},
                "j6": {"color": "blanc", "result": "✗"},
                "j5": {"color": "rouge", "result": "✓"},
                "j4": {"color": "rouge", "result": "✓"},
                "j3": {"color": "rouge", "result": "✓"},
                "j2": {"color": "rouge", "result": "✓"},
            },
        ]
        assert analyzer.calculate_horizon_accuracy(past_matrix, 7) == 0.0
        assert analyzer.calculate_horizon_accuracy(past_matrix, 6) == 0.0
        assert analyzer.calculate_horizon_accuracy(past_matrix, 5) == 100.0
        assert analyzer.calculate_horizon_accuracy(past_matrix, 2) == 100.0


class TestForecastSensorsConfig:
    """Tests for sensor configuration constants."""
    
    def test_forecast_sensors_horizons(self):
        """Test that forecast sensors cover J-2 to J-7."""
        assert set(FORECAST_SENSORS.keys()) == {2, 3, 4, 5, 6, 7}
    
    def test_forecast_sensor_naming(self):
        """Test sensor naming convention."""
        for horizon, sensor_id in FORECAST_SENSORS.items():
            assert f"j{horizon}" in sensor_id
            assert sensor_id.startswith("sensor.rte_tempo_forecast_")
    
    def test_current_color_sensor(self):
        """Test current color sensor is defined."""
        assert CURRENT_COLOR_SENSOR == "sensor.rte_tempo_couleur_actuelle"


class TestBuildPastMatrix:
    """Tests for build_past_matrix method."""
    
    @pytest.fixture
    def analyzer(self):
        """Create analyzer with mock hass."""
        mock_hass = MagicMock()
        return AccuracyAnalyzer(mock_hass)
    
    @pytest.mark.asyncio
    async def test_empty_data(self, analyzer):
        """Test with no forecast or actual data."""
        analyzer.get_forecast_history_by_target_date = AsyncMock(return_value={})
        analyzer.get_actual_colors = AsyncMock(return_value={})
        
        matrix = await analyzer.build_past_matrix(days=30)
        
        assert matrix == []
    
    @pytest.mark.asyncio
    async def test_matrix_structure(self, analyzer):
        """Test matrix has correct structure."""
        today = datetime.date.today()
        yesterday = today - datetime.timedelta(days=1)
        yesterday_str = yesterday.isoformat()
        
        analyzer.get_forecast_history_by_target_date = AsyncMock(return_value={
            yesterday_str: {2: "bleu", 3: "bleu", 4: "blanc", 5: "blanc", 6: "rouge", 7: "rouge"}
        })
        analyzer.get_actual_colors = AsyncMock(return_value={
            yesterday_str: "bleu"
        })
        
        matrix = await analyzer.build_past_matrix(days=30)
        
        assert len(matrix) == 1
        row = matrix[0]
        assert row["date"] == yesterday_str
        assert row["actual"] == "bleu"
        # Check all horizons are present
        for h in [7, 6, 5, 4, 3, 2]:
            assert f"j{h}" in row
            assert "color" in row[f"j{h}"]
            assert "result" in row[f"j{h}"]
    
    @pytest.mark.asyncio
    async def test_correct_comparison(self, analyzer):
        """Test correct/incorrect comparison logic."""
        today = datetime.date.today()
        # Use a Monday to avoid Sunday exclusion
        test_date = today - datetime.timedelta(days=1)
        while test_date.weekday() == 6:  # Skip if Sunday
            test_date -= datetime.timedelta(days=1)
        test_date_str = test_date.isoformat()
        
        analyzer.get_forecast_history_by_target_date = AsyncMock(return_value={
            test_date_str: {2: "bleu", 3: "rouge"}  # J-2 correct, J-3 incorrect
        })
        analyzer.get_actual_colors = AsyncMock(return_value={
            test_date_str: "bleu"
        })
        
        matrix = await analyzer.build_past_matrix(days=30)
        
        row = matrix[0]
        assert row["j2"]["result"] == "✓"  # Correct
        assert row["j3"]["result"] == "✗"  # Incorrect
    
    @pytest.mark.asyncio
    async def test_sorted_descending(self, analyzer):
        """Test matrix is sorted by date descending."""
        today = datetime.date.today()
        date1 = today - datetime.timedelta(days=3)
        date2 = today - datetime.timedelta(days=1)
        
        analyzer.get_forecast_history_by_target_date = AsyncMock(return_value={
            date1.isoformat(): {2: "bleu"},
            date2.isoformat(): {2: "rouge"},
        })
        analyzer.get_actual_colors = AsyncMock(return_value={
            date1.isoformat(): "bleu",
            date2.isoformat(): "rouge",
        })
        
        matrix = await analyzer.build_past_matrix(days=30)
        
        assert len(matrix) == 2
        # Most recent first
        assert matrix[0]["date"] == date2.isoformat()
        assert matrix[1]["date"] == date1.isoformat()


class TestBuildFutureMatrix:
    """Tests for build_future_matrix method."""
    
    @pytest.mark.asyncio
    async def test_future_matrix_no_actual_column(self):
        """Test that future matrix doesn't have 'actual' or 'result' keys."""
        mock_hass = MagicMock()
        
        analyzer = AccuracyAnalyzer(mock_hass)
        # Mock the forecast history to return empty (no forecasts yet)
        analyzer.get_forecast_history_by_target_date = AsyncMock(return_value={})
        
        matrix = await analyzer.build_future_matrix()
        
        # Should have 6 rows (J+2 to J+7)
        assert len(matrix) == 6
        
        for row in matrix:
            assert "date" in row
            assert "actual" not in row
            # Check horizons don't have 'result' key
            for h in [7, 6, 5, 4, 3, 2]:
                if f"j{h}" in row:
                    assert "result" not in row[f"j{h}"]
    
    @pytest.mark.asyncio
    async def test_future_matrix_sorted_ascending(self):
        """Test future matrix is sorted by date ascending."""
        mock_hass = MagicMock()
        
        analyzer = AccuracyAnalyzer(mock_hass)
        analyzer.get_forecast_history_by_target_date = AsyncMock(return_value={})
        
        matrix = await analyzer.build_future_matrix()
        
        # Verify ascending order
        dates = [row["date"] for row in matrix]
        assert dates == sorted(dates)
    
    @pytest.mark.asyncio
    async def test_future_matrix_diagonal_pattern(self):
        """Test that future matrix has correct diagonal pattern.
        
        For today = T:
        - J+2 (T+2): only J-2 available (forecast made today)
        - J+3 (T+3): J-3 (today) and J-2 (tomorrow, not yet) -> only J-3
        - J+7 (T+7): only J-7 (today)
        """
        mock_hass = MagicMock()
        today = datetime.date.today()
        
        # Create forecast data with diagonal pattern
        forecasts = {}
        for days_ahead in range(2, 8):
            target_date = today + datetime.timedelta(days=days_ahead)
            date_str = target_date.isoformat()
            # Only the horizon that matches days_ahead should have data
            # (forecast made today for that horizon)
            forecasts[date_str] = {days_ahead: "bleu"}
        
        analyzer = AccuracyAnalyzer(mock_hass)
        analyzer.get_forecast_history_by_target_date = AsyncMock(return_value=forecasts)
        
        matrix = await analyzer.build_future_matrix()
        
        # Check diagonal pattern
        for i, row in enumerate(matrix):
            days_ahead = i + 2  # J+2, J+3, ..., J+7
            
            # The horizon that equals days_ahead should have data
            # (it was forecast today)
            for h in range(7, 1, -1):
                if h == days_ahead:
                    # This horizon was forecast today
                    assert row[f"j{h}"]["color"] == "bleu", f"J+{days_ahead} should have J-{h} forecast"
                elif h > days_ahead:
                    # This horizon would be forecast in the future
                    assert row[f"j{h}"]["color"] is None, f"J+{days_ahead} should NOT have J-{h} forecast"
                else:
                    # This horizon was forecast in the past (before today)
                    # In our test data, we only have today's forecasts
                    assert row[f"j{h}"]["color"] is None


class TestAnalyze:
    """Tests for the main analyze method."""
    
    @pytest.mark.asyncio
    async def test_analyze_returns_all_fields(self):
        """Test analyze returns all expected fields."""
        mock_hass = MagicMock()
        mock_hass.states.get.return_value = None
        
        analyzer = AccuracyAnalyzer(mock_hass)
        analyzer.get_forecast_history_by_target_date = AsyncMock(return_value={})
        analyzer.get_actual_colors = AsyncMock(return_value={})
        
        result = await analyzer.analyze(days=30)
        
        # Check all expected keys
        assert "accuracy_30d" in result
        assert "accuracy_7d" in result
        assert "accuracy_j2" in result
        assert "accuracy_j3" in result
        assert "accuracy_j4" in result
        assert "accuracy_j5" in result
        assert "accuracy_j6" in result
        assert "accuracy_j7" in result
        assert "total_days" in result
        assert "correct_predictions" in result
        assert "incorrect_predictions" in result
        assert "excluded_predictions" in result
        assert "past_matrix" in result
        assert "future_matrix" in result
    
    @pytest.mark.asyncio
    async def test_analyze_accuracy_calculation(self):
        """Test analyze calculates accuracy correctly."""
        mock_hass = MagicMock()
        mock_hass.states.get.return_value = None
        
        today = datetime.date.today()
        # Use dates that are not Sundays
        date1 = today - datetime.timedelta(days=2)
        while date1.weekday() == 6:
            date1 -= datetime.timedelta(days=1)
        date2 = date1 - datetime.timedelta(days=1)
        while date2.weekday() == 6:
            date2 -= datetime.timedelta(days=1)
        
        analyzer = AccuracyAnalyzer(mock_hass)
        analyzer.get_forecast_history_by_target_date = AsyncMock(return_value={
            date1.isoformat(): {2: "bleu"},
            date2.isoformat(): {2: "rouge"},
        })
        analyzer.get_actual_colors = AsyncMock(return_value={
            date1.isoformat(): "bleu",  # Correct
            date2.isoformat(): "bleu",  # Incorrect
        })
        
        result = await analyzer.analyze(days=30)
        
        # 1 correct, 1 incorrect = 50%
        assert result["accuracy_j2"] == 50.0
