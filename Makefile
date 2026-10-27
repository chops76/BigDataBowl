.PHONY: install lint format test clean

install:
	pip install -e ".[dev]"
	pre-commit install

lint:
	ruff check .
	ruff format --check .

format:
	ruff check --fix .
	ruff format .

test:
	pytest

clean:
	rm -rf .pytest_cache .ruff_cache .coverage coverage.xml htmlcov
