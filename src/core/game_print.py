from typing import Optional
from core.logger import logger
from core.config import TUI_MODE

# async queue for TUI mode
_async_message_queue = None


def set_async_queue(queue) -> None:
    """Register an async queue for TUI message routing."""
    global _async_message_queue
    _async_message_queue = queue


def game_print(message: str) -> None:
    logger.debug(message)

    if TUI_MODE and _async_message_queue is not None:
        _async_message_queue.put_nowait(message)
    else:
        print(message)