# Baalbek

Miller column TUI explorer for Click CLI apps and mise tasks, built with Textual. Named after the ruins with impressive columns.

## Quick Reference

- **Version:** check `pyproject.toml`
- **Python:** 3.11+
- **Build:** hatchling
- **Key deps:** Click (≥8.3.1), Textual (≥8.0.2), pyte (≥0.8.2)
- **Not on PyPI** — consumers install via `baalbek @ git+https://github.com/anateus/baalbek`

## Commands

```bash
uv run pytest           # run all tests (~102 tests)
uv run python -m build  # build package
```

## Architecture

```
src/baalbek/
├── app.py              # BaalbekApp, @tui decorator, app name heuristic
├── introspect.py       # Walks Click command tree → CommandSchema
├── runner.py           # PTY-based command execution with pyte output capture
├── schemas.py          # CommandSchema, OptionSchema, ArgumentSchema dataclasses
├── modes.py            # NORMAL / EDIT mode enum
├── db.py               # SQLite history (~/.local/share/baalbek/history.db)
├── baalbek.tcss        # Textual CSS
├── mise_app.py         # MiseBaalbek app, baalbek-mise CLI entry point
├── mise_introspect.py  # Parses mise tasks JSON → CommandSchema tree
├── screens/
│   ├── commander.py    # Main screen, keybindings, orchestration
│   ├── mise_commander.py # Mise-specific screen: mise run execution, delimiter change
│   ├── delimiter_modal.py # Modal for changing task name delimiter
│   └── output_zoom.py  # Fullscreen output viewer
└── widgets/
    ├── miller.py       # Core: committed columns + derived preview columns
    ├── command_list.py # OptionList subclass (can_focus=False for previews)
    ├── option_form.py  # Parameter form with field-highlight navigation
    ├── history_list.py # Execution history
    ├── output_viewer.py# Terminal output with ANSI via pyte
    └── breadcrumbs.py  # Navigation path display
```

## Key Design Decisions

- **Miller columns: committed vs preview** — `_committed` list is the source of truth; `_preview` is derived by `_sync_preview()`. View derived from state, not state from view events.
- **Preview columns suppress Selected** — Textual auto-fires `Selected` on mount (item 0 highlight). Preview `CommandList` widgets have `can_focus=False` and suppress this.
- **NORMAL/EDIT modes** — j/k moves `.field-highlight` CSS class without Textual focus. `i` enters EDIT (focuses widget), `Escape` exits.
- **Execution** — `pty.fork()` with real-time stdout mirroring. Prepends `sys.argv[0]` to args. Falls back to capture-only when no terminal.
- **App name** — picks longer of `cli.name` vs `pyproject.toml [project.name]`, appends description.
- **Mise integration** — `mise_introspect.py` runs `mise tasks --all -x -J`, splits task names by delimiter (default `:`) into a hierarchy, and groups by source directory when tasks come from multiple dirs. `MiseCommanderScreen` overrides `build_command_args()` to produce `mise run <task>` commands. The `usage` CLI parses task usage specs into flags/arguments.

## Code Style

- **Prefer `match`/`case` over `isinstance` chains** — For multi-branch type dispatch, use Python 3.10+ structural pattern matching ([PEP 634](https://peps.python.org/pep-0634/), [PEP 636 class patterns](https://peps.python.org/pep-0636/#adding-a-ui-matching-objects)). Single `isinstance` guard checks, comprehensions, and value computations are fine as-is.

```python
# Preferred: match/case for type dispatch
match focused:
    case CommandList() if focused.selected_schema:
        handle_command(focused)
    case ParameterList() | RunPanel():
        handle_params(focused)

# Fine as-is: single guard checks
if isinstance(schemas, dict):
    ...
```

## Versioning

Bump the version in `pyproject.toml` with every commit that touches code. Follow semver loosely — default to patch bumps, only bump minor/major for truly significant changes.

## Commits

Always include `uv.lock` when it has changes — it must stay in sync with `pyproject.toml`.

## Known Gotchas

- Pyright reports false positive unresolved imports (runs from baalbek dir but consumer projects have their own venvs). Ignore these.
- Consumer upgrade: `uv lock --upgrade-package baalbek && uv sync` (not `--reinstall-package`).
