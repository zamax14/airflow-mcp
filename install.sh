#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env from .env.example — edit it with your Airflow credentials before running."
fi

if command -v docker >/dev/null 2>&1; then
  echo "Docker found — building image..."
  docker build -t mcp-airflow .
  cat <<'JSON'

Add this to your .mcp.json:

{
  "mcpServers": {
    "airflow": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "--env-file", ".env", "mcp-airflow"]
    }
  }
}
JSON
elif command -v uv >/dev/null 2>&1; then
  echo "uv found — syncing dependencies..."
  uv sync --group dev
  cat <<'JSON'

Add this to your .mcp.json:

{
  "mcpServers": {
    "airflow": {
      "command": "uv",
      "args": ["run", "mcp-airflow"]
    }
  }
}
JSON
else
  echo "Neither docker nor uv found." >&2
  echo "Install one: https://docs.docker.com/get-docker/ or https://docs.astral.sh/uv/" >&2
  exit 1
fi
