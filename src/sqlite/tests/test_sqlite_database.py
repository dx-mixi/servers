import os
import sqlite3
import tempfile
from contextlib import closing
import pytest
from src.mcp_server_sqlite.server import SqliteDatabase


def test_init_database():
    """SqliteDatabase初期化のテスト"""
    # インメモリデータベースを使用
    db = SqliteDatabase(":memory:")

    with closing(sqlite3.connect(":memory:")) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        assert len(tables) == 0


def test_synthesize_memo():
    """_synthesize_memo関数のテスト"""
    db = SqliteDatabase(":memory:")  # インメモリデータベースを使用

    assert db._synthesize_memo() == "No business insights have been discovered yet."

    db.insights = ["売上が10%増加", "新規顧客が増加傾向"]
    memo = db._synthesize_memo()
    assert "売上が10%増加" in memo
    assert "新規顧客が増加傾向" in memo
    assert "Analysis has revealed 2 key business insights" in memo


def test_execute_query():
    """_execute_query関数のテスト"""
    with tempfile.NamedTemporaryFile(delete=False) as f:
        db_path = f.name

    try:
        db = SqliteDatabase(db_path)

        create_result = db._execute_query(
            "CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)"
        )
        assert "affected_rows" in create_result[0]

        insert_result = db._execute_query("INSERT INTO test (name) VALUES ('テスト名')")
        assert insert_result[0]["affected_rows"] == 1

        select_result = db._execute_query("SELECT * FROM test")
        assert len(select_result) == 1
        assert select_result[0]["name"] == "テスト名"

        param_result = db._execute_query(
            "SELECT * FROM test WHERE name = ?", ["テスト名"]
        )
        assert len(param_result) == 1
        assert param_result[0]["id"] == 1

        with pytest.raises(sqlite3.Error):
            db._execute_query("SELECT * FROM non_existent_table")
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)
