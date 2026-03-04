from __future__ import annotations

import click
from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Footer, Static

from baalbek.introspect import introspect_click_app
from baalbek.widgets.breadcrumbs import Breadcrumbs
from baalbek.widgets.miller import MillerColumns
from baalbek.widgets.parameter_list import ParameterList


class CommanderScreen(Screen):
    BINDINGS = [
        Binding("ctrl+r", "run_command", "Run"),
        Binding("ctrl+h", "toggle_history", "History"),
        Binding("escape", "quit", "Quit"),
    ]

    def __init__(self, cli: click.BaseCommand, app_name: str | None = None, app_description: str | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self._cli = cli
        self._app_name = app_name or cli.name or "CLI"
        self._app_description = app_description
        self._commands = introspect_click_app(cli, exclude_names={"tui"})

    def compose(self) -> ComposeResult:
        title = f"[b]{self._app_name}[/b]"
        if self._app_description:
            title += f" [dim]- {self._app_description}[/dim]"
        yield Static(title, id="app-title", markup=True)
        yield Breadcrumbs(id="breadcrumbs")
        yield MillerColumns(self._commands, id="miller")
        yield Footer()

    def on_key(self, event) -> None:
        key = event.key

        if key in ("h", "left"):
            mc = self.query_one(MillerColumns)
            mc.move_focus_left()
            self._update_breadcrumbs()
            event.prevent_default()
        elif key in ("l", "right", "enter"):
            mc = self.query_one(MillerColumns)
            from baalbek.widgets.output_viewer import OutputViewer
            if isinstance(mc.focused_column, OutputViewer):
                self._zoom_output(mc.focused_column._raw_output)
            elif isinstance(mc.focused_column, ParameterList):
                mc.select_highlighted()
            else:
                mc.move_focus_right()
                self._update_breadcrumbs()
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

    def action_quit(self) -> None:
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
            input("\nPress Enter to continue...")

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
        if mc.has_history():
            mc.hide_history()
            return
        db = HistoryDB(self.app._db_path)
        try:
            records = db.list_runs()
        finally:
            db.close()
        mc.show_history(records)

    def on_miller_columns_command_selected(self, event: MillerColumns.CommandSelected) -> None:
        from baalbek.db import HistoryDB

        command_path = " ".join(self.query_one(MillerColumns).get_command_args())
        if not command_path:
            return
        db = HistoryDB(self.app._db_path)
        try:
            all_records = db.list_runs()
        finally:
            db.close()
        matching = [r for r in all_records if command_path in r.command]
        if matching:
            self.query_one(MillerColumns).show_history(matching)

    def on_history_list_selected(self, event) -> None:
        mc = self.query_one(MillerColumns)
        mc.show_output(event.record.raw_output)

    def _zoom_output(self, raw_output: bytes) -> None:
        from baalbek.screens.output_zoom import OutputZoomScreen
        self.app.push_screen(OutputZoomScreen(raw_output))

    def build_command_args(self) -> list[str]:
        import sys

        mc = self.query_one(MillerColumns)
        subcommand_args = mc.get_command_args()
        if not subcommand_args:
            return []
        return [sys.argv[0]] + subcommand_args
