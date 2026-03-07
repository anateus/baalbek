from __future__ import annotations

import shlex

from baalbek.schemas import CommandSchema
from baalbek.screens.commander import CommanderScreen
from baalbek.widgets.miller import MillerColumns
from baalbek.widgets.parameter_list import ParameterList
from baalbek.widgets.run_panel import RunPanel


def _split_generic_args(value: str) -> list[str]:
    if not value or not value.strip():
        return []
    try:
        return shlex.split(value)
    except ValueError:
        return value.split()


class MiseCommanderScreen(CommanderScreen):
    def __init__(
        self,
        commands: dict[str, CommandSchema],
        app_name: str | None = None,
        app_description: str | None = None,
        delimiter: str = ":",
        raw_tasks: list[dict] | None = None,
        **kwargs,
    ) -> None:
        super().__init__(commands, app_name=app_name, app_description=app_description, **kwargs)
        self._delimiter = delimiter
        self._raw_tasks = raw_tasks or []

    def build_command_args(self) -> list[str]:
        mc = self.query_one(MillerColumns)
        run_name = None
        param_args: list[str] = []

        for col in mc._committed:
            match col:
                case RunPanel():
                    schema = col.parameter_list._schema
                    if schema.run_name:
                        run_name = schema.run_name
                    values = col.parameter_list.get_values()
                    self._append_mise_args(param_args, schema, values)
                case ParameterList():
                    schema = col._schema
                    if schema.run_name:
                        run_name = schema.run_name
                    values = col.get_values()
                    self._append_mise_args(param_args, schema, values)

        if not run_name:
            return []

        return ["mise", "run", run_name] + param_args

    def _append_mise_args(
        self,
        args: list[str],
        schema: CommandSchema,
        values: dict,
    ) -> None:
        for opt in schema.options:
            val = values.get(opt.name)
            if val is None:
                continue
            if opt.is_flag:
                if val and val != opt.default:
                    args.append(opt.opts[0])
            elif val != "" and str(val) != str(opt.default):
                args.extend([opt.opts[0], str(val)])

        for arg_schema in schema.arguments:
            val = values.get(arg_schema.name)
            if not val or val == "":
                continue
            if arg_schema.name == "arguments":
                args.extend(_split_generic_args(str(val)))
            else:
                args.append(str(val))
