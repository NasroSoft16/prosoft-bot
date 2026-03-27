"""
multi_timeframe.py — PROSOFT MTF Gate (MANDATORY entry filter)
==============================================================
يحلل 4 أطر زمنية بالتوازي ويتطلب توافق ≥55% قبل أي دخول.
يُستخدم كـ GATE إجبارية في main.py قبل كل إشارة شراء.
"""

import os
from src.utils.logger import app_logger

# ── Weights (shorter = noisier, less weight) ──────────────────────────────────
TIMEFRAMES = {
    '1m':  1,
    '5m':  3,
    '15m': 2,
    '1h':  2,
}

CONSENSUS_THRESHOLD = float(os.getenv('MTF_CONSENSUS_THRESHOLD', '0.55'))
# ─────────────────────────────────────────────────────────────────────────────


class MultiTimeframeAnalyzer:
    """
    Mandatory entry gate. Call `get_signal()` before every trade entry.
    Returns decision=BUY only when weighted consensus ≥ CONSENSUS_THRESHOLD.
    """

    def __init__(self, api, ta):
        self.api = api
        self.ta  = ta
        self.threshold = float(os.getenv('MTF_CONSENSUS_THRESHOLD', '0.55'))

    # ── Private ───────────────────────────────────────────────────────────────

    def _analyze_one(self, symbol: str, timeframe: str) -> dict:
        try:
            df = self.api.get_historical_klines(symbol, timeframe, limit=200)
            if df is None or df.empty or len(df) < 30:
                return {'timeframe': timeframe, 'signal': 'NEUTRAL',
                        'rsi': 50.0, 'error': True}

            df   = self.ta.calculate_indicators(df)
            curr = df.iloc[-1]

            rsi       = float(curr.get('RSI',       50.0))
            ema_fast  = float(curr.get('EMA_20',    curr.get('EMA_50',  0)))
            ema_slow  = float(curr.get('EMA_50',    curr.get('EMA_200', 0)))
            macd_hist = float(curr.get('MACD_HIST', 0.0))
            close     = float(curr['close'])

            # ── Signal classification ────────────────────────────────────
            signal = 'NEUTRAL'

            if rsi < 38 and ema_fast >= ema_slow and macd_hist > 0:
                signal = 'BUY'      # oversold + bullish trend
            elif rsi > 70 and ema_fast < ema_slow and macd_hist < 0:
                signal = 'SELL'     # overbought + bearish trend
            elif 42 <= rsi <= 72 and close > ema_fast > ema_slow and macd_hist > 0:
                signal = 'BUY'      # trend-ride zone (more aggressive)
            elif 38 <= rsi < 42 and macd_hist > 0 and close > ema_fast:
                signal = 'BUY'      # recovering from dip

            return {
                'timeframe': timeframe,
                'signal':    signal,
                'rsi':       round(rsi, 1),
                'ema_fast':  round(ema_fast, 6),
                'ema_slow':  round(ema_slow, 6),
                'macd_hist': round(macd_hist, 8),
                'close':     round(close, 6),
                'error':     False,
            }

        except Exception as e:
            app_logger.warning(f"[MTF] Error on {timeframe}: {e}")
            return {'timeframe': timeframe, 'signal': 'NEUTRAL',
                    'rsi': 50.0, 'error': True}

    # ── Public API ────────────────────────────────────────────────────────────

    def get_signal(self, symbol: str) -> dict:
        """
        Analyse all timeframes and return weighted consensus.

        Returns
        -------
        {
            decision   : 'BUY' | 'SELL' | 'HOLD'
            confidence : float 0–100
            buy_score  : float 0–100
            sell_score : float 0–100
            details    : {timeframe: analysis_dict}
            veto       : bool  (True = do NOT enter trade)
        }
        """
        app_logger.info(f"[MTF] Scanning {symbol} across {len(TIMEFRAMES)} timeframes...")

        details     = {}
        buy_weight  = 0
        sell_weight = 0
        total_w     = 0

        for tf, weight in TIMEFRAMES.items():
            result = self._analyze_one(symbol, tf)
            details[tf] = result
            total_w    += weight
            if result['signal'] == 'BUY':
                buy_weight  += weight
            elif result['signal'] == 'SELL':
                sell_weight += weight

        buy_score  = (buy_weight  / total_w) * 100 if total_w else 0
        sell_score = (sell_weight / total_w) * 100 if total_w else 0

        buy_ratio  = buy_weight  / total_w if total_w else 0
        sell_ratio = sell_weight / total_w if total_w else 0

        if buy_ratio >= self.threshold:
            decision   = 'BUY'
            confidence = buy_score
            veto       = False
        elif sell_ratio >= self.threshold:
            decision   = 'SELL'
            confidence = sell_score
            veto       = True   # no long entry when trend is down
        else:
            decision   = 'HOLD'
            confidence = max(buy_score, sell_score)
            veto       = True   # mixed signals = no trade

        log_parts = [f"{tf}:{d['signal']}({d['rsi']:.0f})" for tf, d in details.items()]
        app_logger.info(
            f"[MTF] {symbol} → {decision} ({confidence:.0f}%) | "
            + " | ".join(log_parts)
        )

        return {
            'decision':   decision,
            'confidence': round(confidence, 1),
            'buy_score':  round(buy_score, 1),
            'sell_score': round(sell_score, 1),
            'details':    details,
            'veto':       veto,
        }

    def is_entry_allowed(self, symbol: str) -> tuple:
        """
        Convenience gate for main.py:
            allowed, reason = mtf.is_entry_allowed('BTCUSDT')
            if not allowed: return

        Returns (True, '') or (False, reason_string).
        """
        if os.getenv('MTF_ENABLED', 'true').lower() == 'false':
            return True, "MTF DISABLED by .env bypass"

        result = self.get_signal(symbol)

        if result['veto']:
            reason = (
                f"MTF VETO: {result['decision']} "
                f"(buy={result['buy_score']:.0f}% sell={result['sell_score']:.0f}%)"
            )
            return False, reason

        return True, f"MTF OK: {result['confidence']:.0f}% consensus BUY"
