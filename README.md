# Baalbek

A Miller column TUI explorer for [Click](https://click.palletsprojects.com/) CLI apps and [mise](https://mise.jdx.dev/) tasks, built with [Textual](https://textual.textualize.io/).

Navigate your CLI's command tree with vim-style keybindings, preview subcommands and options in real time, and build up commands interactively.

![Screenshot](screenshot.svg)

## Install

Add to your `pyproject.toml` dependencies:

```toml
"baalbek @ git+https://github.com/anateus/baalbek"
```

PyPI publishing coming soon.

## Usage

### Click apps

```python
import click
from baalbek import tui

@tui()
@click.group()
def cli():
    pass

# ... define your commands ...

if __name__ == "__main__":
    cli()
```

Then run `cli tui` to launch the interactive explorer.

### Mise tasks

Baalbek can also explore and run [mise](https://mise.jdx.dev/) tasks. Install baalbek and run:

```bash
baalbek-mise
```

This introspects your project's mise tasks (via `mise tasks --all -x -J`) and presents them in the same Miller column interface. Tasks are organized into a hierarchy by splitting on a configurable delimiter (`:` by default). For example, tasks named `deploy:infra:prod` and `deploy:infra:staging` appear as a navigable tree:

```
deploy → infra → prod
               → staging
```

If tasks come from multiple source directories, they are additionally grouped by directory.

Tasks with [usage](https://usage.jdx.dev/) specs get fully parsed flags and arguments in the parameter form. Tasks without usage specs get a generic free-text arguments field.

Press `Ctrl+T` to change the delimiter at any time — the task tree rebuilds instantly.

## Keybindings

| Key | Action |
|-----|--------|
| `h` / `←` | Move focus left |
| `l` / `→` / `Enter` | Move focus right / select |
| `j` / `↓` | Move cursor down |
| `k` / `↑` | Move cursor up |
| `s` / `S` | Cycle sort mode / reverse sort |
| `/` | Fuzzy search within focused column |
| `Ctrl+R` | Run command |
| `Ctrl+H` | Toggle history |
| `Ctrl+D` | Reset parameters to defaults |
| `Ctrl+T` | Change task name delimiter (mise mode) |
| `Tab` / `Shift+Tab` | Move focus right / left |
| `q` | Quit |

## Acknowledgements

Inspired by [Trogon](https://github.com/Textualize/trogon), Textualize's TUI for Click apps.

## Name

Named after [Baalbek](https://en.wikipedia.org/wiki/Baalbek) — the ancient ruins in Lebanon with famously impressive columns.
