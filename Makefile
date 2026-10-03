.PHONY: all lint test format

PYTHON ?= .venv/bin/python

all: lint test

lint:
	@echo "Running linters..."
	@$(PYTHON) -m ruff check scripts/ tests/
	@$(PYTHON) -m ruff format --check scripts/ tests/

format:
	@echo "Formatting code..."
	@$(PYTHON) -m ruff format scripts/ tests/

test:
	@echo "Running tests..."
	@$(PYTHON) -m pytest tests/ -v --cov=scripts --cov-report=term-missing
