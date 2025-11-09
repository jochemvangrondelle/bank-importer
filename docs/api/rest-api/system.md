# System Endpoints

System information and health check endpoints.

## GET /system/health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-01T00:00:00Z"
}
```

## GET /system/info

Get system information.

**Response:**
```json
{
  "name": "Bank Importer Thailand",
  "version": "1.0.0",
  "python_version": "3.11.0"
}
```

## GET /system/version

Get version information.

**Response:**
```json
{
  "version": "1.0.0",
  "build_date": "2025-01-01",
  "git_commit": "abc123"
}
```

See the [OpenAPI Specification](../openapi.md) for complete details.
