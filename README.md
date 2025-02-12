# LoggerPlusPlus - English documentation

## Introduction

**LoggerPlusPlus** is a Python library designed to enhance and improve the standard `logging` module. The default module has certain limitations in terms of usability and features, such as the lack of log coloring, inconsistent formatting, and limited file size management.

LoggerPlusPlus addresses these shortcomings by providing structured and colored log presentation, centralized management of multiple `loggers`, and advanced functionalities, such as performance tracking and post-execution log analysis.

This library is aimed at professionals looking for an efficient and flexible logging solution, suitable for both simple projects and complex applications requiring multiple loggers managed in a consistent manner. Thanks to its `LoggerManager`, it ensures centralized configuration and an optimized monitoring experience. Its efficiency and numerous features make it particularly useful for developers of complex applications, as well as data scientists and analysts needing detailed process tracking.

## Installation

### Via PyPI with pip

To install the library via the official package manager:

```bash
pip install loggerplusplus
```

### Via GitHub

To access the latest development version or contribute to the project:

```bash
git clone https://github.com/your-username/loggerplusplus.git
cd loggerplusplus
pip install .
```

## Logger

The central component of **LoggerPlusPlus** is the `Logger` object, which manages and displays logs. To use it, start by importing it:

```python
from loggerplusplus import Logger
```

The `Logger` configuration relies on a `LoggerConfig` object, which groups several sub-configurations:

- **`LogLevelsConfig`**: Manages the log levels allowed for display, writing, and decorators.
- **`PlacementConfig`**: Defines the log formatting and structuring (identifier length, display format, etc.).
- **`MonitorConfig`**: Controls disk space usage for log files.

### Configuration Parameters

Here are the main configurable options for a `Logger`:

- **`identifier` (str)**: Name of the logger, used as the log source (default `"unknown"`).
- **`colors` (BaseColors)**: Color palette used for logs (e.g., `ClassicColors`).
- **`path` (str)**: Directory where log files will be stored (default `"logs"`).
- **`follow_logger_manager_rules` (bool)**: If `True`, applies the rules defined by the `LoggerManager`. (This parameter is extensively detailed in the `LoggerManager` section of the documentation).

#### Log Level Configuration (`LogLevelsConfig`)

- **`decorator_log_level` (LogLevels)**: Log level allowed for decorators (default `DEBUG`).
- **`print_log_level` (LogLevels)**: Log level allowed for display (default `DEBUG`).
- **`file_log_level` (LogLevels)**: Log level allowed for file writing (default `DEBUG`).
- **`print_log` (bool)**: Enables or disables log display in the console.
- **`write_to_file` (bool)**: Enables or disables log file writing.

#### Display Configuration (`PlacementConfig`)

- **`identifier_max_width` (int)**: Maximum identifier width (truncated if exceeded, `0` for automatic).
- **`level_max_width` (int)**: Maximum log level width.
- **`filename_lineno_max_width` (int)**: Maximum width for filename and line number (`15` by default).
- **`placement_improvement` (bool)**: Dynamically adjusts element widths for better readability.

#### Log File Management (`MonitorConfig`)

- **`display_monitoring` (bool)**: Displays disk space monitoring information.
- **`files_monitoring` (bool)**: Enables automatic deletion of oversized log files.
- **`file_size_unit` (str)**: File size unit (`"GB"`, `"MB"`, etc.).
- **`file_size_precision` (int)**: Number of decimal places for size display.
- **`disk_alert_threshold_percent` (float)**: Disk saturation alert threshold (e.g., `0.8` for 80%).
- **`log_files_size_alert_threshold_percent` (float)**: Alert threshold for log file size (e.g., `0.2` for 20%).
- **`max_log_file_size` (float)**: Maximum allowed log file size before deleting older ones (`1.0 GB` by default).

### Instantiation

The `Logger` offers great flexibility in instantiation. It can be configured in several ways:

- By passing a `LoggerConfig` object directly.
- By specifying only the keys of the sub-configurations (`LogLevelsConfig`, `PlacementConfig`, `MonitorConfig`).
- By using a dictionary containing the desired parameters.

#### Instantiation with Explicit Configurations

