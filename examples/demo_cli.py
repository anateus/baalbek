import click
from baalbek import tui


@tui()
@click.group()
@click.option("--verbose", "-v", is_flag=True)
def cli(verbose):
    pass


# --- deploy group (existing) ---

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


# --- data group (deeply nested: cli → data → candidates → ...) ---

@cli.group()
def data():
    pass


@data.group()
def candidates():
    pass


@candidates.command("import")
@click.argument("file", type=click.Path(exists=False))
@click.option("--batch-size", type=click.IntRange(1, 10000), default=500)
@click.option("--dry-run", is_flag=True)
def candidates_import(file, batch_size, dry_run):
    click.echo(f"Importing {file} batch_size={batch_size} dry_run={dry_run}")


@candidates.command()
@click.option("--source", type=click.Choice(["twitter", "mastodon", "bluesky"]), required=True)
@click.option("--base-delay", type=click.FloatRange(0.1, 30.0), default=1.0)
@click.option("--page", type=click.IntRange(1), default=1)
@click.option("--page-size", type=click.IntRange(1, 100), default=25)
def scrape(source, base_delay, page, page_size):
    click.echo(f"Scraping {source} delay={base_delay} page={page} size={page_size}")


@candidates.command("list")
@click.option("--tag", "-t", multiple=True)
@click.option("--status", type=click.Choice(["pending", "approved", "rejected"]), default="pending")
@click.option("--page", type=click.IntRange(1), default=1)
@click.option("--page-size", type=click.IntRange(1, 100), default=25)
def candidates_list(tag, status, page, page_size):
    click.echo(f"Listing candidates tags={tag} status={status} page={page} size={page_size}")


@candidates.command()
@click.argument("candidate_id")
@click.option("--reason", type=str, default="")
def approve(candidate_id, reason):
    click.echo(f"Approved {candidate_id} reason={reason}")


# --- simulation group (7 subcommands) ---

@cli.group()
def simulation():
    pass


@simulation.command()
@click.option("--name", required=True)
@click.option("--orchestrator-id", required=True, type=int)
@click.option("--agent-id", "-a", multiple=True, type=int)
@click.option("--removal-rate", type=click.FloatRange(0.0, 1.0), default=0.5)
@click.option("--rounds", type=click.IntRange(1, 10000), default=100)
@click.option("--seed", type=int, default=None)
@click.option("--dry-run", is_flag=True)
def create(name, orchestrator_id, agent_id, removal_rate, rounds, seed, dry_run):
    click.echo(
        f"Creating simulation '{name}' orchestrator={orchestrator_id} "
        f"agents={agent_id} removal_rate={removal_rate} rounds={rounds} "
        f"seed={seed} dry_run={dry_run}"
    )


@simulation.command("list")
@click.option("--status", type=click.Choice(["pending", "running", "paused", "completed", "cancelled"]))
@click.option("--limit", type=click.IntRange(1, 1000), default=20)
def simulation_list(status, limit):
    click.echo(f"Listing simulations status={status} limit={limit}")


@simulation.command("status")
@click.argument("simulation_id", type=int)
@click.option("--json", "as_json", is_flag=True)
def simulation_status(simulation_id, as_json):
    click.echo(f"Status of simulation {simulation_id} json={as_json}")


@simulation.command()
@click.argument("simulation_id", type=int)
@click.option("--force", is_flag=True)
def launch(simulation_id, force):
    click.echo(f"Launching simulation {simulation_id} force={force}")


@simulation.command()
@click.argument("simulation_id", type=int)
def pause(simulation_id):
    click.echo(f"Pausing simulation {simulation_id}")


@simulation.command()
@click.argument("simulation_id", type=int)
def resume(simulation_id):
    click.echo(f"Resuming simulation {simulation_id}")


@simulation.command()
@click.argument("simulation_id", type=int)
@click.option("--force", is_flag=True)
def cancel(simulation_id, force):
    click.echo(f"Cancelling simulation {simulation_id} force={force}")


if __name__ == "__main__":
    cli()
