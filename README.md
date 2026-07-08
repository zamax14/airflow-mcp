# Airflow MCP

A [Model Context Protocol](https://modelcontextprotocol.io/) server that exposes Apache Airflow's REST API to AI agents (Claude Code, Claude Desktop, etc.), so they can inspect and operate on DAGs, DAG runs, task instances and logs.

The server is general-purpose: point it at any Airflow 2.x/3.x instance via `AIRFLOW_BASE_URL`. It has no knowledge of any specific project's DAGs, and does not edit DAG files or manage Airflow users/roles/pools/connections.

## Status

Early scaffolding — tools are not implemented yet. See the project board / issues for progress.

## Requirements

- Python >= 3.12
- [uv](https://docs.astral.sh/uv/)
- An Apache Airflow instance reachable over HTTP, with a user that has at least `Viewer` role (`Op` if you need the write tools)

## Setup

```bash
uv sync --group dev
cp .env.example .env
```

Fill in `.env` with your Airflow instance's URL and credentials.

## Development

```bash
uv run pytest
uv run ruff check .
uv run mypy src
```
