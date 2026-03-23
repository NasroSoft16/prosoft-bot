"""
fear_greed_integration.py — PROSOFT Fear & Greed Mode Enhancer
==============================================================
يعمل فوق GlobalMacroFilter الموجود لتحويل مؤشر الخوف والطمع
إلى تعديلات فعلية على حجم الصفقة وهدف الربح.

الفكرة: "اشترِ بكثرة حين يخاف الناس، واحذر حين يطمعون."
— وارن بافت

Usage:
    from src.ai.fear_greed_integration import FearGreedIntegration
    fg = FearGreedIntegration(bot.macro_filter)

    params = fg.adjust_trade_params(base_size=100.0, base_tp_pct=2.0)
    trade_size  = params['size']          # حجم الصفقة المعدَّل
    take_profit = params['take_profit']   # هدف الربح المعدَّل (%)
    state       = params['state_ar']      # الحالة بالعربية
"""

from src.utils.logger import app_logger

# ─── Market state configuration ──────────────────────────────────────────────
# FGI range → (size_multiplier, tp_multiplier)
# في الخوف: نشتري أكثر ونأخذ ربحاً أسرع
# في الطمع: نكون أكثر حذراً ونسمح بأهداف أكبر
_MARKET_STATES = [
    # (max_fgi, state_key, size_mult, tp_mult, name_ar)
    ( 20, 'extreme_fear',  1.5, 0.8,  'خوف شديد 😱'),
    ( 40, 'fear',          1.2, 0.9,  'خوف 😰'),
    ( 60, 'neutral',       1.0, 1.0,  'محايد 😐'),
    ( 80, 'greed',         0.8, 1.1,  'طمع 🤑'),
    (100, 'extreme_greed', 0.5, 1.2,  'طمع شديد 🔥'),
]
# ─────────────────────────────────────────────────────────────────────────────


def _classify(fgi: int) -> tuple:
    """Return (state_key, size_multiplier, tp_multiplier, arabic_name)."""
    for max_val, key, size_m, tp_m, name_ar in _MARKET_STATES:
        if fgi <= max_val:
            return key, size_m, tp_m, name_ar
    return 'neutral', 1.0, 1.0, 'محايد 😐'


class FearGreedIntegration:
    """
    Reads the Fear & Greed Index already computed by GlobalMacroFilter
    and returns adjusted trade parameters accordingly.

    Designed to use the *already-cached* FGI from macro_filter.macro_state
    (updated every 10 loops in main.py), so it adds zero API calls.
    """

    def __init__(self, macro_filter):
        """
        Parameters
        ----------
        macro_filter : GlobalMacroFilter instance (from bot.macro_filter)
        """
        self.macro_filter = macro_filter

    def get_fgi(self) -> int:
        """
        Returns the latest Fear & Greed Index (0–100) from macro_filter cache.
        Falls back to 50 (neutral) if unavailable.
        """
        try:
            return int(self.macro_filter.macro_state.get('fear_greed_index', 50))
        except Exception:
            return 50

    def adjust_trade_params(self, base_size: float, base_tp_pct: float) -> dict:
        """
        Adjust trade size and take-profit percentage based on market sentiment.

        Parameters
        ----------
        base_size   : float — base trade size in USDT (e.g. 100.0)
        base_tp_pct : float — base take-profit percentage (e.g. 2.0 means 2%)

        Returns
        -------
        dict with keys:
            size         : float — adjusted USDT trade size
            take_profit  : float — adjusted TP percentage
            state        : str   — market state key
            state_ar     : str   — market state in Arabic
            fgi          : int   — current Fear & Greed Index (0–100)
            size_mult    : float — the multiplier applied to size
            tp_mult      : float — the multiplier applied to TP
        """
        fgi                         = self.get_fgi()
        state, size_m, tp_m, name_ar = _classify(fgi)

        adjusted_size = round(base_size   * size_m, 2)
        adjusted_tp   = round(base_tp_pct * tp_m,   3)

        app_logger.info(
            f"[FearMode] FGI={fgi} | {name_ar} | "
            f"Size: ${base_size:.2f} → ${adjusted_size:.2f} ({size_m}x) | "
            f"TP: {base_tp_pct}% → {adjusted_tp}% ({tp_m}x)"
        )

        return {
            'size':        adjusted_size,
            'take_profit': adjusted_tp,
            'state':       state,
            'state_ar':    name_ar,
            'fgi':         fgi,
            'size_mult':   size_m,
            'tp_mult':     tp_m
        }

    def get_summary(self) -> str:
        """Short human-readable summary for dashboard/logs."""
        fgi                         = self.get_fgi()
        state, size_m, tp_m, name_ar = _classify(fgi)
        return f"FGI {fgi}/100 — {name_ar} (حجم ×{size_m}, TP ×{tp_m})"
