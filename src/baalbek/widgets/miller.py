from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.message import Message
from textual.widget import Widget

from baalbek.schemas import CommandSchema
from baalbek.widgets.command_list import CommandList
from baalbek.widgets.parameter_list import ParameterList


class MillerColumns(Widget):
    class CommandSelected(Message):
        def __init__(self, schema: CommandSchema) -> None:
            super().__init__()
            self.schema = schema

    MAX_VISIBLE = 3

    def __init__(self, commands: dict[str, CommandSchema], **kwargs) -> None:
        super().__init__(**kwargs)
        self._root_commands = commands
        self._committed: list[Widget] = []
        self._schemas_at_depth: list[dict[str, CommandSchema] | CommandSchema] = []
        self._preview: list[Widget] = []
        self._path: list[str] = []
        self._focus_index: int = 0

    @property
    def _columns(self) -> list[Widget]:
        return self._committed + self._preview

    def compose(self) -> ComposeResult:
        yield Horizontal(id="miller-viewport")

    def on_mount(self) -> None:
        col = CommandList(self._root_commands)
        self._committed.append(col)
        self._schemas_at_depth.append(self._root_commands)
        viewport = self.query_one("#miller-viewport")
        viewport.mount(col)
        self._focus_index = 0
        self._update_focus_styles()
        self._sync_preview()

    @property
    def column_count(self) -> int:
        return len(self._columns)

    @property
    def current_path(self) -> list[str]:
        return list(self._path)

    def select_command(self, name: str) -> None:
        depth = len(self._path)
        if depth >= len(self._schemas_at_depth):
            return
        schemas = self._schemas_at_depth[depth]
        if not isinstance(schemas, dict) or name not in schemas:
            return
        schema = schemas[name]
        self._clear_preview()
        self._path.append(name)
        self._trim_committed_to(depth + 1)
        viewport = self.query_one("#miller-viewport")

        if schema.is_group:
            if schema.has_own_params:
                form = ParameterList(schema)
                self._committed.append(form)
                self._schemas_at_depth.append(schema)
                viewport.mount(form)
                self._focus_index = len(self._committed) - 1
            child_list = CommandList(schema.subcommands)
            self._committed.append(child_list)
            self._schemas_at_depth.append(schema.subcommands)
            viewport.mount(child_list)
            if not schema.has_own_params:
                self._focus_index = len(self._committed) - 1
        else:
            form = ParameterList(schema)
            self._committed.append(form)
            self._schemas_at_depth.append(schema)
            viewport.mount(form)
            self._focus_index = len(self._committed) - 1
            self.post_message(self.CommandSelected(schema))

        self._sync_preview()
        self._update_viewport()
        self._update_focus_styles()

    def _sync_preview(self) -> None:
        self._clear_preview()
        if not self._committed or not isinstance(self._committed[-1], CommandList):
            return
        last_cmd_list = self._committed[-1]
        schema = last_cmd_list.selected_schema
        if not schema:
            return

        viewport = self.query_one("#miller-viewport")
        if schema.is_group:
            if schema.has_own_params:
                form = ParameterList(schema)
                form.add_class("preview")
                self._preview.append(form)
                viewport.mount(form)
            child_list = CommandList(schema.subcommands)
            child_list.add_class("preview")
            self._preview.append(child_list)
            viewport.mount(child_list)
        else:
            form = ParameterList(schema)
            form.add_class("preview")
            self._preview.append(form)
            viewport.mount(form)
        self._update_viewport()

    def _clear_preview(self) -> None:
        for col in self._preview:
            col.display = False
            col.remove()
        self._preview.clear()

    def on_click(self, event) -> None:
        widget = event.widget
        while widget is not None and widget is not self:
            if widget in self._committed:
                idx = self._committed.index(widget)
                if idx != self._focus_index:
                    self._focus_index = idx
                    self._update_focus_styles()
                break
            widget = widget.parent

    def on_command_list_selected(self, event: CommandList.Selected) -> None:
        sender = event.command_list
        if sender.has_class("preview"):
            return

        try:
            sender_idx = self._committed.index(sender)
        except ValueError:
            return

        self._trim_committed_to(sender_idx + 1)

        cmd_lists_before = sum(
            1 for c in self._committed[:sender_idx]
            if isinstance(c, CommandList)
        )
        self._path = self._path[:cmd_lists_before]

        self._focus_index = min(self._focus_index, len(self._committed) - 1)
        self._sync_preview()
        self._update_focus_styles()

    @property
    def focused_column(self) -> Widget | None:
        columns = self._columns
        if 0 <= self._focus_index < len(columns):
            return columns[self._focus_index]
        return None

    def move_focus_right(self) -> bool:
        next_idx = self._focus_index + 1
        if next_idx < len(self._committed):
            self._focus_index = next_idx
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
        from baalbek.widgets.history_list import HistoryList

        focused = self.focused_column
        if isinstance(focused, (CommandList, ParameterList, HistoryList)):
            focused.action_cursor_down()

    def move_cursor_up(self) -> None:
        from baalbek.widgets.history_list import HistoryList

        focused = self.focused_column
        if isinstance(focused, (CommandList, ParameterList, HistoryList)):
            focused.action_cursor_up()

    def select_highlighted(self) -> None:
        focused = self.focused_column
        if isinstance(focused, CommandList) and focused.selected_schema:
            self.select_command(focused.selected_schema.name)
        elif isinstance(focused, ParameterList):
            focused.open_edit_for_highlighted()

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
        self._trim_committed_to(depth + 1)
        self._focus_index = len(self._committed) - 1
        self._sync_preview()
        self._update_viewport()
        self._update_focus_styles()

    def get_command_args(self) -> list[str]:
        args: list[str] = []
        for col in self._committed:
            if isinstance(col, CommandList):
                if col.selected_schema:
                    args.append(col.selected_schema.name)
            elif isinstance(col, ParameterList):
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

    def _trim_committed_to(self, count: int) -> None:
        from baalbek.widgets.history_list import HistoryList
        from baalbek.widgets.output_viewer import OutputViewer

        while len(self._committed) > count:
            col = self._committed.pop()
            if not isinstance(col, (HistoryList, OutputViewer)):
                if self._schemas_at_depth:
                    self._schemas_at_depth.pop()
            col.remove()

    def has_history(self) -> bool:
        from baalbek.widgets.history_list import HistoryList

        return any(isinstance(c, HistoryList) for c in self._committed)

    def hide_history(self) -> None:
        self._remove_history_columns()
        self._update_viewport()

    def show_history(self, records: list) -> None:
        from baalbek.widgets.history_list import HistoryList

        self._remove_history_columns()
        history = HistoryList(records)
        self._committed.append(history)
        viewport = self.query_one("#miller-viewport")
        viewport.mount(history)
        self._update_viewport()
        self._update_focus_styles()

    def show_output(self, raw_output: bytes) -> None:
        from baalbek.widgets.output_viewer import OutputViewer

        for col in list(self._committed):
            if isinstance(col, OutputViewer):
                self._committed.remove(col)
                col.display = False
                col.remove()
                break
        viewer = OutputViewer(raw_output)
        self._committed.append(viewer)
        viewport = self.query_one("#miller-viewport")
        viewport.mount(viewer)
        self._update_viewport()

    def _remove_history_columns(self) -> None:
        from baalbek.widgets.history_list import HistoryList
        from baalbek.widgets.output_viewer import OutputViewer

        to_remove = [c for c in self._committed if isinstance(c, (HistoryList, OutputViewer))]
        for col in to_remove:
            self._committed.remove(col)
            col.display = False
            col.remove()

    def _update_viewport(self) -> None:
        columns = self._columns
        n = len(columns)
        if n <= self.MAX_VISIBLE:
            for col in columns:
                col.display = True
            return
        start = min(self._focus_index, n - self.MAX_VISIBLE)
        start = max(0, start)
        end = start + self.MAX_VISIBLE
        for i, col in enumerate(columns):
            col.display = start <= i < end
