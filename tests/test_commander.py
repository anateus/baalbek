from __future__ import annotations

import click
import pytest
from textual.app import App

from baalbek.screens.commander import CommanderScreen
from baalbek.widgets.breadcrumbs import Breadcrumbs
from baalbek.widgets.miller import MillerColumns


@click.group()
def sample_cli():
    pass


@sample_cli.command()
@click.option("--name", default="world")
def greet(name):
    click.echo(f"Hello {name}")


@sample_cli.group()
def deploy():
    pass


@deploy.command()
@click.argument("service_name")
def service(service_name):
    pass


class CommanderApp(App):
    def on_mount(self) -> None:
        self.push_screen(CommanderScreen(sample_cli))


@pytest.mark.asyncio
async def test_screen_renders():
    async with CommanderApp().run_test() as pilot:
        await pilot.pause()
        screen = pilot.app.screen
        assert isinstance(screen, CommanderScreen)


@pytest.mark.asyncio
async def test_has_breadcrumbs():
    async with CommanderApp().run_test() as pilot:
        await pilot.pause()
        pilot.app.screen.query_one(Breadcrumbs)


@pytest.mark.asyncio
async def test_has_miller_columns():
    async with CommanderApp().run_test() as pilot:
        await pilot.pause()
        mc = pilot.app.screen.query_one(MillerColumns)
        assert mc.column_count >= 2


@pytest.mark.asyncio
async def test_s_key_cycles_sort_mode():
    from baalbek.db import SortMode

    async with CommanderApp().run_test() as pilot:
        await pilot.pause()
        mc = pilot.app.screen.query_one(MillerColumns)
        assert mc.sort_mode == SortMode.FREQUENCY
        await pilot.press("s")
        assert mc.sort_mode == SortMode.ALPHA
        assert mc.sort_reversed is False
        await pilot.press("s")
        assert mc.sort_mode == SortMode.FREQUENCY


@pytest.mark.asyncio
async def test_shift_s_key_cycles_sort_reversed():
    from baalbek.db import SortMode

    async with CommanderApp().run_test() as pilot:
        await pilot.pause()
        mc = pilot.app.screen.query_one(MillerColumns)
        await pilot.press("S")
        assert mc.sort_mode == SortMode.ALPHA
        assert mc.sort_reversed is True
