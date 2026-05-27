# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**hdx-hapi-datasets** reads the database dump from [HAPI](https://hapi.humdata.org/) and creates country and subcategory datasets on HDX.

## Commands

Install dependencies:
```bash
uv sync
```

Run the pipeline:
```bash
uv run python -m hdx.scraper.hapi
```

Run tests:
```bash
uv run pytest
```

Run a single test:
```bash
uv run pytest tests/test_main.py
```

Lint check:
```bash
pre-commit run --all-files
```

## Architecture

The pipeline flows through these stages in `__main__.py`:

1. **`SubcategoryReader.read_countries`** — Queries the database for all countries with data and returns a list of ISO3 codes.

2. **`SubcategoryReader.get_subcategory`** — For each subcategory (population, funding, etc.), queries the database and populates datasets.

3. **`Datasets.get_country_dataset`** / **`Datasets.get_subcategory_dataset`** — Constructs HDX `Dataset` objects for a given country or subcategory.

### Key design points

- **One dataset per country + one per subcategory**: the pipeline iterates over countries and subcategories to create/update HDX datasets.
- **PostgreSQL restore**: the pipeline downloads a pg_restore file and loads it into a local Postgres database before querying.
- **`Read`** (`hdx-python-scraper`) handles HTTP downloads with save/replay support via `save=True`/`use_saved=True` — used in tests with fixture data.
- **Static config inside the package**: `config/` lives under `src/hdx/scraper/hapi/config/` and is located via `script_dir_plus_file`.

### Config files

- `src/hdx/scraper/hapi/config/project_configuration.yaml` — database URI default, subcategory definitions, dataset description template
- `src/hdx/scraper/hapi/config/hdx_dataset_static.yaml` — Static HDX metadata (license, methodology, source, etc.)

## Environment

Requires `~/.hdx_configuration.yaml` with HDX credentials, or env vars: `HDX_KEY`, `HDX_SITE`, `USER_AGENT`, `TEMP_DIR`, `LOG_FILE_ONLY`.

Requires `~/.useragents.yaml` with an `hdx-hapi-datasets` entry.

Requires a running PostgreSQL instance at `postgresql+psycopg://postgres:postgres@localhost:5432/hapirestore` (or override via `--db-uri`).

## Collaboration Style

- Be objective, not agreeable. Act as a partner, not a sycophant. Push back when you disagree, flag tradeoffs honestly, and don't sugarcoat problems.
- Keep explanations brief and to the point.
- Don't rely on recalled knowledge for facts that could be stale (API behaviour, library versions, external systems). Search or read the actual source first.

## Scope of Changes

When fixing a bug or addressing PR feedback, change only what is necessary to resolve the specific issue. Do not refactor surrounding code, rename variables, adjust formatting, or make improvements in the same commit unless they are directly required by the fix.
