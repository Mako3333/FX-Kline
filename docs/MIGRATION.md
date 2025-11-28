# Migration Guide: MCP Tools Restructuring (v0.1.0 → v0.2.0)

This guide helps you migrate from the deprecated MCP tools to the new specialized tools introduced in v0.2.0.

## Overview

Version 0.2.0 introduces a major restructuring of MCP tools to improve tool selection accuracy and user experience. The old tools remain functional but are deprecated and will be removed on **2026-05-16** (6 months from release).

## Quick Migration Table

| Old Tool (Deprecated) | New Tool | Migration Complexity |
|----------------------|----------|---------------------|
| `fetch_ohlc` | `get_intraday_ohlc` or `get_daily_ohlc` | Medium (choose based on interval) |
| `fetch_ohlc_batch` | `get_ohlc_batch` | Easy (rename only) |
| `list_available_pairs` | `list_pairs` | Easy (rename only) |
| `list_available_timeframes` | `list_timeframes` | Easy (rename only) |

---

## Detailed Migration Instructions

### 1. Migrating `fetch_ohlc`

**The old tool:**
```json
{
  "name": "fetch_ohlc",
  "arguments": {
    "pair": "USDJPY",
    "interval": "1h",
    "period": "5d"
  }
}
```

**Choose the appropriate new tool based on interval:**

#### For intraday intervals (1m, 5m, 15m, 30m, 1h, 4h):
```json
{
  "name": "get_intraday_ohlc",
  "arguments": {
    "pair": "USDJPY",
    "interval": "1h",
    "period": "5d"
  }
}
```

#### For daily+ intervals (1d, 1wk, 1mo):
```json
{
  "name": "get_daily_ohlc",
  "arguments": {
    "pair": "USDJPY",
    "interval": "1d",
    "period": "30d"
  }
}
```

**Why split?**
- Better tool selection accuracy for AI agents
- Clear separation of use cases (intraday trading vs. swing trading)
- Validation prevents using wrong interval for wrong analysis type
- Default values optimized for each use case

**Migration checklist:**
- [ ] Identify all `fetch_ohlc` calls in your code
- [ ] For each call, check the `interval` parameter
- [ ] Replace with `get_intraday_ohlc` (1m-4h) or `get_daily_ohlc` (1d-1mo)
- [ ] Update default `period` if needed (intraday: 5d, daily: 30d)

---

### 2. Migrating `fetch_ohlc_batch`

**The old tool:**
```json
{
  "name": "fetch_ohlc_batch",
  "arguments": {
    "requests": [...]
  }
}
```

**The new tool:**
```json
{
  "name": "get_ohlc_batch",
  "arguments": {
    "requests": [...]
  }
}
```

**Migration steps:**
1. Simply rename `fetch_ohlc_batch` → `get_ohlc_batch`
2. All parameters remain identical
3. Behavior is unchanged

**Why rename?**
- Consistency with new tool naming convention
- Shorter, more intuitive name
- Matches naming pattern: `get_*`

---

### 3. Migrating `list_available_pairs`

**The old tool:**
```json
{
  "name": "list_available_pairs",
  "arguments": {
    "preset_only": false
  }
}
```

**The new tool:**
```json
{
  "name": "list_pairs",
  "arguments": {
    "preset_only": false
  }
}
```

**Migration steps:**
1. Rename `list_available_pairs` → `list_pairs`
2. All parameters remain identical

---

### 4. Migrating `list_available_timeframes`

**The old tool:**
```json
{
  "name": "list_available_timeframes",
  "arguments": {
    "preset_only": false
  }
}
```

**The new tool:**
```json
{
  "name": "list_timeframes",
  "arguments": {
    "preset_only": false
  }
}
```

**Migration steps:**
1. Rename `list_available_timeframes` → `list_timeframes`
2. All parameters remain identical

---

## New Features in v0.2.0

### 1. New Tool: `ping`

Health check endpoint for server monitoring:

```json
{
  "name": "ping",
  "arguments": {}
}
```

**Returns:**
- Server version and status
- Supported pairs/timeframes count
- Available features list
- All endpoints (including deprecated ones)

