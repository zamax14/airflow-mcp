from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AIRFLOW_", env_file=".env")

    base_url: str
    auth_mode: Literal["basic", "bearer"] = "basic"
    username: str | None = None
    password: SecretStr | None = None
    token: SecretStr | None = None
    request_timeout: float = 10
    trigger_timeout: float = 30
    log_max_lines: int = 500
