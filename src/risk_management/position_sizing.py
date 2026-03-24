"""
position_sizing.py — PROSOFT Sovereign Risk Engine v2
يحسب حجم الصفقة بناءً على:
  - نسبة المخاطرة الأساسية
  - مؤشر الخوف والطمع (FGI)
  - الخسائر المتتالية
  - مضاعف الثقة من AI
  - حماية رأس المال الصغير
"""

import os
from src.utils.logger import app_logger


class RiskManager:
    def __init__(
        self,
        risk_per_trade=0.012,
        max_daily_loss_pct=0.04,
        max_consecutive_losses=3,
    ):
        self.risk_per_trade          = float(os.getenv('RISK_PER_TRADE',       risk_per_trade))
        self.max_daily_loss_pct      = float(os.getenv('MAX_DAILY_LOSS_PCT',   max_daily_loss_pct))
        self.max_consecutive_losses  = int(os.getenv('MAX_CONSEC_LOSSES',      max_consecutive_losses))

        # Session trackers
        self.daily_pnl_pct           = 0.0
        self.consecutive_losses      = 0
        self.trades_today            = 0
        self._session_start_balance  = None

    # ── Position sizing ───────────────────────────────────────────────────

    def calculate_position_size(
        self,
        balance: float,
        price: float,
        stop_loss: float,
        ai_conf: float = 0.65,
        fgi: int = 50,
    ) -> float:
        """
        Full sovereign position sizing.

        Parameters
        ----------
        balance   : available USDT
        price     : current asset price
        stop_loss : calculated SL price
        ai_conf   : model confidence 0–1
        fgi       : Fear & Greed Index 0–100
        """
        try:
            if self._session_start_balance is None:
                self._session_start_balance = balance

            risk_distance = abs(price - stop_loss)
            if risk_distance <= 0:
                app_logger.warning("[RISK] SL distance = 0, skipping trade.")
                return 0.0

            # ── 1. Base risk amount ──────────────────────────────────────
            base_risk_usdt = balance * self.risk_per_trade

            # ── 2. AI confidence multiplier (0.7x – 1.3x) ───────────────
            #   conf=0.85 → 1.0x  | conf=0.95 → 1.18x  | conf=0.55 → 0.76x
            ai_mult = max(0.7, min(1.3, ai_conf / 0.85))

            # ── 3. Fear & Greed multiplier ───────────────────────────────
            #   Extreme Fear (<25) → buy more (contrarian)
            #   Extreme Greed (>80) → reduce exposure
            if fgi < 20:
                fgi_mult = 1.50
            elif fgi < 35:
                fgi_mult = 1.25
            elif fgi < 60:
                fgi_mult = 1.00
            elif fgi < 80:
                fgi_mult = 0.80
            else:
                fgi_mult = 0.55

            # ── 4. Consecutive loss reducer ──────────────────────────────
            if self.consecutive_losses == 1:
                loss_mult = 0.80
            elif self.consecutive_losses == 2:
                loss_mult = 0.60
            elif self.consecutive_losses >= 3:
                loss_mult = 0.40
            else:
                loss_mult = 1.00

            # ── 5. Compounding: reinvest a portion of profit ─────────────
            compound_mult = 1.0
            initial       = float(os.getenv('INITIAL_DEPOSIT', balance))
            if balance > initial * 1.05:
                profit_pct  = (balance - initial) / initial
                compound_mult = 1.0 + (profit_pct * float(os.getenv('COMPOUNDING_RATIO', 0.3)))
                compound_mult = min(compound_mult, 1.5)   # cap at 1.5×

            # ── 6. Combined risk amount ──────────────────────────────────
            final_risk_usdt = (
                base_risk_usdt
                * ai_mult
                * fgi_mult
                * loss_mult
                * compound_mult
            )

            position_size = final_risk_usdt / risk_distance

            # ── 7. Hard cap: never risk more than 95% of balance ─────────
            max_position  = (balance * 0.95) / price
            position_size = min(position_size, max_position)

            # ── 8. Micro-account: ensure Binance minimum ($10.5) ─────────
            min_qty = 10.5 / price
            if balance >= 10.5 and position_size < min_qty:
                position_size = min_qty

            total_cost = position_size * price
            if total_cost > balance * 0.95:
                position_size = (balance * 0.95) / price

            app_logger.info(
                f"[RISK] size={position_size:.6f} (${total_cost:.2f}) | "
                f"mults: ai={ai_mult:.2f} fgi={fgi_mult:.2f} "
                f"loss={loss_mult:.2f} comp={compound_mult:.2f}"
            )
            return max(0.0, position_size)

        except Exception as e:
            app_logger.error(f"[RISK] Sizing error: {e}")
            return 0.0

    # ── Session management ────────────────────────────────────────────────

    def update_performance(self, profit_loss_pct: float):
        self.daily_pnl_pct += profit_loss_pct
        if profit_loss_pct < 0:
            self.consecutive_losses += 1
        else:
            self.consecutive_losses = 0
        self.trades_today += 1

    def can_trade(self) -> bool:
        if self.daily_pnl_pct <= -self.max_daily_loss_pct:
            app_logger.warning(
                f"[RISK] Daily loss limit hit ({self.daily_pnl_pct:.2%}). Trading paused."
            )
            return False
        if self.consecutive_losses >= self.max_consecutive_losses:
            app_logger.warning(
                f"[RISK] {self.consecutive_losses} consecutive losses. Cooling down."
            )
            return False
        return True

    def reset_daily_stats(self):
        self.daily_pnl_pct      = 0.0
        self.consecutive_losses = 0
        self.trades_today       = 0
        self._session_start_balance = None
