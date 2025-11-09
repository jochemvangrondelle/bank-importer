#!/bin/bash

# Smart Docker entrypoint for bank-importer
# Handles both script name and direct command execution

set -e

# Function to display help
show_help() {
    echo "Bank Importer Thailand - Docker Container"
    echo ""
    echo "Usage:"
    echo "  docker run <image> [command] [args...]"
    echo ""
    echo "Examples:"
    echo "  docker run <image> --help                    # Show help"
    echo "  docker run <image> import-files data/in/     # Import files"
    echo "  docker run <image> export --target csv       # Export to CSV"
    echo "  docker run <image> status                    # Show status"
    echo "  docker run <image> version                   # Show version"
    echo ""
    echo "Environment Variables:"
    echo "  APP_VERSION    - Application version (auto-detected)"
    echo ""
    echo "Volumes:"
    echo "  /app/data/in   - Input directory (bank statements)"
    echo "  /app/data/out  - Output directory (exports)"
    echo "  /app/logs      - Logs directory"
    echo ""
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to run the application
run_app() {
    local cmd="$1"
    shift

    # If no arguments provided, show help
    if [ $# -eq 0 ]; then
        show_help
        exit 0
    fi

    # Check if the command is a direct bank-importer command
    if command_exists "bank-importer"; then
        exec bank-importer "$@"
    else
        echo "Error: bank-importer command not found"
        exit 1
    fi
}

# Main logic
main() {
    # If no arguments provided, show help
    if [ $# -eq 0 ]; then
        show_help
        exit 0
    fi

    # Handle special cases
    case "$1" in
        --help|-h|help)
            show_help
            exit 0
            ;;
        --version|-v|version)
            if command_exists "bank-importer"; then
                bank-importer --version
            else
                echo "Version: ${APP_VERSION:-unknown}"
            fi
            exit 0
            ;;
        *)
            # Run the application with all arguments
            run_app "$@"
            ;;
    esac
}

# Run main function with all arguments
main "$@"