**Use cases:**
- Connection testing
- Debugging
- Monitoring server health
- Discovering available features

---

### 2. MCP 2025 Compliance

#### Tool Annotations
All tools now include annotations:
- `readOnlyHint`: true (all tools are read-only)
- `idempotentHint`: true (repeated calls produce same result)
- `openWorldHint`: true for data fetching, false for metadata
- `title`: Japanese language titles

#### Enhanced Error Handling
Errors now include:
- `category`: ClientError, ServerError, or DataError
- `hint`: Recovery suggestions
- `recoverable`: Whether error can be recovered from
- `suggested_tools`: Tools that might help resolve the error
- `context`: Additional error context

Example:
```json
{
  "success": false,
  "error": {
    "type": "ValidationError",
    "category": "ClientError",
    "message": "Unsupported currency pair: BTCUSD",
    "hint": "Call 'list_pairs' tool to see all supported currency pairs",
    "recoverable": true,
    "suggested_tools": ["list_pairs"],
    "context": {
      "attempted_pair": "BTCUSD",
      "valid_pairs_count": 8
    }
  }
}
```

#### Completions Feature
Argument auto-completion for all parameters:
- `pair`: Lists all supported pairs with descriptions
- `interval`: Tool-specific intervals (intraday vs. daily)
- `period`: Common period values with recommendations
- `preset_only`: true/false with explanations
- `exclude_weekends`: true/false with usage guidance

---

## Migration Timeline

| Date | Event |
|------|-------|
| **2025-11-16** | v0.2.0 released with deprecated warnings |
| **2026-02-16** | 3 months - Reminder warnings in logs |
| **2026-04-16** | 5 months - Final migration reminder |
| **2026-05-16** | **Deprecated tools removed** |

---

## Migration Checklist

### For AI Agent Developers

- [ ] Review all MCP tool calls in your codebase
- [ ] Update `fetch_ohlc` calls to `get_intraday_ohlc` or `get_daily_ohlc`
- [ ] Rename `fetch_ohlc_batch` → `get_ohlc_batch`
- [ ] Rename `list_available_pairs` → `list_pairs`
- [ ] Rename `list_available_timeframes` → `list_timeframes`
- [ ] Test all tool calls with new names
- [ ] Update your prompts to use new tool names
- [ ] Consider using new `ping` tool for health checks

### For End Users (Claude Desktop / Cline)

- [ ] Update MCP server configuration (if custom prompts reference tools)
- [ ] Review any saved workflows using old tool names
- [ ] No action needed if using AI agent's default tool selection

---

## Backward Compatibility

**During the 6-month transition period:**
- ✅ All old tools remain fully functional
- ✅ Deprecated warnings appear in tool descriptions
- ✅ No breaking changes to existing integrations
- ✅ Both old and new tools can be used simultaneously

**After 2026-05-16:**
- ❌ Old tools will be removed
- ✅ Only new tools will be available
- ❌ Code using old tools will fail

---

## Getting Help

- **Documentation**: See README.md for new tool descriptions
- **Changelog**: See CHANGELOG.md for detailed version history
- **Issues**: Report problems at https://github.com/Mako3333/FX-Kline/issues

---

## Example: Full Migration

**Before (v0.1.0):**
```python
# AI agent code using old tools
tools = [
    {"name": "fetch_ohlc", "arguments": {"pair": "USDJPY", "interval": "1h"}},
    {"name": "fetch_ohlc", "arguments": {"pair": "EURUSD", "interval": "1d"}},
    {"name": "list_available_pairs", "arguments": {}},
]
```

**After (v0.2.0):**
```python
# AI agent code using new tools
tools = [
    {"name": "get_intraday_ohlc", "arguments": {"pair": "USDJPY", "interval": "1h"}},
    {"name": "get_daily_ohlc", "arguments": {"pair": "EURUSD", "interval": "1d"}},
    {"name": "list_pairs", "arguments": {}},
]
```

---

**Last Updated:** 2025-11-16
**Version:** 0.2.0
