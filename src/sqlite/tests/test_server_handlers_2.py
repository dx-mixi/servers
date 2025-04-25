import asyncio
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import mcp.types as types
from src.mcp_server_sqlite.server import SqliteDatabase, main


@pytest.mark.asyncio
async def test_handle_get_prompt():
    """handle_get_prompt関数のテスト"""
    server = MagicMock()
    get_prompt_handler = None

    def side_effect(func=None):
        nonlocal get_prompt_handler
        if func is not None:
            get_prompt_handler = func
            return func
        return side_effect

    server.get_prompt = side_effect

    with patch("src.mcp_server_sqlite.server.Server", return_value=server):
        with patch("src.mcp_server_sqlite.server.SqliteDatabase"):
            try:
                asyncio.create_task(main("test.db"))
                await asyncio.sleep(0.1)  # ハンドラ登録のための時間を確保
            except Exception:
                pass

    assert get_prompt_handler is not None

    result = await get_prompt_handler("mcp-demo", {"topic": "retail"})
    assert result.description == "Demo template for retail"
    assert len(result.messages) == 1
    assert result.messages[0].role == "user"
    assert "retail" in result.messages[0].content.text

    with pytest.raises(ValueError, match="Unknown prompt"):
        await get_prompt_handler("invalid-prompt", {"topic": "retail"})

    with pytest.raises(ValueError, match="Missing required argument"):
        await get_prompt_handler("mcp-demo", {})

    with pytest.raises(ValueError, match="Missing required argument"):
        await get_prompt_handler("mcp-demo", {"not_topic": "retail"})


@pytest.mark.asyncio
async def test_handle_list_tools():
    """handle_list_tools関数のテスト"""
    server = MagicMock()
    list_tools_handler = None

    def side_effect(func=None):
        nonlocal list_tools_handler
        if func is not None:
            list_tools_handler = func
            return func
        return side_effect

    server.list_tools = side_effect

    with patch("src.mcp_server_sqlite.server.Server", return_value=server):
        with patch("src.mcp_server_sqlite.server.SqliteDatabase"):
            try:
                asyncio.create_task(main("test.db"))
                await asyncio.sleep(0.1)  # ハンドラ登録のための時間を確保
            except Exception:
                pass

    assert list_tools_handler is not None

    result = await list_tools_handler()
    assert len(result) == 6  # 6つのツールがリストされる

    tool_names = [tool.name for tool in result]
    assert "read_query" in tool_names
    assert "write_query" in tool_names
    assert "create_table" in tool_names
    assert "list_tables" in tool_names
    assert "describe_table" in tool_names
    assert "append_insight" in tool_names


@pytest.mark.asyncio
async def test_handle_call_tool():
    """handle_call_tool関数のテスト"""
    server = MagicMock()
    call_tool_handler = None

    def side_effect(func=None):
        nonlocal call_tool_handler
        if func is not None:
            call_tool_handler = func
            return func
        return side_effect

    server.call_tool = side_effect

    mock_db = MagicMock()
    mock_db._execute_query.return_value = [{"name": "test_table"}]
    mock_db._synthesize_memo.return_value = "テストメモ"
    mock_db.insights = []

    with patch("src.mcp_server_sqlite.server.Server", return_value=server):
        with patch("src.mcp_server_sqlite.server.SqliteDatabase", return_value=mock_db):
            try:
                asyncio.create_task(main("test.db"))
                await asyncio.sleep(0.1)  # ハンドラ登録のための時間を確保
            except Exception:
                pass

    assert call_tool_handler is not None

    list_tables_result = await call_tool_handler("list_tables", {})
    assert len(list_tables_result) == 1
    assert "[{'name': 'test_table'}]" in list_tables_result[0].text

    with pytest.raises(ValueError, match="Missing table_name argument"):
        await call_tool_handler("describe_table", {})

    describe_table_result = await call_tool_handler(
        "describe_table", {"table_name": "test"}
    )
    assert len(describe_table_result) == 1
    assert "[{'name': 'test_table'}]" in describe_table_result[0].text

    with pytest.raises(ValueError, match="Missing insight argument"):
        await call_tool_handler("append_insight", {})

    server.request_context = MagicMock()
    server.request_context.session = MagicMock()
    server.request_context.session.send_resource_updated = AsyncMock()

    append_insight_result = await call_tool_handler(
        "append_insight", {"insight": "テストインサイト"}
    )
    assert len(append_insight_result) == 1
    assert "Insight added to memo" in append_insight_result[0].text
    assert "テストインサイト" in mock_db.insights

    with pytest.raises(ValueError, match="Only SELECT queries are allowed"):
        await call_tool_handler("read_query", {"query": "INSERT INTO test VALUES (1)"})

    read_query_result = await call_tool_handler(
        "read_query", {"query": "SELECT * FROM test"}
    )
    assert len(read_query_result) == 1
    assert "[{'name': 'test_table'}]" in read_query_result[0].text

    with pytest.raises(ValueError, match="SELECT queries are not allowed"):
        await call_tool_handler("write_query", {"query": "SELECT * FROM test"})

    write_query_result = await call_tool_handler(
        "write_query", {"query": "INSERT INTO test VALUES (1)"}
    )
    assert len(write_query_result) == 1
    assert "[{'name': 'test_table'}]" in write_query_result[0].text

    with pytest.raises(ValueError, match="Only CREATE TABLE statements are allowed"):
        await call_tool_handler(
            "create_table", {"query": "INSERT INTO test VALUES (1)"}
        )

    create_table_result = await call_tool_handler(
        "create_table", {"query": "CREATE TABLE new_table (id INT)"}
    )
    assert len(create_table_result) == 1
    assert "Table created successfully" in create_table_result[0].text

    with pytest.raises(ValueError, match="Unknown tool"):
        await call_tool_handler("non_existent_tool", {})
