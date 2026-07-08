import time

import httpx

from mcp_airflow.config import Settings


class AuthError(Exception):
    """Raised when Airflow authentication fails or is misconfigured."""


class BearerTokenCache:
    """Caches a bearer token for a fixed TTL.

    # ponytail: no JWT expiry parsing, a fixed TTL is enough here;
    # callers should force a refresh after a 401 from Airflow.
    """

    def __init__(self, ttl_seconds: float = 300) -> None:
        self._ttl = ttl_seconds
        self._token: str | None = None
        self._fetched_at: float = 0.0

    def get(self) -> str | None:
        if self._token and (time.monotonic() - self._fetched_at) < self._ttl:
            return self._token
        return None

    def set(self, token: str) -> None:
        self._token = token
        self._fetched_at = time.monotonic()


def basic_auth(settings: Settings) -> httpx.BasicAuth:
    if not settings.username or not settings.password:
        raise AuthError("basic auth requires AIRFLOW_USERNAME and AIRFLOW_PASSWORD")
    return httpx.BasicAuth(settings.username, settings.password.get_secret_value())


async def fetch_bearer_token(
    client: httpx.AsyncClient, settings: Settings, cache: BearerTokenCache
) -> str:
    if settings.token:
        return settings.token.get_secret_value()

    cached = cache.get()
    if cached:
        return cached

    if not settings.username or not settings.password:
        raise AuthError("bearer auth requires AIRFLOW_TOKEN or AIRFLOW_USERNAME/AIRFLOW_PASSWORD")

    try:
        response = await client.post(
            "/auth/token",
            json={
                "username": settings.username,
                "password": settings.password.get_secret_value(),
            },
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise AuthError(f"failed to fetch bearer token: HTTP {exc.response.status_code}") from None

    token = str(response.json()["access_token"])
    cache.set(token)
    return token
