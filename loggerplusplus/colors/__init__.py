# ====== Code Summary ======
# This module defines different color schemes for log levels using the `colorama` library.
# It provides a base class (`BaseColors`) and multiple subclasses (`ClassicColors`, `DarkModeColors`, etc.)
# that define color mappings for log levels such as DEBUG, INFO, WARNING, ERROR, CRITICAL, and FATAL.
# These classes can be used to format log messages with different visual styles.

# Base class for colors
from loggerplusplus.colors.base import BaseColors

# Derived color classes
from loggerplusplus.colors.classic import ClassicColors
from loggerplusplus.colors.cyberpunk import CyberpunkColors
from loggerplusplus.colors.dark_mode import DarkModeColors
from loggerplusplus.colors.neon import NeonColors
from loggerplusplus.colors.pastel import PastelColors
