import logging

from src.logging_config import setup_logging
from src.config import settings


def test_setup_logging():
    setup_logging("INFO")
    logger=logging.getLogger()

    assert logger.level==logging.INFO


def test_log_level_from_settings(monkeypatch):
    monkeypatch.setattr(
        settings,
        "log_level",
        "DEBUG"
    )

    setup_logging()
    logger=logging.getLogger()

    assert logger.level==logging.DEBUG
