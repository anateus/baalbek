# Baalbek

A Miller column TUI explorer for [Click](https://click.palletsprojects.com/) CLI apps, built with [Textual](https://textual.textualize.io/).

Navigate your CLI's command tree with vim-style keybindings, preview subcommands and options in real time, and build up commands interactively.

## Install

Add to your `pyproject.toml` dependencies:

```toml
"baalbek @ git+https://github.com/anateus/baalbek"
```

PyPI publishing coming soon.

## Usage

```python
import click
from baalbek import explorer

@click.group()
def cli():
    pass

# ... define your commands ...

if __name__ == "__main__":
    explorer(cli)
```

## Keybindings

| Key | Action |
|-----|--------|
| `h` / `Left` | Move focus left |
| `l` / `Right` / `Enter` | Move focus right / select |
| `j` / `Down` | Move cursor down |
| `k` / `Up` | Move cursor up |
| `i` | Enter edit mode (edit field values) |
| `Escape` | Exit edit mode / quit |
| `Ctrl+R` | Run command |
| `Ctrl+H` | Toggle history |

## Acknowledgements

Inspired by [Trogon](https://github.com/Textualize/trogon), Textualize's TUI for Click apps.

## Name

Named after [Baalbek](https://en.wikipedia.org/wiki/Baalbek) — the ancient ruins in Lebanon with famously impressive columns.
