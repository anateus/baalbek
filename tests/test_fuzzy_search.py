from __future__ import annotations

import click
import pytest
from textual.app import App

from baalbek.introspect import introspect_click_app
from baalbek.screens.commander import CommanderScreen
from baalbek.widgets.miller import MillerColumns
from baalbek.widgets.search_bar import SearchBar


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


@sample_cli.command()
def status():
    click.echo("ok")


class FuzzyApp(App):
    def on_mount(self) -> None:
        commands = introspect_click_app(sample_cli, exclude_names={"tui"})
        self.push_screen(CommanderScreen(commands))


@pytest.mark.asyncio
async def test_slash_activates_search():
    async with FuzzyApp().run_test() as pilot:
        await pilot.pause()
        bar = pilot.app.screen.query_one(SearchBar)
        assert bar.display is False
        await pilot.press("/")
        await pilot.pause()
        assert bar.display is True


@pytest.mark.asyncio
async def test_search_moves_highlight():
    async with FuzzyApp().run_test() as pilot:
        await pilot.pause()
        mc = pilot.app.screen.query_one(MillerColumns)
        focused = mc.focused_column
        initial_idx = focused.highlighted

        await pilot.press("/")
        await pilot.press("d", "e", "p")
        await pilot.pause()

        labels = mc.get_focused_labels()
        deploy_idx = labels.index("deploy")
        assert focused.highlighted == deploy_idx


@pytest.mark.asyncio
async def test_search_enter_navigates_and_restarts():
    async with FuzzyApp().run_test() as pilot:
        await pilot.pause()
        mc = pilot.app.screen.query_one(MillerColumns)
        initial_path = mc.current_path

        await pilot.press("/")
        await pilot.press("d", "e", "p")
        await pilot.press("enter")
        await pilot.pause()

        bar = pilot.app.screen.query_one(SearchBar)
        assert bar.display is True
        assert bar.query_text == ""
        assert mc.current_path != initial_path
        assert "deploy" in mc.current_path


@pytest.mark.asyncio
async def test_search_escape_preserves_position():
    async with FuzzyApp().run_test() as pilot:
        await pilot.pause()
        mc = pilot.app.screen.query_one(MillerColumns)
        focused = mc.focused_column

        await pilot.press("/")
        await pilot.press("d", "e", "p")
        await pilot.pause()
        labels = mc.get_focused_labels()
        deploy_idx = labels.index("deploy")
        assert focused.highlighted == deploy_idx

        await pilot.press("escape")
        await pilot.pause()
        bar = pilot.app.screen.query_one(SearchBar)
        assert bar.display is False
        assert focused.highlighted == deploy_idx


@pytest.mark.asyncio
async def test_backspace_on_empty_exits_search():
    async with FuzzyApp().run_test() as pilot:
        await pilot.pause()
        bar = pilot.app.screen.query_one(SearchBar)
        await pilot.press("/")
        assert bar.display is True
        await pilot.press("backspace")
        await pilot.pause()
        assert bar.display is False


@pytest.mark.asyncio
async def test_search_bar_shows_query():
    async with FuzzyApp().run_test() as pilot:
        await pilot.pause()
        bar = pilot.app.screen.query_one(SearchBar)
        await pilot.press("/")
        await pilot.press("d", "e", "p")
        await pilot.pause()
        assert bar.query_text == "dep"
        assert "/dep" in bar.render_text
