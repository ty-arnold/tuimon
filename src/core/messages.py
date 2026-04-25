from data import MESSAGES, MESSAGE_COLORS
from core.colors import log_color

def msg(key: str, **kwargs) -> str:
    if key not in MESSAGES:
        raise KeyError(f"Message key '{key}' not found. Check core/messages.py.")
    text        = MESSAGES[key].format(**kwargs)
    color_key   = MESSAGE_COLORS.get(key)
    if color_key:
        return log_color(color_key, text)
    return text