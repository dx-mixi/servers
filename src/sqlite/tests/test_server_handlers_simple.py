import pytest
from unittest.mock import patch, MagicMock
from pydantic import AnyUrl
from src.mcp_server_sqlite.server import SqliteDatabase


@pytest.fixture
def db():
    """インメモリSQLiteデータベースを返すフィクスチャ"""
    return SqliteDatabase(":memory:")


@pytest.mark.asyncio
async def test_handle_list_resources():
    """handle_list_resources関数のテスト"""
    from src.mcp_server_sqlite.server import handle_list_resources
    
    result = await handle_list_resources()
    
    assert len(result) == 1
    assert result[0].uri == AnyUrl("memo://insights")
    assert result[0].name == "Business Insights Memo"
    assert result[0].mimeType == "text/plain"


@pytest.mark.asyncio
async def test_handle_read_resource():
    """handle_read_resource関数のテスト"""
    from src.mcp_server_sqlite.server import handle_read_resource
    
    mock_db = MagicMock()
    mock_db._synthesize_memo.return_value = "テストメモ"
    
    with patch("src.mcp_server_sqlite.server.db", mock_db):
        valid_uri = AnyUrl("memo://insights")
        result = await handle_read_resource(valid_uri)
        assert "テストメモ" in result
        
        invalid_scheme_uri = AnyUrl("http://example.com")
        with pytest.raises(ValueError, match="Unsupported URI scheme"):
            await handle_read_resource(invalid_scheme_uri)
        
        invalid_path_uri = AnyUrl("memo://invalid")
        with pytest.raises(ValueError, match="Unknown resource path"):
            await handle_read_resource(invalid_path_uri)


@pytest.mark.asyncio
async def test_handle_list_prompts():
    """handle_list_prompts関数のテスト"""
    from src.mcp_server_sqlite.server import handle_list_prompts
    
    result = await handle_list_prompts()
    
    assert len(result) == 1
    assert result[0].name == "mcp-demo"
    assert len(result[0].arguments) == 1
    assert result[0].arguments[0].name == "topic"
    assert result[0].arguments[0].required is True


@pytest.mark.asyncio
async def test_handle_get_prompt():
    """handle_get_prompt関数のテスト"""
    from src.mcp_server_sqlite.server import handle_get_prompt
    
    result = await handle_get_prompt("mcp-demo", {"topic": "retail"})
    assert result.description == "Demo template for retail"
    assert len(result.messages) == 1
    assert result.messages[0].role == "user"
    assert "retail" in result.messages[0].content.text
    
    with pytest.raises(ValueError, match="Unknown prompt"):
        await handle_get_prompt("invalid-prompt", {"topic": "retail"})
    
    with pytest.raises(ValueError, match="Missing required argument"):
        await handle_get_prompt("mcp-demo", {})
    
    with pytest.raises(ValueError, match="Missing required argument"):
        await handle_get_prompt("mcp-demo", {"not_topic": "retail"})


@pytest.mark.asyncio
async def test_handle_call_tool():
    """handle_call_tool関数のテスト"""
    from src.mcp_server_sqlite.server import handle_call_tool
    
    mock_db = MagicMock()
    mock_db._execute_query.return_value = [{"name": "test_table"}]
    mock_db.insights = []
    
    with patch("src.mcp_server_sqlite.server.db", mock_db):
        list_tables_result = await handle_call_tool("list_tables", {})
        assert len(list_tables_result) == 1
        assert "[{'name': 'test_table'}]" in list_tables_result[0].text
        
        with pytest.raises(ValueError, match="Missing table_name argument"):
            await handle_call_tool("describe_table", {})
        
        describe_table_result = await handle_call_tool("describe_table", {"table_name": "test"})
        assert len(describe_table_result) == 1
        assert "[{'name': 'test_table'}]" in describe_table_result[0].text
        
        with pytest.raises(ValueError, match="Missing insight argument"):
            await handle_call_tool("append_insight", {})
        
        with patch("src.mcp_server_sqlite.server.server") as mock_server:
            mock_server.request_context.session.send_resource_updated = MagicMock()
            append_insight_result = await handle_call_tool("append_insight", {"insight": "テストインサイト"})
            assert len(append_insight_result) == 1
            assert "Insight added to memo" in append_insight_result[0].text
            assert "テストインサイト" in mock_db.insights
        
        with pytest.raises(ValueError, match="Only SELECT queries are allowed"):
            await handle_call_tool("read_query", {"query": "INSERT INTO test VALUES (1)"})
        
        read_query_result = await handle_call_tool("read_query", {"query": "SELECT * FROM test"})
        assert len(read_query_result) == 1
        assert "[{'name': 'test_table'}]" in read_query_result[0].text
        
        with pytest.raises(ValueError, match="SELECT queries are not allowed"):
            await handle_call_tool("write_query", {"query": "SELECT * FROM test"})
        
        write_query_result = await handle_call_tool("write_query", {"query": "INSERT INTO test VALUES (1)"})
        assert len(write_query_result) == 1
        assert "[{'name': 'test_table'}]" in write_query_result[0].text
        
        with pytest.raises(ValueError, match="Only CREATE TABLE statements are allowed"):
            await handle_call_tool("create_table", {"query": "INSERT INTO test VALUES (1)"})
        
        create_table_result = await handle_call_tool("create_table", {"query": "CREATE TABLE new_table (id INT)"})
        assert len(create_table_result) == 1
        assert "Table created successfully" in create_table_result[0].text
        
        with pytest.raises(ValueError, match="Unknown tool"):
            await handle_call_tool("non_existent_tool", {})
