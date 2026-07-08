import pytest
from pydantic import ValidationError

from mcp_airflow.config import Settings


def test_defaults(monkeypatch):
    monkeypatch.delenv("AIRFLOW_AUTH_MODE", raising=False)
    settings = Settings(_env_file=None, base_url="http://localhost:8080")

    assert settings.auth_mode == "basic"
    assert settings.request_timeout == 10
    assert settings.trigger_timeout == 30
    assert settings.log_max_lines == 500


def test_base_url_is_required():
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_invalid_auth_mode_raises_clearly():
    with pytest.raises(ValidationError, match="auth_mode"):
        Settings(_env_file=None, base_url="http://localhost:8080", auth_mode="oauth")
