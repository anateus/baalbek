from __future__ import annotations

from enum import Enum, auto


class InputMode(Enum):
    NORMAL = auto()
    EDIT = auto()


_NAV_KEYS = {"h", "j", "k", "l"}


class ModeManager:
    def __init__(self) -> None:
        self._mode = InputMode.NORMAL

    @property
    def mode(self) -> InputMode:
        return self._mode

    def enter_edit(self) -> None:
        self._mode = InputMode.EDIT

    def exit_edit(self) -> None:
        self._mode = InputMode.NORMAL

    def is_navigation_key(self, key: str) -> bool:
        if self._mode != InputMode.NORMAL:
            return False
        return key in _NAV_KEYS
