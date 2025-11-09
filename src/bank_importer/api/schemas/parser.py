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

"""Parser API schemas."""

from pydantic import BaseModel, Field

from bank_importer.models.config_models import ParserInfo


class ParserInfoResponse(BaseModel):
    """Parser information response schema."""

    name: str
    bank_type: str
    supported_extensions: list[str] = Field(default_factory=list)
    supported_patterns: list[str] = Field(default_factory=list)
    description: str | None = None

    @classmethod
    def from_parser_info(cls, parser: ParserInfo) -> "ParserInfoResponse":
        """Create from ParserInfo model."""
        return cls(
            name=parser.name,
            bank_type=parser.bank_type,
            supported_extensions=parser.supported_extensions,
            supported_patterns=parser.supported_patterns,
            description=parser.description,
        )


class ParserDetectRequest(BaseModel):
    """Parser detection request schema."""

    file_path: str = Field(..., description="Path to the file to analyze")


class ParserDetectResponse(BaseModel):
    """Parser detection response schema."""

    parser_name: str | None = Field(None, description="Detected parser name")
    confidence: float = Field(
        0.0,
        ge=0.0,
        le=1.0,
        description="Detection confidence score",
    )
