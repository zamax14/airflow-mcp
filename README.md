# Airflow MCP

A [Model Context Protocol](https://modelcontextprotocol.io/) server that exposes Apache Airflow's REST API to AI agents (Claude Code, Claude Desktop, etc.), so they can inspect and operate on DAGs, DAG runs, task instances and logs.

The server is general-purpose: point it at any Airflow 2.x/3.x instance via `AIRFLOW_BASE_URL`. It has no knowledge of any specific project's DAGs, and does not edit DAG files or manage Airflow users/roles/pools/connections.

## Tools

### Read-only

| Tool | Description | Parameters |
|---|---|---|
| `list_dags` | List DAGs, optionally filtered by tag or active state | `tags?`, `only_active?`, `limit?`, `offset?` |
| `get_dag` | Get metadata for a single DAG | `dag_id` |
| `list_dag_runs` | List DAG run history | `dag_id`, `state?`, `limit?` |
| `get_dag_run` | Get details for a single DAG run, including trigger conf | `dag_id`, `dag_run_id` |
| `list_task_instances` | List task instances and their state for a DAG run | `dag_id`, `dag_run_id` |
| `get_task_logs` | Get logs for a task instance, truncated to `AIRFLOW_LOG_MAX_LINES` | `dag_id`, `dag_run_id`, `task_id`, `try_number?` |

### Write (sensitive — annotated so MCP clients require confirmation)

| Tool | Description | Parameters |
|---|---|---|
| `trigger_dag_run` | Trigger a new DAG run (destructive, non-idempotent) | `dag_id`, `conf?`, `logical_date?` |
| `pause_dag` | Pause a DAG (idempotent) | `dag_id` |
| `unpause_dag` | Resume a paused DAG (idempotent) | `dag_id` |

## Requirements

- Python >= 3.12
- [uv](https://docs.astral.sh/uv/)
- An Apache Airflow instance reachable over HTTP, with a user that has at least `Viewer` role (`Op` if you need the write tools)

### Least privilege

Use a dedicated Airflow user for this server, scoped to the minimum role it needs:

- `Viewer` is enough if you only register the read-only tools.
- `Op` is required if you also register `trigger_dag_run`, `pause_dag` or `unpause_dag`.
- Never point this server at an `Admin` account unless you have a specific reason to.

## Quickstart

```bash
./install.sh
```

Detects whether you have Docker or uv installed, sets up `.env` (from `.env.example`, if missing), builds the image or syncs dependencies accordingly, and prints the `.mcp.json` snippet to register the server.

## Setup

```bash
uv sync --group dev
cp .env.example .env
```

Fill in `.env` with your Airflow instance's URL and credentials.

## Docker

No local Python/uv needed — build once, run anywhere Docker runs:

```bash
docker build -t mcp-airflow .
cp .env.example .env  # fill in your Airflow credentials
```

Run in stdio mode (default, for MCP clients that spawn the process):

```bash
docker run -i --rm --env-file .env mcp-airflow
```

Run in streamable-http mode (standalone service, listens on `:8000`):

```bash
docker run --rm -p 8000:8000 --env-file .env -e MCP_TRANSPORT=streamable-http mcp-airflow
```

## Registering with an MCP client

### stdio (recommended for local development)

```json
{
  "mcpServers": {
    "airflow": {
      "command": "uv",
      "args": ["run", "mcp-airflow"],
      "env": {
        "AIRFLOW_BASE_URL": "http://localhost:8080",
        "AIRFLOW_AUTH_MODE": "basic",
        "AIRFLOW_USERNAME": "airflow",
        "AIRFLOW_PASSWORD": "airflow"
      }
    }
  }
}
```

### stdio via Docker

```json
{
  "mcpServers": {
    "airflow": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "--env-file", ".env", "mcp-airflow"]
    }
  }
}
```

### streamable-http (server running as a standalone process)

Start the server with `MCP_TRANSPORT=streamable-http uv run mcp-airflow` (or the Docker command above), then register:

```json
{
  "mcpServers": {
    "airflow": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

## Development

```bash
uv run pytest
uv run ruff check .
uv run mypy src
```
