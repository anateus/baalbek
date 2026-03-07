from __future__ import annotations

import json
import subprocess

from baalbek.schemas import ArgumentSchema, CommandSchema, OptionSchema


def _default_arguments() -> list[ArgumentSchema]:
    return [
        ArgumentSchema(
            name="arguments",
            type="STRING",
            required=False,
            default=None,
            choices=None,
            multiple=False,
            nargs=1,
        )
    ]


def parse_usage_spec(
    spec: str,
) -> tuple[list[OptionSchema], list[ArgumentSchema]]:
    if not spec.strip():
        return [], _default_arguments()

    try:
        result = subprocess.run(
            ["usage", "generate", "json", "--spec", spec],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return [], _default_arguments()

    if result.returncode != 0:
        return [], _default_arguments()

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return [], _default_arguments()

    cmd = data.get("cmd", {})

    options: list[OptionSchema] = []
    for flag in cmd.get("flags", []):
        has_arg = "arg" in flag
        long_opts = [f"--{l}" for l in flag.get("long", [])]
        short_opts = [f"-{s}" for s in flag.get("short", [])]
        all_opts = short_opts + long_opts

        options.append(
            OptionSchema(
                name=flag["name"],
                type="STRING" if has_arg else "BOOL",
                default=None,
                required=False,
                is_flag=not has_arg,
                is_boolean_flag=not has_arg,
                flag_value=True if not has_arg else None,
                opts=all_opts[:1] if all_opts else [],
                secondary_opts=all_opts[1:] if len(all_opts) > 1 else [],
                help=flag.get("help"),
                choices=None,
                multiple=False,
                nargs=1,
                counting=False,
            )
        )

    arguments: list[ArgumentSchema] = []
    for arg in cmd.get("args", []):
        default_val = arg["default"][0] if arg.get("default") else None
        arguments.append(
            ArgumentSchema(
                name=arg["name"],
                type="STRING",
                required=arg.get("required", False),
                default=default_val,
                choices=None,
                multiple=False,
                nargs=1,
            )
        )

    return options, arguments


def _parse_task_params(
    task: dict,
) -> tuple[list[OptionSchema], list[ArgumentSchema]]:
    usage_spec = task.get("usage", "").strip()
    if usage_spec:
        return parse_usage_spec(usage_spec)
    return [], _default_arguments()


def _set_parents(
    commands: dict[str, CommandSchema],
    parent: CommandSchema | None = None,
) -> None:
    for schema in commands.values():
        schema.parent = parent
        if schema.subcommands:
            _set_parents(schema.subcommands, schema)


def _split_tasks_by_delimiter(
    tasks: list[dict],
    delimiter: str,
) -> dict[str, CommandSchema]:
    root: dict[str, CommandSchema] = {}

    for task in tasks:
        parts = task["name"].split(delimiter) if delimiter else [task["name"]]
        current = root

        for part in parts[:-1]:
            if part not in current:
                current[part] = CommandSchema(
                    name=part,
                    docstring=None,
                    options=[],
                    arguments=[],
                    subcommands={},
                    is_group=True,
                )
            elif not current[part].is_group:
                current[part].is_group = True
                if not current[part].subcommands:
                    current[part].subcommands = {}
            current = current[part].subcommands

        leaf_name = parts[-1]
        options, arguments = _parse_task_params(task)

        if leaf_name in current and current[leaf_name].is_group:
            current[leaf_name].docstring = task.get("description") or current[leaf_name].docstring
            current[leaf_name].options = options
            current[leaf_name].arguments = arguments
            current[leaf_name].run_name = task["name"]
        else:
            current[leaf_name] = CommandSchema(
                name=leaf_name,
                docstring=task.get("description") or None,
                options=options,
                arguments=arguments,
                run_name=task["name"],
            )

    _set_parents(root)
    return root
