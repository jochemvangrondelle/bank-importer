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

"""Parse endpoints for modular file parsing operations."""

import tempfile
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse

from bank_importer.api.dependencies import get_config_manager
from bank_importer.api.schemas.parse import ParseFileRequest, ParseFileResponse
from bank_importer.api.schemas.transaction import TransactionResponse
from bank_importer.api.security import require_auth
from bank_importer.config import ConfigManager
from bank_importer.library import export_transactions, parse_file
from bank_importer.models.enums import (
    CountryCode,
    Currency,
    ParserDetectionBehavior,
    ParserName,
    TargetName,
)

router = APIRouter()


@router.post(
    "/file",
    status_code=status.HTTP_200_OK,
    tags=["Parse"],
)
async def parse_file_endpoint(
    file: Annotated[UploadFile, File(description="Bank statement file to parse")],
    parser_name: Annotated[
        ParserName | None,
        Form(description="Parser name to use. If not provided, will auto-detect."),
    ] = None,
    account_config_name: Annotated[
        str | None,
        Form(
            description=(
                "Name of account configuration to use (recommended for security). "
                "If provided, account settings including password will be loaded from config."
            ),
        ),
    ] = None,
    account_number: Annotated[
        str | None,
        Form(
            description="Account number (required if account_config_name not provided)",
        ),
    ] = None,
    account_name: Annotated[
        str | None,
        Form(
            description="Account display name (required if account_config_name not provided)",
        ),
    ] = None,
    bank_name: Annotated[
        str | None,
        Form(description="Bank name (required if account_config_name not provided)"),
    ] = None,
    currency: Annotated[
        Currency,
        Form(description="Currency code (ISO 4217)"),
    ] = Currency.THB,
    country_code: Annotated[
        CountryCode,
        Form(description="Country code (ISO 3166-1 alpha-2)"),
    ] = CountryCode.TH,
    password: Annotated[
        str | None,
        Form(
            description=(
                "Password for password-protected PDFs (less secure - prefer account_config_name). "
                "Note: This is transmitted over the network. Use account_config_name with "
                "environment variables or file-based secrets for better security."
            ),
        ),
    ] = None,
    parser_detection_behavior: Annotated[
        ParserDetectionBehavior,
        Form(
            description="Parser detection behavior: automatic (auto-detect if not specified) or manual (require parser to be specified)",
        ),
    ] = ParserDetectionBehavior.AUTOMATIC,
    config_manager: ConfigManager = Depends(get_config_manager),
    _: dict = Depends(require_auth),
) -> ParseFileResponse:
    """Parse a bank statement file and return transactions (synchronous, no database).

    This endpoint provides a simple, modular way to parse a file without requiring
    database setup. Supports two modes:

    1. **Account-based (recommended)**: Use `account_config_name` to load settings from config.
       Passwords can be stored securely using environment variables or file-based secrets.

    2. **Direct mode**: Provide account details directly. Less secure but useful for one-off operations.

    **Security**: For production use, prefer `account_config_name` with passwords stored in
    environment variables (e.g., `ACCOUNTS_MY_ACCOUNT_PASSWORD`) or file-based secrets.

    **Use Case**: Parse a single PDF file and get transactions as JSON.

    **Example (Account-based - Recommended)**:
    ```bash
    curl -X POST "http://localhost:8000/api/v1/parse/file" \
      -H "Authorization: Bearer YOUR_TOKEN" \
      -F "file=@statement.pdf" \
      -F "account_config_name=krungsri_pdf"
    ```

    **Example (Direct mode - Less secure)**:
    ```bash
    curl -X POST "http://localhost:8000/api/v1/parse/file" \
      -H "Authorization: Bearer YOUR_TOKEN" \
      -F "file=@statement.pdf" \
      -F "parser_name=krungsri_pdf" \
      -F "account_number=1234567890" \
      -F "account_name=My Account" \
      -F "bank_name=Krungsri" \
      -F "password=mypassword"
    ```

    **Response**: Returns list of transactions as JSON.
    """
    # Save uploaded file to temporary location
    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=Path(file.filename).suffix,
    ) as tmp_file:
        content = await file.read()
        tmp_file.write(content)
        tmp_path = Path(tmp_file.name)

    try:
        # Load account config if account_config_name is provided
        if account_config_name:
            account_config = config_manager.get_account_config(account_config_name)
            if not account_config:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Account configuration '{account_config_name}' not found",
                )
            # Use parser from config if not provided
            if not parser_name and account_config.get("parser"):
                parser_str = account_config.get("parser")
                # Try to convert to enum if it's a valid parser name
                try:
                    parser_name = ParserName(parser_str)
                except (ValueError, AttributeError):
                    parser_name = None  # Will use string value
        else:
            # Validate required fields for direct mode
            if not account_number or not account_name or not bank_name:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "Either 'account_config_name' or all of 'account_number', "
                        "'account_name', and 'bank_name' must be provided"
                    ),
                )
            # Build account config from form data
            # Convert enum to string if needed
            currency_str = (
                currency.value if isinstance(currency, Currency) else currency
            )
            account_config = {
                "name": account_name.lower().replace(" ", "_"),
                "account_number": account_number,
                "account_name": account_name,
                "bank_name": bank_name,
                "currency": currency_str,
                "country_code": country_code,
            }
            # Add password if provided (direct mode)
            if password:
                account_config["password"] = password

        # Parse the file using library function
        # Convert enum to string and boolean for library function
        parser_name_str = (
            parser_name.value if isinstance(parser_name, ParserName) else parser_name
        )
        auto_detect = parser_detection_behavior == ParserDetectionBehavior.AUTOMATIC
        transactions_list = list(
            parse_file(
                tmp_path,
                parser_name=parser_name_str,
                account_config=account_config,
                auto_detect=auto_detect,
            ),
        )

        # Determine parser name used
        if parser_name_str:
            used_parser = parser_name_str
        else:
            # Auto-detected - we'd need to call detect_parser, but for now use the provided or default
            from bank_importer.library import detect_parser

            detected = detect_parser(tmp_path)
            used_parser = detected or "unknown"

        return ParseFileResponse(
            transactions=[
                TransactionResponse.from_transaction(t) for t in transactions_list
            ],
            parser_name=used_parser,
            total_transactions=len(transactions_list),
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error parsing file: {e!s}",
        ) from e
    finally:
        # Clean up temporary file
        if tmp_path.exists():
            tmp_path.unlink()


