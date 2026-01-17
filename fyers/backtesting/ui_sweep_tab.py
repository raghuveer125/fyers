"""
Parameter Sweep UI Tab - Add to simulator-ui HTML
This section should be added after the closing </div> of simulatorArea and before </body>
"""

PARAMETER_SWEEP_TAB_HTML = """
        <div id="sweepArea" style="display:none;">
            <div style="padding: 20px;">
                <h2 style="color: #58a6ff; margin-bottom: 20px;">📊 MACD Parameter Sweep</h2>
                
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
                    <h3 style="color: #8b949e; margin-bottom: 15px;">Fast Period Range</h3>
                    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px;">
                        <div class="control-group">
                            <label>Start</label>
                            <input type="number" id="fastStart" value="8" min="2" max="50">
                        </div>
                        <div class="control-group">
                            <label>End</label>
                            <input type="number" id="fastEnd" value="24" min="2" max="50">
                        </div>
                        <div style="padding-top: 23px; color: #8b949e; font-size: 12px;">
                            Range: <strong id="fastRange">17</strong> values
                        </div>
                    </div>
                </div>

                <div style="background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 20px; margin-bottom: 20px;">
                    <h3 style="color: #8b949e; margin-bottom: 15px;">Slow Period Range</h3>
                    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px;">
                        <div class="control-group">
                            <label>Start</label>
                            <input type="number" id="slowStart" value="18" min="2" max="100">
                        </div>
                        <div class="control-group">
                            <label>End</label>
                            <input type="number" id="slowEnd" value="52" min="2" max="100">
                        </div>
                        <div style="padding-top: 23px; color: #8b949e; font-size: 12px;">
                            Range: <strong id="slowRange">35</strong> values
                        </div>
                    </div>
                </div>

                <div style="background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 20px; margin-bottom: 20px;">
                    <h3 style="color: #8b949e; margin-bottom: 15px;">Signal Period Range</h3>
                    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px;">
                        <div class="control-group">
                            <label>Start</label>
                            <input type="number" id="signalStart" value="5" min="2" max="50">
                        </div>
                        <div class="control-group">
                            <label>End</label>
                            <input type="number" id="signalEnd" value="12" min="2" max="50">
                        </div>
                        <div style="padding-top: 23px; color: #8b949e; font-size: 12px;">
                            Range: <strong id="signalRange">8</strong> values
                        </div>
                    </div>
                </div>

                <div style="background: #21262d; border-left: 4px solid #58a6ff; padding: 15px; margin-bottom: 20px; border-radius: 4px;">
                    <strong style="color: #c9d1d9;">Total Combinations:</strong> <span id="totalCombinations" style="color: #58a6ff; font-size: 18px; font-weight: 600;">4,760</span>
                </div>

                <div class="control-group" style="max-width: 200px;">
                    <label>Initial Capital</label>
                    <input type="number" id="sweepCapital" value="100000" min="1000">
                </div>

                <button class="btn btn-primary btn-large" id="runSweepBtn" onclick="runSweep()" style="width: 100%; margin-top: 20px;">
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

                        <div style="display: flex; gap: 10px;">
                            <a id="csvDownloadLink" href="#" class="btn btn-secondary" download>📊 Download CSV</a>
                            <a id="htmlReportLink" href="#" target="_blank" class="btn btn-secondary">📈 View Full Report</a>
                            <button class="btn btn-secondary" onclick="newSweep()">🔄 New Sweep</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <style>
            .tab-buttons {
                display: flex;
                gap: 10px;
                margin-bottom: 20px;
                border-bottom: 2px solid #30363d;
                padding-bottom: 0;
            }
            .tab-btn {
                padding: 12px 20px;
                border: none;
                background: transparent;
                color: #8b949e;
                cursor: pointer;
                font-size: 14px;
                font-weight: 600;
                border-bottom: 3px solid transparent;
                transition: all 0.2s;
            }
            .tab-btn.active {
                color: #58a6ff;
                border-bottom-color: #58a6ff;
            }
            .tab-btn:hover { color: #c9d1d9; }
        </style>
"""
