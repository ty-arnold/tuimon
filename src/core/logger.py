import logging
import os
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LOG_DIR      = os.path.join(PROJECT_ROOT, "logs")

def setup_logger(debug=False):
    os.makedirs(LOG_DIR, exist_ok=True)
    logger = logging.getLogger("tuimon")
    logger.setLevel(logging.DEBUG)
    logger.propagate = False  # prevent messages from propagating to root logger

    logger.handlers.clear()

    # console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter("%(message)s"))

    # file handler
    timestamp    = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_handler = logging.FileHandler(
        f"{LOG_DIR}/battle_{timestamp}.log",
        mode  = "a",
        delay = False
    )
    file_handler.setLevel(logging.DEBUG if debug else logging.INFO)
    file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger

# default null logger - does nothing until setup_logger is called
logger = logging.getLogger("tuimon")
