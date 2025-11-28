# L3 Prediction Generation - Prompt Template

## 📋 Overview

This document contains the system prompt for generating **L3_prediction.json** from L1 (Fundamental Analysis) and L2 (Technical Analysis) reports.

**L3 is the AI-only baseline**: pure technical + fundamental integration without human intervention.

---

## 🎯 L3 Prediction Prompt

Use this prompt with Claude (Sonnet 4.5 recommended) to generate L3_prediction.json.

### System Prompt

```
You are an expert FX trading AI that integrates fundamental and technical analysis to generate trading predictions. Your role is to produce a **structured, quantitative prediction** based solely on the provided L1 and L2 reports, without human intervention.

**Your Output Format**:
You must output a valid JSON object with the following structure:

{
  "prediction": {
    "direction": "LONG" | "SHORT" | "WAIT",
    "pair": "USDJPY",
    "entry_price": 151.50,
    "stop_loss": 150.80,
    "target_price": 152.90,
    "confidence_score": 0.75,
    "confidence_breakdown": {
      "technical_alignment": 0.8,
      "trend_strength": 0.7,
      "support_resistance_proximity": 0.9,
      "fundamental_alignment": 0.6
    },
    "risk_reward_ratio": 2.0,
    "reasoning": "明確な理由を日本語で記述",
    "alternative_scenario": {
      "direction": "WAIT",
      "probability": 0.25,
      "reason": "レンジ相場の可能性も考慮"
    }
  },
  "metadata": {
    "generated_at": "2025-11-27T15:30:00+09:00",
    "model": "claude-sonnet-4.5",
    "schema_version": "1.0"
  }
}

**Key Guidelines**:

1. **Direction Decision**:
   - "LONG": Strong bullish setup (confidence > 0.65)
   - "SHORT": Strong bearish setup (confidence > 0.65)
   - "WAIT": Unclear or conflicting signals (confidence < 0.65)

2. **Confidence Score Calculation** (0.0-1.0):
   - Technical alignment: How many technical indicators agree (SMA ordering, EMA reactions, Support/Resistance proximity)
   - Trend strength: ADX > 25 → High, ADX < 20 → Low
   - Support/Resistance proximity: Price near key level → High
   - Fundamental alignment: L1 theme matches technical direction → High

   Final confidence = Weighted average:
   - Technical: 40%
   - Trend strength: 25%
   - SR proximity: 20%
   - Fundamental: 15%

3. **Entry Price**:
   - LONG: Slightly below current price (wait for pullback to nearest support)
   - SHORT: Slightly above current price (wait for bounce to nearest resistance)
   - Use 1h or 4h support/resistance from L2

4. **Stop Loss**:
   - LONG: Below nearest support - (ATR × 0.5)
   - SHORT: Above nearest resistance + (ATR × 0.5)
   - Never risk more than 2% of account

5. **Target Price**:
   - Must achieve Risk:Reward ≥ 2:1
   - Use next major resistance (LONG) or support (SHORT) from L2

6. **Reasoning**:
   - Write in Japanese
   - Concise (2-3 sentences)
   - Explain the PRIMARY reason for the decision
   - Mention key support/resistance levels

7. **Alternative Scenario**:
   - Always provide a second-best scenario
   - Estimate probability (must sum to 1.0 with main prediction)
   - Useful for risk management

**IMPORTANT**:
- Do NOT consider human preferences, risk tolerance, or trading style
- This is a PURE AI prediction based solely on L1+L2 data
- Be conservative with confidence scores (avoid overconfidence)
- If L1 and L2 contradict, reduce confidence and lean toward WAIT
```

---

## 📝 Example Usage

### Input: L1 + L2 Reports

**L1 Fundamental (Summary)**:
```
市場テーマ: ドル高継続
- FRBハト派姿勢後退（インフレ再燃懸念）
- 日銀は追加利上げに慎重姿勢
- 米雇用統計は明日22:30発表（高リスク）
```

**L2 Technical (Summary for USDJPY)**:
```
1d: Trend=UP, SMA ordering=bullish, EMA25 support bounce
    Support: [151.50, 150.80], Resistance: [153.20, 154.50]
    RSI=58, ATR=1.20

4h: Trend=UP, SMA ordering=bullish
    Support: [151.80, 151.50], Resistance: [152.90, 153.20]
    RSI=62, ATR=0.45

1h: Trend=UP, SMA ordering=bullish
    Support: [152.10, 151.90], Resistance: [152.70, 153.00]
    RSI=65, ATR=0.25
```

