import pytest
from unittest.mock import patch, MagicMock
import argparse
from src.mcp_server_sqlite import main


def test_main_args():
    """main関数の引数解析のテスト"""
    with patch("argparse.ArgumentParser.parse_args") as mock_parse_args:
        mock_parse_args.return_value = argparse.Namespace(db_path="./test_db.sqlite")
        with patch("src.mcp_server_sqlite.server.main") as mock_main:
            main()
            mock_main.assert_called_once_with("./test_db.sqlite")
