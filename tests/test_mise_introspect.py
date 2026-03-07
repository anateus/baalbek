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


class TestSplitTasksByDelimiter:
    def _make_task(self, name, description="", usage="", source="/project/mise.toml"):
        return {
            "name": name,
            "description": description,
            "usage": usage,
            "source": source,
        }

    def test_single_task_no_delimiter(self):
        from baalbek.mise_introspect import _split_tasks_by_delimiter

        tasks = [self._make_task("build", "Build project")]
        tree = _split_tasks_by_delimiter(tasks, ":")
        assert "build" in tree
        assert tree["build"].name == "build"
        assert tree["build"].docstring == "Build project"
        assert tree["build"].is_group is False
        assert tree["build"].run_name == "build"

    def test_nested_task_creates_groups(self):
        from baalbek.mise_introspect import _split_tasks_by_delimiter

        tasks = [self._make_task("apply:infra:prod", "Deploy to prod")]
        tree = _split_tasks_by_delimiter(tasks, ":")
        assert "apply" in tree
        assert tree["apply"].is_group is True
        assert tree["apply"].run_name is None
        assert "infra" in tree["apply"].subcommands
        assert tree["apply"].subcommands["infra"].is_group is True
        prod = tree["apply"].subcommands["infra"].subcommands["prod"]
        assert prod.name == "prod"
        assert prod.run_name == "apply:infra:prod"
        assert prod.is_group is False

    def test_sibling_tasks_share_group(self):
        from baalbek.mise_introspect import _split_tasks_by_delimiter

        tasks = [
            self._make_task("deploy:server"),
            self._make_task("deploy:client"),
        ]
        tree = _split_tasks_by_delimiter(tasks, ":")
        assert "deploy" in tree
        assert tree["deploy"].is_group is True
        assert "server" in tree["deploy"].subcommands
        assert "client" in tree["deploy"].subcommands

    def test_parent_links_set(self):
        from baalbek.mise_introspect import _split_tasks_by_delimiter

        tasks = [self._make_task("a:b:c")]
        tree = _split_tasks_by_delimiter(tasks, ":")
        c = tree["a"].subcommands["b"].subcommands["c"]
        assert c.parent is not None
        assert c.parent.name == "b"
        assert c.parent.parent is not None
        assert c.parent.parent.name == "a"

    def test_task_without_usage_gets_default_arguments(self):
        from baalbek.mise_introspect import _split_tasks_by_delimiter

        tasks = [self._make_task("test")]
        tree = _split_tasks_by_delimiter(tasks, ":")
        assert len(tree["test"].arguments) == 1
        assert tree["test"].arguments[0].name == "arguments"

    def test_custom_delimiter(self):
        from baalbek.mise_introspect import _split_tasks_by_delimiter

        tasks = [self._make_task("deploy/server/prod")]
        tree = _split_tasks_by_delimiter(tasks, "/")
        assert "deploy" in tree
        assert "server" in tree["deploy"].subcommands
        assert "prod" in tree["deploy"].subcommands["server"].subcommands
        assert tree["deploy"].subcommands["server"].subcommands["prod"].run_name == "deploy/server/prod"

    def test_task_name_conflicts_with_group_prefix(self):
        from baalbek.mise_introspect import _split_tasks_by_delimiter

        tasks = [
            self._make_task("deploy", "Direct deploy"),
            self._make_task("deploy:server", "Deploy server"),
        ]
        tree = _split_tasks_by_delimiter(tasks, ":")
        assert tree["deploy"].is_group is True
        assert "server" in tree["deploy"].subcommands
        assert tree["deploy"].run_name == "deploy"
        assert tree["deploy"].docstring == "Direct deploy"
