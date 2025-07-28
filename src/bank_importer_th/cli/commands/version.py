"""Version command for the bank importer CLI."""

from ...cli_utils import cli_error_handler
from ...logging_config import get_console
from ...version import format_version, get_version_info


@cli_error_handler
def version() -> None:
    """**Show** version information."""
    console = get_console()

    version_info = get_version_info()

    console.print(f"🏦 Bank Importer v{format_version()}")
    console.print(f"📦 Version: {version_info['version']}")
    console.print(f"🔢 Major: {version_info['major']}")
    console.print(f"🔢 Minor: {version_info['minor']}")
    console.print(f"🔢 Patch: {version_info['patch']}")
    console.print(f"🚀 Release: {'Yes' if version_info['is_release'] else 'No'}")
