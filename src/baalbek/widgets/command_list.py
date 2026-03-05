from __future__ import annotations

from textual import on
from textual.message import Message
from textual.widgets import OptionList
from textual.widgets.option_list import Option

from baalbek.schemas import CommandSchema


class CommandList(OptionList):
    can_focus = False

    class Selected(Message):
        def __init__(self, schema: CommandSchema, command_list: CommandList) -> None:
            super().__init__()
            self.schema = schema
            self.command_list = command_list

    def __init__(self, commands: dict[str, CommandSchema], **kwargs) -> None:
        self._commands = commands
        self._schemas: list[CommandSchema] = []
        options: list[Option] = []
        for name in sorted(commands):
            schema = commands[name]
            self._schemas.append(schema)
            label = f"{name} \u25b8" if schema.is_group else name
            options.append(Option(label, id=name))
        super().__init__(*options, **kwargs)

    @property
    def selected_schema(self) -> CommandSchema | None:
        idx = self.highlighted
        if idx is not None and 0 <= idx < len(self._schemas):
            return self._schemas[idx]
        return None

    def get_labels(self) -> list[str]:
        return [f"{s.name} \u25b8" if s.is_group else s.name for s in self._schemas]

    def resort(self, order: list[str]) -> None:
        current = self.selected_schema
        current_name = current.name if current else None

        ordered_names = [n for n in order if n in self._commands]
        remaining = sorted(n for n in self._commands if n not in ordered_names)
        all_names = ordered_names + remaining

        self._schemas = [self._commands[n] for n in all_names]
        self.clear_options()
        options = []
        for name in all_names:
            schema = self._commands[name]
            label = f"{name} \u25b8" if schema.is_group else name
            options.append(Option(label, id=name))
        self.add_options(options)

        if current_name:
            for idx, schema in enumerate(self._schemas):
                if schema.name == current_name:
                    self.highlighted = idx
                    break

    @on(OptionList.OptionHighlighted)
    def _on_highlight(self, event: OptionList.OptionHighlighted) -> None:
        if self.has_class("preview"):
            return
        schema = self.selected_schema
        if schema:
            self.post_message(self.Selected(schema, self))
