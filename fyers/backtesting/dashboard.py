import os
from datetime import datetime

from .engine import BacktestResult


def generate_entry_exit_cards(trades: list) -> str:
    """Generate HTML cards for entry/exit details."""
    cards_html = ""
    for i, t in enumerate(trades, 1):
        pnl_class = "positive" if t["pnl"] > 0 else "negative"
        exit_time = t.get("exit_time", "-")
        exit_price = f"{t['exit_price']:.2f}" if t.get("exit_price") else "-"
        
        cards_html += f"""
        <div style="background: #21262d; border: 1px solid #30363d; border-radius: 6px; padding: 12px; margin-bottom: 10px;">
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                <div>
                    <span style="color: #8b949e; font-size: 11px;">ENTRY TIME</span>
                    <div style="color: #58a6ff; font-weight: 600; margin-top: 2px;">{t["entry_time"]}</div>
                </div>
                <div>
                    <span style="color: #8b949e; font-size: 11px;">EXIT TIME</span>
                    <div style="color: #58a6ff; font-weight: 600; margin-top: 2px;">{exit_time}</div>
                </div>
                <div>
                    <span style="color: #8b949e; font-size: 11px;">ENTRY PRICE</span>
                    <div style="color: #3fb950; font-weight: 600; margin-top: 2px;">₹{t["entry_price"]:.2f}</div>
                </div>
                <div>
                    <span style="color: #8b949e; font-size: 11px;">EXIT PRICE</span>
                    <div style="color: #f85149; font-weight: 600; margin-top: 2px;">₹{exit_price}</div>
                </div>
                <div>
                    <span style="color: #8b949e; font-size: 11px;">LOTS PURCHASED</span>
                    <div style="color: #c9d1d9; font-weight: 600; margin-top: 2px;">{t.get("quantity", 1)}</div>
                </div>
                <div>
                    <span style="color: #8b949e; font-size: 11px;">P&L</span>
                    <div style="color: #{('3fb950' if t['pnl'] >= 0 else 'f85149')}; font-weight: 600; margin-top: 2px;">₹{t['pnl']:.2f}</div>
                </div>
            </div>
        </div>
        """
    return cards_html


