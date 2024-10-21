# HDX HAPI Datasets Pipeline

[![Build Status](https://github.com/OCHA-DAP/hdx-hapi-datasets/actions/workflows/run-python-tests.yaml/badge.svg)](https://github.com/OCHA-DAP/hdx-hapi-datasets/actions/workflows/run-python-tests.yaml)
[![Coverage Status](https://coveralls.io/repos/github/OCHA-DAP/hdx-hapi-datasets/badge.svg?branch=main&ts=1)](https://coveralls.io/github/OCHA-DAP/hdx-hapi-datasets?branch=main)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

This pipeline reads the database dump from HAPI and creates country datasets
on HDX.

This library is part of the [Humanitarian Data Exchange](https://data.humdata.org/) (HDX) project. 
If you have humanitarian related data, please upload your datasets to HDX.

## Running

Create a Postgres database at "postgresql+psycopg://postgres:postgres@localhost:5432/hapirestore"

Execute using:

```shell
python -m python -m hdx.scraper.hapi
```
