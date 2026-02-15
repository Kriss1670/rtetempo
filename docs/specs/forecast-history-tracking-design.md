# Design Document: Forecast History Tracking

## Overview

Extension du système d'accuracy pour analyser les prévisions à différents horizons (J+2 à J+7) en utilisant l'historique existant du recorder Home Assistant. Les sensors forecast stockent déjà l'attribut `date` (date cible), ce qui permet de reconstruire la matrice de comparaison sans stockage supplémentaire.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Home Assistant Recorder                   │
│  (stocke l'historique des sensors avec attributs)           │
├─────────────────────────────────────────────────────────────┤
│  Sensors Forecast (J+2 à J+7)                               │
│  ├── state: couleur prévue                                  │
│  └── attributes.date: date cible de la prévision            │
├─────────────────────────────────────────────────────────────┤
│  AccuracyAnalyzer                                           │
│  ├── get_forecast_history()    → lit historique multi-sensor│
│  ├── build_accuracy_matrix()   → construit la matrice       │
│  └── calculate_horizon_accuracy() → stats par horizon       │
├─────────────────────────────────────────────────────────────┤
│  TempoAccuracySensor                                        │
│  ├── state: accuracy_30d (%)                                │
│  └── attributes:                                            │
│      ├── accuracy_j2, accuracy_j3, ..., accuracy_j7         │
│      ├── history_matrix: [{date, j7, j6, ..., j2, actual}]  │
│      └── total_days, correct_days, etc.                     │
└─────────────────────────────────────────────────────────────┘
```

## Avantages de cette approche

- **Pas de stockage supplémentaire** : utilise le recorder HA existant
- **Données historiques disponibles** : on peut analyser les 30 derniers jours immédiatement
- **Maintenance simplifiée** : pas de fichier JSON à gérer

## Observations sur les données réelles

Analyse des prévisions du 22-29 décembre 2025 :

| Date | J-7 | J-6 | J-5 | J-4 | J-3 | J-2 | Réel |
|------|-----|-----|-----|-----|-----|-----|------|
| 29/12 | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 ✅ |
| 28/12 | 🔵 | 🔵 | 🔵 | 🔵 | 🔵 | 🔵 | 🔵 ✅ |
| 26/12 | ⚪ | ⚪ | ⚪ | ⚪ | 🔴 | ⚪ | ⚪ (J-3 faux) |
| 25/12 | 🔵 | ⚪ | 🔵 | 🔵 | 🔵 | 🔵 | 🔵 (J-6 faux) |
| 24/12 | ⚪ | 🔵 | ⚪ | 🔵 | 🔵 | 🔵 | 🔵 (J-7,J-5 faux) |
| 23/12 | 🔵 | 🔴 | 🔵 | ⚪ | ⚪ | 🔵 | 🔵 (J-6,J-4,J-3 faux) |
| 22/12 | ⚪ | ⚪ | 🔴 | ⚪ | ⚪ | ⚪ | ⚪ (J-5 faux) |

**Constats** :
- Les prévisions à J-7 et J-6 sont souvent instables
- Les prévisions se stabilisent généralement à partir de J-4/J-3
- La probabilité augmente au fil des jours (ex: 56% à J-7 → 100% à J-2)

## Components and Interfaces

### AccuracyAnalyzer

```python
class AccuracyAnalyzer:
    """Analyzes forecast accuracy using HA recorder history."""
    
    FORECAST_SENSORS = {
        2: "sensor.rte_tempo_forecast_opendpe_j2",
        3: "sensor.rte_tempo_forecast_opendpe_j3",
        4: "sensor.rte_tempo_forecast_opendpe_j4",
        5: "sensor.rte_tempo_forecast_opendpe_j5",
        6: "sensor.rte_tempo_forecast_opendpe_j6",
        7: "sensor.rte_tempo_forecast_opendpe_j7",
    }
    
    async def get_forecast_history_by_horizon(
        self, 
        horizon: int, 
        days: int = 30
    ) -> dict[str, str]:
        """Get forecast history for a specific horizon.
        
        Reads recorder history and extracts forecasts by target date.
        Uses the 'date' attribute to identify which date was being predicted.
        
        Returns:
            Dict mapping target_date (ISO) to predicted color
        """
        
    async def build_accuracy_matrix(self, days: int = 30) -> list[dict]:
        """Build the full accuracy matrix.
        
        For each target date in the last N days:
        - Get what was predicted at J-7, J-6, J-5, J-4, J-3, J-2
        - Get the actual color
        - Compare and mark ✓/✗/-
        
        Returns:
            List of dicts with keys: date, j7, j6, j5, j4, j3, j2, actual
            Each jX contains: {color, result}
        """
        
    def calculate_horizon_accuracy(
        self, 
        matrix: list[dict], 
        horizon: int
    ) -> float:
        """Calculate accuracy for a specific horizon from the matrix."""
```

### Algorithme de reconstruction

Pour chaque sensor forecast (J+2 à J+7):
1. Lire l'historique des 30 derniers jours depuis le recorder
2. Pour chaque état avec attribut `date`:
   - Extraire la date cible et la couleur prévue
   - Ignorer les états `unknown` et `unavailable`
3. Grouper par date cible pour construire la matrice
4. **Si plusieurs couleurs le même jour** : prendre la dernière valeur (la plus récente)

**Note** : Les changements intra-journaliers sont rares (2 cas sur 14 jours analysés) mais existent :
- 1er janvier 2026 prévu le 28/12 : Blanc → Bleu
- 31 décembre 2025 prévu le 24/12 : Blanc → Rouge

## Data Models

### MatrixRow

```python
@dataclass
class HorizonForecast:
    """Forecast at a specific horizon."""
    color: str | None     # "bleu", "blanc", "rouge" or None if missing
    result: str           # "✓", "✗", or "-"

@dataclass
class MatrixRow:
    """One row in the accuracy matrix."""
    date: str                          # Target date ISO
    actual: str | None                 # Actual color
    j7: HorizonForecast | None
    j6: HorizonForecast | None
    j5: HorizonForecast | None
    j4: HorizonForecast | None
    j3: HorizonForecast | None
    j2: HorizonForecast | None
```

### Structure de données en mémoire

```python
# Matrice construite depuis l'historique HA
matrix = [
    {
        "date": "2025-12-29",
        "actual": "rouge",
        "j7": {"color": "rouge", "result": "✓"},
        "j6": {"color": "rouge", "result": "✓"},
        "j5": {"color": "rouge", "result": "✓"},
        "j4": {"color": "rouge", "result": "✓"},
        "j3": {"color": "rouge", "result": "✓"},
        "j2": {"color": "rouge", "result": "✓"},
    },
    {
        "date": "2025-12-28",
        "actual": "bleu",
        "j7": {"color": "bleu", "result": "-"},  # dimanche exclu
        ...
    }
]
```

## Règles de comparaison

| Condition | Résultat affiché |
|-----------|------------------|
| Prévision == Réel | ✓ (vert) |
| Prévision != Réel | ✗ (rouge) |
| Pas de prévision | - (gris) |
| Dimanche ou férié | - (exclu des stats) |

## Error Handling

| Scenario | Handling |
|----------|----------|
| Recorder unavailable | Return empty matrix, log warning |
| Forecast sensor history missing | Skip that horizon, mark as "-" |
| Actual color unknown | Store None, skip comparison |
| Invalid date attribute | Skip that entry, log warning |
