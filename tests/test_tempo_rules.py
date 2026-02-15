"""Property-based tests for Tempo rules.

Uses hypothesis to validate correctness properties from the design document.
Each test references the specific property and requirements it validates.
"""
from __future__ import annotations

import datetime

import pytest
from hypothesis import given, settings, strategies as st

# Import real modules for coverage
from custom_components.rtetempo.forecast import ForecastDay
from custom_components.rtetempo.tempo_rules import (
    FIXED_HOLIDAYS,
    compute_easter,
    get_movable_holidays,
    is_french_holiday,
    adjust_forecast_day,
    apply_tempo_rules,
)


# ============================================================================
# Strategies for generating test data
# ============================================================================

# Date strategy: reasonable range for Tempo forecasts
date_strategy = st.dates(
    min_value=datetime.date(2020, 1, 1),
    max_value=datetime.date(2030, 12, 31)
)

# Color strategy: valid Tempo colors
color_strategy = st.sampled_from(["bleu", "blanc", "rouge"])

# Probability strategy: 0.0 to 1.0
probability_strategy = st.floats(min_value=0.0, max_value=1.0, allow_nan=False)


def forecast_strategy(date_strat=date_strategy):
    """Generate random ForecastDay instances."""
    return st.builds(
        ForecastDay,
        date=date_strat,
        color=color_strategy,
        probability=probability_strategy,
        indicator=st.none(),
        source=st.just("open_dpe"),
    )


# Strategy for French holidays only
@st.composite
def french_holiday_strategy(draw):
    """Generate dates that are French holidays."""
    year = draw(st.integers(min_value=2020, max_value=2030))
    
    # Choose between fixed and movable holidays
    if draw(st.booleans()):
        # Fixed holiday
        month, day = draw(st.sampled_from(FIXED_HOLIDAYS))
        return datetime.date(year, month, day)
    else:
        # Movable holiday
        movable = get_movable_holidays(year)
        return draw(st.sampled_from(movable))


# Strategy for Sundays that are NOT holidays
@st.composite
def sunday_non_holiday_strategy(draw):
    """Generate Sundays that are not French holidays."""
    date = draw(date_strategy)
    # Find next Sunday
    days_until_sunday = (6 - date.weekday()) % 7
    sunday = date + datetime.timedelta(days=days_until_sunday)
    
    # Skip if it's a holiday
    if is_french_holiday(sunday):
        # Try another date
        sunday = sunday + datetime.timedelta(days=7)
        if is_french_holiday(sunday):
            sunday = sunday + datetime.timedelta(days=7)
    
    return sunday


# Strategy for Saturdays that are NOT holidays
@st.composite  
def saturday_strategy(draw):
    """Generate Saturdays that are not French holidays."""
    date = draw(date_strategy)
    days_until_saturday = (5 - date.weekday()) % 7
    saturday = date + datetime.timedelta(days=days_until_saturday)
    
    # Skip if it's a holiday (holiday rule takes precedence)
    while is_french_holiday(saturday):
        saturday = saturday + datetime.timedelta(days=7)
    
    return saturday


# Strategy for weekdays (Mon-Fri) that are NOT holidays
@st.composite
def weekday_non_holiday_strategy(draw):
    """Generate weekdays (Mon-Fri) that are not French holidays."""
    date = draw(date_strategy)
    # Ensure it's a weekday
    while date.weekday() >= 5 or is_french_holiday(date):
        date = date + datetime.timedelta(days=1)
    return date


# ============================================================================
# Unit Tests for Holiday Detection
# ============================================================================

