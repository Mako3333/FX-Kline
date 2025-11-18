# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2025-11-16

### 🎉 Major Release: MCP 2025 Compliance & Tool Restructuring

This release introduces a major restructuring of MCP tools to improve AI agent experience and comply with MCP 2025 specification.

### Added

#### New MCP Tools
- **`get_intraday_ohlc`**: Specialized tool for intraday trading (1m-4h intervals)
  - Validates interval is appropriate for intraday analysis
  - Default period optimized for day trading (5d)
  - Clear error messages guiding users to correct tool

- **`get_daily_ohlc`**: Specialized tool for swing/position trading (1d-1mo intervals)
  - Validates interval is appropriate for longer-term analysis
  - Default period optimized for swing trading (30d)
  - Clear error messages guiding users to correct tool

- **`get_ohlc_batch`**: Simplified name for batch requests
  - Alias for `fetch_ohlc_batch` with consistent naming
  - Same functionality, better discoverability

- **`list_pairs`**: Simplified name for currency pairs list
  - Alias for `list_available_pairs`
  - Shorter, more intuitive name

- **`list_timeframes`**: Simplified name for timeframes list
  - Alias for `list_available_timeframes`
  - Shorter, more intuitive name

- **`ping`**: Health check endpoint
  - Returns server version, status, and capabilities
  - Lists all available endpoints (including deprecated ones)
  - Useful for debugging and monitoring

#### MCP 2025 Features

- **Tool Annotations** ([MCP 2025 spec](https://modelcontextprotocol.io/))
  - `readOnlyHint`: true for all tools
  - `idempotentHint`: true for all tools
  - `openWorldHint`: true for data fetching, false for metadata
  - `title`: Japanese language titles for better localization

- **Enhanced Error Handling**
  - `category`: ClientError, ServerError, or DataError classification
  - `hint`: Recovery suggestions for each error type
  - `recoverable`: Boolean flag indicating if error can be recovered from
  - `suggested_tools`: Array of tools that might help resolve the error
  - `context`: Additional error context for debugging

- **Completions Feature** ([MCP 2025 spec](https://modelcontextprotocol.io/))
  - Argument auto-completion for all parameters
  - `pair`: Lists all supported pairs with descriptions
  - `interval`: Tool-specific intervals (intraday vs. daily)
  - `period`: Common period values with recommendations
  - `preset_only`: true/false with explanations
  - `exclude_weekends`: true/false with usage guidance

#### Documentation

- **MIGRATION.md**: Comprehensive migration guide from v0.1.0 to v0.2.0
  - Detailed migration instructions for each deprecated tool
  - Migration timeline and backward compatibility information
  - Example code showing before/after comparisons

- **CHANGELOG.md**: This file, tracking all version changes

### Changed

#### Tool Descriptions
- All tool descriptions now include "When to use" guidance
- Added tips for related tools
- Added usage examples and scenarios
- Clarified supported values and ranges

#### Error Messages
- More detailed error messages with recovery hints
- Categorized errors for better handling
- Suggested next steps for common errors
- Context-rich error information

### Deprecated

The following tools are deprecated and will be removed on **2026-05-16** (6 months from release):

- **`fetch_ohlc`** → Use `get_intraday_ohlc` or `get_daily_ohlc` instead
  - Migration: Choose based on interval (1m-4h → intraday, 1d-1mo → daily)

- **`fetch_ohlc_batch`** → Use `get_ohlc_batch` instead
  - Migration: Simple rename, parameters unchanged

- **`list_available_pairs`** → Use `list_pairs` instead
  - Migration: Simple rename, parameters unchanged

- **`list_available_timeframes`** → Use `list_timeframes` instead
  - Migration: Simple rename, parameters unchanged

> ⚠️ All deprecated tools remain fully functional during the 6-month transition period.
> See [MIGRATION.md](./MIGRATION.md) for detailed migration instructions.

### Performance

- No performance changes in this release
- Completions feature adds minimal overhead (< 1ms per completion request)
- All existing functionality maintains same performance characteristics

### Breaking Changes

**None** - This release is fully backward compatible. Deprecated tools will continue to work until 2026-05-16.

### Migration Path

1. **Immediate**: No action required, all existing code continues to work
2. **Recommended**: Migrate to new tools before 2026-02-16 (3 months)
3. **Required**: Must migrate before 2026-05-16 (6 months)

See [MIGRATION.md](./MIGRATION.md) for step-by-step migration guide.

---

## [0.1.0] - 2025-11-10

### 🚀 Initial Public Release

First public release of FX-Kline with MCP server integration.

### Added

#### Core Features
- **Parallel Data Fetching**: asyncio-based parallel OHLC data retrieval
- **Timezone Support**: Automatic UTC→JST conversion with DST handling
- **Business Day Filtering**: Market-specific (FX/commodity) weekend/holiday filtering
- **Data Validation**: Pydantic-based type-safe data models
- **Error Handling**: Comprehensive error classification and recovery strategies

#### User Interfaces
- **Streamlit Web UI**: Intuitive GUI for data fetching and export
- **Python API**: Programmatic access for custom workflows
- **MCP Server**: Claude Desktop/Cline integration

#### MCP Tools (v0.1.0)
- `fetch_ohlc`: Fetch OHLC data for a single currency pair
- `fetch_ohlc_batch`: Parallel batch fetching for multiple pairs
- `list_available_pairs`: List all supported currency pairs
- `list_available_timeframes`: List all supported timeframes

#### Supported Markets
- **Currency Pairs**: 8 major pairs (USDJPY, EURUSD, GBPUSD, AUDUSD, EURJPY, GBPJPY, AUDJPY)
- **Commodities**: Gold (XAUUSD)
- **Timeframes**: 1m, 5m, 15m, 30m, 1h, 4h, 1d, 1wk, 1mo

#### Export Formats
- CSV (with/without headers)
- JSON (formatted)
- Clipboard (for spreadsheet paste)

#### Documentation
- README.md with comprehensive setup instructions
- MCP_SETUP.md for MCP server integration guide
- API reference and usage examples
- Troubleshooting section

### Technical Details
- Python 3.10+ support
- yfinance integration for data source
- Pydantic v2 for data validation
- asyncio for concurrent operations
- Streamlit for UI
- MCP SDK for server implementation

---

## Version History

- **[0.2.0]** - 2025-11-16 - MCP 2025 Compliance & Tool Restructuring
- **[0.1.0]** - 2025-11-10 - Initial Public Release

---

## Links

- [Project Repository](https://github.com/Mako3333/FX-Kline)
- [Migration Guide](./MIGRATION.md)
- [MCP Setup Guide](./MCP_SETUP.md)
- [README](./README.md)

---

**Note**: Dates in this changelog follow the YYYY-MM-DD format.
