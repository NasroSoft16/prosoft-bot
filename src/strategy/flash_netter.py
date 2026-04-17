import time
from src.utils.logger import app_logger

class FlashNetter:
    """
    PROSOFT Flash-Wick Netting (Deep Limit Orders Strategy)
    
    Philosophy: 
    For small accounts, market buying breakouts usually results in slippage and immediate drawdown.
    This module sets "fishing nets" (Limit Buys) far below the current market price (e.g. -5%)
    on highly liquid coins. When a liquidation cascade happens, the wick hits our net,
    and we capture 3-5% profit on the immediate recovery bounce.
    
    No slippage. No FGI-induced FOMO. Safe and passive.
    """
    def __init__(self, api_client):
        self.api = api_client
        self.open_nets = {} # symbol -> {order_id, target_price, timestamp}
        self.drop_percent = 0.05 # 5% below market
        
        # We only throw nets on highly liquid, fast-recovering assets
        self.target_fishing_coins = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'DOGEUSDT', 'BNBUSDT']

    async def manage_nets(self, available_balance):
        """
        Main loop hook to place, monitor, and clean up limit orders.
        Returns newly caught (filled) trades to be added to active_trades.
        """
        caught_fishes = []
        
        try:
            # 1. Check existing open nets on Binance
            symbols_to_check = list(self.open_nets.keys())
            for symbol in symbols_to_check:
                net = self.open_nets[symbol]
                
                # Check order status via Binance API
                try:
                    order_status = self.api.client.get_order(symbol=symbol, orderId=net['order_id'])
                    
                    if order_status['status'] == 'FILLED':
                        app_logger.info(f"🎣 [FLASH NETTER] WICK CAUGHT! Limit Buy Filled for {symbol} @ {net['target_price']}")
                        
                        # Generate trade object for main bot
                        caught_fishes.append({
                            'symbol': symbol,
                            'side': 'BUY',
                            'entry_price': net['target_price'],
                            'qty': float(order_status['executedQty']),
                            'sl': net['target_price'] * 0.96, # Hard Stop Loss
                            'tp': net['target_price'] * 1.03, # 3% quick scalp target
                            'trailing_sl': net['target_price'] * 0.96,
                            'strategy': 'FLASH_NETTING',
                            'conf': 0.99,
                            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
                        })
                        del self.open_nets[symbol]
                        continue
                        
                    elif order_status['status'] in ['CANCELED', 'REJECTED', 'EXPIRED']:
                        del self.open_nets[symbol]
                        continue
                        
                    else:
                        # Still open. Is it too old? (e.g. > 12 hours)
                        if time.time() - net['timestamp'] > 43200:
                            app_logger.info(f"🎣 [FLASH NETTER] Net for {symbol} is stale (>12h). Canceling.")
                            self.api.client.cancel_order(symbol=symbol, orderId=net['order_id'])
                            del self.open_nets[symbol]
                            continue
                except Exception as e:
                    app_logger.error(f"[FLASH NETTER] API Check Error for {symbol}: {e}")
                    
            # 2. Deploy new nets if we have balance (Account > $12)
            if available_balance > 12.0 and len(self.open_nets) < 1:
                # Pick the first coin that we don't have a net for
                for coin in self.target_fishing_coins:
                    if coin not in self.open_nets:
                        # Deploy!
                        current_price_str = self.api.get_symbol_ticker(coin)
                        if current_price_str:
                            current_price = float(current_price_str)
                            target_limit = current_price * (1 - self.drop_percent)
                            
                            # Safety rounding based on binance tick size (roughly 4 decimals most places)
                            target_limit = round(target_limit, 4)
                            
                            qty = 11.5 / target_limit # Use exactly $11.5 to be safe above Binance $10 limit
                            
                            # Standardize qty precision (Binance requires exact LOT_SIZE)
                            # A simple rough rounding is 3 decimals since it's just a limit test
                            qty = round(qty, 3)
                            
                            try:
                                # We need to use binance order_limit_buy directly
                                order = self.api.client.order_limit_buy(
                                    symbol=coin,
                                    quantity=qty,
                                    price=str(target_limit)
                                )
                                if order and 'orderId' in order:
                                    self.open_nets[coin] = {
                                        'order_id': order['orderId'],
                                        'target_price': target_limit,
                                        'timestamp': time.time()
                                    }
                                    app_logger.info(f"🕸️ [FLASH NETTER] Deployed deep limit net for {coin} @ ${target_limit} (-5% deep).")
                                    # Used some balance, break to prevent using all
                                    break
                            except Exception as limit_err:
                                # Usually LOT_SIZE or MIN_NOTIONAL errors. We can ignore and it will retry next loop or pick another coin
                                pass

        except Exception as general_err:
            app_logger.error(f"[FLASH NETTER] Loop Error: {general_err}")
            
        return caught_fishes
