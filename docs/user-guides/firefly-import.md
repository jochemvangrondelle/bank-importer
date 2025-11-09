# Firefly-III Import Guide

This guide explains how to use the bank importer's CSV export functionality to import transactions into Firefly-III.

## Overview

The bank importer now generates **two files** for each export:

1. **CSV file** - Contains the transaction data in Firefly-III compatible format
2. **JSON configuration file** - Contains the import configuration for Firefly-III

## Generated Files

### CSV File Format

The CSV file includes **53 columns** with comprehensive transaction data for maximum context and easy classification:

#### Core Transaction Data

| Column        | Role               | Description                            |
| ------------- | ------------------ | -------------------------------------- |
| `date`        | `date_transaction` | Transaction date (YYYY-MM-DD format)   |
| `description` | `description`      | Transaction description                |
| `amount`      | `amount`           | Transaction amount (positive/negative) |
| `currency`    | `currency-code`    | Currency code (THB)                    |

#### Account Information

| Column           | Role             | Description                           |
| ---------------- | ---------------- | ------------------------------------- |
| `account_name`   | `account-name`   | Your account name                     |
| `account_iban`   | `account-iban`   | Your account number                   |
| `account_number` | `account-number` | Account number (for non-IBAN systems) |
| `account_bic`    | `account-bic`    | Bank identifier code                  |

#### Opposing Account Information

| Column            | Role              | Description                         |
| ----------------- | ----------------- | ----------------------------------- |
| `opposing_name`   | `opposing-name`   | Counterparty name (if available)    |
| `opposing_iban`   | `opposing-iban`   | Counterparty account (if available) |
| `opposing_number` | `opposing-number` | Counterparty account number         |
| `opposing_bic`    | `opposing-bic`    | Counterparty bank identifier        |

#### Classification Fields

| Column              | Role            | Description          |
| ------------------- | --------------- | -------------------- |
| `category_name`     | `category-name` | Transaction category |
| `budget_name`       | `budget-name`   | Budget assignment    |
| `bill_name`         | `bill-name`     | Bill association     |
| `subscription_name` | `bill-name`     | Subscription name    |

#### Transaction Metadata

| Column             | Role                 | Description                          |
| ------------------ | -------------------- | ------------------------------------ |
| `transaction_type` | `note`               | Type (deposit, withdrawal, transfer) |
| `channel`          | `note`               | Payment channel (ATM, online, etc.)  |
| `reference`        | `internal_reference` | Transaction reference                |
| `check_number`     | `note`               | Check number (if applicable)         |
| `memo`             | `note`               | Additional memo                      |
| `subcategory`      | `note`               | Transaction subcategory              |

#### Amount Details

| Column             | Role                    | Description             |
| ------------------ | ----------------------- | ----------------------- |
| `amount_foreign`   | `amount_foreign`        | Foreign currency amount |
| `foreign_currency` | `foreign-currency-code` | Foreign currency code   |
| `exchange_rate`    | `note`                  | Exchange rate used      |
| `fees`             | `note`                  | Transaction fees        |
| `interest`         | `note`                  | Interest amount         |
| `tax`              | `note`                  | Tax amount              |

#### Date Metadata

| Column             | Role               | Description               |
| ------------------ | ------------------ | ------------------------- |
| `date_transaction` | `date_transaction` | Transaction date          |
| `date_value`       | `date_transaction` | Value date                |
| `date_posting`     | `date_transaction` | Posting date              |
| `date_booking`     | `date_transaction` | Booking date              |
| `date_process`     | `note`             | Processing date           |
| `date_due`         | `note`             | Due date                  |
| `date_invoice`     | `note`             | Invoice date              |
| `date_payment`     | `note`             | Payment date              |
| `date_interest`    | `note`             | Interest calculation date |

#### Balance Information

| Column           | Role   | Description                        |
| ---------------- | ------ | ---------------------------------- |
| `balance`        | `note` | Account balance after transaction  |
| `balance_old`    | `note` | Account balance before transaction |
| `balance_new`    | `note` | New balance                        |
| `balance_change` | `note` | Balance change amount              |

#### Additional Metadata

| Column               | Role                 | Description                                      |
| -------------------- | -------------------- | ------------------------------------------------ |
| `tags`               | `tags-space`         | Tags (imported, parser, type, channel, category) |
| `notes`              | `note`               | Comprehensive notes with all metadata            |
| `external_id`        | `external-id`        | Unique identifier for duplicate detection        |
| `internal_reference` | `internal_reference` | Internal reference number                        |

#### Bank-Specific Information

| Column         | Role   | Description                 |
| -------------- | ------ | --------------------------- |
| `bank_name`    | `note` | Bank name                   |
| `branch_name`  | `note` | Branch name                 |
| `country_code` | `note` | Country code                |
| `parser_name`  | `note` | Parser used to extract data |
| `source_file`  | `note` | Original source file        |

