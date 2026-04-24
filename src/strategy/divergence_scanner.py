"""
divergence_scanner.py — PROSOFT RSI Divergence Scanner v1.0
===========================================================
يكشف التباعد الصاعد (Bullish Divergence) بين السعر والـ RSI.

المنطق:
  - السعر يصنع قاعاً أدنى (Lower Low)  ↘
  - RSI  يصنع قاعاً أعلى (Higher Low)  ↗
  = ضغط البيع ينفد = الانعكاس وشيك

الهدف: +1.0% إلى +3.0% من الانعكاس.
الإطار الزمني: 15m (أدق تعريف للتباعد).
"""

import time
import pandas as pd
from src.utils.logger import app_logger


class RSIDivergenceScanner:
    """
    يمسح قائمة عملات على الإطار 15m ويكشف التباعد الصاعد.
    يُدمج مع بقية المحركات في main.py عبر دالة scan().
    """

    def __init__(self, api_client):
        self.api               = api_client
        self.lookback          = 20     # نطاق البحث عن القاعين بالشموع
        self.profit_target_pct = 0.015  # 1.5% هدف ربح
        self.stop_loss_pct     = 0.007  # 0.7% وقف خسارة
        self._cache            = {}     # cooldown 10 دقائق لكل عملة

    # ─────────────────────────────────────────────
    # أداة مساعدة: إيجاد القيعان المحلية
    # ─────────────────────────────────────────────
    def _local_lows(self, series: pd.Series, window: int = 3) -> list:
        """
        يجد القيعان المحلية في سلسلة زمنية.
        القاع المحلي = نقطة أقل من window جيران على كل جانب.
        يعيد قائمة tuples: [(index, value), ...]
        """
        data = list(series.astype(float))
        lows = []
        for i in range(window, len(data) - window):
            is_low = all(data[i] <= data[i - j] for j in range(1, window + 1)) and \
                     all(data[i] <= data[i + j] for j in range(1, window + 1))
            if is_low:
                lows.append((i, data[i]))
        return lows

    # ─────────────────────────────────────────────
    # كشف التباعد على عملة واحدة
    # ─────────────────────────────────────────────
    def detect(self, df: pd.DataFrame, symbol: str) -> dict | None:
        """
        يكشف التباعد الصاعد على آخر self.lookback شمعة.
        يعيد dict بمعاملات الصفقة أو None.
        """
        if df is None or len(df) < self.lookback + 5:
            return None

        try:
            # العمل على آخر lookback شمعة فقط
            subset     = df.tail(self.lookback).copy().reset_index(drop=True)
            close_vals = subset['close'].astype(float)
            rsi_col    = 'RSI' if 'RSI' in subset.columns else None
            rsi_vals   = subset[rsi_col].astype(float) if rsi_col else pd.Series([50.0] * len(subset))

            price_lows = self._local_lows(close_vals, window=2)
            rsi_lows   = self._local_lows(rsi_vals,   window=2)

            # نحتاج على الأقل قاعين في كلٍّ منهما
            if len(price_lows) < 2 or len(rsi_lows) < 2:
                return None

            # آخر قاعين للسعر والـ RSI
            p1_idx, p1_val = price_lows[-2]
            p2_idx, p2_val = price_lows[-1]
            r1_idx, r1_val = rsi_lows[-2]
            r2_idx, r2_val = rsi_lows[-1]

            # شرط التباعد: السعر أدنى + RSI أعلى
            price_lower_low = p2_val < p1_val * 0.9995   # هامش 0.05% للتسامح مع الضوضاء
            rsi_higher_low  = r2_val > r1_val + 1.0       # فرق RSI > 1 نقطة

            if not (price_lower_low and rsi_higher_low):
                return None

            # ─── مؤشرات جودة إضافية (تصفية الإشارات الضعيفة) ───
            curr    = df.iloc[-1]
            close   = float(curr['close'])
            rsi_now = float(curr.get('RSI', 50))
            cmf     = float(curr.get('CMF', 0))
            ema_50  = float(curr.get('EMA_50', 0))
            atr     = float(curr.get('ATR', close * 0.01))

            # RSI في منطقة التعافي (ليس إرهاقاً)
            rsi_recovering = 25 <= rsi_now <= 55
            # CMF لا يؤكد بيعاً مكثفاً
            cmf_neutral    = cmf > -0.18
            # السعر قريب أو فوق EMA_50 (لا ينهار كلياً)
            above_support  = close >= ema_50 * 0.985 if ema_50 > 0 else True

            if not (rsi_recovering and cmf_neutral):
                return None

            # قوة التباعد (كلما كان الفرق أكبر = ثقة أعلى)
            divergence_strength = (r2_val - r1_val) / max(r1_val, 1) * 100
            confidence          = round(min(0.88, 0.76 + divergence_strength / 200), 2)

            tp = close + max(atr * 2.0, close * self.profit_target_pct)
            sl = close - max(atr * 1.0, close * self.stop_loss_pct)

            app_logger.critical(
                f"📐 [RSI DIVERGENCE] {symbol}: "
                f"Price LL ({p1_val:.6f}→{p2_val:.6f}) | "
                f"RSI HL ({r1_val:.1f}→{r2_val:.1f}) | "
                f"Strength={divergence_strength:.1f}% | Conf={confidence:.0%}"
            )

            return {
                'signal':      'BUY',
                'entry_price': close,
                'take_profit': round(tp, 8),
                'stop_loss':   round(sl, 8),
                'rr_ratio':    round((tp - close) / (close - sl), 2) if close > sl else 0,
                'confidence':  confidence,
                'strategy':    'RSI Divergence',
                'indicators':  {
                    'Strategy':  'RSI Divergence',
                    'RSI_Low1':  round(r1_val, 1),
                    'RSI_Low2':  round(r2_val, 1),
                    'Strength':  round(divergence_strength, 1),
                    'Source':    'DivergenceScanner',
                    'Pattern':   f'Bullish Div ({p1_val:.4f}→{p2_val:.4f})',
                }
            }

        except Exception as e:
            app_logger.error(f"[DIVERGENCE] Detection error for {symbol}: {e}")

        return None

    # ─────────────────────────────────────────────
    # المسح الشامل عبر قائمة عملات
    # ─────────────────────────────────────────────
    def scan(self, symbols: list, get_klines_fn, calculate_indicators_fn) -> list:
        """
        يمسح قائمة من الرموز على الإطار 15m.
        يعيد قائمة مرتبة تنازلياً بالثقة.
        """
        hits = []

        for sym in symbols:
            # cooldown 10 دقائق لكل عملة
            if time.time() - self._cache.get(sym, 0) < 600:
                continue

            try:
                df = get_klines_fn(sym, '15m', limit=80)
                if df is None or df.empty:
                    continue

                df     = calculate_indicators_fn(df)
                result = self.detect(df, sym)

                if result:
                    result['symbol'] = sym
                    self._cache[sym] = time.time()
                    hits.append(result)

            except Exception as e:
                app_logger.error(f"[DIV SCAN] {sym}: {e}")

        return sorted(hits, key=lambda x: x.get('confidence', 0), reverse=True)
