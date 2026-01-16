#Kafka read data for topic
docker exec -it kafka kafka-console-consumer --bootstrap-server kafka:9093 --topic candles_BINANCE_BTCUSDT --from-beginning --property print.key=true