"""
circuit_breaker.py — PROSOFT Automatic Trading Circuit Breaker
=============================================================
قاطع الطوارئ الآلي — يوقف التداول تلقائياً إذا تجاوزت الخسائر الحدود المحددة.

يكمّل RiskManager الموجود (position_sizing.py) دون أن يحل محله:
- RiskManager: تحكم في حجم الصفقة الفردية
- CircuitBreaker: يوقف التداول الكلي عند خسائر خطيرة

الحالة تُحفظ في ملف JSON لتبقى فاعلة حتى بعد إعادة تشغيل البوت.

Usage:
    from src.risk_management.circuit_breaker import CircuitBreaker
    cb = CircuitBreaker()
    cb.set_balance(1000.0)          # يتم تحديثه من main.py

    if cb.can_trade():              # قبل كل صفقة
        ...execute trade...

    cb.record_result(profit=-25)    # بعد كل صفقة
"""

import os
import json
from datetime import date, datetime
from src.utils.logger import app_logger

# ─── Default limits (overridable via environment variables) ───────────────────
_MAX_DAILY_LOSS_PCT   = float(os.getenv('CB_MAX_DAILY_LOSS_PCT',   5.0))   # 5%
_MAX_CONSECUTIVE_LOSS = int(os.getenv('CB_MAX_CONSECUTIVE_LOSS',   5))
STATE_FILE = 'data/circuit_breaker_state.json'
# ─────────────────────────────────────────────────────────────────────────────


class CircuitBreaker:
    """
    Monitors daily P&L and consecutive losses.
    Trips (blocks all trading) if either limit is exceeded.
    Resets automatically at the start of each new day.
    """

    def __init__(self,
                 max_daily_loss_pct: float   = _MAX_DAILY_LOSS_PCT,
                 max_consecutive_loss: int   = _MAX_CONSECUTIVE_LOSS):

        self.max_daily_loss_pct   = max_daily_loss_pct
        self.max_consecutive_loss = max_consecutive_loss

        # Runtime state
        self.is_tripped         = False
        self.trip_reason        = None
        self.consecutive_losses = 0
        self.last_reset_date    = date.today()

        # Balance tracking (set from main.py via set_balance())
        self._session_start_balance = None
        self._current_balance       = None

        os.makedirs('data', exist_ok=True)
        self._load_state()
        app_logger.info(
            f"[CB] Circuit Breaker armed | "
            f"Daily loss limit: {self.max_daily_loss_pct}% | "
            f"Max consecutive losses: {self.max_consecutive_loss}"
        )

    # ── Persistence ───────────────────────────────────────────────────────────

    def _load_state(self):
        """Load persisted trip state so a restart doesn't bypass the breaker."""
        try:
            if os.path.exists(STATE_FILE):
                with open(STATE_FILE) as f:
                    state = json.load(f)

                saved_date = date.fromisoformat(state.get('date', str(date.today())))
                if saved_date == date.today():
                    self.is_tripped         = state.get('is_tripped', False)
                    self.consecutive_losses = state.get('consecutive_losses', 0)
                    self.trip_reason        = state.get('trip_reason')
                    if self.is_tripped:
                        app_logger.warning(f"[CB] ⚠️ Restored tripped state: {self.trip_reason}")
        except Exception as e:
            app_logger.warning(f"[CB] Could not load saved state: {e}")

    def _save_state(self):
        try:
            with open(STATE_FILE, 'w') as f:
                json.dump({
                    'date':               str(date.today()),
                    'is_tripped':         self.is_tripped,
                    'consecutive_losses': self.consecutive_losses,
                    'trip_reason':        self.trip_reason,
                    'timestamp':          datetime.now().isoformat()
                }, f, indent=2)
        except Exception as e:
            app_logger.warning(f"[CB] Could not save state: {e}")

    # ── Daily reset ───────────────────────────────────────────────────────────

    def _check_daily_reset(self):
        """Reset at midnight every new day — fresh start."""
        today = date.today()
        if today > self.last_reset_date:
            app_logger.info("[CB] 🌅 New day — Circuit Breaker reset.")
            self.is_tripped             = False
            self.trip_reason            = None
            self.consecutive_losses     = 0
            self.last_reset_date        = today
            self._session_start_balance = self._current_balance
            self._save_state()

    # ── Balance management ────────────────────────────────────────────────────

    def set_balance(self, balance: float):
        """
        Call once at bot startup (and when balance updates) to set the
        reference balance for daily-loss calculation.
        """
        self._current_balance = balance
        if self._session_start_balance is None:
            self._session_start_balance = balance
            app_logger.info(f"[CB] Session start balance set to ${balance:.2f}")

    # ── Public API ────────────────────────────────────────────────────────────

    def can_trade(self) -> bool:
        """
        Primary gate — call this BEFORE executing any trade.
        Returns True if trading is allowed, False if the breaker has tripped.
        """
        self._check_daily_reset()
        if self.is_tripped:
            app_logger.warning(f"[CB] 🔴 TRADING BLOCKED | Reason: {self.trip_reason}")
        return not self.is_tripped

    def record_result(self, profit: float, new_balance: float = None):
        """
        Call AFTER each trade closes.

        Parameters
        ----------
        profit      : float — P&L in USDT (negative = loss)
        new_balance : float — updated USDT balance (optional but recommended)
        """
        self._check_daily_reset()

        if new_balance is not None:
            self._current_balance = new_balance

        # Track consecutive losses
        if profit < 0:
            self.consecutive_losses += 1
        else:
            self.consecutive_losses = 0

        # Check daily loss %
        if self._session_start_balance and self._session_start_balance > 0 and self._current_balance:
            daily_loss_pct = (
                (self._session_start_balance - self._current_balance)
                / self._session_start_balance * 100
            )
            if daily_loss_pct >= self.max_daily_loss_pct:
                self._trip(
                    f"Daily loss {daily_loss_pct:.1f}% exceeds limit of {self.max_daily_loss_pct}%"
                )

        # Check consecutive losses
        if self.consecutive_losses >= self.max_consecutive_loss:
            self._trip(
                f"{self.consecutive_losses} consecutive losing trades (limit: {self.max_consecutive_loss})"
            )

        self._save_state()

    def _trip(self, reason: str):
        if not self.is_tripped:   # Log only on first trip
            self.is_tripped  = True
            self.trip_reason = reason
            app_logger.critical(f"[CB] 🔴 CIRCUIT BREAKER TRIPPED: {reason}")

    def get_status(self) -> dict:
        """Returns a status dict suitable for dashboard display."""
        daily_loss_pct = 0.0
        if self._session_start_balance and self._current_balance:
            daily_loss_pct = (
                (self._session_start_balance - self._current_balance)
                / self._session_start_balance * 100
            )
        return {
            'active':             not self.is_tripped,
            'is_tripped':         self.is_tripped,
            'trip_reason':        self.trip_reason,
            'daily_loss_pct':     round(daily_loss_pct, 2),
            'consecutive_losses': self.consecutive_losses,
            'max_daily_loss_pct': self.max_daily_loss_pct,
            'max_consec_loss':    self.max_consecutive_loss
        }
