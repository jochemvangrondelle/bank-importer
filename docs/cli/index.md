# CLI Reference

The Bank Importer Thailand command-line interface provides easy-to-use commands for importing, exporting, and managing bank transactions.

## Installation

### Python CLI

Install CLI support:

```bash
uv sync --group cli
```

## Commands

### `init`

Initialize a new configuration file.

```bash
bank-importer init
```

Creates a default `config.toml` file with example configuration.

### `configure`

Interactive configuration management.

```bash
bank-importer configure
```

Allows you to:

- Configure application settings (database URL, output directory, timezone)
- Manage accounts (create, edit, delete)
- Manage export targets (enable/disable, configure)

### `import`

Import bank statement files and parse transactions.

```bash
bank-importer import [PATHS...] [OPTIONS]
```

**Arguments:**

- `PATHS`: Paths to files or directories to import (default: `data/`)

**Options:**

- `--account, -a`: Process specific account only
- `--config, -c`: Configuration file path (default: `config.toml`)
- `--verbose, -v`: Verbose console output
- `--dry-run, -d`: Dry run mode (no file operations)
- `--reprocess-existing`: Reprocess files that have already been imported

**Examples:**

```bash
# Import all files in data/ directory
bank-importer import

# Import specific directory
bank-importer import data/in/krungsri/

# Import specific account
bank-importer import --account my-account

# Dry run to see what would be processed
bank-importer import --dry-run
```

### `export`

Export transactions to targets with multiple files (per source file + consolidated).

```bash
bank-importer export [OPTIONS]
```

**Options:**

- `--target, -t`: Export to specific target (csv, yaml, firefly)
- `--config, -c`: Configuration file path (default: `config.toml`)
- `--verbose, -v`: Verbose console output
- `--dry-run, -d`: Dry run mode (no exports performed)

**Examples:**

```bash
# Export to all enabled targets
bank-importer export

# Export to CSV only
bank-importer export --target csv

# Dry run
bank-importer export --dry-run
```

### `run`

Run the complete pipeline: status + import + export + status.

```bash
bank-importer run [OPTIONS]
```

**Options:**

- `--account, -a`: Process specific account only
- `--config, -c`: Configuration file path (default: `config.toml`)
- `--verbose, -v`: Verbose console output
- `--dry-run, -d`: Dry run mode

**Example:**

```bash
# Run full pipeline for all accounts
bank-importer run

# Run for specific account
bank-importer run --account my-account
```

### `status`

Show current status and statistics.

```bash
bank-importer status [OPTIONS]
```

**Options:**

- `--config, -c`: Configuration file path (default: `config.toml`)

**Example:**

```bash
bank-importer status
```

### `translate`

Translate transaction descriptions.

```bash
bank-importer translate [OPTIONS]
```

**Options:**

- `--account, -a`: Translate for specific account only
- `--config, -c`: Configuration file path (default: `config.toml`)
- `--verbose, -v`: Verbose console output

### `list-parsers`

List all available parsers.

```bash
bank-importer list-parsers
```

### `clean`

Clean output directories and internal database.

```bash
bank-importer clean [OPTIONS]
```

**Options:**

- `--force, -f`: Skip confirmation prompt
- `--output-only`: Only clean output directories, not database
- `--db-only`: Only clean database, not output directories
- `--config, -c`: Configuration file path (default: `config.toml`)
- `--verbose, -v`: Verbose console output

**Example:**

```bash
# Clean everything (with confirmation)
bank-importer clean

# Clean without confirmation
bank-importer clean --force

# Clean only output files
bank-importer clean --output-only
```

### `version`

Show version information.

```bash
bank-importer version
```

### `coverage`

Show code coverage information (development).

```bash
bank-importer coverage
```

## Global Options

All commands support these global options:

- `--config, -c`: Configuration file path (default: `config.toml`)
- `--verbose, -v`: Enable verbose output
- `--help, -h`: Show help message

## Configuration

Commands use the configuration file specified with `--config` (default: `config.toml`). See the [Configuration Guide](../getting-started/configuration.md) for details.

## Examples

### Complete Workflow

```bash
# 1. Initialize configuration
bank-importer init

# 2. Configure accounts interactively
bank-importer configure

# 3. Import bank statements
bank-importer import data/in/

# 4. Check status
bank-importer status

# 5. Export to CSV
bank-importer export --target csv

# 6. Or run everything at once
bank-importer run --account my-account
```

### Batch Processing

```bash
# Import multiple directories
bank-importer import data/in/krungsri/ data/in/scb/

# Export to multiple targets
bank-importer export --target csv
bank-importer export --target yaml
```

### Development and Testing

```bash
# Dry run to test without making changes
bank-importer import --dry-run
bank-importer export --dry-run

# Verbose output for debugging
bank-importer import --verbose
```

## See Also

- [Getting Started Guide](../getting-started/quick-start.md)
- [Configuration Guide](../getting-started/configuration.md)
- [Library API Reference](../api/library.md)
