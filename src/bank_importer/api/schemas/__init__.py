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

"""API schemas for request/response models."""

from bank_importer.api.schemas.auth import (
    LoginRequest,
    LoginResponse,
    SetPasswordRequest,
    SetPasswordResponse,
)
from bank_importer.api.schemas.common import (
    ErrorResponse,
    HealthResponse,
    VersionResponse,
)
from bank_importer.api.schemas.config import (
    AccountConfigResponse,
    AppSettings,
    ConfigResponse,
    ConfigUpdate,
    DatabaseSettings,
    OutputSettings,
    SettingsResponse,
    SettingsUpdate,
    TargetConfigResponse,
    TranslationSettings,
)
from bank_importer.api.schemas.export import (
    ExportJobResponse,
    ExportRequest,
    ExportSessionResponse,
)
from bank_importer.api.schemas.import_ import (
    ImportFileSyncRequest,
    ImportFileSyncResponse,
    ImportJobResponse,
    ImportRequest,
    ImportSessionResponse,
)
from bank_importer.api.schemas.parse import (
    ParseAndExportRequest,
    ParseAndExportResponse,
    ParseFileRequest,
    ParseFileResponse,
)
from bank_importer.api.schemas.parser import (
    ParserDetectRequest,
    ParserDetectResponse,
    ParserInfoResponse,
)
from bank_importer.api.schemas.status import (
    AccountStatus,
    AccountStatusSummary,
    StatusResponse,
)
from bank_importer.api.schemas.transaction import TransactionResponse, TransactionUpdate

__all__ = [
    # Config
    "AccountConfigResponse",
    # Status
    "AccountStatus",
    "AccountStatusSummary",
    "AppSettings",
    "ConfigResponse",
    "ConfigUpdate",
    "DatabaseSettings",
    # Common
    "ErrorResponse",
    # Export
    "ExportJobResponse",
    "ExportRequest",
    "ExportSessionResponse",
    "HealthResponse",
    # Import
    "ImportFileSyncRequest",
    "ImportFileSyncResponse",
    "ImportJobResponse",
    "ImportRequest",
    "ImportSessionResponse",
    # Auth
    "LoginRequest",
    "LoginResponse",
    "OutputSettings",
    # Parse
    "ParseAndExportRequest",
    "ParseAndExportResponse",
    "ParseFileRequest",
    "ParseFileResponse",
    # Parser
    "ParserDetectRequest",
    "ParserDetectResponse",
    "ParserInfoResponse",
    "SetPasswordRequest",
    "SetPasswordResponse",
    "SettingsResponse",
    "SettingsUpdate",
    "StatusResponse",
    "TargetConfigResponse",
    # Transaction
    "TransactionResponse",
    "TransactionUpdate",
    "TranslationSettings",
    "VersionResponse",
]
