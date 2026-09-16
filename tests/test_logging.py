import logging

from src.logging_config import setup_logging

def test_setup_logging():
    setup_logging("INFO")
    logger=logging.getLogger()
    assert logger.level==logging.INFO

import os
def test_log_level_from_env():
    os.environ["LOG_LEVEL"] = "DEBUG"
    setup_logging()
    logger = logging.getLogger()
    assert logger.level == logging.DEBUG