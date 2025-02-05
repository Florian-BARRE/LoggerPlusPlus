# LoggerPlusPlus

## Introduction

**LoggerPlusPlus** est une bibliothèque Python conçue pour enrichir et améliorer le module standard `logging`. Celui-ci
présente certaines limitations en termes d'ergonomie et de fonctionnalités, notamment l'absence de coloration des logs,
un formatage peu uniforme et une gestion limitée de la taille des fichiers de journalisation.

LoggerPlusPlus pallie ces insuffisances en proposant une présentation structurée et colorée des logs, une gestion
centralisée des différents enregistreurs (`loggers`) et des fonctionnalités avancées, telles que le suivi des
performances et l'analyse des logs après exécution.

Cette bibliothèque s'adresse à tout professionnel souhaitant une solution de journalisation efficace et flexible,
adaptée aussi bien aux projets simples qu'aux applications complexes nécessitant plusieurs loggers gérés de manière
homogène. Grâce à son `LoggerManager`, elle garantit une configuration centralisée et une expérience de suivi optimisée.
Son efficacité et ses nombreuses fonctionnalités en font un outil particulièrement adapté aux développeurs
d'applications complexes, ainsi qu'aux data scientists et analystes ayant besoin d’un suivi détaillé des processus.

## Installation

### Via PyPI

Pour installer la bibliothèque via le gestionnaire de paquets officiel :

```bash
pip install loggerplusplus
```

### Via GitHub

Pour accéder à la dernière version en développement ou contribuer au projet :

```bash
git clone https://github.com/votre-utilisateur/loggerplusplus.git
cd loggerplusplus
pip install .
```

## Logger

Le composant central de **LoggerPlusPlus** est l’objet `Logger`, qui permet la gestion et l’affichage des logs. Pour
l’utiliser, commencez par l’importer :

```python
from loggerplusplus import Logger
```

La configuration du `Logger` repose sur un objet `LoggerConfig`, qui regroupe plusieurs sous-configurations :

