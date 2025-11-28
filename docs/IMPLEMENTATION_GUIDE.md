# HITL Trading System - Implementation Guide

## 🎯 Overview

This guide provides step-by-step instructions for implementing the HITL (Human-in-the-Loop) Trading System, from initial setup to production deployment.

---

## 📅 Implementation Roadmap

### Phase 1: Core System Setup (Week 1-2)

#### Week 1: L4 Foundation

**Goal**: Establish L4 (HITL) as the core decision-making layer

**Tasks**:
1. **Create `mako_trading_rules.md`**
   - Document your trading style, rules, and past lessons
   - Location: `docs/mako_trading_rules.md`
   - See template below

2. **Setup Claude Project for L4**
   - Create dedicated Claude Project
   - Upload `mako_trading_rules.md` as project knowledge
   - Configure custom instructions

3. **Define L4 Output Format**
   - Create JSON schema for `L4_tradeplan.json`
   - Include HITL intervention tracking
   - See schema below

**Deliverables**:
- ✅ `docs/mako_trading_rules.md`
- ✅ Claude Project configured
- ✅ `L4_tradeplan.json` schema defined

---

#### Week 2: Evaluation System

**Goal**: Build L3 vs L4 comparison framework

**Tasks**:
1. **Implement `l3_evaluator.py`**
   - Already created: `src/fx_kline/core/l3_evaluator.py`
   - Test with sample data
   - Validate metrics calculation

2. **Create L3 Prediction Prompt**
   - Already created: `docs/memo.md`
   - Test prompt with Claude
   - Validate output format

3. **Setup Daily Evaluation Workflow**
   - Script to run evaluations automatically
   - Store results in `data/YYYY-MM-DD/`

**Deliverables**:
- ✅ `l3_evaluator.py` tested and working
- ✅ Sample L3 and L4 evaluations generated
- ✅ Daily evaluation script

---

### Phase 2: Risk Management (Week 3-4)

#### Week 3: Position Sizing & Risk Guards

**Goal**: Implement comprehensive risk management

**Tasks**:
1. **Create `risk_manager.py`**
   ```python
   # src/fx_kline/core/risk_manager.py
   class RiskManager:
       def calculate_position_size(...)
       def check_trade_allowed(...)
       def check_correlation_risk(...)
   ```

2. **Integrate with L4 Workflow**
   - L4 must check risk_manager before finalizing plan
   - Include risk_check in `L4_tradeplan.json`

3. **Define Risk Parameters**
   - Max risk per trade: 2%
   - Daily loss limit: 4%
   - Weekly loss limit: 8%

**Deliverables**:
- ✅ `risk_manager.py` implemented
- ✅ Risk checks integrated in L4
- ✅ Risk parameters documented

---

#### Week 4: Trade Cost & Timing Filters

**Goal**: Add realistic cost modeling and time-based filters

**Tasks**:
1. **Create `trade_cost.py`**
   - Spread calculation by pair and time
   - Breakeven pips calculator
   - Net profit calculator

2. **Implement Time Filters**
   - Economic calendar integration (manual for now)
   - Market session checks
   - Avoid low-liquidity periods

3. **Update L4 Decision Logic**
   - Include cost-benefit analysis
   - Add time filter warnings

**Deliverables**:
- ✅ `trade_cost.py` implemented
- ✅ Time filters in L4
- ✅ Economic calendar checklist

---

### Phase 3: Backtest & Validation (Week 5-6)

#### Week 5: Historical Simulation

**Goal**: Validate system with past data

**Tasks**:
1. **Create `backtest_simulator.py`**
   ```python
   class HistoricalSimulator:
       def simulate_historical_day(date: str)
       def run_monthly_backtest(year: int, month: int)
   ```

2. **Collect Historical Data**
   - OHLC: Already available via yfinance
   - L1 (News): Manual collection or web scraping
   - Target: 30 days of historical simulation

3. **Run Initial Backtest**
   - Generate L3 and L4 for each historical day
   - Compare against actual outcomes
   - Aggregate results

