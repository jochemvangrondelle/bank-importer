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

"""Run the FastAPI server."""

import argparse
import sys

try:
    import uvicorn
except ImportError:
    sys.exit(1)

from bank_importer.api.config import settings
from bank_importer.api.main import app


def main() -> None:
    """Main entry point for bank-importer-api command."""
    parser = argparse.ArgumentParser(description="Run Bank Importer API server")
    parser.add_argument(
        "--host",
        default=settings.get_api_host(),
        help=f"Host to bind to (default: {settings.DEFAULT_HOST})",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=settings.get_api_port(),
        help=f"Port to bind to (default: {settings.DEFAULT_PORT})",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload (development only)",
    )

    args = parser.parse_args()

    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


if __name__ == "__main__":
    main()
