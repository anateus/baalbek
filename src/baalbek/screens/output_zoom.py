from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.screen import Screen
from textual.widgets import Static

from baalbek.widgets.output_viewer import raw_to_rich_text


class OutputZoomScreen(Screen):
    BINDINGS = [
        Binding("escape", "dismiss", "Back"),
        Binding("q", "dismiss", "Back"),
    ]

    def __init__(self, raw_output: bytes, **kwargs) -> None:
        super().__init__(**kwargs)
        self._raw_output = raw_output

    def compose(self) -> ComposeResult:
        with VerticalScroll():
            yield Static(raw_to_rich_text(self._raw_output), id="zoom-content")

    def action_dismiss(self) -> None:
        self.app.pop_screen()
