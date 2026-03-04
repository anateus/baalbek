from baalbek.runner import run_command


def test_run_simple_command():
    result = run_command(["echo", "hello world"])
    assert result.exit_code == 0
    assert b"hello world" in result.raw_output
    assert "hello world" in result.plain_output


def test_run_command_with_color():
    result = run_command(["printf", "\\033[31mred\\033[0m"])
    assert b"\x1b[31m" in result.raw_output
    assert "red" in result.plain_output
    assert "\x1b[" not in result.plain_output


def test_run_command_failure():
    result = run_command(["false"])
    assert result.exit_code != 0


def test_run_command_multiline():
    result = run_command(["printf", "line1\\nline2\\nline3"])
    assert "line1" in result.plain_output
    assert "line2" in result.plain_output
    assert "line3" in result.plain_output
