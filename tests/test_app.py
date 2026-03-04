import click

from baalbek import Baalbek, tui


def test_tui_decorator_adds_command():
    @tui()
    @click.group()
    def cli():
        pass

    assert "tui" in cli.commands


def test_tui_decorator_custom_name():
    @tui(command="ui")
    @click.group()
    def cli():
        pass

    assert "ui" in cli.commands


def test_baalbek_app_creation():
    @click.group()
    def cli():
        pass

    app = Baalbek(cli)
    assert app is not None


def test_tui_on_non_group():
    @tui()
    @click.command()
    def single():
        pass

    assert isinstance(single, click.Group)
    assert "tui" in single.commands
