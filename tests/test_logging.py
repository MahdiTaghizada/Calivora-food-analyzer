import logging

from src.logging_config import setup_logging

def test_setup_logging():
    setup_logging("INFO")
    logger=logging.getLogger()
    assert logger.level==logging.INFO