from __future__ import annotations

import functools
from pathlib import Path
from typing import Any

import click
from textual.app import App

from baalbek.screens.commander import CommanderScreen

_DEFAULT_DB_PATH = Path.home() / ".local" / "share" / "baalbek" / "history.db"


def _detect_app_name(cli: click.BaseCommand) -> str:
    if cli.name:
        return cli.name
    try:
        import tomllib
        for candidate in [Path("pyproject.toml"), Path.cwd() / "pyproject.toml"]:
            if candidate.exists():
                data = tomllib.loads(candidate.read_text())
                name = data.get("project", {}).get("name")
                if name:
                    return name
    except Exception:
        pass
    return "CLI"


class Baalbek(App):
    CSS_PATH = "baalbek.tcss"

    def __init__(self, cli: click.BaseCommand, db_path: Path | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self._cli = cli
        self._app_name = _detect_app_name(cli)
        self._db_path = db_path or _DEFAULT_DB_PATH

    def on_mount(self) -> None:
        self.push_screen(CommanderScreen(self._cli, app_name=self._app_name))


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