class TestHolidayDetection:
    """Unit tests for French holiday detection. Validates: Requirements 2.4"""
    
    def test_fixed_holidays_2025(self):
        """Test fixed holidays for 2025."""
        fixed_2025 = [
            datetime.date(2025, 1, 1),   # Jour de l'An
            datetime.date(2025, 5, 1),   # Fête du Travail
            datetime.date(2025, 5, 8),   # Victoire 1945
            datetime.date(2025, 7, 14),  # Fête Nationale
            datetime.date(2025, 8, 15),  # Assomption
            datetime.date(2025, 11, 1),  # Toussaint
            datetime.date(2025, 11, 11), # Armistice
            datetime.date(2025, 12, 25), # Noël
        ]
        for date in fixed_2025:
            assert is_french_holiday(date), f"{date} should be a holiday"
    
    def test_movable_holidays_2025(self):
        """Test movable holidays for 2025 (Easter is April 20)."""
        # Easter 2025 is April 20
        easter_2025 = datetime.date(2025, 4, 20)
        assert compute_easter(2025) == easter_2025
        
        movable_2025 = [
            datetime.date(2025, 4, 21),  # Lundi de Pâques (Easter + 1)
            datetime.date(2025, 5, 29),  # Ascension (Easter + 39)
            datetime.date(2025, 6, 9),   # Lundi de Pentecôte (Easter + 50)
        ]
        for date in movable_2025:
            assert is_french_holiday(date), f"{date} should be a movable holiday"
    
    def test_movable_holidays_2026(self):
        """Test movable holidays for 2026 (Easter is April 5)."""
        easter_2026 = datetime.date(2026, 4, 5)
        assert compute_easter(2026) == easter_2026
        
        movable_2026 = [
            datetime.date(2026, 4, 6),   # Lundi de Pâques
            datetime.date(2026, 5, 14),  # Ascension
            datetime.date(2026, 5, 25),  # Lundi de Pentecôte
        ]
        for date in movable_2026:
            assert is_french_holiday(date), f"{date} should be a movable holiday"
    
    def test_non_holidays(self):
        """Test that regular days are not holidays."""
        non_holidays = [
            datetime.date(2025, 1, 2),   # Day after New Year
            datetime.date(2025, 7, 15),  # Day after Bastille Day
            datetime.date(2025, 12, 26), # Day after Christmas
            datetime.date(2025, 6, 15),  # Random weekday
        ]
        for date in non_holidays:
            assert not is_french_holiday(date), f"{date} should NOT be a holiday"
    
    def test_epiphany_not_holiday(self):
        """Epiphany (Jan 6) is NOT a French public holiday."""
        assert not is_french_holiday(datetime.date(2025, 1, 6))
        assert not is_french_holiday(datetime.date(2026, 1, 6))


# ============================================================================
# Property-Based Tests
# ============================================================================

class TestProperty1HolidayLikeSaturday:
    """
    Property 1: Holiday Like Saturday (Never Red) with F Indicator
    
    Per EDF Tempo rules: "Red days never take place on the weekends, nor on public holidays."
    
    *For any* forecast where the date is a French holiday (non-Sunday):
    - If original color is "rouge", convert to "blanc" with adjusted probability + indicator "F"
    - If original color is "bleu" or "blanc", keep color + indicator "F"
    
    Note: Sunday holidays are handled by the Sunday rule (always blue + D takes precedence)
    
    **Validates: Requirements 2.1, 2.2, 2.3, 2.5**
    """
    
    @given(
        holiday_date=french_holiday_strategy(),
        color=color_strategy,
        probability=probability_strategy,
    )
    @settings(max_examples=100)
    def test_holiday_never_red_with_f(self, holiday_date, color, probability):
        """Feature: tempo-forecast-rules, Property 1: Holiday Never Red with F Indicator"""
        forecast = ForecastDay(
            date=holiday_date,
            color=color,
            probability=probability,
        )
        
        result = adjust_forecast_day(forecast)
        
        # If it's a Sunday, Sunday rule takes precedence (blue + D)
        if holiday_date.weekday() == 6:
            assert result.color == "bleu", f"Sunday holiday {holiday_date} should be blue"
            assert result.indicator == "D", f"Sunday holiday {holiday_date} should have indicator 'D'"
        else:
            # Non-Sunday holiday: never red, always has F indicator
            assert result.color != "rouge", f"Holiday {holiday_date} should never be red, got {result.color}"
            assert result.indicator == "F", f"Holiday {holiday_date} should have indicator 'F', got {result.indicator}"
            
            # If original was red, should become blanc with adjusted probability
            if color == "rouge":
                assert result.color == "blanc", f"Holiday red should become blanc, got {result.color}"
                # Verify probability conversion logic
                original_prob = probability if probability is not None else 0.0
                if original_prob > 0.6:
                    assert result.probability == 1.0, f"Holiday red with prob > 0.6 should become 1.0, got {result.probability}"
                else:
                    expected_prob = min(original_prob + 0.1, 1.0)
                    assert result.probability == expected_prob, f"Holiday red with prob {original_prob} should become {expected_prob}, got {result.probability}"
            else:
                # bleu or blanc should stay the same with preserved probability
                assert result.color == color, f"Holiday {color} should stay {color}, got {result.color}"
                assert result.probability == probability, f"Holiday {color} should preserve probability {probability}, got {result.probability}"


