import click
from baalbek import tui


@tui()
@click.group()
@click.option("--verbose", "-v", is_flag=True)
def cli(verbose):
    pass


@cli.group()
@click.option("--env", type=click.Choice(["dev", "staging", "prod"]), default="dev")
def deploy(env):
    pass


@deploy.command()
@click.argument("name")
@click.option("--replicas", type=int, default=1)
@click.option("--region", type=click.Choice(["us-east-1", "eu-west-1"]), default="us-east-1")
def service(name, replicas, region):
    click.echo(f"Deploying {name} with {replicas} replicas in {region}")


@deploy.command()
@click.argument("image")
def container(image):
    click.echo(f"Deploying container: {image}")


@cli.command()
@click.option("--tail", type=int, default=100)
@click.option("--follow", "-f", is_flag=True)
def logs(tail, follow):
    for i in range(min(tail, 5)):
        click.echo(f"[2026-03-04 10:00:{i:02d}] Log line {i}")


@cli.command()
def status():
    click.secho("All systems operational", fg="green")


if __name__ == "__main__":
    cli()
