from __future__ import annotations

import click
from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Footer, Static

from baalbek.introspect import introspect_click_app
from baalbek.modes import InputMode, ModeManager
from baalbek.widgets.breadcrumbs import Breadcrumbs
from baalbek.widgets.miller import MillerColumns


class CommanderScreen(Screen):
    BINDINGS = [
        Binding("ctrl+r", "run_command", "Run"),
        Binding("ctrl+h", "toggle_history", "History"),
        Binding("escape", "quit_or_normal", "Quit/Normal"),
    ]

    def __init__(self, cli: click.BaseCommand, **kwargs) -> None:
        super().__init__(**kwargs)
        self._cli = cli
        self._mode_mgr = ModeManager()
        self._commands = introspect_click_app(cli, exclude_names={"tui"})

    def compose(self) -> ComposeResult:
        yield Breadcrumbs(id="breadcrumbs")
        yield MillerColumns(self._commands, id="miller")
        yield Static("NORMAL", id="mode-indicator")
        yield Footer()

    def on_key(self, event) -> None:
        key = event.key
        if self._mode_mgr.mode == InputMode.EDIT:
            if key == "escape":
                self._mode_mgr.exit_edit()
                self._update_mode_indicator()
                event.prevent_default()
            return

        if key in ("h", "left"):
            self.query_one(MillerColumns).go_back()
            self._update_breadcrumbs()
            event.prevent_default()
        elif key in ("l", "right", "enter"):
            mc = self.query_one(MillerColumns)
            mc.select_highlighted()
            self._update_breadcrumbs()
            event.prevent_default()
        elif key == "i":
            self._mode_mgr.enter_edit()
            self._update_mode_indicator()
            event.prevent_default()
        elif key in ("j", "down"):
            mc = self.query_one(MillerColumns)
            mc.move_cursor_down()
            event.prevent_default()
        elif key in ("k", "up"):
            mc = self.query_one(MillerColumns)
            mc.move_cursor_up()
            event.prevent_default()

    def _update_breadcrumbs(self) -> None:
        mc = self.query_one(MillerColumns)
        self.query_one(Breadcrumbs).path = mc.current_path

    def _update_mode_indicator(self) -> None:
        mode = self._mode_mgr.mode
        indicator = self.query_one("#mode-indicator", Static)
        if mode == InputMode.NORMAL:
            indicator.update("NORMAL")
        else:
            indicator.update("EDIT")

    def action_quit_or_normal(self) -> None:
        if self._mode_mgr.mode == InputMode.EDIT:
            self._mode_mgr.exit_edit()
            self._update_mode_indicator()
        else:
            self.app.exit()

    def action_run_command(self) -> None:
        import json

        from baalbek.db import HistoryDB
        from baalbek.runner import run_command

        args = self.build_command_args()
        if not args:
            return

        command_str = " ".join(args)

        def _execute():
            result = run_command(args)
            db = HistoryDB(self.app._db_path)
            try:
                db.insert_run(
                    command=command_str,
                    args_json=json.dumps(args),
                    exit_code=result.exit_code,
                    raw_output=result.raw_output,
                    plain_output=result.plain_output,
                )
            finally:
                db.close()

        with self.app.suspend():
            _execute()

        mc = self.query_one(MillerColumns)
        db = HistoryDB(self.app._db_path)
        try:
            records = db.list_runs()
        finally:
            db.close()
        mc.show_history(records)

    def action_toggle_history(self) -> None:
        from baalbek.db import HistoryDB

        mc = self.query_one(MillerColumns)
        db = HistoryDB(self.app._db_path)
        try:
            records = db.list_runs()
        finally:
            db.close()
        mc.show_history(records)

    def on_history_list_selected(self, event) -> None:
        mc = self.query_one(MillerColumns)
        mc.show_output(event.record.raw_output)

    def build_command_args(self) -> list[str]:
        mc = self.query_one(MillerColumns)
        return mc.get_command_args()
