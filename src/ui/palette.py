class Colors:
    """
    Attribute-style access to the current Textual theme's CSS variables.
    Underscores in attribute names are converted to dashes to match CSS
    variable naming (e.g. c.text_ui → "text-ui").

    Standard theme vars (success, warning, error, primary, etc.) and
    custom variables defined in Theme(variables={...}) are all accessible.
    """

    def __init__(self, app) -> None:
        self._v = app.get_css_variables()

    def __getattr__(self, name: str) -> str:
        key = name.replace("_", "-")
        val = self._v.get(key)
        if val is None:
            raise AttributeError(f"No theme color '{key}'")
        return val
