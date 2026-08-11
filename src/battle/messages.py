from data.messages import MESSAGE_TEMPLATES
from models.turn_result import Message


def msg(key: str, color: str = "", **kwargs) -> Message:
    """Look up a message template, format it, and return a Message event.
    If `color` is provided, it overrides the template's default color."""
    template = MESSAGE_TEMPLATES[key]
    text = template.text.format(**kwargs)
    return Message(text=text, color=color or template.color)
