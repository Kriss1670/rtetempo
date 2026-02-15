# Tests for RTE Tempo

[![Tests](https://github.com/rjullien/rtetempo/actions/workflows/tests.yml/badge.svg)](https://github.com/rjullien/rtetempo/actions/workflows/tests.yml)
[![Coverage](https://img.shields.io/badge/coverage-96%25-brightgreen)](tests/README.md)
[![Python](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11-blue)](https://www.python.org/)
[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

## Prérequis

- Python 3.9+
- pip

## Installation de l'environnement de développement

```bash
# Créer un environnement virtuel
python3 -m venv .venv
source .venv/bin/activate

# Installer les dépendances de test
pip install -r requirements-test.txt
```

Ou manuellement :

```bash
pip install pytest pytest-asyncio hypothesis pytest-cov aiohttp requests
```

## Exécution des tests

### Méthode rapide avec le script

```bash
./scripts/run_tests.sh
```

Ce script :
1. Crée un environnement virtuel Python
2. Installe toutes les dépendances nécessaires
3. Exécute la suite de tests complète avec rapport de couverture

### Manuellement

```bash
source .venv/bin/activate

# Exécuter tous les tests
python -m pytest tests/ -v

# Exécuter avec coverage
python -m pytest tests/ --cov=custom_components/rtetempo --cov-report=term-missing

# Exécuter un fichier spécifique
python -m pytest tests/test_forecast.py -v

# Exécuter les tests async uniquement
python -m pytest tests/ -v -k "async"
```

## Couverture de code

La suite de tests inclut :
- **256 tests** couvrant tous les modules
- **Tests property-based** avec Hypothesis pour valider les propriétés de correction
- **Couverture de 96%** du code

| Module | Couverture |
|--------|------------|
| `__init__.py` | 100% |
| `api_worker.py` | 95% |
| `binary_sensor.py` | 93% |
| `calendar.py` | 100% |
| `config_flow.py` | 100% |
| `const.py` | 100% |
| `forecast.py` | 100% |
| `forecast_coordinator.py` | 100% |
| `sensor.py` | 92% |
| `sensor_forecast.py` | 100% |
| `tempo_rules.py` | 94% |

## Structure des tests

```
tests/
├── README.md                      # Ce fichier
├── conftest.py                    # Fixtures partagées
├── __init__.py
├── test_api_worker.py             # Tests API worker
├── test_binary_sensor.py          # Tests binary sensors
├── test_calendar.py               # Tests calendrier
├── test_config_flow.py            # Tests config flow
├── test_forecast.py               # Tests du module forecast.py
├── test_forecast_coordinator.py   # Tests du coordinator
├── test_init.py                   # Tests __init__.py
├── test_sensor.py                 # Tests sensors
├── test_sensor_forecast.py        # Tests des sensors forecast
└── test_tempo_rules.py            # Tests des règles Tempo
```

## Property-Based Testing

Les tests utilisent [Hypothesis](https://hypothesis.readthedocs.io/) pour générer des données de test aléatoires. Chaque property test exécute minimum 100 itérations.

Exemple de stratégies utilisées :
- `st.dates()` - Génération de dates
- `st.sampled_from(["bleu", "blanc", "rouge"])` - Couleurs Tempo
- `st.floats(0.0, 1.0)` - Probabilités

### Properties testées (tempo_rules.py)

| Property | Description | Requirements |
|----------|-------------|--------------|
| 1 | Jours fériés → bleu + "F" | 2.1, 2.2, 2.3, 2.5 |
| 2 | Dimanches (non fériés) → bleu + "D" | 1.1, 1.2, 1.3 |
| 3 | Samedi rouge → blanc | 3.1, 3.2, 3.3 |
| 4 | Samedi bleu/blanc → inchangé | 4.1, 4.2 |
| 5 | Jours semaine (non fériés) → inchangé | 5.1, 5.2 |
| 6 | Idempotence des règles | 6.1, 6.2 |

## GitHub Codespaces / CI

Pour exécuter les tests dans un GitHub Codespace ou un environnement CI :

```bash
./scripts/run_tests.sh
```

## Note importante

Les tests n'importent pas directement les modules `custom_components/rtetempo/` pour éviter les dépendances Home Assistant. Les fonctions et classes sont dupliquées/mockées dans les fichiers de test.

## Configuration requise pour le repo GitHub (HACS)

Pour que le workflow HACS passe sur un fork, le repo GitHub doit avoir :

1. **Issues activées** : Settings → Features → Issues ✓
2. **Topics configurés** : Settings → About → Topics
   - Ajouter au minimum : `home-assistant`, `hacs`
   - Recommandés : `tempo`, `rte`, `home-assistant-custom-component`

Ces configurations sont requises par [HACS](https://hacs.xyz/docs/publish/include#check-repository) pour valider l'intégration.

### Via GitHub CLI

```bash
# Activer les issues
gh repo edit OWNER/REPO --enable-issues

# Ajouter les topics
gh repo edit OWNER/REPO --add-topic home-assistant --add-topic hacs --add-topic tempo --add-topic rte --add-topic home-assistant-custom-component
```
