import asyncio
import time
from datetime import datetime

class SwingVault:
    def __init__(self, api_client, telegram_bot, memory, main_bot=None):
        self.api = api_client
        self.telegram = telegram_bot
        self.memory = memory
        self.main_bot = main_bot
        self.vault_trades = []
        
        # Elite coins only
        self.elite_symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "LINKUSDT", "ADAUSDT", "TRXUSDT"]
        
        # Lock to prevent race conditions
        self.trade_lock = asyncio.Lock()
        
        self.last_scan_time = 0
        self.scan_interval = 900  # Scan every 15 minutes for 4H trends
        
        # Determine the persistent directory from the DB path if available
        import os
        db_dir = os.path.dirname(self.memory.db_path) if (self.memory and hasattr(self.memory, 'db_path')) else ""
        if db_dir:
            self.state_file = os.path.join(db_dir, "vault_state.json")
        else:
            self.state_file = "vault_state.json"
            
        self.last_trade_time = self._load_state()
        self.current_rsi_target = 35 # Default
        self.hunger_state = "NORMAL"

    def _load_state(self):
        import json, os
        last_time = time.time() - (86400 * 3)
        
        # Migrating from local file if it exists but the persistent one does not
        local_file = "vault_state.json"
        target_file = self.state_file
        
        if target_file != local_file and not os.path.exists(target_file) and os.path.exists(local_file):
            try:
                import shutil
                shutil.copy(local_file, target_file)
                self.add_log(f"🚚 Migrated state file from {local_file} to persistent {target_file}")
            except Exception as e:
                self.add_log(f"⚠️ Failed to migrate state file: {e}")
                
        if os.path.exists(target_file):
            try:
                with open(target_file, 'r') as f:
                    data = json.load(f)
                    self.vault_trades = data.get('vault_trades', [])
                    return data.get('last_trade_time', last_time)
            except:
                pass
        return last_time
        
    def _save_state(self):
        import json
        try:
            with open(self.state_file, 'w') as f:
                json.dump({
                    'last_trade_time': self.last_trade_time,
                    'vault_trades': self.vault_trades
                }, f)
        except:
            pass

    def add_log(self, msg):
        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Vault - INFO - {msg}")

    async def run_cycle(self):
        """Called by main.py periodically."""
        # 1. Manage open trades
        if self.vault_trades:
            await self._manage_vault_trades()
            return # If we have a swing trade open, don't scan for more (max 1 vault trade)

        # 2. Scan for new entries (only every 15 mins)
        now = time.time()
        if now - self.last_scan_time >= self.scan_interval:
            self.last_scan_time = now
            await self._scan_elite_coins()

    async def _scan_elite_coins(self):
        """Scans elite coins for deep dips on higher timeframes."""
        # Ensure we have at least $15 for the vault
        balance_raw = self.api.get_account_balance('USDT')
        if balance_raw < 15.0:
            return

        budget = balance_raw * 0.60 # 60% of available balance
        if budget < 10.5:
            budget = balance_raw * 0.95 # Fallback if 60% is too small, though Scalper shouldn't leave it this low

        lowest_rsi = 100
        best_coin = None
        
        # Adaptive RSI Logic
        hours_since_trade = (time.time() - self.last_trade_time) / 3600
        
        if hours_since_trade < 24:
            self.current_rsi_target = 30
            self.hunger_state = "SATISFIED"
        elif hours_since_trade < 72:
            self.current_rsi_target = 35
            self.hunger_state = "NORMAL"
        elif hours_since_trade < 168:
            self.current_rsi_target = 38
            self.hunger_state = "HUNGRY"
        else:
            self.current_rsi_target = 42
            self.hunger_state = "STARVING"

        for symbol in self.elite_symbols:
            try:
                # Fetch 4-hour candles
                df = self.api.get_historical_klines(symbol, interval='4h', limit=50)
                if df is None or df.empty: continue

                # Basic RSI calculation
                delta = df['close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs))
                current_rsi = rsi.iloc[-1]

                # Look for extreme oversold conditions based on adaptive target
                if current_rsi < self.current_rsi_target and current_rsi < lowest_rsi:
                    lowest_rsi = current_rsi
                    best_coin = symbol

            except Exception as e:
                self.add_log(f"Error scanning {symbol}: {e}")

        # If we found a great dip
        if best_coin and lowest_rsi < self.current_rsi_target:
            await self._execute_vault_entry(best_coin, budget)

    async def _execute_vault_entry(self, symbol, usdt_budget):
        if self.main_bot and hasattr(self.main_bot, 'active_trades'):
            if any(t.get('symbol') == symbol for t in self.main_bot.active_trades):
                self.add_log(f"⚠️ [SWING VAULT] {symbol} is already active in Scalp/Main bot. Skipping Swing Entry.")
                return
                
        async with self.trade_lock:
            try:
                current_price = float(self.api.get_symbol_ticker(symbol))
                if not current_price: return

                qty = usdt_budget / current_price
                
                # Execute Market Buy
                order = self.api.place_market_order(symbol, 'BUY', qty)
                if order and 'status' in order and order['status'] == 'FILLED':
                    fill_price = float(order['fills'][0]['price']) if 'fills' in order and order['fills'] else current_price
                    actual_qty = float(order['executedQty'])
                    
                    sl_price = fill_price * 0.95  # Deep 5% stop loss for 4H breathing room
                    
                    self.vault_trades.append({
                        'symbol': symbol,
                        'side': 'BUY',
                        'qty': actual_qty,
                        'entry_price': fill_price,
                        'sl': sl_price,
                        'tp': fill_price * 1.10, # 10% theoretical TP, but we will trail it
                        'trailing_sl': sl_price,
                        'highest_price': fill_price,
                        'pnl_pct': 0.0,
                        'time': datetime.now().strftime("%H:%M:%S"),
                        'trade_type': 'SWING',
                        'order_id': order['orderId']
                    })

                    self.add_log(f"🎯 [SWING VAULT] Executed entry on {symbol} at ${fill_price:.4f}. Budget: ${usdt_budget:.2f}")
                    
                    # Reset hunger
                    self.last_trade_time = time.time()
                    self._save_state()
                    
                    await self.telegram.send_message(
                        f"🎯 *SWING VAULT ENTRY / الدخول الاستثماري*\n"
                        f"Asset: `{symbol}`\n"
                        f"Price: `${fill_price:.4f}`\n"
                        f"Budget: `${usdt_budget:.2f}`\n"
                        f"Strategy: Adaptive 4H Deep Dip (RSI Target: < {self.current_rsi_target})"
                    )
            except Exception as e:
                self.add_log(f"Failed vault entry for {symbol}: {e}")

    async def _manage_vault_trades(self):
        """Lazy trailing stop for long-term holds."""
        async with self.trade_lock:
            for trade in list(self.vault_trades):
                try:
                    symbol = trade['symbol']
                    current_price = float(self.api.get_symbol_ticker(symbol))
                    
                    entry_p = trade['entry_price']
                    pnl_pct = (current_price - entry_p) / entry_p
                    trade['pnl_pct'] = pnl_pct
                    
                    if current_price > trade.get('highest_price', entry_p):
                        trade['highest_price'] = current_price
                    
                    highest_pct = (trade['highest_price'] - entry_p) / entry_p
                    
                    # 1. SMART SCALE-OUT LOGIC (Partial Take Profit)
                    if highest_pct >= 0.0300 and not trade.get('sold_tier_1', False):
                        qty_to_sell = trade['qty'] * 0.25 # Sell 25%
                        sell_order = self.api.place_market_order(symbol, 'SELL', qty_to_sell)
                        if sell_order and sell_order.get('status') == 'FILLED':
                            trade['qty'] -= float(sell_order['executedQty'])
                            trade['sold_tier_1'] = True
                            self.add_log(f"💰 [SCALE-OUT] Sold 25% of {symbol} at +{highest_pct*100:.2f}% profit!")
                            await self.telegram.send_message(f"💰 *SCALE-OUT 1 (25%)*: `{symbol}` locked at +{highest_pct*100:.2f}% profit!")

                    if highest_pct >= 0.0600 and not trade.get('sold_tier_2', False):
                        qty_to_sell = trade['qty'] * 0.333 # Sell 1/3 of remaining (which is ~25% of original)
                        sell_order = self.api.place_market_order(symbol, 'SELL', qty_to_sell)
                        if sell_order and sell_order.get('status') == 'FILLED':
                            trade['qty'] -= float(sell_order['executedQty'])
                            trade['sold_tier_2'] = True
                            self.add_log(f"💰 [SCALE-OUT] Sold another 25% of {symbol} at +{highest_pct*100:.2f}% profit!")
                            await self.telegram.send_message(f"💰 *SCALE-OUT 2 (25%)*: `{symbol}` locked at +{highest_pct*100:.2f}% profit!")

                    # 2. DYNAMIC PARABOLIC TRAILING LOGIC
                    new_sl = trade['sl']
                    
                    trail_pct = 0.02 # Default 2% trail
                    if highest_pct >= 0.0500:
                        try:
                            # Quick 15m momentum check to tighten the stop if overbought
                            df_15 = self.api.get_historical_klines(symbol, interval='15m', limit=15)
                            if df_15 is not None and not df_15.empty:
                                delta = df_15['close'].diff()
                                rs = (delta.where(delta > 0, 0)).rolling(window=14).mean() / (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                                rsi_15 = 100 - (100 / (1 + rs)).iloc[-1]
                                if rsi_15 > 75: # Extreme Overbought -> Tighten stop to 0.5%
                                    trail_pct = 0.005 
                                    self.add_log(f"🔥 [PARABOLIC TRAIL] {symbol} RSI is {rsi_15:.1f}. Tightening stop loss to 0.5%!")
                        except:
                            pass
                    
                    if highest_pct >= 0.0500: # 5% profit reached -> Trail dynamically
                        new_sl = trade['highest_price'] * (1 - trail_pct)
                    elif highest_pct >= 0.0300: # 3% profit reached -> Lock at +1.5%
                        new_sl = entry_p * 1.015
                    elif highest_pct >= 0.0150: # 1.5% profit reached -> Break-even lock
                        new_sl = entry_p * 1.002
                        
                    if new_sl > trade.get('trailing_sl', trade['sl']):
                        trade['trailing_sl'] = new_sl
                        trade['sl'] = new_sl
                        self.add_log(f"🛡️ [SWING VAULT] {symbol} Trailing SL updated to ${new_sl:.4f} (+{((new_sl/entry_p)-1)*100:.2f}%)")

                    # Check Stop Loss / Trailing Stop trigger
                    if current_price <= trade['sl']:
                        self.add_log(f"🛑 [SWING VAULT] {symbol} hit SL/Trailing at {current_price:.4f}")
                        
                        # Execute Market Sell
                        close_order = self.api.place_market_order(symbol, 'SELL', trade['qty'])
                        if close_order and close_order['status'] == 'FILLED':
                            self.vault_trades.remove(trade)
                            net_profit = (current_price - entry_p) / entry_p * 100
                            
                            # Save to diagnostic snapshot & memory DB
                            try:
                                self.memory.save_trade({
                                    'symbol': symbol,
                                    'side': 'BUY',
                                    'entry_price': entry_p,
                                    'exit_price': current_price,
                                    'peak_price': trade.get('highest_price', current_price),
                                    'pnl_usd': (current_price - entry_p) * trade['qty'],
                                    'duration': 0,
                                    'ai_conf': 0.99,
                                    'macro_fgi': 0
                                })
                            except Exception as mem_e:
                                self.add_log(f"Memory save error: {mem_e}")
                                
                            await self.telegram.send_message(
                                f"🔒 *SWING VAULT CLOSED / إغلاق صفقة الاستثمار*\n"
                                f"Asset: `{symbol}`\n"
                                f"Exit Price: `${current_price:.4f}`\n"
                                f"Net PNL: `{net_profit:+.2f}%`"
                            )
                except Exception as e:
                    self.add_log(f"Error managing vault trade {trade.get('symbol')}: {e}")
            self._save_state()
