from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.message import Message
from textual.widgets import Static

from baalbek.schemas import CommandSchema
from baalbek.widgets.parameter_list import ParameterList


class RunPanel(Vertical):
    class RunRequested(Message):
        pass

    def __init__(self, schema: CommandSchema, **kwargs) -> None:
        super().__init__(**kwargs)
        self._schema = schema
        self._button_highlighted = False
        self._button_disabled = self._has_unfilled_required()

    def compose(self) -> ComposeResult:
        btn = Static("▶ Run command", id="run-button")
        if self._button_disabled:
            btn.add_class("disabled")
        yield btn
        hint = Static("", id="run-hint")
        hint.display = False
        yield hint
        pl = ParameterList(self._schema)
        if self.has_class("preview"):
            pl.add_class("preview")
        yield pl

    def _has_unfilled_required(self) -> bool:
        for arg in self._schema.arguments:
            if arg.required:
                return True
        return False

    @property
    def parameter_list(self) -> ParameterList:
        return self.query_one(ParameterList)

    @property
    def is_button_highlighted(self) -> bool:
        return self._button_highlighted

    def _update_button_visual(self) -> None:
        btn = self.query_one("#run-button", Static)
        if self._button_highlighted:
            btn.add_class("highlighted")
        else:
            btn.remove_class("highlighted")

    def action_cursor_down(self) -> None:
        pl = self.parameter_list
        if self._button_highlighted:
            self._button_highlighted = False
            self._update_button_visual()
            if pl.option_count > 0:
                pl.highlighted = 0
        else:
            idx = pl.highlighted
            if idx is not None and idx >= pl.option_count - 1:
                self._button_highlighted = True
                self._update_button_visual()
                pl.highlighted = None
            else:
                pl.action_cursor_down()

    def action_cursor_up(self) -> None:
        pl = self.parameter_list
        if self._button_highlighted:
            self._button_highlighted = False
            self._update_button_visual()
            if pl.option_count > 0:
                pl.highlighted = pl.option_count - 1
        else:
            idx = pl.highlighted
            if idx is not None and idx <= 0:
                self._button_highlighted = True
                self._update_button_visual()
                pl.highlighted = None
            else:
                pl.action_cursor_up()

    def open_edit_or_run(self) -> None:
        if self._button_highlighted:
            if not self._button_disabled:
                self.post_message(self.RunRequested())
        else:
            self.parameter_list.open_edit_for_highlighted()

    def _update_button_state(self) -> None:
        btn = self.query_one("#run-button", Static)
        values = self.parameter_list.get_values()
        has_unfilled = False
        for arg in self._schema.arguments:
            if arg.required:
                val = values.get(arg.name)
                if not val or val == "":
                    has_unfilled = True
                    break
        self._button_disabled = has_unfilled
        if has_unfilled:
            btn.add_class("disabled")
        else:
            btn.remove_class("disabled")

    def show_last_run_failed(self) -> None:
        hint = self.query_one("#run-hint", Static)
        hint.update("Last run with these arguments failed")
        hint.display = True

    def _clear_hint(self) -> None:
        hint = self.query_one("#run-hint", Static)
        hint.update("")
        hint.display = False

    def on_parameter_list_values_changed(self, event) -> None:
        self._update_button_state()
        self._clear_hint()

    def on_click(self, event) -> None:
        if self.query_one("#run-button", Static).is_mouse_over and not self._button_disabled:
            self.post_message(self.RunRequested())
