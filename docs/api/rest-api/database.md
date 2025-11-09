# Database Endpoints

Database operations and initialization endpoints.

## GET /database/init

Initialize database.

Creates database tables if they don't exist.

**Response:**
```json
{
  "status": "initialized",
  "tables_created": 10
}
```

## GET /database/status

Get database status.

**Response:**
```json
{
  "status": "connected",
  "url": "sqlite:///bank_importer.db",
  "tables": [
    "transactions",
    "import_sessions",
    "export_sessions"
  ]
}
```

See the [OpenAPI Specification](../openapi.md) for complete details.
