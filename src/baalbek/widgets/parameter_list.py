from __future__ import annotations

from typing import Any

from textual import on
from textual.message import Message
from textual.widgets import OptionList
from textual.widgets.option_list import Option

from baalbek.db import HistoryDB
from baalbek.schemas import CommandSchema
from baalbek.widgets.option_form import _default_str


class ParameterList(OptionList):
    can_focus = False

    class Selected(Message):
        def __init__(self, parameter_list: ParameterList) -> None:
            super().__init__()
            self.parameter_list = parameter_list

    def __init__(self, schema: CommandSchema, **kwargs) -> None:
        self._schema = schema
        self._param_names: list[str] = []
        self._values: dict[str, Any] = {}
        options = self._build_options(schema)
        super().__init__(*options, **kwargs)

    @property
    def _command_path(self) -> str:
        return "/".join(s.name for s in self._schema.path_from_root)

    def on_mount(self) -> None:
        if self.has_class("preview"):
            return
        db_path = getattr(self.app, "_db_path", None)
        if db_path is None:
            return
        db = HistoryDB(db_path)
        try:
            saved = db.load_draft(self._command_path)
        finally:
            db.close()
        if saved:
            self._values = saved
            self._rebuild_display()

    def _build_options(self, schema: CommandSchema) -> list[Option]:
        options: list[Option] = []
        self._param_names = []
        for arg in schema.arguments:
            self._param_names.append(arg.name)
            val = self._values.get(arg.name, _default_str(arg.default))
            label = self._format_row(arg.name, val, required=arg.required)
            options.append(Option(label, id=f"param-{arg.name}"))
        for opt in schema.options:
            self._param_names.append(opt.name)
            val = self._values.get(opt.name)
            if val is None:
                if opt.is_flag:
                    val = bool(opt.default)
                else:
                    val = _default_str(opt.default)
            label = self._format_row(opt.name, val)
            options.append(Option(label, id=f"param-{opt.name}"))
        return options

    @staticmethod
    def _format_row(name: str, value: Any, required: bool = False) -> str:
        display_val = str(value) if value not in (None, "", False) else "—"
        if isinstance(value, bool) and value:
            display_val = "✓"
        suffix = " *" if required else ""
        return f"{name}{suffix}: {display_val}"

    def get_values(self) -> dict[str, Any]:
        return dict(self._values)

    @property
    def highlighted_param_name(self) -> str | None:
        idx = self.highlighted
        if idx is not None and 0 <= idx < len(self._param_names):
            return self._param_names[idx]
        return None

    def open_edit_for_highlighted(self) -> None:
        from baalbek.screens.parameter_edit import ParameterFormModal

        focus_param = self.highlighted_param_name
        self.app.push_screen(
            ParameterFormModal(self._schema, focus_param, dict(self._values)),
            callback=self._on_modal_done,
        )

    def _on_modal_done(self, values: dict[str, Any] | None) -> None:
        if values is None:
            return
        self._values = values
        self._rebuild_display()
        self._save_draft()

    def _save_draft(self) -> None:
        db_path = getattr(self.app, "_db_path", None)
        if db_path is None:
            return
        db = HistoryDB(db_path)
        try:
            db.save_draft(self._command_path, self._values)
        finally:
            db.close()

    def reset_to_defaults(self) -> None:
        self._values = {}
        self._rebuild_display()
        db_path = getattr(self.app, "_db_path", None)
        if db_path is None:
            return
        db = HistoryDB(db_path)
        try:
            db.delete_draft(self._command_path)
        finally:
            db.close()

    def _rebuild_display(self) -> None:
        self.clear_options()
        options = self._build_options(self._schema)
        self.add_options(options)

    @on(OptionList.OptionHighlighted)
    def _on_highlight(self, event: OptionList.OptionHighlighted) -> None:
        if self.has_class("preview"):
            return
        self.post_message(self.Selected(self))
