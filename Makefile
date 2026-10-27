.PHONY: install lint format test data test-data clean

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

data:
	pip install -e ".[data]"
	python -m databowl.download

test-data:
	pytest -m data

clean:
	rm -rf .pytest_cache .ruff_cache .coverage coverage.xml htmlcov