```python
from loggerplusplus import Logger, LoggerConfig, LogLevelsConfig, PlacementConfig, MonitorConfig, LogLevels
from loggerplusplus.colors import ClassicColors

# Define sub-configurations
log_levels_config = LogLevelsConfig(print_log_level=LogLevels.INFO)
placement_config = PlacementConfig(identifier_max_width=15)
monitor_config = MonitorConfig(files_monitoring=True)

# Instantiate logger with a complete configuration
logger_config = LoggerConfig(
    identifier="logger_explicit_config",
    log_levels_config=log_levels_config,
    placement_config=placement_config,
    monitor_config=monitor_config,
    colors=ClassicColors,
    path="logs",
    follow_logger_manager_rules=False,
)

logger = Logger(config=logger_config)  # Logger instantiation
```

#### Instantiation with Top-Level Parameters

```python
logger = Logger(
    identifier="logger_explicit_sub_config",
    log_levels_config=log_levels_config,
    placement_config=placement_config,
    monitor_config=monitor_config,
    colors=ClassicColors,
    path="logs",
    follow_logger_manager_rules=False,
)
```

#### Instantiation with Second-Level Parameters

You can also specify parameters directly without using sub-configurations.

```python
logger = Logger(
    identifier="logger_implicit",
    print_log_level=LogLevels.INFO,
    identifier_max_width=15,
    files_monitoring=True,
    colors=ClassicColors,
    path="logs",
    follow_logger_manager_rules=False,
)
```

> ⚠️ Parameters must be specified during instantiation. Using `Logger(logger_config)` will not work.

#### Instantiation from a Dictionary

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

> Any unspecified parameter will take its default value as indicated in the `Configuration Parameters` section.

### Usage

#### Log Levels

LoggerPlusPlus provides various log levels, from the most critical to the least important. These levels are defined in the `LogLevels` enumeration:

```python
from enum import IntEnum
import logging


class LogLevels(IntEnum):
    """
    Enumeration of log levels for clear and explicit use.
    """
    FATAL = logging.FATAL  # Highest severity, distinct from CRITICAL
    CRITICAL = logging.CRITICAL
    ERROR = logging.ERROR
    WARNING = logging.WARNING
    INFO = logging.INFO
    DEBUG = logging.DEBUG
    NOTSET = logging.NOTSET
```

Each log level is associated with a logger method for recording messages:

```python
from loggerplusplus import Logger

logger = Logger(identifier="logger")

logger.debug("This is a debug message")
logger.info("This is an informational message")
logger.warning("This is a warning")
logger.error("This is an error message")
logger.critical("This is a critical message")
logger.fatal("This is a fatal message")
```

---

#### Manually Defining the Log Level

It is also possible to manually specify the log level using the `log()` method:

```python
from loggerplusplus import LogLevels

logger.log("This is a debug message", LogLevels.DEBUG)
logger.log("This is an informational message", LogLevels.INFO)
logger.log("This is a warning", LogLevels.WARNING)
logger.log("This is an error message", LogLevels.ERROR)
logger.log("This is a critical message", LogLevels.CRITICAL)
logger.log("This is a fatal message", LogLevels.FATAL)
```

## LoggerManager

In a context where multiple loggers are used, it is often necessary to centralize their configuration and management. This is precisely the role of the `LoggerManager`.

The `LoggerManager` is a global class that does not require instantiation. Its attributes can be modified to affect the behavior of the loggers associated with it.

The `follow_logger_manager_rules` parameter of the `Logger` determines whether a logger should follow the rules defined by the `LoggerManager`. If this parameter is enabled, the logger will automatically inherit the global configurations defined by the `LoggerManager`, without the need to redefine each parameter individually.

However, it is possible to enable `follow_logger_manager_rules` while modifying specific logger parameters. In this case, the `LoggerManager` configurations will be applied except for the explicitly defined parameters at the logger level.

The `LoggerManager` has an attribute `global_config` containing the global configuration for loggers. This attribute can be modified to adjust the global settings of loggers.

#### Additional Options in `LoggerManager`

Some advanced options allow for intelligent modifications to `global_config` based on instantiated loggers and their parameters:

