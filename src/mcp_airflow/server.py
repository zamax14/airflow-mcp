import os
from typing import Any

from mcp.server.fastmcp import FastMCP

from mcp_airflow.client import AirflowClient, pagination_params
from mcp_airflow.config import Settings

mcp = FastMCP("airflow")

_client: AirflowClient | None = None


def get_client() -> AirflowClient:
    global _client
    if _client is None:
        _client = AirflowClient(Settings())
    return _client


def _tag_name(tag: Any) -> str:
    return tag["name"] if isinstance(tag, dict) else str(tag)


def _dag_summary(dag: dict[str, Any]) -> dict[str, Any]:
    return {
        "dag_id": dag["dag_id"],
        "description": dag.get("description"),
        "tags": [_tag_name(tag) for tag in dag.get("tags", [])],
        "is_paused": dag["is_paused"],
        "schedule": dag.get("timetable_summary") or dag.get("schedule_interval"),
    }


@mcp.tool()
async def list_dags(
    tags: list[str] | None = None,
    only_active: bool | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> list[dict[str, Any]]:
    """List Airflow DAGs, optionally filtered by tag or active state."""
    params: dict[str, Any] = pagination_params(limit, offset)
    if tags:
        params["tags"] = tags
    if only_active is not None:
        params["only_active"] = only_active

    response = await get_client().request("GET", "/dags", params=params)
    return [_dag_summary(dag) for dag in response.json()["dags"]]


@mcp.tool()
async def get_dag(dag_id: str) -> dict[str, Any]:
    """Get metadata for a single Airflow DAG."""
    response = await get_client().request("GET", f"/dags/{dag_id}")
    dag = response.json()
    return {
        **_dag_summary(dag),
        "owners": dag.get("owners", []),
        "next_dagrun": dag.get("next_dagrun_logical_date"),
    }


def _dag_run_summary(dag_run: dict[str, Any]) -> dict[str, Any]:
    return {
        "dag_run_id": dag_run["dag_run_id"],
        "state": dag_run["state"],
        "logical_date": dag_run.get("logical_date"),
        "start_date": dag_run.get("start_date"),
        "end_date": dag_run.get("end_date"),
    }


@mcp.tool()
async def list_dag_runs(
    dag_id: str,
    state: str | None = None,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """List DAG run history for a given DAG."""
    params: dict[str, Any] = pagination_params(limit)
    if state:
        params["state"] = state

    response = await get_client().request("GET", f"/dags/{dag_id}/dagRuns", params=params)
    return [_dag_run_summary(dag_run) for dag_run in response.json()["dag_runs"]]


@mcp.tool()
async def get_dag_run(dag_id: str, dag_run_id: str) -> dict[str, Any]:
    """Get details for a single DAG run, including its trigger conf."""
    response = await get_client().request("GET", f"/dags/{dag_id}/dagRuns/{dag_run_id}")
    dag_run = response.json()
    return {**_dag_run_summary(dag_run), "conf": dag_run.get("conf", {})}


def main() -> None:
    transport = os.environ.get("MCP_TRANSPORT", "stdio")
    if transport == "streamable-http":
        mcp.run(transport="streamable-http")
    else:
        mcp.run()


if __name__ == "__main__":
    main()
