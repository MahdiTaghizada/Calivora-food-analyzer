import logging
import os

LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

def setup_logging(log_level=LOG_LEVEL):
    logging.basicConfig(
        level=log_level.upper(),
        format=LOG_FORMAT,
        force=True
    )