from pathlib import Path

from baalbek.db import HistoryDB


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
