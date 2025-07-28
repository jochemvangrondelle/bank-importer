"""List parsers command for the bank importer CLI."""

from rich.table import Table

from ...cli_parameters import CONFIG_FILE_PARAM
from ...cli_utils import cli_error_handler
from ...logging_config import get_console
from ...parser_detector import ParserDetector


@cli_error_handler
def list_parsers(
    config_file: str = CONFIG_FILE_PARAM,
) -> None:
    """**List** all available parsers with their capabilities."""
    console = get_console()

    # Create parser detector to get available parsers
    parser_detector = ParserDetector()
    available_parsers = parser_detector.list_available_parsers()

    # Create rich table for parsers
    table = Table(
        title="🔧 Available Parsers",
        show_header=True,
        header_style="bold magenta",
        border_style="blue",
    )

    # Add columns
    table.add_column("Parser Name", style="cyan", no_wrap=True)
    table.add_column("Description", style="green", no_wrap=False)
    table.add_column("Supported Extensions", style="yellow", no_wrap=True)
    table.add_column("Type", style="blue", no_wrap=True)

    # Parser descriptions and metadata
    parser_info = {
        "amex_th_csv": {
            "description": "American Express Thailand CSV statement parser",
            "extensions": [".csv"],
            "type": "Bank-specific",
        },
        "krungsri_pdf": {
            "description": "Krungsri Bank PDF statement parser (password-protected)",
            "extensions": [".pdf"],
            "type": "Bank-specific",
        },
        "krungsri_text": {
            "description": "Krungsri Bank text statement parser",
            "extensions": [".txt"],
            "type": "Bank-specific",
        },
        "scb_pdf": {
            "description": "Siam Commercial Bank (SCB) PDF statement parser",
            "extensions": [".pdf"],
            "type": "Bank-specific",
        },
        "generic_csv": {
            "description": "Generic CSV/TSV parser with auto-detection of delimiters and formats",
            "extensions": [".csv", ".tsv", ".txt"],
            "type": "Generic",
        },
        "generic_json": {
            "description": "Generic JSON parser for transaction data",
            "extensions": [".json", ".jsonl"],
            "type": "Generic",
        },
        "generic_fixed_width": {
            "description": "Generic fixed-width text parser for legacy bank formats",
            "extensions": [".txt", ".dat", ".prn"],
            "type": "Generic",
        },
    }

    # Add rows for each parser
    for parser_name in available_parsers:
        info = parser_info.get(
            parser_name,
            {
                "description": "No description available",
                "extensions": [],
                "type": "Unknown",
            },
        )

        extensions_str = ", ".join(info["extensions"]) if info["extensions"] else "N/A"

        table.add_row(
            str(parser_name),
            str(info["description"]),
            str(extensions_str),
            str(info["type"]),
        )

    # Print the table
    console.print(table)

    # Print summary
    bank_specific = sum(
        1 for info in parser_info.values() if info["type"] == "Bank-specific"
    )
    generic = sum(1 for info in parser_info.values() if info["type"] == "Generic")

    console.print(f"\n📊 Summary: {len(available_parsers)} total parsers")
    console.print(f"🏦 Bank-specific: {bank_specific}")
    console.print(f"🔧 Generic: {generic}")

    # Print usage hints
    console.print(f"\n💡 Usage:")
    console.print(
        f"  • Use 'bank-importer-th import-files <file>' to auto-detect parser"
    )
    console.print(f"  • Configure parsers in config.toml for specific accounts")
    console.print(f"  • Generic parsers work with most standard formats")
