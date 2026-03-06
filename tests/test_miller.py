from __future__ import annotations

import pytest
from textual.app import App, ComposeResult

from baalbek.db import SortMode
from baalbek.schemas import CommandSchema, OptionSchema
from baalbek.widgets.command_list import CommandList
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
        assert mc.column_count >= 2


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
        committed_after_select = len(mc._committed)
        mc.go_back()
        await pilot.pause()
        assert len(mc._committed) < committed_after_select


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


@pytest.mark.asyncio
async def test_miller_default_sort_mode():
    async with MillerApp(make_commands()).run_test() as pilot:
        mc = pilot.app.query_one(MillerColumns)
        assert mc.sort_mode == SortMode.FREQUENCY
        assert mc.sort_reversed is False


@pytest.mark.asyncio
async def test_miller_cycle_sort_forward():
    async with MillerApp(make_commands()).run_test() as pilot:
        mc = pilot.app.query_one(MillerColumns)
        mc.cycle_sort(reverse=False)
        assert mc.sort_mode == SortMode.ALPHA
        assert mc.sort_reversed is False
        mc.cycle_sort(reverse=False)
        assert mc.sort_mode == SortMode.FREQUENCY


@pytest.mark.asyncio
async def test_miller_cycle_sort_reverse():
    async with MillerApp(make_commands()).run_test() as pilot:
        mc = pilot.app.query_one(MillerColumns)
        mc.cycle_sort(reverse=True)
        assert mc.sort_mode == SortMode.ALPHA
        assert mc.sort_reversed is True


@pytest.mark.asyncio
async def test_miller_apply_sort_alpha():
    async with MillerApp(make_commands()).run_test() as pilot:
        mc = pilot.app.query_one(MillerColumns)
        await pilot.pause()
        mc.apply_sort(SortMode.ALPHA, False, {})
        first_col = mc._committed[0]
        assert isinstance(first_col, CommandList)
        labels = first_col.get_labels()
        plain = [l.replace(" \u25b8", "") for l in labels]
        assert plain == sorted(plain)


@pytest.mark.asyncio
async def test_miller_apply_sort_frequency():
    async with MillerApp(make_commands()).run_test() as pilot:
        mc = pilot.app.query_one(MillerColumns)
        await pilot.pause()
        scores = {"logs": 10.0, "deploy": 1.0}
        mc.apply_sort(SortMode.FREQUENCY, False, scores)
        first_col = mc._committed[0]
        assert isinstance(first_col, CommandList)
        labels = first_col.get_labels()
        assert labels[0].startswith("logs")


@pytest.mark.asyncio
async def test_miller_apply_sort_frequency_reversed():
    async with MillerApp(make_commands()).run_test() as pilot:
        mc = pilot.app.query_one(MillerColumns)
        await pilot.pause()
        scores = {"logs": 10.0, "deploy": 1.0}
        mc.apply_sort(SortMode.FREQUENCY, True, scores)
        first_col = mc._committed[0]
        assert isinstance(first_col, CommandList)
        labels = first_col.get_labels()
        assert labels[0].startswith("deploy")


def make_deep_commands() -> dict[str, CommandSchema]:
    leaf = CommandSchema(
        name="leaf", docstring="A leaf command", options=[], arguments=[],
    )
    mid = CommandSchema(
        name="mid",
        docstring="Mid group",
        options=[],
        arguments=[],
        subcommands={"leaf": leaf},
        is_group=True,
    )
    top = CommandSchema(
        name="top",
        docstring="Top group",
        options=[],
        arguments=[],
        subcommands={"mid": mid},
        is_group=True,
    )
    other = CommandSchema(
        name="other", docstring="Other command", options=[], arguments=[],
    )
    return {"top": top, "other": other}


@pytest.mark.asyncio
async def test_all_columns_visible_when_they_fit():
    async with MillerApp(make_deep_commands()).run_test(size=(200, 40)) as pilot:
        mc = pilot.app.query_one(MillerColumns)
        await pilot.pause()
        mc.select_command("top")
        await pilot.pause()
        mc.select_command("mid")
        await pilot.pause()
        mc.select_command("leaf")
        await pilot.pause()
        all_cols = mc._columns
        visible = [c for c in all_cols if c.display]
        assert len(all_cols) > 3
        assert len(visible) == len(all_cols)


def make_deep_commands() -> dict[str, CommandSchema]:
    leaf = CommandSchema(
        name="leaf", docstring="A leaf", options=[], arguments=[],
    )
    mid = CommandSchema(
        name="mid",
        docstring="Middle group",
        options=[],
        arguments=[],
        subcommands={"leaf": leaf},
        is_group=True,
    )
    top = CommandSchema(
        name="top",
        docstring="Top group",
        options=[],
        arguments=[],
        subcommands={"mid": mid},
        is_group=True,
    )
    flat = CommandSchema(
        name="flat", docstring="Flat cmd", options=[], arguments=[],
    )
    return {"top": top, "flat": flat}


@pytest.mark.asyncio
async def test_preview_unfurls_recursively():
    async with MillerApp(make_deep_commands()).run_test(size=(200, 40)) as pilot:
        mc = pilot.app.query_one(MillerColumns)
        await pilot.pause()
        first_col = mc._committed[0]
        for idx, schema in enumerate(first_col._schemas):
            if schema.name == "top":
                first_col.highlighted = idx
                break
        await pilot.pause()
        preview_cols = mc._preview
        assert len(preview_cols) >= 3


@pytest.mark.asyncio
async def test_leaf_command_creates_run_panel():
    from baalbek.widgets.run_panel import RunPanel
    commands = make_commands()
    async with MillerApp(commands).run_test() as pilot:
        mc = pilot.app.query_one(MillerColumns)
        await pilot.pause()
        mc.select_command("logs")
        await pilot.pause()
        panels = pilot.app.query(RunPanel)
        assert len(panels) >= 1
