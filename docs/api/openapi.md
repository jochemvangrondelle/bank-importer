# OpenAPI Specification

The Bank Importer Thailand REST API is fully documented using OpenAPI 3.1.0.

## Specification File

The complete OpenAPI specification is available at:

- **File**: [api/openapi.yaml](../../api/openapi.yaml)
- **Format**: YAML (OpenAPI 3.1.0)

## Interactive Documentation

When running the API server, interactive documentation is available at:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## Specification Details

### Version

- **API Version**: 1.0.0
- **OpenAPI Version**: 3.1.0

### Servers

- **Development**: `http://localhost:8000/api/v1`
- **Production**: `https://api.example.com/api/v1` (configure as needed)

### Tags

The API is organized into the following tags:

- **System**: System information and health
- **Configuration**: Configuration management
- **Parsers**: Parser information and detection
- **Import**: File import and transaction management
- **Export**: Transaction export to targets
- **Translation**: Translation service management
- **Status**: Status and statistics
- **Database**: Database operations

## Using the Specification

### Generate Client Code

You can generate client code for various languages using tools like:

- **OpenAPI Generator**: [openapi-generator.tech](https://openapi-generator.tech/)
- **Swagger Codegen**: [swagger.io/tools/swagger-codegen](https://swagger.io/tools/swagger-codegen/)

### Example: Generate Python Client

```bash
# Install OpenAPI Generator
npm install -g @openapi-generator-plus/cli

# Generate Python client
openapi-generator-plus generate \
  --generator python \
  --input api/openapi.yaml \
  --output ./generated-client
```

### Validate the Specification

```bash
# Using swagger-cli
npm install -g swagger-cli
swagger-cli validate api/openapi.yaml

# Using openapi-cli
npm install -g @apidevtools/swagger-cli
swagger-cli validate api/openapi.yaml
```

## Schema Definitions

The OpenAPI specification includes detailed schemas for:

- **Request Bodies**: Import requests, export requests, configuration updates
- **Response Models**: Import sessions, export sessions, transactions, status
- **Error Models**: Standard error response format

## Examples

See the [REST API Overview](rest-api.md) for usage examples.

## Contributing

When adding new endpoints:

1. Update `api/openapi.yaml` with the new endpoint
2. Include request/response schemas
3. Add examples where helpful
4. Update this documentation if needed

## See Also

- [REST API Overview](rest-api.md)
- [Library API](library.md)
- [CLI Reference](../cli/index.md)
