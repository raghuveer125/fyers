#Kafka read data for topic
docker exec -it kafka kafka-console-consumer --bootstrap-server kafka:9093 --topic candles_BINANCE_BTCUSDT --from-beginning --property print.key=true



Back Testing:
# 1. Navigate to project directory
cd /Users/bhoomidakshpc/project1/StockAutoTradingVR/Fyers

# 2. Create virtual environment
python3 -m venv venv

# 3. Activate virtual environment
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Run the service
python -m fyers.backtesting.api
