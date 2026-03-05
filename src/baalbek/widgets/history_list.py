from __future__ import annotations

from rich.table import Table
from textual import on
from textual.message import Message
from textual.widgets import OptionList
from textual.widgets.option_list import Option

from baalbek.db import RunRecord


class HistoryList(OptionList):
    can_focus = False

    class Selected(Message):
        def __init__(self, record: RunRecord) -> None:
            super().__init__()
            self.record = record

    def __init__(self, records: list[RunRecord], **kwargs) -> None:
        self._records = records
        self._suppress_initial_highlight = True
        options = []
        for rec in records:
            border_color = "green" if rec.exit_code == 0 else "red"
            table = Table(show_header=False, box=None, padding=(0, 0), show_edge=False, expand=True)
            table.add_column(width=1, style=border_color, no_wrap=True)
            table.add_column(ratio=1)
            table.add_row("\u258c", rec.command)
            options.append(Option(table, id=f"run-{rec.id}"))
        super().__init__(*options, **kwargs)

    @property
    def selected_record(self) -> RunRecord | None:
        idx = self.highlighted
        if idx is not None and 0 <= idx < len(self._records):
            return self._records[idx]
        return None

    @on(OptionList.OptionHighlighted)
    def _on_highlight(self, event: OptionList.OptionHighlighted) -> None:
        if self._suppress_initial_highlight:
            self._suppress_initial_highlight = False
            return
        record = self.selected_record
        if record:
            self.post_message(self.Selected(record))
