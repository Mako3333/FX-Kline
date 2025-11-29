# Repository Guidelines

## Project Structure & Module Organization
- Root entry points only: `main.py`, `ohlc_aggregator.py`, `consolidate_summaries.py`, `run_mcp_server.py`.
- All other scripts go under `scripts/` (debug → `scripts/debug/`; utilities → `scripts/`).
- Source lives in `src/fx_kline/`:
  - Core logic in `src/fx_kline/core/` (fetchers, validators, business-day helpers, pydantic models).
  - UI in `src/fx_kline/ui/` (Streamlit app, widgets, presentation helpers).
- Tests in `tests/` and integration tests in `tests/integration/`.
- Keep wrappers thin: root files import from `src/fx_kline` and call `main()`.

## Build, Test, and Development Commands
- Install/sync deps: `uv sync`
- Run Streamlit UI: `uv run streamlit run src/fx_kline/ui/streamlit_app.py` or `python main.py`
- L2 pipeline (CI/CLI): `python ohlc_aggregator.py`
- Consolidate summaries (CI/CLI): `python consolidate_summaries.py`
- Quick fetch validation: `uv run python test_fetch.py`
- Lint: `uv run ruff check --fix .`
- Format: `uv run black .`
- Test suite: `uv run pytest`

## Coding Style & Naming Conventions
- Python 3.10+, 4-space indentation, type hints everywhere.
- Filenames and symbols use `snake_case` (e.g., `data_fetcher.py`, `timezone_utils.py`).
- Use pydantic models for data contracts.
- Keep UI caching with `st.cache_data` for expensive I/O.
- New assets/fixtures belong outside `src/` (use a `data/` directory if needed).

## Testing Guidelines
- Use `pytest`; mirror feature names: `tests/test_timezone_utils.py`.
- Place live/external-service tests in `tests/integration/`; mark network-dependent tests and provide offline guards/fixtures.
- Run all tests with `uv run pytest` before submitting.

## Commit & Pull Request Guidelines
- Commits: imperative, scope-prefixed (e.g., `core: add batch retry logic`). Group related changes.
- Pull Requests: explain the problem and solution, list verification steps (commands run, screenshots for Streamlit as relevant), link issues, and note follow-ups/risks.

## Streamlit & MCP Notes
- Implement workflows in `core/`, cover with tests, then thread into UI to keep the agent-facing API stable.
- Keep MCP helpers UI-agnostic.
