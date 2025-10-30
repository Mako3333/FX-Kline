# Repository Guidelines

## Project Structure & Module Organization
Core trading logic lives in `src/fx_kline/core/`, split into fetchers, validators, business-day helpers, and pydantic models. Streamlit UI elements, reusable widgets, and presentation helpers sit under `src/fx_kline/ui/`. `main.py` boots the app for local demos, while `debug_fetch.py` and `test_fetch.py` offer quick data checks without the UI. Keep new assets or reference datasets out of `src/`; store large fixtures under a dedicated `data/` subdirectory if one becomes necessary.

## Build, Test, and Development Commands
Install and sync dependencies with `uv sync`. Launch the Streamlit interface via `uv run streamlit run src/fx_kline/ui/streamlit_app.py` or run the Python wrapper `python main.py`. For quick fetch validation in a terminal-only session, call `uv run python test_fetch.py`. When adding libraries, update `pyproject.toml` and regenerate `uv.lock` with `uv lock`.

## Coding Style & Naming Conventions
Target Python 3.10+ and four-space indentation. Favor descriptive module names that match the existing pattern (`data_fetcher.py`, `timezone_utils.py`) and snake_case for functions, variables, and filenames. Use type hints and pydantic models for data contracts. Run `uv run ruff check --fix .` for linting and `uv run black .` for formatting before asking for review.

## Testing Guidelines
Author pytest-based suites under `tests/` (create the folder if it does not exist) and mirror feature names in test module titles, e.g., `tests/test_timezone_utils.py`. Use `uv run pytest` for the full suite, and rely on `uv run python test_fetch.py` only for manual smoke checks that hit live market data. When tests require network calls, mark them and provide offline guards or fixtures so CI can skip flaky scenarios.

## Commit & Pull Request Guidelines
The history is currently empty; seed it with imperative, scope-prefixed messages such as `core: add batch retry logic` to clarify intent. Group related changes into a single commit and mention relevant modules in the body. Pull requests should explain the problem, outline the solution, and include verification steps (commands run, screenshots of the Streamlit UI when applicable). Link to open issues and flag any follow-up tasks so reviewers understand remaining risks.

## Streamlit & MCP Notes
Cache expensive I/O inside Streamlit callbacks using `st.cache_data` where possible, and guard MCP-facing helpers so they remain UI-agnostic. When exposing new data fetch workflows, implement them in `core/` first, cover them with pytest, then thread them into the UI layer to keep the agent-facing API stable.
