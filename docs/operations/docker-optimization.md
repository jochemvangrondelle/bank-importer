# Docker Optimization Guide

This document describes the Docker optimization strategies used in Bank Importer Thailand.

## Image Size Optimization

### Base Image Selection

We use `python:3.13-slim-bookworm` as the base image, which provides:

- **Small size**: ~150MB base image (vs ~900MB for full Python image)
- **Security**: Regular security updates from Debian
- **Compatibility**: Full compatibility with Python packages (unlike Alpine)
- **Performance**: Better performance than Alpine for Python workloads

### Why Not Alpine?

While Alpine Linux (~5MB base) is smaller, we avoid it because:

- **PDF processing**: `pdfplumber` and related libraries require additional dependencies
- **Compatibility**: Some Python packages have compatibility issues with musl libc
- **Build complexity**: Requires more build dependencies and longer build times
- **Runtime performance**: glibc-based images perform better for Python workloads

### Multi-Stage Build

The Dockerfile uses a multi-stage build pattern:

1. **Builder stage**: Contains build tools and compiles dependencies
2. **Production stage**: Contains only runtime dependencies and compiled packages

This reduces the final image size by excluding:

- Build tools (gcc, make, etc.)
- Development dependencies
- Source code and build artifacts
- Package manager caches

## Build Optimization

### Layer Caching

The Dockerfile is structured to maximize layer caching:

```dockerfile
# Dependencies are copied first (changes less frequently)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Application code is copied last (changes more frequently)
COPY src/ ./src/
```

This ensures that dependency installation is cached when only application code changes.

### Dependency Installation

- **Frozen lockfile**: Uses `uv.lock` for reproducible builds
- **No dev dependencies**: `--no-dev` flag excludes development packages
- **No editable installs**: `--no-editable` prevents unnecessary file copying
- **Single layer**: Dependencies installed in one RUN command

### File Exclusions

The `.dockerignore` file excludes:

- Test files and test data
- Documentation (except README.md for package metadata)
- Development tools and IDE files
- Build artifacts and caches
- CI/CD configuration files

## Runtime Optimization

### Minimal Runtime Dependencies

Only essential runtime dependencies are installed:

- `libmagic1`: Required for file type detection
- Python runtime: From slim base image

### Environment Variables

Optimized environment variables:

- `PYTHONUNBUFFERED=1`: Ensures immediate output
- `PYTHONDONTWRITEBYTECODE=1`: Prevents `.pyc` file creation
- `PATH`: Includes virtual environment

### User Permissions

- Runs as non-root user (`appuser`)
- Minimal file permissions
- Read-only mounts for input data

## Build Performance

### GitHub Actions Optimization

- **Build cache**: Uses GitHub Actions cache for Docker layers
- **Multi-platform**: Builds for both AMD64 and ARM64
- **Parallel builds**: Builds and tests run in parallel
- **Cache sharing**: Build cache shared across workflows

### Local Build Optimization

For local development, you can optimize builds:

```bash
# Build with cache
docker build --cache-from ghcr.io/jochemvangrondelle/bank-importer:latest .

# Build for specific platform (faster)
docker build --platform linux/amd64 .

# Use BuildKit for better caching
DOCKER_BUILDKIT=1 docker build .
```

## Image Size Comparison

| Image Type    | Size       | Notes                                   |
| ------------- | ---------- | --------------------------------------- |
| Full Python   | ~900MB     | Includes all development tools          |
| Python Slim   | ~150MB     | Minimal runtime, our choice             |
| Alpine        | ~50MB      | Compatibility issues with PDF libraries |
| Our Optimized | ~200-300MB | Includes all dependencies               |

## Further Optimization Tips

### If Size is Critical

1. **Use distroless images**: Consider `gcr.io/distroless/python3` for even smaller images
2. **Remove unnecessary files**: Clean up any temporary files in final stage
3. **Compress layers**: Use `docker-squash` to combine layers (not recommended for production)
4. **Analyze image**: Use `dive` to identify large files

### If Build Speed is Critical

1. **Use build cache**: Ensure `.dockerignore` is comprehensive
2. **Parallel builds**: Build multiple images in parallel
3. **Layer optimization**: Order commands by change frequency
4. **Use BuildKit**: Enable BuildKit for better caching

## Monitoring

### Check Image Size

```bash
docker images ghcr.io/jochemvangrondelle/bank-importer
```

### Analyze Image Layers

```bash
docker history ghcr.io/jochemvangrondelle/bank-importer:latest
```

### Use Dive for Analysis

```bash
dive ghcr.io/jochemvangrondelle/bank-importer:latest
```

## Best Practices

1. **Keep base image updated**: Regularly update to latest slim image
2. **Minimize layers**: Combine RUN commands where possible
3. **Use specific tags**: Pin base image versions for reproducibility
4. **Clean up**: Remove package caches and temporary files
5. **Test regularly**: Ensure optimizations don't break functionality

## Current Optimizations

✅ Multi-stage build
✅ Minimal base image (slim-bookworm)
✅ Layer caching optimization
✅ Comprehensive .dockerignore
✅ No dev dependencies in production
✅ Non-root user
✅ Minimal runtime dependencies
✅ Build cache in CI/CD
✅ Multi-platform support

## Future Improvements

- [ ] Consider distroless images for even smaller size
- [ ] Analyze and remove any unnecessary dependencies
- [ ] Optimize Python package installation further
- [ ] Consider using `pip-tools` for dependency optimization
- [ ] Explore using `uv` for faster dependency resolution
