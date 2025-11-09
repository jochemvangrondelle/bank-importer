# REST API Overview

The Bank Importer Thailand REST API provides programmatic access to all functionality available through the CLI, enabling web-based UI development and integration with other systems.

## Base URL

```
http://localhost:8000/api/v1
```

For production, replace with your production server URL.

## Authentication

The API supports optional authentication. See the [Security Policy](../project/security.md) for details.

## API Endpoints

### System

- `GET /system/health` - Health check
- `GET /system/info` - System information
- `GET /system/version` - Version information

### Configuration

- `GET /config` - Get current configuration
- `PUT /config` - Update configuration
- `GET /config/accounts` - List accounts
- `POST /config/accounts` - Create account
- `GET /config/accounts/{account_name}` - Get account
- `PUT /config/accounts/{account_name}` - Update account
- `DELETE /config/accounts/{account_name}` - Delete account
- `GET /config/targets` - List targets
- `POST /config/targets` - Create target
- `PUT /config/targets/{target_name}` - Update target
- `DELETE /config/targets/{target_name}` - Delete target

### Parsers

- `GET /parsers` - List available parsers
- `GET /parsers/{parser_name}` - Get parser information
- `POST /parsers/detect` - Detect parser for a file

### Parse

- `POST /parse/file` - Parse a file and return transactions (synchronous, no database)
- `POST /parse/file/export` - Parse a file and export to CSV/YAML (synchronous, no database)
- `POST /parse/file/path` - Parse a file by server path (synchronous, no database)

See [Parse API Documentation](rest-api/parse.md) for details.

### Import

- `POST /import/files` - Import files (async job)
- `POST /import/file` - Import a single file synchronously (with database)
- `GET /import/sessions` - List import sessions
- `GET /import/sessions/{session_id}` - Get import session
- `GET /import/sessions/{session_id}/transactions` - Get session transactions

### Export

- `POST /export` - Export transactions (async job)
- `GET /export/sessions` - List export sessions
- `GET /export/sessions/{session_id}` - Get export session
- `GET /export/sessions/{session_id}/download` - Download export file

### Translation

- `POST /translation/translate` - Translate text
- `GET /translation/terms` - Get translation terms
- `POST /translation/terms` - Add translation term

### Status

- `GET /status` - Get system status
- `GET /status/statistics` - Get statistics

### Database

- `GET /database/init` - Initialize database
- `GET /database/status` - Database status

## OpenAPI Specification

The complete OpenAPI 3.1.0 specification is available:

- **File**: [openapi.yaml](../../api/openapi.yaml)
- **Documentation**: [OpenAPI Documentation](openapi.md)

## Quick Start

### Using cURL

```bash
# Health check
curl http://localhost:8000/api/v1/system/health

# List parsers
curl http://localhost:8000/api/v1/parsers

# Import files
curl -X POST http://localhost:8000/api/v1/import/files \
  -H "Content-Type: application/json" \
  -d '{"account_name": "my-account"}'

# Export transactions
curl -X POST http://localhost:8000/api/v1/export \
  -H "Content-Type: application/json" \
  -d '{"target_name": "csv"}'
```

### Using Python

```python
import requests

base_url = "http://localhost:8000/api/v1"

# Health check
response = requests.get(f"{base_url}/system/health")
print(response.json())

# List parsers
response = requests.get(f"{base_url}/parsers")
parsers = response.json()
print(parsers)

# Import files
response = requests.post(
    f"{base_url}/import/files",
    json={"account_name": "my-account"}
)
job = response.json()
print(f"Job ID: {job['job_id']}")
```

## Response Format

All API responses follow a consistent format:

### Success Response

```json
{
  "status": "success",
  "data": { ... }
}
```

### Error Response

```json
{
  "status": "error",
  "error": {
    "code": "ERROR_CODE",
    "message": "Error message",
    "details": { ... }
  }
}
```

## Status Codes

- `200 OK` - Request successful
- `201 Created` - Resource created
- `202 Accepted` - Request accepted (async job)
- `400 Bad Request` - Invalid request
- `401 Unauthorized` - Authentication required
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

## Rate Limiting

Rate limiting may be applied in production. Check response headers for rate limit information.

## See Also

- [OpenAPI Specification](openapi.md)
- [CLI Reference](../cli/index.md)
- [Library API](library.md)
