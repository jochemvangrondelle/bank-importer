# Configuration Centralization

All configuration values have been centralized into dedicated configuration files for better maintainability and environment variable support.

## Backend Configuration

**File**: `src/bank_importer/api/config.py`

Uses `pydantic-settings` for type-safe configuration with automatic environment variable loading.

### Features

- ✅ **Type validation**: All settings are type-checked
- ✅ **Environment variables**: Automatic loading from env vars (with `API_` prefix)
- ✅ **Default values**: Sensible defaults for all settings
- ✅ **Backward compatibility**: Legacy uppercase properties maintained
- ✅ **Config file integration**: Still supports reading from `config.toml` for JWT secret

### Environment Variables

All settings can be overridden via environment variables:

```bash
# Server settings
API_HOST=0.0.0.0
API_PORT=8000

# JWT settings
JWT_SECRET_KEY=your-secret-key-here

# CORS settings
CORS_ORIGINS=http://localhost:3000,https://example.com
```

### Configuration Priority

For JWT secret key (highest to lowest):

1. Environment variable: `JWT_SECRET_KEY`
2. Config file: `config.toml` → `[api]` → `jwt_secret_key`
3. Default: `bank-importer-secret-key-change-in-production` (⚠️ insecure!)

### Usage

```python
from bank_importer.api.config import settings

# Access settings
host = settings.host
port = settings.port
secret_key = settings.get_jwt_secret_key(config_manager)

# Legacy uppercase properties still work
host = settings.DEFAULT_HOST
port = settings.DEFAULT_PORT
```

## Frontend Configuration

**File**: `src/frontend/src/config/settings.ts`

Centralized TypeScript configuration with environment variable support.

### Features

- ✅ **Type-safe**: Full TypeScript type checking
- ✅ **Environment variables**: Via Vite's `VITE_*` prefix
- ✅ **Grouped by domain**: API, Auth, UI, Upload, Export configs
- ✅ **Error/Success messages**: Centralized user-facing messages

### Environment Variables

```bash
# API Configuration
VITE_API_URL=/api/v1  # Relative URL for production, absolute for dev
VITE_APP_NAME=Bank Importer TH
```

### Configuration Groups

- **API_CONFIG**: API endpoints and base URL
- **APP_CONFIG**: Application name and version
- **AUTH_CONFIG**: Authentication settings (token storage, redirects)
- **UI_CONFIG**: UI defaults (page sizes, date formats)
- **UPLOAD_CONFIG**: File upload limits and allowed types
- **EXPORT_CONFIG**: Export target options
- **ERROR_MESSAGES**: User-facing error messages
- **SUCCESS_MESSAGES**: User-facing success messages

### Usage

```typescript
import { API_CONFIG, AUTH_CONFIG, APP_CONFIG } from "../config/settings";

// Use in code
const loginUrl = API_CONFIG.ENDPOINTS.AUTH.LOGIN;
const tokenKey = AUTH_CONFIG.TOKEN_STORAGE_KEY;
const appName = APP_CONFIG.NAME;
```

## Migration Guide

### Backend

**Before:**

```python
SECRET_KEY = "bank-importer-secret-key-change-in-production"
ALGORITHM = "HS256"
```

**After:**

```python
from bank_importer.api.config import settings

secret_key = settings.get_jwt_secret_key(config)
algorithm = settings.jwt_algorithm
# Or use legacy properties:
algorithm = settings.JWT_ALGORITHM
```

### Frontend

**Before:**

```typescript
const API_URL = "http://localhost:8000/api/v1";
localStorage.setItem("token", token);
```

**After:**

```typescript
import { API_CONFIG, AUTH_CONFIG } from "../config/settings";

const apiUrl = API_CONFIG.BASE_URL;
localStorage.setItem(AUTH_CONFIG.TOKEN_STORAGE_KEY, token);
```

## Benefits

1. **Single source of truth**: All config values in one place
2. **Environment-aware**: Easy to override for different environments
3. **Type safety**: Catch configuration errors at development time
4. **Documentation**: Self-documenting with descriptions
5. **Validation**: Automatic validation of configuration values
6. **Maintainability**: Easy to find and update configuration

## Production Recommendations

1. **Set JWT_SECRET_KEY**: Always set via environment variable in production
2. **Configure CORS**: Set `CORS_ORIGINS` to specific domains, not `*`
3. **Use secrets management**: Store sensitive values in environment variables or secrets manager
4. **Review defaults**: Check all default values before deploying
