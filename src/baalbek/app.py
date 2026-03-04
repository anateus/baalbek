from __future__ import annotations

import functools
from pathlib import Path
from typing import Any

import click
from textual.app import App

from baalbek.screens.commander import CommanderScreen

_DEFAULT_DB_PATH = Path.home() / ".local" / "share" / "baalbek" / "history.db"


class Baalbek(App):
    CSS = """
    #miller-viewport {
        height: 1fr;
    }
    #breadcrumbs {
        height: 1;
        background: $surface;
        padding: 0 1;
    }
    #mode-indicator {
        height: 1;
        background: $surface;
        padding: 0 1;
    }
    """

    def __init__(self, cli: click.BaseCommand, db_path: Path | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self._cli = cli
        self._db_path = db_path or _DEFAULT_DB_PATH

    def on_mount(self) -> None:
        self.push_screen(CommanderScreen(self._cli))


def tui(
    command: str = "tui",
    help: str = "Open interactive TUI",
    db_path: Path | None = None,
) -> Any:
    def decorator(app: click.BaseCommand) -> click.Group:
        if isinstance(app, click.Group):
            group = app
        else:
            group = click.Group()
            group.add_command(app)

        @group.command(name=command, help=help)
        def launch_tui():
            baalbek_app = Baalbek(group, db_path=db_path)
            baalbek_app.run()

        return group

    return decorator