class TestProperty2SundayAlwaysBlue:
    """
    Property 2: Sunday Always Blue with D Indicator (Non-Holiday)
    
    *For any* forecast where the date is a Sunday and NOT a French holiday,
    the adjusted forecast SHALL have color "bleu" and indicator "D",
    regardless of the original color and probability.
    
    **Validates: Requirements 1.1, 1.2, 1.3**
    """
    
    @given(
        sunday_date=sunday_non_holiday_strategy(),
        color=color_strategy,
        probability=probability_strategy,
    )
    @settings(max_examples=100)
    def test_sunday_non_holiday_blue_with_d(self, sunday_date, color, probability):
        """Feature: tempo-forecast-rules, Property 2: Sunday Always Blue with D Indicator"""
        # Verify precondition
        assert sunday_date.weekday() == 6, "Date must be Sunday"
        assert not is_french_holiday(sunday_date), "Date must not be a holiday"
        
        forecast = ForecastDay(
            date=sunday_date,
            color=color,
            probability=probability,
        )
        
        result = adjust_forecast_day(forecast)
        
        assert result.color == "bleu", f"Sunday {sunday_date} should be blue, got {result.color}"
        assert result.indicator == "D", f"Sunday {sunday_date} should have indicator 'D', got {result.indicator}"


class TestProperty3SaturdayRedConversion:
    """
    Property 3: Saturday Red Conversion
    
    *For any* forecast where the date is a Saturday and the original color is "rouge":
    - If original probability > 0.6, the adjusted forecast SHALL have color "blanc" and probability 1.0
    - If original probability ≤ 0.6, the adjusted forecast SHALL have color "blanc" and probability = original + 0.1
    
    **Validates: Requirements 3.1, 3.2, 3.3**
    """
    
    @given(
        saturday_date=saturday_strategy(),
        probability=probability_strategy,
    )
    @settings(max_examples=100)
    def test_saturday_red_conversion(self, saturday_date, probability):
        """Feature: tempo-forecast-rules, Property 3: Saturday Red Conversion"""
        # Verify precondition
        assert saturday_date.weekday() == 5, "Date must be Saturday"
        
        forecast = ForecastDay(
            date=saturday_date,
            color="rouge",
            probability=probability,
        )
        
        result = adjust_forecast_day(forecast)
        
        # Saturday red should NEVER remain red
        assert result.color == "blanc", f"Saturday red should become blanc, got {result.color}"
        
        # Check probability conversion
        if probability > 0.6:
            assert result.probability == 1.0, f"High prob red should become 100%, got {result.probability}"
        else:
            expected = min(probability + 0.1, 1.0)
            assert abs(result.probability - expected) < 0.001, \
                f"Low prob red {probability} should become {expected}, got {result.probability}"


