from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.message import Message
from textual.widget import Widget

from baalbek.schemas import CommandSchema
from baalbek.widgets.command_list import CommandList
from baalbek.widgets.option_form import OptionForm


class MillerColumns(Widget):
    class CommandSelected(Message):
        def __init__(self, schema: CommandSchema) -> None:
            super().__init__()
            self.schema = schema

    MAX_VISIBLE = 3

    def __init__(self, commands: dict[str, CommandSchema], **kwargs) -> None:
        super().__init__(**kwargs)
        self._root_commands = commands
        self._columns: list[Widget] = []
        self._path: list[str] = []
        self._schemas_at_depth: list[dict[str, CommandSchema] | CommandSchema] = []

    def compose(self) -> ComposeResult:
        yield Horizontal(id="miller-viewport")

    def on_mount(self) -> None:
        col = CommandList(self._root_commands)
        self._columns.append(col)
        self._schemas_at_depth.append(self._root_commands)
        viewport = self.query_one("#miller-viewport")
        viewport.mount(col)

    @property
    def column_count(self) -> int:
        return len(self._columns)

    @property
    def current_path(self) -> list[str]:
        return list(self._path)

    def select_command(self, name: str) -> None:
        depth = len(self._path)
        schemas = self._schemas_at_depth[depth]
        if not isinstance(schemas, dict) or name not in schemas:
            return
        schema = schemas[name]
        self._path.append(name)
        self._trim_columns_to(depth + 1)
        viewport = self.query_one("#miller-viewport")

        if schema.is_group:
            if schema.has_own_params:
                form = OptionForm(schema)
                self._columns.append(form)
                self._schemas_at_depth.append(schema)
                viewport.mount(form)
            child_list = CommandList(schema.subcommands)
            self._columns.append(child_list)
            self._schemas_at_depth.append(schema.subcommands)
            viewport.mount(child_list)
        else:
            form = OptionForm(schema)
            self._columns.append(form)
            self._schemas_at_depth.append(schema)
            viewport.mount(form)
            self.post_message(self.CommandSelected(schema))

        self._update_viewport()

    def go_back(self) -> None:
        if not self._path:
            return
        self._path.pop()
        depth = len(self._path)
        self._trim_columns_to(depth + 1)
        self._update_viewport()

    def _trim_columns_to(self, count: int) -> None:
        while len(self._columns) > count:
            col = self._columns.pop()
            self._schemas_at_depth.pop()
            col.remove()

    def show_history(self, records: list) -> None:
        from baalbek.widgets.history_list import HistoryList

        self._remove_history_columns()
        history = HistoryList(records, id="history-column")
        self._columns.append(history)
        viewport = self.query_one("#miller-viewport")
        viewport.mount(history)
        self._update_viewport()

    def show_output(self, raw_output: bytes) -> None:
        from baalbek.widgets.output_viewer import OutputViewer

        for col in list(self._columns):
            if isinstance(col, OutputViewer):
                self._columns.remove(col)
                col.remove()
                break
        viewer = OutputViewer(raw_output, id="output-column")
        self._columns.append(viewer)
        viewport = self.query_one("#miller-viewport")
        viewport.mount(viewer)
        self._update_viewport()

    def _remove_history_columns(self) -> None:
        from baalbek.widgets.history_list import HistoryList
        from baalbek.widgets.output_viewer import OutputViewer

        to_remove = [c for c in self._columns if isinstance(c, (HistoryList, OutputViewer))]
        for col in to_remove:
            self._columns.remove(col)
            col.remove()

    def _update_viewport(self) -> None:
        for i, col in enumerate(self._columns):
            if i < len(self._columns) - self.MAX_VISIBLE:
                col.display = False
            else:
                col.display = True
