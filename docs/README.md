# FX HITL Trading System - Documentation Index

## 📚 Overview

Welcome to the comprehensive documentation for the **FX HITL (Human-in-the-Loop) Trading System**. This system integrates AI predictions with human judgment to create a hybrid trading approach that combines the best of both worlds.

**System Architecture**:
```
L1 (Fundamental) → L2 (Technical) → L3 (AI Prediction) → L4 (HITL Decision) → L5 (Review)
                                            ↓
                                    Evaluation & Learning
```

---

## 📖 Documentation Structure

### Core Documents

#### 1. [HITL_SYSTEM_ADVICE.md](./HITL_SYSTEM_ADVICE.md) ⭐ **START HERE**
**Professional fund manager's comprehensive advice**

**Contents**:
- Risk management framework (position sizing, stop loss, correlation)
- Trade cost considerations (spreads, timing)
- Performance tracking (KPIs, metrics)
- Market environment filters
- Time-based filters
- Backtest/forward test methodology
- Economic event risk management

**Read this if**: You want to understand the complete system from a professional trading perspective.

**Key Takeaway**: Implementation priorities and success criteria for production trading.

---

#### 2. [ACADEMIC_VALUE.md](./ACADEMIC_VALUE.md) 📚
**Research potential and academic contributions**

**Contents**:
- Research questions (RQ1-3)
- Methodology for academic papers
- Data collection and statistical rigor
- Potential journals and conferences
- Open science approach
- Calibration analysis
- Layered decision architecture theory

**Read this if**: You're interested in the research/academic value of this system, or planning to publish findings.

**Key Takeaway**: This system has significant academic value beyond just trading profits.

---

#### 3. [IMPLEMENTATION_GUIDE.md](./IMPLEMENTATION_GUIDE.md) 🔧
**Step-by-step implementation roadmap**

**Contents**:
- 12-week implementation plan (Phase 1-5)
- Technical setup instructions
- Key templates (mako_trading_rules.md, L4_tradeplan.json)
- Daily workflow automation
- Success criteria per phase
- Common pitfalls and solutions

**Read this if**: You're ready to start building the system.

**Key Takeaway**: Structured approach from zero to production in 12 weeks.

---

#### 4. [memo.md](./memo.md) 🤖
**L3 Prediction Generation - Prompt Template**

**Contents**:
- System prompt for generating L3_prediction.json
- Confidence score calculation guidelines
- Example inputs and outputs
- Calibration guidelines
- Testing and validation checklist
- Integration with l3_evaluator.py

**Read this if**: You need to generate AI-only predictions (L3) from L1+L2 reports.

**Key Takeaway**: Copy-paste ready prompt for Claude to generate structured predictions.

---

#### 5. [CONTENT_STRATEGY.md](./CONTENT_STRATEGY.md) 📱
**Content monetization and community building**

**Contents**:
- X (Twitter) content strategy
- Note (Japanese Medium) monetization
- GitHub open source approach
- Content templates and schedules
- Revenue projections
- Community engagement tactics

**Read this if**: You want to build an audience and create a secondary income stream through transparent process sharing.

**Key Takeaway**: Dual revenue model (trading + content) with specific tactics.

---

## 🚀 Quick Start Guide

### For Traders

**Goal**: Start trading with HITL system

1. Read: [HITL_SYSTEM_ADVICE.md](./HITL_SYSTEM_ADVICE.md) (Priority sections: Risk Management, Trade Cost)
2. Follow: [IMPLEMENTATION_GUIDE.md](./IMPLEMENTATION_GUIDE.md) Phase 1-2
3. Create: Your own `mako_trading_rules.md` (see template in Implementation Guide)
4. Test: Paper trading for 2 weeks

**Time**: 2-4 weeks to production-ready

---

### For Researchers

**Goal**: Use this system for academic research

1. Read: [ACADEMIC_VALUE.md](./ACADEMIC_VALUE.md)
2. Review: Statistical methodology and required sample sizes
3. Setup: Data collection pipeline
4. Run: Historical simulation (backtest_simulator.py)

**Output**: Dataset for publication, potential paper topics

---

### For Content Creators

**Goal**: Build audience through transparent process sharing

1. Read: [CONTENT_STRATEGY.md](./CONTENT_STRATEGY.md)
2. Setup: X and Note accounts
3. Create: Content templates
4. Schedule: Daily/weekly posting

