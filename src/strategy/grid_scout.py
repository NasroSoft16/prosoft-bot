import time
import math
from src.utils.logger import app_logger

class GridScout:
    """PROSOFT QUANTUM PRIME: Flash Arbitrage & Grid Scouting (Range Sniper)"""
    
    def __init__(self, api_wrapper, telegram_bot=None):
        self.api = api_wrapper
        self.telegram = telegram_bot
        self.active_grids = {} # symbol -> {'buy_price': x, 'sell_price': y, 'state': 'WAITING_BUY', 'sl': z, 'qty': 0}
        self.max_allocation = 11.5 # Micro account allocation
        
    def analyze_micro_channel(self, df):
        """
        Analyzes recent candles to find a tight, sideways trading channel.
        Ideal for Range Sniper.
        """
        if df is None or len(df) < 20: return None
        
        recent = df.tail(20)
        high = recent['high'].max()
        low = recent['low'].min()
        
        # Calculate the channel spread percentage
        spread_pct = ((high - low) / low) * 100
        
        # We want a tight channel, e.g., 0.6% to 2.5% volatility
        if 0.6 <= spread_pct <= 2.5:
            return {
                'channel_low': low,
                'channel_high': high,
                'spread': spread_pct,
                'mid_point': (high + low) / 2
            }
        return None

    def _get_precision(self, symbol):
        # Fallback simplistic precision handling. In a real scenario, fetch from exchange info.
        return 4 if 'SHIB' in symbol or 'PEPE' in symbol or 'BONK' in symbol or 'FLOKI' in symbol else 2

    async def execute_grid_cycle(self, symbol, current_price, usdt_balance):
        """
        Executes a continuous buy low / sell high loop inside the detected channel.
        Simulates "Mining" by generating small USDT fractions continuously.
        Returns True if an action was taken.
        """
        if symbol not in self.active_grids:
            return False
            
        grid = self.active_grids[symbol]
        
        try:
            # 1. EMERGENCY STOP LOSS (Breakout Detection)
            if grid['state'] == 'WAITING_SELL':
                if current_price <= grid['sl']:
                    app_logger.warning(f"🚨 [GRID SCOUT] {symbol} broke Support! Hitting 0.8% SL at {current_price} to prevent crash.")
                    # Execute Market Sell
                    close_order = self.api.place_market_order(symbol, 'SELL', grid['qty'])
                    if close_order and close_order.get('status') == 'FILLED':
                        del self.active_grids[symbol]
                        if self.telegram:
                            await self.telegram.send_message(f"🚨 *RANGE SNIPER SL HIT*\n{symbol} broke Support. Cut loss at 0.8%. Returning to Scalper.")
                    return True

            # 2. BUY OPPORTUNITY
            if grid['state'] == 'WAITING_BUY' and current_price <= grid['buy_price']:
                # Allocate exactly $11 to this cycle (min required by Binance + small buffer)
                if usdt_balance >= self.max_allocation:
                    app_logger.info(f"🕸️ [GRID SCOUT] Buy Triggered on {symbol} @ {current_price}")
                    
                    qty = self.max_allocation / current_price
                    # Execute API Buy
                    order = self.api.place_market_order(symbol, 'BUY', qty)
                    if order and order.get('status') == 'FILLED':
                        fill_price = float(order['fills'][0]['price']) if 'fills' in order and order['fills'] else current_price
                        actual_qty = float(order['executedQty'])
                        
                        grid['state'] = 'WAITING_SELL'
                        grid['qty'] = actual_qty
                        grid['buy_price_executed'] = fill_price
                        grid['sl'] = fill_price * 0.992 # 0.8% strict Stop Loss
                        
                        if self.telegram:
                            await self.telegram.send_message(f"🕸️ *RANGE SNIPER BUY*\n{symbol} at `{fill_price:.4f}`\nTarget: `{grid['sell_price']:.4f}`")
                        return True
                    
            # 3. SELL OPPORTUNITY (Take Profit)
            elif grid['state'] == 'WAITING_SELL' and current_price >= grid['sell_price']:
                app_logger.info(f"🕸️ [GRID SCOUT] Sell Triggered on {symbol} @ {current_price}. Profit Secured!")
                
                # Execute API Sell
                order = self.api.place_market_order(symbol, 'SELL', grid['qty'])
                if order and order.get('status') == 'FILLED':
                    fill_price = float(order['fills'][0]['price']) if 'fills' in order and order['fills'] else current_price
                    profit_pct = (fill_price - grid['buy_price_executed']) / grid['buy_price_executed'] * 100
                    
                    # Reset grid for next cycle
                    grid['state'] = 'WAITING_BUY'
                    grid['qty'] = 0
                    
                    if self.telegram:
                        await self.telegram.send_message(f"✅ *RANGE SNIPER PROFIT*\n{symbol} sold at `{fill_price:.4f}`\nPnL: `+{profit_pct:.2f}%`\nWaiting for next dip...")
                    return True
                
        except Exception as e:
            app_logger.error(f"Grid Scout Error on {symbol}: {e}")
            
        return False
        
    def deploy_grid(self, symbol, df):
        """Sets up the grid boundaries based on analysis."""
        if symbol in self.active_grids and self.active_grids[symbol]['state'] != 'WAITING_BUY':
            return False # Already holding a bag, don't reset channel
            
        channel = self.analyze_micro_channel(df)
        if channel:
            self.active_grids[symbol] = {
                'buy_price': channel['channel_low'] * 1.002, # Slightly above the very bottom
                'sell_price': channel['channel_high'] * 0.995, # Slightly below the very top
                'state': 'WAITING_BUY',
                'qty': 0,
                'sl': channel['channel_low'] * 0.992 # Strict stop
            }
            app_logger.info(f"🕸️ [GRID SCOUT] Grid Deployed for {symbol}. Spread: {channel['spread']:.2f}% (Support: {channel['channel_low']:.4f})")
            return True
        return False
