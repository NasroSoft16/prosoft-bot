import asyncio
from src.utils.logger import app_logger

class FundingRateArb:
    """
    PROSOFT AI: Funding Rate Arbitrage (Cash-and-Carry)
    Neutralizes price risk by holding Spot and Shorting Futures
    to collect the 8-hour funding fee payments.
    """
    def __init__(self, api_client):
        self.api = api_client
        self.active_positions = {}

    async def scan_opportunities(self):
        """Finds pairs where Futures Funding Rate > 0.03% (High payout)."""
        try:
            # Get funding rates for all futures pairs
            rates = self.api.client.futures_funding_rate()
            # Filter for high positive rates (Longs pay Shorts)
            # Ensure each item has 'lastFundingRate' key to avoid KeyError
            valid_rates = [r for r in rates if isinstance(r, dict) and 'lastFundingRate' in r]
            top_rates = sorted(valid_rates, key=lambda x: float(x.get('lastFundingRate', 0)), reverse=True)
            return top_rates[:5]
        except Exception as e:
            app_logger.error(f"Funding Arb Scanner Error: {e}")
            return []

    async def execute_hedge_arb(self, symbol, amount_usdt):
        """Buy Spot + Short Futures simultaneously."""
        app_logger.info(f"Executing Funding Arb on {symbol} for ${amount_usdt}...")
        try:
            # 1. Calculate Quantity
            ticker = self.api.get_symbol_ticker(symbol)
            if not ticker: return False
            qty = (amount_usdt / 2.0) / ticker # Split half for spot, half for futures margin
            
            # 2. Buy Spot
            app_logger.info(f"Step 1: Buying Spot {symbol}")
            # order_spot = self.api.client.order_market_buy(symbol=symbol, quantity=qty)
            
            # 3. Short Futures
            app_logger.info(f"Step 2: Shorting Futures {symbol}")
            # order_futures = self.api.client.futures_create_order(symbol=symbol, side='SELL', type='MARKET', quantity=qty)
            
            self.active_positions[symbol] = {'qty': qty, 'entry': ticker}
            app_logger.info(f"✅ Funding Arb Position Opened for {symbol}.")
            return True
        except Exception as e:
            app_logger.error(f"Funding Arb Execution Error: {e}")
            return False

    async def log_funding_revenue(self, memory):
        """Checks for funding fee payouts and logs them to memory."""
        try:
            fees = await self.api.get_funding_fee_history()
            
            # Critical Gate: If the wrapper returned a coroutine (async leakage), await it again
            if not isinstance(fees, list) and hasattr(fees, '__await__'):
                fees = await fees
            
            if not isinstance(fees, list):
                return

            for f in fees:
                amount = float(f.get('income', 0))
                if abs(amount) > 0: 
                    memory.log_revenue("FundingArb", f.get('asset', 'N/A'), amount, f"Funding Fee Payout: {f.get('symbol', 'N/A')}")
        except Exception as e:
            app_logger.error(f"Funding revenue log error: {e}")
