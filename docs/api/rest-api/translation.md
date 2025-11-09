# Translation Endpoints

Translation service management endpoints.

## POST /translation/translate

Translate text.

**Request:**
```json
{
  "text": "จ่ายบิล",
  "source_language": "th",
  "target_language": "en"
}
```

**Response:**
```json
{
  "original": "จ่ายบิล",
  "translated": "Bill Payment",
  "method": "term_mapping"
}
```

## GET /translation/terms

Get translation terms.

## POST /translation/terms

Add translation term.

**Request:**
```json
{
  "source": "จ่ายบิล",
  "target": "Bill Payment",
  "source_language": "th",
  "target_language": "en"
}
```

See the [OpenAPI Specification](../openapi.md) for complete details.
