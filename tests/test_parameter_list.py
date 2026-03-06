from __future__ import annotations

from pathlib import Path

import pytest
from textual.app import App, ComposeResult

from baalbek.db import HistoryDB
from baalbek.schemas import ArgumentSchema, CommandSchema, OptionSchema
from baalbek.widgets.parameter_list import ParameterList


def _sample_schema() -> CommandSchema:
    return CommandSchema(
        name="deploy",
        docstring="Deploy a service",
        arguments=[
            ArgumentSchema(
                name="name",
                type="STRING",
                required=True,
                default=None,
                choices=None,
                multiple=False,
                nargs=1,
            ),
        ],
        options=[
            OptionSchema(
                name="replicas",
                type="INT",
                default=1,
                required=False,
                is_flag=False,
                is_boolean_flag=False,
                flag_value=None,
                opts=["--replicas", "-r"],
                secondary_opts=[],
                help="Number of replicas",
                choices=None,
                multiple=False,
                nargs=1,
                counting=False,
            ),
            OptionSchema(
                name="verbose",
                type="BOOL",
                default=False,
                required=False,
                is_flag=True,
                is_boolean_flag=True,
                flag_value=True,
                opts=["--verbose", "-v"],
                secondary_opts=[],
                help="Enable verbose output",
                choices=None,
                multiple=False,
                nargs=0,
                counting=False,
            ),
        ],
    )


class ParameterListApp(App):
    def __init__(self, schema: CommandSchema, db_path: Path | None = None, preview: bool = False) -> None:
        super().__init__()
        self._schema = schema
        if db_path is not None:
            self._db_path = db_path
        self._preview = preview

    def compose(self) -> ComposeResult:
        pl = ParameterList(self._schema)
        if self._preview:
            pl.add_class("preview")
        yield pl


@pytest.mark.asyncio
async def test_renders_params():
    app = ParameterListApp(_sample_schema())
    async with app.run_test() as pilot:
        pl = pilot.app.query_one(ParameterList)
        assert pl.option_count == 3


@pytest.mark.asyncio
async def test_get_values_empty_initially():
    app = ParameterListApp(_sample_schema())
    async with app.run_test() as pilot:
        pl = pilot.app.query_one(ParameterList)
        values = pl.get_values()
        assert values == {}


@pytest.mark.asyncio
async def test_highlighted_param_name():
    app = ParameterListApp(_sample_schema())
    async with app.run_test() as pilot:
        pl = pilot.app.query_one(ParameterList)
        assert pl.highlighted_param_name == "name"


@pytest.mark.asyncio
async def test_modal_updates_values():
    app = ParameterListApp(_sample_schema())
    async with app.run_test() as pilot:
        pl = pilot.app.query_one(ParameterList)
        pl._on_modal_done({"name": "myapp", "replicas": "3", "verbose": True})
        assert pl.get_values() == {"name": "myapp", "replicas": "3", "verbose": True}
        assert pl.option_count == 3


@pytest.mark.asyncio
async def test_loads_saved_draft_on_mount(tmp_path: Path):
    db_path = tmp_path / "history.db"
    db = HistoryDB(db_path)
    db.save_draft("deploy", {"name": "saved-app", "replicas": "5"})
    db.close()
    app = ParameterListApp(_sample_schema(), db_path=db_path)
    async with app.run_test() as pilot:
        pl = pilot.app.query_one(ParameterList)
        assert pl.get_values() == {"name": "saved-app", "replicas": "5"}


@pytest.mark.asyncio
async def test_saves_draft_on_modal_done(tmp_path: Path):
    db_path = tmp_path / "history.db"
    app = ParameterListApp(_sample_schema(), db_path=db_path)
    async with app.run_test() as pilot:
        pl = pilot.app.query_one(ParameterList)
        pl._on_modal_done({"name": "myapp", "replicas": "3"})
    db = HistoryDB(db_path)
    result = db.load_draft("deploy")
    db.close()
    assert result == {"name": "myapp", "replicas": "3"}


@pytest.mark.asyncio
async def test_preview_loads_draft_for_display(tmp_path: Path):
    db_path = tmp_path / "history.db"
    db = HistoryDB(db_path)
    db.save_draft("deploy", {"name": "saved-value"})
    db.close()
    app = ParameterListApp(_sample_schema(), db_path=db_path, preview=True)
    async with app.run_test() as pilot:
        pl = pilot.app.query_one(ParameterList)
        assert pl.get_values() == {"name": "saved-value"}


@pytest.mark.asyncio
async def test_reset_clears_values_and_draft(tmp_path: Path):
    db_path = tmp_path / "history.db"
    db = HistoryDB(db_path)
    db.save_draft("deploy", {"name": "myapp"})
    db.close()
    app = ParameterListApp(_sample_schema(), db_path=db_path)
    async with app.run_test() as pilot:
        pl = pilot.app.query_one(ParameterList)
        assert pl.get_values() == {"name": "myapp"}
        pl.reset_to_defaults()
        assert pl.get_values() == {}
    db = HistoryDB(db_path)
    assert db.load_draft("deploy") is None
    db.close()
