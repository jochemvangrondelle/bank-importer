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

"""Pytest configuration for bank importer tests."""

# Patch passlib bcrypt wrap bug detection before any imports
# This avoids issues with bcrypt 5.0.0 and passlib compatibility
try:
    import passlib.handlers.bcrypt as bcrypt_handler

    def patched_detect_wrap_bug(ident: bytes) -> bool:
        """Patched version that skips wrap bug detection."""
        return False

    # Patch before CryptContext is initialized
    bcrypt_handler.detect_wrap_bug = patched_detect_wrap_bug
except (ImportError, AttributeError):
    pass

from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from bank_importer.models.database import DatabaseManager
from bank_importer.models.import_session import ImportSession
from bank_importer.models.transaction import Transaction


@pytest.fixture(scope="session")
def test_data_dir() -> Path:
    """Get the test data directory."""
    return Path(__file__).parent / "data"


@pytest.fixture(scope="session")
def sample_account_config() -> dict[str, Any]:
    """Sample account configuration for testing."""
    return {
        "name": "test_account",
        "bank_name": "Test Bank",
        "account_number": "123-456-789",
        "account_name": "Test User",
        "currency": "THB",
        "country_code": "TH",
        "reference": "test_ref",
    }


@pytest.fixture(autouse=True)
def setup_test_environment(test_data_dir: Path) -> None:
    """Set up test environment."""
    # Ensure test data directory exists
    test_data_dir.mkdir(exist_ok=True)

    # Create .gitkeep file if it doesn't exist
    gitkeep_file = test_data_dir / ".gitkeep"
    if not gitkeep_file.exists():
        gitkeep_file.touch()


# Database fixtures
@pytest.fixture
def db_manager(tmp_path: Path) -> DatabaseManager:
    """Create a database manager with temporary database."""
    db_path = tmp_path / "test.db"
    db_url = f"sqlite:///{db_path}"
    return DatabaseManager(db_url)


@pytest.fixture
def sample_transaction() -> Transaction:
    """Create a sample transaction for testing."""
    return Transaction(
        date=datetime(2024, 1, 1, tzinfo=UTC),
        description="Test transaction",
        amount=Decimal("100.00"),
        balance=Decimal("1000.00"),
        transaction_type="debit",
        account_number="123-456-789",
        currency="THB",
        country_code="TH",
        source_file="test.txt",
    )


@pytest.fixture
def sample_transactions() -> list[Transaction]:
    """Create multiple sample transactions for testing."""
    return [
        Transaction(
            date=datetime(2024, 1, day, tzinfo=UTC),
            description=f"Test transaction {day}",
            amount=Decimal(f"{day * 10}.00"),
            balance=Decimal(f"{1000 + day * 10}.00"),
            transaction_type="debit" if day % 2 == 0 else "credit",
            account_number="123-456-789",
            currency="THB",
            country_code="TH",
            source_file=f"test_{day}.txt",
        )
        for day in range(1, 6)
    ]


@pytest.fixture
def sample_import_session() -> ImportSession:
    """Create a sample import session for testing."""
    return ImportSession(
        file_path="test.txt",
        file_hash="abc123",
        account_name="test_account",
        bank_name="Test Bank",
        session_name="test_session",
        status="processing",
        started_at=datetime.now(UTC),
    )


@pytest.fixture
def sample_import_sessions() -> list[ImportSession]:
    """Create multiple sample import sessions for testing."""
    return [
        ImportSession(
            file_path=f"test_{i}.txt",
            file_hash=f"hash{i}",
            account_name="test_account",
            bank_name="Test Bank",
            session_name=f"session_{i}",
            status=status,
            started_at=datetime.now(UTC),
        )
        for i, status in enumerate(["pending", "processing", "completed", "failed"], 1)
    ]


# Transaction factory fixture for parameterized tests
@pytest.fixture
def transaction_factory() -> type[Transaction]:
    """Factory function to create transactions with custom parameters."""

    def _create_transaction(
        date: datetime | None = None,
        description: str = "Test transaction",
        amount: Decimal | str = "100.00",
        balance: Decimal | str = "1000.00",
        transaction_type: str = "debit",
        account_number: str = "123-456-789",
        currency: str = "THB",
        country_code: str = "TH",
        source_file: str | None = "test.txt",
        **kwargs: Any,
    ) -> Transaction:
        """Create a transaction with specified parameters."""
        return Transaction(
            date=date or datetime(2024, 1, 1, tzinfo=UTC),
            description=description,
            amount=Decimal(str(amount)),
            balance=Decimal(str(balance)),
            transaction_type=transaction_type,
            account_number=account_number,
            currency=currency,
            country_code=country_code,
            source_file=source_file,
            **kwargs,
        )

    return _create_transaction


# Import session factory fixture
@pytest.fixture
def import_session_factory() -> type[ImportSession]:
    """Factory function to create import sessions with custom parameters."""

    def _create_import_session(
        file_path: str = "test.txt",
        file_hash: str = "abc123",
        account_name: str = "test_account",
        bank_name: str = "Test Bank",
        session_name: str = "test_session",
        status: str = "processing",
        started_at: datetime | None = None,
        **kwargs: Any,
    ) -> ImportSession:
        """Create an import session with specified parameters."""
        return ImportSession(
            file_path=file_path,
            file_hash=file_hash,
            account_name=account_name,
            bank_name=bank_name,
            session_name=session_name,
            status=status,
            started_at=started_at or datetime.now(UTC),
            **kwargs,
        )

    return _create_import_session
