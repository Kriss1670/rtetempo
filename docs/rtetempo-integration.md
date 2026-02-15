# Documentation: Intégration RTE Tempo

## Vue d'ensemble

L'intégration RTE Tempo pour Home Assistant permet de récupérer et afficher les couleurs du calendrier Tempo EDF via l'API officielle RTE. Elle fournit des sensors, un calendrier et des binary sensors pour automatiser votre maison en fonction des tarifs Tempo.

## Prérequis

### Compte API RTE

1. Créer un compte sur [data.rte-france.com](https://data.rte-france.com)
2. S'abonner à l'API "Tempo Like Supply Contract"
3. Récupérer le `client_id` et `client_secret` de votre application

## Installation

### Via HACS (recommandé)

1. Ajouter le dépôt personnalisé dans HACS
2. Rechercher "RTE Tempo"
3. Installer et redémarrer Home Assistant

### Manuelle

Copier le dossier `custom_components/rtetempo` dans votre répertoire `config/custom_components/`.

## Configuration

### Ajout de l'intégration

1. Aller dans **Paramètres > Appareils et services**
2. Cliquer sur **Ajouter une intégration**
3. Rechercher "RTE Tempo"
4. Entrer vos identifiants API :
   - `client_id` : ID de votre application RTE
   - `client_secret` : Secret de votre application RTE
   - `forecast_enabled` : Activer les prévisions Open DPE (optionnel)

### Options (après installation)

Pour modifier les options après l'installation :
1. Aller dans **Paramètres > Appareils et services > RTE Tempo**
2. Cliquer sur **Configurer**

| Option | Description | Défaut |
|--------|-------------|--------|
| `adjusted_days` | Mode calendrier 6h-6h (voir détails ci-dessous) | `false` |
| `forecast_enabled` | Active les sensors de prévision J+2 à J+7 via Open DPE | `false` |

Note : `adjusted_days` n'est disponible que dans les options (pas lors de l'installation initiale).

#### Option `adjusted_days` (mode 6h-6h)

Cette option modifie **uniquement l'affichage du calendrier**, pas les sensors.

| Mode | Événements calendrier | Cas d'usage |
|------|----------------------|-------------|
| `false` (défaut) | Journée entière (minuit-minuit) | Affichage simple dans l'UI |
| `true` | Heures précises (6h-6h) | **Automatisations basées sur le calendrier** |

**Pourquoi activer `adjusted_days: true` ?**

Les jours Tempo changent à **6h du matin**, pas à minuit. Avec `adjusted_days: true` :
- L'événement calendrier change d'état exactement à 6h00
- Permet de déclencher des automatisations sur le changement d'événement calendrier
- Évite les race conditions entre sensors à 6h (couleur vs heures creuses)

**Exemple d'automatisation avec calendrier 6h-6h :**
```yaml
automation:
  - alias: "Jour rouge détecté à 6h"
    trigger:
      - platform: state
        entity_id: calendar.rte_tempo_calendrier
        to: "on"
    condition:
      # Vérifier si c'est un jour rouge via l'attribut message (contient 🔴, ⚪, ou 🔵)
      - condition: template
        value_template: "{{ '🔴' in state_attr('calendar.rte_tempo_calendrier', 'message') }}"
    action:
      - service: switch.turn_off
        target:
          entity_id: switch.chauffe_eau
```

**Note importante :** Les sensors (`couleur_actuelle`, `prochaine_couleur`, etc.) ne sont pas affectés par cette option - ils utilisent toujours la logique basée sur l'heure actuelle (seuil 6h).

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      API RTE Tempo                           │
│         data.rte-france.com/open_api/tempo_like_...         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    api_worker.py                             │
│  APIWorker (Thread autonome)                                │
│  - Authentification OAuth2                                  │
│  - Récupération des données (364 jours passés + 2 futurs)   │
│  - Cache en mémoire                                         │
│  - Refresh intelligent                                      │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
        ┌──────────┐   ┌──────────┐   ┌──────────┐
        │ Sensors  │   │ Calendar │   │ Binary   │
        │          │   │          │   │ Sensors  │
        └──────────┘   └──────────┘   └──────────┘