- **`LoggerManager.enable_files_logs_monitoring_only_for_one_logger` (bool)**: Enables log file monitoring for a single logger (the first one with this option enabled).
- **`LoggerManager.enable_dynamic_config_update` (bool)**: Allows dynamically updating logger configurations based on the `LoggerManager`.
- **`LoggerManager.enable_unique_logger_identifier` (bool)**: Ensures unique logger identifiers (adds a prefix to avoid duplicates).

### Configuring `LoggerManager`

#### Configuring the Global Configuration (type: `LoggerConfig`)

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
    file_size_unit="GB",
    disk_alert_threshold_percent=0.8,
    log_files_size_alert_threshold_percent=0.2,
    max_log_file_size=1.0,
    # Placement
    identifier_max_width=15,
    filename_lineno_max_width=15,
)
```

#### Configuring `LoggerManager` Options

```python
LoggerManager.enable_files_logs_monitoring_only_for_one_logger = True
LoggerManager.enable_dynamic_config_update = True
LoggerManager.enable_unique_logger_identifier = True
```

> ⚠️ Only loggers with `follow_logger_manager_rules` enabled will be affected by the configurations and options defined in the `LoggerManager`.

## Decorators

**LoggerPlusPlus** provides decorators that allow automatic logging of function execution and execution time measurement.

### Logging a Function: **`@log`**

The `@log` decorator automatically logs the execution of a function. It displays the start of the decorated function's execution as well as its input parameters.

#### Parameters

- **`param_logger` (Logger | str | Callable)**: Logger to use for logging.
    - Can be a string representing the logger's identifier, which will be automatically retrieved from instantiated loggers or created if nonexistent.
    - Can be an instance of `Logger`.
    - Can be a lambda function returning a logger, useful for loggers defined as class attributes.
- **`log_level` (LogLevels)**: Log level to use for logging (default `DEBUG`).

#### Usage Example

Logging via identifier:

```python
from loggerplusplus import Logger, log

logger = Logger(identifier="logger_decorator_log")


@log(param_logger="logger_decorator_log")  # Retrieves the logger via its identifier
def test1(a, b):
    return a + b


@log(param_logger="another_logger")  # Creates a logger with the identifier "another_logger"
def test2(a, b):
    return a + b
```

Logging via instance:

```python
logger = Logger(identifier="logger_decorator_log")


@log(param_logger=logger)
def test(a, b):
    return a + b
```

Logging via callable for a class logger:

```python
class MyClass:
    def __init__(self):
        self.logger = Logger(identifier="class_logger")

    @log(param_logger=lambda self: self.logger)
    def process_data(self):
        import time
        time.sleep(1)
```

### Measuring Execution Time: **`@time_tracker`**

The `@time_tracker` decorator automatically measures the execution time of a function. It logs the execution duration of the decorated function.

#### Parameters

- **`param_logger` (Logger | str | Callable)**: Logger to use for logging.
    - Can be a string representing the logger's identifier, which will be automatically retrieved from instantiated loggers or created if nonexistent.
    - Can be an instance of `Logger`.
    - Can be a lambda function returning a logger, useful for loggers defined as class attributes.
- **`log_level` (LogLevels)**: Log level to use for logging (default `DEBUG`).

Usage is identical to `@log`.

Decorators combination is supported.

```python
class MyClass:
    def __init__(self):
        self.logger = Logger(identifier="class_logger")


    @track_time(param_logger=lambda self: self.logger)
    @log(param_logger=lambda self: self.logger)
    def process_data(self):
        import time
        time.sleep(1)
```




## LogAnalyser

The `LogAnalyser` class is a powerful tool for analyzing execution logs generated by LoggerPlusPlus's time tracking functionality. It provides capabilities to analyze and visualize function execution times and occurrences from log files.


### Basic Usage

```python
from loggerplusplus.analyser import LogAnalyser

# Initialize the analyzer with your log file
analyser = LogAnalyser("path/to/your/logfile.log")

