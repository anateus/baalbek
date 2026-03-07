from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Input, Label, Static


class DelimiterModal(ModalScreen[str | None]):
    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
    ]

    def __init__(self, current: str = ":", **kwargs) -> None:
        super().__init__(**kwargs)
        self._current = current

    def compose(self) -> ComposeResult:
        with Vertical(id="delimiter-modal-container"):
            yield Label("Task name delimiter")
            yield Static("Split task names into hierarchy levels")
            yield Input(value=self._current, id="delimiter-input", max_length=3)
            yield Static("[dim]Common: [b]:[/b]  [b]/[/b]  [b].[/b]  [b]-[/b][/dim]", markup=True)

    def on_mount(self) -> None:
        self.query_one("#delimiter-input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        value = event.value.strip()
        if value:
            self.dismiss(value)

    def action_cancel(self) -> None:
        self.dismiss(None)
