import logging

LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
def setup_logging(log_level="INFO"):
    logging.basicConfig(
        level=log_level.upper(),
        format=LOG_FORMAT
    )