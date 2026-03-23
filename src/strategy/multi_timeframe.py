"""
multi_timeframe.py — PROSOFT Multi-Timeframe Analysis Engine
============================================================
تحليل 4 أطر زمنية في وقت واحد لتقليل الإشارات الكاذبة.
الإطار الزمني الأطول يأخذ وزناً أعلى في القرار النهائي.

Usage (from main.py or any module):
    from src.strategy.multi_timeframe import MultiTimeframeAnalyzer
    mtf = MultiTimeframeAnalyzer(binance_client_wrapper, technical_analysis)
    result = mtf.get_signal('BTCUSDT')
    # result = {'decision': 'BUY'|'SELL'|'HOLD', 'confidence': 70.0, ...}
"""

from src.utils.logger import app_logger

# ─── Timeframe weights (longer = more reliable) ───────────────────────────────
TIMEFRAMES = {
    '1m':  1,   # دقيقة  — وزن 1 (زخم لحظي)
    '5m':  3,   # 5 دقائق — وزن 3 (الأصل الجديد)
    '15m': 2,   # ربع ساعة — وزن 2 (تأكيد متوسط)
    '1h':  2,   # ساعة  — وزن 2 (فلتر الاتجاه القريب)
}

# Minimum weighted agreement needed to issue BUY/SELL (55% for Scalping)
CONSENSUS_THRESHOLD = 0.55
# ─────────────────────────────────────────────────────────────────────────────


class MultiTimeframeAnalyzer:
    """
    Analyses multiple timeframes and returns a weighted consensus signal.
    Plugs into the existing PROSOFT architecture via BinanceClientWrapper
    and TechnicalAnalysis.
    """

    def __init__(self, api, ta):
        """
        Parameters
        ----------
        api : BinanceClientWrapper   — existing Binance API wrapper
        ta  : TechnicalAnalysis      — existing indicator calculator
        """
        self.api = api
        self.ta  = ta

    # ── Private helpers ───────────────────────────────────────────────────────

    def _analyze_one(self, symbol: str, timeframe: str) -> dict:
        """
        Fetch candles for one timeframe, compute indicators,
        and classify the signal as BUY / SELL / NEUTRAL.
        """
        try:
            df = self.api.get_historical_klines(symbol, timeframe, limit=200)
            if df is None or df.empty or len(df) < 30:
                return {'timeframe': timeframe, 'signal': 'NEUTRAL', 'rsi': 50.0, 'error': True}

            df = self.ta.calculate_indicators(df)
            curr = df.iloc[-1]

            rsi       = float(curr.get('RSI',       50.0))
            ema_fast  = float(curr.get('EMA_9',     curr.get('EMA_50',  0)))
            ema_slow  = float(curr.get('EMA_50',    curr.get('EMA_200', 0)))
            macd_hist = float(curr.get('MACD_HIST', 0.0))

            # ── Signal logic ─────────────────────────────────────────────────
            signal = 'NEUTRAL'
            if rsi < 38 and ema_fast > ema_slow and macd_hist > 0:
                signal = 'BUY'   # oversold + bullish trend momentum
            elif rsi > 62 and ema_fast < ema_slow and macd_hist < 0:
                signal = 'SELL'  # overbought + bearish trend momentum

            return {
                'timeframe': timeframe,
                'signal':    signal,
                'rsi':       round(rsi, 1),
                'ema_fast':  round(ema_fast, 6),
                'ema_slow':  round(ema_slow, 6),
                'macd_hist': round(macd_hist, 6),
                'error':     False
            }

        except Exception as e:
            app_logger.warning(f"[MTF] Error on {timeframe}: {e}")
            return {'timeframe': timeframe, 'signal': 'NEUTRAL', 'rsi': 50.0, 'error': True}

    # ── Public API ────────────────────────────────────────────────────────────

    def get_signal(self, symbol: str) -> dict:
        """
        Analyse all configured timeframes and return a weighted consensus.

        Returns
        -------
        dict with keys:
            decision   : 'BUY' | 'SELL' | 'HOLD'
            confidence : float 0–100 (weighted agreement percentage)
            buy_score  : float 0–100
            sell_score : float 0–100
            details    : dict  {timeframe → analysis dict}
        """
        app_logger.info(f"[MTF] Analysing {symbol} across {len(TIMEFRAMES)} timeframes...")

        details     = {}
        buy_weight  = 0
        sell_weight = 0
        total_weight = sum(TIMEFRAMES.values())

        for tf, weight in TIMEFRAMES.items():
            result = self._analyze_one(symbol, tf)
            details[tf] = result

            if result['signal'] == 'BUY':
                buy_weight += weight
            elif result['signal'] == 'SELL':
                sell_weight += weight

            app_logger.info(
                f"[MTF]  [{tf}] {result['signal']} | RSI={result['rsi']}"
            )

        buy_pct  = buy_weight  / total_weight
        sell_pct = sell_weight / total_weight

        if buy_pct >= CONSENSUS_THRESHOLD:
            decision   = 'BUY'
            confidence = round(buy_pct  * 100, 1)
        elif sell_pct >= CONSENSUS_THRESHOLD:
            decision   = 'SELL'
            confidence = round(sell_pct * 100, 1)
        else:
            decision   = 'HOLD'
            confidence = round((1.0 - max(buy_pct, sell_pct)) * 100, 1)

        app_logger.info(
            f"[MTF] ▶ Decision: {decision} | Confidence: {confidence}% "
            f"(BUY {buy_pct*100:.0f}% vs SELL {sell_pct*100:.0f}%)"
        )

        return {
            'decision':   decision,
            'confidence': confidence,
            'buy_score':  round(buy_pct  * 100, 1),
            'sell_score': round(sell_pct * 100, 1),
            'details':    details
        }
