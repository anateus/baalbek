from __future__ import annotations

import pytest
from textual.app import App, ComposeResult
from textual.widgets import Checkbox, Input, Select

from baalbek.schemas import ArgumentSchema, CommandSchema, OptionSchema
from baalbek.widgets.option_form import OptionForm


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
                name="env",
                type="CHOICE",
                default=None,
                required=False,
                is_flag=False,
                is_boolean_flag=False,
                flag_value=None,
                opts=["--env", "-e"],
                secondary_opts=[],
                help="Target environment",
                choices=["dev", "staging", "prod"],
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


class OptionFormApp(App):
    def __init__(self, schema: CommandSchema) -> None:
        super().__init__()
        self._schema = schema

    def compose(self) -> ComposeResult:
        yield OptionForm(self._schema)


@pytest.mark.asyncio
async def test_form_renders():
    app = OptionFormApp(_sample_schema())
    async with app.run_test() as pilot:
        form = pilot.app.query_one(OptionForm)
        assert form is not None


@pytest.mark.asyncio
async def test_form_has_inputs():
    app = OptionFormApp(_sample_schema())
    async with app.run_test() as pilot:
        inputs = pilot.app.query(Input)
        assert len(inputs) >= 1


@pytest.mark.asyncio
async def test_form_get_values():
    app = OptionFormApp(_sample_schema())
    async with app.run_test() as pilot:
        form = pilot.app.query_one(OptionForm)
        values = form.get_values()
        assert "name" in values
        assert "replicas" in values
        assert "env" in values
        assert "verbose" in values
