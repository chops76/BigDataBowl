# Big Data Bowl Project

![CI](https://github.com/chops76/BigDataBowl/actions/workflows/ci.yml/badge.svg)

Repo for Alena, Andrew, and Dan's cool project

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
make install
```

## Getting the data

Data comes from the [NFL Big Data Bowl 2027](https://www.kaggle.com/competitions/nfl-big-data-bowl-2027/data)
Kaggle competition.

1. Join the competition and accept its rules on kaggle.com.
2. Create an API token at https://www.kaggle.com/settings/api, then follow the instructions to save it locally.
3. Run `make data`. It downloads into `data/raw/` and is a no-op if data is already there.

Tests marked `@pytest.mark.data` need the real data and are skipped automatically
when it isn't present.

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
