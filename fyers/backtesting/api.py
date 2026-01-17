from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from typing import Optional
import os
import uuid

from .engine import BacktestEngine
from .strategies import RSIStrategy, MACDStrategy, RSIMACDStrategy
from .strategies.rsi import RSIConfig
from .strategies.macd import MACDConfig
from .dashboard import generate_dashboard
from .simulator import LiveSimulator

app = FastAPI(
    title="Backtesting Service",
    description="API for backtesting trading strategies",
    version="1.0.0"
)

engine = BacktestEngine()
simulator = LiveSimulator()

REPORTS_DIR = os.path.join(os.path.dirname(__file__), "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)


class RSIBacktestRequest(BaseModel):
    symbol: str = "BSE:RELIANCE-A"
    timeframe: str = "1h"
    period: int = 14
    overbought: float = 70.0
    oversold: float = 30.0
    initial_capital: float = 100000.0
    quantity: int = 1
    start_timestamp: Optional[int] = None
    end_timestamp: Optional[int] = None


class MACDBacktestRequest(BaseModel):
    symbol: str = "BSE:RELIANCE-A"
    timeframe: str = "1h"
    fast_period: int = 12
    slow_period: int = 26
    signal_period: int = 9
    initial_capital: float = 100000.0
    quantity: int = 1
    start_timestamp: Optional[int] = None
    end_timestamp: Optional[int] = None


class RSIMACDBacktestRequest(BaseModel):
    symbol: str = "BSE:RELIANCE-A"
    timeframe: str = "1h"
    rsi_period: int = 14
    rsi_overbought: float = 70.0
    rsi_oversold: float = 30.0
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9
    initial_capital: float = 100000.0
    quantity: int = 1
    start_timestamp: Optional[int] = None
    end_timestamp: Optional[int] = None


@app.get("/")
def root():
    return {
        "service": "Backtesting API",
        "version": "1.0.0",
        "endpoints": {
            "/data": "GET - List available candle data",
            "/backtest/rsi": "POST - Run RSI strategy backtest",
            "/backtest/macd": "POST - Run MACD strategy backtest",
            "/backtest/rsi-macd": "POST - Run RSI+MACD strategy backtest",
            "/report/{filename}": "GET - View generated HTML report"
        }
    }


@app.get("/data")
def get_available_data():
    try:
        data = engine.get_available_data()
        return {"status": "ok", "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/backtest/rsi")
def backtest_rsi(request: RSIBacktestRequest):
    try:
        config = RSIConfig(
            period=request.period,
            overbought=request.overbought,
            oversold=request.oversold
        )
        strategy = RSIStrategy(config=config, initial_capital=request.initial_capital)

        result = engine.run(
            strategy=strategy,
            symbol=request.symbol,
            timeframe=request.timeframe,
            start_timestamp=request.start_timestamp,
            end_timestamp=request.end_timestamp,
            quantity=request.quantity
        )

        report_name = f"rsi_{request.symbol.replace(':', '_')}_{request.timeframe}.html"
        report_path = os.path.join(REPORTS_DIR, report_name)
        generate_dashboard(result, report_path)

        return {
            "status": "ok",
            "strategy_config": result.strategy_config,
            "metrics": result.metrics,
            "trades_count": len(result.trades),
            "trades": result.trades[:20],
            "report_url": f"/report/{report_name}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/backtest/macd")
def backtest_macd(request: MACDBacktestRequest):
    try:
        config = MACDConfig(
            fast_period=request.fast_period,
            slow_period=request.slow_period,
            signal_period=request.signal_period
        )
        strategy = MACDStrategy(config=config, initial_capital=request.initial_capital)

        result = engine.run(
            strategy=strategy,
            symbol=request.symbol,
            timeframe=request.timeframe,
            start_timestamp=request.start_timestamp,
            end_timestamp=request.end_timestamp,
            quantity=request.quantity
        )

        report_name = f"macd_{request.symbol.replace(':', '_')}_{request.timeframe}.html"
        report_path = os.path.join(REPORTS_DIR, report_name)
        generate_dashboard(result, report_path)

        return {
            "status": "ok",
            "strategy_config": result.strategy_config,
            "metrics": result.metrics,
            "trades_count": len(result.trades),
            "trades": result.trades[:20],
            "report_url": f"/report/{report_name}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/backtest/rsi-macd")
def backtest_rsi_macd(request: RSIMACDBacktestRequest):
    try:
        rsi_config = RSIConfig(
            period=request.rsi_period,
            overbought=request.rsi_overbought,
            oversold=request.rsi_oversold
        )
        macd_config = MACDConfig(
            fast_period=request.macd_fast,
            slow_period=request.macd_slow,
            signal_period=request.macd_signal
        )
        strategy = RSIMACDStrategy(
            rsi_config=rsi_config,
            macd_config=macd_config,
            initial_capital=request.initial_capital
        )

        result = engine.run(
            strategy=strategy,
            symbol=request.symbol,
            timeframe=request.timeframe,
            start_timestamp=request.start_timestamp,
            end_timestamp=request.end_timestamp,
            quantity=request.quantity
        )

        report_name = f"rsi_macd_{request.symbol.replace(':', '_')}_{request.timeframe}.html"
        report_path = os.path.join(REPORTS_DIR, report_name)
        generate_dashboard(result, report_path)

        return {
            "status": "ok",
            "strategy_config": result.strategy_config,
            "metrics": result.metrics,
            "trades_count": len(result.trades),
            "trades": result.trades[:20],
            "report_url": f"/report/{report_name}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/report/{filename}")
def get_report(filename: str):
    if not filename.endswith(".html"):
        raise HTTPException(status_code=400, detail="Invalid file type")

    filepath = os.path.join(REPORTS_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Report not found")

    return FileResponse(filepath, media_type="text/html")


class SimulatorRequest(BaseModel):
    symbol: str = "BSE:RELIANCE-A"
    timeframe: str = "1h"
    strategy: str = "RSI"
    initial_capital: float = 100000.0
    rsi_period: int = 14
    rsi_overbought: float = 70.0
    rsi_oversold: float = 30.0
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9


@app.post("/simulator/create")
def create_simulator(request: SimulatorRequest):
    try:
        session_id = str(uuid.uuid4())[:8]

        strategy_params = {
            "period": request.rsi_period,
            "overbought": request.rsi_overbought,
            "oversold": request.rsi_oversold,
            "rsi_period": request.rsi_period,
            "rsi_overbought": request.rsi_overbought,
            "rsi_oversold": request.rsi_oversold,
            "fast_period": request.macd_fast,
            "slow_period": request.macd_slow,
            "signal_period": request.macd_signal,
            "macd_fast": request.macd_fast,
            "macd_slow": request.macd_slow,
            "macd_signal": request.macd_signal
        }

        result = simulator.create_session(
            session_id=session_id,
            symbol=request.symbol,
            timeframe=request.timeframe,
            strategy_type=request.strategy,
            strategy_params=strategy_params,
            initial_capital=request.initial_capital
        )

        return {"status": "ok", **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/simulator/{session_id}/step")
def simulator_step(session_id: str):
    try:
        result = simulator.step(session_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/simulator/{session_id}")
def get_simulator_state(session_id: str):
    try:
        result = simulator.get_state(session_id)
        return {"status": "ok", **result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/simulator/{session_id}/reset")
def reset_simulator(session_id: str):
    try:
        result = simulator.reset(session_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/simulator/{session_id}")
def delete_simulator(session_id: str):
    try:
        simulator.delete_session(session_id)
        return {"status": "ok", "message": "Session deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class MACDSweepRequest(BaseModel):
    symbol: str = "BSE:RELIANCE-A"
    timeframe: str = "1h"
    fast_start: int = 8
    fast_end: int = 24
    slow_start: int = 18
    slow_end: int = 52
    signal_start: int = 5
    signal_end: int = 12
    initial_capital: float = 100000.0


@app.post("/backtest/macd-sweep")
def backtest_macd_sweep(request: MACDSweepRequest):
    try:
        import csv
        from .strategies import Candle
        
        results = []
        candle_data = engine.get_candles(request.symbol, request.timeframe)
        
        if not candle_data:
            raise ValueError(f"No candles found for {request.symbol} {request.timeframe}")
        
        candles = [
            Candle(
                timestamp=row["timestamp"],
                datetime=str(row["datetime"]),
                open=row["open"],
                high=row["high"],
                low=row["low"],
                close=row["close"],
                volume=row["volume"],
            )
            for row in candle_data
        ]
        
        total_combinations = (request.fast_end - request.fast_start + 1) * \
                           (request.slow_end - request.slow_start + 1) * \
                           (request.signal_end - request.signal_start + 1)
        
        processed = 0
        
        for fast in range(request.fast_start, request.fast_end + 1):
            for slow in range(request.slow_start, request.slow_end + 1):
                for signal in range(request.signal_start, request.signal_end + 1):
                    config = MACDConfig(fast_period=fast, slow_period=slow, signal_period=signal)
                    strategy = MACDStrategy(config=config, initial_capital=request.initial_capital)
                    strategy.reset()
                    
                    for candle in candles:
                        sig = strategy.on_candle(candle)
                        strategy.process_signal(sig, candle, quantity=1)
                    
                    metrics = strategy.get_metrics()
                    results.append({
                        "fast_period": fast,
                        "slow_period": slow,
                        "signal_period": signal,
                        **metrics,
                    })
                    
                    processed += 1
        
        # Sort by total_pnl ascending
        results.sort(key=lambda r: r["total_pnl"])
        
        # Save CSV
        csv_report_name = f"macd_sweep_{request.symbol.replace(':', '_')}_{request.timeframe}.csv"
        csv_report_path = os.path.join(REPORTS_DIR, csv_report_name)
        
        fieldnames = [
            "fast_period", "slow_period", "signal_period",
            "total_pnl", "total_pnl_percent", "win_rate", "total_trades",
            "winning_trades", "losing_trades", "avg_pnl", "max_drawdown",
            "final_equity", "return_percent"
        ]
        
        with open(csv_report_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        
        # Generate consolidated HTML report
        html_report_name = f"macd_sweep_{request.symbol.replace(':', '_')}_{request.timeframe}_report.html"
        html_report_path = os.path.join(REPORTS_DIR, html_report_name)
        
        best_3 = results[-3:][::-1]
        worst_3 = results[:3]
        
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>MACD Parameter Sweep Report</title>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0d1117; color: #c9d1d9; padding: 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        h1, h2 {{ color: #58a6ff; }}
        .metric {{ background: #161b22; padding: 15px; border-radius: 8px; margin: 10px 0; border-left: 3px solid #58a6ff; }}
        .positive {{ color: #3fb950; }}
        .negative {{ color: #f85149; }}
        table {{ width: 100%; border-collapse: collapse; background: #161b22; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #30363d; }}
        th {{ background: #21262d; color: #8b949e; }}
        .best {{ background: #161b22; border-left: 3px solid #3fb950; }}
        .worst {{ background: #161b22; border-left: 3px solid #f85149; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 MACD Parameter Sweep Report</h1>
        <h2>{request.symbol} | {request.timeframe} | {len(results)} Combinations</h2>
        
        <div class="metric best">
            <strong>🏆 Best Configuration</strong><br>
            Fast={best_3[0]['fast_period']}, Slow={best_3[0]['slow_period']}, Signal={best_3[0]['signal_period']}<br>
            <span class="positive">P&L: ₹{best_3[0]['total_pnl']:.2f}</span> | Win Rate: {best_3[0]['win_rate']:.1f}% | Trades: {best_3[0]['total_trades']}
        </div>
        
        <div class="metric worst">
            <strong>📉 Worst Configuration</strong><br>
            Fast={worst_3[0]['fast_period']}, Slow={worst_3[0]['slow_period']}, Signal={worst_3[0]['signal_period']}<br>
            <span class="negative">P&L: ₹{worst_3[0]['total_pnl']:.2f}</span> | Win Rate: {worst_3[0]['win_rate']:.1f}% | Trades: {worst_3[0]['total_trades']}
        </div>
        
        <h3>🏅 Top 10 Performers</h3>
        <table>
            <thead>
                <tr>
                    <th>Fast</th>
                    <th>Slow</th>
                    <th>Signal</th>
                    <th>P&L</th>
                    <th>Return %</th>
                    <th>Win Rate</th>
                    <th>Trades</th>
                    <th>Max DD</th>
                </tr>
            </thead>
            <tbody>
"""
        
        for i, row in enumerate(best_3[:10]):
            pnl_class = "positive" if row['total_pnl'] >= 0 else "negative"
            html_content += f"""                <tr>
                    <td>{row['fast_period']}</td>
                    <td>{row['slow_period']}</td>
                    <td>{row['signal_period']}</td>
                    <td class="{pnl_class}">₹{row['total_pnl']:.2f}</td>
                    <td>{row.get('return_percent', 0):.2f}%</td>
                    <td>{row['win_rate']:.1f}%</td>
                    <td>{row['total_trades']}</td>
                    <td>{row.get('max_drawdown', 0):.2f}</td>
                </tr>
"""
        
        html_content += """            </tbody>
        </table>
        
        <h3>📉 Bottom 10 Performers</h3>
        <table>
            <thead>
                <tr>
                    <th>Fast</th>
                    <th>Slow</th>
                    <th>Signal</th>
                    <th>P&L</th>
                    <th>Return %</th>
                    <th>Win Rate</th>
                    <th>Trades</th>
                    <th>Max DD</th>
                </tr>
            </thead>
            <tbody>
"""
        
        for row in worst_3[:10]:
            pnl_class = "positive" if row['total_pnl'] >= 0 else "negative"
            html_content += f"""                <tr>
                    <td>{row['fast_period']}</td>
                    <td>{row['slow_period']}</td>
                    <td>{row['signal_period']}</td>
                    <td class="{pnl_class}">₹{row['total_pnl']:.2f}</td>
                    <td>{row.get('return_percent', 0):.2f}%</td>
                    <td>{row['win_rate']:.1f}%</td>
                    <td>{row['total_trades']}</td>
                    <td>{row.get('max_drawdown', 0):.2f}</td>
                </tr>
"""
        
        html_content += """            </tbody>
        </table>
        
        <p style="color: #8b949e; margin-top: 30px; font-size: 12px;">
            Report generated on 17 January 2026 | Total Combinations: """ + str(total_combinations) + """ | Data: """ + request.symbol + """ """ + request.timeframe + """
        </p>
    </div>
</body>
</html>"""
        
        with open(html_report_path, 'w') as f:
            f.write(html_content)
        
        return {
            "status": "ok",
            "total_combinations": total_combinations,
            "csv_report": f"/report/{csv_report_name}",
            "html_report": f"/report/{html_report_name}",
            "best_3": best_3,
            "worst_3": worst_3,
            "all_results": results
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/simulator-ui")
def simulator_ui():
    html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Live Market Simulator</title>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0d1117;
            color: #c9d1d9;
            padding: 20px;
        }
        .container { max-width: 1600px; margin: 0 auto; }
        h1 { color: #58a6ff; margin-bottom: 20px; }
        h2 { color: #8b949e; margin: 15px 0 10px; font-size: 16px; }

        .controls {
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
            align-items: flex-end;
            margin-bottom: 20px;
            padding: 20px;
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 8px;
        }
        .control-group { display: flex; flex-direction: column; gap: 5px; }
        .control-group label { font-size: 12px; color: #8b949e; }
        .control-group input, .control-group select {
            padding: 8px 12px;
            background: #0d1117;
            border: 1px solid #30363d;
            border-radius: 4px;
            color: #c9d1d9;
            font-size: 14px;
        }
        .control-group input:focus, .control-group select:focus {
            outline: none;
            border-color: #58a6ff;
        }

        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 6px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }
        .btn-primary { background: #238636; color: white; }
        .btn-primary:hover { background: #2ea043; }
        .btn-secondary { background: #21262d; color: #c9d1d9; border: 1px solid #30363d; }
        .btn-secondary:hover { background: #30363d; }
        .btn-danger { background: #da3633; color: white; }
        .btn-danger:hover { background: #f85149; }
        .btn-large { padding: 15px 40px; font-size: 18px; }
        .btn:disabled { opacity: 0.5; cursor: not-allowed; }

        .main-grid {
            display: grid;
            grid-template-columns: 1fr 350px;
            gap: 20px;
        }

        .chart-container {
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 15px;
        }

        .sidebar {
            display: flex;
            flex-direction: column;
            gap: 15px;
            max-height: calc(100vh - 200px);
            overflow-y: auto;
        }

        .info-card {
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 8px;
            padding: 15px;
        }

        .step-btn-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 10px;
            padding: 20px;
        }

        .metrics-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
        }
        .metric { padding: 10px; background: #0d1117; border-radius: 4px; }
        .metric-label { font-size: 11px; color: #8b949e; text-transform: uppercase; }
        .metric-value { font-size: 18px; font-weight: 600; margin-top: 3px; }

        .positive { color: #3fb950; }
        .negative { color: #f85149; }
        .neutral { color: #8b949e; }

        .signal-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
        }
        .signal-BUY { background: #238636; color: white; }
        .signal-SELL { background: #da3633; color: white; }
        .signal-HOLD { background: #30363d; color: #8b949e; }

        .candle-info {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 8px;
            font-size: 13px;
        }
        .candle-info span { color: #8b949e; }
        .candle-info strong { color: #c9d1d9; }

        .trade-log {
            max-height: 200px;
            overflow-y: auto;
            font-size: 12px;
        }
        .trade-entry {
            padding: 8px;
            border-bottom: 1px solid #21262d;
        }
        .trade-entry:last-child { border-bottom: none; }

        .progress-bar {
            height: 4px;
            background: #21262d;
            border-radius: 2px;
            margin-top: 10px;
            overflow: hidden;
        }
        .progress-fill {
            height: 100%;
            background: #58a6ff;
            transition: width 0.3s;
        }

        .status-text {
            font-size: 13px;
            color: #8b949e;
            margin-top: 5px;
        }

        #autoplayControls {
            display: flex;
            gap: 10px;
            align-items: center;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Backtesting Studio</h1>

        <div class="tab-buttons">
            <button class="tab-btn active" onclick="switchTab('simulator')">🎬 Live Simulator</button>
            <button class="tab-btn" onclick="switchTab('sweep')">📊 Parameter Sweep</button>
        </div>

        <div id="simulatorTab">
        <div class="controls">
            <div class="control-group">
                <label>Symbol</label>
                <select id="symbol">
                    <option value="BSE:RELIANCE-A">BSE:RELIANCE-A</option>
                </select>
            </div>
            <div class="control-group">
                <label>Timeframe</label>
                <select id="timeframe">
                    <option value="1m">1 Minute</option>
                    <option value="5m">5 Minutes</option>
                    <option value="15m">15 Minutes</option>
                    <option value="30m">30 Minutes</option>
                    <option value="1h" selected>1 Hour</option>
                    <option value="1D">1 Day</option>
                </select>
            </div>
            <div class="control-group">
                <label>Strategy</label>
                <select id="strategy" onchange="toggleStrategyParams()">
                    <option value="RSI">RSI</option>
                    <option value="MACD">MACD</option>
                    <option value="RSI+MACD">RSI + MACD</option>
                </select>
            </div>
            <div class="control-group" id="rsiParams">
                <label>RSI Period</label>
                <input type="number" id="rsiPeriod" value="14" min="2" max="50">
            </div>
            <div class="control-group" id="rsiOB">
                <label>Overbought</label>
                <input type="number" id="overbought" value="70" min="50" max="100">
            </div>
            <div class="control-group" id="rsiOS">
                <label>Oversold</label>
                <input type="number" id="oversold" value="30" min="0" max="50">
            </div>
            <div class="control-group" id="macdFast" style="display:none;">
                <label>MACD Fast</label>
                <input type="number" id="macdFastPeriod" value="12" min="2" max="50">
            </div>
            <div class="control-group" id="macdSlow" style="display:none;">
                <label>MACD Slow</label>
                <input type="number" id="macdSlowPeriod" value="26" min="2" max="100">
            </div>
            <div class="control-group" id="macdSignal" style="display:none;">
                <label>MACD Signal</label>
                <input type="number" id="macdSignalPeriod" value="9" min="2" max="50">
            </div>
            <div class="control-group">
                <label>Capital</label>
                <input type="number" id="capital" value="100000" min="1000">
            </div>
            <button class="btn btn-primary" onclick="createSession()">Start Simulation</button>
        </div>

        <div class="main-grid" id="simulatorArea" style="display:none;">
            <div class="charts">
                <div class="chart-container">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                        <h2 style="margin: 0;">Price Chart</h2>
                        <select id="chartTypeSelect" onchange="toggleChartType()" style="padding: 6px 12px; background: #0d1117; border: 1px solid #30363d; border-radius: 4px; color: #c9d1d9;">
                            <option value="line">Line</option>
                            <option value="candlestick">Candlestick</option>
                        </select>
                    </div>
                    <div id="priceChart"></div>
                </div>
                <div class="chart-container">
                    <h2>Indicator</h2>
                    <div id="indicatorChart"></div>
                </div>
                <div class="chart-container">
                    <h2>Equity Curve</h2>
                    <div id="equityChart"></div>
                </div>
                <div class="chart-container">
                    <h2>Entry & Exit Details</h2>
                    <table style="width: 100%; font-size: 12px; border-collapse: collapse;">
                        <thead>
                            <tr style="background: #21262d;">
                                <th style="padding: 8px; text-align: left; border-bottom: 1px solid #30363d; color: #8b949e;">#</th>
                                <th style="padding: 8px; text-align: left; border-bottom: 1px solid #30363d; color: #8b949e;">Entry Time</th>
                                <th style="padding: 8px; text-align: left; border-bottom: 1px solid #30363d; color: #8b949e;">Exit Time</th>
                                <th style="padding: 8px; text-align: left; border-bottom: 1px solid #30363d; color: #8b949e;">Entry Price</th>
                                <th style="padding: 8px; text-align: left; border-bottom: 1px solid #30363d; color: #8b949e;">Exit Price</th>
                                <th style="padding: 8px; text-align: left; border-bottom: 1px solid #30363d; color: #8b949e;">Lots</th>
                                <th style="padding: 8px; text-align: left; border-bottom: 1px solid #30363d; color: #8b949e;">P&L</th>
                            </tr>
                        </thead>
                        <tbody id="entryExitTable">
                            <tr><td colspan="7" style="padding: 8px; color: #8b949e;">No trades yet</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <div class="sidebar">
                <div class="info-card step-btn-container">
                    <button class="btn btn-primary btn-large" id="stepBtn" onclick="step()">
                        Next Candle
                    </button>
                    <div id="autoplayControls">
                        <button class="btn btn-secondary" id="autoplayBtn" onclick="toggleAutoplay()">Auto Play</button>
                        <select id="autoplaySpeed">
                            <option value="1000">1s</option>
                            <option value="500" selected>0.5s</option>
                            <option value="200">0.2s</option>
                            <option value="100">0.1s</option>
                        </select>
                    </div>
                    <div class="progress-bar"><div class="progress-fill" id="progressFill"></div></div>
                    <div class="status-text" id="statusText">Ready to start</div>
                </div>

                <div class="info-card">
                    <h2>Current Candle</h2>
                    <div class="candle-info" id="candleInfo">
                        <div><span>Time:</span><br><strong id="candleTime">-</strong></div>
                        <div><span>Open:</span><br><strong id="candleOpen">-</strong></div>
                        <div><span>High:</span><br><strong id="candleHigh">-</strong></div>
                        <div><span>Low:</span><br><strong id="candleLow">-</strong></div>
                        <div><span>Close:</span><br><strong id="candleClose">-</strong></div>
                        <div><span>Volume:</span><br><strong id="candleVolume">-</strong></div>
                    </div>
                </div>

                <div class="info-card">
                    <h2>Signal & Position</h2>
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-top:10px;">
                        <div>
                            <span class="signal-badge signal-HOLD" id="signalBadge">HOLD</span>
                        </div>
                        <div style="text-align:right;">
                            <span style="color:#8b949e;">Position:</span>
                            <strong id="positionText">Flat</strong>
                        </div>
                    </div>
                    <div style="margin-top:15px;" id="indicatorValues">
                        <div><span style="color:#8b949e;">RSI:</span> <strong id="rsiValue">-</strong></div>
                    </div>
                </div>

                <div class="info-card">
                    <h2>Metrics</h2>
                    <div class="metrics-grid">
                        <div class="metric">
                            <div class="metric-label">Equity</div>
                            <div class="metric-value" id="equityValue">₹100,000</div>
                        </div>
                        <div class="metric">
                            <div class="metric-label">P&L</div>
                            <div class="metric-value" id="pnlValue">₹0</div>
                        </div>
                        <div class="metric">
                            <div class="metric-label">Trades</div>
                            <div class="metric-value" id="tradesValue">0</div>
                        </div>
                        <div class="metric">
                            <div class="metric-label">Win Rate</div>
                            <div class="metric-value" id="winRateValue">0%</div>
                        </div>
                    </div>
                </div>

                <div class="info-card">
                    <h2>Trade Log</h2>
                    <div class="trade-log" id="tradeLog">
                        <div style="color:#8b949e; padding:10px;">No trades yet</div>
                    </div>
                </div>

                <button class="btn btn-secondary" onclick="resetSession()">Reset</button>
            </div>
        </div>
        </div>

        <div id="sweepTab" style="display:none;">
            <div style="padding: 20px; background: #0d1117; min-height: 600px;">
                <h2 style="color: #58a6ff; margin-bottom: 20px;">⚙️ MACD Parameter Sweep</h2>
                
                <div class="controls" style="margin-bottom: 20px;">
                    <div class="control-group">
                        <label>Symbol</label>
                        <select id="sweepSymbol">
                            <option value="BSE:RELIANCE-A">BSE:RELIANCE-A</option>
                        </select>
                    </div>
                    <div class="control-group">
                        <label>Timeframe</label>
                        <select id="sweepTimeframe">
                            <option value="1m">1 Minute</option>
                            <option value="5m">5 Minutes</option>
                            <option value="15m">15 Minutes</option>
                            <option value="30m">30 Minutes</option>
                            <option value="1h" selected>1 Hour</option>
                            <option value="1D">1 Day</option>
                        </select>
                    </div>
                </div>

                <div style="background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 20px; margin-bottom: 20px;">
                    <h3 style="color: #8b949e; margin-bottom: 15px;">⚡ Fast Period Range</h3>
                    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px;">
                        <div class="control-group">
                            <label>Start</label>
                            <input type="number" id="fastStart" value="8" min="2" max="50" oninput="updateCombinations()">
                        </div>
                        <div class="control-group">
                            <label>End</label>
                            <input type="number" id="fastEnd" value="24" min="2" max="50" oninput="updateCombinations()">
                        </div>
                        <div style="padding-top: 23px; color: #8b949e; font-size: 12px;">
                            Range: <strong id="fastRange" style="color: #58a6ff;">17</strong> values
                        </div>
                    </div>
                </div>

                <div style="background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 20px; margin-bottom: 20px;">
                    <h3 style="color: #8b949e; margin-bottom: 15px;">📈 Slow Period Range</h3>
                    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px;">
                        <div class="control-group">
                            <label>Start</label>
                            <input type="number" id="slowStart" value="18" min="2" max="100" oninput="updateCombinations()">
                        </div>
                        <div class="control-group">
                            <label>End</label>
                            <input type="number" id="slowEnd" value="52" min="2" max="100" oninput="updateCombinations()">
                        </div>
                        <div style="padding-top: 23px; color: #8b949e; font-size: 12px;">
                            Range: <strong id="slowRange" style="color: #58a6ff;">35</strong> values
                        </div>
                    </div>
                </div>

                <div style="background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 20px; margin-bottom: 20px;">
                    <h3 style="color: #8b949e; margin-bottom: 15px;">📊 Signal Period Range</h3>
                    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px;">
                        <div class="control-group">
                            <label>Start</label>
                            <input type="number" id="signalStart" value="5" min="2" max="50" oninput="updateCombinations()">
                        </div>
                        <div class="control-group">
                            <label>End</label>
                            <input type="number" id="signalEnd" value="12" min="2" max="50" oninput="updateCombinations()">
                        </div>
                        <div style="padding-top: 23px; color: #8b949e; font-size: 12px;">
                            Range: <strong id="signalRange" style="color: #58a6ff;">8</strong> values
                        </div>
                    </div>
                </div>

                <div style="background: #21262d; border-left: 4px solid #58a6ff; padding: 15px; margin-bottom: 20px; border-radius: 4px;">
                    <strong style="color: #c9d1d9;">Total Combinations:</strong> <span id="totalCombinations" style="color: #58a6ff; font-size: 18px; font-weight: 600;">4,760</span>
                </div>

                <div class="control-group" style="max-width: 200px; margin-bottom: 20px;">
                    <label>Initial Capital</label>
                    <input type="number" id="sweepCapital" value="100000" min="1000">
                </div>

                <button class="btn btn-primary btn-large" id="runSweepBtn" onclick="runSweep()" style="width: 100%; max-width: 100%; padding: 15px 40px;">
                    🚀 Run Parameter Sweep
                </button>

                <div id="sweepProgress" style="display:none; margin-top: 20px;">
                    <div style="background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 20px;">
                        <h3 style="color: #8b949e; margin-bottom: 10px;">Running Sweep...</h3>
                        <div class="progress-bar" style="height: 6px;">
                            <div class="progress-fill" id="sweepProgressBar" style="width: 0%;"></div>
                        </div>
                        <div style="margin-top: 10px; color: #8b949e; font-size: 12px;">
                            <span id="sweepStatus">Initializing...</span>
                        </div>
                    </div>
                </div>

                <div id="sweepResults" style="display:none; margin-top: 20px;">
                    <div style="background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 20px;">
                        <h3 style="color: #58a6ff; margin-bottom: 15px;">✅ Sweep Complete!</h3>

                        <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; margin-bottom: 20px;">
                            <div style="background: #0d1117; padding: 15px; border-radius: 6px; border-left: 3px solid #3fb950;">
                                <div style="color: #8b949e; font-size: 12px; text-transform: uppercase;">Best P&L</div>
                                <div style="font-size: 20px; font-weight: 600; color: #3fb950; margin-top: 5px;" id="bestPnL">+₹53.70</div>
                                <div style="color: #8b949e; font-size: 11px; margin-top: 5px;" id="bestConfig">Fast=23, Slow=19, Signal=5</div>
                            </div>
                            <div style="background: #0d1117; padding: 15px; border-radius: 6px; border-left: 3px solid #f85149;">
                                <div style="color: #8b949e; font-size: 12px; text-transform: uppercase;">Worst P&L</div>
                                <div style="font-size: 20px; font-weight: 600; color: #f85149; margin-top: 5px;" id="worstPnL">-₹196.90</div>
                                <div style="color: #8b949e; font-size: 11px; margin-top: 5px;" id="worstConfig">Fast=8, Slow=18, Signal=5</div>
                            </div>
                        </div>

                        <h4 style="color: #8b949e; margin-bottom: 10px;">🏆 Top 5 Performers</h4>
                        <table id="topPerformersTable" style="width: 100%; font-size: 12px; border-collapse: collapse; margin-bottom: 20px;">
                            <thead>
                                <tr style="background: #21262d;">
                                    <th style="padding: 8px; text-align: left; border-bottom: 1px solid #30363d; color: #8b949e;">Fast</th>
                                    <th style="padding: 8px; text-align: left; border-bottom: 1px solid #30363d; color: #8b949e;">Slow</th>
                                    <th style="padding: 8px; text-align: left; border-bottom: 1px solid #30363d; color: #8b949e;">Signal</th>
                                    <th style="padding: 8px; text-align: right; border-bottom: 1px solid #30363d; color: #8b949e;">P&L</th>
                                    <th style="padding: 8px; text-align: right; border-bottom: 1px solid #30363d; color: #8b949e;">Win Rate</th>
                                    <th style="padding: 8px; text-align: right; border-bottom: 1px solid #30363d; color: #8b949e;">Trades</th>
                                </tr>
                            </thead>
                            <tbody id="topPerformersBody"></tbody>
                        </table>

                        <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                            <a id="htmlReportLink" href="fyers/backtesting/reports/macd_sweep_consolidated_report.html" target="_blank" class="btn btn-secondary">📈 View Detailed Report</a>
                            <button class="btn btn-secondary" onclick="newSweep()">🔄 New Sweep</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <style>
        .tab-buttons {
            display: flex;
            gap: 0;
            margin-bottom: 0;
            border-bottom: 2px solid #30363d;
            padding: 0;
        }
        .tab-btn {
            padding: 12px 24px;
            border: none;
            background: transparent;
            color: #8b949e;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            border-bottom: 3px solid transparent;
            transition: all 0.2s;
            margin: 0;
        }
        .tab-btn.active {
            color: #58a6ff;
            border-bottom-color: #58a6ff;
        }
        .tab-btn:hover { color: #c9d1d9; }
    </style>

    <script>
        let sessionId = null;
        let autoplayInterval = null;
        let priceData = { x: [], close: [], high: [], low: [], open: [] };
        let indicatorData = { x: [], rsi: [], macd: [], signal: [], histogram: [] };
        let equityData = { x: [], y: [] };
        let buySignals = { x: [], y: [] };
        let sellSignals = { x: [], y: [] };
        let strategyType = 'RSI';
        let chartType = 'line';

        function toggleStrategyParams() {
            const strategy = document.getElementById('strategy').value;
            strategyType = strategy;

            const rsiParams = ['rsiParams', 'rsiOB', 'rsiOS'];
            const macdParams = ['macdFast', 'macdSlow', 'macdSignal'];

            if (strategy === 'RSI') {
                rsiParams.forEach(id => document.getElementById(id).style.display = 'flex');
                macdParams.forEach(id => document.getElementById(id).style.display = 'none');
            } else if (strategy === 'MACD') {
                rsiParams.forEach(id => document.getElementById(id).style.display = 'none');
                macdParams.forEach(id => document.getElementById(id).style.display = 'flex');
            } else {
                rsiParams.forEach(id => document.getElementById(id).style.display = 'flex');
                macdParams.forEach(id => document.getElementById(id).style.display = 'flex');
            }
        }

        async function createSession() {
            const body = {
                symbol: document.getElementById('symbol').value,
                timeframe: document.getElementById('timeframe').value,
                strategy: document.getElementById('strategy').value,
                initial_capital: parseFloat(document.getElementById('capital').value),
                rsi_period: parseInt(document.getElementById('rsiPeriod').value),
                rsi_overbought: parseFloat(document.getElementById('overbought').value),
                rsi_oversold: parseFloat(document.getElementById('oversold').value),
                macd_fast: parseInt(document.getElementById('macdFastPeriod').value),
                macd_slow: parseInt(document.getElementById('macdSlowPeriod').value),
                macd_signal: parseInt(document.getElementById('macdSignalPeriod').value)
            };

            try {
                const res = await fetch('/simulator/create', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(body)
                });
                const data = await res.json();

                if (data.status === 'ok') {
                    sessionId = data.session_id;
                    document.getElementById('simulatorArea').style.display = 'grid';
                    document.getElementById('statusText').textContent = `Session ${sessionId} - ${data.total_candles} candles`;

                    priceData = { x: [], close: [], high: [], low: [], open: [] };
                    indicatorData = { x: [], rsi: [], macd: [], signal: [], histogram: [] };
                    equityData = { x: [], y: [] };
                    buySignals = { x: [], y: [] };
                    sellSignals = { x: [], y: [] };

                    initCharts();
                } else {
                    alert('Error: ' + data.detail);
                }
            } catch (e) {
                alert('Error creating session: ' + e.message);
            }
        }

        function initCharts() {
            const layout = {
                paper_bgcolor: '#161b22',
                plot_bgcolor: '#161b22',
                font: { color: '#c9d1d9' },
                xaxis: { gridcolor: '#30363d', linecolor: '#30363d', rangeslider: { visible: false } },
                yaxis: { gridcolor: '#30363d', linecolor: '#30363d' },
                margin: { t: 20, r: 20, b: 40, l: 60 },
                showlegend: true,
                legend: { x: 0, y: 1, bgcolor: 'rgba(0,0,0,0)' },
                height: 300
            };

            renderPriceChart(layout);

            if (strategyType === 'RSI' || strategyType === 'RSI+MACD') {
                Plotly.newPlot('indicatorChart', [
                    { x: [], y: [], type: 'scatter', mode: 'lines', name: 'RSI', line: { color: '#a371f7' } }
                ], {
                    ...layout,
                    height: 200,
                    yaxis: { ...layout.yaxis, range: [0, 100] },
                    shapes: [
                        { type: 'line', y0: 70, y1: 70, x0: 0, x1: 1, xref: 'paper', line: { color: '#f85149', dash: 'dash', width: 1 } },
                        { type: 'line', y0: 30, y1: 30, x0: 0, x1: 1, xref: 'paper', line: { color: '#3fb950', dash: 'dash', width: 1 } }
                    ]
                });
            } else {
                Plotly.newPlot('indicatorChart', [
                    { x: [], y: [], type: 'scatter', mode: 'lines', name: 'MACD', line: { color: '#58a6ff' } },
                    { x: [], y: [], type: 'scatter', mode: 'lines', name: 'Signal', line: { color: '#f85149' } },
                    { x: [], y: [], type: 'bar', name: 'Histogram', marker: { color: [] } }
                ], { ...layout, height: 200 });
            }

            Plotly.newPlot('equityChart', [
                { x: [], y: [], type: 'scatter', mode: 'lines', fill: 'tozeroy', line: { color: '#3fb950' }, fillcolor: 'rgba(63,185,80,0.1)' }
            ], { ...layout, height: 200 });
        }

        function renderPriceChart(layout) {
            if (chartType === 'candlestick') {
                Plotly.newPlot('priceChart', [
                    { x: priceData.x, open: priceData.open, high: priceData.high, low: priceData.low, close: priceData.close, type: 'candlestick', name: 'Price', yaxis: 'y' },
                    { x: buySignals.x, y: buySignals.y, type: 'scatter', mode: 'markers', name: 'Buy', marker: { color: '#3fb950', size: 12, symbol: 'triangle-up' }, yaxis: 'y' },
                    { x: sellSignals.x, y: sellSignals.y, type: 'scatter', mode: 'markers', name: 'Sell', marker: { color: '#f85149', size: 12, symbol: 'triangle-down' }, yaxis: 'y' }
                ], { ...layout, height: 300 });
            } else {
                Plotly.newPlot('priceChart', [
                    { x: priceData.x, y: priceData.close, type: 'scatter', mode: 'lines', name: 'Price', line: { color: '#58a6ff' }, yaxis: 'y' },
                    { x: buySignals.x, y: buySignals.y, type: 'scatter', mode: 'markers', name: 'Buy', marker: { color: '#3fb950', size: 12, symbol: 'triangle-up' }, yaxis: 'y' },
                    { x: sellSignals.x, y: sellSignals.y, type: 'scatter', mode: 'markers', name: 'Sell', marker: { color: '#f85149', size: 12, symbol: 'triangle-down' }, yaxis: 'y' }
                ], { ...layout, height: 300 });
            }
        }

        function toggleChartType() {
            chartType = document.getElementById('chartTypeSelect').value;
            const layout = {
                paper_bgcolor: '#161b22',
                plot_bgcolor: '#161b22',
                font: { color: '#c9d1d9' },
                xaxis: { gridcolor: '#30363d', linecolor: '#30363d', rangeslider: { visible: false } },
                yaxis: { gridcolor: '#30363d', linecolor: '#30363d' },
                margin: { t: 20, r: 20, b: 40, l: 60 },
                showlegend: true,
                legend: { x: 0, y: 1, bgcolor: 'rgba(0,0,0,0)' },
                height: 300
            };
            renderPriceChart(layout);
        }

        async function step() {
            if (!sessionId) return;

            try {
                const res = await fetch(`/simulator/${sessionId}/step`, { method: 'POST' });
                const data = await res.json();

                if (data.status === 'finished') {
                    document.getElementById('statusText').textContent = 'Simulation complete!';
                    document.getElementById('stepBtn').disabled = true;
                    stopAutoplay();
                    return;
                }

                const step = data.step;
                const candle = step.candle;

                priceData.x.push(candle.datetime);
                priceData.close.push(candle.close);
                priceData.open.push(candle.open);
                priceData.high.push(candle.high);
                priceData.low.push(candle.low);

                if (step.signal === 'BUY') {
                    buySignals.x.push(candle.datetime);
                    buySignals.y.push(candle.close);
                    addEntryRow(candle.datetime, candle.close);
                } else if (step.signal === 'SELL') {
                    sellSignals.x.push(candle.datetime);
                    sellSignals.y.push(candle.close);
                    addExitRow(candle.datetime, candle.close);
                }

                indicatorData.x.push(candle.datetime);
                if (step.indicators.rsi !== null) indicatorData.rsi.push(step.indicators.rsi);
                if (step.indicators.macd_line !== null) indicatorData.macd.push(step.indicators.macd_line);
                if (step.indicators.macd_signal !== null) indicatorData.signal.push(step.indicators.macd_signal);
                if (step.indicators.macd_histogram !== null) indicatorData.histogram.push(step.indicators.macd_histogram);

                equityData.x.push(candle.datetime);
                equityData.y.push(step.equity);

                // Update price chart - purge and recreate for clean state
                const priceLayout = {
                    paper_bgcolor: '#161b22',
                    plot_bgcolor: '#161b22',
                    font: { color: '#c9d1d9' },
                    xaxis: { 
                        gridcolor: '#30363d', 
                        linecolor: '#30363d',
                        domain: [0, 1],
                        rangeslider: { visible: false }
                    },
                    yaxis: { 
                        gridcolor: '#30363d', 
                        linecolor: '#30363d',
                        domain: [0, 1]
                    },
                    margin: { t: 20, r: 20, b: 40, l: 60 },
                    showlegend: true,
                    legend: { x: 0, y: 1, bgcolor: 'rgba(0,0,0,0)' },
                    height: 300
                };
                
                Plotly.purge('priceChart');
                
                if (chartType === 'candlestick') {
                    Plotly.newPlot('priceChart', [
                        { x: priceData.x, open: priceData.open, high: priceData.high, low: priceData.low, close: priceData.close, type: 'candlestick', name: 'Price', increasing: {line: {color: '#3fb950'}}, decreasing: {line: {color: '#f85149'}}, xaxis: 'x', yaxis: 'y' },
                        { x: buySignals.x, y: buySignals.y, type: 'scatter', mode: 'markers', name: 'Buy', marker: { color: '#3fb950', size: 12, symbol: 'triangle-up' }, xaxis: 'x', yaxis: 'y' },
                        { x: sellSignals.x, y: sellSignals.y, type: 'scatter', mode: 'markers', name: 'Sell', marker: { color: '#f85149', size: 12, symbol: 'triangle-down' }, xaxis: 'x', yaxis: 'y' }
                    ], priceLayout, {displayModeBar: false});
                } else {
                    Plotly.newPlot('priceChart', [
                        { x: priceData.x, y: priceData.close, type: 'scatter', mode: 'lines', name: 'Price', line: { color: '#58a6ff' }, xaxis: 'x', yaxis: 'y' },
                        { x: buySignals.x, y: buySignals.y, type: 'scatter', mode: 'markers', name: 'Buy', marker: { color: '#3fb950', size: 12, symbol: 'triangle-up' }, xaxis: 'x', yaxis: 'y' },
                        { x: sellSignals.x, y: sellSignals.y, type: 'scatter', mode: 'markers', name: 'Sell', marker: { color: '#f85149', size: 12, symbol: 'triangle-down' }, xaxis: 'x', yaxis: 'y' }
                    ], priceLayout, {displayModeBar: false});
                }

                if (strategyType === 'RSI' || strategyType === 'RSI+MACD') {
                    Plotly.update('indicatorChart', {
                        x: [indicatorData.x.slice(-indicatorData.rsi.length)],
                        y: [indicatorData.rsi]
                    });
                } else {
                    const colors = indicatorData.histogram.map(v => v >= 0 ? '#3fb950' : '#f85149');
                    Plotly.update('indicatorChart', {
                        x: [indicatorData.x.slice(-indicatorData.macd.length), indicatorData.x.slice(-indicatorData.signal.length), indicatorData.x.slice(-indicatorData.histogram.length)],
                        y: [indicatorData.macd, indicatorData.signal, indicatorData.histogram],
                        'marker.color': [null, null, colors]
                    });
                }

                Plotly.update('equityChart', { x: [equityData.x], y: [equityData.y] });

                document.getElementById('candleTime').textContent = candle.datetime;
                document.getElementById('candleOpen').textContent = candle.open.toFixed(2);
                document.getElementById('candleHigh').textContent = candle.high.toFixed(2);
                document.getElementById('candleLow').textContent = candle.low.toFixed(2);
                document.getElementById('candleClose').textContent = candle.close.toFixed(2);
                document.getElementById('candleVolume').textContent = candle.volume.toLocaleString();

                const signalBadge = document.getElementById('signalBadge');
                signalBadge.textContent = step.signal;
                signalBadge.className = `signal-badge signal-${step.signal}`;

                document.getElementById('positionText').textContent = step.position === 1 ? 'Long' : 'Flat';

                let indicatorHtml = '';
                if (step.indicators.rsi !== null) {
                    indicatorHtml += `<div><span style="color:#8b949e;">RSI:</span> <strong>${step.indicators.rsi}</strong></div>`;
                }
                if (step.indicators.macd_line !== null) {
                    indicatorHtml += `<div><span style="color:#8b949e;">MACD:</span> <strong>${step.indicators.macd_line}</strong></div>`;
                    indicatorHtml += `<div><span style="color:#8b949e;">Signal:</span> <strong>${step.indicators.macd_signal}</strong></div>`;
                }
                document.getElementById('indicatorValues').innerHTML = indicatorHtml || '<div><span style="color:#8b949e;">Warming up...</span></div>';

                const metrics = data.metrics;
                const pnl = metrics.total_pnl;
                document.getElementById('equityValue').textContent = '₹' + metrics.final_equity.toLocaleString();
                document.getElementById('pnlValue').textContent = '₹' + pnl.toLocaleString();
                document.getElementById('pnlValue').className = `metric-value ${pnl >= 0 ? 'positive' : 'negative'}`;
                document.getElementById('tradesValue').textContent = metrics.total_trades;
                document.getElementById('winRateValue').textContent = metrics.win_rate.toFixed(1) + '%';

                if (step.last_completed_trade && data.metrics.total_trades > 0) {
                    updateTradeLog(step.last_completed_trade, data.metrics.total_trades);
                }

                const progress = ((data.total - data.remaining) / data.total) * 100;
                document.getElementById('progressFill').style.width = progress + '%';
                document.getElementById('statusText').textContent = `Candle ${data.total - data.remaining} of ${data.total}`;

            } catch (e) {
                console.error('Step error:', e);
                stopAutoplay();
            }
        }

        let lastTradeCount = 0;
        let tradeCounter = 0;
        let currentTradeRowId = null;

        function addEntryRow(entryTime, entryPrice) {
            const tbody = document.getElementById('entryExitTable');
            
            // Clear placeholder if it exists
            if (tbody.querySelector('tr td[colspan]')) {
                tbody.innerHTML = '';
            }
            
            tradeCounter++;
            currentTradeRowId = `trade-${tradeCounter}`;
            
            const row = document.createElement('tr');
            row.id = currentTradeRowId;
            row.style.borderBottom = '1px solid #30363d';
            row.innerHTML = `
                <td style="padding: 8px; color: #c9d1d9;">${tradeCounter}</td>
                <td style="padding: 8px; color: #58a6ff;">${entryTime}</td>
                <td style="padding: 8px; color: #8b949e;">-</td>
                <td style="padding: 8px; color: #3fb950;">₹${entryPrice.toFixed(2)}</td>
                <td style="padding: 8px; color: #8b949e;">-</td>
                <td style="padding: 8px; color: #c9d1d9;">1</td>
                <td style="padding: 8px; color: #8b949e;">-</td>
            `;
            tbody.insertBefore(row, tbody.firstChild);
        }

        function addExitRow(exitTime, exitPrice) {
            if (!currentTradeRowId) return;
            
            const row = document.getElementById(currentTradeRowId);
            if (!row) return;
            
            // Update the row with exit data
            const cells = row.querySelectorAll('td');
            cells[2].textContent = exitTime;
            cells[2].style.color = '#58a6ff';
            cells[4].textContent = `₹${exitPrice.toFixed(2)}`;
            cells[4].style.color = '#f85149';
            
            // Calculate P&L
            const entryPrice = parseFloat(cells[3].textContent.replace('₹', ''));
            const pnl = (exitPrice - entryPrice) * 1;
            const pnlClass = pnl >= 0 ? '#3fb950' : '#f85149';
            cells[6].textContent = `₹${pnl.toFixed(2)}`;
            cells[6].style.color = pnlClass;
        }

        function updateTradeLog(trade, totalTrades) {
            if (totalTrades <= lastTradeCount) return;
            lastTradeCount = totalTrades;

            const log = document.getElementById('tradeLog');
            if (log.querySelector('div[style]')) {
                log.innerHTML = '';
            }

            const pnlClass = trade.pnl >= 0 ? 'positive' : 'negative';
            const entry = document.createElement('div');
            entry.className = 'trade-entry';
            entry.innerHTML = `
                <div style="display:flex; justify-content:space-between;">
                    <span>#${totalTrades}</span>
                    <span class="${pnlClass}">₹${trade.pnl.toFixed(2)} (${trade.pnl_percent.toFixed(2)}%)</span>
                </div>
                <div style="color:#8b949e; font-size:11px; margin-top:3px;">
                    ${trade.entry_price.toFixed(2)} → ${trade.exit_price.toFixed(2)}
                </div>
            `;
            log.insertBefore(entry, log.firstChild);
        }

        function updateEntryExitCard(trade) {
            // Function no longer needed as we're using addEntryRow and addExitRow
        }

        function toggleAutoplay() {
            if (autoplayInterval) {
                stopAutoplay();
            } else {
                startAutoplay();
            }
        }

        function startAutoplay() {
            const speed = parseInt(document.getElementById('autoplaySpeed').value);
            document.getElementById('autoplayBtn').textContent = 'Stop';
            document.getElementById('autoplayBtn').classList.add('btn-danger');
            document.getElementById('autoplayBtn').classList.remove('btn-secondary');
            autoplayInterval = setInterval(step, speed);
        }

        function stopAutoplay() {
            if (autoplayInterval) {
                clearInterval(autoplayInterval);
                autoplayInterval = null;
            }
            document.getElementById('autoplayBtn').textContent = 'Auto Play';
            document.getElementById('autoplayBtn').classList.remove('btn-danger');
            document.getElementById('autoplayBtn').classList.add('btn-secondary');
        }

        async function resetSession() {
            if (!sessionId) return;
            stopAutoplay();

            try {
                await fetch(`/simulator/${sessionId}/reset`, { method: 'POST' });

                priceData = { x: [], close: [], high: [], low: [], open: [] };
                indicatorData = { x: [], rsi: [], macd: [], signal: [], histogram: [] };
                equityData = { x: [], y: [] };
                buySignals = { x: [], y: [] };
                sellSignals = { x: [], y: [] };
                lastTradeCount = 0;

                initCharts();

                document.getElementById('stepBtn').disabled = false;
                document.getElementById('tradeLog').innerHTML = '<div style="color:#8b949e; padding:10px;">No trades yet</div>';
                document.getElementById('progressFill').style.width = '0%';
                document.getElementById('statusText').textContent = 'Session reset';
                document.getElementById('signalBadge').textContent = 'HOLD';
                document.getElementById('signalBadge').className = 'signal-badge signal-HOLD';

            } catch (e) {
                alert('Error resetting session: ' + e.message);
            }
        }

        // ===== PARAMETER SWEEP TAB FUNCTIONS =====
        
        function switchTab(tab) {
            document.getElementById('simulatorTab').style.display = tab === 'simulator' ? 'block' : 'none';
            document.getElementById('sweepTab').style.display = tab === 'sweep' ? 'block' : 'none';
            
            const btns = document.querySelectorAll('.tab-btn');
            btns.forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
        }

        function updateCombinations() {
            const fast = Math.abs(parseInt(document.getElementById('fastEnd').value) - parseInt(document.getElementById('fastStart').value)) + 1;
            const slow = Math.abs(parseInt(document.getElementById('slowEnd').value) - parseInt(document.getElementById('slowStart').value)) + 1;
            const signal = Math.abs(parseInt(document.getElementById('signalEnd').value) - parseInt(document.getElementById('signalStart').value)) + 1;
            
            document.getElementById('fastRange').textContent = fast;
            document.getElementById('slowRange').textContent = slow;
            document.getElementById('signalRange').textContent = signal;
            document.getElementById('totalCombinations').textContent = (fast * slow * signal).toLocaleString();
        }

        async function runSweep() {
            const symbol = document.getElementById('sweepSymbol').value;
            const timeframe = document.getElementById('sweepTimeframe').value;
            const fastStart = parseInt(document.getElementById('fastStart').value);
            const fastEnd = parseInt(document.getElementById('fastEnd').value);
            const slowStart = parseInt(document.getElementById('slowStart').value);
            const slowEnd = parseInt(document.getElementById('slowEnd').value);
            const signalStart = parseInt(document.getElementById('signalStart').value);
            const signalEnd = parseInt(document.getElementById('signalEnd').value);
            const capital = parseFloat(document.getElementById('sweepCapital').value);

            document.getElementById('runSweepBtn').disabled = true;
            document.getElementById('sweepProgress').style.display = 'block';
            document.getElementById('sweepResults').style.display = 'none';
            document.getElementById('sweepStatus').textContent = 'Running sweep... This may take 30-60 seconds.';
            document.getElementById('sweepProgressBar').style.width = '50%';

            try {
                const res = await fetch('/backtest/macd-sweep', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        symbol: symbol,
                        timeframe: timeframe,
                        fast_start: fastStart,
                        fast_end: fastEnd,
                        slow_start: slowStart,
                        slow_end: slowEnd,
                        signal_start: signalStart,
                        signal_end: signalEnd,
                        initial_capital: capital
                    })
                });

                const data = await res.json();

                if (data.status === 'ok') {
                    document.getElementById('sweepStatus').textContent = '✅ Sweep complete! Displaying results...';
                    document.getElementById('sweepProgressBar').style.width = '100%';

                    // Display results
                    const best = data.best_3[0];
                    const worst = data.worst_3[0];

                    document.getElementById('bestPnL').textContent = '₹' + best.total_pnl.toFixed(2);
                    document.getElementById('bestConfig').textContent = `Fast=${best.fast_period}, Slow=${best.slow_period}, Signal=${best.signal_period} (${best.win_rate.toFixed(1)}% WR)`;
                    
                    document.getElementById('worstPnL').textContent = '₹' + worst.total_pnl.toFixed(2);
                    document.getElementById('worstConfig').textContent = `Fast=${worst.fast_period}, Slow=${worst.slow_period}, Signal=${worst.signal_period} (${worst.win_rate.toFixed(1)}% WR)`;

                    // Populate top performers table
                    const tbody = document.getElementById('topPerformersBody');
                    tbody.innerHTML = '';
                    for (let i = 0; i < Math.min(5, data.best_3.length); i++) {
                        const row = data.best_3[i];
                        const pnlClass = row.total_pnl >= 0 ? 'color: #3fb950;' : 'color: #f85149;';
                        tbody.innerHTML += `
                            <tr style="border-bottom: 1px solid #30363d;">
                                <td style="padding: 8px;">${row.fast_period}</td>
                                <td style="padding: 8px;">${row.slow_period}</td>
                                <td style="padding: 8px;">${row.signal_period}</td>
                                <td style="padding: 8px; text-align: right; ${pnlClass}">₹${row.total_pnl.toFixed(2)}</td>
                                <td style="padding: 8px; text-align: right;">${row.win_rate.toFixed(1)}%</td>
                                <td style="padding: 8px; text-align: right;">${row.total_trades}</td>
                            </tr>
                        `;
                    }

                    // Set report link
                    document.getElementById('htmlReportLink').href = data.html_report;

                    setTimeout(() => {
                        document.getElementById('sweepProgress').style.display = 'none';
                        document.getElementById('sweepResults').style.display = 'block';
                    }, 500);
                } else {
                    alert('Error: ' + data.detail);
                }
            } catch (e) {
                alert('Sweep error: ' + e.message);
            } finally {
                document.getElementById('runSweepBtn').disabled = false;
            }
        }

        function newSweep() {
            document.getElementById('sweepProgress').style.display = 'none';
            document.getElementById('sweepResults').style.display = 'none';
            document.getElementById('runSweepBtn').disabled = false;
        }
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html)


def start_server():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5050)


if __name__ == "__main__":
    start_server()
