import logging
from logging.handlers import RotatingFileHandler

from config import PROJECT_ROOT


def configure_logging() -> logging.Logger:
    """Configure one rotating file logger for the application."""
    logger = logging.getLogger("vcti_agent")

    if logger.handlers:
        return logger

    log_directory = PROJECT_ROOT / "logs"
    log_directory.mkdir(exist_ok=True)

    logger.setLevel(logging.INFO)
    logger.propagate = False

    file_handler = RotatingFileHandler(
        log_directory / "agent.log",
        maxBytes=1_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        )
    )

    logger.addHandler(file_handler)
    return logger
