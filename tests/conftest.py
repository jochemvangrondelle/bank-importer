"""Pytest configuration for bank importer tests."""

from pathlib import Path
from typing import Any

import pytest


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