analyser.analyse_time_tracker()
analyser.analyse_func_occurences()
```

### Methods

#### analyze_time_tracker

This method analyzes the execution times of specified functions and generates a detailed plot. It provides insights into the performance of your functions by visualizing their execution durations over time. The plot includes average execution times, making it easier to identify performance bottlenecks and optimize your code effectively.

```python
analyser.analyse_time_tracker(
    func_names=None,                     # Function name(s) to analyze
    identifier=None,                     # Log identifier(s) to filter
    min_execution_time_ms=0.0,           # Minimum execution time to include
    max_execution_time_ms=float('inf'),  # Maximum execution time to include
    is_sort_by_avg_time=True,            # Sort functions by average time
    nb_max_funcs=float('inf'),           # Maximum number of functions to display
    is_sort_order_descending=True        # Order by maximum execution time
)
```

Parameters:
- `func_names` (str | list[str] | None): Function name(s) to filter.
  - Single string: analyze only that function
  - List of strings: analyze only those functions
  - None: analyze all functions
- `identifier` (str | list[str] | None): Log identifier(s) to filter
  - Single string: analyze logs with that identifier
  - List of strings: analyze logs with those identifiers
  - None: analyze all log entries
 - `min_execution_time_ms` (float): Minimum execution time in milliseconds to include
  - `max_execution_time_ms` (float): Maximum execution time in milliseconds to include
  - `is_sort_by_avg_time` (bool): If True, sort functions by average execution time
    - consider setting it to false for better performance    
  - `nb_max_funcs` (int): Maximum number of functions to display in the plot 
    - ignored if is_sort_by_avg_time is False
  - `is_sort_order_descending` (bool): If True, order functions by maximum execution time
    - ignored if is_sort_by_avg_time is False

Example usage:

```python
# Analyze all functions with execution times between 100ms and 1000ms
analyser.analyse_time_tracker(
    min_execution_time_ms=100,
    max_execution_time_ms=1000
)

# Analyze specific functions with specific identifier
analyser.analyse_time_tracker(
    func_names=["process_data", "calculate_metrics"],
    identifier=["worker1", "worker2"],
)
```

#### analyse_func_occurences

This method analyzes the number of occurrences of each function in the log file and generates a bar plot.

```python
analyser.analyse_func_occurences(
    occurrence_threshold=1,   # Minimum number of occurrences to include
    nb_func=10,               # Number of functions to display
    top_occ=True,             # Display highest occurrences first
    identifier=None           # Log identifier(s) to filter
)
```

Parameters:
- `occurrence_threshold` (int): Minimum number of occurrences for a function to be included
- `nb_func` (int): Number of top functions to display (-1 for all)
   - Set to -1 it  runs a sorting algorithm, consider letting the default value for better performance
- `top_occ` (bool): If True, display functions with highest occurrences first
- `identifier` (str | list[str] | None): Log identifier(s) to filter
  - Single string: analyze logs with that identifier
  - List of strings: analyze logs with those identifiers
  - None: analyze all log entries

Example usage:

```python
# Analyze all functions with at least 5 occurrences
analyser.analyse_func_occurences(occurrence_threshold=5)

# Show top 10 most frequent functions
analyser.analyse_func_occurences(
    nb_func=10,
    top_occ=True
)

# Analyze occurrences for specific log identifiers
analyser.analyse_func_occurences(
    identifier=["worker1", "worker2"],
    occurrence_threshold=3
)
```

### Visual Output

Both methods generate visual plots using matplotlib:

- `analyse_time_tracker()` creates a line plot showing:
  - Execution times for each function over time
  - Average execution time in the legend
  - Different colors for each function
  - Grid for better readability

- `analyse_func_occurences()` creates a bar plot showing:
  - Number of occurrences for each function
  - Function names on the x-axis (rotated 45° for better readability)
  - Occurrence count on the y-axis
  - Clean, modern styling with skyblue bars

### Integration with Time Tracking

The LogAnalyser works seamlessly with LoggerPlusPlus's `@time_tracker` decorator. When you use the decorator on your functions, it automatically logs execution times that can later be analyzed:

```python
from loggerplusplus import Logger, time_tracker

logger = Logger(identifier="performance_logger")

@time_tracker(param_logger=logger)
def test():
    # Your code here
    pass

@log(param_logger=logger)
def test():
    # Your code here
    pass

