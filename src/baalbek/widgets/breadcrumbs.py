from __future__ import annotations

from textual.reactive import reactive
from textual.widgets import Static


class Breadcrumbs(Static):
    path: reactive[list[str]] = reactive(list, init=False)

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.path = []

    @property
    def render_text(self) -> str:
        if not self.path:
            return ""
        items = [f"[on #333333] {p} [/]" for p in self.path]
        return " [dim]▸[/] ".join(items)

    def watch_path(self) -> None:
        self.update(self.render_text)