### User Prompt to Claude

```
以下のL1とL2レポートに基づいて、L3_prediction.jsonを生成してください。

# L1 Fundamental Analysis
[L1ファイルの内容を貼り付け]

# L2 Technical Analysis
[L2ファイルの内容を貼り付け]

上記のシステムプロンプトに従い、JSON形式で予測を出力してください。
現在価格: USDJPY 152.30
```

### Expected Output (L3_prediction.json)

```json
{
  "prediction": {
    "direction": "WAIT",
    "pair": "USDJPY",
    "entry_price": null,
    "stop_loss": null,
    "target_price": null,
    "confidence_score": 0.45,
    "confidence_breakdown": {
      "technical_alignment": 0.85,
      "trend_strength": 0.75,
      "support_resistance_proximity": 0.60,
      "fundamental_alignment": 0.70
    },
    "risk_reward_ratio": null,
    "reasoning": "テクニカルは強い上昇トレンドを示唆するが、明日の米雇用統計（高インパクトイベント）を24時間以内に控えており、現時点でのエントリーはリスクが高い。指標発表後の反応を見てから判断すべき。",
    "alternative_scenario": {
      "direction": "LONG",
      "probability": 0.55,
      "reason": "雇用統計が予想通りなら、151.50サポートからのロング検討"
    }
  },
  "metadata": {
    "generated_at": "2025-11-27T15:30:00+09:00",
    "model": "claude-sonnet-4.5",
    "schema_version": "1.0"
  }
}
```

**Analysis of this example**:
- ✅ Technical indicators are bullish (alignment=0.85)
- ✅ Fundamental theme supports USD (alignment=0.70)
- ❌ BUT: High-impact event within 24 hours
- **Result**: WAIT decision with low confidence (0.45)
- **Alternative**: LONG after event (probability 0.55)

This demonstrates **conservative AI judgment** when risks are present.

---

## 🎛️ Confidence Score Calibration Guidelines

To ensure AI confidence matches actual prediction accuracy:

### High Confidence (0.75-0.90)

**Conditions**:
- ✅ All timeframes (1h, 4h, 1d) show same trend
- ✅ Price near strong support/resistance
- ✅ Fundamental theme aligns with technical direction
- ✅ No high-impact events within 48 hours
- ✅ Market regime is TRENDING (ADX > 25)

**Example**: Clear uptrend + bullish fundamentals + support bounce

### Medium Confidence (0.55-0.75)

**Conditions**:
- ⚠️ Most timeframes align, but 1 contradicts
- ⚠️ Support/resistance less clear
- ⚠️ Fundamental theme is neutral
- ⚠️ Market regime is mixed

**Example**: Daily uptrend, but 1h showing short-term weakness

### Low Confidence (0.35-0.55)

**Conditions**:
- ❌ Timeframes show conflicting signals
- ❌ Price in middle of range (no clear support/resistance)
- ❌ Fundamental theme unclear or mixed
- ❌ Market regime is CHOPPY

**Example**: Daily up, 4h down, 1h sideways

### Very Low Confidence (0.00-0.35)

**Conditions**:
- ❌ Highly conflicting signals across all dimensions
- ❌ High-impact event imminent
- ❌ Extreme volatility (ATR >> historical average)

**Recommendation**: Always output WAIT for confidence < 0.50

---

## 🔧 Adjusting Prompt for Specific Needs

### For More Aggressive Predictions

Modify confidence threshold:
```
"LONG" / "SHORT": confidence > 0.55 (instead of 0.65)
"WAIT": confidence < 0.55 (instead of 0.65)
```

### For More Conservative Predictions

Add additional filters:
```
- Require risk:reward ≥ 3:1 (instead of 2:1)
- Never trade within 48 hours of high-impact events (instead of 24)
- Require ADX > 30 for TRENDING confirmation (instead of 25)
```

### For Specific Currency Pairs

Add pair-specific rules:
```
USDJPY:
  - Extra weight on BoJ/Fed policy divergence
  - Respect 150.00, 152.00, 155.00 as psychological levels

EURUSD:
  - Extra weight on ECB/Fed policy
  - Respect 1.0500, 1.1000 as major levels

XAUUSD (Gold):
  - Extra weight on real yields, geopolitical risk
  - Highly sensitive to risk-off events
```

---

## 🧪 Testing and Validation

### 1. Prompt Testing Checklist

Before using in production:

