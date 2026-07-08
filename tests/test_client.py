import httpx
import pytest
import respx

from mcp_airflow.client import AirflowClient, pagination_params
from mcp_airflow.config import Settings


def _settings(**overrides) -> Settings:
    defaults = {
        "base_url": "http://localhost:8080",
        "username": "airflow",
        "password": "airflow",
    }
    defaults.update(overrides)
    return Settings(_env_file=None, **defaults)


@pytest.mark.anyio
async def test_request_sends_basic_auth_and_returns_json():
    with respx.mock:
        respx.get("http://localhost:8080/api/v2/dags").mock(
            return_value=httpx.Response(200, json={"dags": []})
        )
        client = AirflowClient(_settings())
        response = await client.request("GET", "/dags")
        await client.aclose()

    assert response.json() == {"dags": []}


@pytest.mark.anyio
async def test_request_sends_bearer_token_header():
    with respx.mock:
        respx.post("http://localhost:8080/auth/token").mock(
            return_value=httpx.Response(200, json={"access_token": "abc123"})
        )
        dags_route = respx.get("http://localhost:8080/api/v2/dags").mock(
            return_value=httpx.Response(200, json={"dags": []})
        )
        client = AirflowClient(_settings(auth_mode="bearer"))
        await client.request("GET", "/dags")
        await client.aclose()

    assert dags_route.calls.last.request.headers["authorization"] == "Bearer abc123"


@pytest.mark.anyio
async def test_request_retries_on_5xx_then_succeeds():
    with respx.mock:
        route = respx.get("http://localhost:8080/api/v2/dags").mock(
            side_effect=[
                httpx.Response(503),
                httpx.Response(200, json={"dags": []}),
            ]
        )
        client = AirflowClient(_settings(), backoff_seconds=0)
        response = await client.request("GET", "/dags")
        await client.aclose()

    assert response.status_code == 200
    assert route.call_count == 2


@pytest.mark.anyio
async def test_request_does_not_retry_on_4xx():
    with respx.mock:
        route = respx.get("http://localhost:8080/api/v2/dags/missing").mock(
            return_value=httpx.Response(404, json={"detail": "not found"})
        )
        client = AirflowClient(_settings(), backoff_seconds=0)
        with pytest.raises(httpx.HTTPStatusError):
            await client.request("GET", "/dags/missing")
        await client.aclose()

    assert route.call_count == 1


def test_pagination_params_omits_unset_values():
    assert pagination_params() == {}
    assert pagination_params(limit=10) == {"limit": 10}
    assert pagination_params(limit=10, offset=20) == {"limit": 10, "offset": 20}
