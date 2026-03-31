import pandas as pd
from src.utils.logger import app_logger

class MemeRocketSniper:
    """PROSOFT AI: Hyper-Volatility & Meme Rocket Sniper"""
    
    def __init__(self, api_wrapper):
        self.api = api_wrapper
        
    def detect_rocket(self, df, symbol):
        """
        Detects if a coin is 'mooning' or having a sudden liquidity surge.
        Criteria: Volume is > 5x the average of the last 20 candles and price is surging.
        """
        if df is None or len(df) < 20: return None
        
        recent = df.tail(20)
        avg_volume = recent['volume'].mean()
        curr_volume = df.iloc[-1]['volume']
        curr_price_change = ((df.iloc[-1]['close'] - df.iloc[-1]['open']) / df.iloc[-1]['open']) * 100
        
        # Rocket Criteria: Volume Spike > 500% AND Price Surge > 2% in one candle
        if curr_volume > (avg_volume * 5.0) and curr_price_change > 2.0:
            app_logger.critical(f"🚀 [ROCKET SNIPER] EXPLOSIVE MOMENTUM DETECTED ON {symbol}!")
            app_logger.info(f"   └─ Volume Surge: {((curr_volume/avg_volume)-1)*100:.0f}% | Price: +{curr_price_change:.2f}%")
            
            # Return entry protocol
            return {
                'signal': 'ROCKET_BUY',
                'entry_price': df.iloc[-1]['close'],
                'target_profit': 5.0, # Aggressive 5% target for rockets
                'emergency_sl': 0.4   # Balanced 0.4% Stop loss for memes (Expert scale)
            }
        return None
