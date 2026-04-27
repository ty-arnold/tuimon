from dataclasses import dataclass
from typing import Callable, Optional
from core.logger import logger
from core.config import TUI_MODE

# output handler for custom routing
_output_handler: Optional[Callable[[str], None]] = None

# async queue for TUI mode
_async_message_queue = None

# synchronous buffer for collecting messages during turn resolution
_message_buffer: list[str] = []
_buffering:      bool      = False

@dataclass
class HpSnapshot:
    pokemon_name: str
    start_pct:    int
    end_pct:      int
    max_hp:       int

def record_hp_change(pokemon_name: str, start_pct: int, end_pct: int, max_hp: int) -> None:
    if _buffering:
        _message_buffer.append(HpSnapshot(
            pokemon_name = pokemon_name,
            start_pct    = start_pct,
            end_pct      = end_pct,
            max_hp       = max_hp,
        ))

def set_output_handler(handler: Callable[[str], None]) -> None:
    """Register a custom output handler e.g. a Textual widget."""
    global _output_handler
    _output_handler = handler


def clear_output_handler() -> None:
    """Restore default terminal output."""
    global _output_handler
    _output_handler = None


def set_async_queue(queue) -> None:
    """Register an async queue for TUI message routing."""
    global _async_message_queue
    _async_message_queue = queue


def start_buffering() -> None:
    """Start collecting messages into the buffer instead of outputting them."""
    global _buffering, _message_buffer
    _buffering      = True
    _message_buffer = []


def stop_buffering() -> list[str | HpSnapshot]:
    global _buffering
    _buffering = False
    messages   = _message_buffer.copy()
    _message_buffer.clear()
    return messages

def game_print(message: str) -> None:
    logger.debug(message)  # file only - never prints to console via logger

    if _buffering:
        _message_buffer.append(message)
    elif TUI_MODE and _async_message_queue is not None:
        _async_message_queue.put_nowait(message)
    elif _output_handler is not None:
        _output_handler(message)
    else:
        print(message)