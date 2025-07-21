"""CLI interface for bank importer."""

from pathlib import Path

import click

from .processor import Processor


@click.group()
def cli() -> None:
    """Bank Importer Thailand - Convert bank statements to structured data."""
    pass


@cli.command()
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True, path_type=Path),
    help="Path to configuration file (default: config.toml)",
)
@click.option("--account", "-a", help="Process specific account only")
def run(config: Path, account: str) -> None:
    """Run the bank importer pipeline."""
    try:
        processor = Processor(config)

        if account:
            # Process specific account
            account_config = processor.config_manager.get_account_config(account)
            if not account_config:
                click.echo(f"Account '{account}' not found in configuration")
                return

            click.echo(f"Processing account: {account}")
            transactions = list(processor.process_account(account))
        else:
            # Process all accounts
            click.echo("Processing all accounts...")
            transactions = list(processor.process_accounts())

        click.echo(f"Processed {len(transactions)} account results")

        # Show summary
        if transactions:
            total_processed = sum(t.get("processed_transactions", 0) for t in transactions)
            total_errors = sum(t.get("error_count", 0) for t in transactions)
            click.echo(f"Total transactions processed: {total_processed}")
            if total_errors > 0:
                click.echo(f"Total errors: {total_errors}")

            # Show account results
            click.echo("\nAccount results:")
            for result in transactions:
                status = "✅" if result.get("error_count", 0) == 0 else "❌"
                click.echo(
                    f"  {status} {result['account_name']}: {result.get('processed_transactions', 0)} transactions"
                )
                if result.get("error_message"):
                    click.echo(f"    Error: {result['error_message']}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort() from e


@cli.command()
@click.option(
    "--config", "-c", type=click.Path(path_type=Path), help="Path to configuration file (default: config.toml)"
)
def init(config: Path) -> None:
    """Initialize configuration file."""
    try:
        processor = Processor(config)
        processor.config_manager.save_config()
        click.echo(f"Configuration saved to {processor.config_manager.config_path}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort() from e


@cli.command()
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True, path_type=Path),
    help="Path to configuration file (default: config.toml)",
)
def list_accounts(config: Path) -> None:
    """List configured accounts."""
    try:
        processor = Processor(config)
        accounts = processor.config_manager.get_all_accounts()

        if not accounts:
            click.echo("No accounts configured")
            return

        click.echo("Configured accounts:")
        for account in accounts:
            click.echo(f"  {account['name']}: {account['bank_name']} ({account['account_number']})")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort() from e


@cli.command()
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True, path_type=Path),
    help="Path to configuration file (default: config.toml)",
)
@click.option("--account", "-a", help="Show sessions for specific account only")
def list_sessions(config: Path, account: str) -> None:
    """List import sessions."""
    try:
        processor = Processor(config)

        if account:
            sessions = processor.db_manager.get_import_sessions_by_account(account)
        else:
            # Get all sessions by getting all accounts first
            accounts = processor.config_manager.get_all_accounts()
            sessions = []
            for acc in accounts:
                sessions.extend(processor.db_manager.get_import_sessions_by_account(acc["name"]))

        if not sessions:
            click.echo("No import sessions found")
            return

        click.echo("Import sessions:")
        for session in sessions:
            status_icon = {"pending": "⏳", "processing": "🔄", "completed": "✅", "failed": "❌"}.get(
                session["status"], "❓"
            )

            click.echo(f"  {status_icon} {session['session_name']} ({session['account_name']}) - {session['status']}")
            click.echo(f"    File: {session['file_path']}")
            click.echo(f"    Transactions: {session['processed_transactions']}/{session['total_transactions']}")
            if session["error_count"] > 0:
                click.echo(f"    Errors: {session['error_count']}")
            if session["created_at"]:
                click.echo(f"    Created: {session['created_at']}")
            click.echo()

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort() from e


if __name__ == "__main__":
    cli()
