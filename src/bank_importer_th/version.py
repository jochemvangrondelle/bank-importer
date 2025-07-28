"""Version management utilities."""

import os


def get_version() -> str:
    """Get the current version from package."""
    from . import __version__

    return __version__


def get_version_info() -> dict:
    """Get detailed version information."""
    version = get_version()

    # Parse version components
    parts = version.split(".")
    major = int(parts[0]) if len(parts) > 0 else 0
    minor = int(parts[1]) if len(parts) > 1 else 0
    patch = int(parts[2]) if len(parts) > 2 else 0

    return {
        "version": version,
        "major": major,
        "minor": minor,
        "patch": patch,
        "is_release": "dev" not in version
        and "alpha" not in version
        and "beta" not in version,
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

    return version
