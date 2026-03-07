from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Sequence


@dataclass
class OptionSchema:
    name: str
    type: str
    default: Any
    required: bool
    is_flag: bool
    is_boolean_flag: bool
    flag_value: Any
    opts: list[str]
    secondary_opts: list[str]
    help: str | None
    choices: Sequence[str] | None
    multiple: bool
    nargs: int
    counting: bool


@dataclass
class ArgumentSchema:
    name: str
    type: str
    required: bool
    default: Any
    choices: Sequence[str] | None
    multiple: bool
    nargs: int


@dataclass
class CommandSchema:
    name: str
    docstring: str | None
    options: list[OptionSchema]
    arguments: list[ArgumentSchema]
    subcommands: dict[str, CommandSchema] = field(default_factory=dict)
    parent: CommandSchema | None = None
    is_group: bool = False
    run_name: str | None = None

    @property
    def path_from_root(self) -> list[CommandSchema]:
        path = []
        current: CommandSchema | None = self
        while current is not None:
            path.append(current)
            current = current.parent
        path.reverse()
        return path

    @property
    def has_own_params(self) -> bool:
        return len(self.options) > 0 or len(self.arguments) > 0
