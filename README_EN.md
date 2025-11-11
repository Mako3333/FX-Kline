# FX-Kline

<div align="center">

**AI-Powered Foreign Exchange OHLC Data Fetcher**

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![MCP Compatible](https://img.shields.io/badge/MCP-Compatible-green.svg)](https://modelcontextprotocol.io/)

English | [日本語](./README.md)

</div>

---

## 📖 Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Demo](#demo)
- [Supported Markets](#supported-markets)
- [Quick Start](#quick-start)
- [Usage](#usage)
- [MCP Server Integration](#mcp-server-integration)
- [Project Structure](#project-structure)
- [API Reference](#api-reference)
- [Development](#development)
- [Troubleshooting](#troubleshooting)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

**FX-Kline** is a Python application for efficiently fetching and processing OHLC (Open-High-Low-Close) data from foreign exchange markets. It provides both an intuitive Streamlit UI and a Model Context Protocol (MCP) server, supporting manual analysis and AI-driven automated analysis.

### Why Choose FX-Kline?

- 🚀 **Parallel Data Fetching**: Fetch multiple currency pairs and timeframes simultaneously (asyncio implementation)
- 🌏 **Full JST Support**: Automatic UTC→JST conversion with DST (Daylight Saving Time) support
- 📊 **Business Day Filtering**: Advanced filtering based on FX market trading days
- 🤖 **AI Integration**: MCP server compatible with Claude Desktop/Cline
- 💾 **Multiple Export Formats**: CSV, JSON, and clipboard support
- 🎯 **Easy to Use**: Three interfaces - Web UI, Python API, and MCP

---

## Key Features

### 🔥 Core Capabilities

| Feature | Description |
|---------|-------------|
| **Parallel Fetching** | High-speed multi-request processing with asyncio |
| **Timezone Conversion** | Automatic UTC→JST conversion with US/Europe DST support |
| **Business Day Filter** | Market-specific (FX/Commodities) weekend/holiday exclusion |
| **Data Validation** | Type-safe data models with Pydantic |
| **Error Handling** | Detailed error classification and recovery strategies |

### 🎨 User Interfaces

#### 1️⃣ Streamlit Web UI
- Intuitive GUI for data fetching
- Real-time preview
- One-click export

#### 2️⃣ Python API
- Programmatic access
- Batch processing support
- Custom workflow integration

#### 3️⃣ MCP Server ✨
- Natural language operations via Claude Desktop
- Automatic integration with AI analysis
- Multi-tool collaboration

---

## Demo

### Streamlit UI

```bash
# Launch UI
uv run streamlit run src/fx_kline/ui/streamlit_app.py
```

> 💡 With Streamlit UI, you can select multiple currency pairs and timeframes using multi-select and fetch them in parallel.

### Python API

```python
from fx_kline.core import OHLCRequest, fetch_batch_ohlc_sync

# Fetch multiple requests in parallel
requests = [
    OHLCRequest(pair="USDJPY", interval="1d", period="30d"),
    OHLCRequest(pair="EURUSD", interval="1h", period="5d"),
]

response = fetch_batch_ohlc_sync(requests)
print(f"Completed: {response.total_succeeded}/{response.total_requested}")
```

### MCP Server

```
User: "Fetch the last 30 days of USDJPY daily data and analyze the trend"

Claude: Fetching and analyzing data...
        [Automatically executes fetch_ohlc tool]
        Analysis: Uptrend continues, moving averages show...
```

---

## Supported Markets

### 📈 Currency Pairs (8 pairs total)

| Category | Pair | Code |
|----------|------|------|
| **Majors** | USD/JPY | `USDJPY` |
| | EUR/USD | `EURUSD` |
| | GBP/USD | `GBPUSD` |
| | AUD/USD | `AUDUSD` |
| **Crosses** | EUR/JPY | `EURJPY` |
| | GBP/JPY | `GBPJPY` |
| | AUD/JPY | `AUDJPY` |
| **Commodities** | Gold | `XAUUSD` |

### ⏱️ Timeframes

- `5m` - 5 minutes
- `15m` - 15 minutes
- `1h` - 1 hour
- `4h` - 4 hours
- `1d` - Daily

> 📝 Future updates will support 1-minute, weekly, and monthly timeframes

---

## Quick Start

### Prerequisites

- **Python**: 3.10 or higher
- **Package Manager**: [uv](https://github.com/astral-sh/uv) (recommended) or pip

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/Mako3333/FX-Kline.git
cd FX-Kline

# 2. Install dependencies
uv sync

# 3. (Optional) For MCP server usage
uv sync --extra mcp
```

### Launch

#### Streamlit UI

```bash
# Method 1: Streamlit command
uv run streamlit run src/fx_kline/ui/streamlit_app.py

# Method 2: Simple script
python main.py
```

Your browser will automatically open http://localhost:8501

#### MCP Server

See the detailed guide in [MCP_SETUP.md](./MCP_SETUP.md)

---

## Usage

### 🖥️ Streamlit UI

1. **Configure in Sidebar**
   - Select currency pairs (multiple selection)
   - Select timeframes (multiple selection)
   - Specify fetch period in business days

2. **Fetch Data**
   - Click "Fetch Data" button
   - Requests execute in parallel

3. **Export**
   - Download CSV/JSON
   - Copy to clipboard

### 💻 Python API

```python
from fx_kline.core import OHLCRequest, fetch_batch_ohlc_sync

# Create requests
requests = [
    OHLCRequest(pair="USDJPY", interval="1d", period="30d"),
    OHLCRequest(pair="EURUSD", interval="1h", period="5d"),
    OHLCRequest(pair="XAUUSD", interval="15m", period="1d"),
]

# Batch fetch
response = fetch_batch_ohlc_sync(requests, exclude_weekends=True)

# Process results
for ohlc in response.successful:
    print(f"{ohlc.pair}: {ohlc.data_count} data points")
    # Data is stored in ohlc.rows
```

See [API Reference](#api-reference) for details.

---

## MCP Server Integration

<div align="center">

### 🤖 Integrate with Claude Desktop for Automated AI Analysis

</div>

FX-Kline operates as a Model Context Protocol (MCP) server and can be used directly from AI tools like Claude Desktop and Cline.

### ✨ MCP Server Benefits

| Benefit | Description |
|---------|-------------|
| 🗣️ **Natural Language Interface** | "Fetch USDJPY data" - that's all you need |
| 🔄 **Automated Workflows** | Automate data fetch→analysis→report generation |
| 🧩 **Tool Integration** | Combine with other MCP tools for advanced analysis |
| ⚡ **Efficiency** | No code needed, interactive data exploration |

### 🚀 MCP Quick Start

```bash
# 1. Install MCP dependencies
uv sync --extra mcp

# 2. Edit Claude Desktop config file
# macOS/Linux: ~/.config/claude/claude_desktop_config.json
# Windows: %APPDATA%\Claude\claude_desktop_config.json
```

**Configuration Example**:

```json
{
  "mcpServers": {
    "fx-kline": {
      "command": "uv",
      "args": ["run", "python", "/path/to/FX-Kline/run_mcp_server.py"]
    }
  }
}
```

> **⚠️ Important**: Replace `/path/to/FX-Kline/` with the **absolute path** to your FX-Kline directory.
>
> Example (macOS/Linux): `/Users/username/projects/FX-Kline/run_mcp_server.py`
> Example (Windows): `C:\Users\username\projects\FX-Kline\run_mcp_server.py`

For detailed setup instructions and use cases, see **[MCP_SETUP.md](./MCP_SETUP.md)**

### 🛠️ Implemented MCP Tools

| Tool Name | Function |
|-----------|----------|
| `fetch_ohlc` | Fetch data for single currency pair |
| `fetch_ohlc_batch` | Parallel batch fetching for multiple requests |
| `list_available_pairs` | List available currency pairs |
| `list_available_timeframes` | List available timeframes |

### 📚 Usage Example

```
User: "Fetch 1-hour data for USDJPY, EURUSD, and GBPUSD over the last 5 days and analyze correlations"

Claude: Fetching data...
        [Executes fetch_ohlc_batch tool]

        Correlation Analysis:
        - USDJPY vs EURUSD: -0.65 (negative correlation)
        - USDJPY vs GBPUSD: -0.72 (strong negative correlation)
        - EURUSD vs GBPUSD: +0.89 (strong positive correlation)

        Analysis: USD/JPY shows inverse correlation with other pairs...
```

---

## Project Structure

```
fx-kline/
├── src/fx_kline/
│   ├── core/                      # Core business logic
│   │   ├── models.py              # Pydantic data models
│   │   ├── validators.py          # Input validation & constants
│   │   ├── timezone_utils.py      # UTC↔JST conversion, DST support
│   │   ├── business_days.py       # Business day filtering
│   │   └── data_fetcher.py        # Parallel data fetching
│   ├── mcp/                       # MCP server implementation
│   │   ├── server.py              # MCP server core
│   │   └── tools.py               # MCP tool definitions
│   └── ui/
│       └── streamlit_app.py       # Streamlit web app
├── main.py                        # Streamlit launcher
├── run_mcp_server.py              # MCP server launcher
├── claude_desktop_config.example.json  # Claude Desktop config example
├── test_mcp_tools.py              # MCP tools test
├── pyproject.toml                 # Project configuration
├── README.md                      # Japanese README
└── MCP_SETUP.md                   # MCP setup guide
```

### Architecture Highlights

- **3-Tier Structure**: Core (business logic), UI (presentation), MCP (integration layer)
- **Complete Separation**: Each layer is independent and doesn't affect others
- **Reusability**: Core module can be used from both UI and MCP
- **Extensibility**: Easy to add new interfaces

---

## API Reference

### OHLCRequest

Define a single data fetch request.

```python
from fx_kline.core import OHLCRequest

request = OHLCRequest(
    pair="USDJPY",      # Currency pair code
    interval="1h",      # Timeframe (5m, 15m, 1h, 4h, 1d)
    period="30d"        # Fetch period (1d, 5d, 1mo, 3mo, 1y, etc.)
)
```

### fetch_batch_ohlc_sync()

Fetch multiple requests in parallel.

```python
from fx_kline.core import fetch_batch_ohlc_sync

response = fetch_batch_ohlc_sync(
    requests=[...],           # List of OHLCRequests
    exclude_weekends=True     # Exclude weekend data
)

# Response
response.successful          # List of successful OHLCData
response.failed             # List of failed FetchErrors
response.total_requested    # Total request count
response.total_succeeded    # Success count
response.total_failed       # Failure count
response.summary            # Summary string
```

### Export Functions

```python
from fx_kline.core import export_to_csv, export_to_json

# CSV format
csv_string = export_to_csv(ohlc_data)

# JSON format
json_string = export_to_json(ohlc_data)
```

### Timezone Utilities

```python
from fx_kline.core import (
    get_jst_now,                    # Current JST time
    utc_to_jst,                     # UTC→JST conversion
    get_us_market_hours_in_jst,     # NY market hours (JST)
    is_us_dst_active                # US DST check
)
```

### Business Day Utilities

```python
from fx_kline.core import (
    get_business_days_back,         # Date N business days ago
    count_business_days,            # Business days in period
    filter_business_days            # Remove weekends from DataFrame
)
```

Detailed API documentation [here](./docs/API.md) (to be added)

---

## Development

### Running Tests

```bash
# Basic data fetch test
uv run python test_fetch.py

# MCP tools test
uv run python test_mcp_tools.py

# Debug (yfinance data structure check)
uv run python debug_fetch.py
```

### Code Quality

```bash
# Formatting
uv run black .

# Linting
uv run ruff check --fix .
```

### Dependency Management

```bash
# Update dependencies
uv sync --upgrade

# Install specific groups only
uv sync --extra mcp        # MCP
uv sync --extra dev        # Development
```

---

## Troubleshooting

### Common Issues

<details>
<summary><b>Streamlit won't start</b></summary>

```bash
# Reset Streamlit config
rm -rf ~/.streamlit
uv sync --upgrade
uv run streamlit run src/fx_kline/ui/streamlit_app.py
```
</details>

<details>
<summary><b>Cannot fetch data</b></summary>

1. Check internet connection
2. Check yfinance version: `uv pip list | grep yfinance`
3. Verify currency pair code (use uppercase)
4. Run debug script: `uv run python debug_fetch.py`
</details>

<details>
<summary><b>MCP server not recognized</b></summary>

1. Completely quit Claude Desktop
2. Verify config file path is absolute
3. Install dependencies: `uv sync --extra mcp`
4. Restart Claude Desktop
</details>

<details>
<summary><b>Incorrect timezone</b></summary>

- All data is automatically converted to JST (Japan Standard Time)
- Check current time with `get_jst_now()`
- DST (Daylight Saving Time) is automatically handled
</details>

### Error Types

| Error | Cause | Solution |
|-------|-------|----------|
| `NoDataAvailable` | No data for specified period | Extend fetch period |
| `AllWeekendData` | All fetched data is weekends | Extend fetch period |
| `ValidationError` | Invalid currency pair/timeframe | Check supported pairs |
| `TypeError` | Data type conversion error | Check yfinance version |

---

## Roadmap

### 🎯 Current Status (v0.1.0)

- ✅ Streamlit Web UI
- ✅ Python API
- ✅ MCP Server Integration
- ✅ 8 currency pairs
- ✅ 5 timeframes

### 🚀 Future Plans

#### v0.2.0 (Next Version)
- [ ] 1-minute, weekly, and monthly timeframe support
- [ ] Data caching functionality
- [ ] Enhanced rate limiting protection
- [ ] Comprehensive test suite

#### v0.3.0
- [ ] Additional currency pairs
- [ ] Custom indicator functionality
- [ ] Database storage option
- [ ] REST API

#### v1.0.0
- [ ] Complete English documentation
- [ ] Docker support
- [ ] Web hosting support
- [ ] Premium data source support

Share your ideas and requests via [Issues](https://github.com/Mako3333/FX-Kline/issues)

---

## Contributing

Contributions to FX-Kline are welcome!

### How to Contribute

1. **Create an Issue**: Bug reports or feature requests go to [Issues](https://github.com/Mako3333/FX-Kline/issues)
2. **Pull Requests**:
   - Fork and create a branch
   - Implement code
   - Add tests
   - Create PR

### Development Guidelines

- Python 3.10+ compatible
- 4-space indentation
- Use type hints
- Validate data with Pydantic models
- Commit messages in English (e.g., `feat: add new feature`)

See [AGENTS.md](./AGENTS.md) for details.

### Contributors

Thanks to all contributors to this project.

---

## License

This project is released under the [MIT License](./LICENSE).

```
MIT License

Copyright (c) 2025 Mako3333

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files...
```

---

## Acknowledgments

- [yfinance](https://github.com/ranaroussi/yfinance) - Market data provider
- [Streamlit](https://streamlit.io/) - Web UI framework
- [Model Context Protocol](https://modelcontextprotocol.io/) - AI integration standard
- [Anthropic Claude](https://www.anthropic.com/) - AI analysis partner

---

## Support & Contact

- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/Mako3333/FX-Kline/issues)
- 💡 **Feature Requests**: [GitHub Issues](https://github.com/Mako3333/FX-Kline/issues)
- 📧 **Other**: GitHub Discussions or Issues

---

<div align="center">

**[⬆ Back to Top](#fx-kline)**

Made with ❤️ by [Mako3333](https://github.com/Mako3333)

⭐ Star this project if you find it helpful!

</div>
