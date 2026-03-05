from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.message import Message
from textual.widgets import Button

from baalbek.schemas import CommandSchema
from baalbek.widgets.parameter_list import ParameterList


class RunPanel(Vertical):
    class RunRequested(Message):
        pass

    def __init__(self, schema: CommandSchema, **kwargs) -> None:
        super().__init__(**kwargs)
        self._schema = schema

    def compose(self) -> ComposeResult:
        yield Button("Run", id="run-button", variant="success", disabled=self._has_unfilled_required())
        yield ParameterList(self._schema)

    def _has_unfilled_required(self) -> bool:
        for arg in self._schema.arguments:
            if arg.required:
                return True
        return False

    @property
    def parameter_list(self) -> ParameterList:
        return self.query_one(ParameterList)

    def _update_button_state(self) -> None:
        btn = self.query_one("#run-button", Button)
        values = self.parameter_list.get_values()
        has_unfilled = False
        for arg in self._schema.arguments:
            if arg.required:
                val = values.get(arg.name)
                if not val or val == "":
                    has_unfilled = True
                    break
        btn.disabled = has_unfilled

    def on_parameter_list_values_changed(self, event) -> None:
        self._update_button_state()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "run-button":
            self.post_message(self.RunRequested())
