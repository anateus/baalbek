import click
import pytest

from baalbek import Baalbek, tui
from baalbek.db import HistoryDB, SortMode
from baalbek.widgets.breadcrumbs import Breadcrumbs
from baalbek.widgets.command_list import CommandList
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


@pytest.mark.asyncio
async def test_sort_toggle_with_history(tmp_path):
    db_path = tmp_path / "history.db"
    db = HistoryDB(db_path)
    db.insert_run("greet --name world", '["script", "greet"]', 0, None, None)
    db.insert_run("greet --name world", '["script", "greet"]', 0, None, None)
    db.insert_run("greet --name world", '["script", "greet"]', 0, None, None)
    db.insert_run("deploy service", '["script", "deploy"]', 0, None, None)
    db.close()

    app = Baalbek(demo_cli, db_path=db_path)
    async with app.run_test() as pilot:
        await pilot.pause()
        mc = pilot.app.screen.query_one(MillerColumns)

        assert mc.sort_mode == SortMode.FREQUENCY
        first_col = mc._committed[0]
        assert isinstance(first_col, CommandList)
        freq_labels = first_col.get_labels()
        assert freq_labels[0].startswith("greet")

        await pilot.press("s")
        assert mc.sort_mode == SortMode.ALPHA
        alpha_labels = first_col.get_labels()
        plain = [l.replace(" ▸", "") for l in alpha_labels]
        assert plain == sorted(plain)

        await pilot.press("s")
        assert mc.sort_mode == SortMode.FREQUENCY

        await pilot.press("S")
        assert mc.sort_mode == SortMode.ALPHA
        assert mc.sort_reversed is True
