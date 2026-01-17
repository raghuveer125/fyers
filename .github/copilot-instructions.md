# Stock Auto Trading VR - AI Agent Instructions

## Architecture Overview

This is a real-time algorithmic trading system with backtesting capabilities. The architecture follows a **data ingestion → storage → backtesting → visualization** pipeline:

1. **Data Ingestion Layer** (`fyers/`, `binance/`) - WebSocket streams from Fyers/Binance → Kafka topics → PostgreSQL
2. **Kafka Streaming** - Centralized message broker for real-time candle data (topics: `candles_BINANCE_<symbol>`, `candles_FYERS_<symbol>_<timeframe>`)
3. **Storage** - PostgreSQL database (`fyers` DB) with `candles` table storing OHLCV data
4. **Backtesting Engine** (`fyers/backtesting/`) - Strategy testing framework with live simulation support
5. **REST API** (FastAPI on port 8000) - Exposes backtesting endpoints and report generation

## Critical Workflows

### Starting Services

```bash
# Start Kafka infrastructure (required first)
docker-compose up -d

# Start Fyers data stream (uses shell script pattern)
./start_fyers.sh

# Start Binance data stream
./start_binance.sh

# Start backtesting API
source venv/bin/activate
python -m fyers.backtesting.api
```

### Backtesting Workflow

```bash
# 1. Activate venv and run API
python -m fyers.backtesting.api

# 2. Call REST endpoints (curl/Postman)
POST /backtest/rsi
POST /backtest/macd
POST /backtest/rsi-macd

# 3. View HTML reports
GET /report/<filename>

# Reports are generated in: fyers/backtesting/reports/
```

### Debugging Kafka Data

```bash
# Inspect Kafka topics (via Docker exec)
docker exec -it kafka kafka-console-consumer \
  --bootstrap-server kafka:9093 \
  --topic candles_BINANCE_BTCUSDT \
  --from-beginning --property print.key=true

# Access Kafka UI: http://localhost:8080
```

## Database Schema

**PostgreSQL Connection Details:**
- Host: `localhost`, Port: `5432`
- User: `trader`, Password: `trader123`, DB: `fyers`

**`candles` Table Structure:**
```sql
timestamp (int), datetime (timestamp), symbol (text), timeframe (text),
open (float), high (float), low (float), close (float), volume (int)
```

Query pattern: `WHERE symbol = ? AND timeframe = ? ORDER BY timestamp ASC`

## Strategy Development Pattern

All strategies inherit from `Strategy` base class (`fyers/backtesting/strategies/base.py`). **Critical pattern:**

1. **Implement abstract methods:**
   - `on_candle(candle: Candle) -> Signal` - Core logic, return BUY/SELL/HOLD
   - `reset()` - Clear indicators and reset StrategyState
   - `get_config() -> dict` - Return strategy parameters for reporting

2. **State management:**
   - Use `self.state.position` (0=flat, 1=long) to track positions
   - Call `process_signal()` to handle trades automatically
   - Never manually modify `self.state.trades` or `self.state.equity`

3. **Indicator pattern (see `RSI` class in `rsi.py`):**
   ```python
   def __init__(self, config):
       self.gains = deque(maxlen=config.period)  # Use deque for rolling windows
       self.value = None
   
   def update(self, close: float) -> Optional[float]:
       # Calculate indicator, return None if insufficient data
       if len(self.gains) == self.config.period:
           # Compute value
       return self.value
   ```

4. **Config dataclass pattern:**
   ```python
   @dataclass
   class MyStrategyConfig:
       param1: int = 14
       param2: float = 70.0
   ```

## Project-Specific Conventions

### Candle Builder Pattern
Both Fyers and Binance use identical `CandleBuilder` classes for real-time OHLCV aggregation:
- Tick/trade data → time-bucketed candles
- `get_candle_start_time()` aligns timestamps to timeframe boundaries
- Publishes completed candles to Kafka with `"closed": true` flag

### Module Import Style
```python
# Always use relative imports within backtesting module
from .base import Strategy, Signal, Candle
from .strategies import RSIStrategy, MACDStrategy

# Absolute imports for external packages
from fastapi import FastAPI
import psycopg2
```

### Shell Script Pattern
Lifecycle scripts (`start_*.sh`, `stop_*.sh`) follow consistent pattern:
- PID file tracking for process management
- Log file redirection (`streamer.log`)
- Pre-flight checks for files/configs
- Graceful shutdown with SIGTERM

### API Response Structure
```python
# Success response pattern
{
    "status": "ok",
    "report_url": "/report/<filename>",
    "metrics": {...}
}

# Always include status, use HTTPException for errors
```

## Key Files Reference

- **[fyers/backtesting/api.py](fyers/backtesting/api.py)** - FastAPI endpoints, request models
- **[fyers/backtesting/engine.py](fyers/backtesting/engine.py)** - Core backtesting loop, DB queries
- **[fyers/backtesting/strategies/base.py](fyers/backtesting/strategies/base.py)** - Strategy interface, Signal enum, Trade dataclass
- **[fyers/backtesting/simulator.py](fyers/backtesting/simulator.py)** - Step-by-step live simulation for UI
- **[fyers/fyer_script_with_candles.py](fyers/fyer_script_with_candles.py)** - Fyers WebSocket client + OAuth flow
- **[docker-compose.yml](docker-compose.yml)** - Kafka/Zookeeper/Kafka-UI services

## External Dependencies

- **Fyers API**: OAuth2 flow via `fyers_apiv3`, uses `CLIENT_ID`, `SECRET_KEY`, `REDIRECT_URI` from `.env`
- **Binance WebSocket**: Public streams, no auth required
- **Kafka**: Internal listener `kafka:9093`, external `localhost:9092`
- **PostgreSQL**: Must be running separately (not in docker-compose)

## Testing Considerations

- No formal test suite exists - validation via backtesting reports
- To test strategies: run backtest via API → check HTML report metrics
- To verify data ingestion: query PostgreSQL or inspect Kafka topics
- Dashboard uses Plotly.js for equity curve / drawdown visualization
