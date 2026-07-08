import os

from mcp.server.fastmcp import FastMCP

from mcp_airflow.client import AirflowClient
from mcp_airflow.config import Settings

mcp = FastMCP("airflow")

_client: AirflowClient | None = None


def get_client() -> AirflowClient:
    global _client
    if _client is None:
        _client = AirflowClient(Settings())
    return _client


def main() -> None:
    transport = os.environ.get("MCP_TRANSPORT", "stdio")
    if transport == "streamable-http":
        mcp.run(transport="streamable-http")
    else:
        mcp.run()


if __name__ == "__main__":
    main()