# Later, analyze the results:
analyser = LogAnalyser("logs/performance_logger.log")
analyser.analyse_time_tracker()
analyser.analyse_func_occurences()
```



### Best Practices

1. **Filtering**: Use the filtering parameters to focus on relevant data:
   - `func_names` to analyze specific functions
   - `identifier` to analyze specific log sources
   - `min_execution_time_ms` and `max_execution_time_ms` to focus on specific time ranges

2. **Visualization**: Adjust visualization parameters for better readability:
   - Use `nb_max_funcs` to limit the number of functions displayed
   - Use `is_sort_by_avg_time` and `is_sort_order_descending` to organize data meaningfully
   - Consider using `occurrence_threshold` to filter out rarely-called functions

3. **Performance**: For large log files:
   - Filter data using `min_execution_time_ms` and `max_execution_time_ms`
   - Use `nb_max_funcs` to limit the number of displayed functions
   - Set `is_sort_by_avg_time` to False and `nb_func` to -1 to avoid sorting operations


### Author

Project created and maintained by **Florian BARRE**.  
For any questions or contributions, feel free to contact me.  
[My Website](https://florianbarre.fr/) | [My LinkedIn](www.linkedin.com/in/barre-florian) | [My GitHub](https://github.com/Florian-BARRE)
---

---
# LoggerPlusPlus - documentation Française

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

### Via PyPI avec pip

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

La combination des décorateurs est prise en charge.

```python
class MyClass:
    def __init__(self):
        self.logger = Logger(identifier="class_logger")


    @track_time(param_logger=lambda self: self.logger)
    @log(param_logger=lambda self: self.logger)
    def process_data(self):
        import time
        time.sleep(1)
```


## LogAnalyser

La classe `LogAnalyser` permet d'analyser les logs générés par Loggerplusplus. Elle permet de visualiser les temps d'exécution des fonctions ainsi que leur fréquence d'apparition dans les fichiers de log.

### Utilisation de base

```python
from loggerplusplus.analyser import LogAnalyser

# Initialiser l'analyseur avec votre fichier de log
analyser = LogAnalyser("chemin/vers/votre/fichier.log")

analyser.analyse_time_tracker()
analyser.analyse_func_occurences()

```

### Méthodes

#### analyse_time_tracker

Cette méthode analyse les temps d'exécution des fonctions spécifiées et génère un graphique détaillé. Elle fournit des informations sur les performances des fonctions en visualisant leurs durées d'exécution au fil du temps. Le graphique inclut les temps d'exécution moyens, ce qui facilite l'identification des goulets d'étranglement de performance et l'optimisation efficace de votre code.

```python
analyser.analyse_time_tracker(
    func_names=None,                    # Nom(s) de fonction à analyser
    identifier=None,                    # Identifiant(s) de log à filtrer
    min_execution_time_ms=0.0,          # Temps d'exécution minimum à inclure
    max_execution_time_ms=float('inf'), # Temps d'exécution maximum à inclure
    is_sort_by_avg_time=True,           # Trier les fonctions par temps moyen
    nb_max_funcs=float('inf'),          # Nombre maximal de fonctions à afficher
    is_sort_order_descending=True       # Trier par temps d'exécution maximal
)

```

Paramètres :

-   `func_names` (str | list[str] | None) : Nom(s) de fonction à filtrer.
    -   Chaîne unique : analyse cette fonction uniquement
    -   Liste de chaînes : analyse ces fonctions uniquement
    -   None : analyse toutes les fonctions
-   `identifier` (str | list[str] | None) : Identifiant(s) de log à filtrer
    -   Chaîne unique : analyse les log avec cet identifiant
    -   Liste de chaînes : analyse les log avec ces identifiants
    -   None : analyse toutes les entrées de log
-   `min_execution_time_ms` (float) : Temps d'exécution minimum en millisecondes à inclure
-   `max_execution_time_ms` (float) : Temps d'exécution maximum en millisecondes à inclure
-   `is_sort_by_avg_time` (bool) : Si True, trie les fonctions par temps d'exécution moyen
-   `nb_max_funcs` (int) : Nombre maximal de fonctions à afficher sur le graphique
    - ignoré si is_sort_by_avg_time est False
-   `is_sort_order_descending` (bool) : Si True, trie par temps d'exécution maximum
    - ignoré si is_sort_by_avg_time est False

Exemple d'utilisation :

```python
# Analyser toutes les fonctions avec des temps d'exécution entre 100ms et 1000ms
analyser.analyse_time_tracker(
    min_execution_time_ms=100,
    max_execution_time_ms=1000
)

