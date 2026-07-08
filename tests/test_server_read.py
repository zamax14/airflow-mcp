import httpx
import pytest
import respx

import mcp_airflow.server as server
from mcp_airflow.client import AirflowClient
from mcp_airflow.config import Settings

BASE_URL = "http://localhost:8080"


@pytest.fixture
def airflow_client(monkeypatch):
    settings = Settings(
        _env_file=None,
        base_url=BASE_URL,
        username="airflow",
        password="airflow",
        log_max_lines=3,
    )
    client = AirflowClient(settings)
    monkeypatch.setattr(server, "_client", client)
    monkeypatch.setattr(server, "_settings", settings)
    return client


@pytest.mark.anyio
async def test_list_dags(airflow_client):
    with respx.mock:
        respx.get(f"{BASE_URL}/api/v2/dags").mock(
            return_value=httpx.Response(
                200,
                json={
                    "dags": [
                        {
                            "dag_id": "d1",
                            "description": "desc",
                            "tags": [{"name": "t1"}],
                            "is_paused": False,
                            "timetable_summary": "@daily",
                        }
                    ]
                },
            )
        )
        result = await server.list_dags()

    assert result == [
        {
            "dag_id": "d1",
            "description": "desc",
            "tags": ["t1"],
            "is_paused": False,
            "schedule": "@daily",
        }
    ]


@pytest.mark.anyio
async def test_get_dag(airflow_client):
    with respx.mock:
        respx.get(f"{BASE_URL}/api/v2/dags/d1").mock(
            return_value=httpx.Response(
                200,
                json={
                    "dag_id": "d1",
                    "description": None,
                    "tags": [],
                    "is_paused": True,
                    "timetable_summary": None,
                    "owners": ["airflow"],
                    "next_dagrun_logical_date": "2026-01-01T00:00:00+00:00",
                },
            )
        )
        result = await server.get_dag("d1")

    assert result["owners"] == ["airflow"]
    assert result["next_dagrun"] == "2026-01-01T00:00:00+00:00"
    assert result["is_paused"] is True


@pytest.mark.anyio
async def test_list_dag_runs(airflow_client):
    with respx.mock:
        respx.get(f"{BASE_URL}/api/v2/dags/d1/dagRuns").mock(
            return_value=httpx.Response(
                200,
                json={
                    "dag_runs": [
                        {
                            "dag_run_id": "run1",
                            "state": "success",
                            "logical_date": "2026-01-01T00:00:00+00:00",
                            "start_date": "2026-01-01T00:00:00+00:00",
                            "end_date": "2026-01-01T00:05:00+00:00",
                        }
                    ]
                },
            )
        )
        result = await server.list_dag_runs("d1")

    assert result[0]["dag_run_id"] == "run1"
    assert result[0]["state"] == "success"


@pytest.mark.anyio
async def test_get_dag_run(airflow_client):
    with respx.mock:
        respx.get(f"{BASE_URL}/api/v2/dags/d1/dagRuns/run1").mock(
            return_value=httpx.Response(
                200,
                json={
                    "dag_run_id": "run1",
                    "state": "running",
                    "logical_date": None,
                    "start_date": "2026-01-01T00:00:00+00:00",
                    "end_date": None,
                    "conf": {"key": "value"},
                },
            )
        )
        result = await server.get_dag_run("d1", "run1")

    assert result["conf"] == {"key": "value"}


@pytest.mark.anyio
async def test_list_task_instances(airflow_client):
    with respx.mock:
        respx.get(f"{BASE_URL}/api/v2/dags/d1/dagRuns/run1/taskInstances").mock(
            return_value=httpx.Response(
                200,
                json={
                    "task_instances": [
                        {"task_id": "t1", "state": "success", "duration": 1.5, "try_number": 1}
                    ]
                },
            )
        )
        result = await server.list_task_instances("d1", "run1")

    assert result == [{"task_id": "t1", "state": "success", "duration": 1.5, "try_number": 1}]


@pytest.mark.anyio
async def test_get_task_logs_returns_full_content_when_under_limit(airflow_client):
    with respx.mock:
        respx.get(f"{BASE_URL}/api/v2/dags/d1/dagRuns/run1/taskInstances/t1/logs/1").mock(
            return_value=httpx.Response(200, json={"content": "line1\nline2"})
        )
        result = await server.get_task_logs("d1", "run1", "t1")

    assert result == "line1\nline2"


@pytest.mark.anyio
async def test_get_task_logs_truncates_past_max_lines(airflow_client):
    content = "\n".join(f"line{i}" for i in range(10))
    with respx.mock:
        respx.get(f"{BASE_URL}/api/v2/dags/d1/dagRuns/run1/taskInstances/t1/logs/1").mock(
            return_value=httpx.Response(200, json={"content": content})
        )
        result = await server.get_task_logs("d1", "run1", "t1")

    assert result == "line0\nline1\nline2\n... (7 more lines truncated)"
