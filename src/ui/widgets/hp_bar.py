from textual.widget import Widget
from rich.text      import Text
from ui.palette     import Colors

class HpBar(Widget):

    DEFAULT_CSS = """
    HpBar {
        width: 1fr;
        height: 1;
        margin: 0;
        padding: 0;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._current = 0
        self._maximum = 100
        self._color   = None   # resolved from theme on first set_hp

    def set_hp(self, current: int, maximum: int) -> None:
        self._current = current
        self._maximum = maximum
        pct = (current / maximum) if maximum > 0 else 0
        c   = Colors(self.app)
        if pct > 0.5:
            self._color = c.success
        elif pct > 0.25:
            self._color = c.warning
        else:
            self._color = c.error
        self.refresh()

    def render(self) -> Text:
        c         = Colors(self.app)
        color     = self._color or c.success
        pct       = (self._current / self._maximum) if self._maximum > 0 else 0
        bar_width = self.size.width - 12
        filled    = int(bar_width * pct)
        empty     = bar_width - filled

        bar  = f"[on {color}]{' ' * filled}[/on {color}]"
        bar += f"[on {c.hp_empty}]{' ' * empty}[/on {c.hp_empty}]"

        hp = (
            f"  [{c.text_ui}]{self._current}[/{c.text_ui}]"
            f"[{c.text_muted_ui}]/{self._maximum}[/{c.text_muted_ui}]"
        )

        return Text.from_markup(bar + hp)
