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

"""Version command for the bank importer CLI."""

import os

from bank_importer.cli.utils import cli_error_handler
from bank_importer.logging_config import get_console
from bank_importer.version import format_version, get_version_info


@cli_error_handler
def version() -> None:
    """**Show** version information."""
    console = get_console()

    version_info = get_version_info()

    # Get version from package
    version_str = format_version()

    # Check if running in Docker
    docker_version = os.environ.get("APP_VERSION")
    if docker_version:
        version_str = docker_version

    console.print(f"🏦 Bank Importer v{version_str}")
    console.print(f"📦 Version: {version_info['version']}")
    console.print(f"🔢 Major: {version_info['major']}")
    console.print(f"🔢 Minor: {version_info['minor']}")
    console.print(f"🔢 Patch: {version_info['patch']}")
    console.print(f"🚀 Release: {'Yes' if version_info['is_release'] else 'No'}")

    # Show additional info if available
    git_commit = os.environ.get("GIT_COMMIT") or os.environ.get("GITHUB_SHA")
    if git_commit:
        console.print(f"🔖 Commit: {git_commit[:8]}")

    build_date = os.environ.get("BUILD_DATE")
    if build_date:
        console.print(f"📅 Build: {build_date}")