@router.post(
    "/file/export",
    response_class=FileResponse,
    status_code=status.HTTP_200_OK,
    tags=["Parse"],
)
async def parse_and_export_file(
    file: Annotated[
        UploadFile,
        File(description="Bank statement file to parse and export"),
    ],
    parser_name: Annotated[
        str | None,
        Form(description="Parser name to use. If not provided, will auto-detect."),
    ] = None,
    account_config_name: Annotated[
        str | None,
        Form(
            description=(
                "Name of account configuration to use (recommended for security). "
                "If provided, account settings including password will be loaded from config."
            ),
        ),
    ] = None,
    account_number: Annotated[
        str | None,
        Form(
            description="Account number (required if account_config_name not provided)",
        ),
    ] = None,
    account_name: Annotated[
        str | None,
        Form(
            description="Account display name (required if account_config_name not provided)",
        ),
    ] = None,
    bank_name: Annotated[
        str | None,
        Form(description="Bank name (required if account_config_name not provided)"),
    ] = None,
    currency: Annotated[
        Currency,
        Form(description="Currency code (ISO 4217)"),
    ] = Currency.THB,
    country_code: Annotated[
        CountryCode,
        Form(description="Country code (ISO 3166-1 alpha-2)"),
    ] = CountryCode.TH,
    password: Annotated[
        str | None,
        Form(
            description=(
                "Password for password-protected PDFs (less secure - prefer account_config_name). "
                "Note: This is transmitted over the network. Use account_config_name with "
                "environment variables or file-based secrets for better security."
            ),
        ),
    ] = None,
    target_name: Annotated[
        TargetName,
        Form(description="Export target name"),
    ] = TargetName.CSV,
    parser_detection_behavior: Annotated[
        ParserDetectionBehavior,
        Form(
            description="Parser detection behavior: automatic (auto-detect if not specified) or manual (require parser to be specified)",
        ),
    ] = ParserDetectionBehavior.AUTOMATIC,
    config_manager: ConfigManager = Depends(get_config_manager),
    _: dict = Depends(require_auth),
) -> FileResponse:
    """Parse a bank statement file and export to CSV/YAML (synchronous, no database).

    This endpoint provides a simple, modular way to parse a file and get a CSV/YAML
    file back without requiring database setup. Supports two modes:

    1. **Account-based (recommended)**: Use `account_config_name` to load settings from config.
       Passwords can be stored securely using environment variables or file-based secrets.

    2. **Direct mode**: Provide account details directly. Less secure but useful for one-off operations.

    **Security**: For production use, prefer `account_config_name` with passwords stored in
    environment variables (e.g., `ACCOUNTS_MY_ACCOUNT_PASSWORD`) or file-based secrets.

    **Use Case**: Parse a single PDF file and get CSV file back.

    **Example (Account-based - Recommended)**:
    ```bash
    curl -X POST "http://localhost:8000/api/v1/parse/file/export" \
      -H "Authorization: Bearer YOUR_TOKEN" \
      -F "file=@statement.pdf" \
      -F "account_config_name=krungsri_pdf" \
      -F "target_name=csv" \
      -o output.csv
    ```

    **Example (Direct mode - Less secure)**:
    ```bash
    curl -X POST "http://localhost:8000/api/v1/parse/file/export" \
      -H "Authorization: Bearer YOUR_TOKEN" \
      -F "file=@statement.pdf" \
      -F "parser_name=krungsri_pdf" \
      -F "account_number=1234567890" \
      -F "account_name=My Account" \
      -F "bank_name=Krungsri" \
      -F "password=mypassword" \
      -F "target_name=csv" \
      -o output.csv
    ```

    **Response**: Returns the exported file (CSV, YAML, etc.) as a download.
    """
    # Save uploaded file to temporary location
    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=Path(file.filename).suffix,
    ) as tmp_file:
        content = await file.read()
        tmp_file.write(content)
        tmp_path = Path(tmp_file.name)

    # Create temporary output directory
    with tempfile.TemporaryDirectory() as tmp_output_dir:
        try:
            # Load account config if account_config_name is provided
            if account_config_name:
                account_config = config_manager.get_account_config(account_config_name)
                if not account_config:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Account configuration '{account_config_name}' not found",
                    )
                # Use parser from config if not provided
                if not parser_name and account_config.get("parser"):
                    parser_name = account_config.get("parser")
            else:
                # Validate required fields for direct mode
                if not account_number or not account_name or not bank_name:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=(
                            "Either 'account_config_name' or all of 'account_number', "
                            "'account_name', and 'bank_name' must be provided"
                        ),
                    )
                # Build account config from form data
                # Convert enums to strings if needed
                currency_str = (
                    currency.value if isinstance(currency, Currency) else currency
                )
                country_code_str = (
                    country_code.value
                    if isinstance(country_code, CountryCode)
                    else country_code
                )
                account_config = {
                    "name": account_name.lower().replace(" ", "_"),
                    "account_number": account_number,
                    "account_name": account_name,
                    "bank_name": bank_name,
                    "currency": currency_str,
                    "country_code": country_code_str,
                }
                # Add password if provided (direct mode)
                if password:
                    account_config["password"] = password

            # Parse the file using library function
            # Convert enum to string and boolean for library function
            parser_name_str = (
                parser_name.value
                if isinstance(parser_name, ParserName)
                else parser_name
            )
            auto_detect = parser_detection_behavior == ParserDetectionBehavior.AUTOMATIC
            transactions_list = list(
                parse_file(
                    tmp_path,
                    parser_name=parser_name_str,
                    account_config=account_config,
                    auto_detect=auto_detect,
                ),
            )

            if not transactions_list:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No transactions found in file",
                )

            # Export transactions using library function
            # Convert enum to string if needed
            target_name_str = (
                target_name.value
                if isinstance(target_name, TargetName)
                else target_name
            )
            export_result = export_transactions(
                transactions_list,
                target_name_str,
                output_dir=tmp_output_dir,
                account_config=account_config,
            )

            if not export_result.success or not export_result.output_file:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Export failed: {export_result.error_message}",
                )

            # Return the exported file
            output_path = Path(export_result.output_file)
            if not output_path.exists():
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Exported file not found",
                )

            # Determine media type based on target
            media_types = {
                "csv": "text/csv",
                "yaml": "application/x-yaml",
                "firefly": "text/csv",
            }
            media_type = media_types.get(target_name, "application/octet-stream")

            return FileResponse(
                path=str(output_path),
                filename=output_path.name,
                media_type=media_type,
            )

        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            ) from e
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error processing file: {e!s}",
            ) from e
        finally:
            # Clean up temporary input file
            if tmp_path.exists():
                tmp_path.unlink()


