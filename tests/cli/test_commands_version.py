# Copyright (C) 2025 Jochem van Grondelle <jochem@vangrondelle.net>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the PolyForm Noncommercial License 1.0.0.
# You may not use this program except in compliance with the License.
# A copy of the License is available at https://polyformproject.org/licenses/noncommercial/1.0.0/
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# PolyForm Noncommercial License 1.0.0 for more details.

"""Tests for CLI version command."""

import os
from unittest.mock import patch

import pytest

from bank_importer.cli.commands import version


class TestVersionCommand:
    """Tests for version command."""

    @patch("bank_importer.cli.commands.version.get_console")
    @patch("bank_importer.cli.commands.version.get_version_info")
    @patch("bank_importer.cli.commands.version.format_version")
    def test_version_basic(
        self, mock_format_version, mock_get_version_info, mock_console
    ) -> None:
        """Test version command with basic output."""
        mock_format_version.return_value = "0.1.0"
        mock_get_version_info.return_value = {
            "version": "0.1.0",
            "major": 0,
            "minor": 1,
            "patch": 0,
            "is_release": True,
        }
        mock_console_instance = mock_console.return_value

        version.version()

        mock_console_instance.print.assert_called()
        assert mock_format_version.called
        assert mock_get_version_info.called

    @patch("bank_importer.cli.commands.version.get_console")
    @patch("bank_importer.cli.commands.version.get_version_info")
    @patch("bank_importer.cli.commands.version.format_version")
    @patch.dict(os.environ, {"APP_VERSION": "1.2.3-docker"})
    def test_version_with_docker_version(
        self, mock_format_version, mock_get_version_info, mock_console
    ) -> None:
        """Test version command with Docker version."""
        mock_format_version.return_value = "0.1.0"
        mock_get_version_info.return_value = {
            "version": "0.1.0",
            "major": 0,
            "minor": 1,
            "patch": 0,
            "is_release": True,
        }
        mock_console_instance = mock_console.return_value

        version.version()

        # Should use Docker version instead of formatted version
        mock_console_instance.print.assert_called()
        calls = [str(call) for call in mock_console_instance.print.call_args_list]
        assert any("1.2.3-docker" in str(call) for call in calls)

    @patch("bank_importer.cli.commands.version.get_console")
    @patch("bank_importer.cli.commands.version.get_version_info")
    @patch("bank_importer.cli.commands.version.format_version")
    @patch.dict(os.environ, {"GIT_COMMIT": "abc123def456"})
    def test_version_with_git_commit(
        self, mock_format_version, mock_get_version_info, mock_console
    ) -> None:
        """Test version command with Git commit."""
        mock_format_version.return_value = "0.1.0"
        mock_get_version_info.return_value = {
            "version": "0.1.0",
            "major": 0,
            "minor": 1,
            "patch": 0,
            "is_release": False,
        }
        mock_console_instance = mock_console.return_value

        version.version()

        mock_console_instance.print.assert_called()
        calls = [str(call) for call in mock_console_instance.print.call_args_list]
        assert any("abc123de" in str(call) for call in calls)

    @patch("bank_importer.cli.commands.version.get_console")
    @patch("bank_importer.cli.commands.version.get_version_info")
    @patch("bank_importer.cli.commands.version.format_version")
    @patch.dict(os.environ, {"GITHUB_SHA": "xyz789"})
    def test_version_with_github_sha(
        self, mock_format_version, mock_get_version_info, mock_console
    ) -> None:
        """Test version command with GitHub SHA."""
        mock_format_version.return_value = "0.1.0"
        mock_get_version_info.return_value = {
            "version": "0.1.0",
            "major": 0,
            "minor": 1,
            "patch": 0,
            "is_release": False,
        }
        mock_console_instance = mock_console.return_value

        version.version()

        mock_console_instance.print.assert_called()
        calls = [str(call) for call in mock_console_instance.print.call_args_list]
        assert any("xyz789" in str(call) for call in calls)

    @patch("bank_importer.cli.commands.version.get_console")
    @patch("bank_importer.cli.commands.version.get_version_info")
    @patch("bank_importer.cli.commands.version.format_version")
    @patch.dict(os.environ, {"BUILD_DATE": "2025-01-15"})
    def test_version_with_build_date(
        self, mock_format_version, mock_get_version_info, mock_console
    ) -> None:
        """Test version command with build date."""
        mock_format_version.return_value = "0.1.0"
        mock_get_version_info.return_value = {
            "version": "0.1.0",
            "major": 0,
            "minor": 1,
            "patch": 0,
            "is_release": True,
        }
        mock_console_instance = mock_console.return_value

        version.version()

        mock_console_instance.print.assert_called()
        calls = [str(call) for call in mock_console_instance.print.call_args_list]
        assert any("2025-01-15" in str(call) for call in calls)

    @patch("bank_importer.cli.commands.version.get_console")
    @patch("bank_importer.cli.commands.version.get_version_info")
    @patch("bank_importer.cli.commands.version.format_version")
    def test_version_with_all_info(
        self, mock_format_version, mock_get_version_info, mock_console
    ) -> None:
        """Test version command with all optional info."""
        mock_format_version.return_value = "0.1.0"
        mock_get_version_info.return_value = {
            "version": "0.1.0",
            "major": 0,
            "minor": 1,
            "patch": 0,
            "is_release": False,
        }
        mock_console_instance = mock_console.return_value

        with patch.dict(
            os.environ,
            {
                "APP_VERSION": "1.0.0-docker",
                "GIT_COMMIT": "abc123",
                "BUILD_DATE": "2025-01-15",
            },
        ):
            version.version()

        mock_console_instance.print.assert_called()
        assert mock_console_instance.print.call_count >= 5  # Multiple print calls
