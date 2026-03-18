import pandas as pd
import ta
from src.utils.logger import app_logger

class TechnicalAnalysis:
    @staticmethod
    def calculate_indicators(df):
        """Calculates indicators for the given dataframe."""
        try:
            # EMA calculations (20, 50 and 200)
            df['EMA_20'] = ta.trend.ema_indicator(df['close'], window=20)
            df['EMA_50'] = ta.trend.ema_indicator(df['close'], window=50)
            df['EMA_200'] = ta.trend.ema_indicator(df['close'], window=200)

            # RSI calculation
            df['RSI'] = ta.momentum.rsi(df['close'], window=14)

            # MACD calculation
            df['MACD'] = ta.trend.macd(df['close'])
            df['MACD_SIGNAL'] = ta.trend.macd_signal(df['close'])
            df['MACD_HIST'] = ta.trend.macd_diff(df['close'])

            # ATR calculation for dynamic SL and TP
            df['ATR'] = ta.volatility.average_true_range(df['high'], df['low'], df['close'], window=14)

            # Volume SMA for volume spikes detection
            df['VOLUME_SMA'] = df['volume'].rolling(window=20).mean()

            # Distance to EMA for AI feature
            df['DIST_EMA_50'] = (df['close'] - df['EMA_50']) / df['EMA_50']
            
            # Smart Fill: Don't drop all rows if history is short.
            # Fill NaNs with current values or 0s to keep the dataframe size stable
            df.ffill(inplace=True)
            df.bfill(inplace=True) # Backfill the remaining 
            
            return df
        except Exception as e:
            app_logger.error(f"Error calculating indicators: {e}")
            return df # Return partially filled instead of None

    @staticmethod
    def is_volume_spike(df, row_index=-1, multiplier=1.5):
        """Detects if the volume is a spike compared to the SMA."""
        current_volume = df['volume'].iloc[row_index]
        volume_sma = df['VOLUME_SMA'].iloc[row_index]
        return current_volume > (volume_sma * multiplier)
