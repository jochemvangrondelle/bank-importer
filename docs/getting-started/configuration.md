# Configuration Guide

Learn how to configure Bank Importer Thailand for your bank accounts and export targets.

## Configuration File

The configuration file (`config.toml`) is created when you run `bank-importer init`. It uses TOML format.

## Environment Variables and File-Based Secrets

Any configuration value can be provided via environment variables or file-based secrets, with the following priority:

1. **Environment variables** (highest priority)
2. **File-based secrets** (`{key}_file` attributes)
3. **TOML values** (fallback)

### Environment Variable Naming

Environment variables follow a hierarchical naming convention:

- **Account-level**: `ACCOUNTS_{ACCOUNT_NAME}_{KEY}`

  - Example: `ACCOUNTS_KRUNGSRI_PDF_PASSWORD` for account `krungsri_pdf` password
  - Example: `ACCOUNTS_MY_ACCOUNT_PASSWORD` for account `my-account` password

- **Nested configs**: `{SECTION}_{SUBSECTION}_{KEY}`

  - Example: `TRANSLATION_GOOGLE_TRANSLATE_API_KEY` for `[translation] google_translate_api_key`
  - Example: `ACCOUNTS_MY_ACCOUNT_TRANSLATION_API_KEY` for account-specific translation API key

- **Top-level**: `{SECTION}_{KEY}`
  - Example: `DATABASE_URL` for `[database] url`

Account names are normalized: hyphens and underscores are converted to underscores, then uppercased.

### File-Based Secrets

Use `{key}_file` attributes to read secrets from files:

```toml
[[accounts]]
name = "krungsri_pdf"
password_file = "~/secrets/krungsri_password.txt"
# password = "fallback-value"  # Optional fallback if file doesn't exist
```

File paths support `~` expansion (home directory). The file content is read and whitespace is stripped.

### Examples

#### Account Password via Environment Variable

```bash
export ACCOUNTS_KRUNGSRI_PDF_PASSWORD="my-secret-password"
```

```toml
[[accounts]]
name = "krungsri_pdf"
# password will be read from ACCOUNTS_KRUNGSRI_PDF_PASSWORD
```

#### Account Password via File

```toml
[[accounts]]
name = "krungsri_pdf"
password_file = "~/secrets/krungsri_password.txt"
```

#### Translation API Key via Environment Variable

```bash
export TRANSLATION_GOOGLE_TRANSLATE_API_KEY="<example>"
```

```toml
[translation]
# google_translate_api_key will be read from TRANSLATION_GOOGLE_TRANSLATE_API_KEY
```

## Account Configuration

Each bank account requires a configuration section:

```toml
[accounts.my-account]
name = "My Bank Account"
bank_name = "Krungsri"
account_number = "XXX-1-12345-X"
currency = "THB"
parser = "krungsri_pdf"
file_path = "data/raw/krungsri"
password = "your-pdf-password"
```

### Account Fields

- **name**: Unique identifier for the account
- **bank_name**: Name of the bank (e.g., "Krungsri", "SCB")
- **account_number**: Your account number
- **currency**: Currency code (e.g., "THB", "USD")
- **parser**: Parser to use (see available parsers below)
- **file_path**: Directory containing bank statement files
- **password**: Password for password-protected PDFs (optional)

### Available Parsers

- `krungsri_pdf`: Krungsri PDF statements
- `krungsri_text`: Krungsri text files
- `scb_pdf`: SCB PDF statements
- `generic_csv`: Generic CSV files
- `generic_json`: Generic JSON files
- `generic_fixed_width`: Fixed-width text files
- `amex_th_csv`: American Express Thailand CSV

## Translation Configuration

Enable automatic translation of Thai transaction descriptions:

```toml
[translation]
enabled = true
source_language = "th"
target_language = "en"
use_term_mapping = true
api_key = "your-google-translate-api-key"  # Optional
```

### Account-Specific Translation

```toml
[accounts.my-account]
# ... other fields ...

[accounts.my-account.translation]
enabled = true
source_language = "th"
target_language = "en"
```

## Export Targets

Configure export targets:

```toml
[[targets]]
name = "csv"
enabled = true
output_dir = "data/out"

[[targets]]
name = "yaml"
enabled = true
output_dir = "data/out"
```

## Advanced Configuration

See the [Generic Parsers Guide](../user-guides/generic-parsers.md) for configuring CSV, JSON, and fixed-width parsers.
