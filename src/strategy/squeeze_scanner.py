"""
squeeze_scanner.py — PROSOFT Volatility Squeeze Scanner v1.0
============================================================
يرصد ضغط بولينجر باند (BB Squeeze) عبر قائمة عملات ثم يصطاد
الانفجار السعري الفعلي (Breakout) فور اختراق النطاق العلوي.

المنطق:
  - عندما ينضغط BB_WIDTH إلى أدنى من 72% من متوسطه = سوق يتنفس
    ويتجمع قبل الانفجار.
  - الانفجار يتأكد حين يخترق السعر BB_UPPER مع حجم تداول كافٍ.

الهدف: +0.8% إلى +2.0% في 5-15 دقيقة.
SL:    0.4% أو ATR-based — أيهما أوسع.
"""

import time
import pandas as pd
from src.utils.logger import app_logger


class VolatilitySqueezeScanner:
    """
    يمسح قائمة أزواج USDT بحثاً عن فرص انفجار ما بعد الضغط (Squeeze Breakout).
    يُستخدم على إطار 5m ويُنفَّذ بالتوازي مع محركات الاستراتيجية الأخرى.
    """

    def __init__(self, api_client, ta_engine):
        self.api              = api_client
        self.ta               = ta_engine
        self.profit_target_pct = 0.012   # 1.2% هدف ربح
        self.stop_loss_pct     = 0.004   # 0.4% وقف خسارة
        self._hit_cache        = {}      # كاش لمنع الدخول المتكرر (5 دقائق cooldown)

    # ─────────────────────────────────────────────
    # الفحص الداخلي لعملة واحدة
    # ─────────────────────────────────────────────
    def _check(self, df: pd.DataFrame, symbol: str) -> dict | None:
        """
        يفحص عملة واحدة: هل هي في ضغط وتكسر للأعلى الآن؟
        يعيد dict بمعاملات الصفقة أو None إذا لم تُستوف الشروط.
        """
        if df is None or len(df) < 30:
            return None

        try:
            curr = df.iloc[-1]
            prev = df.iloc[-2]

            close     = float(curr['close'])
            bb_upper  = float(curr.get('BB_UPPER', close * 1.01))
            bb_width  = float(curr.get('BB_WIDTH', 0.02))
            rsi       = float(curr.get('RSI', 50))
            volume    = float(curr.get('volume', 0))
            vol_sma   = float(curr.get('VOLUME_SMA', volume if volume > 0 else 1))
            atr       = float(curr.get('ATR', close * 0.008))

            prev_close    = float(prev['close'])
            prev_bb_upper = float(prev.get('BB_UPPER', bb_upper))

            # ── متوسط BB_WIDTH لآخر 20 شمعة (مقياس مدى الضغط) ──
            if 'BB_WIDTH' in df.columns:
                bb_width_avg = float(df['BB_WIDTH'].tail(20).mean())
            else:
                bb_width_avg = bb_width  # لا مقارنة ممكنة

            # ── الشرط 1: ضغط متراكم ──
            is_squeezed = bb_width < bb_width_avg * 0.72

            # ── الشرط 2: كسر للأعلى الآن (الشمعة الحالية كسرت والسابقة لم تكسر) ──
            is_breaking = close > bb_upper and prev_close <= prev_bb_upper

            # ── الشرط 3: حجم تداول يؤكد الاندفاع ──
            vol_surge = volume > vol_sma * 1.5 if vol_sma > 0 else False

            # ── الشرط 4: RSI في منطقة الزخم (لم يصل الإرهاق) ──
            rsi_ok = 48 <= rsi <= 78

            if is_squeezed and is_breaking and vol_surge and rsi_ok:
                tp = close + max(atr * 1.5, close * self.profit_target_pct)
                sl = close - max(atr * 0.8, close * self.stop_loss_pct)

                app_logger.critical(
                    f"💥 [SQUEEZE BREAKOUT] {symbol}: "
                    f"BB_Width={bb_width:.4f} (avg={bb_width_avg:.4f}) | "
                    f"Vol×{volume/max(vol_sma,1):.1f} | RSI={rsi:.0f} | "
                    f"Entry={close:.6f} TP={tp:.6f} SL={sl:.6f}"
                )

                return {
                    'signal':      'BUY',
                    'entry_price': close,
                    'take_profit': round(tp, 8),
                    'stop_loss':   round(sl, 8),
                    'rr_ratio':    round((tp - close) / (close - sl), 2) if close > sl else 0,
                    'confidence':  0.83,
                    'strategy':    'Squeeze Breakout',
                    'indicators':  {
                        'Strategy':  'Squeeze Breakout',
                        'BB_Width':  round(bb_width, 4),
                        'BB_Avg':    round(bb_width_avg, 4),
                        'RSI':       round(rsi, 1),
                        'Vol_X':     round(volume / max(vol_sma, 1), 2),
                        'Source':    'SqueezeScanner',
                        'Pattern':   'BB Squeeze Breakout',
                    }
                }

        except Exception as e:
            app_logger.error(f"[SQUEEZE] Check error for {symbol}: {e}")

        return None

    # ─────────────────────────────────────────────
    # المسح الشامل عبر قائمة عملات
    # ─────────────────────────────────────────────
    def scan(self, symbols: list, get_klines_fn, calculate_indicators_fn) -> list:
        """
        يمسح قائمة من الرموز ويعيد قائمة مرتبة بالثقة من الأعلى.

        المعاملات:
          symbols               — قائمة رموز مثل ['BTCUSDT', 'ETHUSDT', ...]
          get_klines_fn         — دالة تجلب OHLCV (مثل self.api.get_historical_klines)
          calculate_indicators_fn — دالة تحسب المؤشرات (مثل self.ta.calculate_indicators)
        """
        hits = []

        for sym in symbols:
            # تجاهل العملة إذا اكتُشفت في آخر 5 دقائق (cooldown)
            if time.time() - self._hit_cache.get(sym, 0) < 300:
                continue

            try:
                df = get_klines_fn(sym, '5m', limit=60)
                if df is None or df.empty:
                    continue

                df     = calculate_indicators_fn(df)
                result = self._check(df, sym)

                if result:
                    result['symbol'] = sym
                    self._hit_cache[sym] = time.time()
                    hits.append(result)

            except Exception as e:
                app_logger.error(f"[SQUEEZE SCAN] {sym}: {e}")

        # ترتيب تنازلي حسب الثقة
        return sorted(hits, key=lambda x: x.get('confidence', 0), reverse=True)
