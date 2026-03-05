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
from baalbek.widgets.run_panel import RunPanel


class CommanderScreen(Screen):
    BINDINGS = [
        Binding("ctrl+r", "run_command", "Run"),
        Binding("ctrl+h", "toggle_history", "History"),
        Binding("ctrl+d", "reset_defaults", "Reset"),
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
            from baalbek.widgets.history_list import HistoryList
            from baalbek.widgets.output_viewer import OutputViewer
            if isinstance(mc.focused_column, OutputViewer):
                self._zoom_output(mc.focused_column._raw_output)
            elif isinstance(mc.focused_column, (ParameterList, RunPanel)):
                mc.select_highlighted()
            elif isinstance(mc.focused_column, HistoryList):
                record = mc.focused_column.selected_record
                if record:
                    mc.show_output(record.raw_output)
            else:
                mc.move_focus_right()
                self._update_breadcrumbs()
            event.prevent_default()
        elif key == "tab":
            mc = self.query_one(MillerColumns)
            mc.move_focus_right()
            self._update_breadcrumbs()
            event.prevent_default()
        elif key == "shift+tab":
            mc = self.query_one(MillerColumns)
            mc.move_focus_left()
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
        elif key == "s":
            self._cycle_sort(reverse=False)
            event.prevent_default()
        elif key == "S":
            self._cycle_sort(reverse=True)
            event.prevent_default()

    def _update_breadcrumbs(self) -> None:
        mc = self.query_one(MillerColumns)
        self.query_one(Breadcrumbs).path = mc.current_path

    def on_mount(self) -> None:
        self._apply_frequency_sort()

    def _get_frequency_scores(self) -> dict[str, float]:
        from baalbek.db import HistoryDB, compute_frequency_scores

        try:
            db = HistoryDB(self.app._db_path)
            try:
                runs = db.recent_command_data(days=7)
            finally:
                db.close()
            return compute_frequency_scores(runs, set(self._commands.keys()))
        except AttributeError:
            return {}

    def _apply_frequency_sort(self) -> None:
        from baalbek.db import SortMode

        mc = self.query_one(MillerColumns)
        frequency_scores = self._get_frequency_scores()
        mc.apply_sort(SortMode.FREQUENCY, False, frequency_scores)

    def _cycle_sort(self, reverse: bool) -> None:
        from baalbek.db import SortMode

        mc = self.query_one(MillerColumns)
        mc.cycle_sort(reverse=reverse)

        frequency_scores: dict[str, float] = {}
        if mc.sort_mode == SortMode.FREQUENCY:
            frequency_scores = self._get_frequency_scores()

        mc.apply_sort(mc.sort_mode, mc.sort_reversed, frequency_scores)

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

    def action_reset_defaults(self) -> None:
        mc = self.query_one(MillerColumns)
        col = mc.focused_column
        if isinstance(col, ParameterList):
            col.reset_to_defaults()
        elif isinstance(col, RunPanel):
            col.parameter_list.reset_to_defaults()

    def on_run_panel_run_requested(self, event) -> None:
        self.action_run_command()

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