class TestProperty4SaturdayAllowedColorsUnchanged:
    """
    Property 4: Saturday Allowed Colors Unchanged
    
    *For any* forecast where the date is a Saturday and the original color is
    "bleu" or "blanc", the adjusted forecast SHALL be identical to the original
    forecast (same color and probability).
    
    **Validates: Requirements 4.1, 4.2**
    """
    
    @given(
        saturday_date=saturday_strategy(),
        color=st.sampled_from(["bleu", "blanc"]),
        probability=probability_strategy,
    )
    @settings(max_examples=100)
    def test_saturday_allowed_colors_unchanged(self, saturday_date, color, probability):
        """Feature: tempo-forecast-rules, Property 4: Saturday Allowed Colors Unchanged"""
        # Verify precondition
        assert saturday_date.weekday() == 5, "Date must be Saturday"
        
        forecast = ForecastDay(
            date=saturday_date,
            color=color,
            probability=probability,
        )
        
        result = adjust_forecast_day(forecast)
        
        assert result.color == color, f"Saturday {color} should stay {color}, got {result.color}"
        assert result.probability == probability, \
            f"Saturday {color} probability should stay {probability}, got {result.probability}"


class TestProperty5WeekdayNonHolidayUnchanged:
    """
    Property 5: Weekday Non-Holiday Unchanged
    
    *For any* forecast where the date is a weekday (Monday-Friday) and NOT a
    French holiday, the adjusted forecast SHALL be identical to the original
    forecast (same color and probability).
    
    **Validates: Requirements 5.1, 5.2**
    """
    
    @given(
        weekday_date=weekday_non_holiday_strategy(),
        color=color_strategy,
        probability=probability_strategy,
    )
    @settings(max_examples=100)
    def test_weekday_non_holiday_unchanged(self, weekday_date, color, probability):
        """Feature: tempo-forecast-rules, Property 5: Weekday Non-Holiday Unchanged"""
        # Verify preconditions
        assert weekday_date.weekday() < 5, "Date must be Mon-Fri"
        assert not is_french_holiday(weekday_date), "Date must not be a holiday"
        
        forecast = ForecastDay(
            date=weekday_date,
            color=color,
            probability=probability,
        )
        
        result = adjust_forecast_day(forecast)
        
        assert result.color == color, f"Weekday {color} should stay {color}, got {result.color}"
        assert result.probability == probability, \
            f"Weekday probability should stay {probability}, got {result.probability}"


class TestProperty6RuleIdempotence:
    """
    Property 6: Rule Idempotence
    
    *For any* forecast, applying the rules twice SHALL produce the same result
    as applying them once. This ensures the rules are deterministic and stable.
    
    **Validates: Requirements 6.1, 6.2**
    """
    
    @given(forecast=forecast_strategy())
    @settings(max_examples=100)
    def test_rule_idempotence(self, forecast):
        """Feature: tempo-forecast-rules, Property 6: Rule Idempotence"""
        # Apply once
        result1 = adjust_forecast_day(forecast)
        
        # Apply twice
        result2 = adjust_forecast_day(result1)
        
        assert result1.color == result2.color, \
            f"Idempotence failed: {result1.color} != {result2.color}"
        assert result1.probability == result2.probability, \
            f"Idempotence failed: {result1.probability} != {result2.probability}"
        assert result1.indicator == result2.indicator, \
            f"Idempotence failed: {result1.indicator} != {result2.indicator}"


class TestApplyTempoRules:
    """Tests for apply_tempo_rules function."""
    
    def test_empty_list(self):
        """Empty forecast list should return empty list."""
        assert apply_tempo_rules([]) == []
    
    @given(st.lists(forecast_strategy(), min_size=1, max_size=10))
    @settings(max_examples=50)
    def test_preserves_list_length(self, forecasts):
        """apply_tempo_rules should preserve the number of forecasts."""
        result = apply_tempo_rules(forecasts)
        assert len(result) == len(forecasts)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
