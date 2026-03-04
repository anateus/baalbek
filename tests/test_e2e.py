import click
import pytest

from baalbek import Baalbek, tui
from baalbek.widgets.breadcrumbs import Breadcrumbs
from baalbek.widgets.miller import MillerColumns


@tui()
@click.group()
def demo_cli():
    pass


@demo_cli.command()
@click.option("--name", default="world")
def greet(name):
    click.echo(f"Hello {name}")


@demo_cli.group()
def deploy():
    pass


@deploy.command()
def service():
    click.echo("deployed")


@pytest.mark.asyncio
async def test_app_launches_and_shows_commands():
    app = Baalbek(demo_cli)
    async with app.run_test() as pilot:
        await pilot.pause()
        mc = pilot.app.screen.query_one(MillerColumns)
        assert mc.column_count >= 2
        bc = pilot.app.screen.query_one(Breadcrumbs)
        assert bc is not None


@pytest.mark.asyncio
async def test_navigation_into_group():
    app = Baalbek(demo_cli)
    async with app.run_test() as pilot:
        await pilot.pause()
        mc = pilot.app.screen.query_one(MillerColumns)
        mc.select_command("deploy")
        await pilot.pause()
        assert mc.column_count >= 2
        assert "deploy" in mc.current_path
