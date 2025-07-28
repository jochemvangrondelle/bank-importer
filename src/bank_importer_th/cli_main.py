"""Command-line interface for the bank importer."""

import typer

from .cli.commands import (
    clean,
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


def main() -> None:
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()