```

## Entités créées

### Sensors

| Entity ID | Nom | Description |
|-----------|-----|-------------|
| `sensor.rte_tempo_couleur_actuelle` | Couleur actuelle | Bleu, Blanc ou Rouge |
| `sensor.rte_tempo_couleur_actuelle_emoji` | Couleur actuelle (visuel) | 🔵, ⚪ ou 🔴 |
| `sensor.rte_tempo_prochaine_couleur` | Prochaine couleur | Couleur du lendemain |
| `sensor.rte_tempo_prochaine_couleur_emoji` | Prochaine couleur (visuel) | Emoji |
| `sensor.rte_tempo_prochaine_couleur_changement` | Changement couleur | Timestamp du prochain changement |
| `sensor.rte_tempo_cycle_jours_restants_bleu` | Jours restants Bleu | Jours bleus restants dans le cycle |
| `sensor.rte_tempo_cycle_jours_restants_blanc` | Jours restants Blanc | Jours blancs restants (max 43) |
| `sensor.rte_tempo_cycle_jours_restants_rouge` | Jours restants Rouge | Jours rouges restants (max 22) |
| `sensor.rte_tempo_cycle_jours_deja_places_bleu` | Jours placés Bleu | Jours bleus déjà utilisés |
| `sensor.rte_tempo_cycle_jours_deja_places_blanc` | Jours placés Blanc | Jours blancs déjà utilisés |
| `sensor.rte_tempo_cycle_jours_deja_places_rouge` | Jours placés Rouge | Jours rouges déjà utilisés |
| `sensor.rte_tempo_cycle_prochaine_reinitialisation` | Prochain cycle | Date du 1er septembre |
| `sensor.rte_tempo_heures_creuses_changement` | Changement HC/HP | Prochain changement heures creuses |

### Binary Sensors

| Entity ID | Nom | Description |
|-----------|-----|-------------|
| `sensor.rte_tempo_heures_creuses` | Heures Creuses | ON si heures creuses (22h-6h) |

### Calendrier

| Entity ID | Nom | Description |
|-----------|-----|-------------|
| `calendar.rte_tempo_calendrier` | Calendrier | Calendrier avec les couleurs Tempo |

## Constantes Tempo

| Constante | Valeur | Description |
|-----------|--------|-------------|
| Heure de changement | 6h | Les jours Tempo changent à 6h du matin |
| Début heures creuses | 22h | Début des heures creuses |
| Jours rouges max | 22 | Maximum de jours rouges par cycle |
| Jours blancs max | 43 | Maximum de jours blancs par cycle |
| Début de cycle | 1er septembre | Début du cycle annuel Tempo |

## API Worker

L'`APIWorker` est un thread autonome qui :

1. **Authentification** : Gère le token OAuth2 avec renouvellement automatique
2. **Récupération** : Interroge l'API RTE pour les 364 derniers jours + 2 jours futurs
3. **Cache** : Stocke les données en mémoire pour accès rapide
4. **Refresh intelligent** : 
   - Attend la confirmation de la couleur du lendemain (vers 10h40)
   - Réessaie en cas d'erreur (10 minutes)
   - Attend le lendemain si données complètes

### Formats de données

L'API Worker maintient deux formats de données :

| Format | Variable | Usage |
|--------|----------|-------|
| Date | `_tempo_days_date` | Événements journée entière |
| DateTime | `_tempo_days_time` | Événements avec heures (6h-6h) |

L'option `adjusted_days` détermine quel format est utilisé pour le calendrier.

## Automatisations

### Exemple : Notification jour rouge

```yaml
automation:
  - alias: "Notification Tempo Rouge"
    trigger:
      - platform: state
        entity_id: sensor.rte_tempo_prochaine_couleur
        to: "Rouge"
    action:
      - service: notify.mobile_app
        data:
          title: "⚠️ Tempo Rouge demain"
          message: "Pensez à réduire votre consommation !"
```

### Exemple : Désactiver chauffe-eau jour rouge

```yaml
automation:
  - alias: "Chauffe-eau Tempo"
    trigger:
      - platform: time
        at: "06:00:00"
    condition:
      - condition: state
        entity_id: sensor.rte_tempo_couleur_actuelle
        state: "Rouge"
    action:
      - service: switch.turn_off
        target:
          entity_id: switch.chauffe_eau
```

## Dépendances

- `requests` : Requêtes HTTP
- `requests_oauthlib` : Authentification OAuth2
- `oauthlib` : Gestion des tokens OAuth

## Liens utiles

- [API RTE Data](https://data.rte-france.com)
- [Documentation API Tempo](https://data.rte-france.com/catalog/-/api/consumption/Tempo-Like-Supply-Contract/v1.1)
- [Tarifs Tempo EDF](https://particulier.edf.fr/fr/accueil/gestion-contrat/options/tempo.html)