**Revenue Target**: ¥25,000-50,000/month by Month 6

---

## 🎯 Key Concepts

### L1: Fundamental Analysis
- **What**: Market themes, economic indicators, central bank policy
- **Who**: Human (mako)
- **Output**: `L1_fundamental.md`
- **Frequency**: Daily (before major trading sessions)

### L2: Technical Analysis
- **What**: OHLC data, support/resistance, indicators (RSI, ATR, SMA, EMA)
- **Who**: Automated (ohlc_aggregator.py)
- **Output**: `L2_technical.md` or JSON
- **Frequency**: Daily (via GitHub Actions)

### L3: AI Prediction
- **What**: Pure AI prediction based on L1+L2, no human intervention
- **Who**: Claude (using prompt from memo.md)
- **Output**: `L3_prediction.json`
- **Purpose**: Benchmark for measuring L4's value

### L4: HITL Decision
- **What**: Human + AI collaborative decision (the core of the system)
- **Who**: Human (mako) + AI (Claude Project with trading rules)
- **Output**: `L4_tradeplan.json`
- **Key Feature**: Tracks human interventions and reasoning

### L5: Review & Learning
- **What**: Post-trade review, pattern identification, rule refinement
- **Who**: Human (mako)
- **Output**: `L5_review.yaml`
- **Frequency**: Weekly

---

## 📊 System Components

### Implemented

- ✅ `src/fx_kline/core/ohlc_aggregator.py` - L2 technical analysis generation
- ✅ `src/fx_kline/core/l3_evaluator.py` - Prediction evaluation (L3 vs L4)
- ✅ `docs/memo.md` - L3 prediction prompt template
- ✅ Comprehensive documentation (this directory)

### To Be Implemented

**Phase 1 (Week 1-2)**:
- [ ] `docs/mako_trading_rules.md` - Personal trading rules
- [ ] Claude Project setup for L4
- [ ] L4_tradeplan.json schema validation

**Phase 2 (Week 3-4)**:
- [ ] `src/fx_kline/core/risk_manager.py` - Risk management module
- [ ] `src/fx_kline/core/trade_cost.py` - Cost calculation
- [ ] Economic calendar integration

**Phase 3 (Week 5-6)**:
- [ ] `src/fx_kline/core/backtest_simulator.py` - Historical simulation
- [ ] 30-day backtest execution
- [ ] Performance report generation

**Phase 4 (Week 7-8)**:
- [ ] `scripts/content_publisher.py` - X/Note automation
- [ ] Content templates
- [ ] First public posts

---

## 📈 Success Metrics

### Trading Performance

| Metric | Target (6 months) | Minimum Acceptable |
|--------|-------------------|---------------------|
| Win Rate | 60% | 55% |
| Profit Factor | 2.0 | 1.5 |
| Sharpe Ratio | 1.5 | 1.0 |
| Max Drawdown | -15% | -20% |
| Monthly Return | +5% | +3% |

### L3 vs L4 Comparison

| Metric | Expected Outcome |
|--------|------------------|
| Direction Accuracy | L4 > L3 by 10-15% |
| Sharpe Ratio | L4 > L3 by 30-50% |
| Max Drawdown | L4 < L3 by 20-30% |
| Skip Accuracy | L4 skip decisions: 80%+ correct |

### Content/Community

| Metric | 6 Months | 12 Months |
|--------|----------|-----------|
| X Followers | 600 | 1000+ |
| Note Subscribers | 50 | 100 |
| GitHub Stars | 300 | 500 |
| Monthly Content Revenue | ¥25,000 | ¥50,000 |

---

## 🤝 Contributing

This is primarily a personal trading system, but contributions are welcome for:

- **Bug fixes** in evaluation scripts
- **Documentation improvements**
- **Additional analysis tools**
- **Research collaborations** (see ACADEMIC_VALUE.md)

Please open an issue first to discuss proposed changes.

---

## 📞 Support & Contact

### Internal Resources
- All documentation in this `docs/` directory
- Code in `src/fx_kline/`
- Sample data in `data/` (anonymized)

### External Resources
- **Claude API**: https://console.anthropic.com
- **yfinance**: https://pypi.org/project/yfinance/
- **pandas-ta**: https://github.com/twopirllc/pandas-ta

### Community
- **GitHub Issues**: [Link to your repository issues]
- **X (Twitter)**: @[your-handle]
- **Note**: [your-note-url]

