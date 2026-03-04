from __future__ import annotations

import pytest
from textual.app import App, ComposeResult

from baalbek.schemas import CommandSchema, OptionSchema
from baalbek.widgets.miller import MillerColumns


def make_commands() -> dict[str, CommandSchema]:
    service = CommandSchema(
        name="service", docstring="Deploy a service", options=[], arguments=[],
    )
    container = CommandSchema(
        name="container", docstring="Deploy a container", options=[], arguments=[],
    )
    deploy = CommandSchema(
        name="deploy",
        docstring="Deploy things",
        options=[],
        arguments=[],
        subcommands={"service": service, "container": container},
        is_group=True,
    )
    logs = CommandSchema(
        name="logs", docstring="View logs", options=[], arguments=[],
    )
    return {"deploy": deploy, "logs": logs}


def make_commands_with_options() -> dict[str, CommandSchema]:
    service = CommandSchema(
        name="service", docstring="Deploy a service", options=[], arguments=[],
    )
    container = CommandSchema(
        name="container", docstring="Deploy a container", options=[], arguments=[],
    )
    deploy = CommandSchema(
        name="deploy",
        docstring="Deploy things",
        options=[
            OptionSchema(
                name="verbose",
                type="BOOL",
                default=False,
                required=False,
                is_flag=True,
                is_boolean_flag=True,
                flag_value=True,
                opts=["--verbose"],
                secondary_opts=[],
                help="Enable verbose output",
                choices=None,
                multiple=False,
                nargs=1,
                counting=False,
            ),
        ],
        arguments=[],
        subcommands={"service": service, "container": container},
        is_group=True,
    )
    logs = CommandSchema(
        name="logs", docstring="View logs", options=[], arguments=[],
    )
    return {"deploy": deploy, "logs": logs}


class MillerApp(App):
    def __init__(self, commands: dict[str, CommandSchema]) -> None:
        super().__init__()
        self._commands = commands

    def compose(self) -> ComposeResult:
        yield MillerColumns(self._commands)


@pytest.mark.asyncio
async def test_initial_column():
    async with MillerApp(make_commands()).run_test() as pilot:
        mc = pilot.app.query_one(MillerColumns)
        await pilot.pause()
        assert mc.column_count == 1


@pytest.mark.asyncio
async def test_navigate_into_group():
    async with MillerApp(make_commands()).run_test() as pilot:
        mc = pilot.app.query_one(MillerColumns)
        await pilot.pause()
        mc.select_command("deploy")
        await pilot.pause()
        assert mc.column_count >= 2


@pytest.mark.asyncio
async def test_navigate_back():
    async with MillerApp(make_commands()).run_test() as pilot:
        mc = pilot.app.query_one(MillerColumns)
        await pilot.pause()
        mc.select_command("deploy")
        await pilot.pause()
        count_after_select = mc.column_count
        mc.go_back()
        await pilot.pause()
        assert mc.column_count < count_after_select


@pytest.mark.asyncio
async def test_group_with_options_adds_extra_column():
    async with MillerApp(make_commands_with_options()).run_test() as pilot:
        mc = pilot.app.query_one(MillerColumns)
        await pilot.pause()
        mc.select_command("deploy")
        await pilot.pause()
        assert mc.column_count >= 3


@pytest.mark.asyncio
async def test_breadcrumbs_update():
    async with MillerApp(make_commands()).run_test() as pilot:
        mc = pilot.app.query_one(MillerColumns)
        await pilot.pause()
        assert mc.current_path == []
        mc.select_command("deploy")
        await pilot.pause()
        assert mc.current_path == ["deploy"]
