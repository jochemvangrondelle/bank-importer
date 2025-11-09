# Parser Endpoints

Parser information and detection endpoints.

## GET /parsers

List all available parsers.

**Response:**
```json
{
  "parsers": [
    {
      "name": "krungsri_pdf",
      "description": "Krungsri Bank PDF parser",
      "supported_extensions": [".pdf"],
      "bank_type": "krungsri"
    }
  ]
}
```

## GET /parsers/{parser_name}

Get parser information.

## POST /parsers/detect

Detect parser for a file.

**Request:**
```json
{
  "file_path": "statement.pdf",
  "parent_folder_hint": "krungsri"
}
```

**Response:**
```json
{
  "parser_name": "krungsri_pdf",
  "confidence": 0.95
}
```

See the [OpenAPI Specification](../openapi.md) for complete details.
