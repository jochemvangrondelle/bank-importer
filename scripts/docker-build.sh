#!/bin/bash

# Docker Build Script with Buildx support
# Supports both local development and multi-platform builds

set -e

# Default values
PLATFORM="linux/amd64"
PUSH=false
VERSION="latest"
TARGET="production"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to display help
show_help() {
    echo "Docker Build Script for Bank Importer Thailand"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -p, --platform PLATFORM    Target platform (default: linux/amd64)"
    echo "                             Options: linux/amd64, linux/arm64, linux/amd64,linux/arm64"
    echo "  -v, --version VERSION       Image version tag (default: latest)"
    echo "  -t, --target TARGET         Build target (default: production)"
    echo "  --push                      Push to registry after build"
    echo "  --multi-platform            Build for multiple platforms (amd64, arm64)"
    echo "  --local                     Build for local platform only"
    echo "  -h, --help                  Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Build for local platform"
    echo "  $0 --multi-platform --push           # Build and push multi-platform"
    echo "  $0 --platform linux/arm64            # Build for ARM64 only"
    echo "  $0 --version v1.2.3 --push           # Build specific version and push"
    echo ""
}

# Function to check if buildx is available
check_buildx() {
    if ! docker buildx version >/dev/null 2>&1; then
        echo -e "${RED}Error: Docker Buildx is not available${NC}"
        echo "Please install Docker Buildx or update Docker to a newer version"
        exit 1
    fi
}

# Function to create buildx builder if needed
setup_buildx() {
    local builder_name="bank-importer-builder"

    if ! docker buildx inspect "$builder_name" >/dev/null 2>&1; then
        echo -e "${BLUE}Creating buildx builder: $builder_name${NC}"
        docker buildx create --name "$builder_name" --use
    else
        echo -e "${BLUE}Using existing buildx builder: $builder_name${NC}"
        docker buildx use "$builder_name"
    fi
}

# Function to get version from package
get_version() {
    if command -v uv >/dev/null 2>&1; then
        uv run --python 3.11 python -c "from src.bank_importer_th import __version__; print(__version__)" 2>/dev/null || echo "latest"
    else
        echo "latest"
    fi
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -p|--platform)
            PLATFORM="$2"
            shift 2
            ;;
        -v|--version)
            VERSION="$2"
            shift 2
            ;;
        -t|--target)
            TARGET="$2"
            shift 2
            ;;
        --push)
            PUSH=true
            shift
            ;;
        --multi-platform)
            PLATFORM="linux/amd64,linux/arm64"
            shift
            ;;
        --local)
            PLATFORM="linux/amd64"
            LOCAL_BUILD=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

# Auto-detect version if not specified
if [[ "$VERSION" == "latest" ]]; then
    VERSION=$(get_version)
fi

echo -e "${GREEN}Building Bank Importer Thailand${NC}"
echo -e "Platform: ${YELLOW}$PLATFORM${NC}"
echo -e "Version: ${YELLOW}$VERSION${NC}"
echo -e "Target: ${YELLOW}$TARGET${NC}"
echo -e "Push: ${YELLOW}$PUSH${NC}"
echo ""

# Check prerequisites
check_buildx
setup_buildx

# Build command
BUILD_CMD="docker buildx build --target $TARGET --platform $PLATFORM --build-arg VERSION=$VERSION"

# Add --load flag for local builds
if [[ "$LOCAL_BUILD" == "true" ]]; then
    BUILD_CMD="$BUILD_CMD --load"
fi

# Add tags
BUILD_CMD="$BUILD_CMD --tag bank-importer-th:$VERSION --tag bank-importer-th:latest"

# Add Harbor registry tags if pushing
if [[ "$PUSH" == "true" ]]; then
    BUILD_CMD="$BUILD_CMD --tag reg.jochempiya.org/jochem/bank-importer-th:$VERSION"

    # Add appropriate tag based on version
    if [[ "$VERSION" == *"beta"* || "$VERSION" == *"alpha"* || "$VERSION" == *"rc"* ]]; then
        BUILD_CMD="$BUILD_CMD --tag reg.jochempiya.org/jochem/bank-importer-th:latest"
        echo -e "${BLUE}Adding 'latest' tag for pre-release version${NC}"
    else
        BUILD_CMD="$BUILD_CMD --tag reg.jochempiya.org/jochem/bank-importer-th:stable"
        echo -e "${BLUE}Adding 'stable' tag for release version${NC}"
    fi
fi

# Add push flag if pushing
if [[ "$PUSH" == "true" ]]; then
    BUILD_CMD="$BUILD_CMD --push"
fi

# Add context
BUILD_CMD="$BUILD_CMD ."

echo -e "${BLUE}Running build command:${NC}"
echo "$BUILD_CMD"
echo ""

# Execute build
eval $BUILD_CMD

if [[ $? -eq 0 ]]; then
    echo ""
    echo -e "${GREEN}✅ Build completed successfully!${NC}"

    if [[ "$PUSH" == "true" ]]; then
        echo -e "${GREEN}✅ Images pushed to registry:${NC}"
        echo "  - reg.jochempiya.org/jochem/bank-importer-th:$VERSION"
        echo "  - reg.jochempiya.org/jochem/bank-importer-th:latest"
    else
        echo -e "${GREEN}✅ Local images created:${NC}"
        echo "  - bank-importer-th:$VERSION"
        echo "  - bank-importer-th:latest"
    fi
else
    echo -e "${RED}❌ Build failed!${NC}"
    exit 1
fi