def generate_dashboard(result: BacktestResult, output_path: str = "backtest_report.html") -> str:
    metrics = result.metrics
    config = result.strategy_config

    equity_dates = [e["datetime"] for e in result.equity_curve]
    equity_values = [e["equity"] for e in result.equity_curve]

    drawdown_dates = [d["datetime"] for d in result.drawdowns]
    drawdown_values = [d["drawdown"] for d in result.drawdowns]

    candle_dates = [c["datetime"] for c in result.candles]
    closes = [c["close"] for c in result.candles]

    buy_dates = []
    buy_prices = []
    sell_dates = []
    sell_prices = []

    for s in result.signals:
        if s["signal"] == "BUY":
            buy_dates.append(s["datetime"])
            buy_prices.append(s["price"])
        elif s["signal"] == "SELL":
            sell_dates.append(s["datetime"])
            sell_prices.append(s["price"])

    trades_html = ""
    entry_exit_cards_html = ""
    for i, t in enumerate(result.trades, 1):
        pnl_class = "positive" if t["pnl"] > 0 else "negative"
        exit_price_str = f"{t['exit_price']:.2f}" if t["exit_price"] else "-"
        trades_html += f"""
        <tr>
            <td>{i}</td>
            <td>{t["entry_time"]}</td>
            <td>{t["entry_price"]:.2f}</td>
            <td>{t["exit_time"] or "-"}</td>
            <td>{exit_price_str}</td>
            <td>{t.get("quantity", 1)}</td>
            <td class="{pnl_class}">{t["pnl"]:.2f}</td>
            <td class="{pnl_class}">{t["pnl_percent"]:.2f}%</td>
        </tr>
        """
    
    # Generate entry/exit cards
    if result.trades:
        entry_exit_cards_html = generate_entry_exit_cards(result.trades)
    else:
        entry_exit_cards_html = '<p style="color: #8b949e;">No trades to display</p>'

    config_html = ""
    for key, value in config.items():
        config_html += f"<p><strong>{key}:</strong> {value}</p>"

    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Backtest Report - {config.get("strategy", "Strategy")}</title>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: #0d1117;
            color: #c9d1d9;
            padding: 20px;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        h1 {{
            color: #58a6ff;
            margin-bottom: 20px;
            font-size: 28px;
        }}
        h2 {{
            color: #8b949e;
            margin: 20px 0 10px;
            font-size: 18px;
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }}
        .metric-card {{
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 8px;
            padding: 15px;
        }}
        .metric-label {{
            color: #8b949e;
            font-size: 12px;
            text-transform: uppercase;
        }}
        .metric-value {{
            font-size: 24px;
            font-weight: 600;
            margin-top: 5px;
        }}
        .positive {{ color: #3fb950; }}
        .negative {{ color: #f85149; }}
        .chart-container {{
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 20px;
        }}
        .config-box {{
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 20px;
        }}
        .config-box p {{
            margin: 5px 0;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }}
        th, td {{
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #30363d;
        }}
        th {{
            background: #21262d;
            color: #8b949e;
            font-size: 12px;
            text-transform: uppercase;
        }}
        tr:hover {{
            background: #21262d;
        }}
        .timestamp {{
            color: #8b949e;
            font-size: 12px;
            margin-top: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Backtest Report: {config.get("strategy", "Strategy")}</h1>

        <div class="config-box">
            <h2>Strategy Configuration</h2>
            {config_html}
        </div>

        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-label">Total Trades</div>
                <div class="metric-value">{metrics["total_trades"]}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Win Rate</div>
                <div class="metric-value">{metrics["win_rate"]:.1f}%</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Total P&L</div>
                <div class="metric-value {'positive' if metrics['total_pnl'] >= 0 else 'negative'}">
                    ₹{metrics["total_pnl"]:,.2f}
                </div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Return</div>
                <div class="metric-value {'positive' if metrics['return_percent'] >= 0 else 'negative'}">
                    {metrics["return_percent"]:.2f}%
                </div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Max Drawdown</div>
                <div class="metric-value negative">{metrics["max_drawdown"]:.2f}%</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Final Equity</div>
                <div class="metric-value">₹{metrics["final_equity"]:,.2f}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Winning Trades</div>
                <div class="metric-value positive">{metrics["winning_trades"]}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Losing Trades</div>
                <div class="metric-value negative">{metrics["losing_trades"]}</div>
            </div>
        </div>

        <div class="chart-container">
            <h2>Price Chart with Signals</h2>
            <div id="priceChart"></div>
        </div>

        <div class="chart-container">
            <h2>Equity Curve</h2>
            <div id="equityChart"></div>
        </div>

        <div class="chart-container">
            <h2>Drawdown</h2>
            <div id="drawdownChart"></div>
        </div>

        <div class="chart-container">
            <h2>Trade History</h2>
            <table>
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Entry Time</th>
                        <th>Entry Price</th>
                        <th>Exit Time</th>
                        <th>Exit Price</th>
                        <th>Lots</th>
                        <th>P&L</th>
                        <th>P&L %</th>
                    </tr>
                </thead>
                <tbody>
                    {trades_html if trades_html else "<tr><td colspan='8'>No trades executed</td></tr>"}
                </tbody>
            </table>
        </div>

        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-label">Entry & Exit Details</div>
                <div style="margin-top: 15px; font-size: 13px;">
                    {entry_exit_cards_html}
                </div>
            </div>
        </div>

        <p class="timestamp">Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
    </div>

    <script>
        const layout = {{
            paper_bgcolor: '#161b22',
            plot_bgcolor: '#161b22',
            font: {{ color: '#c9d1d9' }},
            xaxis: {{
                gridcolor: '#30363d',
                linecolor: '#30363d'
            }},
            yaxis: {{
                gridcolor: '#30363d',
                linecolor: '#30363d'
            }},
            margin: {{ t: 20, r: 20, b: 40, l: 60 }}
        }};

        // Price Chart
        Plotly.newPlot('priceChart', [
            {{
                x: {candle_dates},
                y: {closes},
                type: 'scatter',
                mode: 'lines',
                name: 'Price',
                line: {{ color: '#58a6ff', width: 1 }}
            }},
            {{
                x: {buy_dates},
                y: {buy_prices},
                type: 'scatter',
                mode: 'markers',
                name: 'Buy',
                marker: {{ color: '#3fb950', size: 10, symbol: 'triangle-up' }}
            }},
            {{
                x: {sell_dates},
                y: {sell_prices},
                type: 'scatter',
                mode: 'markers',
                name: 'Sell',
                marker: {{ color: '#f85149', size: 10, symbol: 'triangle-down' }}
            }}
        ], {{...layout, height: 400}});

        // Equity Curve
        Plotly.newPlot('equityChart', [{{
            x: {equity_dates},
            y: {equity_values},
            type: 'scatter',
            mode: 'lines',
            fill: 'tozeroy',
            line: {{ color: '#3fb950', width: 2 }},
            fillcolor: 'rgba(63, 185, 80, 0.1)'
        }}], {{...layout, height: 300}});

        // Drawdown
        Plotly.newPlot('drawdownChart', [{{
            x: {drawdown_dates},
            y: {drawdown_values},
            type: 'scatter',
            mode: 'lines',
            fill: 'tozeroy',
            line: {{ color: '#f85149', width: 2 }},
            fillcolor: 'rgba(248, 81, 73, 0.1)'
        }}], {{...layout, height: 250, yaxis: {{...layout.yaxis, autorange: 'reversed'}}}});
    </script>
</body>
</html>
    """

    with open(output_path, "w") as f:
        f.write(html)

    return os.path.abspath(output_path)
