from __future__ import annotations

import pytest
from textual.app import App, ComposeResult
from textual.widgets import Button

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
    def __init__(self, schema: CommandSchema) -> None:
        super().__init__()
        self._schema = schema

    def compose(self) -> ComposeResult:
        yield RunPanel(self._schema)


@pytest.mark.asyncio
async def test_run_panel_has_button():
    async with RunPanelApp(make_leaf_command()).run_test() as pilot:
        await pilot.pause()
        btn = pilot.app.query_one("#run-button", Button)
        assert btn is not None


@pytest.mark.asyncio
async def test_run_button_disabled_when_required_arg_missing():
    async with RunPanelApp(make_leaf_command(required_arg=True)).run_test() as pilot:
        await pilot.pause()
        btn = pilot.app.query_one("#run-button", Button)
        assert btn.disabled is True


@pytest.mark.asyncio
async def test_run_button_enabled_when_no_required_args():
    async with RunPanelApp(make_leaf_command(required_arg=False)).run_test() as pilot:
        await pilot.pause()
        btn = pilot.app.query_one("#run-button", Button)
        assert btn.disabled is False


@pytest.mark.asyncio
async def test_run_button_enables_after_filling_required_arg():
    schema = make_leaf_command(required_arg=True)
    async with RunPanelApp(schema).run_test() as pilot:
        await pilot.pause()
        panel = pilot.app.query_one(RunPanel)
        btn = pilot.app.query_one("#run-button", Button)
        assert btn.disabled is True
        panel.parameter_list._values["target"] = "prod"
        panel.parameter_list._rebuild_display()
        await pilot.pause()
        panel._update_button_state()
        await pilot.pause()
        assert btn.disabled is False


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
