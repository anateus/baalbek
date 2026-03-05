from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class RunRecord:
    id: int
    command: str
    args_json: str
    exit_code: int | None
    raw_output: bytes | None
    plain_output: str | None
    started_at: str
    finished_at: str | None


_SCHEMA_RUNS = """\
CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    command TEXT NOT NULL,
    args_json TEXT NOT NULL,
    exit_code INTEGER,
    raw_output BLOB,
    plain_output TEXT,
    started_at TEXT NOT NULL,
    finished_at TEXT
);
"""

_SCHEMA_DRAFTS = """\
CREATE TABLE IF NOT EXISTS drafts (
    command_path TEXT PRIMARY KEY,
    values_json TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""


class HistoryDB:
    def __init__(self, db_path: Path) -> None:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(db_path)
        self._conn.execute(_SCHEMA_RUNS)
        self._conn.execute(_SCHEMA_DRAFTS)
        self._conn.commit()

    def insert_run(
        self,
        command: str,
        args_json: str,
        exit_code: int | None,
        raw_output: bytes | None,
        plain_output: str | None,
    ) -> int:
        now = datetime.now(timezone.utc).isoformat()
        cur = self._conn.execute(
            "INSERT INTO runs (command, args_json, exit_code, raw_output, plain_output, started_at)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (command, args_json, exit_code, raw_output, plain_output, now),
        )
        self._conn.commit()
        return cur.lastrowid  # type: ignore[return-value]

    def get_run(self, run_id: int) -> RunRecord | None:
        cur = self._conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,))
        row = cur.fetchone()
        if row is None:
            return None
        return RunRecord(*row)

    def list_runs(self, limit: int = 50) -> list[RunRecord]:
        cur = self._conn.execute(
            "SELECT * FROM runs ORDER BY id DESC LIMIT ?", (limit,)
        )
        return [RunRecord(*row) for row in cur.fetchall()]

    def save_draft(self, command_path: str, values: dict) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self._conn.execute(
            "INSERT INTO drafts (command_path, values_json, updated_at)"
            " VALUES (?, ?, ?)"
            " ON CONFLICT(command_path) DO UPDATE SET values_json=excluded.values_json, updated_at=excluded.updated_at",
            (command_path, json.dumps(values), now),
        )
        self._conn.commit()

    def load_draft(self, command_path: str) -> dict | None:
        cur = self._conn.execute(
            "SELECT values_json FROM drafts WHERE command_path = ?",
            (command_path,),
        )
        row = cur.fetchone()
        if row is None:
            return None
        return json.loads(row[0])

    def delete_draft(self, command_path: str) -> None:
        self._conn.execute(
            "DELETE FROM drafts WHERE command_path = ?", (command_path,)
        )
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()
