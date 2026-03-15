import os
from src.utils.logger import app_logger

class RiskManager:
    def __init__(self, risk_per_trade=0.01, max_daily_loss_pct=0.03, max_consecutive_losses=2):
        self.risk_per_trade = float(os.getenv('RISK_PER_TRADE', risk_per_trade))
        self.max_daily_loss_pct = float(os.getenv('MAX_DAILY_LOSS_PCT', max_daily_loss_pct))
        self.max_consecutive_losses = int(os.getenv('MAX_CONSEC_LOSSES', max_consecutive_losses))
        
        # In-memory session tracking
        self.daily_pnl_pct = 0.0
        self.consecutive_losses = 0
        self.trades_today = 0

    def calculate_position_size(self, balance, price, stop_loss):
        """Calculates position size based on 1% risk rule with Micro-Account support."""
        try:
            # 1. Standard Risk Calculation
            risk_amount = balance * self.risk_per_trade
            risk_per_unit = abs(price - stop_loss)
            
            if risk_per_unit == 0:
                return 0.0
            
            position_size = risk_amount / risk_per_unit
            
            # --- MICRO-ACCOUNT OPTIMIZATION (For $10 - $100 Accounts) ---
            # Binance minimum order is 10 USDT.
            if balance < 100:
                min_usdt = 10.5 # A bit above $10 to be safe
                if balance >= min_usdt:
                    required_size = min_usdt / price
                    # If our risk calculation is smaller than the min allowed by Binance,
                    # we use the minimum size as long as it's within 95% of our capital.
                    if position_size < required_size:
                        position_size = required_size
            
            # 2. Safety Bounds
            total_cost = position_size * price
            
            # Never use more than 95% of balance for one trade (buffer for fees)
            if total_cost > (balance * 0.95):
                position_size = (balance * 0.95) / price
                
            # --- AUTO-COMPOUNDER (Hyper-Growth for Micro Accounts) ---
            # Phase 3: Zero-Waste Compounding
            # If the account has grown past its initial benchmark, 
            # we allocate a percentage of profits into the next trade.
            initial_deposit = float(os.getenv('INITIAL_DEPOSIT', 15.0))
            compound_ratio = float(os.getenv('COMPOUNDING_RATIO', 0.50)) # Default 50% of profits
            
            if balance > initial_deposit:
                profit_pool = balance - initial_deposit
                bonus_allocation = profit_pool * compound_ratio
                bonus_size = bonus_allocation / price
                position_size += bonus_size
                app_logger.info(f"🧬 [AUTO-COMPOUNDER] Strategy v12.0: Added {bonus_size:.6f} to size from Profit Pool (${bonus_allocation:.2f})")
            
            # Recalculate cost after compounder
            total_cost = position_size * price
            if total_cost > (balance * 0.95):
                position_size = (balance * 0.95) / price
            
            app_logger.info(f"Capital Strategy: Base Risk Amount {risk_amount:.2f} USDT | Final Compounded Size: {position_size:.6f} (${position_size*price:.2f})")
            return position_size
        except Exception as e:
            app_logger.error(f"Risk Management Error: {e}")
            return 0.0

    def update_performance(self, profit_loss_pct):
        """Updates internal risk trackers after a trade closes."""
        self.daily_pnl_pct += profit_loss_pct
        if profit_loss_pct < 0:
            self.consecutive_losses += 1
        else:
            self.consecutive_losses = 0
        
        self.trades_today += 1

    def can_trade(self):
        """Checks if current risk limits allow for a new trade."""
        if self.daily_pnl_pct <= -self.max_daily_loss_pct:
            app_logger.warning("Daily loss limit reached. Trading halted today.")
            return False
        
        if self.consecutive_losses >= self.max_consecutive_losses:
            app_logger.warning(f"{self.max_consecutive_losses} consecutive losses reached. Taking a break.")
            return False
            
        return True

    def reset_daily_stats(self):
        """Resets stats for a new day."""
        self.daily_pnl_pct = 0.0
        self.consecutive_losses = 0
        self.trades_today = 0
