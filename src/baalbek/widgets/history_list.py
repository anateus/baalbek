from __future__ import annotations

from rich.table import Table
from rich.text import Text
from textual import on
from textual.message import Message
from textual.widgets import OptionList
from textual.widgets.option_list import Option

from baalbek.db import RunRecord

_HINT_UNFOCUSED = "press tab to review history"
_HINT_FOCUSED = "shift+tab to go back"


class HistoryList(OptionList):
    can_focus = False

    class Selected(Message):
        def __init__(self, record: RunRecord) -> None:
            super().__init__()
            self.record = record

    def __init__(self, records: list[RunRecord], **kwargs) -> None:
        self._records = records
        self._suppress_initial_highlight = True
        self._hint_id = "history-hint"
        options: list[Option] = []
        options.append(Option(Text(_HINT_UNFOCUSED, style="dim italic"), id=self._hint_id))
        for rec in records:
            border_color = "green" if rec.exit_code == 0 else "red"
            table = Table(show_header=False, box=None, padding=(0, 0), show_edge=False, expand=True)
            table.add_column(width=1, style=border_color, no_wrap=True)
            table.add_column(ratio=1)
            table.add_row("\u258c", rec.command)
            options.append(Option(table, id=f"run-{rec.id}"))
        super().__init__(*options, **kwargs)

    def _update_hint(self) -> None:
        is_focused = self.has_class("focused")
        hint_text = _HINT_FOCUSED if is_focused else _HINT_UNFOCUSED
        self.replace_option_prompt(self._hint_id, Text(hint_text, style="dim italic"))

    def add_class(self, *class_names, **kwargs):
        had_focused = self.has_class("focused")
        super().add_class(*class_names, **kwargs)
        if not had_focused and self.has_class("focused"):
            self._update_hint()

    def remove_class(self, *class_names, **kwargs):
        had_focused = self.has_class("focused")
        super().remove_class(*class_names, **kwargs)
        if had_focused and not self.has_class("focused"):
            self._update_hint()

    @property
    def selected_record(self) -> RunRecord | None:
        idx = self.highlighted
        if idx is not None:
            record_idx = idx - 1
            if 0 <= record_idx < len(self._records):
                return self._records[record_idx]
        return None

    @on(OptionList.OptionHighlighted)
    def _on_highlight(self, event: OptionList.OptionHighlighted) -> None:
        if self._suppress_initial_highlight:
            self._suppress_initial_highlight = False
            return
        record = self.selected_record
        if record:
            self.post_message(self.Selected(record))
