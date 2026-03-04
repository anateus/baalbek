from __future__ import annotations

from baalbek.schemas import ArgumentSchema, CommandSchema, OptionSchema


def test_option_schema_creation() -> None:
    opt = OptionSchema(
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
        nargs=1,
        counting=False,
    )
    assert opt.name == "verbose"
    assert opt.type == "BOOL"
    assert opt.default is False
    assert opt.required is False
    assert opt.is_flag is True
    assert opt.is_boolean_flag is True
    assert opt.flag_value is True
    assert opt.opts == ["--verbose", "-v"]
    assert opt.secondary_opts == []
    assert opt.help == "Enable verbose output"
    assert opt.choices is None
    assert opt.multiple is False
    assert opt.nargs == 1
    assert opt.counting is False


def test_argument_schema_creation() -> None:
    arg = ArgumentSchema(
        name="filename",
        type="STRING",
        required=True,
        default=None,
        choices=None,
        multiple=False,
        nargs=1,
    )
    assert arg.name == "filename"
    assert arg.type == "STRING"
    assert arg.required is True
    assert arg.default is None
    assert arg.choices is None
    assert arg.multiple is False
    assert arg.nargs == 1


def test_command_schema_creation() -> None:
    cmd = CommandSchema(
        name="cli",
        docstring="Top-level group",
        options=[],
        arguments=[],
        is_group=True,
    )
    assert cmd.name == "cli"
    assert cmd.docstring == "Top-level group"
    assert cmd.options == []
    assert cmd.arguments == []
    assert cmd.subcommands == {}
    assert cmd.parent is None
    assert cmd.is_group is True


def test_command_schema_path_from_root() -> None:
    root = CommandSchema(name="root", docstring=None, options=[], arguments=[], is_group=True)
    child = CommandSchema(name="child", docstring=None, options=[], arguments=[], parent=root, is_group=True)
    leaf = CommandSchema(name="leaf", docstring=None, options=[], arguments=[], parent=child)

    path = leaf.path_from_root
    assert path == [root, child, leaf]


def test_command_schema_has_own_params() -> None:
    opt = OptionSchema(
        name="flag",
        type="BOOL",
        default=False,
        required=False,
        is_flag=True,
        is_boolean_flag=True,
        flag_value=True,
        opts=["--flag"],
        secondary_opts=[],
        help=None,
        choices=None,
        multiple=False,
        nargs=1,
        counting=False,
    )
    with_params = CommandSchema(name="cmd", docstring=None, options=[opt], arguments=[])
    assert with_params.has_own_params is True

    without_params = CommandSchema(name="empty", docstring=None, options=[], arguments=[])
    assert without_params.has_own_params is False
