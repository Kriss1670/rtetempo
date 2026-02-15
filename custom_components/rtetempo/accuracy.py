"""Accuracy analysis for Tempo forecasts.

This module compares forecast predictions to actual colors to calculate accuracy.
Sundays and French holidays are excluded from calculations.
Supports multi-horizon analysis (J-7 to J-2) with past and future matrices.
"""
from __future__ import annotations

import datetime
import logging
from collections import defaultdict
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from .tempo_rules import is_french_holiday

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

# Forecast sensor entity IDs by horizon
FORECAST_SENSORS = {
    2: "sensor.rte_tempo_forecast_opendpe_j2",
    3: "sensor.rte_tempo_forecast_opendpe_j3",
    4: "sensor.rte_tempo_forecast_opendpe_j4",
    5: "sensor.rte_tempo_forecast_opendpe_j5",
    6: "sensor.rte_tempo_forecast_opendpe_j6",
    7: "sensor.rte_tempo_forecast_opendpe_j7",
}

CURRENT_COLOR_SENSOR = "sensor.rte_tempo_couleur_actuelle"
NEXT_COLOR_SENSOR = "sensor.rte_tempo_prochaine_couleur"


@dataclass
class HorizonForecast:
    """Forecast at a specific horizon."""
    color: Optional[str] = None  # "bleu", "blanc", "rouge" or None
    result: str = "-"  # "✓", "✗", or "-"
    
    def to_dict(self) -> dict:
        """Convert to dict for JSON serialization."""
        return {"color": self.color, "result": self.result}


