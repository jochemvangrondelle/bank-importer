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

"""Tests for API dependencies."""

from pathlib import Path

import pytest

from bank_importer.api.dependencies import (
    get_config_manager,
    get_db_manager,
    get_parser_detector,
    get_processor,
)


class TestDependencies:
    """Tests for dependency injection functions."""

    @pytest.mark.parametrize(
        "config_file",
        [
            "config.toml",
            "custom_config.toml",
        ],
    )
    def test_get_config_manager(self, tmp_path: Path, config_file: str) -> None:
        """Test getting ConfigManager instance."""
        config_path = tmp_path / config_file
        config_path.write_text("[app]\ntimezone = 'UTC'")
        manager = get_config_manager(str(config_path))
        assert manager is not None
        assert manager.config_path == config_path

    def test_get_db_manager(self, tmp_path: Path) -> None:
        """Test getting DatabaseManager instance."""
        config_path = tmp_path / "config.toml"
        config_path.write_text(
            "[app]\ntimezone = 'UTC'\n[database]\nurl = 'sqlite:///test.db'",
        )
        config_manager = get_config_manager(str(config_path))
        db_manager = get_db_manager(config_manager)
        assert db_manager is not None

    def test_get_parser_detector(self) -> None:
        """Test getting ParserDetector instance."""
        detector = get_parser_detector()
        assert detector is not None
        assert len(detector.parsers) > 0

    def test_get_processor(self, tmp_path: Path) -> None:
        """Test getting Processor instance."""
        config_path = tmp_path / "config.toml"
        config_path.write_text(
            "[app]\ntimezone = 'UTC'\n[database]\nurl = 'sqlite:///test.db'",
        )
        config_manager = get_config_manager(str(config_path))
        db_manager = get_db_manager(config_manager)
        processor = get_processor(config_manager, db_manager)
        assert processor is not None