**Deliverables**:
- ✅ `backtest_simulator.py` working
- ✅ 30-day historical simulation complete
- ✅ Initial performance report

---

#### Week 6: Refinement & Calibration

**Goal**: Improve system based on backtest results

**Tasks**:
1. **Analyze Backtest Results**
   - Identify failure patterns
   - Check confidence calibration
   - Measure L3 vs L4 delta

2. **Refine Rules**
   - Update `mako_trading_rules.md` based on findings
   - Adjust L3 prompt if needed
   - Tune risk parameters

3. **Repeat Backtest**
   - Validate improvements
   - Target: 60%+ accuracy, Sharpe > 1.0

**Deliverables**:
- ✅ Backtest analysis report
- ✅ Refined trading rules
- ✅ Improved performance metrics

---

### Phase 4: Content Strategy (Week 7-8)

#### Week 7: X (Twitter) Automation

**Goal**: Build transparent content pipeline

**Tasks**:
1. **Create `content_publisher.py`**
   - Auto-post daily decisions to X
   - Include summary metrics
   - Template-based posts

2. **Design Content Templates**
   - Pre-trade announcement
   - Post-trade result
   - Weekly summary

3. **Test Publishing**
   - Dry-run with test account
   - Refine formatting
   - Schedule automation

**Deliverables**:
- ✅ `content_publisher.py` working
- ✅ X account configured
- ✅ First public post

---

#### Week 8: Note Content Creation

**Goal**: Build premium content offering

**Tasks**:
1. **Design Note Article Structure**
   - Weekly free articles
   - Monthly premium deep-dives
   - Template creation

2. **Create Sample Articles**
   - Write 2-3 sample articles
   - Get feedback from test readers
   - Refine format

3. **Setup Monetization**
   - Note premium membership
   - Pricing: ¥500-1000/month
   - Payment integration

**Deliverables**:
- ✅ Note article templates
- ✅ 3 sample articles published
- ✅ Premium membership launched

---

### Phase 5: Production Launch (Week 9-12)

#### Week 9-10: Paper Trading

**Goal**: Run system with real-time data, no real money

**Tasks**:
1. **Setup Paper Trading Account**
   - Use demo broker account
   - Connect to real-time data feed
   - Track all trades

2. **Run Daily Workflow**
   - L1: Manual analysis (mako)
   - L2: Auto-generated (GitHub Actions)
   - L3: Auto-generated (Claude API)
   - L4: Manual decision (mako + Claude Project)
   - L5: Weekly review

3. **Monitor Performance**
   - Daily metrics tracking
   - Weekly reviews
   - Identify any issues

**Deliverables**:
- ✅ 20 paper trades executed
- ✅ System running smoothly
- ✅ No critical bugs

---

#### Week 11-12: Real Money Launch

**Goal**: Transition to live trading with small capital

**Tasks**:
1. **Start with Small Capital**
   - Initial: ¥100,000-500,000
   - Limit position size to 0.1 lots
   - Conservative risk (1% per trade)

2. **Strict Discipline**
   - Follow ALL rules without exception
   - No emotional overrides
   - Document everything

3. **Weekly Check-ins**
   - Review all trades
   - Update L5 reviews
   - Publish content

**Deliverables**:
- ✅ First 10 real trades executed
- ✅ Positive expectancy confirmed
- ✅ Content publishing on schedule

---

## 📝 Key Templates

### Template 1: mako_trading_rules.md

