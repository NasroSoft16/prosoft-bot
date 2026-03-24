"""
manipulation_shield.py — PROSOFT Market Manipulation Detector
درع التلاعب: يكشف 5 أنواع من التلاعب قبل الدخول.
"""

import pandas as pd
from src.utils.logger import app_logger


class ManipulationShield:
    """
    Detects manipulation before entry. Run analyze() before every BUY.
    Also tracks order book history for spoofing detection.
    """

    def __init__(self):
        self._prev_bid_walls = set()   # previous top bids for spoofing check
        self._prev_ask_walls = set()

    # ── Main analysis ─────────────────────────────────────────────────────

    def analyze(self, df) -> dict:
        """
        Runs all candle-based manipulation checks.
        Returns {'is_safe': bool, 'reason': str, 'checks': dict}
        """
        if df is None or len(df) < 10:
            return {'is_safe': True, 'reason': 'Insufficient data', 'checks': {}}

        checks = {}

        try:
            curr = df.iloc[-1]
            prev = df.iloc[-2]

            body        = abs(float(curr['close']) - float(curr['open']))
            upper_wick  = float(curr['high']) - max(float(curr['close']), float(curr['open']))
            lower_wick  = min(float(curr['close']), float(curr['open'])) - float(curr['low'])

            # ── Check 1: Wick Trap (Pump & Dump candle) ──────────────────
            if body > 0 and upper_wick > (body * 3.5):
                checks['wick_trap'] = True
                return {
                    'is_safe': False,
                    'reason':  f'Wick Trap: upper wick {upper_wick:.4f} >> body {body:.4f}',
                    'checks':  checks
                }
            checks['wick_trap'] = False

            # ── Check 2: Fake Breakout ────────────────────────────────────
            prev_high = float(df['high'].iloc[-6:-1].max())
            if float(curr['high']) > prev_high and float(curr['close']) < prev_high * 0.998:
                checks['fake_breakout'] = True
                return {
                    'is_safe': False,
                    'reason':  f'Fake Breakout: touched {curr["high"]:.4f}, closed below {prev_high:.4f}',
                    'checks':  checks
                }
            checks['fake_breakout'] = False

            # ── Check 3: Volume Divergence (rising price, falling volume) ─
            vol_sma = float(df['volume'].iloc[-10:].mean())
            if (float(curr['close']) > float(prev['close'])
                    and float(curr['volume']) < vol_sma * 0.45):
                checks['vol_divergence'] = True
                return {
                    'is_safe': False,
                    'reason':  f'Volume Divergence: price up but vol {curr["volume"]:.0f} < avg {vol_sma:.0f}',
                    'checks':  checks
                }
            checks['vol_divergence'] = False

            # ── Check 4: Rapid Pump (3+ big green candles + low vol) ──────
            last_3     = df.tail(3)
            all_green  = all(last_3['close'] > last_3['open'])
            avg_change = ((last_3['close'] - last_3['open']) / last_3['open'] * 100).mean()
            if all_green and avg_change > 1.8 and float(curr['volume']) < vol_sma * 0.55:
                checks['rapid_pump'] = True
                return {
                    'is_safe': False,
                    'reason':  f'Pump Pattern: 3 green candles avg +{avg_change:.1f}% + weak volume',
                    'checks':  checks
                }
            checks['rapid_pump'] = False

            # ── Check 5: Shooting Star / Doji at resistance ───────────────
            # Star: small body at bottom, huge upper wick
            if body > 0:
                candle_range = float(curr['high']) - float(curr['low'])
                if candle_range > 0 and (upper_wick / candle_range) > 0.65 and body < candle_range * 0.25:
                    checks['shooting_star'] = True
                    return {
                        'is_safe': False,
                        'reason':  'Shooting Star: rejection at highs',
                        'checks':  checks
                    }
            checks['shooting_star'] = False

        except Exception as e:
            app_logger.error(f"[SHIELD] Candle check error: {e}")

        return {'is_safe': True, 'reason': 'Clean — no patterns detected.', 'checks': checks}

    # ── Order Book Spoofing Detection ─────────────────────────────────────

    def check_orderbook_spoofing(self, order_book_analysis: dict) -> dict:
        """
        Detects spoofing: large bid/ask walls that appear and vanish.
        Call with the output from OrderFlowAnalyzer.analyze_order_book().
        """
        if not order_book_analysis:
            return {'is_safe': True, 'reason': 'No order book data'}

        current_buys = {w['price'] for w in order_book_analysis.get('buy_walls', [])}
        current_asks = {w['price'] for w in order_book_analysis.get('sell_walls', [])}

        # Spoofing = large walls visible last scan, now gone without execution
        vanished_bids = self._prev_bid_walls - current_buys
        vanished_asks = self._prev_ask_walls - current_asks

        self._prev_bid_walls = current_buys
        self._prev_ask_walls = current_asks

        if len(vanished_bids) >= 2:
            return {
                'is_safe': False,
                'reason':  f'BID SPOOFING: {len(vanished_bids)} large buy walls vanished (fake support)',
            }
        if len(vanished_asks) >= 2:
            return {
                'is_safe': False,
                'reason':  f'ASK SPOOFING: {len(vanished_asks)} large sell walls vanished (fake resistance)',
            }

        return {'is_safe': True, 'reason': 'Order book appears genuine'}

    # ── Combined gate ─────────────────────────────────────────────────────

    def full_check(self, df, order_book_analysis=None) -> dict:
        """
        Run all checks. Returns first failure or overall safe.
        Use this in main.py before entering any trade.
        """
        candle_result = self.analyze(df)
        if not candle_result['is_safe']:
            return candle_result

        if order_book_analysis:
            ob_result = self.check_orderbook_spoofing(order_book_analysis)
            if not ob_result['is_safe']:
                return ob_result

        return {'is_safe': True, 'reason': 'All checks passed'}
