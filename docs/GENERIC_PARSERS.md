# Generic Parsers Documentation

This document describes the generic parsers available in the bank importer system. These parsers can automatically detect file formats and extract transaction data from various sources.

## Overview

The generic parsers provide flexible, format-agnostic transaction extraction capabilities. They automatically detect file formats, field mappings, and data types to convert various file formats into standardized transaction records.

## Available Parsers

### 1. Generic CSV Parser (`generic_csv`)

**Supported Formats**: `.csv`, `.tsv`, `.txt`

**Features**:

- **Auto-delimiter detection**: Comma, tab, semicolon, pipe
- **Auto-quote detection**: Double quotes, single quotes, none
- **Multiple encodings**: UTF-8, Latin-1
- **Flexible field mapping**: Maps CSV headers to transaction fields
- **Multiple date formats**: YYYY-MM-DD, DD/MM/YYYY, MM/DD/YYYY, etc.

**Enhanced Field Support**:

- **Core fields**: `date`, `description`, `amount`, `balance`, `transaction_type`, `account_number`
- **Balance tracking**: `old_balance`, `new_balance`
- **Multiple dates**: `transaction_date`, `value_date`, `posting_date`, `effective_date`
- **Transaction details**: `channel`, `reference`, `check_number`, `memo`, `category`, `subcategory`
- **Financial metadata**: `exchange_rate`, `foreign_currency`, `foreign_amount`, `fees`, `interest`, `tax`

### 2. Generic JSON Parser (`generic_json`)

**Supported Formats**: `.json`, `.jsonl`

**Features**:

- **Multiple JSON structures**: Arrays, objects with transactions, single transactions
- **JSON Lines support**: One JSON object per line
- **Automatic type conversion**: Handles strings, numbers, dates
- **Flexible field mapping**: Normalizes JSON keys for matching

**Enhanced Field Support**:

- All fields supported by CSV parser
- **Nested object support**: Can extract from nested JSON structures
- **Array handling**: Processes arrays of transactions
- **Type inference**: Automatically converts data types

### 3. Generic Fixed-Width Parser (`generic_fixed_width`)

**Supported Formats**: `.txt`, `.dat`, `.prn`

**Features**:

- **Auto-field detection**: Pattern-based field position identification
- **Legacy format support**: Handles old bank statement formats
- **Smart description extraction**: Finds descriptions in gaps between fields
- **Pattern recognition**: Date and amount pattern matching

**Enhanced Field Support**:

- Core transaction fields
- **Position-based extraction**: Uses character positions for field boundaries
- **Pattern matching**: Recognizes common date and amount patterns
- **Flexible layout**: Adapts to different fixed-width formats

## Enhanced Transaction Model

The transaction model has been enhanced to support comprehensive bank statement data:

### Core Fields

- `date`: Primary transaction date
- `description`: Transaction description
- `amount`: Transaction amount (positive for deposits, negative for withdrawals)
- `balance`: Account balance after transaction
- `transaction_type`: Type of transaction (deposit, withdrawal, transfer, etc.)
- `account_number`: Account identifier

### Enhanced Balance Tracking

- `old_balance`: Account balance before transaction
- `new_balance`: Account balance after transaction
- `balance_change`: Calculated field (new_balance - old_balance)

### Multiple Date Fields

- `transaction_date`: Date when transaction occurred
- `value_date`: Date when transaction takes effect
- `posting_date`: Date when transaction was posted to account
- `effective_date`: Date when transaction becomes effective
- `primary_date`: Smart date field (prefers value_date over transaction_date over date)

### Transaction Details

- `channel`: Transaction channel (ATM, POS, ONLINE, BANK, etc.)
- `reference`: Transaction reference number
- `check_number`: Check number (if applicable)
- `memo`: Additional transaction memo
- `category`: Transaction category
- `subcategory`: Transaction subcategory

### Financial Metadata