---

## ⚠️ Disclaimer

This system is for **educational and research purposes only**. It is NOT investment advice.

**Important**:
- Past performance does not guarantee future results
- Trading carries significant risk of loss
- Only trade with money you can afford to lose
- Always do your own research
- Consult a licensed financial advisor before trading

---

## 📚 Reading Order

### If you have 30 minutes:
1. This README (you are here)
2. HITL_SYSTEM_ADVICE.md - Section 1-3 (Risk Management)

### If you have 2 hours:
1. This README
2. HITL_SYSTEM_ADVICE.md (full)
3. IMPLEMENTATION_GUIDE.md - Phase 1

### If you want to implement:
1. All documentation in order:
   - HITL_SYSTEM_ADVICE.md
   - IMPLEMENTATION_GUIDE.md
   - memo.md
   - CONTENT_STRATEGY.md (if building audience)
   - ACADEMIC_VALUE.md (if doing research)

---

## 🎓 Learning Path

```
Start Here
    ↓
┌─────────────────────┐
│  README.md          │ ← You are here
│  (This document)    │
└─────────────────────┘
    ↓
┌─────────────────────┐
│ HITL_SYSTEM_        │
│ ADVICE.md           │
│ (Core trading       │
│  concepts)          │
└─────────────────────┘
    ↓
┌─────────────────────┐
│ IMPLEMENTATION_     │
│ GUIDE.md            │
│ (Step-by-step)      │
└─────────────────────┘
    ↓
┌───────────┬─────────┐
│  memo.md  │ CONTENT_│
│  (L3)     │ STRATEGY│
│           │ .md     │
└───────────┴─────────┘
         ↓
┌─────────────────────┐
│ ACADEMIC_VALUE.md   │
│ (Optional: Research)│
└─────────────────────┘
```

---

## 🔄 Version History

- **v1.0** (2025-11-28): Initial documentation release
  - Complete system architecture documentation
  - Implementation guide
  - Academic research framework
  - Content strategy

---

## 🌟 Key Insights from Professional Fund Manager

### Top 3 Critical Success Factors

1. **Risk Management > Everything Else**
   - 2% per trade rule is non-negotiable
   - Daily/weekly loss limits prevent catastrophic drawdown
   - Correlation risk must be monitored

2. **L4 (HITL) is the Core Value**
   - L3 is just a benchmark
   - Human intervention at specific moments (risk events, regime changes) is where edge comes from
   - Document every intervention for learning

3. **Transparency = Differentiation**
   - Showing failures builds more trust than showing only wins
   - Process > outcomes (in content strategy)
   - Open source + open data = academic credibility

### Top 3 Risks to Avoid

1. **Emotional Trading**
   - Revenge trading after losses
   - Overconfidence after wins
   - Solution: Hard rules, automated risk guards

2. **Over-optimization**
   - Tweaking rules after every trade
   - Curve-fitting to recent data
   - Solution: Only change rules after 30+ trade analysis

3. **Ignoring Costs**
   - Spreads eat into profits significantly
   - Poor timing (low liquidity hours) amplifies costs
   - Solution: Model all costs, avoid bad hours

---

## 💡 Quick Tips

### For Beginners
- Start with paper trading for at least 20 trades
- Focus on L4 (HITL) decision quality, not L3 accuracy
- Master risk management before worrying about entries

### For Intermediate
- Track intervention success rate (most important metric)
- Run historical simulations to validate rules
- Build content audience early (it takes time)

### For Advanced
- Consider academic publication (see ACADEMIC_VALUE.md)
- Collaborate with other researchers
- Open source your findings for maximum impact

---

## 🎯 Next Steps

**Right now** (5 minutes):
- Read the rest of this README
- Bookmark this docs/ directory

**Today** (1 hour):
- Read HITL_SYSTEM_ADVICE.md Sections 1-3
- Understand risk management basics

**This week** (5 hours):
- Complete HITL_SYSTEM_ADVICE.md
- Start IMPLEMENTATION_GUIDE.md Phase 1
- Create your mako_trading_rules.md

**This month** (20 hours):
- Complete Phase 1-2 of implementation
- Execute 10 paper trades
- Setup content publishing infrastructure

**Good luck, and trade responsibly! 🚀**

---

**Last Updated**: 2025-11-28
**Version**: 1.0
**Maintainer**: mako
**License**: MIT (code), CC BY 4.0 (documentation)
