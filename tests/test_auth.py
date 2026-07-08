import httpx
import pytest
import respx

from mcp_airflow.auth import AuthError, BearerTokenCache, basic_auth, fetch_bearer_token
from mcp_airflow.config import Settings

PASSWORD = "super-secret-password"


def _settings(**overrides) -> Settings:
    defaults = {
        "base_url": "http://localhost:8080",
        "username": "airflow",
        "password": PASSWORD,
    }
    defaults.update(overrides)
    return Settings(_env_file=None, **defaults)


def test_basic_auth_builds_header():
    auth = basic_auth(_settings())

    assert isinstance(auth, httpx.BasicAuth)


def test_basic_auth_requires_credentials():
    with pytest.raises(AuthError):
        basic_auth(_settings(username=None, password=None))


@pytest.mark.anyio
async def test_fetch_bearer_token_uses_static_token():
    settings = _settings(auth_mode="bearer", token="static-token")

    async with httpx.AsyncClient(base_url=settings.base_url) as client:
        token = await fetch_bearer_token(client, settings, BearerTokenCache())

    assert token == "static-token"


@pytest.mark.anyio
async def test_fetch_bearer_token_fetches_and_caches():
    settings = _settings(auth_mode="bearer")
    cache = BearerTokenCache()

    async with httpx.AsyncClient(base_url=settings.base_url) as client:
        with respx.mock:
            route = respx.post("http://localhost:8080/auth/token").mock(
                return_value=httpx.Response(200, json={"access_token": "fetched-token"})
            )
            first = await fetch_bearer_token(client, settings, cache)
            second = await fetch_bearer_token(client, settings, cache)

    assert first == "fetched-token"
    assert second == "fetched-token"
    assert route.call_count == 1


@pytest.mark.anyio
async def test_bearer_token_error_never_leaks_password():
    settings = _settings(auth_mode="bearer")

    async with httpx.AsyncClient(base_url=settings.base_url) as client:
        with respx.mock:
            respx.post("http://localhost:8080/auth/token").mock(
                return_value=httpx.Response(401, json={"detail": "invalid credentials"})
            )
            with pytest.raises(AuthError) as exc_info:
                await fetch_bearer_token(client, settings, BearerTokenCache())

    assert PASSWORD not in str(exc_info.value)
