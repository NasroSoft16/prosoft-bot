import time
from src.utils.logger import app_logger

class YieldFarmer:
    """
    PROSOFT AI: Yield Farming & Launchpool Optimizer
    
    v2.0 PHILOSOPHY (Fixed for small accounts):
    =============================================
    OLD (BROKEN): Sends ALL idle USDT to Earn every 45 seconds → blocks trading!
    NEW (FIXED):  
      1. Keeps a strict "War Chest" of $13 reserved ALWAYS for trading
      2. Only farms SURPLUS above war chest (equity > $50 threshold)
      3. Has a 30-minute cooldown between farm attempts
      4. For accounts < $50 total equity: FARMING IS DISABLED (not worth the risk)
    """
    
    # Minimum USDT to ALWAYS keep available for trading (Binance min $10 + $3 buffer)
    TRADING_WAR_CHEST = 13.0
    
    # Minimum account size to enable farming (no point farming $5)
    MIN_EQUITY_FOR_FARMING = 50.0
    
    # Cooldown between farm attempts (30 minutes)
    FARM_COOLDOWN_SEC = 1800
    
    def __init__(self, api_client):
        self.api = api_client
        self.is_farming = False
        self.last_farm_attempt = 0.0   # Timestamp of last attempt
        self.min_farm_amount = 10.0    # USDT minimum to move to Earn

    async def check_and_farm(self, threshold_usdt=50.0):
        """
        Safely checks if there is SURPLUS balance that can be farmed
        WITHOUT disrupting trading capital.
        """
        try:
            # --- Cooldown Guard: Don't spam the API ---
            now = time.time()
            if now - self.last_farm_attempt < self.FARM_COOLDOWN_SEC:
                return False  # Silent skip - not time yet
            
            balance = self.api.get_account_balance('USDT')
            
            # --- War Chest Guard: NEVER farm if balance threatens trading ---
            if balance <= self.TRADING_WAR_CHEST:
                app_logger.debug(f"[YieldFarmer] Balance ${balance:.2f} ≤ war chest ${self.TRADING_WAR_CHEST}. Farming skipped.")
                return False
            
            # --- Account Size Guard: Small accounts don't benefit from farming ---
            from src.risk_management.portfolio_manager import PortfolioManager
            # Use balance as proxy for equity for simplicity
            if balance < self.MIN_EQUITY_FOR_FARMING:
                app_logger.debug(f"[YieldFarmer] Account balance ${balance:.2f} < ${self.MIN_EQUITY_FOR_FARMING} minimum. Farming disabled for small accounts.")
                return False  
            
            # --- Calculate only the SURPLUS (what's safe to farm) ---
            surplus = balance - self.TRADING_WAR_CHEST
            
            if surplus >= self.min_farm_amount and not self.is_farming:
                self.last_farm_attempt = now
                app_logger.info(f"💰 [YieldFarmer] Farming SURPLUS ${surplus:.2f} (keeping ${self.TRADING_WAR_CHEST} war chest). Moving to Simple Earn...")
                success = self.api.simple_earn_subscribe('USDT', surplus)
                if success:
                    self.is_farming = True
                    return True
                else:
                    app_logger.warning(f"[YieldFarmer] Earn subscription failed (API returned False). Will retry in 30m.")
                    
        except Exception as e:
            app_logger.error(f"Yield Farmer Error: {e}")
        return False

    async def recall_funds(self):
        """Redeems ALL farmed funds immediately for trading."""
        if self.is_farming:
            app_logger.info("🔄 [YieldFarmer] Trading Signal! Recalling funds from Earn...")
            success = self.api.simple_earn_redeem('USDT')
            if success:
                self.is_farming = False
                # Small delay to let Binance unlock the funds
                import asyncio
                await asyncio.sleep(2.0)
                return True
        return False

    async def sync_rewards(self, memory):
        """Fetches latest rewards and logs them to memory."""
        try:
            rewards = self.api.get_simple_earn_rewards('USDT')
            for r in rewards:
                amount = float(r.get('rewards', 0))
                if amount > 0:
                    memory.log_revenue("YieldFarmer", "USDT", amount, f"Simple Earn Interest: {r.get('time', '')}")
        except Exception as e:
            app_logger.error(f"Yield sync error: {e}")
