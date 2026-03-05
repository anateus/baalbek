from datetime import datetime, timedelta, timezone
from pathlib import Path

from baalbek.db import HistoryDB, SortMode, compute_frequency_scores


def test_create_db(tmp_path: Path) -> None:
    db_path = tmp_path / "sub" / "history.db"
    db = HistoryDB(db_path)
    assert db_path.exists()
    db.close()


def test_insert_and_fetch_run(tmp_path: Path) -> None:
    db = HistoryDB(tmp_path / "history.db")
    run_id = db.insert_run(
        command="greet",
        args_json='{"name": "world"}',
        exit_code=0,
        raw_output=b"\x1b[31mhello\x1b[0m",
        plain_output="hello",
    )
    rec = db.get_run(run_id)
    assert rec is not None
    assert rec.id == run_id
    assert rec.command == "greet"
    assert rec.args_json == '{"name": "world"}'
    assert rec.exit_code == 0
    assert rec.raw_output == b"\x1b[31mhello\x1b[0m"
    assert rec.plain_output == "hello"
    assert rec.started_at is not None
    assert rec.finished_at is None
    db.close()


def test_list_runs_newest_first(tmp_path: Path) -> None:
    db = HistoryDB(tmp_path / "history.db")
    ids = [db.insert_run(f"cmd{i}", "{}", 0, None, None) for i in range(3)]
    runs = db.list_runs()
    assert [r.id for r in runs] == list(reversed(ids))
    db.close()


def test_list_runs_with_limit(tmp_path: Path) -> None:
    db = HistoryDB(tmp_path / "history.db")
    for i in range(10):
        db.insert_run(f"cmd{i}", "{}", 0, None, None)
    runs = db.list_runs(limit=3)
    assert len(runs) == 3
    db.close()


def test_save_and_load_draft(tmp_path: Path) -> None:
    db = HistoryDB(tmp_path / "history.db")
    db.save_draft("cli/deploy", {"name": "myapp", "replicas": 3})
    result = db.load_draft("cli/deploy")
    assert result == {"name": "myapp", "replicas": 3}
    db.close()


def test_save_draft_upsert(tmp_path: Path) -> None:
    db = HistoryDB(tmp_path / "history.db")
    db.save_draft("cli/deploy", {"name": "v1"})
    db.save_draft("cli/deploy", {"name": "v2"})
    result = db.load_draft("cli/deploy")
    assert result == {"name": "v2"}
    db.close()


def test_load_draft_missing(tmp_path: Path) -> None:
    db = HistoryDB(tmp_path / "history.db")
    assert db.load_draft("nonexistent") is None
    db.close()


def test_delete_draft(tmp_path: Path) -> None:
    db = HistoryDB(tmp_path / "history.db")
    db.save_draft("cli/deploy", {"name": "myapp"})
    db.delete_draft("cli/deploy")
    assert db.load_draft("cli/deploy") is None
    db.close()


def test_recent_command_data(tmp_path):
    db = HistoryDB(tmp_path / "history.db")
    db.insert_run("deploy web", '["script", "deploy", "web"]', 0, None, None)
    db.insert_run("logs tail", '["script", "logs", "tail"]', 0, None, None)
    rows = db.recent_command_data(days=7)
    assert len(rows) == 2
    assert rows[0][0] in ("deploy web", "logs tail")
    db.close()


def test_recent_command_data_excludes_old(tmp_path):
    db = HistoryDB(tmp_path / "history.db")
    db.insert_run("deploy web", '["script", "deploy"]', 0, None, None)
    old_time = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
    db._conn.execute(
        "INSERT INTO runs (command, args_json, exit_code, started_at) VALUES (?, ?, ?, ?)",
        ("old cmd", '["script", "old"]', 0, old_time),
    )
    db._conn.commit()
    rows = db.recent_command_data(days=7)
    assert len(rows) == 1
    assert rows[0][0] == "deploy web"
    db.close()


def test_compute_frequency_scores_basic():
    now = datetime.now(timezone.utc)
    runs = [
        ("deploy web", now.isoformat()),
        ("deploy api", now.isoformat()),
        ("deploy web", now.isoformat()),
        ("logs tail", now.isoformat()),
    ]
    scores = compute_frequency_scores(runs, {"deploy", "logs"})
    assert scores["deploy"] > scores["logs"]


def test_compute_frequency_scores_recency_weighting():
    now = datetime.now(timezone.utc)
    old = (now - timedelta(days=6)).isoformat()
    runs = [
        ("deploy web", old),
        ("deploy web", old),
        ("deploy web", old),
        ("logs tail", now.isoformat()),
    ]
    scores = compute_frequency_scores(runs, {"deploy", "logs"})
    assert scores["logs"] > scores["deploy"]


def test_compute_frequency_scores_unknown_commands_ignored():
    now = datetime.now(timezone.utc)
    runs = [("unknown cmd", now.isoformat())]
    scores = compute_frequency_scores(runs, {"deploy", "logs"})
    assert scores == {}


def test_sort_mode_enum():
    assert SortMode.FREQUENCY.value == "frequency"
    assert SortMode.ALPHA.value == "alpha"
