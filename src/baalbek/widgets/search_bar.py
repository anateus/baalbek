from __future__ import annotations

from textual.reactive import reactive
from textual.widgets import Static


class SearchBar(Static):
    DEFAULT_CSS = """
    SearchBar {
        height: 1;
        padding: 0 1;
        background: $surface;
        color: $text-disabled;
        display: none;
    }
    """

    query_text: reactive[str] = reactive("", layout=True)

    def show(self) -> None:
        self.display = True

    def hide(self) -> None:
        self.display = False

    @property
    def render_text(self) -> str:
        return f"/{self.query_text}" if self.query_text else "/"

    def watch_query_text(self, value: str) -> None:
        self.update(self.render_text)