```markdown
# Mako's Trading Rules & Style

## Basic Profile
- **Frequency**: 2-5 trades per week (selective)
- **Timeframe**: 4h-1d primary, 1h for entry timing
- **Pairs**: USDJPY (main), EURJPY/GBPJPY (secondary)
- **Risk per trade**: 1-2% of account

## Entry Conditions (ALL must be met)

### 1. Fundamental Alignment
- L1 market theme must support direction
- Example: "Dollar strength theme" → Only consider USDJPY LONG
- If L1 is unclear or conflicting → WAIT

### 2. Multi-Timeframe Confluence
- **Daily**: Trend direction
- **4-hour**: Pullback/bounce to support/resistance
- **1-hour**: Entry timing confirmation

If ANY timeframe conflicts → WAIT

### 3. Risk:Reward Minimum
- Must be at least 2:1
- Preferably 3:1 or better
- Use nearest support/resistance for stop/target

### 4. Support/Resistance Clarity
- Entry near strong S/R level
- Clear invalidation point (stop loss)
- Target at next major level

## Mandatory WAIT Conditions

If ANY of these is true → WAIT:

1. **High-impact event within 24 hours**
   - US NFP, FOMC, BOJ meeting, etc.
   - Check economic calendar EVERY day

2. **RSI Extremes**
   - RSI > 70 or RSI < 30 on 1d chart
   - Indicates potential reversal

3. **Excessive Volatility**
   - ATR > 150% of 14-day average
   - Market too unstable

4. **Unclear Market Regime**
   - L2 shows CHOPPY regime
   - Conflicting signals across timeframes

5. **Lack of Conviction**
   - If confidence < 80% → WAIT
   - "When in doubt, sit it out"

## Position Management

### Entry
- Preferred: Limit order at support/resistance
- Acceptable: Market order if setup is strong
- Position size: Calculate via risk_manager

### Stop Loss
- Place OUTSIDE support/resistance
- Typically: S/R level ± (ATR × 0.5)
- NEVER move stop loss closer (except to breakeven)

### Take Profit
- Primary target: Risk:Reward 2:1
- Scale out: 50% at 2R, 50% at trailing stop
- Trailing stop: ATR × 2

### Time-based Exit
- If no movement after 2 days → Re-evaluate
- Consider closing if setup invalidated

## Past Mistakes & Lessons

### Mistake 1: Ignoring Fundamentals (2024-11-15)
- **What happened**: Strong chart setup, but contradicted L1 theme
- **Result**: -65 pips
- **Lesson**: NEVER ignore L1. If L1 conflicts with L2, WAIT.

### Mistake 2: Trading Before NFP (2024-10-22)
- **What happened**: Entered 12 hours before NFP
- **Result**: Stopped out by volatility spike
- **Lesson**: 24-hour rule is NON-NEGOTIABLE

### Mistake 3: Greed - Didn't Take Profit (2024-09-10)
- **What happened**: Hit 2R target but held for "more"
- **Result**: Gave back 50% of profit
- **Lesson**: AT LEAST take 50% at 2R. Always.

### Mistake 4: Revenge Trading (2024-08-20)
- **What happened**: Lost 2 trades, immediately entered 3rd to "recover"
- **Result**: 3rd loss, total -6%
- **Lesson**: After 2 losses in a row, STOP for the day.

## Psychological Rules

### Before Entry
- [ ] Am I following ALL entry conditions?
- [ ] Am I calm and confident (not anxious)?
- [ ] Have I checked economic calendar?
- [ ] Is my stop loss pre-calculated?

### During Trade
- [ ] Avoid checking price too frequently (max 3x/day)
- [ ] Do NOT move stop loss (except to breakeven)
- [ ] Trust the plan

### After Trade (Win or Loss)
- [ ] Log trade in journal immediately
- [ ] What did I do right?
- [ ] What could be improved?
- [ ] Am I emotionally stable for next trade?

## Forbidden Actions

❌ **NEVER**:
- Trade during high-impact events
- Move stop loss toward price (increasing risk)
- Average down on losing position
- Exceed 2% risk per trade
- Trade when tired, angry, or emotional
- Deviate from rules "just this once"

## Weekly Review Checklist

Every Sunday:
- [ ] Review all trades (journal)
- [ ] Calculate metrics (win rate, profit factor, etc.)
- [ ] Update this document with new lessons
- [ ] Plan next week's potential setups
- [ ] Check next week's economic calendar

---

**Version**: 1.0
**Last Updated**: 2025-11-28
**Next Review**: 2025-12-05
```

---

