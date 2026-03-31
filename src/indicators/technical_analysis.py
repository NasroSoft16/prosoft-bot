import pandas as pd
import ta
from src.utils.logger import app_logger


class TechnicalAnalysis:
    @staticmethod
    def calculate_indicators(df):
        """Calculates ALL indicators needed by every strategy module."""
        try:
            # ── Fast EMAs (needed by BaseStrategy, MTF, MicroScalper) ──
            df['EMA_9']  = ta.trend.ema_indicator(df['close'], window=9)
            df['EMA_20'] = ta.trend.ema_indicator(df['close'], window=20)
            df['EMA_50'] = ta.trend.ema_indicator(df['close'], window=50)
            df['EMA_200'] = ta.trend.ema_indicator(df['close'], window=200)

            # ── RSI ──
            df['RSI'] = ta.momentum.rsi(df['close'], window=14)

            # ── MACD ──
            df['MACD']        = ta.trend.macd(df['close'])
            df['MACD_SIGNAL'] = ta.trend.macd_signal(df['close'])
            df['MACD_HIST']   = ta.trend.macd_diff(df['close'])

            # ── Stochastic RSI (Fast Momentum) ──
            df['STOCH_RSI'] = ta.momentum.stochrsi(df['close'], window=14, smooth1=3, smooth2=3)

            # ── CMF (Money Flow) ──
            df['CMF'] = ta.volume.chaikin_money_flow(df['high'], df['low'], df['close'], df['volume'], window=20)

            # ── VWAP (Institutional Bias) ──
            vwap = ta.volume.VolumeWeightedAveragePrice(df['high'], df['low'], df['close'], df['volume'], window=14)
            df['VWAP'] = vwap.volume_weighted_average_price()

            # ── ATR (dynamic SL / TP) ──
            df['ATR'] = ta.volatility.average_true_range(
                df['high'], df['low'], df['close'], window=14
            )

            # ── Volume ──
            df['VOLUME_SMA'] = df['volume'].rolling(window=20).mean()

            # ── EMA distance feature (AI model input) ──
            df['DIST_EMA_50'] = (df['close'] - df['EMA_50']) / df['EMA_50']

            # ── Bollinger Bands (for volatility squeeze detection) ──
            bb = ta.volatility.BollingerBands(df['close'], window=20, window_dev=2)
            df['BB_UPPER'] = bb.bollinger_hband()
            df['BB_LOWER'] = bb.bollinger_lband()
            df['BB_WIDTH'] = (df['BB_UPPER'] - df['BB_LOWER']) / df['close']

            # ── Momentum (rate of change) ──
            df['MOM_10'] = df['close'].pct_change(10) * 100

            # ── Smart fill ──
            df.ffill(inplace=True)
            df.bfill(inplace=True)

            return df

        except Exception as e:
            app_logger.error(f"Error calculating indicators: {e}")
            return df

    @staticmethod
    def is_volume_spike(df, row_index=-1, multiplier=1.5):
        """Detects volume spike vs rolling SMA."""
        try:
            current_volume = df['volume'].iloc[row_index]
            volume_sma     = df['VOLUME_SMA'].iloc[row_index]
            if volume_sma and volume_sma > 0:
                return current_volume > (volume_sma * multiplier)
        except Exception:
            pass
        return False

    @staticmethod
    def is_squeeze(df):
        """Bollinger Band squeeze = low volatility before explosive move."""
        try:
            return df['BB_WIDTH'].iloc[-1] < df['BB_WIDTH'].rolling(20).mean().iloc[-1] * 0.7
        except Exception:
            return False
