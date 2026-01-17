# Backtesting Studio Integration - Implementation Summary

## Overview

The parameter sweep functionality has been successfully integrated with the simulator UI at **localhost:5050** with a new **"Parameter Sweep"** tab.

## 🎯 What's New

### 1. **New API Endpoint**
- **Endpoint**: `POST /backtest/macd-sweep`
- **Port**: 5050
- **Location**: [fyers/backtesting/api.py](fyers/backtesting/api.py#L215)

**Request Parameters:**
```json
{
  "symbol": "BSE:RELIANCE-A",
  "timeframe": "1h",
  "fast_start": 8,
  "fast_end": 24,
  "slow_start": 18,
  "slow_end": 52,
  "signal_start": 5,
  "signal_end": 12,
  "initial_capital": 100000.0
}
```

**Response:**
```json
{
  "status": "ok",
  "total_combinations": 4760,
  "csv_report": "/report/macd_sweep_BSE_RELIANCE-A_1h.csv",
  "best_3": [...],
  "worst_3": [...],
  "all_results": [...]
}
```

### 2. **Updated Web UI at localhost:5050**

The simulator UI now has **two tabs**:

#### Tab 1: 🎬 Live Simulator
- Single strategy backtesting with candle-by-candle step-through
- Real-time charts (Plotly)
- Equity curve tracking
- Entry/exit logging
- Auto-play functionality

#### Tab 2: 📊 Parameter Sweep (NEW)
- **Select Symbol**: BSE:RELIANCE-A
- **Select Timeframe**: 1m, 5m, 15m, 30m, 1h, 1D
- **Configure Ranges**:
  - Fast Period (e.g., 8-24)
  - Slow Period (e.g., 18-52)
  - Signal Period (e.g., 5-12)
- **Live Counter**: Shows total combinations to test
- **Initial Capital**: Configurable
- **Run Button**: Single-click sweep execution

### 3. **Sweep Results Display**

After running a sweep, the UI shows:
- 📊 **Best P&L**: Highest performing configuration with metrics
- 📉 **Worst P&L**: Lowest performing configuration
- 🏆 **Top 5 Performers**: Table with Fast/Slow/Signal parameters and metrics
- 📈 **Detailed Report Link**: Opens full HTML report with all 4,760+ results
- 🔄 **New Sweep Button**: Run another sweep without reloading

## 🚀 How to Use

### Starting the Service

```bash
cd /Users/bhoomidakshpc/project1/StockAutoTradingVR/Fyers

# Activate environment (if not already done)
source .venv/bin/activate

# Start the API on port 5050
python -m fyers.backtesting.api
```

### Accessing the UI

1. Open **http://localhost:5050** in your browser
2. Click the **"📊 Parameter Sweep"** tab
3. Configure your parameter ranges
4. Click **"🚀 Run Parameter Sweep"**
5. Wait for results (30-60 seconds depending on combination count)
6. Review results and click **"📈 View Detailed Report"** for full analysis

## 📊 Features

### Dynamic Parameter Range Updates
- Change Fast, Slow, or Signal ranges
- Total combinations count updates in real-time
- Example: Fast (8-24) × Slow (18-52) × Signal (5-12) = **4,760 combinations**

### Progressive Results
- Best 3 configurations highlighted
- Worst 3 configurations shown
- Top 5 performers in sortable table
- All results available in CSV for external analysis

### Performance Metrics Displayed
- **P&L**: Absolute profit/loss (₹)
- **Win Rate**: Percentage of profitable trades
- **Trade Count**: Number of trades executed
- **Max Drawdown**: Worst peak-to-trough decline
- **Return %**: Total return on capital

## 📁 Generated Files

Each sweep generates:
1. **CSV Report**: `fyers/backtesting/reports/macd_sweep_SYMBOL_TIMEFRAME.csv`
   - All 4,760+ parameter combinations with metrics
   - Sortable in Excel/Google Sheets
   - Format: Fast, Slow, Signal, P&L, Win Rate, Trades, etc.

2. **Consolidated HTML Report**: `fyers/backtesting/reports/macd_sweep_consolidated_report.html`
   - Professional visual report
   - Best/worst performers highlighted
   - Detailed insights and recommendations
   - View directly in browser

## 🔧 Customization

### Change Default Ranges
In the **Parameter Sweep** tab, modify:
- **Fast Start/End** (default: 8-24)
- **Slow Start/End** (default: 18-52)
- **Signal Start/End** (default: 5-12)

### Support Other Strategies
To add RSI or RSI+MACD sweeps:
1. Create similar endpoints: `POST /backtest/rsi-sweep`, `POST /backtest/rsi-macd-sweep`
2. Follow the same pattern as `macd_sweep_request` model
3. Add corresponding UI tab

### Change Initial Capital
Default: ₹100,000
- Adjust in the **"Initial Capital"** input field before running sweep

## 🎬 Usage Example Workflow

```
1. Start API
   python -m fyers.backtesting.api

2. Open http://localhost:5050

3. Switch to "Parameter Sweep" tab

4. Configure:
   - Symbol: BSE:RELIANCE-A
   - Timeframe: 1h
   - Fast: 8-24
   - Slow: 18-52
   - Signal: 5-12
   - Capital: 100000

5. Click "Run Parameter Sweep"

6. Wait for completion (~45 seconds for 4,760 combos)

7. View best config: Fast=23, Slow=19, Signal=5 (P&L: +₹53.70)

8. Click "View Detailed Report" for full analysis

9. Download CSV for custom analysis
```

## 🐛 Troubleshooting

### "No candles found for {symbol} {timeframe}"
- **Cause**: No data in PostgreSQL for that symbol/timeframe
- **Solution**: Start Fyers/Binance streams first to populate candles
  ```bash
  ./start_fyers.sh
  ./start_binance.sh
  ```

### Sweep is slow
- **Cause**: Large parameter ranges (fast 50 combos × slow 50 × signal 50 = 125,000 runs)
- **Solution**: Reduce ranges (fast 8-24 = 17 values is reasonable)

### "Port 5050 already in use"
- **Cause**: Another process using port 5050
- **Solution**: Kill the process or restart your terminal

## 📞 Architecture Notes

- **Backend**: FastAPI (Python)
- **Frontend**: Vanilla JavaScript + Plotly.js for charts
- **Data**: PostgreSQL (localhost:5432, trader/trader123/fyers)
- **Message Queue**: Kafka (for real-time streams)
- **Threading**: Single-threaded sweep (CPU-intensive, no async needed)

## ✅ Files Modified/Created

1. **[fyers/backtesting/api.py](fyers/backtesting/api.py)**
   - Added `MACDSweepRequest` model
   - Added `POST /backtest/macd-sweep` endpoint
   - Updated `/simulator-ui` HTML with:
     - Tab navigation
     - Parameter sweep section
     - Results display
     - JavaScript for sweep logic

2. **[fyers/backtesting/ui_sweep_tab.py](fyers/backtesting/ui_sweep_tab.py)**
   - Utility file with HTML/CSS reference (optional)

## 🎓 Next Steps

1. **Run your first sweep** at localhost:5050
2. **Analyze results** in the consolidated report
3. **Extract best parameters** and deploy for live trading
4. **Extend to RSI/RSI+MACD** by following the MACD pattern
5. **Optimize further** with more granular parameter ranges on best performers

---

**Status**: ✅ Ready for use
**Last Updated**: 17 January 2026