- [ ] Test with bullish L1 + bullish L2 → Should output LONG
- [ ] Test with bearish L1 + bearish L2 → Should output SHORT
- [ ] Test with bullish L1 + bearish L2 → Should output WAIT (conflict)
- [ ] Test with event proximity flag → Should output WAIT
- [ ] Test confidence score calculation → Should match guidelines
- [ ] Validate JSON schema → Must be valid JSON

### 2. Confidence Calibration Check

After collecting 30+ predictions:

```python
import pandas as pd
import matplotlib.pyplot as plt

# Load evaluation results
df = pd.read_json("evaluations/all_l3_results.json")

# Create calibration plot
df['confidence_bin'] = pd.cut(df['confidence_score'], bins=[0, 0.5, 0.7, 0.9, 1.0])
calibration = df.groupby('confidence_bin')['direction_correct'].mean()

# Expected: confidence_bin should match accuracy
# E.g., 0.7-0.9 bin should have ~80% accuracy
print(calibration)
```

**Expected Result**:
```
confidence_bin
(0.0, 0.5]     0.45  # Slightly under-confident (good)
(0.5, 0.7]     0.62  # Well-calibrated
(0.7, 0.9]     0.78  # Well-calibrated
(0.9, 1.0]     0.85  # Slightly over-confident
```

If AI is consistently over/under-confident, adjust the confidence formula weights.

---

## 📊 Integration with l3_evaluator.py

The generated **L3_prediction.json** is designed to work seamlessly with the evaluation script:

```bash
# Generate L3 prediction
# (Use Claude with the prompt above)

# Next day: Evaluate against actual outcome
python -m fx_kline.core.l3_evaluator \
  --mode ai \
  --prediction data/2025-11-27/L3_prediction.json \
  --actual data/2025-11-28/ohlc_summary.json \
  --output data/2025-11-27/L4_ai_evaluation.json \
  --market-regime TRENDING

# View results
cat data/2025-11-27/L4_ai_evaluation.json
```

The evaluator will automatically:
- ✅ Check direction accuracy
- ✅ Calculate entry timing score
- ✅ Compute realized pips (if trade executed)
- ✅ Measure confidence calibration error
- ✅ Categorize by market regime

---

## 🚀 Automation Workflow

For daily automation:

```bash
#!/bin/bash
# daily_l3_generation.sh

DATE=$(date +%Y-%m-%d)
DATA_DIR="data/${DATE}"

# 1. Fetch OHLC data (already automated via GitHub Actions)
# 2. Generate L2 technical analysis (ohlc_aggregator.py)
# 3. Manually create L1 fundamental analysis (mako's responsibility)

# 4. Generate L3 prediction via Claude API
claude_api_call.py \
  --l1 "${DATA_DIR}/L1_fundamental.md" \
  --l2 "${DATA_DIR}/L2_technical.md" \
  --output "${DATA_DIR}/L3_prediction.json" \
  --prompt docs/memo.md

# 5. (Next day) Evaluate L3 prediction
# This runs automatically the next day via cron
```

---

## 🎓 Learning and Improvement

### Feedback Loop

Every week, review L3 performance:

1. **Identify Failure Patterns**:
   - Where did L3 predictions go wrong?
   - Was it over-confidence in CHOPPY markets?
   - Did it miss fundamental risks?

2. **Refine Prompt**:
   - Add specific rules for failure patterns
   - Adjust confidence calculation weights
   - Update risk filters

3. **Re-test**:
   - Run updated prompt on past 30 days
   - Compare new predictions vs old
   - Validate improvement in calibration

### Example Refinement

**Week 1 Finding**: L3 has 65% accuracy in TRENDING, but only 40% in CHOPPY
**Action**: Add rule: "If market_regime=CHOPPY from L2, set confidence *= 0.7"

**Week 2 Finding**: L3 over-confident (avg confidence 0.75, actual accuracy 0.60)
**Action**: Recalibrate confidence formula weights, reduce fundamental_weight from 15% to 10%

---

## 📚 Reference

### Related Documents

- `HITL_SYSTEM_ADVICE.md`: Overall system design and risk management
- `ACADEMIC_VALUE.md`: Research methodology and statistical rigor
- `l3_evaluator.py`: Evaluation script source code

### Version History

- **v1.0** (2025-11-28): Initial prompt template
- Future: Will be updated based on empirical performance data

---

**Last Updated**: 2025-11-28
**Maintainer**: mako
**Status**: Production-ready
