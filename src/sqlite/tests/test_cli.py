import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock
import argparse
import asyncio
from src.mcp_server_sqlite import main


def test_main_args():
    """main関数の引数解析のテスト"""
    with patch('argparse.ArgumentParser.parse_args') as mock_parse_args:
        mock_parse_args.return_value = argparse.Namespace(db_path="./sqlite_mcp_server.db")
        with patch('src.mcp_server_sqlite.server.main') as mock_main:
            main()
            mock_main.assert_called_once_with("./sqlite_mcp_server.db")

    with patch('argparse.ArgumentParser.parse_args') as mock_parse_args:
        mock_parse_args.return_value = argparse.Namespace(db_path="/custom/path/db.sqlite")
        with patch('src.mcp_server_sqlite.server.main') as mock_main:
            main()
            mock_main.assert_called_once_with("/custom/path/db.sqlite")


def test_server_wrapper():
    """ServerWrapperクラスのテスト"""
    from src.mcp_server_sqlite.server import ServerWrapper
    
    wrapper = ServerWrapper()
    
    with patch('asyncio.run') as mock_run:
        wrapper.run()
        mock_run.assert_called_once()
        args, _ = mock_run.call_args
        assert callable(args[0].__await__)
