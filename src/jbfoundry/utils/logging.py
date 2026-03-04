"""Centralized logging configuration for jbfoundry."""

import logging
import sys
from typing import Optional


class ColoredFormatter(logging.Formatter):
    """Formatter with ANSI colors and shortened module names."""
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
    }
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'

    def format(self, record):
        # Shorten logger name (e.g., jbfoundry.attacks.registry -> attacks.registry)
        name_parts = record.name.split('.')
        if len(name_parts) > 2 and name_parts[0] == 'jbfoundry':
            short_name = '.'.join(name_parts[1:])  # Remove 'jbfoundry' prefix
        elif record.name == '__main__':
            short_name = 'main'
        else:
            short_name = record.name

        # Color the level name
        level_color = self.COLORS.get(record.levelname, '')
        level_name = f"{level_color}{record.levelname:<7}{self.RESET}"

        # Dim the timestamp and module name
        timestamp = f"{self.DIM}{self.formatTime(record, '%H:%M:%S')}{self.RESET}"
        module = f"{self.DIM}{short_name}{self.RESET}"

        # Format: [TIME] LEVEL module | message
        return f"{timestamp} {level_name} {module} | {record.getMessage()}"


def configure_logging(
    verbose: bool = False,
    level: Optional[int] = None,
    format_string: Optional[str] = None,
    use_colors: bool = True
) -> None:
    """
    Configure logging for jbfoundry package (library-friendly).

    Priority: level parameter > verbose flag > JBFOUNDRY_LOG_LEVEL env var > INFO

    Args:
        verbose: If True, set to DEBUG; otherwise check env var or use INFO
        level: Explicit level (overrides everything)
        format_string: Custom format (disables colors)
        use_colors: Use colored output (default True)
    """
    import os

    if level is None:
        if verbose:
            level = logging.DEBUG
        else:
            env_level = os.environ.get("JBFOUNDRY_LOG_LEVEL", "INFO").upper()
            level = getattr(logging, env_level, logging.INFO)

    jbfoundry_logger = logging.getLogger("jbfoundry")
    jbfoundry_logger.setLevel(level)
    jbfoundry_logger.handlers.clear()

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.DEBUG)

    if use_colors and format_string is None:
        stream_handler.setFormatter(ColoredFormatter())
    else:
        if format_string is None:
            format_string = "%(asctime)s %(levelname)s [%(name)s] %(message)s"
        stream_handler.setFormatter(
            logging.Formatter(fmt=format_string, datefmt="%H:%M:%S")
        )

    jbfoundry_logger.addHandler(stream_handler)
    jbfoundry_logger.propagate = True

    main_logger = logging.getLogger("__main__")
    main_logger.setLevel(level)
    main_logger.handlers.clear()
    main_logger.addHandler(stream_handler)
    main_logger.propagate = True


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance (convenience wrapper for logging.getLogger)."""
    return logging.getLogger(name)
