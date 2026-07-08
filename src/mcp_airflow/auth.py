import httpx

from mcp_airflow.config import Settings


class AuthError(Exception):
    """Raised when Airflow authentication fails or is misconfigured."""


def basic_auth(settings: Settings) -> httpx.BasicAuth:
    if not settings.username or not settings.password:
        raise AuthError("basic auth requires AIRFLOW_USERNAME and AIRFLOW_PASSWORD")
    return httpx.BasicAuth(settings.username, settings.password.get_secret_value())


async def fetch_bearer_token(client: httpx.AsyncClient, settings: Settings) -> str:
    if settings.token:
        return settings.token.get_secret_value()

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

    return str(response.json()["access_token"])
