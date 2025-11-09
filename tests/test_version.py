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

"""Tests for version management."""

import os
from unittest.mock import patch

import pytest

from bank_importer.version import format_version, get_version, get_version_info


class TestVersion:
    """Test version management functionality."""

    def test_get_version(self) -> None:
        """Test getting version."""
        version = get_version()
        assert isinstance(version, str)
        assert len(version) > 0

    def test_get_version_info(self) -> None:
        """Test getting version info."""
        info = get_version_info()
        assert "version" in info
        assert "major" in info
        assert "minor" in info
        assert "patch" in info
        assert "is_release" in info
        assert isinstance(info["major"], int)
        assert isinstance(info["minor"], int)
        assert isinstance(info["patch"], int)
        assert isinstance(info["is_release"], bool)

    @pytest.mark.parametrize(
        ("version_string", "expected_major", "expected_minor", "expected_patch"),
        [
            ("1.2.3", 1, 2, 3),
            ("0.1.0", 0, 1, 0),
            ("10.20.30", 10, 20, 30),
        ],
    )
    def test_get_version_info_parsing(
        self,
        version_string: str,
        expected_major: int,
        expected_minor: int,
        expected_patch: int,
    ) -> None:
        """Test version info parsing."""
        with patch("bank_importer.version.get_version", return_value=version_string):
            info = get_version_info()
            assert info["major"] == expected_major
            assert info["minor"] == expected_minor
            assert info["patch"] == expected_patch

    @pytest.mark.parametrize(
        ("version_string", "expected_release"),
        [
            ("1.2.3", True),
            ("1.2.3-dev", False),
            ("1.2.3-prerelease.1", False),
            ("0.1.0", True),
        ],
    )
    def test_get_version_info_release_status(
        self,
        version_string: str,
        expected_release: bool,
    ) -> None:
        """Test version info release status."""
        with patch("bank_importer.version.__version__", version_string):
            info = get_version_info()
            assert info["is_release"] == expected_release

    def test_format_version_basic(self) -> None:
        """Test formatting version without build info."""
        with patch.dict(os.environ, {}, clear=True):
            version = format_version()
            assert isinstance(version, str)
            assert len(version) > 0

    def test_format_version_with_git_commit(self) -> None:
        """Test formatting version with git commit."""
        with patch.dict(os.environ, {"GIT_COMMIT": "abc123def456"}):
            version = format_version()
            assert "commit:abc123de" in version

    def test_format_version_with_build_date(self) -> None:
        """Test formatting version with build date."""
        with patch.dict(os.environ, {"BUILD_DATE": "2024-01-01"}):
            version = format_version()
            assert "build:2024-01-01" in version

    def test_format_version_with_all_build_info(self) -> None:
        """Test formatting version with all build info."""
        with patch.dict(
            os.environ,
            {"GIT_COMMIT": "abc123def456", "BUILD_DATE": "2024-01-01"},
        ):
            version = format_version()
            assert "commit:abc123de" in version
            assert "build:2024-01-01" in version
