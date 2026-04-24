from data import MESSAGES

def msg(key: str, **kwargs) -> str:
    if key not in MESSAGES:
        raise KeyError(f"Message key '{key}' not found in MESSAGES. Check core/messages.py.")
    return MESSAGES[key].format(**kwargs)