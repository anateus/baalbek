from __future__ import annotations

import pytest
from textual.app import App, ComposeResult

from baalbek.db import RunRecord
from baalbek.schemas import CommandSchema
from baalbek.widgets.miller import MillerColumns


def make_commands() -> dict[str, CommandSchema]:
    logs = CommandSchema(
        name="logs", docstring="View logs", options=[], arguments=[],
    )
    return {"logs": logs}


def make_record(id: int = 1) -> RunRecord:
    return RunRecord(
        id=id,
        command="logs",
        args_json='["logs"]',
        exit_code=0,
        raw_output=b"hello world",
        plain_output="hello world",
        started_at="2025-01-01T00:00:00",
        finished_at="2025-01-01T00:00:01",
    )


class MillerApp(App):
    def __init__(self, commands: dict[str, CommandSchema]) -> None:
        super().__init__()
        self._commands = commands

    def compose(self) -> ComposeResult:
        yield MillerColumns(self._commands)


@pytest.mark.asyncio
async def test_show_history_adds_column():
    async with MillerApp(make_commands()).run_test() as pilot:
        mc = pilot.app.query_one(MillerColumns)
        await pilot.pause()
        initial = mc.column_count
        mc.show_history([make_record(1), make_record(2)])
        await pilot.pause()
        assert mc.column_count == initial + 1
