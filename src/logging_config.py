import logging

from src.config import settings

LOG_FORMAT="%(asctime)s [%(levelname)s] %(name)s: %(message)s"

def setup_logging(log_level=None):
    if log_level is None:
        log_level=settings.log_level

    logging.basicConfig(
        level=log_level.upper(),
        format=LOG_FORMAT,
        force=True
    )
