# Requirements Document: Forecast History Tracking

## Introduction

Système d'analyse de la précision des prévisions Tempo qui utilise l'historique existant du recorder Home Assistant pour comparer les prévisions J+2 à J+7 avec la couleur réelle. Permet d'analyser l'évolution de la précision des prévisions selon l'horizon.

## Glossaire

- **AccuracyAnalyzer**: Module qui analyse l'historique des prévisions depuis le recorder HA
- **Horizon**: Nombre de jours entre la prévision et la date cible (J+2 à J+7)
- **Accuracy_Matrix**: Tableau comparant prévisions à différents horizons vs réalité
- **Target_Date**: Date pour laquelle une prévision a été faite (attribut `date` du sensor)

## Requirements

### Requirement 1: Lecture de l'historique des prévisions

**User Story:** En tant qu'utilisateur, je veux que le système lise l'historique des prévisions depuis le recorder HA pour analyser les prédictions passées.

#### Acceptance Criteria

1. THE AccuracyAnalyzer SHALL read history from all forecast sensors (J+2 to J+7)
2. WHEN reading history, THE AccuracyAnalyzer SHALL extract the target date from the `date` attribute
3. THE AccuracyAnalyzer SHALL analyze the last 30 days of history
4. WHEN a forecast entry lacks a valid `date` attribute, THE AccuracyAnalyzer SHALL skip that entry

### Requirement 2: Construction de la matrice de comparaison (passé)

**User Story:** En tant qu'utilisateur, je veux voir ce qui était prévu à J-7, J-6, J-5, J-4, J-3, J-2, J-1 pour les dates passées, afin de comprendre la précision des prévisions à différents horizons.

#### Acceptance Criteria

1. WHEN displaying past history, THE Accuracy_Matrix SHALL show columns for each horizon (J-7 to J-1)
2. THE Accuracy_Matrix SHALL include J-1 (official RTE value, 100% accurate)
3. WHEN a forecast matches the actual color, THE Accuracy_Matrix SHALL display a checkmark (✓)
4. WHEN a forecast differs from actual, THE Accuracy_Matrix SHALL display a cross (✗)
5. WHEN no forecast was recorded for a horizon, THE Accuracy_Matrix SHALL display a dash (-)
6. THE Accuracy_Matrix SHALL show the actual color in a dedicated "Réel" column
7. THE Accuracy_Matrix SHALL be sorted by date descending (most recent first)

### Requirement 3: Construction de la matrice de prévisions (futur)

**User Story:** En tant qu'utilisateur, je veux voir les prévisions actuelles pour les dates futures.

#### Acceptance Criteria

1. WHEN displaying future forecasts, THE Future_Matrix SHALL show columns for each horizon (J-7 to J-2)
2. THE Future_Matrix SHALL NOT include a "Réel" column (color unknown)
3. THE Future_Matrix SHALL show the predicted color for each available horizon
4. WHEN no forecast is available for a horizon, THE Future_Matrix SHALL display a dash (-)
5. THE Future_Matrix SHALL be sorted by date ascending (nearest future first)

### Requirement 4: Calcul de précision par horizon

**User Story:** En tant qu'utilisateur, je veux voir les statistiques de précision par horizon pour comprendre quel horizon de prévision est le plus fiable.

#### Acceptance Criteria

1. THE AccuracyAnalyzer SHALL calculate accuracy percentage for each horizon (J-7 to J-1)
2. WHEN calculating accuracy, THE AccuracyAnalyzer SHALL exclude Sundays and French holidays
3. THE sensor attributes SHALL expose accuracy_j1, accuracy_j2, accuracy_j3, accuracy_j4, accuracy_j5, accuracy_j6, accuracy_j7
4. THE accuracy_j1 SHALL always be 100% (official RTE value)

### Requirement 5: Exposition via sensor HA

**User Story:** En tant qu'utilisateur, je veux que les données de tracking soient exposées comme un sensor Home Assistant pour les afficher dans les dashboards.

#### Acceptance Criteria

1. THE TempoAccuracySensor SHALL expose the full history matrix in its attributes
2. THE sensor state SHALL remain the overall 30-day accuracy percentage
3. THE sensor attributes SHALL include per-horizon accuracy statistics
4. THE sensor SHALL update hourly to incorporate new data
