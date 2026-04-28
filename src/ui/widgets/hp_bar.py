from textual.widget import Widget
from rich.text      import Text

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
        self._color   = "#0dc958"

    def set_hp(self, current: int, maximum: int) -> None:
        self._current = current
        self._maximum = maximum
        pct = (current / maximum) if maximum > 0 else 0
        if pct > 0.5:
            self._color = "#0dc958"
        elif pct > 0.25:
            self._color = "#c7ab42"
        else:
            self._color = "#cc4444"
        self.refresh()

    def render(self) -> Text:
        pct       = (self._current / self._maximum) if self._maximum > 0 else 0
        bar_width = self.size.width - 12
        filled    = int(bar_width * pct)
        empty     = bar_width - filled

        # nerd font half circles - left cap filled color, right cap empty color
        LEFT_CAP  = "\ue0b6"  # 
        RIGHT_CAP = "\ue0b4"  # 

        if filled > 0 and empty > 0:
            bar  = f"[{self._color}]{LEFT_CAP}{'█' * filled}[/{self._color}]"
            bar += f"[#222233]{'█' * empty}{RIGHT_CAP}[/#222233]"
        elif filled == 0:
            bar  = f"[#222233]{LEFT_CAP}{'█' * bar_width}{RIGHT_CAP}[/#222233]"
        else:
            bar  = f"[{self._color}]{LEFT_CAP}{'█' * bar_width}{RIGHT_CAP}[/{self._color}]"

        hp = f"  [#aaaacc]{self._current}[/#aaaacc][#555577]/{self._maximum}[/#555577]"

        return Text.from_markup(bar + hp)