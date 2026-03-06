from __future__ import annotations

import pytest
from textual.app import App, ComposeResult

from baalbek.widgets.search_bar import SearchBar


class SearchBarApp(App):
    def compose(self) -> ComposeResult:
        yield SearchBar()


@pytest.mark.asyncio
async def test_search_bar_hidden_by_default():
    async with SearchBarApp().run_test() as pilot:
        bar = pilot.app.query_one(SearchBar)
        assert bar.display is False


@pytest.mark.asyncio
async def test_search_bar_shows_query():
    async with SearchBarApp().run_test() as pilot:
        bar = pilot.app.query_one(SearchBar)
        bar.query_text = "deploy"
        bar.show()
        await pilot.pause()
        assert "deploy" in bar.render_text
