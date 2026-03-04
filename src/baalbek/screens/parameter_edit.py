from __future__ import annotations

from typing import Any

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen

from baalbek.schemas import CommandSchema
from baalbek.widgets.option_form import OptionForm


class ParameterFormModal(ModalScreen[dict[str, Any]]):
    BINDINGS = [
        Binding("escape", "save_and_close", "Close"),
    ]

    def __init__(
        self,
        schema: CommandSchema,
        focus_param: str | None,
        initial_values: dict[str, Any],
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._schema = schema
        self._focus_param = focus_param
        self._initial_values = initial_values

    def compose(self) -> ComposeResult:
        with Vertical(id="param-modal-container"):
            yield OptionForm(self._schema, id="param-form")

    def on_mount(self) -> None:
        form = self.query_one(OptionForm)
        if self._initial_values:
            form.set_values(self._initial_values)
        if self._focus_param:
            form.focus_param(self._focus_param)

    def action_save_and_close(self) -> None:
        form = self.query_one(OptionForm)
        self.dismiss(form.get_values())
