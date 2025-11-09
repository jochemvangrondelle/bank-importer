# Parse API Endpoints

The Parse API provides modular endpoints for parsing bank statement files without requiring database setup. These endpoints are ideal for one-off parsing operations or when you need immediate results.

## Endpoints

### Parse File

**`POST /api/v1/parse/file`**

Parse a bank statement file and return transactions as JSON (synchronous, no database).

**Request**: `multipart/form-data`

**Parameters**:

- `file` (required): Bank statement file to parse
- `account_config_name` (optional): Name of account configuration to use (recommended for security)
- `parser_name` (optional): Parser name to use (auto-detects if not provided)
  - Available values: `amex_th_csv`, `krungsri_pdf`, `krungsri_text`, `scb_pdf`, `generic_csv`, `generic_json`, `generic_fixed_width`
- `account_number` (optional): Account number (required if `account_config_name` not provided)
- `account_name` (optional): Account display name (required if `account_config_name` not provided)
- `bank_name` (optional): Bank name (required if `account_config_name` not provided)
- `currency` (optional): Currency code (ISO 4217), default: `THB`
  - Available values: `THB`, `USD`, `EUR`, `GBP`, `JPY`, `SGD`, `MYR`, `IDR`, `PHP`, `VND`, `CNY`, `HKD`, `AUD`, `NZD`, `KRW`, `INR`, `CHF`, `CAD`
- `country_code` (optional): Country code (ISO 3166-1 alpha-2), default: `TH`
- `password` (optional): Password for password-protected PDFs (less secure - prefer `account_config_name`)
- `parser_detection_behavior` (optional): Parser detection behavior, default: `automatic`
  - `automatic`: Auto-detect parser if `parser_name` is not provided
  - `manual`: Require parser to be specified, fail if not provided

**Response**: `200 OK`

```json
{
  "transactions": [
    {
      "date": "2024-01-15T00:00:00",
      "description": "Transaction description",
      "amount": "1000.00",
      "balance": "5000.00",
      "transaction_type": "debit",
      "account_number": "1234567890",
      "currency": "THB",
      "country_code": "TH"
    }
  ],
  "parser_name": "krungsri_pdf",
  "total_transactions": 1
}
```

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
  -F "currency=THB" \
  -F "password=mypassword"
```

### Parse and Export File

**`POST /api/v1/parse/file/export`**

Parse a bank statement file and export to CSV/YAML (synchronous, no database).

**Request**: `multipart/form-data`

**Parameters**:

- `file` (required): Bank statement file to parse and export
- `account_config_name` (optional): Name of account configuration to use (recommended for security)
- `parser_name` (optional): Parser name to use (auto-detects if not provided)
- `account_number` (optional): Account number (required if `account_config_name` not provided)
- `account_name` (optional): Account display name (required if `account_config_name` not provided)
- `bank_name` (optional): Bank name (required if `account_config_name` not provided)
- `currency` (optional): Currency code (ISO 4217), default: `THB`
- `country_code` (optional): Country code (ISO 3166-1 alpha-2), default: `TH`
- `password` (optional): Password for password-protected PDFs (less secure - prefer `account_config_name`)
- `target_name` (optional): Export target name, default: `csv`
  - Available values: `csv`, `yaml`, `firefly`
- `auto_detect` (optional): Auto-detect parser if `parser_name` is not provided, default: `true`

**Response**: `200 OK` - Returns the exported file (CSV, YAML, etc.) as a download

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
  -F "currency=THB" \
  -F "password=mypassword" \
  -F "target_name=csv" \
  -o output.csv
```

### Parse File by Path

**`POST /api/v1/parse/file/path`**

Parse a file by path and return transactions (synchronous, no database). Use this when files are already available on the server.

**Request**: `application/json`

**Body**:

```json
{
  "file_path": "/data/in/statement.pdf",
  "parser_name": "krungsri_pdf",
  "account_number": "1234567890",
  "account_name": "My Account",
  "bank_name": "Krungsri",
  "currency": "THB",
  "country_code": "TH",
  "password": "mypassword",
  "auto_detect": true
}
```

**Response**: Same as `POST /api/v1/parse/file`

## Security Considerations

### Account-based Configuration (Recommended)

For production use, prefer `account_config_name` with passwords stored securely:

1. **Environment Variables**: Set `ACCOUNTS_{ACCOUNT_NAME}_PASSWORD` environment variable
2. **File-based Secrets**: Use `password_file` in config pointing to a secure file

**Example**:

```bash
# Set password in environment
export ACCOUNTS_KRUNGSRI_PDF_PASSWORD="my-secret-password"

# Use account config name (password loaded from env)
curl -X POST "http://localhost:8000/api/v1/parse/file" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@statement.pdf" \
  -F "account_config_name=krungsri_pdf"
```

### Direct Password Mode (Less Secure)

Direct password transmission is less secure but useful for one-off operations. The password is transmitted over the network, so ensure you're using HTTPS in production.

## Error Responses

### 400 Bad Request

Invalid request parameters or missing required fields.

```json
{
  "detail": "Either 'account_config_name' or all of 'account_number', 'account_name', and 'bank_name' must be provided"
}
```

### 404 Not Found

Account configuration not found.

```json
{
  "detail": "Account configuration 'krungsri_pdf' not found"
}
```

### 500 Internal Server Error

Error parsing file or processing request.

```json
{
  "detail": "Error parsing file: <error message>"
}
```

## See Also

- [Import API](import.md) - For database-backed import operations
- [Parsers API](parsers.md) - For parser information and detection
- [Configuration Guide](../../getting-started/configuration.md) - For account configuration setup