- **`LogLevelsConfig`** : Gère les niveaux de logs autorisés pour l’affichage, l’écriture et les décorateurs.
- **`PlacementConfig`** : Détermine la mise en forme et la structuration des logs (taille des identifiants, format
  d'affichage, etc.).
- **`MonitorConfig`** : Contrôle la gestion de l’espace disque occupé par les fichiers de logs.

### Paramètres de Configuration

Voici les principales options configurables pour un `Logger` :

- **`identifier` (str)** : Nom du logger, utilisé comme source des logs (par défaut `"unknown"`).
- **`colors` (BaseColors)** : Palette de couleurs utilisée pour les logs (ex. `ClassicColors`).
- **`path` (str)** : Répertoire où seront stockés les fichiers de logs (par défaut `"logs"`).
- **`follow_logger_manager_rules` (bool)** : Si `True`, applique les règles définies par le `LoggerManager`. (Ce
  paramètre est largement détaillé dans la partie `LoggerManager` de la documentation).

#### Configuration des niveaux de logs (`LogLevelsConfig`)

- **`decorator_log_level` (LogLevels)** : Niveau de log autorisé pour les décorateurs (par défaut `DEBUG`).
- **`print_log_level` (LogLevels)** : Niveau de log autorisé pour l’affichage (par défaut `DEBUG`).
- **`file_log_level` (LogLevels)** : Niveau de log autorisé pour l’écriture dans les fichiers (par défaut `DEBUG`).
- **`print_log` (bool)** : Active ou désactive l’affichage des logs dans la console.
- **`write_to_file` (bool)** : Active ou désactive l’écriture des logs dans un fichier.

#### Configuration de l’affichage (`PlacementConfig`)

- **`identifier_max_width` (int)** : Largeur maximale de l’identifiant (troncature si dépassement, `0` pour
  automatique).
- **`level_max_width` (int)** : Largeur maximale du niveau de log.
- **`filename_lineno_max_width` (int)** : Largeur maximale pour le nom du fichier et le numéro de ligne (`15` par
  défaut).
- **`placement_improvement` (bool)** : Ajuste dynamiquement la largeur des éléments pour une meilleure lisibilité.

#### Gestion des fichiers de logs (`MonitorConfig`)

- **`display_monitoring` (bool)** : Affiche les informations de suivi de l’espace disque.
- **`files_monitoring` (bool)** : Active la suppression automatique des fichiers de logs trop volumineux.
- **`file_size_unit` (str)** : Unité de taille des fichiers (`"Go"`, `"Mo"`, etc.).
- **`file_size_precision` (int)** : Nombre de chiffres après la virgule pour l’affichage des tailles.
- **`disk_alert_threshold_percent` (float)** : Seuil d’alerte de saturation du disque (ex. `0.8` pour 80%).
- **`log_files_size_alert_threshold_percent` (float)** : Seuil d’alerte pour les fichiers de logs (ex. `0.2` pour 20%).
- **`max_log_file_size` (float)** : Taille maximale autorisée pour un fichier de log avant suppression des plus
  anciens (`1.0 Go` par défaut).

### Instanciation

Le `Logger` offre une grande flexibilité d’instanciation. Il peut être configuré de plusieurs manières :

- En passant directement un objet `LoggerConfig`.
- En spécifiant uniquement les clés des sous-configurations (`LogLevelsConfig`, `PlacementConfig`, `MonitorConfig`).
- En utilisant un dictionnaire contenant les paramètres souhaités.

#### Instanciation avec configurations explicites

```python
from loggerplusplus import Logger, LoggerConfig, LogLevelsConfig, PlacementConfig, MonitorConfig, LogLevels
from loggerplusplus.colors import ClassicColors

# Définition des sous-configurations
log_levels_config = LogLevelsConfig(print_log_level=LogLevels.INFO)
placement_config = PlacementConfig(identifier_max_width=15)
monitor_config = MonitorConfig(files_monitoring=True)

# Instanciation du logger avec une configuration complète
logger_config = LoggerConfig(
    identifier="logger_implicite_config",
    log_levels_config=log_levels_config,
    placement_config=placement_config,
    monitor_config=monitor_config,
    colors=ClassicColors,
    path="logs",
    follow_logger_manager_rules=False,
)

logger = Logger(config=logger_config)  # Instanciation du logger
```

#### Instanciation avec des paramètres de premier niveau

```python
logger = Logger(
    identifier="logger_explicite_sous_config",
    log_levels_config=log_levels_config,
    placement_config=placement_config,
    monitor_config=monitor_config,
    colors=ClassicColors,
    path="logs",
    follow_logger_manager_rules=False,
)
```

#### Instanciation avec des paramètres de second niveau

Il est également possible de renseigner directement les paramètres souhaités sans passer par les sous-configurations.

```python
logger = Logger(
    identifier="logger_implicite",
    print_log_level=LogLevels.INFO,
    identifier_max_width=15,
    files_monitoring=True,
    colors=ClassicColors,
    path="logs",
    follow_logger_manager_rules=False,
)
```

> ⚠️ Il est impératif de spécifier les paramètres lors de l’instanciation. L'utilisation de `Logger(logger_config)` ne
> fonctionnera pas.

#### Instanciation à partir d’un dictionnaire

```python
dict_config = {
    "identifier": "logger_dict",
    "print_log_level": LogLevels.INFO,
    "identifier_max_width": 15,
    "files_monitoring": True,
    "colors": ClassicColors,
    "path": "logs",
    "follow_logger_manager_rules": False,
}

logger = Logger(**dict_config)
```

> Tout paramètre non renseigné prendra sa valeur par défaut renseignée dans la partie `Paramètres de Configuration` de
> la documentation.

### Utilisation

#### Niveaux de logs

LoggerPlusPlus propose différents niveaux de logs, du plus critique au moins important. Ces niveaux sont définis dans
l'énumération `LogLevels` :

```python
from enum import IntEnum
import logging


class LogLevels(IntEnum):
    """
    Enumeration des niveaux de logs pour assurer une utilisation explicite et claire.
    """
    FATAL = logging.FATAL  # Sévérité la plus haute, distincte de CRITICAL
    CRITICAL = logging.CRITICAL
    ERROR = logging.ERROR
    WARNING = logging.WARNING
    INFO = logging.INFO
    DEBUG = logging.DEBUG
    NOTSET = logging.NOTSET
```

Chaque niveau de log est associé à une méthode du logger permettant d'enregistrer des messages :

```python
from loggerplusplus import Logger

logger = Logger(identifier="logger")

logger.debug("Ceci est un message de débogage")
logger.info("Ceci est un message d'information")
logger.warning("Ceci est un avertissement")
logger.error("Ceci est un message d'erreur")
logger.critical("Ceci est un message critique")
logger.fatal("Ceci est un message fatal")
```

#### Définition manuelle du niveau de log

Il est également possible de spécifier manuellement le niveau de log en utilisant la méthode `log()` :

```python
from loggerplusplus import LogLevels

logger.log("Ceci est un message de débogage", LogLevels.DEBUG)
logger.log("Ceci est un message d'information", LogLevels.INFO)
logger.log("Ceci est un avertissement", LogLevels.WARNING)
logger.log("Ceci est un message d'erreur", LogLevels.ERROR)
logger.log("Ceci est un message critique", LogLevels.CRITICAL)
logger.log("Ceci est un message fatal", LogLevels.FATAL)
```

## LoggerManager

Dans un contexte où plusieurs loggers sont utilisés, il est souvent nécessaire de centraliser leur configuration et leur
gestion. C’est précisément le rôle du `LoggerManager`.

Le `LoggerManager` est une classe globale qui ne nécessite pas d’instanciation. Ses attributs peuvent être modifiés afin
d'agir sur le comportement des loggers qui lui sont associés.

Le paramètre `follow_logger_manager_rules` du `Logger` permet de déterminer si un logger doit suivre les règles définies
par le `LoggerManager`. Si ce paramètre est activé, le logger héritera automatiquement des configurations globales
définies par le `LoggerManager`, sans qu’il soit nécessaire de redéfinir chaque paramètre individuellement.

Il est néanmoins possible d’activer `follow_logger_manager_rules` tout en modifiant certains paramètres spécifiques du
logger. Dans ce cas, les configurations du `LoggerManager` seront appliquées sauf pour les paramètres explicitement
définis au niveau du logger.

Le `LoggerManager` possède un attribut `global_config` contenant la configuration globale des loggers. Cet attribut peut
être modifié pour ajuster les paramètres globaux des loggers.

#### Options supplémentaires du `LoggerManager`

Certaines options avancées permettent de modifier intelligemment `global_config` en fonction des loggers instanciés et
de leurs paramètres :

- **`LoggerManager.enable_files_logs_monitoring_only_for_one_logger` (bool)** : Active le monitoring des fichiers de
  logs pour un seul logger (le premier avec cette option activée).
- **`LoggerManager.enable_dynamic_config_update` (bool)** : Permet de mettre à jour dynamiquement les configurations des
  loggers en fonction du `LoggerManager`.
- **`LoggerManager.enable_unique_logger_identifier` (bool)** : Rend les identifiants des loggers uniques (ajoute un
  préfixe pour éviter les doublons).

### Configuration du `LoggerManager`

#### Configuration de la configuration globale (type: `LoggerConfig`)

```python
from loggerplusplus import LoggerManager, LogLevels, LoggerConfig, logger_colors

LoggerManager.global_config = LoggerConfig.from_kwargs(
    colors=logger_colors.ClassicColors,
    path="logs",
    # LogLevels
    decorator_log_level=LogLevels.DEBUG,
    print_log_level=LogLevels.DEBUG,
    file_log_level=LogLevels.DEBUG,
    # Loggers Output
    print_log=True,
    write_to_file=True,
    # Monitoring
    display_monitoring=False,
    files_monitoring=False,
    file_size_unit="Go",
    disk_alert_threshold_percent=0.8,
    log_files_size_alert_threshold_percent=0.2,
    max_log_file_size=1.0,
    # Placement
    identifier_max_width=15,
    filename_lineno_max_width=15,
)
```

#### Configuration des options du `LoggerManager`

```python
LoggerManager.enable_files_logs_monitoring_only_for_one_logger = True
LoggerManager.enable_dynamic_config_update = True
LoggerManager.enable_unique_logger_identifier = True
```

> ⚠️ Seuls les loggers ayant l’option `follow_logger_manager_rules` activée seront concernés par les configurations et
> les options définies dans le `LoggerManager`.

## Décorateurs

**LoggerPlusPlus** propose des décorateurs permettant de journaliser automatiquement l'exécution des fonctions et d'en
mesurer la durée d'exécution.

### Logger une fonction : **`@log`**

Le décorateur `@log` permet de journaliser automatiquement l'exécution d'une fonction. Il affiche le début de
l'exécution de la fonction décorée ainsi que ses paramètres d'entrée.

#### Paramètres

- **`param_logger` (Logger | str | Callable)** : Logger à utiliser pour la journalisation.
    - Peut être une chaîne de caractères représentant le nom de l'identifiant du logger, qui sera automatiquement
      récupéré parmi les loggers instanciés ou créé si inexistant.
    - Peut être une instance de `Logger`.
    - Peut être une fonction lambda retournant un logger, utile notamment pour les loggers définis comme attributs d’une
      classe.
- **`log_level` (LogLevels)** : Niveau de log à utiliser pour la journalisation (par défaut `DEBUG`).

#### Exemple d'utilisation

Log via identifiant :

```python
from loggerplusplus import Logger, log

logger = Logger(identifier="logger_decorator_log")


@log(param_logger="logger_decorator_log")  # Récupère le logger via son identifiant
def test1(a, b):
    return a + b


@log(param_logger="autre_logger")  # Crée un logger avec l'identifiant "autre_logger"
def test2(a, b):
    return a + b
```

Log via instance :

```python
logger = Logger(identifier="logger_decorator_log")


@log(param_logger=logger)
def test(a, b):
    return a + b
```

Log via callable pour un logger d'une classe :

```python
class MyClass:
    def __init__(self):
        self.logger = Logger(identifier="class_logger")

    @log(param_logger=lambda self: self.logger)
    def process_data(self):
        import time
        time.sleep(1)
```

### Mesurer le temps d'exécution : **`@time_tracker`**

Le décorateur `@time_tracker` permet de mesurer automatiquement la durée d'exécution d'une fonction. Il affiche le temps
d'exécution de la fonction décorée.

#### Paramètres

- **`param_logger` (Logger | str | Callable)** : Logger à utiliser pour la journalisation.
    - Peut être une chaîne de caractères représentant le nom de l'identifiant du logger, qui sera automatiquement
      récupéré parmi les loggers instanciés ou créé si inexistant.
    - Peut être une instance de `Logger`.
    - Peut être une fonction lambda retournant un logger, utile notamment pour les loggers définis comme attributs d’une
      classe.
- **`log_level` (LogLevels)** : Niveau de log à utiliser pour la journalisation (par défaut `DEBUG`).

L'utilisation est identique à `@log`.

## LogAnalyzer

à venir ...

### Auteur

Projet créé et maintenu par **Florian BARRE**.  
Pour toute question ou contribution, n'hésitez pas à me contacter.
[Mon Site](https://florianbarre.fr/) | [Mon LinkedIn](www.linkedin.com/in/barre-florian) | [Mon GitHub](https://github.com/Florian-BARRE)
