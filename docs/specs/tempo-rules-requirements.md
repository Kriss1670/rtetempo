# Requirements Document: Tempo Forecast Rules

## Introduction

Ce document définit les exigences pour l'application des règles Tempo EDF sur les prévisions de couleur sur 7 jours. Selon les règles officielles EDF Tempo : **"Les jours rouges n'ont jamais lieu les week-ends ni les jours fériés."**

## Glossaire

- **Forecast_Engine**: Le module responsable du calcul et de l'ajustement des couleurs Tempo prévisionnelles
- **Tempo_Color**: Une couleur Tempo parmi "bleu", "blanc", "rouge"
- **Probability**: La probabilité (0.0 à 1.0) qu'une couleur soit attribuée à un jour donné
- **Probability_Indicator**: L'indicateur affiché à la place de la probabilité - "D" pour dimanche ou "F" pour jour férié
- **Allowed_Colors**: Les couleurs autorisées pour un jour donné selon les règles Tempo
- **French_Holiday**: Un jour férié français officiel (1er janvier, lundi de Pâques, 1er mai, 8 mai, Ascension, lundi de Pentecôte, 14 juillet, 15 août, 1er novembre, 11 novembre, 25 décembre)

## Règles EDF Tempo

| Type de jour | Couleurs possibles | Notes |
|--------------|-------------------|-------|
| Dimanche | Bleu uniquement | Fait partie des 300 jours bleus/an |
| Jour férié | Bleu ou Blanc | Jamais rouge |
| Samedi | Bleu ou Blanc | Jamais rouge |
| Lundi-Vendredi | Bleu, Blanc ou Rouge | Toutes couleurs possibles |

## Requirements

### Requirement 1: Règle du Dimanche

**User Story:** En tant qu'utilisateur, je veux que les dimanches soient toujours affichés en bleu avec un indicateur "D", car les règles Tempo garantissent que le dimanche est toujours un jour bleu.

#### Acceptance Criteria

1. WHEN the Forecast_Engine processes a forecast for a Sunday THEN the Forecast_Engine SHALL set the color to "bleu"
2. WHEN the Forecast_Engine processes a forecast for a Sunday THEN the Forecast_Engine SHALL replace the probability with indicator "D"
3. WHEN the Forecast_Engine processes a forecast for a Sunday THEN the Forecast_Engine SHALL ignore the original color and probability from the API
4. WHEN a day is both a Sunday and a French_Holiday THEN the Forecast_Engine SHALL display "D" (Sunday rule takes precedence)

### Requirement 2: Règle des Jours Fériés (identique aux samedis)

**User Story:** En tant qu'utilisateur, je veux que les jours fériés français soient traités exactement comme les samedis (jamais rouge) avec un indicateur "F", car les règles Tempo garantissent que les jours rouges n'ont jamais lieu les jours fériés.

#### Acceptance Criteria

1. WHEN the Forecast_Engine processes a forecast for a French_Holiday with red color and probability > 60% THEN the Forecast_Engine SHALL set the color to "blanc" with 100% probability + indicator "F"
2. WHEN the Forecast_Engine processes a forecast for a French_Holiday with red color and probability ≤ 60% THEN the Forecast_Engine SHALL set the color to "blanc" with probability = original + 10% + indicator "F"
3. WHEN the Forecast_Engine processes a forecast for a French_Holiday with "bleu" or "blanc" color THEN the Forecast_Engine SHALL keep the original color and probability + add indicator "F"
4. THE Forecast_Engine SHALL recognize all official French holidays including movable holidays (Easter Monday, Ascension, Whit Monday)
5. WHEN the Forecast_Engine processes a forecast for a French_Holiday THEN the Forecast_Engine SHALL never display "rouge" as the color

### Requirement 3: Règle du Samedi avec prévision Rouge

**User Story:** En tant qu'utilisateur, je veux que les samedis avec une prévision rouge soient ajustés en blanc, car le rouge n'est pas autorisé le samedi selon les règles Tempo.

#### Acceptance Criteria

1. WHEN the Forecast_Engine processes a Saturday forecast with red color and probability greater than 60% THEN the Forecast_Engine SHALL set the color to "blanc" with 100% probability
2. WHEN the Forecast_Engine processes a Saturday forecast with red color and probability less than or equal to 60% THEN the Forecast_Engine SHALL set the color to "blanc" with probability equal to the original red probability plus 10%
3. WHEN the Forecast_Engine processes a Saturday forecast with red color THEN the Forecast_Engine SHALL never display "rouge" as the color

### Requirement 4: Règle du Samedi avec couleurs autorisées

**User Story:** En tant qu'utilisateur, je veux que les samedis avec des couleurs autorisées (bleu ou blanc) conservent leur prévision originale.

#### Acceptance Criteria

1. WHEN the Forecast_Engine processes a Saturday forecast with "bleu" color THEN the Forecast_Engine SHALL keep the original color and probability unchanged
2. WHEN the Forecast_Engine processes a Saturday forecast with "blanc" color THEN the Forecast_Engine SHALL keep the original color and probability unchanged

### Requirement 5: Règle des jours de semaine

**User Story:** En tant qu'utilisateur, je veux que les jours de semaine (lundi à vendredi) conservent leur prévision originale sans modification sauf si c'est un jour férié.

#### Acceptance Criteria

1. WHEN the Forecast_Engine processes a forecast for a weekday (Monday through Friday) that is NOT a holiday THEN the Forecast_Engine SHALL keep the original color and probability unchanged
2. WHEN the Forecast_Engine processes a forecast for a weekday THEN the Forecast_Engine SHALL allow all three colors (bleu, blanc, rouge)

### Requirement 6: Application des règles sur les 7 jours

**User Story:** En tant qu'utilisateur, je veux que les règles Tempo soient appliquées à toutes les prévisions des 7 prochains jours.

#### Acceptance Criteria

1. WHEN the Forecast_Engine fetches forecasts from the API THEN the Forecast_Engine SHALL apply the Tempo rules to each of the 7 forecast days
2. WHEN the Forecast_Engine returns the forecast list THEN the Forecast_Engine SHALL return the adjusted forecasts with corrected colors and probabilities
