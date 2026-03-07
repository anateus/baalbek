from __future__ import annotations

from pathlib import Path

from textual.app import App

from baalbek.mise_introspect import introspect_mise_tasks, load_mise_tasks
from baalbek.screens.mise_commander import MiseCommanderScreen

_DEFAULT_DB_PATH = Path.home() / ".local" / "share" / "baalbek" / "history.db"


class MiseBaalbek(App):
    CSS_PATH = "baalbek.tcss"
    ALLOW_SELECT = False

    def __init__(
        self,
        delimiter: str = ":",
        db_path: Path | None = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._delimiter = delimiter
        self._db_path = db_path or _DEFAULT_DB_PATH

    def on_mount(self) -> None:
        raw_tasks = load_mise_tasks()
        commands = introspect_mise_tasks(raw_tasks, delimiter=self._delimiter)
        cwd_name = Path.cwd().name or "mise"
        self.push_screen(
            MiseCommanderScreen(
                commands,
                app_name=cwd_name,
                app_description="mise tasks",
                delimiter=self._delimiter,
                raw_tasks=raw_tasks,
            )
        )


def main() -> None:
    app = MiseBaalbek()
    app.run()


if __name__ == "__main__":
    main()
