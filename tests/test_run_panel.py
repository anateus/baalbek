from __future__ import annotations

from pathlib import Path

import pytest
from textual.app import App, ComposeResult
from textual.widgets import Static

from baalbek.db import HistoryDB
from baalbek.schemas import ArgumentSchema, CommandSchema
from baalbek.widgets.run_panel import RunPanel


def make_leaf_command(required_arg: bool = False) -> CommandSchema:
    args = []
    if required_arg:
        args.append(ArgumentSchema(
            name="target",
            type="STRING",
            required=True,
            default=None,
            choices=None,
            multiple=False,
            nargs=1,
        ))
    return CommandSchema(
        name="deploy",
        docstring="Deploy",
        options=[],
        arguments=args,
    )


class RunPanelApp(App):
    def __init__(self, schema: CommandSchema, db_path: Path | None = None) -> None:
        super().__init__()
        self._schema = schema
        if db_path is not None:
            self._db_path = db_path

    def compose(self) -> ComposeResult:
        yield RunPanel(self._schema)


@pytest.mark.asyncio
async def test_run_panel_has_button():
    async with RunPanelApp(make_leaf_command()).run_test() as pilot:
        await pilot.pause()
        btn = pilot.app.query_one("#run-button", Static)
        assert btn is not None


@pytest.mark.asyncio
async def test_run_button_disabled_when_required_arg_missing():
    async with RunPanelApp(make_leaf_command(required_arg=True)).run_test() as pilot:
        await pilot.pause()
        btn = pilot.app.query_one("#run-button", Static)
        assert btn.has_class("disabled")


@pytest.mark.asyncio
async def test_run_button_enabled_when_no_required_args():
    async with RunPanelApp(make_leaf_command(required_arg=False)).run_test() as pilot:
        await pilot.pause()
        btn = pilot.app.query_one("#run-button", Static)
        assert not btn.has_class("disabled")


@pytest.mark.asyncio
async def test_run_button_enables_after_filling_required_arg():
    schema = make_leaf_command(required_arg=True)
    async with RunPanelApp(schema).run_test() as pilot:
        await pilot.pause()
        panel = pilot.app.query_one(RunPanel)
        btn = pilot.app.query_one("#run-button", Static)
        assert btn.has_class("disabled")
        panel.parameter_list._values["target"] = "prod"
        panel.parameter_list._rebuild_display()
        await pilot.pause()
        panel._update_button_state()
        await pilot.pause()
        assert not btn.has_class("disabled")


@pytest.mark.asyncio
async def test_cursor_wraps_to_run_button():
    schema = make_leaf_command(required_arg=True)
    async with RunPanelApp(schema).run_test() as pilot:
        await pilot.pause()
        panel = pilot.app.query_one(RunPanel)
        assert not panel.is_button_highlighted
        for _ in range(panel.parameter_list.option_count):
            panel.action_cursor_down()
        await pilot.pause()
        assert panel.is_button_highlighted
        panel.action_cursor_down()
        await pilot.pause()
        assert not panel.is_button_highlighted


@pytest.mark.asyncio
async def test_run_button_enabled_when_draft_fills_required_arg(tmp_path: Path):
    schema = make_leaf_command(required_arg=True)
    db_path = tmp_path / "history.db"
    db = HistoryDB(db_path)
    db.save_draft("deploy", {"target": "prod"})
    db.close()
    async with RunPanelApp(schema, db_path=db_path).run_test() as pilot:
        await pilot.pause()
        btn = pilot.app.query_one("#run-button", Static)
        assert not btn.has_class("disabled")


@pytest.mark.asyncio
async def test_show_last_run_failed_hint():
    async with RunPanelApp(make_leaf_command()).run_test() as pilot:
        await pilot.pause()
        panel = pilot.app.query_one(RunPanel)
        hint = pilot.app.query_one("#run-hint", Static)
        assert not hint.display
        panel.show_last_run_failed()
        await pilot.pause()
        assert hint.display
        assert "failed" in str(hint.content).lower()


@pytest.mark.asyncio
async def test_hint_clears_on_values_changed():
    async with RunPanelApp(make_leaf_command()).run_test() as pilot:
        await pilot.pause()
        panel = pilot.app.query_one(RunPanel)
        hint = pilot.app.query_one("#run-hint", Static)
        panel.show_last_run_failed()
        await pilot.pause()
        assert hint.display
        panel.parameter_list._on_modal_done({"some": "value"})
        await pilot.pause()
        assert not hint.display
