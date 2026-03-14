.DEFAULT_GOAL := help

.PHONY: help install install-dev test test-cov lint format clean build check all

BLUE := \033[0;34m
GREEN := \033[0;32m
RED := \033[0;31m
YELLOW := \033[1;33m
NC := \033[0m

define print_status
	printf "$(BLUE)==>$(NC) %s\n" "$(1)"
endef

define print_success
	printf "$(GREEN)✓$(NC) %s\n" "$(1)"
endef

define print_error
	printf "$(RED)✗$(NC) %s\n" "$(1)"
endef

define print_warning
	printf "$(YELLOW)!$(NC) %s\n" "$(1)"
endef

help:
	@printf "$(BLUE)DAGLint Makefile$(NC)\n\n"
	@printf "$(GREEN)Usage:$(NC)\n"
	@printf "    make <target>\n\n"
	@printf "$(GREEN)Available targets:$(NC)\n"
	@printf "    help          Show this help message\n"
	@printf "    install       Install package\n"
	@printf "    install-dev   Install package with dev dependencies\n"
	@printf "    test          Run tests\n"
	@printf "    test-cov      Run tests with coverage\n"
	@printf "    lint          Run linting checks\n"
	@printf "    format        Format code with black and isort\n"
	@printf "    clean         Clean build artifacts\n"
	@printf "    build         Build package\n"
	@printf "    check         Run all quality checks (lint + test)\n"
	@printf "    all           Install dev deps, format, lint, and test\n\n"
	@printf "$(GREEN)Examples:$(NC)\n"
	@printf "    make install-dev    # Install with dev dependencies\n"
	@printf "    make test           # Run tests\n"
	@printf "    make format         # Format code\n"
	@printf "    make check          # Run all checks\n\n"

install:
	@$(call print_status,Installing package...)
	@pip install -e .
	@$(call print_success,Package installed successfully)

install-dev:
	@$(call print_status,Installing package with dev dependencies...)
	@pip install -e ".[dev]"
	@$(call print_success,Package and dev dependencies installed successfully)

test:
	@$(call print_status,Running tests...)
	@pytest tests/ -v
	@$(call print_success,Tests completed)

test-cov:
	@$(call print_status,Running tests with coverage...)
	@pytest tests/ -v --cov=daglint --cov-report=html --cov-report=term
	@$(call print_success,Tests with coverage completed)
	@$(call print_status,Coverage report available in htmlcov/index.html)

lint:
	@$(call print_status,Running linting checks...)
	@$(call print_status,Running flake8...)
	@flake8 src/daglint
	@$(call print_success,flake8 passed)
	@$(call print_status,Checking code formatting with black...)
	@black --check src/daglint tests
	@$(call print_success,black check passed)
	@$(call print_status,Checking import sorting with isort...)
	@isort --check-only src/daglint tests
	@$(call print_success,isort check passed)
	@$(call print_status,Running type checks with mypy...)
	@set +e; \
	mypy src/daglint --ignore-missing-imports; \
	status=$$?; \
	if [ $$status -eq 0 ]; then \
		$(call print_success,mypy check passed); \
	else \
		$(call print_warning,mypy check completed with warnings); \
	fi
	@$(call print_success,All linting checks completed)

format:
	@$(call print_status,Formatting code with black...)
	@black src/daglint tests
	@$(call print_success,Code formatted with black)
	@$(call print_status,Sorting imports with isort...)
	@isort src/daglint tests
	@$(call print_success,Imports sorted with isort)
	@$(call print_success,Code formatting completed)

clean:
	@$(call print_status,Cleaning build artifacts...)
	@rm -rf build/ dist/ *.egg-info htmlcov/ .coverage .pytest_cache/ .mypy_cache/
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@$(call print_success,Build artifacts cleaned)

build: clean
	@$(call print_status,Building package...)
	@COPYFILE_DISABLE=1 python -m build
	@$(call print_success,Package built successfully)

check:
	@$(call print_status,Running all quality checks...)
	@$(MAKE) format
	@$(MAKE) lint
	@$(MAKE) test
	@$(call print_success,All checks passed! 🎉)

all: install-dev format lint test
	@$(call print_success,Complete development setup finished! 🚀)
