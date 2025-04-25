import sqlite3
import pytest
from unittest.mock import patch, MagicMock
from src.mcp_server_sqlite.server import SqliteDatabase


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
    """_execute_query関数のテスト - 一時ファイルを使用"""
    import tempfile
    import os
    
    fd, temp_path = tempfile.mkstemp()
    try:
        os.close(fd)
        
        db = SqliteDatabase(temp_path)
        
        create_result = db._execute_query(
            "CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)"
        )
        assert "affected_rows" in create_result[0]
        
        insert_result = db._execute_query(
            "INSERT INTO test (name) VALUES ('テスト名')"
        )
        assert insert_result[0]["affected_rows"] == 1
        
        select_result = db._execute_query("SELECT * FROM test")
        assert len(select_result) == 1
        assert select_result[0]["name"] == "テスト名"
        
        with pytest.raises(sqlite3.Error):
            db._execute_query("SELECT * FROM non_existent_table")
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
