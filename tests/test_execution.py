from __future__ import annotations

import click
import pytest
from textual.app import App

from baalbek.screens.commander import CommanderScreen


@click.group()
def sample_cli():
    pass


@sample_cli.command()
@click.option("--name", default="world")
def greet(name):
    click.echo(f"Hello {name}")


class ExecutionApp(App):
    def on_mount(self) -> None:
        self.push_screen(CommanderScreen(sample_cli))


@pytest.mark.asyncio
async def test_build_command_args():
    async with ExecutionApp().run_test() as pilot:
        await pilot.pause()
        screen = pilot.app.screen
        assert isinstance(screen, CommanderScreen)
        args = screen.build_command_args()
        assert isinstance(args, list)
        assert args[0].endswith("pytest") or args[0].endswith("pytest.exe")
        assert args[1:] == ["greet"]
