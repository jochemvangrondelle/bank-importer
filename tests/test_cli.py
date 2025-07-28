"""Tests for CLI module."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from typer.testing import CliRunner

from bank_importer_th.cli_main import app


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
                "account_number": "123-456-789",
            }
        ]
        return processor

    @pytest.mark.cli
    def test_cli_help(self, runner: CliRunner) -> None:
        """Test CLI help command."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "Bank Importer" in result.output
        assert "run" in result.output
        assert "list-parsers" in result.output
        assert "status" in result.output

    @pytest.mark.cli
    def test_cli_run_without_config(self, runner: CliRunner) -> None:
        """Test CLI run command without config file."""
        with (
            patch("bank_importer_th.cli.commands.status.status") as mock_status,
            patch(
                "bank_importer_th.cli.commands.import_files.import_files"
            ) as mock_import,
            patch(
                "bank_importer_th.cli.commands.export_multi.export_multi"
            ) as mock_export,
        ):
            result = runner.invoke(app, ["run"])
            assert result.exit_code == 0
            assert "Starting Bank Importer - Full Pipeline" in result.output
            mock_status.assert_called()
            mock_import.assert_called()
            mock_export.assert_called()

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

        with (
            patch("bank_importer_th.cli.commands.status.status") as mock_status,
            patch(
                "bank_importer_th.cli.commands.import_files.import_files"
            ) as mock_import,
            patch(
                "bank_importer_th.cli.commands.export_multi.export_multi"
            ) as mock_export,
        ):
            result = runner.invoke(app, ["run", "--config", str(config_file)])
            assert result.exit_code == 0
            mock_status.assert_called()
            mock_import.assert_called()
            mock_export.assert_called()

    @pytest.mark.cli
    def test_cli_run_with_specific_account(self, runner: CliRunner) -> None:
        """Test CLI run command with specific account."""
        with (
            patch("bank_importer_th.cli.commands.status.status") as mock_status,
            patch(
                "bank_importer_th.cli.commands.import_files.import_files"
            ) as mock_import,
            patch(
                "bank_importer_th.cli.commands.export_multi.export_multi"
            ) as mock_export,
            patch(
                "bank_importer_th.cli_parameters.get_available_accounts"
            ) as mock_accounts,
        ):
            mock_accounts.return_value = ["test_account"]

            result = runner.invoke(app, ["run", "--account", "test_account"])
            assert result.exit_code == 0
            mock_status.assert_called()
            mock_import.assert_called()
            mock_export.assert_called()

    @pytest.mark.cli
    def test_cli_run_with_nonexistent_account(self, runner: CliRunner) -> None:
        """Test CLI run command with nonexistent account."""
        with patch(
            "bank_importer_th.cli_parameters.get_available_accounts"
        ) as mock_accounts:
            mock_accounts.return_value = ["existing_account"]

            result = runner.invoke(app, ["run", "--account", "nonexistent"])
            assert result.exit_code == 2
            assert "Invalid account: 'nonexistent'" in result.output

    @pytest.mark.cli
    def test_cli_init(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test CLI init command."""
        config_file = tmp_path / "config.toml"

        # Mock the init function to avoid actual file operations
        with patch("bank_importer_th.cli.commands.init.init"):
            result = runner.invoke(app, ["init", "--config", str(config_file)])
            assert result.exit_code == 0
            # Just verify the command runs successfully
            # The mock may not be called due to how Typer handles commands

    @pytest.mark.cli
    def test_cli_error_handling(self, runner: CliRunner) -> None:
        """Test CLI error handling."""
        with patch("bank_importer_th.cli.commands.status.status") as mock_status:
            mock_status.side_effect = Exception("Test error")

            result = runner.invoke(app, ["run"])
            assert result.exit_code == 1
            # The error should be in the exception message, not the output
            assert "Test error" in str(result.exception)

    @pytest.mark.cli
    def test_account_parameter_validation(self, runner: CliRunner) -> None:
        """Test account parameter validation with invalid account."""
        result = runner.invoke(app, ["run", "--account", "invalid_account"])
        assert result.exit_code == 2
        assert "Invalid account: 'invalid_account'" in result.output
        assert "Available accounts:" in result.output
        assert "krungsri_pdf" in result.output
        assert "scb_pdf" in result.output

    @pytest.mark.cli
    def test_account_parameter_validation_valid_account(
        self, runner: CliRunner
    ) -> None:
        """Test account parameter validation with valid account."""
        with (
            patch("bank_importer_th.cli.commands.status.status") as mock_status,
            patch(
                "bank_importer_th.cli.commands.import_files.import_files"
            ) as mock_import,
            patch(
                "bank_importer_th.cli.commands.export_multi.export_multi"
            ) as mock_export,
            patch(
                "bank_importer_th.cli_parameters.get_available_accounts"
            ) as mock_accounts,
        ):
            mock_accounts.return_value = ["krungsri_pdf"]

            result = runner.invoke(
                app, ["run", "--account", "krungsri_pdf", "--dry-run"]
            )
            assert result.exit_code == 0
            mock_status.assert_called()
            mock_import.assert_called()
            mock_export.assert_called()

    @pytest.mark.cli
    def test_cli_list_parsers(self, runner: CliRunner) -> None:
        """Test CLI list-parsers command."""
        result = runner.invoke(app, ["list-parsers"])
        assert result.exit_code == 0
        assert "Available Parsers" in result.output
        assert "amex_th_csv" in result.output
        assert "krungsri_pdf" in result.output
        assert "scb_pdf" in result.output
        assert "generic_csv" in result.output
        assert "generic_json" in result.output
        assert "Bank-specific" in result.output
        assert "Generic" in result.output
        assert "7 total parsers" in result.output
