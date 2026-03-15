import asyncio
import time
from src.utils.logger import app_logger

class YieldFarmer:
    """
    PROSOFT AI: Yield Farming & Launchpool Optimizer
    Automatically stakes idle funds into Binance Flexible Earn or Launchpool 
    when no trading opportunities exist, and pulls them back when needed.
    """
    def __init__(self, api_client):
        self.api = api_client
        self.is_farming = False
        self.min_farm_amount = 10.0 # USDT minimum

    async def check_and_farm(self, threshold_usdt=20.0):
        """Checks if balance is idle and moves it to Generate Yield."""
        try:
            balance = self.api.get_account_balance('USDT')
            if balance > threshold_usdt and not self.is_farming:
                app_logger.info(f"Idle Balance Detected (${balance}). Moving to Simple Earn...")
                success = self.api.simple_earn_subscribe('USDT', balance)
                if success:
                    self.is_farming = True
                    return True
        except Exception as e:
            app_logger.error(f"Yield Farmer Error: {e}")
        return False

    async def recall_funds(self):
        """Redeems funds immediately for trading."""
        if self.is_farming:
            app_logger.info("Trading Signal Detected! Redeeming funds from Earn...")
            success = self.api.simple_earn_redeem('USDT')
            if success:
                self.is_farming = False
                return True
        return False

    async def sync_rewards(self, memory):
        """Fetches latest rewards and logs them to memory."""
        try:
            rewards = self.api.get_simple_earn_rewards('USDT')
            for r in rewards:
                # Log only if amount > 0 and recently
                amount = float(r['rewards'])
                if amount > 0:
                    memory.log_revenue("YieldFarmer", "USDT", amount, f"Simple Earn Interest: {r['time']}")
        except Exception as e:
            app_logger.error(f"Yield sync error: {e}")
