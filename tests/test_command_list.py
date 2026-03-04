from __future__ import annotations

import pytest
from textual.app import App, ComposeResult

from baalbek.schemas import CommandSchema
from baalbek.widgets.command_list import CommandList


def make_commands() -> dict[str, CommandSchema]:
    deploy = CommandSchema(
        name="deploy",
        docstring="Deploy services",
        options=[],
        arguments=[],
        subcommands={"web": CommandSchema(
            name="web", docstring=None, options=[], arguments=[],
        )},
        is_group=True,
    )
    logs = CommandSchema(
        name="logs",
        docstring="View logs",
        options=[],
        arguments=[],
    )
    return {"deploy": deploy, "logs": logs}


class CommandListApp(App):
    def __init__(self, commands: dict[str, CommandSchema]) -> None:
        super().__init__()
        self._commands = commands

    def compose(self) -> ComposeResult:
        yield CommandList(self._commands)


@pytest.mark.asyncio
async def test_renders_commands():
    async with CommandListApp(make_commands()).run_test() as pilot:
        cl = pilot.app.query_one(CommandList)
        assert cl.option_count == 2


@pytest.mark.asyncio
async def test_groups_have_indicator():
    async with CommandListApp(make_commands()).run_test() as pilot:
        cl = pilot.app.query_one(CommandList)
        labels = cl.get_labels()
        deploy_label = [l for l in labels if "deploy" in l][0]
        assert "\u25b8" in deploy_label


@pytest.mark.asyncio
async def test_selected_command():
    async with CommandListApp(make_commands()).run_test() as pilot:
        cl = pilot.app.query_one(CommandList)
        await pilot.pause()
        assert cl.selected_schema is not None