# Analyser des fonctions spécifiques avec un identifiant particulier
analyser.analyse_time_tracker(
    func_names=["process_data", "calculate_metrics"],
    identifier=["worker1", "worker2"],
)
```

#### analyse_func_occurences

Cette méthode analyse le nombre d'occurrences de chaque fonction dans le fichier de log et génère un diagramme en barres.

```python
analyser.analyse_func_occurences(
    occurrence_threshold=1,    # Nombre minimum d'occurrences à inclure
    nb_func=10,               # Nombre de fonctions à afficher
    top_occ=True,             # Afficher les occurrences les plus élevées en premier
    identifier=None           # Identifiant(s) de log à filtrer
)
```

Paramètres :
-   `occurrence_threshold` (int) : Nombre minimum d'occurrences d'une fonction à inclure
-   `nb_func` (int) : Nombre de fonctions à afficher (-1 pour toutes)
-   `top_occ` (bool) : Si True, affiche les fonctions avec le plus d'occurrences en premier
-   `identifier` (str | list[str] | None) : Identifiant(s) de log à filtrer

Exemple d'utilisation :

```python
# Analyser toutes les fonctions ayant au moins 5 occurrences
analyser.analyse_func_occurences(occurrence_threshold=5)

# Afficher les 10 fonctions les plus fréquentes
analyser.analyse_func_occurences(
    nb_func=10,
    top_occ=True
)

# Analyser les occurrences pour des identifiants spécifiques
analyser.analyse_func_occurences(
    identifier=["worker1", "worker2"],
    occurrence_threshold=3
)
```

### Sortie visuelle

Les deux méthodes génèrent des graphiques avec matplotlib :

-   `analyse_time_tracker()` crée un diagramme à barres.
    
    -   Les temps d'exécution de chaque fonction au fil du temps
    -   Le temps d'exécution moyen dans la légende
    -   Des couleurs différentes pour chaque fonction
    -   Une grille pour une meilleure lisibilité
-   `analyse_func_occurences()` crée un diagramme en barres affichant :
    -   Le nombre d'occurrences de chaque fonction
    -   Les noms des fonctions sur l'axe des abscisses (tournés à 45° pour plus de lisibilité)
    -   Le nombre d'occurrences sur l'axe des ordonnées
    -   Un style moderne et propre avec des barres bleues ciel

### Intégration avec le suivi du temps

Le `LogAnalyser` fonctionne parfaitement avec les décorateurs `@time_tracker` et `@log` de LoggerPlusPlus. Lorsque vous utilisez un décorateur sur vos fonctions il génère des logs qui pourront être analysés directement via la classe:

```python
from loggerplusplus import Logger, time_tracker,log

logger = Logger(identifier="performance_logger")

@time_tracker(param_logger=logger)
def test():
    # Votre code ici
    pass
@log(param_logger=logger)
def test2():
    # Votre code ici
    pass

# Plus tard, analyser les résultats :
analyser = LogAnalyser("logs/performance_logger.log")
analyser.analyse_time_tracker()
analyser.analyse_func_occurences()
```

### Bonnes pratiques

1.  **Filtrage** : Utilisez les paramètres de filtrage pour cibler les données pertinentes.
2.  **Visualisation** : Ajustez les paramètres de visualisation pour une meilleure lisibilité.
3.  **Performance** : Pour les fichiers de log volumineux, utilisez des filtres et limitez le nombre de fonctions affichées.

### Auteur

Projet créé et maintenu par **Florian BARRE**.  
Pour toute question ou contribution, n'hésitez pas à me contacter.
[Mon Site](https://florianbarre.fr/) | [Mon LinkedIn](www.linkedin.com/in/barre-florian) | [Mon GitHub](https://github.com/Florian-BARRE)