- `exchange_rate`: Exchange rate for foreign currency transactions
- `foreign_currency`: Foreign currency code
- `foreign_amount`: Amount in foreign currency
- `fees`: Transaction fees
- `interest`: Interest earned or paid
- `tax`: Tax amount

### Account Information

- `currency`: Transaction currency
- `country_code`: Country code

### Processing Metadata

- `raw_text`: Original text data
- `raw_json`: Original JSON data
- `source_file`: Source file path
- `parser_name`: Parser used for extraction

## Configuration Examples

### CSV Parser Configuration

```toml
[[accounts]]
name = "generic_csv_example"
parser = "generic_csv"
file_pattern = "example_transactions.csv"
account_number = "123456789"
currency = "THB"
country_code = "TH"
```

### JSON Parser Configuration

```toml
[[accounts]]
name = "generic_json_example"
parser = "generic_json"
file_pattern = "example_transactions.json"
account_number = "123456789"
currency = "THB"
country_code = "TH"
```

### Fixed-Width Parser Configuration

```toml
[[accounts]]
name = "generic_fixed_width_example"
parser = "generic_fixed_width"
file_pattern = "example_transactions.txt"
account_number = "123456789"
currency = "THB"
country_code = "TH"
```

## Field Mapping

### CSV Header Mapping

The CSV parser automatically maps common header variations:

| Standard Field     | CSV Header Variations                             |
| ------------------ | ------------------------------------------------- |
| `date`             | `date`, `transactiondate`, `txdate`, `datetime`   |
| `description`      | `description`, `desc`, `memo`, `note`, `details`  |
| `amount`           | `amount`, `amt`, `value`, `sum`, `total`          |
| `balance`          | `balance`, `bal`, `runningbalance`                |
| `old_balance`      | `oldbalance`, `previousbalance`, `openingbalance` |
| `new_balance`      | `newbalance`, `closingbalance`, `endingbalance`   |
| `transaction_date` | `transactiondate`, `txdate`, `trandate`           |
| `value_date`       | `valuedate`, `effectivedate`, `settlementdate`    |
| `posting_date`     | `postingdate`, `bookdate`, `processeddate`        |
| `effective_date`   | `effectivedate`, `valuedate`, `settlementdate`    |
| `transaction_type` | `type`, `transactiontype`, `txntype`, `category`  |
| `account_number`   | `account`, `accountnumber`, `accno`, `accountid`  |
| `currency`         | `currency`, `curr`, `ccy`                         |
| `country_code`     | `country`, `countrycode`, `cc`                    |
| `channel`          | `channel`, `method`, `source`, `medium`           |
| `reference`        | `reference`, `ref`, `id`, `transactionid`         |
| `check_number`     | `checknumber`, `checkno`, `cheque`                |
| `memo`             | `memo`, `note`, `comment`, `details`              |
| `category`         | `category`, `cat`, `type`                         |
| `subcategory`      | `subcategory`, `subcat`, `subtype`                |
| `exchange_rate`    | `exchangerate`, `rate`, `fxrate`                  |
| `foreign_currency` | `foreigncurrency`, `fxcurrency`, `origcurrency`   |
| `foreign_amount`   | `foreignamount`, `fxamount`, `origamount`         |
| `fees`             | `fees`, `fee`, `charges`                          |
| `interest`         | `interest`, `int`, `earnings`                     |
| `tax`              | `tax`, `taxes`, `withholding`                     |

### JSON Key Mapping

The JSON parser normalizes keys by:

- Converting to lowercase
- Removing spaces, underscores, and hyphens
- Mapping to standard field names

## Usage Examples

### Example CSV File

```csv
Date,Description,Amount,Old_Balance,New_Balance,Transaction_Date,Value_Date,Transaction_Type,Account_Number,Currency,Country_Code,Channel,Reference,Check_Number,Memo,Category,Subcategory,Exchange_Rate,Foreign_Currency,Foreign_Amount,Fees,Interest,Tax
2024-01-15,Salary Deposit,50000.00,0.00,50000.00,2024-01-15,2024-01-15,deposit,123456789,THB,TH,BANK,REF001,,Monthly salary,Income,Salary,,,0.00,0.00,0.00
2024-01-16,Grocery Shopping,-1500.50,50000.00,48499.50,2024-01-16,2024-01-16,withdrawal,123456789,THB,TH,POS,REF002,,Food purchase,Expense,Groceries,,,0.00,0.00,0.00
```

