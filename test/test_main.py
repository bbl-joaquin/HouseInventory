# test_main.py

import unittest
from unittest.mock import patch, MagicMock
from src.main import init_db, main

class TestMain(unittest.TestCase):
    @patch('src.main.sqlite3.connect')
    def test_init_db(self, mock_connect):
        # Arrange
        expected_db_path = "scans.db"
        
        # Act
        conn = init_db(expected_db_path)
        
        # Assert
        mock_connect.assert_called_once_with(expected_db_path)
        cursor = conn.cursor()
        cursor.execute.assert_called_once_with("""
            CREATE TABLE IF NOT EXISTS scans (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                sku       TEXT    NOT NULL,
                mode      TEXT    CHECK(mode IN ('input','output')) NOT NULL,
                timestamp TEXT    NOT NULL
            )
        """)
        conn.commit.assert_called_once()

    @patch('src.main.sqlite3.connect')
    def test_main(self, mock_connect):
        # Arrange
        expected_mode = "input"
        
        def mock_input(prompt):
            if prompt.strip().lower() == "sku":
                return "SKU12345"
            elif prompt.strip().lower() == "exit":
                return "exit"
            else:
                return ""
        
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        with patch('builtins.input', side_effect=mock_input), patch('src.main.args', args=['--mode', 'input']):
            main()
        
        # Assert
        mock_cursor.execute.assert_has_calls([
            unittest.mock.call("INSERT INTO scans (sku, mode, timestamp) VALUES (?, ?, ?)", ('SKU12345', expected_mode, unittest.mock.ANY)),
            unittest.mock.call().commit(),
            unittest.mock.call()
        ])
        mock_conn.close.assert_called_once()

if __name__ == "__main__":
    unittest.main()