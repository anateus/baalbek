from __future__ import annotations

import click
import pytest

from baalbek.introspect import introspect_click_app


@click.group()
@click.option("--verbose", is_flag=True)
def sample_cli(verbose):
    pass


@sample_cli.group()
@click.option("--env", type=click.Choice(["dev", "prod"]))
def deploy(env):
    pass


@deploy.command()
@click.argument("name")
@click.option("--replicas", type=int, default=1)
def service(name, replicas):
    pass


@sample_cli.command()
@click.option("--tail", type=int, default=100)
def logs(tail):
    pass


@pytest.fixture
def schema():
    return introspect_click_app(sample_cli)


def test_introspect_returns_root_commands(schema):
    assert "deploy" in schema
    assert "logs" in schema


def test_introspect_root_is_group(schema):
    assert schema["deploy"].is_group is True
    assert schema["logs"].is_group is False


def test_introspect_subcommands(schema):
    assert "service" in schema["deploy"].subcommands


def test_introspect_options(schema):
    service_schema = schema["deploy"].subcommands["service"]
    option_names = [o.name for o in service_schema.options]
    assert "replicas" in option_names


def test_introspect_arguments(schema):
    service_schema = schema["deploy"].subcommands["service"]
    arg_names = [a.name for a in service_schema.arguments]
    assert "name" in arg_names


def test_introspect_choices(schema):
    deploy_schema = schema["deploy"]
    env_opt = next(o for o in deploy_schema.options if o.name == "env")
    assert env_opt.choices == ("dev", "prod")


def test_introspect_group_options(schema):
    assert schema["deploy"].has_own_params is True


def test_introspect_parent_links(schema):
    service_schema = schema["deploy"].subcommands["service"]
    assert service_schema.parent is not None
    assert service_schema.parent.name == "deploy"
