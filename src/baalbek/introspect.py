from __future__ import annotations

import click

from baalbek.schemas import ArgumentSchema, CommandSchema, OptionSchema


def _extract_option(param: click.Option) -> OptionSchema:
    match param.type:
        case click.Choice():
            choices = param.type.choices
        case _:
            choices = None

    return OptionSchema(
        name=param.name or "",
        type=param.type.name.upper(),
        default=param.default,
        required=param.required,
        is_flag=param.is_flag,
        is_boolean_flag=getattr(param, "is_bool_flag", param.is_flag and param.secondary_opts != []),
        flag_value=param.flag_value if param.is_flag else None,
        opts=list(param.opts),
        secondary_opts=list(param.secondary_opts),
        help=param.help,
        choices=choices,
        multiple=param.multiple,
        nargs=param.nargs,
        counting=param.count,
    )


def _extract_argument(param: click.Argument) -> ArgumentSchema:
    match param.type:
        case click.Choice():
            choices = param.type.choices
        case _:
            choices = None

    return ArgumentSchema(
        name=param.name or "",
        type=param.type.name.upper(),
        required=param.required,
        default=param.default,
        choices=choices,
        multiple=param.multiple,
        nargs=param.nargs,
    )


def _introspect_command(
    cmd: click.BaseCommand,
    parent: CommandSchema | None = None,
    include_group_options: bool = True,
    exclude_names: set[str] | None = None,
) -> CommandSchema:
    options: list[OptionSchema] = []
    arguments: list[ArgumentSchema] = []

    for param in cmd.params:
        match param:
            case click.Option() if param.name == "help":
                continue
            case click.Option():
                options.append(_extract_option(param))
            case click.Argument():
                arguments.append(_extract_argument(param))

    schema = CommandSchema(
        name=cmd.name or "",
        docstring=cmd.help,
        options=options,
        arguments=arguments,
        is_group=isinstance(cmd, click.Group),
        parent=parent,
    )

    match cmd:
        case click.Group():
            for sub_name in cmd.list_commands(click.Context(cmd, info_name=cmd.name)):
                if exclude_names and sub_name in exclude_names:
                    continue
                subcmd = cmd.get_command(click.Context(cmd, info_name=cmd.name), sub_name)
                if subcmd is None:
                    continue
                schema.subcommands[sub_name] = _introspect_command(
                    subcmd,
                    parent=schema,
                    include_group_options=include_group_options,
                    exclude_names=exclude_names,
                )

    return schema


def introspect_click_app(
    app: click.BaseCommand,
    include_group_options: bool = True,
    exclude_names: set[str] | None = None,
) -> dict[str, CommandSchema]:
    match app:
        case click.Group():
            result: dict[str, CommandSchema] = {}
            ctx = click.Context(app, info_name=app.name)
            for sub_name in app.list_commands(ctx):
                if exclude_names and sub_name in exclude_names:
                    continue
                subcmd = app.get_command(ctx, sub_name)
                if subcmd is None:
                    continue
                result[sub_name] = _introspect_command(
                    subcmd,
                    include_group_options=include_group_options,
                    exclude_names=exclude_names,
                )
            return result
        case _:
            schema = _introspect_command(
                app,
                include_group_options=include_group_options,
                exclude_names=exclude_names,
            )
            return {schema.name: schema}
