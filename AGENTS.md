# Repository Guidelines

## Project Structure & Module Organization

### Root Directory Rules

**Root-level `.py` files are limited to external entry points only:**

- `main.py`: Development entry point for Streamlit UI
- `ohlc_aggregator.py`: CLI wrapper for L2 pipeline (called from GitHub Actions)
- `consolidate_summaries.py`: CLI wrapper for summary consolidation (called from GitHub Actions)
- `run_mcp_server.py`: MCP server startup entry point

**All other scripts must be placed under `scripts/`:**

- Development/debug scripts → `scripts/debug/`
- Utility scripts → `scripts/`
- Test scripts → `tests/` or `tests/integration/`

This rule ensures the root directory remains clean and maintainable.

### Module Organization

Core trading logic lives in `src/fx_kline/core/`, split into fetchers, validators, business-day helpers, and pydantic models. Streamlit UI elements, reusable widgets, and presentation helpers sit under `src/fx_kline/ui/`. Keep new assets or reference datasets out of `src/`; store large fixtures under a dedicated `data/` subdirectory if one becomes necessary.

### Entry Point Pattern

All root-level `.py` files should be thin wrappers that import from `src/fx_kline`:

```python
# Example: ohlc_aggregator.py
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from fx_kline.core.ohlc_aggregator import main

if __name__ == "__main__":
    raise SystemExit(main())
```

## Build, Test, and Development Commands
Install and sync dependencies with `uv sync`. Launch the Streamlit interface via `uv run streamlit run src/fx_kline/ui/streamlit_app.py` or run the Python wrapper `python main.py`. For quick fetch validation in a terminal-only session, call `uv run python test_fetch.py`. When adding libraries, update `pyproject.toml` and regenerate `uv.lock` with `uv lock`.

## Coding Style & Naming Conventions
Target Python 3.10+ and four-space indentation. Favor descriptive module names that match the existing pattern (`data_fetcher.py`, `timezone_utils.py`) and snake_case for functions, variables, and filenames. Use type hints and pydantic models for data contracts. Run `uv run ruff check --fix .` for linting and `uv run black .` for formatting before asking for review.

## Testing Guidelines

Author pytest-based suites under `tests/` (create the folder if it does not exist) and mirror feature names in test module titles, e.g., `tests/test_timezone_utils.py`. Integration tests that require live data or external services should be placed in `tests/integration/`. Use `uv run pytest` for the full suite. When tests require network calls, mark them and provide offline guards or fixtures so CI can skip flaky scenarios.

## Commit & Pull Request Guidelines
The history is currently empty; seed it with imperative, scope-prefixed messages such as `core: add batch retry logic` to clarify intent. Group related changes into a single commit and mention relevant modules in the body. Pull requests should explain the problem, outline the solution, and include verification steps (commands run, screenshots of the Streamlit UI when applicable). Link to open issues and flag any follow-up tasks so reviewers understand remaining risks.

## Streamlit & MCP Notes
Cache expensive I/O inside Streamlit callbacks using `st.cache_data` where possible, and guard MCP-facing helpers so they remain UI-agnostic. When exposing new data fetch workflows, implement them in `core/` first, cover them with pytest, then thread them into the UI layer to keep the agent-facing API stable.
