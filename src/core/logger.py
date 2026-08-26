import logging
import os
from datetime import datetime
from typing import Optional
from core.paths import LOG_DIR 

# current log path - can be accessed externally
current_log_path: Optional[str] = None

# logger object - imported by other modules
logger = logging.getLogger("tuimon")

def setup_logger(debug: bool = False) -> None:
    global current_log_path

    logger.handlers.clear()
    logger.propagate = False
    logger.setLevel(logging.DEBUG)

    # create logs directory if it doesn't exist
    os.makedirs(LOG_DIR, exist_ok=True)

    # file handler - always active, captures everything
    timestamp        = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    current_log_path = os.path.join(LOG_DIR, f"battle_{timestamp}.log")

    file_handler = logging.FileHandler(current_log_path)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    )
    logger.addHandler(file_handler)

    # console handler - only warnings and above
    # CLI mode uses print() for output so no INFO needed on console
    # TUI mode uses RichLog widget so no console output needed at all
    if debug:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        console_handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(console_handler)
