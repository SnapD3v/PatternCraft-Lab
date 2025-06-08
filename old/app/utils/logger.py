"""
Description: Provides logging functionality for the application. Configures and
manages logging settings, formats, and handlers for different log levels.
"""

import logging
import sys
from colorama import init, Fore, Style


def setup_logger(name=None, log_file=None, level=logging.INFO):
    if sys.platform.startswith("win"):
        import ctypes

        ctypes.windll.kernel32.SetConsoleOutputCP(65001)

    init(autoreset=True)

    COLORS = {
        logging.DEBUG: Fore.CYAN,
        logging.INFO: Fore.GREEN,
        logging.WARNING: Fore.YELLOW,
        logging.ERROR: Fore.RED,
        logging.CRITICAL: Fore.RED + Style.BRIGHT,
    }

    class ColoredFormatter(logging.Formatter):
        def format(self, record):
            log_fmt = (
                "%(asctime)s - %(name)s [%(lineno)d] - %(levelname)s - %(message)s"
            )
            formatter = logging.Formatter(log_fmt)
            color = COLORS.get(record.levelno, "")
            message = color + record.getMessage() + Style.RESET_ALL
            record.message = message
            return formatter.format(record)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.handlers = []

    if sys.version_info >= (3, 7):
        sys.stdout.reconfigure(encoding="utf-8")
    else:
        sys.stdout = open(sys.stdout.fileno(), mode="w",
                          encoding="utf-8", buffering=1)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(ColoredFormatter())
    logger.addHandler(console_handler)

    if log_file:
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s [%(lineno)d] - %(levelname)s - %(message)s"
        )
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger


def log_big_message(logger: logging.Logger, message: str) -> None:
    width = 64
    top_line = "#" * width
    bottom_line = "#" * width

    centered_message = message.center(width - 6)
    middle_line = f"## {centered_message} ##"

    logger.info(top_line)
    logger.info(middle_line)
    logger.info(bottom_line)
