"""Tempo rules for adjusting forecast colors.

This module implements the Tempo rules for Sundays, French holidays, and Saturdays.
"""
from __future__ import annotations

import datetime
import logging
from typing import TYPE_CHECKING, List, Tuple

if TYPE_CHECKING:
    from .forecast import ForecastDay

_LOGGER = logging.getLogger(__name__)

# Fixed French holidays (month, day)
FIXED_HOLIDAYS: List[Tuple[int, int]] = [
    (1, 1),    # Jour de l'An (New Year's Day)
    (5, 1),    # Fête du Travail (Labour Day)
    (5, 8),    # Victoire 1945 (Victory in Europe Day)
    (7, 14),   # Fête Nationale (Bastille Day)
    (8, 15),   # Assomption (Assumption of Mary)
    (11, 1),   # Toussaint (All Saints' Day)
    (11, 11),  # Armistice (Armistice Day)
    (12, 25),  # Noël (Christmas Day)
]


def compute_easter(year: int) -> datetime.date:
    """Compute the date of Easter Sunday for a given year.

    Uses the Butcher-Meeus algorithm, valid for years 1583-4099.

    Args:
        year: The year for which to compute Easter.

    Returns:
        The date of Easter Sunday.
    """
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return datetime.date(year, month, day)


def get_movable_holidays(year: int) -> List[datetime.date]:
    """Get the movable French holidays for a given year.

    Movable holidays depend on Easter:
    - Easter Monday: Easter + 1 day
    - Ascension: Easter + 39 days (Thursday)
    - Whit Monday: Easter + 50 days

    Args:
        year: The year for which to get movable holidays.

    Returns:
        A list of dates for the movable holidays.
    """
    easter = compute_easter(year)
    return [
        easter + datetime.timedelta(days=1),   # Lundi de Pâques (Easter Monday)
        easter + datetime.timedelta(days=39),  # Ascension
        easter + datetime.timedelta(days=50),  # Lundi de Pentecôte (Whit Monday)
    ]


def is_french_holiday(date: datetime.date) -> bool:
    """Check if a date is a French public holiday.

    Includes both fixed holidays and movable holidays (Easter-based).

    Args:
        date: The date to check.

    Returns:
        True if the date is a French public holiday, False otherwise.
    """
    # Check fixed holidays
    if (date.month, date.day) in FIXED_HOLIDAYS:
        return True

    # Check movable holidays
    try:
        movable = get_movable_holidays(date.year)
        return date in movable
    except Exception as exc:
        _LOGGER.error("Error computing movable holidays for %s: %s", date.year, exc)
        return False


def adjust_forecast_day(forecast: "ForecastDay") -> "ForecastDay":
    """Adjust a single forecast day according to Tempo rules.

    Rules applied in order of priority:
    1. Sundays → blue + indicator "D" (always blue, highest priority)
    2. French holidays with red → convert to white + indicator "F"
    3. French holidays with allowed colors → keep color + indicator "F"
    4. Saturdays with red → convert to white with adjusted probability
    5. Otherwise → keep original

    Note: Per EDF Tempo rules, red days never occur on weekends or public holidays.
    - Sundays are always blue (part of the 300 blue days per year)
    - Saturdays and holidays can be blue or white, never red

    Args:
        forecast: The original forecast to adjust.

    Returns:
        A new ForecastDay with adjusted values, or the original if no rules apply.
    """
    from .forecast import ForecastDay

    date = forecast.date
    weekday = date.weekday()  # 0=Monday, 5=Saturday, 6=Sunday

    # Rule 1: Sundays → blue + indicator "D" (highest priority, always blue)
    if weekday == 6:  # Sunday
        return ForecastDay(
            date=date,
            color="bleu",
            probability=None,
            indicator="D",
            source=forecast.source,
        )

    # Rule 2 & 3: French holidays (like Saturdays - can be blue or white, never red)
    if is_french_holiday(date):
        if forecast.color == "rouge":
            # Holiday with red → convert to white + indicator "F"
            original_prob = forecast.probability if forecast.probability is not None else 0.0
            if original_prob > 0.6:
                new_probability = 1.0
            else:
                new_probability = min(original_prob + 0.1, 1.0)
            return ForecastDay(
                date=date,
                color="blanc",
                probability=new_probability,
                indicator="F",
                source=forecast.source,
            )
        else:
            # Holiday with allowed color (bleu, blanc) → keep color + indicator "F"
            return ForecastDay(
                date=date,
                color=forecast.color,
                probability=forecast.probability,
                indicator="F",
                source=forecast.source,
            )

    # Rule 4: Saturdays with red → convert to white
    if weekday == 5 and forecast.color == "rouge":  # Saturday
        original_prob = forecast.probability if forecast.probability is not None else 0.0
        if original_prob > 0.6:
            # High probability red → white with 100%
            new_probability = 1.0
        else:
            # Low probability red → white with original + 10%
            new_probability = min(original_prob + 0.1, 1.0)

        return ForecastDay(
            date=date,
            color="blanc",
            probability=new_probability,
            indicator=None,
            source=forecast.source,
        )

    # Rule 5: Saturday with allowed colors (bleu, blanc) → keep original
    # Rule 6: Weekdays (non-holiday) → keep original
    # Return a copy with indicator explicitly set to None for consistency
    return ForecastDay(
        date=forecast.date,
        color=forecast.color,
        probability=forecast.probability,
        indicator=None,
        source=forecast.source,
    )


def apply_tempo_rules(forecasts: List["ForecastDay"]) -> List["ForecastDay"]:
    """Apply Tempo rules to a list of forecasts.

    Applies adjust_forecast_day to each forecast in the list.

    Args:
        forecasts: The list of original forecasts from the API.

    Returns:
        A new list with all forecasts adjusted according to Tempo rules.
    """
    return [adjust_forecast_day(forecast) for forecast in forecasts]