class AccuracyAnalyzer:
    """Analyzes forecast accuracy by comparing predictions to actual colors.
    
    This class reads history from Home Assistant's recorder and compares
    forecast predictions at multiple horizons (J-7 to J-2) to actual colors.
    Sundays and French holidays are excluded from accuracy calculations.
    """
    
    def __init__(self, hass: "HomeAssistant"):
        """Initialize the analyzer."""
        self.hass = hass
    
    def is_excluded(self, date: datetime.date) -> bool:
        """Check if date should be excluded from accuracy calculation."""
        if date.weekday() == 6:  # Sunday
            return True
        return is_french_holiday(date)

    async def _get_raw_history(
        self, 
        entity_id: str, 
        days: int = 30
    ) -> List[Any]:
        """Get raw state history for an entity from HA recorder."""
        from homeassistant.components.recorder import get_instance
        from homeassistant.components.recorder.history import get_significant_states
        
        end_time = datetime.datetime.now(datetime.timezone.utc)
        start_time = end_time - datetime.timedelta(days=days + 10)  # Extra days for horizon
        
        try:
            states = await get_instance(self.hass).async_add_executor_job(
                get_significant_states,
                self.hass,
                start_time,
                end_time,
                [entity_id],
            )
            return states.get(entity_id, [])
        except Exception as err:
            _LOGGER.error("Error getting history for %s: %s", entity_id, err)
            return []

    async def get_forecast_history_by_target_date(
        self, 
        days: int = 30
    ) -> Dict[str, Dict[int, str]]:
        """Get forecast history organized by target date and horizon.
        
        Returns:
            Dict mapping target_date (ISO) to {horizon: color}
            Example: {"2025-12-29": {7: "rouge", 6: "rouge", ...}}
        """
        result: Dict[str, Dict[int, str]] = defaultdict(dict)
        
        for horizon, sensor_id in FORECAST_SENSORS.items():
            states = await self._get_raw_history(sensor_id, days)
            
            # Group by target date, keeping last value per forecast_date
            by_target_and_forecast_date: Dict[str, Dict[str, tuple]] = defaultdict(dict)
            
            for state in states:
                # Skip invalid states
                if state.state in ("unknown", "unavailable", None):
                    continue
                
                color = state.state.lower()
                if color not in ("bleu", "blanc", "rouge"):
                    continue
                
                # Get target date from attribute
                attrs = state.attributes or {}
                target_date = attrs.get("date")
                if not target_date:
                    continue
                
                # Get forecast date (when prediction was made)
                forecast_date = state.last_changed.strftime("%Y-%m-%d")
                forecast_time = state.last_changed
                
                # Keep last value per forecast_date (if multiple same day)
                existing = by_target_and_forecast_date[target_date].get(forecast_date)
                if existing is None or forecast_time > existing[1]:
                    by_target_and_forecast_date[target_date][forecast_date] = (color, forecast_time)
            
            # For each target date, find the forecast made at the right horizon
            for target_date, forecasts_by_day in by_target_and_forecast_date.items():
                try:
                    target = datetime.date.fromisoformat(target_date)
                except ValueError:
                    continue
                
                # Find forecast made (horizon) days before target
                expected_forecast_date = (target - datetime.timedelta(days=horizon)).isoformat()
                
                if expected_forecast_date in forecasts_by_day:
                    result[target_date][horizon] = forecasts_by_day[expected_forecast_date][0]
        
        return dict(result)

    async def get_actual_colors(self, days: int = 30) -> Dict[str, str]:
        """Get actual colors by date from history.
        
        Also includes tomorrow's official color from RTE (J+1).
        
        Returns:
            Dict mapping date (ISO) to actual color
        """
        states = await self._get_raw_history(CURRENT_COLOR_SENSOR, days)
        
        result: Dict[str, str] = {}
        for state in states:
            if state.state in ("unknown", "unavailable", None):
                continue
            
            color = state.state.lower()
            if color not in ("bleu", "blanc", "rouge"):
                continue
            
            date_str = state.last_changed.strftime("%Y-%m-%d")
            # Keep last value per date
            result[date_str] = color
        
        # Add tomorrow's official color (J+1) if available
        tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
        next_color_state = self.hass.states.get(NEXT_COLOR_SENSOR)
        if next_color_state and next_color_state.state not in ("unknown", "unavailable", None):
            color = next_color_state.state.lower()
            if color in ("bleu", "blanc", "rouge"):
                result[tomorrow] = color
        
        return result

    def _compare(self, predicted: Optional[str], actual: str, date: datetime.date) -> str:
        """Compare prediction to actual and return result symbol."""
        if predicted is None:
            return "-"
        if self.is_excluded(date):
            return "-"
        return "✓" if predicted == actual else "✗"

    async def build_past_matrix(self, days: int = 30) -> List[dict]:
        """Build the past accuracy matrix.
        
        Includes dates up to tomorrow (J+1) since we have the official RTE color.
        
        Returns:
            List of dicts sorted by date descending (most recent first)
            Each dict: {date, j7, j6, j5, j4, j3, j2, actual}
            where jX = {color, result}
        """
        forecasts = await self.get_forecast_history_by_target_date(days)
        actuals = await self.get_actual_colors(days)
        
        today = datetime.date.today()
        tomorrow = today + datetime.timedelta(days=1)
        matrix = []
        
        # Include dates where we have actual color (up to tomorrow since we have J+1 official)
        for date_str, actual in sorted(actuals.items(), reverse=True):
            try:
                date = datetime.date.fromisoformat(date_str)
            except ValueError:
                continue
            
            # Skip dates after tomorrow (we don't have official color yet)
            if date > tomorrow:
                continue
            
            # Skip if older than requested days
            if (today - date).days > days:
                continue
            
            row = {
                "date": date_str,
                "actual": actual,
            }
            
            # Add each horizon
            date_forecasts = forecasts.get(date_str, {})
            for h in range(7, 1, -1):  # J-7 to J-2
                predicted = date_forecasts.get(h)
                result = self._compare(predicted, actual, date)
                row[f"j{h}"] = {"color": predicted, "result": result}
            
            matrix.append(row)
        
        return matrix

    async def build_future_matrix(self) -> List[dict]:
        """Build the future forecast matrix (no actual column).
        
        For future dates, we use the same forecast history as past_matrix.
        The diagonal pattern is:
        - J+2 (2 days ahead): only J-2 forecast exists (made today)
        - J+3 (3 days ahead): J-3 (today) and J-2 (tomorrow, not yet)
        - J+7 (7 days ahead): J-7 (today), J-6 to J-2 (future, not yet)
        
        So for a target date, we have forecasts for horizons where:
        forecast_date = target_date - horizon <= today
        
        Returns:
            List of dicts sorted by date ascending (nearest future first)
            Each dict: {date, j7, j6, j5, j4, j3, j2}
            where jX = {color} (no result since actual unknown)
        """
        today = datetime.date.today()
        
        # Get forecast history - this contains all forecasts by target date
        forecasts = await self.get_forecast_history_by_target_date(days=14)
        
        matrix = []
        
        # For each future date (J+2 to J+7)
        for days_ahead in range(2, 8):
            target_date = today + datetime.timedelta(days=days_ahead)
            date_str = target_date.isoformat()
            
            row = {"date": date_str}
            
            # Get forecasts for this target date from history
            date_forecasts = forecasts.get(date_str, {})
            
            # For each horizon, check if we have a forecast
            for horizon in range(7, 1, -1):  # J-7 to J-2
                # Calculate when this forecast would have been made
                forecast_date = target_date - datetime.timedelta(days=horizon)
                
                # Only include if forecast_date is today or in the past
                # (forecast has already been made)
                if forecast_date <= today:
                    color = date_forecasts.get(horizon)
                    row[f"j{horizon}"] = {"color": color}
                else:
                    # Forecast not yet made (future forecast date)
                    row[f"j{horizon}"] = {"color": None}
            
            matrix.append(row)
        
        return matrix

    def calculate_horizon_accuracy(
        self, 
        past_matrix: List[dict], 
        horizon: int
    ) -> float:
        """Calculate accuracy for a specific horizon.
        
        Args:
            past_matrix: The past matrix from build_past_matrix()
            horizon: The horizon to calculate (2-7)
            
        Returns:
            Accuracy percentage (0.0 to 100.0)
        """
        key = f"j{horizon}"
        valid = []
        correct = 0
        
        for row in past_matrix:
            h_data = row.get(key, {})
            result = h_data.get("result", "-")
            
            if result != "-":
                valid.append(result)
                if result == "✓":
                    correct += 1
        
        if not valid:
            return 0.0
        
        return round((correct / len(valid)) * 100, 1)

    async def analyze(self, days: int = 30) -> dict:
        """Run full analysis and return results.
        
        Returns:
            Dict with accuracy stats, past matrix, and future matrix
        """
        past_matrix = await self.build_past_matrix(days)
        future_matrix = await self.build_future_matrix()
        
        # Calculate per-horizon accuracy
        horizon_accuracy = {}
        for h in range(2, 8):
            horizon_accuracy[f"accuracy_j{h}"] = self.calculate_horizon_accuracy(past_matrix, h)
        
        # Calculate overall stats
        total_correct = 0
        total_incorrect = 0
        total_excluded = 0
        
        for row in past_matrix:
            for h in range(2, 8):
                result = row.get(f"j{h}", {}).get("result", "-")
                if result == "✓":
                    total_correct += 1
                elif result == "✗":
                    total_incorrect += 1
                elif result == "-":
                    total_excluded += 1
        
        # Overall accuracy (J-2 only for backward compatibility)
        accuracy_30d = self.calculate_horizon_accuracy(past_matrix, 2)
        
        # 7-day accuracy
        cutoff = datetime.date.today() - datetime.timedelta(days=7)
        recent_matrix = [
            r for r in past_matrix 
            if datetime.date.fromisoformat(r["date"]) >= cutoff
        ]
        accuracy_7d = self.calculate_horizon_accuracy(recent_matrix, 2) if recent_matrix else 0.0
        
        return {
            "accuracy_30d": accuracy_30d,
            "accuracy_7d": accuracy_7d,
            **horizon_accuracy,
            "total_days": len(past_matrix),
            "correct_predictions": total_correct,
            "incorrect_predictions": total_incorrect,
            "excluded_predictions": total_excluded,
            "past_matrix": past_matrix,
            "future_matrix": future_matrix,
        }
