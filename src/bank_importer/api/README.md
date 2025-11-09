# Bank Importer TH API

FastAPI-based REST API for Bank Importer TH.

## Running the API

### Development Server

```bash
# Using uvicorn directly
uvicorn bank_importer.api.main:app --reload --host 0.0.0.0 --port 8000

# Or using the run script
python -m bank_importer.api.run
```

### Production Server

```bash
uvicorn bank_importer.api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API Documentation

Once the server is running, access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/api/v1/docs
- **ReDoc**: http://localhost:8000/api/v1/redoc
- **OpenAPI JSON**: http://localhost:8000/api/v1/openapi.json

## API Endpoints

All endpoints are prefixed with `/api/v1`:

- `/api/v1/system` - System endpoints (health, version)
- `/api/v1/config` - Configuration management
- `/api/v1/parsers` - Parser information
- `/api/v1/import` - File import operations
- `/api/v1/transactions` - Transaction management
- `/api/v1/export` - Export operations
- `/api/v1/translation` - Translation service
- `/api/v1/status` - Status and statistics
- `/api/v1/database` - Database operations

## Example Usage

### Health Check

```bash
curl http://localhost:8000/api/v1/system/health
```

### List Accounts

```bash
curl http://localhost:8000/api/v1/config/accounts
```

### Import Files

```bash
curl -X POST http://localhost:8000/api/v1/import/files \
  -H "Content-Type: application/json" \
  -d '{
    "file_paths": ["data/in"],
    "account_name": "my_account"
  }'
```

### Get Transactions

```bash
curl "http://localhost:8000/api/v1/transactions?account_number=12345&limit=10"
```

## Configuration

The API uses the same `config.toml` file as the CLI. Make sure it exists and is properly configured before starting the API server.
