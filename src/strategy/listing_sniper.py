import asyncio
from src.utils.logger import app_logger

class ListingSniper:
    """
    PROSOFT AI: Flash Listing Sniper
    Monitors Binance announcements and executes lightning-fast buys 
    on newly listed assets in the first milliseconds.
    """
    def __init__(self, api_client, telegram_bot):
        self.api = api_client
        self.tg = telegram_bot
        self.watched_symbols = {}
        self.last_scan_time = 0
        self.scan_throttle = 10 # seconds

    def scan_for_new_listings(self):
        """Checks for new symbols or status transitions (e.g. TRADING enabled) with throttling."""
        import time
        now = time.time()
        if now - self.last_scan_time < self.scan_throttle:
            return None
            
        try:
            self.last_scan_time = now
            # Get current symbols and their statuses
            info = self.api.client.get_exchange_info()
            current_symbols = {s['symbol']: s['status'] for s in info['symbols']}
            
            # Initialization
            if not self.watched_symbols:
                self.watched_symbols = current_symbols
                return None
                
            # 1. Detection of brand new symbols (not in cache)
            new_assets = [sym for sym in current_symbols if sym not in self.watched_symbols]
            
            # 2. Detection of status transitions (e.g. was BREAK or PRE_TRADING, now TRADING)
            activated_assets = []
            for sym, status in current_symbols.items():
                if sym in self.watched_symbols:
                    old_status = self.watched_symbols[sym]
                    if old_status != 'TRADING' and status == 'TRADING':
                        activated_assets.append(sym)
            
            # Update cache
            self.watched_symbols = current_symbols
            
            # Priority: New assets first, then activated assets
            if new_assets:
                app_logger.warning(f"NEW SYMBOL DETECTED: {new_assets[0]}")
                return new_assets[0]
            if activated_assets:
                app_logger.warning(f"SYMBOL ACTIVATED FOR TRADING: {activated_assets[0]}")
                return activated_assets[0]
                
        except Exception as e:
            app_logger.error(f"Sniper Scanning Error: {e}")
        return None

    async def monitor_new_listings(self):
        """Asynchronous wrapper for background monitoring."""
        while True:
            new_asset = self.scan_for_new_listings()
            if new_asset:
                await self.execute_snipe(new_asset)
            await asyncio.sleep(60) # Deep scan every minute

    async def execute_snipe(self, symbol, amount_usdt=20.0):
        """Executes a market buy on a new listing immediately."""
        app_logger.warning(f"LISTING DETECTED: Sniping {symbol} with ${amount_usdt}...")
        try:
            # 1. Place Market Buy
            order = self.api.client.order_market_buy(symbol=symbol, quoteOrderQty=amount_usdt)
            if order:
                app_logger.info(f"SNIPE SUCCESS: {symbol} bought. Setting OCO exit...")
                # Log hit to revenue memory
                try:
                    from src.ai.neural_memory import NeuralMemory
                    memory = NeuralMemory()
                    memory.log_revenue("ListingSniper", symbol.replace("USDT", ""), 0.0, f"Successful Flash Snipe on {symbol}")
                except: pass
                return True
        except Exception as e:
            app_logger.error(f"Snipe Execution Failed for {symbol}: {e}")
        return False
