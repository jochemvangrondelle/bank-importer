"""Tests for CLI module."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from bank_importer_th.cli import cli


class TestCLI:
    """Test CLI functionality."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create a CLI runner for testing."""
        return CliRunner()

    @pytest.fixture
    def mock_processor(self) -> Mock:
        """Create a mock processor."""
        processor = Mock()
        processor.config_manager.get_all_accounts.return_value = [
            {
                "name": "test_account",
                "bank_name": "Test Bank",
                "account_number": "123-456-789"
            }
        ]
        return processor

    @pytest.mark.cli
    def test_cli_help(self, runner: CliRunner) -> None:
        """Test CLI help command."""
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Bank Importer Thailand" in result.output
        assert "run" in result.output
        assert "list-accounts" in result.output
        assert "list-sessions" in result.output

    @pytest.mark.cli
    def test_cli_run_without_config(self, runner: CliRunner) -> None:
        """Test CLI run command without config file."""
        with patch("bank_importer_th.cli.Processor") as mock_processor_class:
            mock_processor = Mock()
            mock_processor_class.return_value = mock_processor
            mock_processor.process_accounts.return_value = []

            result = runner.invoke(cli, ["run"])
            assert result.exit_code == 0
            assert "Processing all accounts" in result.output

    @pytest.mark.cli
    def test_cli_run_with_config(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test CLI run command with config file."""
        config_file = tmp_path / "config.toml"
        config_file.write_text("""
[[accounts]]
name = "test_account"
parser = "test_parser"
file_path = "test/path"
""")

        with patch("bank_importer_th.cli.Processor") as mock_processor_class:
            mock_processor = Mock()
            mock_processor_class.return_value = mock_processor
            mock_processor.process_accounts.return_value = []

            result = runner.invoke(cli, ["run", "--config", str(config_file)])
            assert result.exit_code == 0
            mock_processor_class.assert_called_once_with(config_file)

    @pytest.mark.cli
    def test_cli_run_with_specific_account(self, runner: CliRunner) -> None:
        """Test CLI run command with specific account."""
        with patch("bank_importer_th.cli.Processor") as mock_processor_class:
            mock_processor = Mock()
            mock_processor_class.return_value = mock_processor
            mock_processor.config_manager.get_account_config.return_value = {
                "name": "test_account",
                "parser": "test_parser"
            }
            mock_processor.process_account.return_value = []

            result = runner.invoke(cli, ["run", "--account", "test_account"])
            assert result.exit_code == 0
            assert "Processing account: test_account" in result.output

    @pytest.mark.cli
    def test_cli_run_with_nonexistent_account(self, runner: CliRunner) -> None:
        """Test CLI run command with nonexistent account."""
        with patch("bank_importer_th.cli.Processor") as mock_processor_class:
            mock_processor = Mock()
            mock_processor_class.return_value = mock_processor
            mock_processor.config_manager.get_account_config.return_value = None

            result = runner.invoke(cli, ["run", "--account", "nonexistent"])
            assert result.exit_code == 0
            assert "Account 'nonexistent' not found" in result.output

    @pytest.mark.cli
    def test_cli_list_accounts(self, runner: CliRunner) -> None:
        """Test CLI list-accounts command."""
        with patch("bank_importer_th.cli.Processor") as mock_processor_class:
            mock_processor = Mock()
            mock_processor_class.return_value = mock_processor
            mock_processor.config_manager.get_all_accounts.return_value = [
                {
                    "name": "account1",
                    "bank_name": "Bank 1",
                    "account_number": "123-456"
                },
                {
                    "name": "account2",
                    "bank_name": "Bank 2",
                    "account_number": "789-012"
                }
            ]

            result = runner.invoke(cli, ["list-accounts"])
            assert result.exit_code == 0
            assert "account1: Bank 1 (123-456)" in result.output
            assert "account2: Bank 2 (789-012)" in result.output

    @pytest.mark.cli
    def test_cli_list_accounts_empty(self, runner: CliRunner) -> None:
        """Test CLI list-accounts command with no accounts."""
        with patch("bank_importer_th.cli.Processor") as mock_processor_class:
            mock_processor = Mock()
            mock_processor_class.return_value = mock_processor
            mock_processor.config_manager.get_all_accounts.return_value = []

            result = runner.invoke(cli, ["list-accounts"])
            assert result.exit_code == 0
            assert "No accounts configured" in result.output

    @pytest.mark.cli
    def test_cli_list_sessions(self, runner: CliRunner) -> None:
        """Test CLI list-sessions command."""
        with patch("bank_importer_th.cli.Processor") as mock_processor_class:
            mock_processor = Mock()
            mock_processor_class.return_value = mock_processor
            mock_processor.config_manager.get_all_accounts.return_value = [
                {"name": "test_account"}
            ]
            mock_processor.db_manager.get_import_sessions_by_account.return_value = [
                {
                    "session_name": "2024-01",
                    "account_name": "test_account",
                    "status": "completed",
                    "file_path": "/path/to/file.txt",
                    "processed_transactions": 10,
                    "total_transactions": 10,
                    "error_count": 0,
                    "created_at": "2024-01-01T00:00:00"
                }
            ]

            result = runner.invoke(cli, ["list-sessions"])
            assert result.exit_code == 0
            assert "✅ 2024-01 (test_account) - completed" in result.output

    @pytest.mark.cli
    def test_cli_list_sessions_empty(self, runner: CliRunner) -> None:
        """Test CLI list-sessions command with no sessions."""
        with patch("bank_importer_th.cli.Processor") as mock_processor_class:
            mock_processor = Mock()
            mock_processor_class.return_value = mock_processor
            mock_processor.config_manager.get_all_accounts.return_value = [
                {"name": "test_account"}
            ]
            mock_processor.db_manager.get_import_sessions_by_account.return_value = []

            result = runner.invoke(cli, ["list-sessions"])
            assert result.exit_code == 0
            assert "No import sessions found" in result.output

    @pytest.mark.cli
    def test_cli_init(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test CLI init command."""
        config_file = tmp_path / "config.toml"

        with patch("bank_importer_th.cli.Processor") as mock_processor_class:
            mock_processor = Mock()
            mock_processor_class.return_value = mock_processor
            mock_processor.config_manager.config_path = config_file

            result = runner.invoke(cli, ["init", "--config", str(config_file)])
            assert result.exit_code == 0
            assert f"Configuration saved to {config_file}" in result.output

    @pytest.mark.cli
    def test_cli_error_handling(self, runner: CliRunner) -> None:
        """Test CLI error handling."""
        with patch("bank_importer_th.cli.Processor") as mock_processor_class:
            mock_processor_class.side_effect = Exception("Test error")

            result = runner.invoke(cli, ["run"])
            assert result.exit_code == 1
            assert "Error: Test error" in result.output
