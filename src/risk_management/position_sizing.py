import os
from src.utils.logger import app_logger

class RiskManager:
    def __init__(self, risk_per_trade=0.015, max_daily_loss_pct=0.04, max_consecutive_losses=3):
        # 12.8 PROSOFT: Monster Defaults (1.5% risk, 4% daily cap)
        self.risk_per_trade = float(os.getenv('RISK_PER_TRADE', risk_per_trade))
        self.max_daily_loss_pct = float(os.getenv('MAX_DAILY_LOSS_PCT', max_daily_loss_pct))
        self.max_consecutive_losses = int(os.getenv('MAX_CONSEC_LOSSES', max_consecutive_losses))
        
        # In-memory session tracking
        self.daily_pnl_pct = 0.0
        self.consecutive_losses = 0
        self.trades_today = 0

    def calculate_position_size(self, budget_per_slot, price, stop_loss, ai_conf=0.85):
        """
        12.8 PROSOFT: Compounding Position Engine.
        Uses the provided budget_per_slot (fraction of equity) 
        and adjusts based on AI Confidence and Risk distance.
        """
        try:
            # 1. Distance Risk Calculation
            # How much % the stop loss is from current price
            risk_distance_pct = abs(price - stop_loss) / price
            if risk_distance_pct == 0: return 0.0
            
            # 2. AI Confidence Multiplier
            # Baseline 0.85. 
            ai_multiplier = max(0.7, min(1.3, ai_conf / 0.85))
            
            # 3. Sovereign Risk Governor: Scale down if we have losses
            sovereign_mult = 1.0
            if self.consecutive_losses == 1: sovereign_mult = 0.75
            elif self.consecutive_losses >= 2: sovereign_mult = 0.5
            
            # 4. Final Budget Allocation
            # We risk a portion of the slot budget based on the SL distance
            # If distance is small (0.5%), we can use more of the budget.
            # If distance is large (5%), we use less.
            # Base risk is set to 1.5% of the budget per 1% of distance.
            base_risk_factor = 0.015 
            target_risk_amount = budget_per_slot * base_risk_factor * ai_multiplier * sovereign_mult
            
            position_size = target_risk_amount / risk_distance_pct / price
            
            # Final Safety: Never exceed allocated budget for the slot
            max_qty = budget_per_slot / price
            if (position_size * price) > budget_per_slot:
                position_size = max_qty * 0.98 # 2% buffer for fees
            
            # Micro-Account Boost
            if budget_per_slot < 20: 
                # If budget is very small, we must use at least $10.5 to meet Binance min
                if budget_per_slot >= 10.5:
                    position_size = 10.5 / price
            
            app_logger.info(f"Sovereign Risk: Mult {ai_multiplier:.2f}x | Sov {sovereign_mult:.2f}x | Size: ${position_size*price:.2f}")
            return position_size
            
        except Exception as e:
            app_logger.error(f"Sovereign Sizing Error: {e}")
            return 0.0

    def update_performance(self, profit_loss_pct):
        """Updates internal risk trackers."""
        self.daily_pnl_pct += profit_loss_pct
        if profit_loss_pct < 0:
            self.consecutive_losses += 1
        else:
            self.consecutive_losses = 0
        self.trades_today += 1

    def can_trade(self):
        """Sovereign Guard: Prevents trading if daily limits are breached."""
        if self.daily_pnl_pct <= -self.max_daily_loss_pct:
            app_logger.warning("SOVEREIGN BLOCK: Daily loss limit reached. Cooling down.")
            return False
        return True

    def reset_daily_stats(self):
        self.daily_pnl_pct = 0.0
        self.consecutive_losses = 0
        self.trades_today = 0
