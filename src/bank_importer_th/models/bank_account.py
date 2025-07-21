"""Bank account model."""

from sqlmodel import Field, SQLModel


class BankAccount(SQLModel, table=True):
    """Represents a bank account configuration."""

    __tablename__ = "bank_accounts"

    # Primary key
    id: int | None = Field(default=None, primary_key=True)

    # Account identification
    account_number: str = Field(max_length=50, unique=True, nullable=False)
    account_name: str = Field(max_length=200, nullable=False)
    bank_name: str = Field(max_length=100, nullable=False)

    # Account details
    currency: str = Field(max_length=3, nullable=False)
    country_code: str = Field(max_length=2, nullable=False)

    # Optional details
    branch_name: str | None = Field(default=None, max_length=100)
    reference: str | None = Field(default=None, max_length=200)

    def validate_account(self) -> None:
        """Validate account configuration."""
        if not self.account_number:
            raise ValueError("Account number is required")
        if not self.account_name:
            raise ValueError("Account name is required")
        if not self.bank_name:
            raise ValueError("Bank name is required")
        if not self.currency:
            raise ValueError("Currency is required")
        if not self.country_code:
            raise ValueError("Country code is required")
