"""
multi_timeframe.py — PROSOFT Adaptive MTF Gate v2.0
====================================================
🧠 INTELLIGENT DYNAMIC THRESHOLD ENGINE
بدلاً من حد ثابت (55%)، يتكيف المحرك ذاتياً بناءً على:
  1. نسبة الربح الحالية (Win Rate) → كلما ربحنا أكثر، انفتحنا أكثر
  2. فترة الجفاف (Drought) → إذا مرت 24 ساعة بدون صفقة، نخفف الشرط
  3. حالة السوق (FGI) → السوق الخائف يستحق حداً أقل صرامة للفرص النادرة
  4. عدد الصفقات الأخيرة → إذا كسبنا 3 متتالية نكون أجرأ، وإذا خسرنا 2 نتراجع

هذا يجعل البوت 'يتنفس' مع السوق بدلاً من الجمود الكامل.
"""

import os
import time
from src.utils.logger import app_logger

# ── Weights (shorter = noisier, less weight) ──────────────────────────────────
TIMEFRAMES = {
    '1m':  1,
    '5m':  3,
    '15m': 2,
    '1h':  2,
}

# ── Adaptive Threshold Boundaries ────────────────────────────────────────────
THRESHOLD_AGGRESSIVE = 0.30   # نفتح بـ 30% إجماع فقط (للصفقات الجيدة جداً)
THRESHOLD_NORMAL     = 0.50   # الحد الطبيعي الجديد (أقل من 0.55 السابق)
THRESHOLD_CAUTIOUS   = 0.65   # حد الحذر (بعد خسائر متتالية)
THRESHOLD_LOCKDOWN   = 0.80   # حد الإغلاق شبه الكامل (for very bad streaks)

# ── Drought Settings ─────────────────────────────────────────────────────────
DROUGHT_HOURS_TRIGGER = 12     # ساعات الجفاف قبل تخفيف الحد
DROUGHT_HOURS_MAX     = 36     # ساعات الجفاف لأقصى تخفيف


