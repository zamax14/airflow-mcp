import httpx

from mcp_airflow.auth import BearerTokenCache, basic_auth, fetch_bearer_token
from mcp_airflow.config import Settings

API_PREFIX = "/api/v2"


class AirflowClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._bearer_cache = BearerTokenCache()
        self._http = httpx.AsyncClient(
            base_url=settings.base_url,
            timeout=settings.request_timeout,
        )
        if settings.auth_mode == "basic":
            self._http.auth = basic_auth(settings)

    async def aclose(self) -> None:
        await self._http.aclose()

    async def _auth_headers(self) -> dict[str, str]:
        if self._settings.auth_mode == "bearer":
            token = await fetch_bearer_token(self._http, self._settings, self._bearer_cache)
            return {"Authorization": f"Bearer {token}"}
        return {}

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: dict | None = None,
        json: dict | None = None,
        timeout: float | None = None,
    ) -> httpx.Response:
        headers = await self._auth_headers()
        response = await self._http.request(
            method,
            f"{API_PREFIX}{path}",
            params=params,
            json=json,
            headers=headers,
            timeout=timeout or self._settings.request_timeout,
        )
        response.raise_for_status()
        return response
