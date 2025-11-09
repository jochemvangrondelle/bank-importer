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

"""Tests for CLI list-parsers command."""

from unittest.mock import MagicMock, patch

from bank_importer.cli.commands import list_parsers


class TestListParsersCommand:
    """Tests for list-parsers command."""

    @patch("bank_importer.cli.commands.list_parsers.get_console")
    @patch("bank_importer.cli.commands.list_parsers.ParserDetector")
    def test_list_parsers_basic(self, mock_parser_detector_class, mock_console) -> None:
        """Test list-parsers command basic functionality."""
        mock_detector = MagicMock()
        mock_detector.list_available_parsers.return_value = [
            "amex_th_csv",
            "generic_csv",
            "krungsri_pdf",
        ]
        mock_parser_detector_class.return_value = mock_detector
        mock_console_instance = mock_console.return_value

        list_parsers.list_parsers()

        mock_parser_detector_class.assert_called_once()
        mock_detector.list_available_parsers.assert_called_once()
        mock_console_instance.print.assert_called()

    @patch("bank_importer.cli.commands.list_parsers.get_console")
    @patch("bank_importer.cli.commands.list_parsers.ParserDetector")
    def test_list_parsers_creates_table(
        self, mock_parser_detector_class, mock_console
    ) -> None:
        """Test list-parsers creates a table."""
        mock_detector = MagicMock()
        mock_detector.list_available_parsers.return_value = ["generic_csv"]
        mock_parser_detector_class.return_value = mock_detector
        mock_console_instance = mock_console.return_value

        with patch("bank_importer.cli.commands.list_parsers.Table") as mock_table_class:
            mock_table = MagicMock()
            mock_table_class.return_value = mock_table

            list_parsers.list_parsers()

            # Should create table with correct title
            mock_table_class.assert_called_once()
            call_kwargs = mock_table_class.call_args[1]
            assert call_kwargs["title"] == "🔧 Available Parsers"

            # Should add columns
            assert mock_table.add_column.call_count >= 4

            # Should add rows
            assert mock_table.add_row.called

            # Should print table
            mock_console_instance.print.assert_called()

    @patch("bank_importer.cli.commands.list_parsers.get_console")
    @patch("bank_importer.cli.commands.list_parsers.ParserDetector")
    def test_list_parsers_shows_summary(
        self, mock_parser_detector_class, mock_console
    ) -> None:
        """Test list-parsers shows summary."""
        mock_detector = MagicMock()
        mock_detector.list_available_parsers.return_value = [
            "amex_th_csv",
            "krungsri_pdf",
            "generic_csv",
        ]
        mock_parser_detector_class.return_value = mock_detector
        mock_console_instance = mock_console.return_value

        list_parsers.list_parsers()

        # Should print summary
        calls = [str(call) for call in mock_console_instance.print.call_args_list]
        assert any(
            "Summary" in str(call) or "total parsers" in str(call) for call in calls
        )

    @patch("bank_importer.cli.commands.list_parsers.get_console")
    @patch("bank_importer.cli.commands.list_parsers.ParserDetector")
    def test_list_parsers_shows_usage_hints(
        self, mock_parser_detector_class, mock_console
    ) -> None:
        """Test list-parsers shows usage hints."""
        mock_detector = MagicMock()
        mock_detector.list_available_parsers.return_value = ["generic_csv"]
        mock_parser_detector_class.return_value = mock_detector
        mock_console_instance = mock_console.return_value

        list_parsers.list_parsers()

        # Should print usage hints
        calls = [str(call) for call in mock_console_instance.print.call_args_list]
        assert any("Usage" in str(call) or "Usage:" in str(call) for call in calls)

    @patch("bank_importer.cli.commands.list_parsers.get_console")
    @patch("bank_importer.cli.commands.list_parsers.ParserDetector")
    def test_list_parsers_with_unknown_parser(
        self, mock_parser_detector_class, mock_console
    ) -> None:
        """Test list-parsers handles unknown parsers."""
        mock_detector = MagicMock()
        mock_detector.list_available_parsers.return_value = ["unknown_parser"]
        mock_parser_detector_class.return_value = mock_detector
        mock_console_instance = mock_console.return_value

        with patch("bank_importer.cli.commands.list_parsers.Table") as mock_table_class:
            mock_table = MagicMock()
            mock_table_class.return_value = mock_table

            list_parsers.list_parsers()

            # Should still add row for unknown parser
            assert mock_table.add_row.called
