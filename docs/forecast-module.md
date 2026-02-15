# Documentation: Module Forecast

## Vue d'ensemble

Le module Forecast fournit les prévisions de couleur Tempo sur 7 jours en utilisant l'API Open DPE. Il applique automatiquement les règles Tempo EDF (dimanches, jours fériés, samedis) avant d'exposer les données via des sensors Home Assistant.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      API Open DPE                            │
│         https://open-dpe.fr/assets/tempo_days_lite.json     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    forecast.py                               │
│  async_fetch_opendpe_forecast() → List[ForecastDay]         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    tempo_rules.py                            │
│  apply_tempo_rules() → List[ForecastDay] (ajustées)         │
│  - Dimanches → bleu + indicateur "D"                        │
│  - Jours fériés → jamais rouge + indicateur "F"             │
│  - Samedis → jamais rouge                                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│               forecast_coordinator.py                        │
│  ForecastCoordinator (DataUpdateCoordinator)                │
│  - Refresh toutes les 6 heures                              │
│  - Refresh programmé à 07:00                                │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                sensor_forecast.py                            │
│  OpenDPEForecastSensor × 14 sensors                         │
│  - J1 à J7 (texte) : "Bleu", "Blanc", "Rouge"              │
│  - J1 à J7 (visuel) : 🔵, ⚪, 🔴                            │
└─────────────────────────────────────────────────────────────┘
```

## Composants

### 1. forecast.py - Modèle et API

#### ForecastDay (dataclass)

```python
@dataclass
class ForecastDay:
    date: datetime.date           # Date de la prévision
    color: str                    # "bleu", "blanc", "rouge"
    probability: Optional[float]  # 0.0 à 1.0 (ex: 0.67 = 67%)
    indicator: Optional[str]      # "D" (dimanche), "F" (férié), ou None
    source: str = "open_dpe"      # Source des données
```

#### async_fetch_opendpe_forecast()

Récupère les prévisions brutes depuis l'API Open DPE.

- **URL** : `https://open-dpe.fr/assets/tempo_days_lite.json`
- **Timeout** : 10 secondes
- **Retour** : Liste de `ForecastDay` (7-9 jours selon l'API)

### 2. tempo_rules.py - Règles Tempo EDF

Applique les règles officielles EDF : "Les jours rouges n'ont jamais lieu les week-ends ni les jours fériés."

| Type de jour | Règle appliquée |
|--------------|-----------------|
| Dimanche | Toujours bleu + indicateur "D" |
| Jour férié (rouge) | Converti en blanc + indicateur "F" |
| Jour férié (bleu/blanc) | Garde couleur + indicateur "F" |
| Samedi (rouge) | Converti en blanc |
| Samedi (bleu/blanc) | Garde couleur originale |
| Lundi-Vendredi | Garde prévision originale |

#### Jours fériés reconnus

**Fixes** : 1er janvier, 1er mai, 8 mai, 14 juillet, 15 août, 1er novembre, 11 novembre, 25 décembre

**Mobiles** (basés sur Pâques) : Lundi de Pâques, Ascension, Lundi de Pentecôte

### 3. forecast_coordinator.py - Coordination

`ForecastCoordinator` hérite de `DataUpdateCoordinator` et gère :

- **Intervalle de refresh** : 6 heures
- **Refresh programmé** : 07:00 chaque jour (l'API est mise à jour vers 06:00)
- **Cleanup** : Annulation du listener lors du unload

```python
async def _async_update_data(self) -> List[ForecastDay]:
    forecasts = await async_fetch_opendpe_forecast(self.session)
    adjusted_forecasts = apply_tempo_rules(forecasts)
    return adjusted_forecasts
```

### 4. sensor_forecast.py - Sensors HA

`OpenDPEForecastSensor` crée 14 sensors (7 texte + 7 visuel) :

| Sensor | Entity ID | État |
|--------|-----------|------|
| OpenDPE J1 | `sensor.rte_tempo_forecast_opendpe_j1` | "Bleu", "Blanc", "Rouge" |
| OpenDPE J1 (visuel) | `sensor.rte_tempo_forecast_opendpe_j1_emoji` | 🔵, ⚪, 🔴 |
| ... | ... | ... |
| OpenDPE J7 | `sensor.rte_tempo_forecast_opendpe_j7` | "Bleu", "Blanc", "Rouge" |
| OpenDPE J7 (visuel) | `sensor.rte_tempo_forecast_opendpe_j7_emoji` | 🔵, ⚪, 🔴 |

#### Attributs des sensors

| Attribut | Description |
|----------|-------------|
| `date` | Date cible de la prévision (ISO format) |
| `probability` | Probabilité (0.0-1.0) si jour normal |
| `indicator` | "D" (dimanche) ou "F" (férié) si applicable |
| `attribution` | Source des données |

#### Icônes dynamiques

| Couleur | Icône |
|---------|-------|
| Bleu | `mdi:check-bold` |
| Blanc | `mdi:information-outline` |
| Rouge | `mdi:alert` |
| Inconnu | `mdi:palette` |

## Format de l'API Open DPE

```json
[
  {
    "date": "2025-12-29",
    "couleur": "ROUGE",
    "probability": 1.0
  },
  {
    "date": "2025-12-30",
    "couleur": "ROUGE",
    "probability": 0.85
  }
]
```

## Flux de données

1. **Fetch** : `async_fetch_opendpe_forecast()` récupère le JSON
2. **Parse** : Conversion en `List[ForecastDay]`
3. **Rules** : `apply_tempo_rules()` ajuste les couleurs
4. **Store** : `ForecastCoordinator.data` stocke les prévisions
5. **Update** : Chaque sensor lit `coordinator.data[index]`
6. **Display** : État et attributs exposés dans HA

## Configuration

Le module forecast est **optionnel** et doit être activé dans la configuration de l'intégration.

### Activation lors de l'installation

Lors de l'ajout de l'intégration RTE Tempo, cocher l'option **"Activer les prévisions Open DPE"** (`OPTION_FORECAST_ENABLED`).

### Activation après installation

1. Aller dans **Paramètres > Appareils et services > RTE Tempo**
2. Cliquer sur **Configurer**
3. Activer l'option **"Activer les prévisions Open DPE"**
4. Sauvegarder

### Options disponibles

| Option | Description | Défaut |
|--------|-------------|--------|
| `forecast_enabled` | Active les sensors de prévision J1-J7 | `false` |

## Dépendances

- `aiohttp` : Requêtes HTTP asynchrones
- `homeassistant.helpers.update_coordinator` : Coordination des mises à jour
- `homeassistant.helpers.aiohttp_client` : Session HTTP partagée
