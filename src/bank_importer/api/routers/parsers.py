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

"""Parser endpoints."""

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from bank_importer.api.dependencies import get_parser_detector
from bank_importer.api.schemas.parser import (
    ParserDetectRequest,
    ParserDetectResponse,
    ParserInfoResponse,
)
from bank_importer.parser_detector import ParserDetector

router = APIRouter()


@router.get("", tags=["Parsers"])
async def list_parsers(
    parser_detector: Annotated[ParserDetector, Depends(get_parser_detector)],
) -> dict[str, list[ParserInfoResponse]]:
    """List available parsers."""
    available_parsers = parser_detector.list_available_parsers()
    parsers = []

    # Parser descriptions and metadata
    parser_info_map = {
        "amex_th_csv": {
            "description": "American Express Thailand CSV statement parser",
            "extensions": [".csv"],
            "bank_type": "amex_th",
        },
        "krungsri_pdf": {
            "description": "Krungsri Bank PDF statement parser (password-protected)",
            "extensions": [".pdf"],
            "bank_type": "krungsri",
        },
        "krungsri_text": {
            "description": "Krungsri Bank text statement parser",
            "extensions": [".txt"],
            "bank_type": "krungsri",
        },
        "scb_pdf": {
            "description": "Siam Commercial Bank (SCB) PDF statement parser",
            "extensions": [".pdf"],
            "bank_type": "scb",
        },
        "generic_csv": {
            "description": "Generic CSV/TSV parser with auto-detection of delimiters and formats",
            "extensions": [".csv", ".tsv", ".txt"],
            "bank_type": "generic",
        },
        "generic_json": {
            "description": "Generic JSON parser for transaction data",
            "extensions": [".json", ".jsonl"],
            "bank_type": "generic",
        },
        "generic_fixed_width": {
            "description": "Generic fixed-width text parser for legacy bank formats",
            "extensions": [".txt", ".dat", ".prn"],
            "bank_type": "generic",
        },
    }

    for parser_name in available_parsers:
        info = parser_info_map.get(
            parser_name,
            {
                "description": "No description available",
                "extensions": [],
                "bank_type": "unknown",
            },
        )
        parsers.append(
            ParserInfoResponse(
                name=parser_name,
                bank_type=str(info["bank_type"]),
                supported_extensions=list(info["extensions"]),
                supported_patterns=[],
                description=str(info["description"]) if info["description"] else None,
            ),
        )

    return {"parsers": parsers}


@router.post("/detect", tags=["Parsers"])
async def detect_parser(
    request: ParserDetectRequest,
    parser_detector: Annotated[ParserDetector, Depends(get_parser_detector)],
) -> ParserDetectResponse:
    """Detect parser for file."""
    file_path = Path(request.file_path)

    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File not found: {request.file_path}",
        )

    detected_parser = parser_detector.detect_parser(file_path)
    confidence = 1.0 if detected_parser else 0.0

    return ParserDetectResponse(
        parser_name=detected_parser,
        confidence=confidence,
    )
