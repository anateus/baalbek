from __future__ import annotations

from typing import Any

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Checkbox, Input, Label, Select, Static

from baalbek.schemas import CommandSchema


def _default_str(value: object) -> str:
    if value is None:
        return ""
    s = str(value)
    if "sentinel" in s.lower() or "unset" in s.lower():
        return ""
    return s


class OptionForm(VerticalScroll):
    def __init__(self, schema: CommandSchema, **kwargs) -> None:
        super().__init__(**kwargs)
        self._schema = schema
        self._widget_map: dict[str, str] = {}

    def compose(self) -> ComposeResult:
        yield Static(f"[b]{self._schema.name}[/b]", markup=True)

        if self._schema.arguments:
            yield Label("Arguments")
            for arg in self._schema.arguments:
                widget_id = f"arg-{arg.name}"
                self._widget_map[arg.name] = widget_id
                yield Label(f"  {arg.name}" + (" (required)" if arg.required else ""))
                yield Input(
                    placeholder=arg.name,
                    value=_default_str(arg.default),
                    id=widget_id,
                )

        if self._schema.options:
            yield Label("Options")
            for opt in self._schema.options:
                widget_id = f"opt-{opt.name}"
                self._widget_map[opt.name] = widget_id
                if opt.is_flag:
                    yield Checkbox(
                        " ".join(opt.opts),
                        value=bool(opt.default),
                        id=widget_id,
                    )
                elif opt.choices:
                    yield Label(f"  {' '.join(opt.opts)}")
                    options = [(c, c) for c in opt.choices]
                    default = opt.default
                    if default is None or _default_str(default) == "" or default not in opt.choices:
                        default = Select.NULL
                    yield Select(
                        options,
                        value=default,
                        allow_blank=True,
                        id=widget_id,
                    )
                else:
                    yield Label(f"  {' '.join(opt.opts)}")
                    yield Input(
                        placeholder=opt.name,
                        value=_default_str(opt.default),
                        id=widget_id,
                    )

    def get_values(self) -> dict[str, Any]:
        values: dict[str, Any] = {}
        for param_name, widget_id in self._widget_map.items():
            try:
                widget = self.query_one(f"#{widget_id}")
            except Exception:
                continue
            match widget:
                case Input() | Checkbox() | Select():
                    values[param_name] = widget.value
        return values

    def set_values(self, values: dict[str, Any]) -> None:
        for param_name, val in values.items():
            widget_id = self._widget_map.get(param_name)
            if not widget_id:
                continue
            try:
                widget = self.query_one(f"#{widget_id}")
            except Exception:
                continue
            match widget:
                case Input():
                    widget.value = str(val) if val else ""
                case Checkbox():
                    widget.value = bool(val)
                case Select():
                    widget.value = val

    def focus_param(self, name: str) -> None:
        widget_id = self._widget_map.get(name)
        if not widget_id:
            return
        try:
            widget = self.query_one(f"#{widget_id}")
        except Exception:
            return
        widget.scroll_visible()
        widget.focus()
