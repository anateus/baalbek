from __future__ import annotations

from pathlib import Path

import pytest
from textual.app import App

from baalbek.schemas import ArgumentSchema, CommandSchema, OptionSchema
from baalbek.screens.mise_commander import MiseCommanderScreen, _split_generic_args
from baalbek.widgets.miller import MillerColumns


def make_mise_commands() -> dict[str, CommandSchema]:
    prod = CommandSchema(
        name="prod",
        docstring="Deploy to prod",
        options=[
            OptionSchema(
                name="version",
                type="STRING",
                default=None,
                required=False,
                is_flag=False,
                is_boolean_flag=False,
                flag_value=None,
                opts=["--version"],
                secondary_opts=[],
                help="Version tag",
                choices=None,
                multiple=False,
                nargs=1,
                counting=False,
            ),
        ],
        arguments=[],
        run_name="deploy:infra:prod",
    )
    infra = CommandSchema(
        name="infra",
        docstring=None,
        options=[],
        arguments=[],
        subcommands={"prod": prod},
        is_group=True,
    )
    prod.parent = infra
    deploy = CommandSchema(
        name="deploy",
        docstring=None,
        options=[],
        arguments=[],
        subcommands={"infra": infra},
        is_group=True,
    )
    infra.parent = deploy
    return {"deploy": deploy}


def make_mise_command_with_generic_args() -> dict[str, CommandSchema]:
    task = CommandSchema(
        name="build",
        docstring="Build project",
        options=[],
        arguments=[
            ArgumentSchema(
                name="arguments",
                type="STRING",
                required=False,
                default=None,
                choices=None,
                multiple=False,
                nargs=1,
            )
        ],
        run_name="build",
    )
    return {"build": task}


class MiseApp(App):
    def __init__(self, commands: dict[str, CommandSchema], db_path: Path | None = None) -> None:
        super().__init__()
        self._commands = commands
        self._db_path = db_path

    def on_mount(self) -> None:
        self.push_screen(
            MiseCommanderScreen(self._commands, app_name="test-mise")
        )


@pytest.mark.asyncio
async def test_mise_build_command_args_with_run_name(tmp_path):
    commands = make_mise_commands()
    db_path = tmp_path / "history.db"
    async with MiseApp(commands, db_path=db_path).run_test() as pilot:
        await pilot.pause()
        screen = pilot.app.screen
        assert isinstance(screen, MiseCommanderScreen)
        mc = screen.query_one(MillerColumns)
        mc.select_command("deploy")
        await pilot.pause()
        mc.select_command("infra")
        await pilot.pause()
        mc.select_command("prod")
        await pilot.pause()
        args = screen.build_command_args()
        assert args[0] == "mise"
        assert args[1] == "run"
        assert args[2] == "deploy:infra:prod"


@pytest.mark.asyncio
async def test_mise_build_returns_empty_when_no_leaf(tmp_path):
    commands = make_mise_commands()
    db_path = tmp_path / "history.db"
    async with MiseApp(commands, db_path=db_path).run_test() as pilot:
        await pilot.pause()
        screen = pilot.app.screen
        args = screen.build_command_args()
        assert args == []


def test_split_generic_args():
    result = _split_generic_args("--flag value 'arg with spaces'")
    assert result == ["--flag", "value", "arg with spaces"]


def test_split_generic_args_empty():
    result = _split_generic_args("")
    assert result == []


def test_split_generic_args_none():
    result = _split_generic_args("  ")
    assert result == []
