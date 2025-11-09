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

"""Version management utilities."""

import os
from typing import Any

from bank_importer import __version__


def get_version() -> str:
    """Get the current version from package."""
    return __version__


def get_version_info() -> dict[str, Any]:
    """Get detailed version information."""
    version = get_version()

    # Parse version components (handle versions like "1.2.3-dev" or "1.2.3-prerelease.1")
    # Split on "-" first to separate version from suffix
    version_part = version.split("-")[0]
    parts = version_part.split(".")
    major = int(parts[0]) if len(parts) > 0 else 0
    minor = int(parts[1]) if len(parts) > 1 else 0
    patch_str = parts[2] if len(parts) > 2 else "0"
    # Handle patch versions that might have non-numeric suffixes
    patch = int(patch_str.split("-")[0]) if patch_str.split("-")[0].isdigit() else 0

    return {
        "version": version,
        "major": major,
        "minor": minor,
        "patch": patch,
        "is_release": "dev" not in version and "prerelease" not in version,
    }


def format_version() -> str:
    """Format version for CLI display."""
    version_info = get_version_info()
    version = version_info["version"]

    # Add build info if available
    build_info = []

    # Git commit info
    git_commit = os.environ.get("GIT_COMMIT")
    if git_commit:
        build_info.append(f"commit:{git_commit[:8]}")

    # Build date
    build_date = os.environ.get("BUILD_DATE")
    if build_date:
        build_info.append(f"build:{build_date}")

    if build_info:
        return f"{version} ({', '.join(build_info)})"

    return str(version)
