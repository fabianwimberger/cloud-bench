.PHONY: all lint test format

all: lint test

lint:
	@echo "Running linters..."
	@ruff check scripts/ tests/
	@ruff format --check scripts/ tests/

format:
	@echo "Formatting code..."
	@ruff format scripts/ tests/

test:
	@echo "Running tests..."
	@pytest tests/ -v