class MultiTimeframeAnalyzer:
    """
    Adaptive MTF Gate — يتكيف مع السوق ذاتياً.

    UPDATE CYCLE (يجب استدعاؤه من main.py):
        mtf.update_performance(win_rate, consecutive_wins, consecutive_losses,
                               last_trade_time, fgi)
    """

    def __init__(self, api, ta):
        self.api = api
        self.ta  = ta

        # State (يتم تحديثها من main.py)
        self.win_rate            = 0.50   # نسبة الربح (0.0 → 1.0)
        self.consecutive_wins    = 0      # عدد الانتصارات المتتالية
        self.consecutive_losses  = 0      # عدد الخسائر المتتالية
        self.last_trade_time     = 0      # timestamp آخر صفقة
        self.current_fgi         = 50     # مؤشر الخوف والطمع
        self.threshold           = THRESHOLD_NORMAL  # الحد الحالي الفعلي
        self._last_adapt_log     = 0      # منع تكرار اللوج

    # ── External State Feed ───────────────────────────────────────────────────

    def update_performance(self, win_rate: float, consecutive_wins: int,
                           consecutive_losses: int, last_trade_time: float,
                           fgi: int = 50):
        """
        يحدَّث من main.py في كل دورة لاتخاذ قرار الحد الديناميكي.
        """
        self.win_rate           = win_rate
        self.consecutive_wins   = consecutive_wins
        self.consecutive_losses = consecutive_losses
        self.last_trade_time    = last_trade_time
        self.current_fgi        = fgi
        # إعادة حساب الحد بعد كل تحديث
        self.threshold = self._calculate_dynamic_threshold()

    def _calculate_dynamic_threshold(self) -> float:
        """
        🧠 قلب المحرك الذكي — يحسب الحد المثالي بناءً على 4 محاور:

        المحور 1: نسبة الربح (Win Rate)
        المحور 2: فترة الجفاف (Drought)
        المحور 3: التسلسل (Streak)
        المحور 4: حالة السوق (FGI)
        """
        base = THRESHOLD_NORMAL  # نبدأ من 0.50

        # ── المحور 1: Win Rate ──────────────────────────────────────────────
        # كلما ارتفع معدل الربح، كلما تساهلنا في قبول الفرص
        if self.win_rate >= 0.70:
            base -= 0.12   # ربح عالٍ جداً → أجرأ (0.38)
        elif self.win_rate >= 0.60:
            base -= 0.07   # ربح جيد → انفتاح (0.43)
        elif self.win_rate >= 0.50:
            base -= 0.02   # ربح معتدل → تعديل طفيف (0.48)
        elif self.win_rate >= 0.40:
            base += 0.05   # ربح ضعيف → تشديد (0.55)
        else:
            base += 0.15   # خسارة مستمرة → حذر شديد (0.65)

        # ── المحور 2: Drought (فترة الجفاف) ────────────────────────────────
        hours_since_trade = (time.time() - self.last_trade_time) / 3600
        if hours_since_trade > DROUGHT_HOURS_MAX:
            # 36+ ساعة بدون صفقة → تخفيف اضطراري قوي
            drought_bonus = -0.15
            app_logger.info(f"🏜️ [MTF] Extreme drought ({hours_since_trade:.1f}h). Emergency threshold loosening.")
        elif hours_since_trade > DROUGHT_HOURS_TRIGGER:
            # 12-36 ساعة → تخفيف تدريجي
            ratio = (hours_since_trade - DROUGHT_HOURS_TRIGGER) / (DROUGHT_HOURS_MAX - DROUGHT_HOURS_TRIGGER)
            drought_bonus = -0.10 * ratio
        else:
            drought_bonus = 0.0
        base += drought_bonus

        # ── المحور 3: Consecutive Streak ────────────────────────────────────
        if self.consecutive_wins >= 3:
            base -= 0.05   # 3 انتصارات متتالية → ثقة متزايدة
        elif self.consecutive_wins >= 5:
            base -= 0.08   # 5+ انتصارات → العرّاب في تجواله! 🍷

        if self.consecutive_losses >= 3:
            base += 0.08   # 3 خسائر متتالية → توقف وتقييم
        elif self.consecutive_losses >= 5:
            base = THRESHOLD_LOCKDOWN  # 5+ خسائر → حالة طوارئ كاملة
            app_logger.warning("🚨 [MTF] 5+ consecutive losses detected. LOCKDOWN threshold activated!")

        # ── المحور 4: FGI (مؤشر الخوف والطمع) ─────────────────────────────
        if self.current_fgi <= 20:
            # رعب شديد → فرص ذهبية نادرة، خفف الحد!
            base -= 0.08
        elif self.current_fgi <= 35:
            # خوف عادي → تخفيف طفيف للبحث عن فرص
            base -= 0.04
        elif self.current_fgi >= 75:
            # طمع مفرط → خطر الشراء في القمة، شدد!
            base += 0.08

        # ── الحدود القصوى (حماية ضد التطرف) ───────────────────────────────
        final = round(min(THRESHOLD_LOCKDOWN, max(THRESHOLD_AGGRESSIVE, base)), 3)

        # سجّل التغيير إذا كان مختلفاً عن الحد الحالي
        if abs(final - self.threshold) > 0.01 or (time.time() - self._last_adapt_log) > 300:
            mode = self._get_mode_name(final)
            app_logger.info(
                f"🧠 [MTF ADAPTIVE] Threshold → {final:.2f} ({mode}) | "
                f"WinRate={self.win_rate:.0%} | "
                f"Drought={hours_since_trade:.1f}h | "
                f"Streak=+{self.consecutive_wins}/-{self.consecutive_losses} | "
                f"FGI={self.current_fgi}"
            )
            self._last_adapt_log = time.time()

        return final

    def _get_mode_name(self, threshold: float) -> str:
        """اسم بشري للحد الحالي."""
        if threshold <= 0.35:
            return "🟢 AGGRESSIVE"
        elif threshold <= 0.45:
            return "🔵 OPEN"
        elif threshold <= 0.55:
            return "🟡 NORMAL"
        elif threshold <= 0.65:
            return "🟠 CAUTIOUS"
        else:
            return "🔴 LOCKDOWN"

    # ── Private Analysis ──────────────────────────────────────────────────────

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

            signal = 'NEUTRAL'

            if rsi < 38 and ema_fast >= ema_slow and macd_hist > 0:
                signal = 'BUY'
            elif rsi > 70 and ema_fast < ema_slow and macd_hist < 0:
                signal = 'SELL'
            elif 42 <= rsi <= 72 and close > ema_fast > ema_slow and macd_hist > 0:
                signal = 'BUY'
            elif 38 <= rsi < 42 and macd_hist > 0 and close > ema_fast:
                signal = 'BUY'

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
        Analyse all timeframes using the CURRENT dynamic threshold.
        The threshold auto-adapts based on last update_performance() call.
        """
        app_logger.info(
            f"[MTF] Scanning {symbol} across {len(TIMEFRAMES)} timeframes "
            f"[Threshold: {self.threshold:.2f} | {self._get_mode_name(self.threshold)}]"
        )

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
            veto       = True
        else:
            decision   = 'HOLD'
            confidence = max(buy_score, sell_score)
            veto       = True

        log_parts = [f"{tf}:{d['signal']}({d['rsi']:.0f})" for tf, d in details.items()]
        app_logger.info(
            f"[MTF] {symbol} → {decision} ({confidence:.0f}%) "
            f"[need≥{self.threshold:.0%}] | " + " | ".join(log_parts)
        )

        return {
            'decision':   decision,
            'confidence': round(confidence, 1),
            'buy_score':  round(buy_score, 1),
            'sell_score': round(sell_score, 1),
            'details':    details,
            'veto':       veto,
            'threshold':  self.threshold,
        }

    def is_entry_allowed(self, symbol: str) -> tuple:
        """
        Convenience gate for main.py:
            allowed, reason = mtf.is_entry_allowed('BTCUSDT')
        """
        if os.getenv('MTF_ENABLED', 'true').lower() == 'false':
            return True, "MTF DISABLED by .env bypass"

        result = self.get_signal(symbol)

        if result['veto']:
            reason = (
                f"MTF VETO [{self._get_mode_name(self.threshold)}]: "
                f"{result['decision']} "
                f"(buy={result['buy_score']:.0f}% need≥{self.threshold:.0%})"
            )
            return False, reason

        return True, (
            f"MTF OK [{self._get_mode_name(self.threshold)}]: "
            f"{result['confidence']:.0f}% consensus BUY ✅"
        )
