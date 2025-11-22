#!/usr/bin/env bash

# DAGLint Development Script
# Provides convenient commands for development tasks

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}==>${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}!${NC} $1"
}

# Help command
show_help() {
    cat << EOF
${BLUE}DAGLint Development Script${NC}

${GREEN}Usage:${NC}
    ./dev.sh [command]

${GREEN}Available commands:${NC}
    help          Show this help message
    install       Install package
    install-dev   Install package with dev dependencies
    test          Run tests
    test-cov      Run tests with coverage
    lint          Run linting checks
    format        Format code with black and isort
    clean         Clean build artifacts
    build         Build package
    check         Run all quality checks (lint + test)
    all           Install dev deps, format, lint, and test

${GREEN}Examples:${NC}
    ./dev.sh install-dev    # Install with dev dependencies
    ./dev.sh test           # Run tests
    ./dev.sh format         # Format code
    ./dev.sh check          # Run all checks

EOF
}

# Install command
cmd_install() {
    print_status "Installing package..."
    pip install -e .
    print_success "Package installed successfully"
}

# Install dev dependencies
cmd_install_dev() {
    print_status "Installing package with dev dependencies..."
    pip install -e ".[dev]"
    print_success "Package and dev dependencies installed successfully"
}

# Run tests
cmd_test() {
    print_status "Running tests..."
    pytest tests/ -v
    print_success "Tests completed"
}

# Run tests with coverage
cmd_test_cov() {
    print_status "Running tests with coverage..."
    pytest tests/ -v --cov=daglint --cov-report=html --cov-report=term
    print_success "Tests with coverage completed"
    print_status "Coverage report available in htmlcov/index.html"
}

# Run linting checks
cmd_lint() {
    print_status "Running linting checks..."

    print_status "Running flake8..."
    if flake8 src/daglint; then
        print_success "flake8 passed"
    else
        print_error "flake8 failed"
        return 1
    fi

    print_status "Checking code formatting with black..."
    if black --check src/daglint tests; then
        print_success "black check passed"
    else
        print_error "black check failed - run './dev.sh format' to fix"
        return 1
    fi

    print_status "Checking import sorting with isort..."
    if isort --check-only src/daglint tests; then
        print_success "isort check passed"
    else
        print_error "isort check failed - run './dev.sh format' to fix"
        return 1
    fi

    print_status "Running type checks with mypy..."
    if mypy src/daglint --ignore-missing-imports; then
        print_success "mypy check passed"
    else
        print_warning "mypy check completed with warnings"
    fi

    print_success "All linting checks completed"
}

# Format code
cmd_format() {
    print_status "Formatting code with black..."
    black src/daglint tests
    print_success "Code formatted with black"

    print_status "Sorting imports with isort..."
    isort src/daglint tests
    print_success "Imports sorted with isort"

    print_success "Code formatting completed"
}

# Clean build artifacts
cmd_clean() {
    print_status "Cleaning build artifacts..."

    rm -rf build/
    rm -rf dist/
    rm -rf *.egg-info
    rm -rf htmlcov/
    rm -rf .coverage
    rm -rf .pytest_cache/
    rm -rf .mypy_cache/
    find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true

    print_success "Build artifacts cleaned"
}

# Build package
cmd_build() {
    print_status "Cleaning previous builds..."
    cmd_clean

    print_status "Building package..."
    # Disable macOS metadata files during build
    export COPYFILE_DISABLE=1
    python -m build
    print_success "Package built successfully"
}

# Run all checks
cmd_check() {
    print_status "Running all quality checks..."

    if cmd_lint && cmd_test; then
        print_success "All checks passed! 🎉"
        return 0
    else
        print_error "Some checks failed"
        return 1
    fi
}

# Run everything (install, format, lint, test)
cmd_all() {
    print_status "Running complete development setup..."

    cmd_install_dev
    cmd_format
    cmd_lint
    cmd_test

    print_success "Complete development setup finished! 🚀"
}

# Main script logic
main() {
    # Check if no arguments provided
    if [ $# -eq 0 ]; then
        show_help
        exit 0
    fi

    # Parse command
    case "$1" in
        help|--help|-h)
            show_help
            ;;
        install)
            cmd_install
            ;;
        install-dev)
            cmd_install_dev
            ;;
        test)
            cmd_test
            ;;
        test-cov)
            cmd_test_cov
            ;;
        lint)
            cmd_lint
            ;;
        format)
            cmd_format
            ;;
        clean)
            cmd_clean
            ;;
        build)
            cmd_build
            ;;
        check)
            cmd_check
            ;;
        all)
            cmd_all
            ;;
        *)
            print_error "Unknown command: $1"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# Run main function
main "$@"

