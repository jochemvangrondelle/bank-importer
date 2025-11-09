# Import Endpoints

File import and transaction management endpoints.

## POST /import/files

Import files (async job).

**Request:**
```json
{
  "account_name": "my-account",
  "reprocess_existing": false
}
```

**Response:**
```json
{
  "job_id": "uuid-here",
  "status": "processing",
  "message": "Import job started"
}
```

## GET /import/sessions

List import sessions.

**Query Parameters:**
- `account_name`: Filter by account name
- `status`: Filter by status
- `limit`: Maximum number of results (default: 100)
- `offset`: Number of results to skip (default: 0)

## GET /import/sessions/{session_id}

Get import session details.

## GET /import/sessions/{session_id}/transactions

Get transactions for an import session.

**Query Parameters:**
- `limit`: Maximum number of results (default: 100)
- `offset`: Number of results to skip (default: 0)

See the [OpenAPI Specification](../openapi.md) for complete details.
