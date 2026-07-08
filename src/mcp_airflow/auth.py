import httpx

from mcp_airflow.config import Settings


class AuthError(Exception):
    """Raised when Airflow authentication fails or is misconfigured."""


def basic_auth(settings: Settings) -> httpx.BasicAuth:
    if not settings.username or not settings.password:
        raise AuthError("basic auth requires AIRFLOW_USERNAME and AIRFLOW_PASSWORD")
    return httpx.BasicAuth(settings.username, settings.password.get_secret_value())