### Example JSON File

```json
{
  "transactions": [
    {
      "date": "2024-01-15",
      "description": "Salary Deposit",
      "amount": 50000.0,
      "old_balance": 0.0,
      "new_balance": 50000.0,
      "transaction_date": "2024-01-15",
      "value_date": "2024-01-15",
      "transaction_type": "deposit",
      "account_number": "123456789",
      "currency": "THB",
      "country_code": "TH",
      "channel": "BANK",
      "reference": "REF001",
      "category": "Income",
      "subcategory": "Salary",
      "fees": 0.0,
      "interest": 0.0,
      "tax": 0.0
    }
  ]
}
```

## Error Handling

### CSV Parser Errors

- **Missing headers**: Raises error if no headers found
- **Invalid dates**: Skips rows with unparseable dates
- **Invalid amounts**: Skips rows with unparseable amounts
- **Encoding issues**: Tries UTF-8, then Latin-1

### JSON Parser Errors

- **Invalid JSON**: Raises error for malformed JSON
- **Missing fields**: Uses defaults for optional fields
- **Type conversion**: Handles various data types gracefully

### Fixed-Width Parser Errors

- **Field detection failure**: Raises error if field positions cannot be determined
- **Pattern matching**: Uses regex patterns to identify fields
- **Line parsing**: Skips lines that don't match expected patterns

## Best Practices

### File Preparation

1. **Clean data**: Remove extra spaces and special characters
2. **Consistent format**: Use consistent date and number formats
3. **Header naming**: Use descriptive, consistent header names
4. **Encoding**: Use UTF-8 encoding for international characters

### Configuration

1. **Account details**: Provide complete account information
2. **File patterns**: Use specific file patterns for better matching
3. **Currency codes**: Use standard ISO currency codes
4. **Country codes**: Use standard ISO country codes

### Data Quality

1. **Validation**: Verify data after import
2. **Deduplication**: Check for duplicate transactions
3. **Balance verification**: Verify running balances
4. **Category assignment**: Review and adjust categories

## Troubleshooting

### Common Issues

**CSV Parser Issues**:

- **Wrong delimiter detected**: Check file for mixed delimiters
- **Date parsing errors**: Verify date format consistency
- **Amount parsing errors**: Check for currency symbols or formatting

**JSON Parser Issues**:

- **Structure not recognized**: Verify JSON structure matches expected format
- **Field mapping errors**: Check key names and normalization
- **Type conversion errors**: Verify data types in JSON

**Fixed-Width Parser Issues**:

- **Field detection failure**: Check for consistent field positions
- **Pattern matching errors**: Verify date and amount patterns
- **Description extraction**: Check for field boundary conflicts

### Debugging Tips

1. **Check raw data**: Examine original file content
2. **Verify field mapping**: Confirm header/key mapping
3. **Test with sample data**: Use small test files first
4. **Review error logs**: Check parser error messages

## Performance Considerations

### Large Files

- **Memory usage**: Parsers process files line by line
- **Processing time**: Linear time complexity
- **Database operations**: Batch inserts for better performance

### Optimization

- **Index usage**: Database indexes on frequently queried fields
- **Field selection**: Only extract needed fields
- **Error handling**: Skip problematic rows to continue processing

## Future Enhancements

### Planned Features

- **Machine learning**: Automatic field detection and categorization
- **Multi-language support**: International character handling
- **Advanced validation**: Business rule validation
- **Real-time processing**: Stream processing for large files
- **API integration**: Direct bank API connections
- **Advanced analytics**: Transaction pattern analysis
