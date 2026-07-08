# Manual end-to-end validation checklist

This checklist is not automated — it requires a real running Apache Airflow instance. Run it once before tagging a release, and whenever a tool's Airflow API mapping changes.

## Setup

- [ ] Airflow instance is reachable at `AIRFLOW_BASE_URL`
- [ ] `.env` is filled in with valid credentials for a `Viewer`/`Op` user
- [ ] Server runs in `stdio` mode and is registered in a local `.mcp.json`

## Checklist

- [ ] `list_dags` returns the expected DAGs and respects `limit`/`offset`/`tags`/`only_active`
- [ ] `get_dag` returns the correct `schedule`, `owners` and `tags` for a known DAG
- [ ] `trigger_dag_run` creates a new run on a low-risk DAG (e.g. `schedule=None`); the MCP client prompts for confirmation before executing
- [ ] `list_dag_runs` / `get_dag_run` show the newly triggered run
- [ ] `get_task_logs` truncates correctly when a task's log exceeds `AIRFLOW_LOG_MAX_LINES`
- [ ] `pause_dag` / `unpause_dag` toggle `is_paused` as seen via `get_dag`, and the MCP client flags them as non-read-only
- [ ] Invalid credentials produce a clean error, with no username/password/token in the error message or in stderr logs
