# Target Manager

The `TargetManager` class manages transaction exports to different target formats.

## Overview

The target manager handles:

- **Target Initialization**: Sets up available export targets (CSV, YAML, Firefly-III)
- **Transaction Export**: Exports transactions to configured targets
- **Export Sessions**: Tracks export operations in the database
- **Account Filtering**: Supports filtering by account reference

## Usage

```python
from bank_importer.config import ConfigManager
from bank_importer.models.database import DatabaseManager
from bank_importer.target_manager import TargetManager

config = ConfigManager()
db = DatabaseManager(config.get_database_url())
target_manager = TargetManager(config, db)

# Export to CSV
result = target_manager.sync_to_target("csv", account_reference="my-account")
```

## Reference

::: bank_importer.target_manager.TargetManager
