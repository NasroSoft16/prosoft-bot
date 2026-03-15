import os
import pandas as pd
from dotenv import load_dotenv
from src.api.binance_client import BinanceClientWrapper
from src.indicators.technical_analysis import TechnicalAnalysis
from src.ai.model_manager import ModelManager
from src.utils.logger import app_logger

load_dotenv()

def train_system(symbol='BTCUSDT', timeframe='1h', days=180):
    """Fetches historical data and trains the AI model."""
    app_logger.info(f"--- Training Start for {symbol} ({timeframe}) ---")
    
    api = BinanceClientWrapper()
    ta = TechnicalAnalysis()
    ai = ModelManager()
    
    # Calculate approximate count for given days
    # 1h = 24 candles per day
    limit = days * 24 
    
    app_logger.info(f"Fetching {limit} historical candles for training...")
    df = api.get_historical_klines(symbol, timeframe, limit=limit)
    
    if df is not None and not df.empty:
        app_logger.info(f"Retrieved {len(df)} candles. Calculating indicators...")
        df = ta.calculate_indicators(df)
        
        app_logger.info(f"Training AI Model (RandomForest) with {len(df)} samples...")
        success = ai.train_model(df, lookahead_period=24) # 24h lookahead
        
        if success:
            app_logger.info("--- Training Complete. Model saved to data/random_forest_model.pkl ---")
        else:
            app_logger.error("Training failed. Not enough data or error in calculations.")
    else:
        app_logger.error("Failed to fetch historical data for training.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Train the Trading Bot AI')
    parser.add_argument('--symbol', default='BTCUSDT', help='Trading symbol')
    parser.add_argument('--timeframe', default='1h', help='Candle interval')
    parser.add_argument('--days', type=int, default=180, help='Days of data to fetch')
    
    args = parser.parse_args()
    train_system(symbol=args.symbol, timeframe=args.timeframe, days=args.days)
