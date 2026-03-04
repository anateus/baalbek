from __future__ import annotations

import pytest
from textual.app import App, ComposeResult

from baalbek.db import RunRecord
from baalbek.widgets.history_list import HistoryList
from baalbek.widgets.output_viewer import OutputViewer


def make_records() -> list[RunRecord]:
    return [
        RunRecord(
            id=1,
            command="deploy",
            args_json="{}",
            exit_code=0,
            raw_output=None,
            plain_output=None,
            started_at="2026-01-01T00:00:00Z",
            finished_at="2026-01-01T00:01:00Z",
        ),
        RunRecord(
            id=2,
            command="test",
            args_json="{}",
            exit_code=1,
            raw_output=None,
            plain_output=None,
            started_at="2026-01-02T00:00:00Z",
            finished_at="2026-01-02T00:01:00Z",
        ),
    ]


class HistoryListApp(App):
    def __init__(self, records: list[RunRecord]) -> None:
        super().__init__()
        self._records = records

    def compose(self) -> ComposeResult:
        yield HistoryList(self._records)


class OutputViewerApp(App):
    def __init__(self, raw_output: bytes) -> None:
        super().__init__()
        self._raw_output = raw_output

    def compose(self) -> ComposeResult:
        yield OutputViewer(self._raw_output)


@pytest.mark.asyncio
async def test_history_list_renders():
    async with HistoryListApp(make_records()).run_test() as pilot:
        hl = pilot.app.query_one(HistoryList)
        assert hl.option_count == 2


@pytest.mark.asyncio
async def test_output_viewer_renders():
    raw = b"\x1b[31mred text\x1b[0m\nnormal text\n"
    async with OutputViewerApp(raw).run_test() as pilot:
        ov = pilot.app.query_one(OutputViewer)
        assert ov is not None
