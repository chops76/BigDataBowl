# Big Data Bowl Project

![CI](https://github.com/chops76/BigDataBowl/actions/workflows/ci.yml/badge.svg)

Repo for Alena, Andrew, and Dan's cool project

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
make install
```

## Common commands

| Command       | What it does                      |
|---------------|-----------------------------------|
| `make test`   | Run tests with coverage           |
| `make lint`   | Check linting and formatting      |
| `make format` | Auto-fix lint issues and format   |

## Layout

```
src/databowl/     code (data loading, features, models)
tests/            pytest tests
data/raw/         original data (not tracked)
data/processed/   derived data (not tracked)
reports/          figures and write-ups
```
