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
        self._focus_index: int = 0

    def compose(self) -> ComposeResult:
        yield Horizontal(id="miller-viewport")

    def on_mount(self) -> None:
        col = CommandList(self._root_commands)
        self._columns.append(col)
        self._schemas_at_depth.append(self._root_commands)
        viewport = self.query_one("#miller-viewport")
        viewport.mount(col)
        if col.selected_schema:
            self._show_preview(col.selected_schema)
        self._focus_index = 0
        self._update_focus_styles()

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
        self._clear_preview()
        self._path.append(name)
        self._trim_columns_to(depth + 1)
        viewport = self.query_one("#miller-viewport")

        if schema.is_group:
            if schema.has_own_params:
                form = OptionForm(schema)
                self._columns.append(form)
                self._schemas_at_depth.append(schema)
                viewport.mount(form)
                self._focus_index = len(self._columns) - 1
            child_list = CommandList(schema.subcommands)
            self._columns.append(child_list)
            self._schemas_at_depth.append(schema.subcommands)
            viewport.mount(child_list)
            if not schema.has_own_params:
                self._focus_index = len(self._columns) - 1
        else:
            form = OptionForm(schema)
            self._columns.append(form)
            self._schemas_at_depth.append(schema)
            viewport.mount(form)
            self._focus_index = len(self._columns) - 1
            self.post_message(self.CommandSelected(schema))

        self._update_viewport()
        self._update_focus_styles()

    def _show_preview(self, schema: CommandSchema) -> None:
        self._clear_preview()
        viewport = self.query_one("#miller-viewport")
        if schema.is_group:
            if schema.has_own_params:
                form = OptionForm(schema)
                form.add_class("preview")
                self._columns.append(form)
                viewport.mount(form)
            child_list = CommandList(schema.subcommands)
            child_list.add_class("preview")
            self._columns.append(child_list)
            viewport.mount(child_list)
        else:
            form = OptionForm(schema)
            form.add_class("preview")
            self._columns.append(form)
            viewport.mount(form)
        self._update_viewport()

    def _clear_preview(self) -> None:
        to_remove = [c for c in self._columns if c.has_class("preview")]
        for col in to_remove:
            self._columns.remove(col)
            col.remove()

    def on_command_list_selected(self, event: CommandList.Selected) -> None:
        self._show_preview(event.schema)

    @property
    def focused_column(self) -> Widget | None:
        if 0 <= self._focus_index < len(self._columns):
            return self._columns[self._focus_index]
        return None

    def move_focus_right(self) -> bool:
        if self._focus_index < len(self._columns) - 1:
            self._focus_index += 1
            self._update_viewport()
            self._update_focus_styles()
            return True
        focused = self.focused_column
        if isinstance(focused, CommandList) and focused.selected_schema:
            self.select_command(focused.selected_schema.name)
            return True
        return False

    def move_focus_left(self) -> bool:
        if self._focus_index > 0:
            self._focus_index -= 1
            self._update_viewport()
            self._update_focus_styles()
            return True
        self.go_back()
        return True

    def move_cursor_down(self) -> None:
        focused = self.focused_column
        if isinstance(focused, CommandList):
            focused.action_cursor_down()

    def move_cursor_up(self) -> None:
        focused = self.focused_column
        if isinstance(focused, CommandList):
            focused.action_cursor_up()

    def select_highlighted(self) -> None:
        focused = self.focused_column
        if isinstance(focused, CommandList) and focused.selected_schema:
            self.select_command(focused.selected_schema.name)
        elif isinstance(focused, OptionForm):
            self.move_focus_right()

    def _update_focus_styles(self) -> None:
        for i, col in enumerate(self._columns):
            if i == self._focus_index:
                col.add_class("focused")
            else:
                col.remove_class("focused")

    def go_back(self) -> None:
        if not self._path:
            return
        self._clear_preview()
        self._path.pop()
        depth = len(self._path)
        self._trim_columns_to(depth + 1)
        self._focus_index = len(self._columns) - 1
        self._update_viewport()
        self._update_focus_styles()

    def get_command_args(self) -> list[str]:
        args: list[str] = []
        for col in self._columns:
            if isinstance(col, CommandList):
                if col.selected_schema:
                    args.append(col.selected_schema.name)
            elif isinstance(col, OptionForm):
                schema = col._schema
                values = col.get_values()
                for opt in schema.options:
                    val = values.get(opt.name)
                    if val is None:
                        continue
                    if opt.is_flag:
                        if val and val != opt.default:
                            args.append(opt.opts[0])
                        elif not val and opt.default:
                            if opt.secondary_opts:
                                args.append(opt.secondary_opts[0])
                    elif val != "" and str(val) != str(opt.default):
                        args.extend([opt.opts[0], str(val)])
                for arg_schema in schema.arguments:
                    val = values.get(arg_schema.name)
                    if val and val != "":
                        args.append(str(val))
        return args

    def _trim_columns_to(self, count: int) -> None:
        from baalbek.widgets.history_list import HistoryList
        from baalbek.widgets.output_viewer import OutputViewer

        while len(self._columns) > count:
            col = self._columns.pop()
            if not isinstance(col, (HistoryList, OutputViewer)):
                if self._schemas_at_depth:
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