### Template 2: L4_tradeplan.json Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "L4 HITL Trade Plan",
  "type": "object",
  "required": ["base_prediction", "final_plan", "generated_at"],
  "properties": {
    "base_prediction": {
      "type": "object",
      "description": "L3 prediction as starting point",
      "properties": {
        "source": { "type": "string", "example": "L3_prediction.json" },
        "original_direction": { "type": "string", "enum": ["LONG", "SHORT", "WAIT"] },
        "original_entry": { "type": "number" },
        "original_confidence": { "type": "number", "minimum": 0, "maximum": 1 }
      }
    },
    "hitl_modifications": {
      "type": "array",
      "description": "Human interventions applied to L3",
      "items": {
        "type": "object",
        "properties": {
          "field": { "type": "string", "example": "entry_price" },
          "original_value": {},
          "modified_value": {},
          "reason": { "type": "string" },
          "modification_type": {
            "type": "string",
            "enum": ["conservative_adjustment", "aggressive_adjustment", "risk_reduction", "trade_cancellation"]
          }
        }
      }
    },
    "risk_check": {
      "type": "object",
      "properties": {
        "account_balance": { "type": "number" },
        "today_loss": { "type": "number" },
        "week_loss": { "type": "number" },
        "risk_guard_status": { "type": "string", "enum": ["OK", "BLOCKED"] },
        "max_position_size": { "type": "number" }
      }
    },
    "final_plan": {
      "type": "object",
      "required": ["direction"],
      "properties": {
        "direction": { "type": "string", "enum": ["LONG", "SHORT", "WAIT"] },
        "pair": { "type": "string" },
        "entry_price": { "type": "number" },
        "stop_loss": { "type": "number" },
        "take_profit": { "type": "number" },
        "position_size": { "type": "number" },
        "risk_percent": { "type": "number" },
        "confidence_score": { "type": "number", "minimum": 0, "maximum": 1 },
        "reasoning": { "type": "string" },
        "execution_status": { "type": "string", "enum": ["PENDING", "EXECUTED", "CANCELLED_BY_HUMAN", "BLOCKED_BY_RISK"] }
      }
    },
    "generated_at": { "type": "string", "format": "date-time" }
  }
}
```

---

### Template 3: Daily Workflow Script

```bash
#!/bin/bash
# daily_workflow.sh - Run this every trading day

set -e  # Exit on error

DATE=$(date +%Y-%m-%d)
DATA_DIR="data/${DATE}"
mkdir -p "${DATA_DIR}"

echo "==================================================="
echo "Daily HITL Trading Workflow: ${DATE}"
echo "==================================================="

# Step 1: Fetch OHLC (already automated via GitHub Actions)
echo "[1/6] OHLC data fetch (automated)"

# Step 2: Generate L2 Technical Analysis
echo "[2/6] Generating L2 technical analysis..."
uv run python -m fx_kline.core.ohlc_aggregator \
  --input-dir data/ohlc \
  --output-dir "${DATA_DIR}" \
  --glob "USDJPY_*.csv" "EURJPY_*.csv"

# Step 3: Manual L1 Fundamental Analysis
echo "[3/6] L1 fundamental analysis (manual)"
echo "Please create: ${DATA_DIR}/L1_fundamental.md"
echo "Press Enter when ready..."
read -r

# Step 4: Generate L3 Prediction (AI-only)
echo "[4/6] Generating L3 prediction..."
# This requires Claude API integration
# For now, manual generation via Claude web interface
echo "Use docs/memo.md prompt to generate L3_prediction.json"
echo "Save to: ${DATA_DIR}/L3_prediction.json"
echo "Press Enter when ready..."
read -r

# Step 5: Generate L4 Trade Plan (HITL)
echo "[5/6] L4 trade plan generation (manual)"
echo "Use Claude Project with mako_trading_rules.md"
echo "Review L1 + L2 + L3, then create L4_tradeplan.json"
echo "Save to: ${DATA_DIR}/L4_tradeplan.json"
echo "Press Enter when ready..."
read -r

# Step 6: Execute Trade (if approved)
echo "[6/6] Trade execution"
echo "Review L4_tradeplan.json and execute via broker platform"
echo "Log execution details for tomorrow's evaluation"

