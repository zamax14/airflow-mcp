import httpx
import pytest
import respx

import mcp_airflow.server as server
from mcp_airflow.client import AirflowClient
from mcp_airflow.config import Settings

BASE_URL = "http://localhost:8080"


@pytest.fixture
def airflow_client(monkeypatch):
    settings = Settings(_env_file=None, base_url=BASE_URL, username="airflow", password="airflow")
    client = AirflowClient(settings)
    monkeypatch.setattr(server, "_client", client)
    monkeypatch.setattr(server, "_settings", settings)
    return client


@pytest.mark.anyio
async def test_trigger_dag_run(airflow_client):
    with respx.mock:
        respx.post(f"{BASE_URL}/api/v2/dags/d1/dagRuns").mock(
            return_value=httpx.Response(
                200,
                json={
                    "dag_run_id": "manual__1",
                    "state": "queued",
                    "logical_date": None,
                    "start_date": None,
                    "end_date": None,
                },
            )
        )
        result = await server.trigger_dag_run("d1", conf={"key": "value"})

    assert result["dag_run_id"] == "manual__1"
    assert result["state"] == "queued"


@pytest.mark.anyio
async def test_pause_dag(airflow_client):
    with respx.mock:
        route = respx.patch(f"{BASE_URL}/api/v2/dags/d1").mock(
            return_value=httpx.Response(
                200,
                json={"dag_id": "d1", "description": None, "tags": [], "is_paused": True},
            )
        )
        result = await server.pause_dag("d1")

    assert result["is_paused"] is True
    assert route.calls.last.request.url.params["update_mask"] == "is_paused"


@pytest.mark.anyio
async def test_unpause_dag(airflow_client):
    with respx.mock:
        respx.patch(f"{BASE_URL}/api/v2/dags/d1").mock(
            return_value=httpx.Response(
                200,
                json={"dag_id": "d1", "description": None, "tags": [], "is_paused": False},
            )
        )
        result = await server.unpause_dag("d1")

    assert result["is_paused"] is False


@pytest.mark.anyio
async def test_write_tools_are_annotated_as_sensitive():
    tools = {tool.name: tool for tool in await server.mcp.list_tools()}

    trigger = tools["trigger_dag_run"].annotations
    assert trigger is not None
    assert trigger.readOnlyHint is False
    assert trigger.destructiveHint is True

    for name in ("pause_dag", "unpause_dag"):
        annotations = tools[name].annotations
        assert annotations is not None
        assert annotations.readOnlyHint is False
        assert annotations.idempotentHint is True
