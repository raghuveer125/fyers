# Parameter Sweep Tab - Quick Start Guide

## 🎯 Quick Access

**URL**: http://localhost:5050  
**Tab**: Click "📊 Parameter Sweep" button

## 📊 UI Layout

```
┌─────────────────────────────────────────────────────────────┐
│  Backtesting Studio                                         │
├─────────────────────────────────────────────────────────────┤
│  [🎬 Live Simulator]  [📊 Parameter Sweep]  ← Switch tabs   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ⚙️  MACD Parameter Sweep                                   │
│                                                             │
│  Symbol: [BSE:RELIANCE-A ▼]                                │
│  Timeframe: [1h ▼]                                          │
│                                                             │
│  ┌─ ⚡ Fast Period Range ─────────────────────────────────┐ │
│  │  Start: [8____]  End: [24____]  Range: 17 values       │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌─ 📈 Slow Period Range ─────────────────────────────────┐ │
│  │  Start: [18____]  End: [52____]  Range: 35 values      │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌─ 📊 Signal Period Range ────────────────────────────────┐ │
│  │  Start: [5___]  End: [12____]  Range: 8 values         │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                             │
│  💰 Initial Capital: [100000________]                      │
│                                                             │
│  Total Combinations: 4,760                                 │
│                                                             │
│  [🚀 Run Parameter Sweep]  ← Click to start                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## ⏳ What Happens When You Click "Run"

### Phase 1: Initialization (5 seconds)
```
Running Sweep...
████░░░░░░░░░░░░░░░░░░░░░░  50%
Initializing...
```

### Phase 2: Processing (30-60 seconds)
- Tests all 4,760 combinations
- Evaluates each against full candle history
- Calculates P&L and metrics
- Progress bar fills to 100%

### Phase 3: Results Display (Instant)
```
✅ Sweep Complete!

┌─────────────┬─────────────┐
│ Best P&L    │ Worst P&L   │
│ +₹53.70     │ -₹196.90    │
│ (Fast=23)   │ (Fast=8)    │
└─────────────┴─────────────┘

🏆 Top 5 Performers

| Fast | Slow | Signal | P&L    | Win Rate | Trades |
|------|------|--------|--------|----------|--------|
| 23   | 19   | 5      | +53.70 | 70.78%   | 397    |
| 24   | 22   | 5      | +52.25 | 70.08%   | 371    |
| 23   | 18   | 5      | +51.55 | 69.98%   | 403    |
| ...  | ...  | ...    | ...    | ...      | ...    |

[📈 View Detailed Report]  [🔄 New Sweep]
```

## 📥 Output Files

After running a sweep, two files are generated:

### 1. CSV Report (sortable in Excel)
```
📁 fyers/backtesting/reports/
└─ macd_sweep_BSE_RELIANCE-A_1h.csv

Columns:
- fast_period, slow_period, signal_period
- total_pnl, total_pnl_percent
- win_rate, total_trades, winning_trades
- losing_trades, avg_pnl, max_drawdown
- final_equity, return_percent
```

### 2. Consolidated HTML Report (view in browser)
```
📁 fyers/backtesting/reports/
└─ macd_sweep_consolidated_report.html

Contains:
- Executive summary (Best/Worst configs)
- Top 10 & Bottom 10 performers
- Key insights & patterns
- Detailed recommendations
- Interactive tables
```

## 🔄 Workflow Example

### Iteration 1: Broad Sweep
```
Fast: 8-24    → 17 combos
Slow: 18-52   → 35 combos  
Signal: 5-12  → 8 combos
━━━━━━━━━━━━━━━━━━━━━━━━━━
Total: 4,760 combinations ✓

Result: Best = Fast=23, Slow=19, Signal=5
```

### Iteration 2: Fine-tuning (Optional)
```
Fast: 21-25   → 5 combos
Slow: 17-21   → 5 combos
Signal: 4-6   → 3 combos
━━━━━━━━━━━━━━━━━━━━━━━━━━
Total: 75 combinations (faster!)

Result: Best = Fast=24, Slow=20, Signal=5
```

## 💡 Tips & Tricks

### Faster Sweeps
- Use smaller ranges: `Fast 20-24` (5 values) instead of `8-24` (17 values)
- For coarse tuning: just adjust one parameter at a time

### Better Results
- Test on different timeframes (1m, 5m, 1h, 1d)
- Test on different symbols
- Compare MACD with RSI and RSI+MACD strategies

### Export for Analysis
- Download CSV reports to Excel
- Create pivot tables
- Build charts of P&L vs parameters
- Identify clusters of profitable configs

## ❌ Common Issues & Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| "No candles found" | No data in DB | Start `./start_fyers.sh` or `./start_binance.sh` |
| Very slow execution | Too many combos | Reduce range (e.g., 8-20 instead of 8-52) |
| Connection refused | API not running | Run `python -m fyers.backtesting.api` |
| Blank sweep tab | JavaScript error | Check browser console (F12) |

## 📞 Support

For issues, check:
1. API logs: `python -m fyers.backtesting.api` (verbose output)
2. Browser console: Press `F12` → Console tab
3. Database: Verify candles exist: `SELECT COUNT(*) FROM candles;`
4. PostgreSQL: Ensure running on localhost:5432

---

**Status**: Ready to use! 🎯  
**Version**: 1.0  
**Date**: 17 January 2026
