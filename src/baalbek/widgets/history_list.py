from __future__ import annotations

from textual import on
from textual.message import Message
from textual.widgets import OptionList
from textual.widgets.option_list import Option

from baalbek.db import RunRecord


class HistoryList(OptionList):
    class Selected(Message):
        def __init__(self, record: RunRecord) -> None:
            super().__init__()
            self.record = record

    def __init__(self, records: list[RunRecord], **kwargs) -> None:
        self._records = records
        options = []
        for rec in records:
            status = "\u2713" if rec.exit_code == 0 else "\u2717"
            label = f"{status} {rec.command}"
            options.append(Option(label, id=f"run-{rec.id}"))
        super().__init__(*options, **kwargs)

    @property
    def selected_record(self) -> RunRecord | None:
        idx = self.highlighted
        if idx is not None and 0 <= idx < len(self._records):
            return self._records[idx]
        return None

    @on(OptionList.OptionHighlighted)
    def _on_highlight(self, event: OptionList.OptionHighlighted) -> None:
        record = self.selected_record
        if record:
            self.post_message(self.Selected(record))
