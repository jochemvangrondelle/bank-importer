# Export Endpoints

Transaction export endpoints.

## POST /export

Export transactions (async job).

**Request:**
```json
{
  "target_name": "csv"
}
```

**Response:**
```json
{
  "job_id": "uuid-here",
  "status": "processing",
  "message": "Export job started"
}
```

## GET /export/sessions

List export sessions.

**Query Parameters:**
- `target_name`: Filter by target name
- `status`: Filter by status
- `limit`: Maximum number of results (default: 100)
- `offset`: Number of results to skip (default: 0)

## GET /export/sessions/{session_id}

Get export session details.

## GET /export/sessions/{session_id}/download

Download export file.

Returns the exported file as a download.

See the [OpenAPI Specification](../openapi.md) for complete details.
