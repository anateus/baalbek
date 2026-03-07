from __future__ import annotations

from unittest.mock import patch


class TestParseUsageSpec:
    def test_parse_flags_and_args(self):
        from baalbek.mise_introspect import parse_usage_spec

        spec = (
            'flag "-v --version <version>" help="Version tag"\n'
            'flag "--no-cache" help="Build without cache"\n'
            'arg "message" help="Migration message" default="auto"'
        )
        options, arguments = parse_usage_spec(spec)

        assert len(options) == 2

        version_opt = next(o for o in options if o.name == "version")
        assert version_opt.is_flag is False
        assert version_opt.help == "Version tag"
        assert any(
            "--version" in opt or "-v" in opt
            for opt in version_opt.opts + version_opt.secondary_opts
        )

        cache_opt = next(o for o in options if o.name == "no-cache")
        assert cache_opt.is_flag is True
        assert cache_opt.help == "Build without cache"

        assert len(arguments) == 1
        assert arguments[0].name == "message"
        assert arguments[0].default == "auto"

    def test_parse_empty_spec_returns_default_arguments(self):
        from baalbek.mise_introspect import parse_usage_spec

        options, arguments = parse_usage_spec("")
        assert options == []
        assert len(arguments) == 1
        assert arguments[0].name == "arguments"

    def test_parse_invalid_spec_returns_default_arguments(self):
        from baalbek.mise_introspect import parse_usage_spec

        options, arguments = parse_usage_spec("this is not valid {{{{")
        assert options == []
        assert len(arguments) == 1
        assert arguments[0].name == "arguments"

    def test_parse_when_usage_cli_missing(self):
        from baalbek.mise_introspect import parse_usage_spec

        with patch("subprocess.run", side_effect=FileNotFoundError):
            options, arguments = parse_usage_spec('flag "--test" help="Test"')
        assert options == []
        assert len(arguments) == 1
        assert arguments[0].name == "arguments"
