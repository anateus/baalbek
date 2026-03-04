from __future__ import annotations

from typing import Any

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Checkbox, Input, Label, Select, Static

from baalbek.schemas import CommandSchema


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
                    value=str(arg.default) if arg.default is not None else "",
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
                    yield Select(
                        options,
                        value=opt.default if opt.default is not None else Select.NULL,
                        allow_blank=True,
                        id=widget_id,
                    )
                else:
                    yield Label(f"  {' '.join(opt.opts)}")
                    yield Input(
                        placeholder=opt.name,
                        value=str(opt.default) if opt.default is not None else "",
                        id=widget_id,
                    )

    def get_values(self) -> dict[str, Any]:
        values: dict[str, Any] = {}
        for param_name, widget_id in self._widget_map.items():
            try:
                widget = self.query_one(f"#{widget_id}")
            except Exception:
                continue
            if isinstance(widget, Input):
                values[param_name] = widget.value
            elif isinstance(widget, Checkbox):
                values[param_name] = widget.value
            elif isinstance(widget, Select):
                values[param_name] = widget.value
        return values
