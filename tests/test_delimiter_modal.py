from __future__ import annotations

import pytest
from textual.app import App

from baalbek.screens.delimiter_modal import DelimiterModal


class ModalApp(App):
    def __init__(self):
        super().__init__()
        self.result = None

    def on_mount(self) -> None:
        self.push_screen(DelimiterModal(current=":"), callback=self._on_result)

    def _on_result(self, value: str | None) -> None:
        self.result = value


@pytest.mark.asyncio
async def test_delimiter_modal_shows_current():
    async with ModalApp().run_test() as pilot:
        await pilot.pause()
        screen = pilot.app.screen
        assert isinstance(screen, DelimiterModal)


@pytest.mark.asyncio
async def test_delimiter_modal_escape_dismisses():
    async with ModalApp().run_test() as pilot:
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()
        assert pilot.app.result is None


@pytest.mark.asyncio
async def test_delimiter_modal_submit():
    async with ModalApp().run_test() as pilot:
        await pilot.pause()
        input_widget = pilot.app.screen.query_one("#delimiter-input")
        input_widget.value = "/"
        await pilot.press("enter")
        await pilot.pause()
        assert pilot.app.result == "/"
