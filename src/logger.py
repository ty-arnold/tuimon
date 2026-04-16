# logger.py
import logging
import os
from datetime import datetime

LOG_DIR = "logs"

def setup_logger(debug=False):
    os.makedirs(LOG_DIR, exist_ok=True)

    logger = logging.getLogger("pokemon_battle")
    logger.setLevel(logging.DEBUG)

    # only add handlers if none exist yet
    if not logger.handlers:
        # console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG if debug else logging.INFO)
        console_handler.setFormatter(logging.Formatter("%(message)s"))

        # file handler
        timestamp    = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_handler = logging.FileHandler(f"{LOG_DIR}/battle_{timestamp}.log")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))

        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

    return logger
# global logger instance
logger = setup_logger(debug=False)