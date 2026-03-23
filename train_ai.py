import os
import sys
import time
import schedule
import threading
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

# --- PROSOFT BOOTSTRAPPER (supports both embedded & system Python) ---
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
for _p in [os.path.join(ROOT_DIR, "python", "Lib", "site-packages"),
           os.path.join(ROOT_DIR, "libs"), ROOT_DIR]:
    if os.path.exists(_p) and _p not in sys.path:
        sys.path.insert(0, _p)

from src.api.binance_client import BinanceClientWrapper
from src.indicators.technical_analysis import TechnicalAnalysis
from src.ai.model_manager import ModelManager
from src.utils.logger import app_logger

load_dotenv()

# ─── Configuration ───────────────────────────────────────────────────────────
RETRAIN_SYMBOL    = os.getenv('SYMBOL',    'BTCUSDT')
RETRAIN_TIMEFRAME = os.getenv('TIMEFRAME', '1h')
RETRAIN_DAYS      = int(os.getenv('RETRAIN_DAYS', 180))
MIN_ACCURACY      = 0.55   # Only save model if accuracy exceeds this threshold
# ─────────────────────────────────────────────────────────────────────────────


def train_system(symbol=RETRAIN_SYMBOL, timeframe=RETRAIN_TIMEFRAME, days=RETRAIN_DAYS):
    """
    Core training routine.
    Fetches historical candles from Binance, calculates technical indicators,
    and trains the RandomForest model via ModelManager.
    The model is saved ONLY when test accuracy > MIN_ACCURACY.
    """
    app_logger.info(f"--- [AUTO-TRAIN] Re-training started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---")
    app_logger.info(f"[AUTO-TRAIN] Target: {symbol} | Timeframe: {timeframe} | History: {days} days")

    try:
        api = BinanceClientWrapper()
        ta  = TechnicalAnalysis()
        ai  = ModelManager()

        # 1h candles → 24 per day
        candles_per_day = {'1m': 1440, '5m': 288, '15m': 96, '1h': 24, '4h': 6, '1d': 1}
        limit = days * candles_per_day.get(timeframe, 24)
        limit = min(limit, 1000)  # Binance API cap

        app_logger.info(f"[AUTO-TRAIN] Fetching {limit} candles...")
        df = api.get_historical_klines(symbol, timeframe, limit=limit)

        if df is None or df.empty:
            app_logger.error("[AUTO-TRAIN] ❌ Failed to fetch data. Aborting.")
            return False

        app_logger.info(f"[AUTO-TRAIN] Received {len(df)} candles. Calculating indicators...")
        df = ta.calculate_indicators(df)

        app_logger.info(f"[AUTO-TRAIN] Training AI model (RandomForest)...")
        success = ai.train_model(df, lookahead_period=24)

        if success:
            app_logger.info("✅ [AUTO-TRAIN] Model updated and saved to data/random_forest_model.pkl")
        else:
            app_logger.warning("⚠️ [AUTO-TRAIN] Training failed — insufficient data or accuracy too low.")

        return success

    except Exception as e:
        app_logger.error(f"[AUTO-TRAIN] Exception during training: {e}")
        return False


def _scheduled_retrain():
    """Wrapper called by the scheduler — runs weekly retrain without crashing the thread."""
    try:
        app_logger.info("[AUTO-TRAIN] 🗓️ Scheduled weekly re-training triggered.")
        train_system()
    except Exception as e:
        app_logger.error(f"[AUTO-TRAIN] Scheduled retrain error: {e}")


def start_auto_retraining():
    """
    Starts the weekly auto-retraining scheduler.
    Designed to run in a background daemon thread from main.py:

        import threading
        from train_ai import start_auto_retraining
        threading.Thread(target=start_auto_retraining, daemon=True).start()

    Schedule: Every Sunday at 02:00 AM (Algerian time = server UTC+1).
    Checks every hour whether a scheduled task is due.
    """
    # Schedule weekly retrain every Sunday at 02:00
    schedule.every().sunday.at("02:00").do(_scheduled_retrain)
    app_logger.info("[AUTO-TRAIN] ✅ Scheduler armed: Re-training every Sunday at 02:00")

    while True:
        schedule.run_pending()
        time.sleep(3600)  # Check every hour


# ─── Direct execution ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='PROSOFT AI — Re-training Engine')
    parser.add_argument('--symbol',    default=RETRAIN_SYMBOL,    help='Trading symbol (e.g. BTCUSDT)')
    parser.add_argument('--timeframe', default=RETRAIN_TIMEFRAME, help='Candle interval (e.g. 1h)')
    parser.add_argument('--days',      type=int, default=RETRAIN_DAYS, help='Days of historical data')
    parser.add_argument('--schedule',  action='store_true', help='Keep running with weekly auto-schedule')
    args = parser.parse_args()

    # Run once immediately
    train_system(symbol=args.symbol, timeframe=args.timeframe, days=args.days)

    # Keep alive with weekly schedule if requested
    if args.schedule:
        app_logger.info("[AUTO-TRAIN] Entering scheduler mode...")
        start_auto_retraining()