echo "==================================================="
echo "Workflow complete. Next steps:"
echo "  - Monitor trade during the day"
echo "  - Tomorrow: Run evaluation with l3_evaluator.py"
echo "  - Weekly: Generate L5_review.yaml"
echo "==================================================="
```

---

## 🔧 Technical Setup

### Prerequisites

- Python 3.10+
- uv package manager
- Claude API access (or Claude.ai web access)
- Git & GitHub account
- FX broker account (demo for testing, live for production)

### Installation

```bash
# Clone repository
git clone https://github.com/Mako3333/FX-Kline.git
cd FX-Kline

# Install dependencies
uv sync

# Install additional tools
uv sync --extra mcp
uv sync --extra dev

# Verify installation
uv run python -m fx_kline.core.l3_evaluator --help
```

### Directory Structure

```
FX-Kline/
├── data/                      # Daily data storage
│   └── YYYY-MM-DD/
│       ├── L1_fundamental.md
│       ├── L2_technical.md
│       ├── L3_prediction.json
│       ├── L4_tradeplan.json
│       ├── L4_ai_evaluation.json
│       ├── L4_hitl_evaluation.json
│       └── L5_review.yaml
├── docs/                      # Documentation
│   ├── HITL_SYSTEM_ADVICE.md
│   ├── ACADEMIC_VALUE.md
│   ├── IMPLEMENTATION_GUIDE.md
│   ├── memo.md
│   └── mako_trading_rules.md
├── src/fx_kline/
│   ├── core/
│   │   ├── l3_evaluator.py    # NEW: Evaluation script
│   │   ├── risk_manager.py    # TODO: Risk management
│   │   ├── trade_cost.py      # TODO: Cost calculation
│   │   └── backtest_simulator.py  # TODO: Historical simulation
│   └── ...
└── scripts/
    ├── daily_workflow.sh      # TODO: Daily automation
    └── content_publisher.py   # TODO: X/Note publishing
```

---

## 🎯 Success Criteria

### Phase 1-2 Complete (Week 4)
- [ ] L3 and L4 pipelines working
- [ ] Risk management implemented
- [ ] 10+ manual trades logged

### Phase 3 Complete (Week 6)
- [ ] 30-day backtest done
- [ ] Accuracy > 55%
- [ ] Sharpe ratio > 1.0

### Phase 4 Complete (Week 8)
- [ ] X account active with 100+ followers
- [ ] 3 Note articles published
- [ ] Premium membership launched

### Phase 5 Complete (Week 12)
- [ ] 20+ real trades executed
- [ ] Positive expectancy confirmed
- [ ] Monthly profit target met

---

## 🚨 Common Pitfalls & Solutions

### Pitfall 1: Inconsistent Rule Application

**Problem**: Sometimes following rules, sometimes not
**Solution**: Use L4 checklist EVERY TIME before trade

### Pitfall 2: Over-optimization

**Problem**: Tweaking rules after every loss
**Solution**: Only change rules after 30+ trades analysis

### Pitfall 3: Emotional Trading

**Problem**: Revenge trading after losses
**Solution**: Hard stop after 2 consecutive losses

### Pitfall 4: Ignoring Risk Management

**Problem**: "Just this once" with 5% risk
**Solution**: Automate risk checks in code (can't bypass)

### Pitfall 5: Inconsistent Documentation

**Problem**: Missing L5 reviews
**Solution**: Calendar reminder every Sunday

---

## 📞 Support & Resources

### Internal Resources
- `docs/HITL_SYSTEM_ADVICE.md`: Comprehensive advice
- `docs/ACADEMIC_VALUE.md`: Research methodology
- `docs/memo.md`: L3 prediction prompt

### External Resources
- Claude API: https://console.anthropic.com
- yfinance docs: https://pypi.org/project/yfinance/
- pandas-ta: https://github.com/twopirllc/pandas-ta

### Community
- GitHub Issues: https://github.com/Mako3333/FX-Kline/issues
- X (Twitter): @[your-handle]
- Note: [your-note-url]

---

**Next Steps**: Start with Week 1 tasks. Create `mako_trading_rules.md` first!

**Last Updated**: 2025-11-28
**Version**: 1.0
