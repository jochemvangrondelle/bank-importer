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

"""Command-line interface for the bank importer."""

try:
    import typer
except ImportError as e:
    msg = "CLI dependencies not installed. Install with: uv sync --group cli"
    raise ImportError(
        msg,
    ) from e

from bank_importer.cli.commands import (
    clean,
    configure,
    coverage,
    export_multi,
    import_files,
    init,
    list_parsers,
    run,
    status,
    translate,
    version,
)

app = typer.Typer(
    help="**Bank Importer**\n\nA Python application to import bank statements and export transactions to various targets.",
    rich_markup_mode="markdown",
    no_args_is_help=True,
    invoke_without_command=True,
)

# Register commands
app.command()(init.init)
app.command()(status.status)
app.command()(import_files.import_files)
app.command(name="export")(export_multi.export_multi)
app.command()(translate.translate)
app.command()(coverage.coverage)
app.command()(run.run)
app.command()(clean.clean)
app.command()(version.version)
app.command()(list_parsers.list_parsers)
app.command()(configure.configure)


def main() -> None:
    """Run the CLI application."""
    app()
