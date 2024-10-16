# HAPI Pipelines

[![Build Status](https://github.com/OCHA-DAP/hapi-pipelines/actions/workflows/run-python-tests.yaml/badge.svg)](https://github.com/OCHA-DAP/hapi-pipelines/actions/workflows/run-python-tests.yaml)
[![Coverage Status](https://coveralls.io/repos/github/OCHA-DAP/hapi-pipelines/badge.svg?branch=main&ts=1)](https://coveralls.io/github/OCHA-DAP/hapi-pipelines?branch=main)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

HAPI is a process that runs ...

For more information, please read the [documentation](https://hapi-pipelines.readthedocs.io/en/latest/).

This library is part of the [Humanitarian Data Exchange](https://data.humdata.org/) (HDX) project. If you have
humanitarian related data, please upload your datasets to HDX.

## Running

Ensure the `hapi` library is installed using `pip install .`.

Use the
[HAPI schema repository](https://github.com/OCHA-DAP/hapi-schemas)
to create an empty PostgreSQL HAPI database.
Then execute using:

```shell
python src/hapi/pipelines/app/__main__.py --db "postgresql+psycopg://postgres:postgres@localhost:5432/hapi"
```
