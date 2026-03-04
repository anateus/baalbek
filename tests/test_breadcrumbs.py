from __future__ import annotations

import pytest
from textual.app import App, ComposeResult

from baalbek.widgets.breadcrumbs import Breadcrumbs


class BreadcrumbsApp(App):
    def compose(self) -> ComposeResult:
        yield Breadcrumbs()


@pytest.mark.asyncio
async def test_initial_empty():
    async with BreadcrumbsApp().run_test() as pilot:
        bc = pilot.app.query_one(Breadcrumbs)
        assert bc.path == []


@pytest.mark.asyncio
async def test_set_path():
    async with BreadcrumbsApp().run_test() as pilot:
        bc = pilot.app.query_one(Breadcrumbs)
        bc.path = ["cli", "deploy", "service"]
        await pilot.pause()
        assert "cli" in bc.render_text
        assert "deploy" in bc.render_text
        assert "service" in bc.render_text


@pytest.mark.asyncio
async def test_separator():
    async with BreadcrumbsApp().run_test() as pilot:
        bc = pilot.app.query_one(Breadcrumbs)
        bc.path = ["a", "b"]
        await pilot.pause()
        assert "▸" in bc.render_text
