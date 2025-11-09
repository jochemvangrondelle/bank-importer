# Status Endpoints

Status and statistics endpoints.

## GET /status

Get system status.

**Response:**
```json
{
  "status": "operational",
  "database": "connected",
  "accounts": 3,
  "transactions": 1500
}
```

## GET /status/statistics

Get detailed statistics.

**Response:**
```json
{
  "accounts": {
    "total": 3,
    "active": 2
  },
  "transactions": {
    "total": 1500,
    "by_account": {
      "account1": 500,
      "account2": 1000
    }
  },
  "import_sessions": {
    "total": 50,
    "completed": 45,
    "failed": 2,
    "processing": 3
  },
  "export_sessions": {
    "total": 30,
    "completed": 28,
    "failed": 1,
    "processing": 1
  }
}
```

See the [OpenAPI Specification](../openapi.md) for complete details.
