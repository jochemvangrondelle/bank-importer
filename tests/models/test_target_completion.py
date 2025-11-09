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

"""Tests for target completion model."""

from datetime import datetime

from bank_importer.models.enums import TargetCompletionStatus
from bank_importer.models.target_completion import TargetCompletion


class TestTargetCompletion:
    """Test TargetCompletion model."""

    def test_status_enum_valid_value(self) -> None:
        """Test status_enum property with valid enum value."""
        completion = TargetCompletion(
            transaction_id=1,
            target_name="csv",
            status="completed",
        )
        assert completion.status_enum == TargetCompletionStatus.COMPLETED

    def test_status_enum_invalid_value_fallback(self) -> None:
        """Test status_enum property with invalid value falls back to PENDING."""
        completion = TargetCompletion(
            transaction_id=1,
            target_name="csv",
            status="invalid_status",
        )
        assert completion.status_enum == TargetCompletionStatus.PENDING

    def test_status_enum_setter(self) -> None:
        """Test status_enum setter."""
        completion = TargetCompletion(
            transaction_id=1,
            target_name="csv",
            status="pending",  # Required field
        )
        completion.status_enum = TargetCompletionStatus.COMPLETED
        assert completion.status == "completed"

    def test_to_dict_with_completed_at(self) -> None:
        """Test to_dict method with completed_at set."""
        completed_at = datetime(2025, 1, 1, 12, 0, 0)
        completion = TargetCompletion(
            id=1,
            transaction_id=1,
            target_name="csv",
            status="completed",
            completed_at=completed_at,
            error_message="test error",
            retry_count=2,
        )
        result = completion.to_dict()
        assert result == {
            "id": 1,
            "transaction_id": 1,
            "target_name": "csv",
            "status": "completed",
            "completed_at": completed_at.isoformat(),
            "error_message": "test error",
            "retry_count": 2,
        }

    def test_to_dict_without_completed_at(self) -> None:
        """Test to_dict method without completed_at."""
        completion = TargetCompletion(
            id=1,
            transaction_id=1,
            target_name="csv",
            status="pending",
            completed_at=None,
            error_message=None,
            retry_count=0,
        )
        result = completion.to_dict()
        assert result == {
            "id": 1,
            "transaction_id": 1,
            "target_name": "csv",
            "status": "pending",
            "completed_at": None,
            "error_message": None,
            "retry_count": 0,
        }