#### Raw Data Preservation

| Column     | Role   | Description                      |
| ---------- | ------ | -------------------------------- |
| `raw_text` | `note` | Original raw text from statement |
| `raw_json` | `note` | Raw JSON data (if applicable)    |

### Import Configuration File

The JSON configuration file is optimized for Firefly-III imports with:

- **Duplicate detection**: Uses external IDs to prevent duplicate imports
- **Column mapping**: Pre-configured for currency and account mapping
- **Import tags**: Automatically adds import tags to all transactions
- **Rules processing**: Enabled for automatic categorization

### Enhanced Data Benefits

The comprehensive data structure provides maximum context for easy classification:

#### **Easy Account Matching**

- Multiple account identifiers (name, IBAN, number, BIC)
- Bank and branch information for verification
- Country codes for international transactions

#### **Rich Classification Data**

- Transaction types (deposit, withdrawal, transfer)
- Payment channels (ATM, online, mobile, etc.)
- Categories and subcategories when available
- Reference numbers for tracking

#### **Complete Financial Context**

- Balance information (before/after/change)
- Foreign currency amounts and exchange rates
- Fees, interest, and tax breakdowns
- Multiple date fields (transaction, value, posting, booking)

#### **Enhanced Metadata**

- Comprehensive tags (parser, type, channel, category)
- Detailed notes with all available information
- Raw data preservation for troubleshooting
- Source file tracking

#### **Smart Mapping Support**

- Pre-configured mappings for common fields
- Extensible mapping for custom classifications
- Support for both IBAN and non-IBAN systems
- Flexible currency handling

## Usage

### 1. Export Transactions

```bash
# Export all transactions to CSV
python3 -m bank_importer sync --target csv

# Export specific account
python3 -m bank_importer sync --target csv --account scb_main
```

### 2. Import into Firefly-III

1. **Upload CSV file** to Firefly-III import page
2. **Upload JSON configuration** file when prompted
3. **Review and confirm** the import settings
4. **Execute import**

### 3. Import Configuration Details

The generated configuration includes:

```json
{
  "version": 3,
  "source": "bank-importer",
  "date": "Y-m-d",
  "delimiter": "comma",
  "headers": true,
  "rules": true,
  "add_import_tag": true,
  "duplicate_detection_method": "classic",
  "ignore_duplicate_lines": true,
  "ignore_duplicate_transactions": true,
  "unique_column_index": 13,
  "unique_column_type": "external-id"
}
```

## Features

### Duplicate Prevention

- **External IDs**: Each transaction has a unique identifier
- **Content-based detection**: Firefly-III checks for duplicate content
- **Automatic skipping**: Duplicates are automatically skipped

### Smart Mapping

- **Currency mapping**: THB currency is pre-mapped
- **Account mapping**: Your account details are pre-mapped
- **Extensible**: Additional mappings can be added in Firefly-III

### Metadata Preservation

- **Original balance**: Stored in notes field
- **Transaction type**: Preserved for reference
- **Parser information**: Tracks which parser processed the transaction
- **Import tags**: Automatically added for tracking

## Configuration

### CSV Target Configuration

The CSV target can be configured in `config.toml`:

```toml
[[targets]]
name    = "csv"
enabled = true

[targets.csv_config]
# CSV export configuration
date_format = "Y-m-d"
delimiter = "comma"
include_headers = true

# Firefly-III import optimization
add_import_tag = true
duplicate_detection = "classic"
ignore_duplicate_lines = true
ignore_duplicate_transactions = true

# Column mapping configuration
map_currency = true
map_account_name = true
map_account_iban = true
map_opposing_name = true
map_opposing_iban = true
map_category = true
map_budget = true
map_bill = true

# External ID for duplicate detection
use_external_id = true
external_id_format = "{account_number}_{date}_{transaction_id}"

# Tags and metadata
default_tags = ["imported", "bank-importer"]
include_parser_tag = true
include_balance_info = true
include_transaction_type = true
```

## Troubleshooting

### Common Issues

1. **Import fails**: Check that the CSV and JSON files are from the same export
2. **Duplicates detected**: This is normal - the system prevents duplicate imports
3. **Mapping issues**: Review the mapping configuration in Firefly-III

### File Locations

- **CSV files**: `output/firefly_export_*.csv`
- **Config files**: `output/firefly_export_*_config.json`

### Verification

Check export status:

```bash
python3 -m bank_importer list-exports
```

## Next Steps

1. **Direct API integration**: Future version will support direct Firefly-III API upload
2. **Enhanced mapping**: Automatic category and budget mapping
3. **Real-time sync**: Continuous synchronization with Firefly-III
