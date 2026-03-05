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


@pytest.mark.asyncio
async def test_resort_reorders_options():
    commands = make_commands()
    async with CommandListApp(commands).run_test() as pilot:
        cl = pilot.app.query_one(CommandList)
        original_labels = cl.get_labels()
        cl.resort(["logs", "deploy"])
        new_labels = cl.get_labels()
        assert new_labels[0].startswith("logs")
        assert new_labels[1].startswith("deploy")
        assert new_labels != original_labels


@pytest.mark.asyncio
async def test_resort_preserves_highlight():
    commands = make_commands()
    async with CommandListApp(commands).run_test() as pilot:
        cl = pilot.app.query_one(CommandList)
        await pilot.pause()
        highlighted_before = cl.selected_schema
        assert highlighted_before is not None
        old_name = highlighted_before.name
        cl.resort(["logs", "deploy"])
        highlighted_after = cl.selected_schema
        assert highlighted_after is not None
        assert highlighted_after.name == old_name


@pytest.mark.asyncio
async def test_resort_with_unknown_names_puts_them_last():
    commands = make_commands()
    async with CommandListApp(commands).run_test() as pilot:
        cl = pilot.app.query_one(CommandList)
        cl.resort(["logs"])
        labels = cl.get_labels()
        assert labels[0].startswith("logs")
        assert len(labels) == 2
