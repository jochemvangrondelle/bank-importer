#!/bin/sh
# Check if frontend API client is up-to-date with OpenAPI spec

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
FRONTEND_DIR="$SCRIPT_DIR/.."
API_SPEC="$PROJECT_ROOT/api/openapi.yaml"
GENERATED_DIR="$FRONTEND_DIR/src/api/generated"

# Check if OpenAPI spec exists
if [ ! -f "$API_SPEC" ]; then
    echo "Error: OpenAPI spec not found at $API_SPEC"
    echo "Please generate it first: python3 scripts/generate_openapi.py api/openapi.yaml"
    exit 1
fi

# Check if generated directory exists
if [ ! -d "$GENERATED_DIR" ]; then
    echo "Error: Generated API client directory not found at $GENERATED_DIR"
    echo "Please run: npm run generate:api"
    exit 1
fi

# Generate temporary client to compare
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

echo "Generating temporary API client for comparison..."
cd "$FRONTEND_DIR"

# Use openapi-typescript-codegen directly to generate in temp dir
npx openapi-typescript-codegen --input "$API_SPEC" --output "$TEMP_DIR/generated" --client axios > /dev/null 2>&1 || {
    echo "Error: Failed to generate API client"
    exit 1
}

# Compare generated files using checksums (more reliable than diff)
# Generate checksums for all files
find "$GENERATED_DIR" -type f -exec sha256sum {} \; | sort > "$TEMP_DIR/existing.sha256"
find "$TEMP_DIR/generated" -type f -exec sha256sum {} \; | sort > "$TEMP_DIR/new.sha256"

# Compare checksums
if ! cmp -s "$TEMP_DIR/existing.sha256" "$TEMP_DIR/new.sha256"; then
    echo "❌ Frontend API client is outdated!"
    echo ""
    echo "Differences found between existing client and generated from latest OpenAPI spec."
    echo ""
    echo "To fix, run:"
    echo "  cd frontend"
    echo "  npm run generate:api"
    exit 1
else
    echo "✓ Frontend API client is up-to-date"
    exit 0
fi
