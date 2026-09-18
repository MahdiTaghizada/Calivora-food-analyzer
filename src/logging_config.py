import logging
import os

LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
# LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")  #fayl import olunanda bir dəfə oxunur.Pytest-də environment test zamanı dəyişsə, bu dəyər köhnə qala bilər.

# def setup_logging(log_level=LOG_LEVEL):
def setup_logging(log_level=None):
    if log_level is None:
        log_level = os.getenv("LOG_LEVEL", "INFO")
    logging.basicConfig(
        level=log_level.upper(),
        format=LOG_FORMAT,
        force=True
    )