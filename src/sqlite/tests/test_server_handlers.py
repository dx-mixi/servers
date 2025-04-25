import os
import tempfile
import asyncio
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from pydantic import AnyUrl
import mcp.types as types
from src.mcp_server_sqlite.server import SqliteDatabase, main


@pytest.fixture
def db():
    """インメモリSQLiteデータベースを返すフィクスチャ"""
    return SqliteDatabase(":memory:")


@pytest.mark.asyncio
async def test_handle_list_resources():
    """handle_list_resources関数のテスト"""
    server = MagicMock()
    list_resources_handler = None

    def side_effect(func=None):
        nonlocal list_resources_handler
        if func is not None:
            list_resources_handler = func
            return func
        return side_effect

    server.list_resources = side_effect

    with patch("src.mcp_server_sqlite.server.Server", return_value=server):
        with patch("src.mcp_server_sqlite.server.SqliteDatabase"):
            try:
                asyncio.create_task(main("test.db"))
                await asyncio.sleep(0.1)  # ハンドラ登録のための時間を確保
            except Exception:
                pass

    assert list_resources_handler is not None

    result = await list_resources_handler()
    assert len(result) == 1
    assert result[0].uri == AnyUrl("memo://insights")
    assert result[0].name == "Business Insights Memo"
    assert result[0].mimeType == "text/plain"


@pytest.mark.asyncio
async def test_handle_read_resource(db):
    """handle_read_resource関数のテスト"""
    server = MagicMock()
    read_resource_handler = None

    def side_effect(func=None):
        nonlocal read_resource_handler
        if func is not None:
            read_resource_handler = func
            return func
        return side_effect

    server.read_resource = side_effect

    with patch("src.mcp_server_sqlite.server.Server", return_value=server):
        with patch("src.mcp_server_sqlite.server.SqliteDatabase", return_value=db):
            try:
                asyncio.create_task(main("test.db"))
                await asyncio.sleep(0.1)  # ハンドラ登録のための時間を確保
            except Exception:
                pass

    assert read_resource_handler is not None

    valid_uri = AnyUrl("memo://insights")
    result = await read_resource_handler(valid_uri)
    assert "No business insights have been discovered yet." in result

    db.insights.append("テストインサイト")
    result = await read_resource_handler(valid_uri)
    assert "テストインサイト" in result

    invalid_scheme_uri = AnyUrl("http://example.com")
    with pytest.raises(ValueError, match="Unsupported URI scheme"):
        await read_resource_handler(invalid_scheme_uri)

    invalid_path_uri = AnyUrl("memo://invalid")
    with pytest.raises(ValueError, match="Unknown resource path"):
        await read_resource_handler(invalid_path_uri)


@pytest.mark.asyncio
async def test_handle_list_prompts():
    """handle_list_prompts関数のテスト"""
    server = MagicMock()
    list_prompts_handler = None

    def side_effect(func=None):
        nonlocal list_prompts_handler
        if func is not None:
            list_prompts_handler = func
            return func
        return side_effect

    server.list_prompts = side_effect

    with patch("src.mcp_server_sqlite.server.Server", return_value=server):
        with patch("src.mcp_server_sqlite.server.SqliteDatabase"):
            try:
                asyncio.create_task(main("test.db"))
                await asyncio.sleep(0.1)  # ハンドラ登録のための時間を確保
            except Exception:
                pass

    assert list_prompts_handler is not None

    result = await list_prompts_handler()
    assert len(result) == 1
    assert result[0].name == "mcp-demo"
    assert len(result[0].arguments) == 1
    assert result[0].arguments[0].name == "topic"
    assert result[0].arguments[0].required is True
