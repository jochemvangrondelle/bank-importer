# Docker Best Practices Applied

This document outlines the Docker best practices implemented in the Dockerfile and docker-compose.yml.

## 1. Rootless Containers ✅

### 1.1 Non-Root User

- ✅ Container runs as non-root user (`appuser`)
- ✅ User is created as a system user without a specific UID
- ✅ This allows platforms like Openshift to use random UIDs

### 1.2 Generic UID (Not Bound to Specific UID)

- ✅ User created without `--uid` flag: `useradd --system --gid appuser --create-home appuser`
- ✅ Temporary data uses `/tmp` (world-writable, supports any UID)
- ✅ Data directories have appropriate permissions (755) for any UID
- ✅ Environment variable `APP_TMP_DATA=/tmp` allows configuration if needed

### 1.3 Executables Owned by Root

- ✅ Virtual environment (`/app/.venv`) owned by root
- ✅ Application files (`/app/src`) owned by root
- ✅ Entrypoint script (`/usr/local/bin/docker-entrypoint.sh`) owned by root with 755 permissions
- ✅ User only needs execution permissions, not ownership
- ✅ This enforces container immutability - prevents runtime modification of binaries

## 2. Multistage Builds ✅

- ✅ Builder stage uses `ghcr.io/astral-sh/uv:python3.13-bookworm-slim` with all build tools
- ✅ Production stage uses minimal `python:3.13-slim-bookworm` base image
- ✅ Only runtime dependencies copied from builder stage
- ✅ Build tools and intermediate files excluded from final image
- ✅ Reduces attack surface and image size

## 3. Tiny Base Image ✅

- ✅ Uses `python:3.13-slim-bookworm` (Debian slim variant)
- ✅ Only installs essential runtime dependency (`libmagic1`)
- ✅ Removes apt cache and build tools after installation
- ✅ Uses Python 3.13 (stable, LTS support)

## 4. Exposed Ports ✅

- ✅ Only exposes port 8000 (API port)
- ✅ Uses `EXPOSE 8000` for documentation
- ✅ Port mapping configured in docker-compose.yml
- ✅ No unnecessary ports exposed (e.g., SSH port 22)

## 5. Credentials and Confidentiality ✅

- ✅ No secrets hardcoded in Dockerfile
- ✅ Configuration via environment variables
- ✅ Config file mounted as read-only volume
- ✅ Example config (`config-example.toml`) included with safe values
- ✅ Secrets should be provided at runtime via:
  - Environment variables (`-e` flag)
  - Docker secrets
  - Kubernetes secrets
  - Bind-mounted config files

## 6. Health Checks ✅

- ✅ `HEALTHCHECK` instruction included in Dockerfile
- ✅ Checks API health endpoint (`/api/v1/system/health`)
- ✅ Falls back to CLI version check if API unavailable
- ✅ Configured in docker-compose.yml with appropriate intervals

## 7. Additional Best Practices

### 7.1 Layer Caching

- ✅ Dependencies installed before copying source code
- ✅ Uses `--mount=type=cache` for UV cache
- ✅ Uses `--mount=type=bind` for lockfile and pyproject.toml

### 7.2 Security Labels

- ✅ OCI labels for metadata
- ✅ Version information in labels

### 7.3 Resource Limits

- ✅ Configured in docker-compose.yml
- ✅ CPU and memory limits set
- ✅ Prevents resource exhaustion

### 7.4 Logging

- ✅ JSON file logging driver
- ✅ Log rotation configured (max-size, max-file)

## Docker Compose Features

The `docker-compose.yml` includes:

- ✅ Build configuration with build args
- ✅ Multi-platform support (amd64, arm64)
- ✅ Health check configuration
- ✅ Resource limits
- ✅ Volume mounts with appropriate permissions
- ✅ Network isolation
- ✅ Restart policy
- ✅ Logging configuration
- ✅ Environment variable support

## Usage Examples

### Build and Run

```bash
# Build and start
docker-compose up --build

# Run in background
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop
docker-compose down
```

### CLI Commands

```bash
# Run CLI commands
docker-compose run --rm api cli import-files data/in/
docker-compose run --rm api cli export-multi --target csv
docker-compose run --rm api cli status
```

### Environment Variables

```bash
# Override API port
API_PORT=9000 docker-compose up

# Build with specific dependency groups
DEPENDENCY_GROUPS=api docker-compose build
```

## Security Considerations

1. **Non-Root Execution**: Container runs as non-root user
2. **Immutable Binaries**: Executables owned by root, not writable
3. **No Secrets in Image**: All secrets provided at runtime
4. **Minimal Attack Surface**: Only essential dependencies included
5. **Read-Only Volumes**: Config and input files mounted read-only
6. **Resource Limits**: Prevents resource exhaustion attacks
7. **Health Checks**: Ensures service availability

## Linting

Consider adding hadolint to CI/CD pipeline:

```yaml
# Example GitHub Actions step
- name: Lint Dockerfile
  uses: hadolint/hadolint-action@v2.1.0
  with:
    dockerfile: Dockerfile
    failure-threshold: warning
```

## Image Signing

For production, enable Docker Content Trust:

```bash
export DOCKER_CONTENT_TRUST=1
docker-compose build
docker-compose push
```

## Notes

- The container supports running with any UID (Openshift compatible)
- Temporary data uses `/tmp` to support random UIDs
- All executables are immutable (owned by root)
- Configuration is externalized (no hardcoded values)
- Health checks ensure service availability
