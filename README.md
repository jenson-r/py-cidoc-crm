# CIDOC CRM Toolkit

A modern, Pydantic v2-based toolkit for modeling [CIDOC CRM v7.1.3](https://cidoc-crm.org/html/cidoc_crm_v7.1.3.html) entities and relationships.

## Features

- **Typed models** built with Pydantic representing core CIDOC CRM entities and properties.
- **Graph storage** with an in-memory NetworkX backend and a repository abstraction for extensibility.
- **FastAPI JSON API** for CRUD access to entities and their relationships.
- **Typer-powered CLI** following the Linux philosophy of composable commands for importing, exporting, and inspecting data.
- **Automated tests** covering the repository layer and HTTP API.

## Getting Started

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[test]
```

### Run the API

```bash
uvicorn cidoc_crm_toolkit.api:app --reload
```

### Use the CLI

```bash
python -m cidoc_crm_toolkit.cli --help
```

## Tests

```bash
pytest
```
