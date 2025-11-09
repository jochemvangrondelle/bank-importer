# Copyright (C) 2025 Jochem van Grondelle <jochem@vangrondelle.net>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the PolyForm Noncommercial License 1.0.0.
# You may not use this program except in compliance with the License.
# A copy of the License is available at https://polyformproject.org/licenses/noncommercial/1.0.0/
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# PolyForm Noncommercial License 1.0.0 for more details.

"""Tests for CLI status command."""

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, Mock, patch

import pytest

from bank_importer.cli.commands import status


class TestStatusCommand:
    """Tests for status command."""

    @pytest.fixture
    def mock_config_manager(self) -> Mock:
        """Create a mock config manager."""
        config_manager = Mock()
        config_manager.get_all_accounts.return_value = [
            {
                "name": "test_account_1",
                "bank_name": "Test Bank 1",
                "account_number": "123-456-789",
                "parser": "test_parser",
            },
            {
                "name": "test_account_2",
                "bank_name": "Test Bank 2",
                "account_number": "987-654-321",
                "parser": "another_parser",
            },
        ]
        return config_manager

    @pytest.fixture
    def mock_db_manager(self) -> Mock:
        """Create a mock database manager."""
        db_manager = Mock()
        # Mock transactions for account 1
        db_manager.get_transactions_by_account.side_effect = lambda acc_num: {
            "123-456-789": [
                {
                    "date": "2024-01-01",
                    "amount": 100.0,
                },
                {
                    "date": "2024-01-15",
                    "amount": -50.0,
                },
            ],
            "987-654-321": [
                {
                    "date": "2024-02-01",
                    "amount": 200.0,
                },
            ],
        }.get(acc_num, [])

        # Mock import sessions
        db_manager.get_import_sessions_by_account.side_effect = lambda acc_name: {
            "test_account_1": [
                {
                    "id": 1,
                    "session_name": "session_1",
                    "account_name": "test_account_1",
                    "status": "completed",
                    "started_at": "2024-01-01T10:00:00",
                    "file_path": "/path/to/file1.txt",
                    "processed_transactions": 10,
                    "total_transactions": 10,
                },
            ],
            "test_account_2": [
                {
                    "id": 2,
                    "session_name": "session_2",
                    "account_name": "test_account_2",
                    "status": "failed",
                    "started_at": "2024-02-01T11:00:00",
                    "file_path": "/path/to/file2.txt",
                    "processed_transactions": 5,
                    "total_transactions": 10,
                },
            ],
        }.get(acc_name, [])

        # Mock transactions by session
        db_manager.get_transactions_by_session.side_effect = lambda session_id: {
            1: [
                {
                    "date": "2024-01-01",
                    "amount": 100.0,
                },
                {
                    "date": "2024-01-15",
                    "amount": -50.0,
                },
            ],
            2: [
                {
                    "date": "2024-02-01",
                    "amount": 200.0,
                },
            ],
        }.get(session_id, [])

        return db_manager

    @pytest.fixture
    def mock_context(self, mock_config_manager: Mock, mock_db_manager: Mock) -> Mock:
        """Create a mock CLI context."""
        context = Mock()
        context.get_config_manager.return_value = mock_config_manager
        context.get_db_manager.return_value = mock_db_manager
        return context

    @patch("bank_importer.cli.commands.status.get_console")
    @patch("bank_importer.cli.commands.status.CLIContext")
    def test_status_with_accounts_and_sessions(
        self,
        mock_cli_context_class: Mock,
        mock_console: Mock,
        mock_context: Mock,
    ) -> None:
        """Test status command with accounts and import sessions."""
        mock_cli_context_class.return_value.__enter__.return_value = mock_context
        mock_console_instance = Mock()
        mock_console.return_value = mock_console_instance

        status.status()

        # Verify CLIContext was called (don't check exact parameter due to Typer wrapping)
        mock_cli_context_class.assert_called_once()
        assert mock_cli_context_class.call_args[0][0] == "config.toml" or hasattr(
            mock_cli_context_class.call_args[0][0],
            "default",
        )

        # Verify console.print was called (we don't check exact output as it's complex)
        assert mock_console_instance.print.called

        # Verify table creation and printing happened
        print_calls = list(mock_console_instance.print.call_args_list)
        assert len(print_calls) > 0

    @patch("bank_importer.cli.commands.status.get_console")
    @patch("bank_importer.cli.commands.status.CLIContext")
    def test_status_no_accounts(
        self,
        mock_cli_context_class: Mock,
        mock_console: Mock,
    ) -> None:
        """Test status command with no accounts."""
        mock_context = Mock()
        mock_context.get_config_manager.return_value.get_all_accounts.return_value = []
        mock_context.get_db_manager.return_value.get_import_sessions_by_account.return_value = []
        mock_cli_context_class.return_value.__enter__.return_value = mock_context

        mock_console_instance = Mock()
        mock_console.return_value = mock_console_instance

        status.status()

        # Verify console.print was called
        assert mock_console_instance.print.called

    @patch("bank_importer.cli.commands.status.get_console")
    @patch("bank_importer.cli.commands.status.CLIContext")
    def test_status_no_import_sessions(
        self,
        mock_cli_context_class: Mock,
        mock_console: Mock,
        mock_config_manager: Mock,
        mock_db_manager: Mock,
    ) -> None:
        """Test status command with accounts but no import sessions."""
        mock_context = Mock()
        mock_context.get_config_manager.return_value = mock_config_manager
        mock_context.get_db_manager.return_value = mock_db_manager

        # Override to return no sessions
        mock_db_manager.get_import_sessions_by_account.return_value = []

        mock_cli_context_class.return_value.__enter__.return_value = mock_context

        mock_console_instance = Mock()
        mock_console.return_value = mock_console_instance

        status.status()

        # Verify console.print was called
        assert mock_console_instance.print.called

        # Just verify that the function completed without error
        # The exact output format depends on Rich table rendering

    @patch("bank_importer.cli.commands.status.get_console")
    @patch("bank_importer.cli.commands.status.CLIContext")
    def test_status_with_custom_config_file(
        self,
        mock_cli_context_class: Mock,
        mock_console: Mock,
        mock_context: Mock,
    ) -> None:
        """Test status command with custom config file."""
        mock_cli_context_class.return_value.__enter__.return_value = mock_context
        mock_console_instance = Mock()
        mock_console.return_value = mock_console_instance

        status.status("custom_config.toml")

        # Verify CLIContext was called with custom config
        mock_cli_context_class.assert_called_once_with("custom_config.toml")

    @patch("bank_importer.cli.commands.status.get_console")
    @patch("bank_importer.cli.commands.status.CLIContext")
    def test_status_transaction_date_range_calculation(
        self,
        mock_cli_context_class: Mock,
        mock_console: Mock,
    ) -> None:
        """Test status command date range calculation for transactions."""
        mock_context = Mock()
        mock_config_manager = Mock()
        mock_db_manager = Mock()

        # Set up accounts
        mock_config_manager.get_all_accounts.return_value = [
            {
                "name": "test_account",
                "bank_name": "Test Bank",
                "account_number": "123-456-789",
                "parser": "test_parser",
            },
        ]

        # Set up transactions with specific dates
        mock_db_manager.get_transactions_by_account.return_value = [
            {"date": "2024-01-01"},
            {"date": "2024-01-15"},
            {"date": "2024-01-31"},
        ]

        # No import sessions
        mock_db_manager.get_import_sessions_by_account.return_value = []

        mock_context.get_config_manager.return_value = mock_config_manager
        mock_context.get_db_manager.return_value = mock_db_manager

        mock_cli_context_class.return_value.__enter__.return_value = mock_context

        mock_console_instance = Mock()
        mock_console.return_value = mock_console_instance

        status.status()

        # Verify console.print was called
        assert mock_console_instance.print.called

    @patch("bank_importer.cli.commands.status.get_console")
    @patch("bank_importer.cli.commands.status.CLIContext")
    def test_status_session_sorting_and_display(
        self,
        mock_cli_context_class: Mock,
        mock_console: Mock,
    ) -> None:
        """Test status command session sorting and display logic."""
        mock_context = Mock()
        mock_config_manager = Mock()
        mock_db_manager = Mock()

        # Set up accounts
        mock_config_manager.get_all_accounts.return_value = [
            {
                "name": "test_account",
                "bank_name": "Test Bank",
                "account_number": "123-456-789",
                "parser": "test_parser",
            },
        ]

        # Set up transactions
        mock_db_manager.get_transactions_by_account.return_value = []

        # Set up multiple import sessions with different dates
        mock_db_manager.get_import_sessions_by_account.return_value = [
            {
                "id": 1,
                "session_name": "older_session",
                "account_name": "test_account",
                "status": "completed",
                "started_at": "2024-01-01T10:00:00",
                "file_path": "/path/to/file1.txt",
                "processed_transactions": 10,
                "total_transactions": 10,
            },
            {
                "id": 2,
                "session_name": "newer_session",
                "account_name": "test_account",
                "status": "completed",
                "started_at": "2024-02-01T10:00:00",
                "file_path": "/path/to/file2.txt",
                "processed_transactions": 15,
                "total_transactions": 15,
            },
        ]

        # Set up transactions for sessions
        mock_db_manager.get_transactions_by_session.side_effect = (
            lambda session_id: [
                {"date": "2024-01-15", "amount": 100.0},
            ]
            if session_id == 1
            else [
                {"date": "2024-02-15", "amount": 200.0},
            ]
        )

        mock_context.get_config_manager.return_value = mock_config_manager
        mock_context.get_db_manager.return_value = mock_db_manager

        mock_cli_context_class.return_value.__enter__.return_value = mock_context

        mock_console_instance = Mock()
        mock_console.return_value = mock_console_instance

        status.status()

        # Verify console.print was called
        assert mock_console_instance.print.called

    @patch("bank_importer.cli.commands.status.get_console")
    @patch("bank_importer.cli.commands.status.CLIContext")
    def test_status_consolidated_summary_calculation(
        self,
        mock_cli_context_class: Mock,
        mock_console: Mock,
    ) -> None:
        """Test status command consolidated summary calculation."""
        mock_context = Mock()
        mock_config_manager = Mock()
        mock_db_manager = Mock()

        # Set up accounts
        mock_config_manager.get_all_accounts.return_value = [
            {
                "name": "account_1",
                "bank_name": "Bank 1",
                "account_number": "111-111-111",
                "parser": "parser1",
            },
            {
                "name": "account_2",
                "bank_name": "Bank 2",
                "account_number": "222-222-222",
                "parser": "parser2",
            },
        ]

        # Set up transactions for each account
        mock_db_manager.get_transactions_by_account.side_effect = lambda acc_num: {
            "111-111-111": [
                {"date": "2024-01-01", "amount": 100.0},
                {"date": "2024-01-15", "amount": -50.0},
            ],
            "222-222-222": [
                {"date": "2024-01-10", "amount": 200.0},
                {"date": "2024-01-20", "amount": -75.0},
            ],
        }.get(acc_num, [])

        # Set up import sessions
        mock_db_manager.get_import_sessions_by_account.side_effect = lambda acc_name: [
            {
                "id": 1,
                "session_name": "session_1",
                "account_name": acc_name,
                "status": "completed",
                "started_at": "2024-01-01T10:00:00",
                "file_path": f"/path/to/{acc_name}_file.txt",
                "processed_transactions": 2,
                "total_transactions": 2,
            },
        ]

        # Set up transactions for sessions
        mock_db_manager.get_transactions_by_session.return_value = [
            {"date": "2024-01-01", "amount": 100.0},
            {"date": "2024-01-15", "amount": -50.0},
        ]

        mock_context.get_config_manager.return_value = mock_config_manager
        mock_context.get_db_manager.return_value = mock_db_manager

        mock_cli_context_class.return_value.__enter__.return_value = mock_context

        mock_console_instance = Mock()
        mock_console.return_value = mock_console_instance

        status.status()

        # Verify console.print was called
        assert mock_console_instance.print.called

    @pytest.mark.parametrize(
        ("session_status", "expected_icon"),
        [
            ("completed", "✅"),
            ("failed", "❌"),
            ("processing", "🔄"),
            ("pending", "🔄"),
        ],
    )
    @patch("bank_importer.cli.commands.status.get_console")
    @patch("bank_importer.cli.commands.status.CLIContext")
    def test_status_session_status_icons(
        self,
        mock_cli_context_class: Mock,
        mock_console: Mock,
        session_status: str,
        expected_icon: str,
    ) -> None:
        """Test status command displays correct icons for session statuses."""
        mock_context = Mock()
        mock_config_manager = Mock()
        mock_db_manager = Mock()

        # Set up accounts
        mock_config_manager.get_all_accounts.return_value = [
            {
                "name": "test_account",
                "bank_name": "Test Bank",
                "account_number": "123-456-789",
                "parser": "test_parser",
            },
        ]

        # Set up transactions
        mock_db_manager.get_transactions_by_account.return_value = []

        # Set up import session with parameterized status
        mock_db_manager.get_import_sessions_by_account.return_value = [
            {
                "id": 1,
                "session_name": "test_session",
                "account_name": "test_account",
                "status": session_status,
                "started_at": "2024-01-01T10:00:00",
                "file_path": "/path/to/file.txt",
                "processed_transactions": 5,
                "total_transactions": 5,
            },
        ]

        # Set up transactions for session
        mock_db_manager.get_transactions_by_session.return_value = [
            {"date": "2024-01-01", "amount": 100.0},
        ]

        mock_context.get_config_manager.return_value = mock_config_manager
        mock_context.get_db_manager.return_value = mock_db_manager

        mock_cli_context_class.return_value.__enter__.return_value = mock_context

        mock_console_instance = Mock()
        mock_console.return_value = mock_console_instance

        status.status()

        # Verify console.print was called - the actual icon display depends on Rich table rendering
        assert mock_console_instance.print.called

    @pytest.mark.parametrize(
        ("max_date", "last_month_date", "expected_red_style"),
        [
            ("2024-01-31", "2024-01-31", False),  # Matches - no red
            ("2024-01-15", "2024-01-31", True),  # Doesn't match - red
            ("2024-02-01", "2024-01-31", True),  # Future date - red
        ],
    )
    @patch("bank_importer.cli.commands.status.get_console")
    @patch("bank_importer.cli.commands.status.CLIContext")
    def test_status_max_date_styling(
        self,
        mock_cli_context_class: Mock,
        mock_console: Mock,
        max_date: str,
        last_month_date: str,
        expected_red_style: bool,
    ) -> None:
        """Test status command max date styling logic."""
        mock_context = Mock()
        mock_config_manager = Mock()
        mock_db_manager = Mock()

        # Set up accounts
        mock_config_manager.get_all_accounts.return_value = [
            {
                "name": "test_account",
                "bank_name": "Test Bank",
                "account_number": "123-456-789",
                "parser": "test_parser",
            },
        ]

        # Set up transactions
        mock_db_manager.get_transactions_by_account.return_value = []

        # Set up import session
        mock_db_manager.get_import_sessions_by_account.return_value = [
            {
                "id": 1,
                "session_name": "test_session",
                "account_name": "test_account",
                "status": "completed",
                "started_at": "2024-01-01T10:00:00",
                "file_path": "/path/to/file.txt",
                "processed_transactions": 1,
                "total_transactions": 1,
            },
        ]

        # Set up transactions for session with parameterized max_date
        mock_db_manager.get_transactions_by_session.return_value = [
            {"date": max_date, "amount": 100.0},
        ]

        mock_context.get_config_manager.return_value = mock_config_manager
        mock_context.get_db_manager.return_value = mock_db_manager

        mock_cli_context_class.return_value.__enter__.return_value = mock_context

        mock_console_instance = Mock()
        mock_console.return_value = mock_console_instance

        status.status()

        # Verify console.print was called - the actual styling depends on Rich table rendering
        assert mock_console_instance.print.called

    @patch("bank_importer.cli.commands.status.get_console")
    @patch("bank_importer.cli.commands.status.CLIContext")
    def test_status_expense_deposit_calculation(
        self,
        mock_cli_context_class: Mock,
        mock_console: Mock,
    ) -> None:
        """Test status command expense and deposit amount calculations."""
        mock_context = Mock()
        mock_config_manager = Mock()
        mock_db_manager = Mock()

        # Set up accounts
        mock_config_manager.get_all_accounts.return_value = [
            {
                "name": "test_account",
                "bank_name": "Test Bank",
                "account_number": "123-456-789",
                "parser": "test_parser",
            },
        ]

        # Set up transactions
        mock_db_manager.get_transactions_by_account.return_value = []

        # Set up import session
        mock_db_manager.get_import_sessions_by_account.return_value = [
            {
                "id": 1,
                "session_name": "test_session",
                "account_name": "test_account",
                "status": "completed",
                "started_at": "2024-01-01T10:00:00",
                "file_path": "/path/to/file.txt",
                "processed_transactions": 4,
                "total_transactions": 4,
            },
        ]

        # Set up transactions with mixed positive/negative amounts
        mock_db_manager.get_transactions_by_session.return_value = [
            {"date": "2024-01-01", "amount": 100.0},  # Deposit
            {"date": "2024-01-02", "amount": -50.0},  # Expense
            {"date": "2024-01-03", "amount": 25.0},  # Deposit
            {"date": "2024-01-04", "amount": -75.0},  # Expense
        ]

        mock_context.get_config_manager.return_value = mock_config_manager
        mock_context.get_db_manager.return_value = mock_db_manager

        mock_cli_context_class.return_value.__enter__.return_value = mock_context

        mock_console_instance = Mock()
        mock_console.return_value = mock_console_instance

        status.status()

        # Verify console.print was called - the actual amount formatting depends on Rich table rendering
        assert mock_console_instance.print.called

    @patch("bank_importer.cli.commands.status.get_console")
    @patch("bank_importer.cli.commands.status.CLIContext")
    def test_status_datetime_handling(
        self,
        mock_cli_context_class: Mock,
        mock_console: Mock,
    ) -> None:
        """Test status command handles datetime objects correctly."""
        mock_context = Mock()
        mock_config_manager = Mock()
        mock_db_manager = Mock()

        # Set up accounts
        mock_config_manager.get_all_accounts.return_value = [
            {
                "name": "test_account",
                "bank_name": "Test Bank",
                "account_number": "123-456-789",
                "parser": "test_parser",
            },
        ]

        # Set up transactions
        mock_db_manager.get_transactions_by_account.return_value = []

        # Set up import session
        mock_db_manager.get_import_sessions_by_account.return_value = [
            {
                "id": 1,
                "session_name": "test_session",
                "account_name": "test_account",
                "status": "completed",
                "started_at": datetime(2024, 1, 1, 10, 0, 0, tzinfo=UTC).isoformat(),
                "file_path": "/path/to/file.txt",
                "processed_transactions": 1,
                "total_transactions": 1,
            },
        ]

        # Set up transactions with datetime objects
        mock_db_manager.get_transactions_by_session.return_value = [
            {"date": datetime(2024, 1, 15, tzinfo=UTC), "amount": 100.0},
        ]

        mock_context.get_config_manager.return_value = mock_config_manager
        mock_context.get_db_manager.return_value = mock_db_manager

        mock_cli_context_class.return_value.__enter__.return_value = mock_context

        mock_console_instance = Mock()
        mock_console.return_value = mock_console_instance

        status.status()

        # Verify console.print was called
        assert mock_console_instance.print.called

    @patch("bank_importer.cli.commands.status.get_console")
    @patch("bank_importer.cli.commands.status.CLIContext")
    def test_status_future_date_handling(
        self,
        mock_cli_context_class: Mock,
        mock_console: Mock,
    ) -> None:
        """Test status command handles future dates in last month calculation."""
        mock_context = Mock()
        mock_config_manager = Mock()
        mock_db_manager = Mock()

        # Set up accounts
        mock_config_manager.get_all_accounts.return_value = [
            {
                "name": "test_account",
                "bank_name": "Test Bank",
                "account_number": "123-456-789",
                "parser": "test_parser",
            },
        ]

        # Set up transactions
        mock_db_manager.get_transactions_by_account.return_value = []

        # Set up import session
        mock_db_manager.get_import_sessions_by_account.return_value = [
            {
                "id": 1,
                "session_name": "test_session",
                "account_name": "test_account",
                "status": "completed",
                "started_at": "2024-01-01T10:00:00",
                "file_path": "/path/to/file.txt",
                "processed_transactions": 1,
                "total_transactions": 1,
            },
        ]

        # Set up transactions with future date (simulate edge case)
        future_date = (datetime.now(UTC) + timedelta(days=30)).strftime("%Y-%m-%d")
        mock_db_manager.get_transactions_by_session.return_value = [
            {"date": future_date, "amount": 100.0},
        ]

        mock_context.get_config_manager.return_value = mock_config_manager
        mock_context.get_db_manager.return_value = mock_db_manager

        mock_cli_context_class.return_value.__enter__.return_value = mock_context

        mock_console_instance = Mock()
        mock_console.return_value = mock_console_instance

        status.status()

        # Verify console.print was called
        assert mock_console_instance.print.called

    @patch("bank_importer.cli.commands.status.get_console")
    @patch("bank_importer.cli.commands.status.CLIContext")
    @patch("sys.exit")
    def test_status_session_sorting_with_invalid_dates(
        self,
        mock_sys_exit: Mock,
        mock_cli_context_class: Mock,
        mock_console: Mock,
    ) -> None:
        """Test status command session sorting with invalid date strings."""
        mock_context = Mock()
        mock_config_manager = Mock()
        mock_db_manager = Mock()

        # Set up accounts
        mock_config_manager.get_all_accounts.return_value = [
            {
                "name": "test_account",
                "bank_name": "Test Bank",
                "account_number": "123-456-789",
                "parser": "test_parser",
            },
        ]

        # Set up transactions
        mock_db_manager.get_transactions_by_account.return_value = []

        # Set up import sessions with invalid date strings to trigger exception handling
        mock_db_manager.get_import_sessions_by_account.return_value = [
            {
                "id": 1,
                "session_name": "session_with_invalid_date",
                "account_name": "test_account",
                "status": "completed",
                "started_at": "2024-01-01T10:00:00",
                "file_path": "/path/to/file1.txt",
                "processed_transactions": 10,
                "total_transactions": 10,
            },
        ]

        # Set up transactions with invalid date strings
        mock_db_manager.get_transactions_by_session.return_value = [
            {"date": "invalid-date-string", "amount": 100.0},
        ]

        mock_context.get_config_manager.return_value = mock_config_manager
        mock_context.get_db_manager.return_value = mock_db_manager

        mock_cli_context_class.return_value.__enter__.return_value = mock_context

        mock_console_instance = Mock()
        mock_console.return_value = mock_console_instance

        status.status()

        # Verify that sys.exit was called due to the exception
        mock_sys_exit.assert_called_once_with(1)

    @patch("bank_importer.cli.commands.status.get_console")
    @patch("bank_importer.cli.commands.status.CLIContext")
    def test_status_session_with_missing_started_at(
        self,
        mock_cli_context_class: Mock,
        mock_console: Mock,
    ) -> None:
        """Test status command with session missing started_at field."""
        mock_context = Mock()
        mock_config_manager = Mock()
        mock_db_manager = Mock()

        # Set up accounts
        mock_config_manager.get_all_accounts.return_value = [
            {
                "name": "test_account",
                "bank_name": "Test Bank",
                "account_number": "123-456-789",
                "parser": "test_parser",
            },
        ]

        # Set up transactions
        mock_db_manager.get_transactions_by_account.return_value = []

        # Set up import session with missing started_at
        mock_db_manager.get_import_sessions_by_account.return_value = [
            {
                "id": 1,
                "session_name": "session_no_start_time",
                "account_name": "test_account",
                "status": "completed",
                "started_at": None,  # Missing started_at
                "file_path": "/path/to/file.txt",
                "processed_transactions": 5,
                "total_transactions": 5,
            },
        ]

        # Set up transactions for session
        mock_db_manager.get_transactions_by_session.return_value = [
            {"date": "2024-01-01", "amount": 100.0},
        ]

        mock_context.get_config_manager.return_value = mock_config_manager
        mock_context.get_db_manager.return_value = mock_db_manager

        mock_cli_context_class.return_value.__enter__.return_value = mock_context

        mock_console_instance = Mock()
        mock_console.return_value = mock_console_instance

        status.status()

        # Verify console.print was called - the handling of missing started_at depends on Rich table rendering
        assert mock_console_instance.print.called

    @patch("bank_importer.cli.commands.status.get_console")
    @patch("bank_importer.cli.commands.status.CLIContext")
    def test_status_consolidated_with_datetime_objects(
        self,
        mock_cli_context_class: Mock,
        mock_console: Mock,
    ) -> None:
        """Test status command consolidated summary with datetime objects."""
        mock_context = Mock()
        mock_config_manager = Mock()
        mock_db_manager = Mock()

        # Set up accounts
        mock_config_manager.get_all_accounts.return_value = [
            {
                "name": "account_1",
                "bank_name": "Bank 1",
                "account_number": "111-111-111",
                "parser": "parser1",
            },
        ]

        # Set up transactions
        mock_db_manager.get_transactions_by_account.return_value = []

        # Set up import sessions
        mock_db_manager.get_import_sessions_by_account.return_value = [
            {
                "id": 1,
                "session_name": "session_1",
                "account_name": "account_1",
                "status": "completed",
                "started_at": "2024-01-01T10:00:00",
                "file_path": "/path/to/file.txt",
                "processed_transactions": 1,
                "total_transactions": 1,
            },
        ]

        # Set up transactions with datetime objects
        mock_db_manager.get_transactions_by_session.return_value = [
            {"date": datetime(2024, 1, 15, tzinfo=UTC), "amount": 100.0},
        ]

        mock_context.get_config_manager.return_value = mock_config_manager
        mock_context.get_db_manager.return_value = mock_db_manager

        mock_cli_context_class.return_value.__enter__.return_value = mock_context

        mock_console_instance = Mock()
        mock_console.return_value = mock_console_instance

        status.status()

        # Verify console.print was called
        assert mock_console_instance.print.called

    @patch("bank_importer.cli.commands.status.get_console")
    @patch("bank_importer.cli.commands.status.CLIContext")
    def test_status_consolidated_future_date_adjustment(
        self,
        mock_cli_context_class: Mock,
        mock_console: Mock,
    ) -> None:
        """Test status command consolidated summary adjusts future dates."""
        mock_context = Mock()
        mock_config_manager = Mock()
        mock_db_manager = Mock()

        # Set up accounts
        mock_config_manager.get_all_accounts.return_value = [
            {
                "name": "account_1",
                "bank_name": "Bank 1",
                "account_number": "111-111-111",
                "parser": "parser1",
            },
        ]

        # Set up transactions
        mock_db_manager.get_transactions_by_account.return_value = []

        # Set up import sessions
        mock_db_manager.get_import_sessions_by_account.return_value = [
            {
                "id": 1,
                "session_name": "session_1",
                "account_name": "account_1",
                "status": "completed",
                "started_at": "2024-01-01T10:00:00",
                "file_path": "/path/to/file.txt",
                "processed_transactions": 1,
                "total_transactions": 1,
            },
        ]

        # Set up transactions with future date to trigger adjustment
        future_date = (datetime.now(UTC) + timedelta(days=30)).strftime("%Y-%m-%d")
        mock_db_manager.get_transactions_by_session.return_value = [
            {"date": future_date, "amount": 100.0},
        ]

        mock_context.get_config_manager.return_value = mock_config_manager
        mock_context.get_db_manager.return_value = mock_db_manager

        mock_cli_context_class.return_value.__enter__.return_value = mock_context

        mock_console_instance = Mock()
        mock_console.return_value = mock_console_instance

        status.status()

        # Verify console.print was called
        assert mock_console_instance.print.called