@router.post(
    "/file/path",
    status_code=status.HTTP_200_OK,
    tags=["Parse"],
)
async def parse_file_by_path(
    request: ParseFileRequest,
    file_path: Annotated[str, Form(description="Path to file on server to parse")],
    config_manager: Annotated[ConfigManager, Depends(get_config_manager)],
    _: Annotated[dict, Depends(require_auth)],
) -> ParseFileResponse:
    """Parse a file by path and return transactions (synchronous, no database).

    This endpoint parses a file that already exists on the server filesystem.
    Use this when files are already available on the server.

    **Use Case**: Parse a file that's already on the server (e.g., uploaded via FTP, S3, etc.).

    **Example**:
    ```bash
    curl -X POST "http://localhost:8000/api/v1/parse/file/path" \
      -H "Authorization: Bearer YOUR_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "file_path": "/data/in/statement.pdf",
        "parser_name": "krungsri_pdf",
        "account_number": "1234567890",
        "account_name": "My Account",
        "bank_name": "Krungsri",
        "password": "mypassword"
      }'
    ```
    """
    path = Path(file_path)

    if not path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File not found: {file_path}",
        )

    try:
        # Build account config from request
        # Convert enums to strings if needed
        currency_str = (
            request.currency.value
            if isinstance(request.currency, Currency)
            else request.currency
        )
        country_code_str = (
            request.country_code.value
            if isinstance(request.country_code, CountryCode)
            else request.country_code
        )
        account_config: dict[str, Any] = {
            "name": request.account_name.lower().replace(" ", "_"),
            "account_number": request.account_number,
            "account_name": request.account_name,
            "bank_name": request.bank_name,
            "currency": currency_str,
            "country_code": country_code_str,
        }

        if request.password:
            # SecretStr needs to be converted to string
            account_config["password"] = (
                request.password.get_secret_value()
                if hasattr(request.password, "get_secret_value")
                else str(request.password)
            )

        # Parse the file using library function
        # Convert enum to string and boolean for library function
        parser_name_str = (
            request.parser_name.value
            if isinstance(request.parser_name, ParserName)
            else request.parser_name
        )
        auto_detect = (
            request.parser_detection_behavior == ParserDetectionBehavior.AUTOMATIC
        )
        transactions_list = list(
            parse_file(
                path,
                parser_name=parser_name_str,
                account_config=account_config,
                config_manager=config_manager,
                auto_detect=auto_detect,
            ),
        )

        # Determine parser name used
        if parser_name_str:
            used_parser = parser_name_str
        else:
            from bank_importer.library import detect_parser

            detected = detect_parser(path)
            used_parser = detected or "unknown"

        return ParseFileResponse(
            transactions=[
                TransactionResponse.from_transaction(t) for t in transactions_list
            ],
            parser_name=used_parser,
            total_transactions=len(transactions_list),
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error parsing file: {e!s}",
        ) from e
