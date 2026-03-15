"""
PROSOFT QUANTUM - درع التلاعب بالسوق (Manipulation Shield)
يكتشف فخاخ الحيتان، الضخ والتفريغ، والشموع المزيفة.
"""
import pandas as pd
from src.utils.logger import app_logger


class ManipulationShield:
    """Detects market manipulation patterns to protect the bot from traps."""

    def analyze(self, df):
        """
        Runs all manipulation checks on the current dataframe.
        Returns a dict with 'is_safe' bool and 'reason' string.
        """
        if df is None or len(df) < 10:
            return {'is_safe': True, 'reason': 'Insufficient data for shield check'}

        try:
            curr = df.iloc[-1]
            prev = df.iloc[-2]

            # --- CHECK 1: Wick Trap (فخ الفتيل / Pump & Dump Candle) ---
            # If the candle has a very long wick relative to its body (3:1 ratio), it's suspicious
            body = abs(curr['close'] - curr['open'])
            upper_wick = curr['high'] - max(curr['close'], curr['open'])
            lower_wick = min(curr['close'], curr['open']) - curr['low']
            
            if body > 0 and upper_wick > (body * 3):
                return {
                    'is_safe': False,
                    'reason': f'Wick Trap Detected: Extreme upper wick ({upper_wick:.2f}) vs body ({body:.2f}). Likely sell wall.'
                }

            # --- CHECK 2: Fake Breakout (اختراق وهمي) ---
            # Price briefly went above previous high, but closed below it (bear trap for longs)
            prev_high = df['high'].iloc[-6:-1].max()
            if curr['high'] > prev_high and curr['close'] < prev_high:
                return {
                    'is_safe': False,
                    'reason': f'Fake Breakout Detected: Price touched {curr["high"]:.2f} but closed below resistance at {prev_high:.2f}.'
                }

            # --- CHECK 3: Volume Divergence (تباين الحجم) ---
            # Price is rising but volume is falling — a classic distribution signal
            vol_sma = df['volume'].iloc[-10:].mean()
            if curr['close'] > prev['close'] and curr['volume'] < (vol_sma * 0.5):
                return {
                    'is_safe': False,
                    'reason': f'Volume Divergence: Price rising on weak volume ({curr["volume"]:.0f} vs avg {vol_sma:.0f}). Possible distribution.'
                }

            # --- CHECK 4: Rapid Consecutive Candles (ضخ متسارع) ---
            # 3+ consecutive big green candles followed by low volume = potential dump incoming
            last_3 = df.tail(3)
            all_green = all(last_3['close'] > last_3['open'])
            avg_change = ((last_3['close'] - last_3['open']) / last_3['open'] * 100).mean()
            if all_green and avg_change > 1.5 and curr['volume'] < (vol_sma * 0.6):
                return {
                    'is_safe': False,
                    'reason': f'Pump & Dump Pattern: 3 consecutive green candles (+{avg_change:.1f}% avg) with falling volume.'
                }

            app_logger.debug("Manipulation Shield: Market appears clean. Proceeding.")
            return {'is_safe': True, 'reason': 'No manipulation patterns detected.'}

        except Exception as e:
            app_logger.error(f"Manipulation Shield Error: {e}")
            return {'is_safe': True, 'reason': f'Shield Error (bypassed): {e}'}
