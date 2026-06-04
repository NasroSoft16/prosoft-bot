import asyncio
import time
from datetime import datetime
import pandas as pd
import math
from binance.exceptions import BinanceAPIException

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
        log_str = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Vault - INFO - {msg}"
        try:
            print(log_str)
        except UnicodeEncodeError:
            try:
                print(log_str.encode('ascii', errors='backslashreplace').decode('ascii'))
            except:
                pass

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
                    # Daily Trend Gate (EMA 20) Check
                    try:
                        df_1d = self.api.get_historical_klines(symbol, interval='1d', limit=50)
                        if df_1d is not None and not df_1d.empty and len(df_1d) >= 20:
                            ema_20_daily = df_1d['close'].ewm(span=20, adjust=False).mean().iloc[-1]
                            current_price_daily = df_1d['close'].iloc[-1]
                            if current_price_daily < ema_20_daily:
                                self.add_log(f"🧠 [SWING VAULT] Skipping {symbol} due to bearish daily trend (Close: {current_price_daily:.4f} < 20 EMA: {ema_20_daily:.4f})")
                                continue
                    except Exception as trend_err:
                        self.add_log(f"⚠️ Error checking daily trend for {symbol}: {trend_err}")

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

                # Split entry budget: 60% market buy, 40% limit buy at -3%
                usdt_tier_1 = usdt_budget * 0.60
                qty_tier_1 = usdt_tier_1 / current_price
                
                # Execute Market Buy (Tier 1)
                order = self.api.place_market_order(symbol, 'BUY', qty_tier_1)
                if order and 'status' in order and order['status'] == 'FILLED':
                    fill_price = float(order['fills'][0]['price']) if 'fills' in order and order['fills'] else current_price
                    actual_qty = float(order['executedQty'])
                    
                    # Calculate 14-period ATR on 4H candles
                    atr_val = None
                    try:
                        df_4h = self.api.get_historical_klines(symbol, interval='4h', limit=50)
                        if df_4h is not None and not df_4h.empty and len(df_4h) >= 15:
                            high = df_4h['high']
                            low = df_4h['low']
                            close_prev = df_4h['close'].shift(1)
                            tr1 = high - low
                            tr2 = (high - close_prev).abs()
                            tr3 = (low - close_prev).abs()
                            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
                            atr_val = tr.rolling(window=14).mean().iloc[-1]
                    except Exception as atr_err:
                        self.add_log(f"⚠️ Error calculating ATR for {symbol}: {atr_err}")

                    if atr_val is not None and not math.isnan(atr_val):
                        sl_distance = 2.5 * atr_val
                        sl_pct = sl_distance / fill_price
                        if sl_pct < 0.025:
                            sl_distance = fill_price * 0.025
                            self.add_log(f"⚠️ ATR SL pct too tight ({sl_pct*100:.2f}%), adjusted to minimum 2.5%")
                        elif sl_pct > 0.080:
                            sl_distance = fill_price * 0.080
                            self.add_log(f"⚠️ ATR SL pct too wide ({sl_pct*100:.2f}%), adjusted to maximum 8.0%")
                        sl_price = fill_price - sl_distance
                    else:
                        sl_distance = fill_price * 0.05
                        sl_price = fill_price - sl_distance
                        self.add_log(f"⚠️ ATR calculation failed. Using fallback 5% SL for {symbol}")

                    # Place Limit BUY (Tier 2) order at 3% below the fill price of Tier 1
                    limit_order_id = None
                    formatted_price = 0.0
                    formatted_qty = 0.0
                    try:
                        info = self.api.client.get_symbol_info(symbol)
                        qty_precision = 6
                        price_precision = 4
                        step_size = 0.0
                        tick_size = 0.0
                        if info and 'filters' in info:
                            for f in info['filters']:
                                if f['filterType'] == 'LOT_SIZE':
                                    step_size = float(f['stepSize'])
                                    if step_size > 0:
                                        qty_precision = int(round(-math.log10(step_size), 0)) if step_size < 1 else 0
                                elif f['filterType'] == 'PRICE_FILTER':
                                    tick_size = float(f['tickSize'])
                                    if tick_size > 0:
                                        price_precision = int(round(-math.log10(tick_size), 0)) if tick_size < 1 else 0

                        limit_price = fill_price * 0.97
                        if tick_size > 0:
                            factor = 10 ** price_precision
                            limit_price = math.floor(limit_price * factor + 1e-10) / factor
                        formatted_price = float(f"{limit_price:.{price_precision}f}")
                        
                        usdt_tier_2 = usdt_budget * 0.40
                        qty_tier_2 = usdt_tier_2 / formatted_price
                        if step_size > 0:
                            factor = 10 ** qty_precision
                            qty_tier_2 = math.floor(qty_tier_2 * factor + 1e-10) / factor
                        formatted_qty = float(f"{qty_tier_2:.{qty_precision}f}")

                        limit_order = self.api.client.create_order(
                            symbol=symbol,
                            side='BUY',
                            type='LIMIT',
                            timeInForce='GTC',
                            quantity=formatted_qty,
                            price=formatted_price
                        )
                        if limit_order:
                            limit_order_id = limit_order.get('orderId')
                            self.add_log(f"📝 [SWING DCA] Placed Limit BUY (Tier 2) for {symbol} at ${formatted_price:.4f}, qty: {formatted_qty}")
                    except Exception as limit_err:
                        self.add_log(f"⚠️ Failed to place Tier 2 limit order for {symbol}: {limit_err}")

                    self.vault_trades.append({
                        'symbol': symbol,
                        'side': 'BUY',
                        'qty': actual_qty,
                        'entry_price': fill_price,
                        'sl': sl_price,
                        'sl_distance': sl_distance,
                        'tp': fill_price * 1.10, # 10% theoretical TP, but we will trail it
                        'trailing_sl': sl_price,
                        'highest_price': fill_price,
                        'pnl_pct': 0.0,
                        'time': datetime.now().strftime("%H:%M:%S"),
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'trade_type': 'SWING',
                        'order_id': order['orderId'],
                        'limit_order_id': limit_order_id,
                        'limit_price': formatted_price,
                        'limit_qty': formatted_qty,
                        'tier_1_qty': actual_qty,
                        'tier_1_price': fill_price,
                        'tier_2_filled': False,
                        'sold_tier_1': False,
                        'sold_tier_2': False
                    })

                    self.add_log(f"🎯 [SWING VAULT] Executed Tier 1 entry on {symbol} at ${fill_price:.4f}. Budget: ${usdt_budget:.2f}")
                    
                    # Reset hunger
                    self.last_trade_time = time.time()
                    self._save_state()
                    
                    telegram_msg = (
                        f"🎯 *SWING VAULT ENTRY / الدخول الاستثماري*\n"
                        f"Asset: `{symbol}`\n"
                        f"Tier 1 (60% Market): `${fill_price:.4f}` | Qty: `{actual_qty:.6f}`\n"
                    )
                    if limit_order_id:
                        telegram_msg += f"Tier 2 (40% Limit): `${formatted_price:.4f}` | Qty: `{formatted_qty:.6f}` (Pending)\n"
                    else:
                        telegram_msg += f"Tier 2 (40% Limit): Failed to place limit order\n"
                    telegram_msg += (
                        f"Stop Loss: `${sl_price:.4f}`\n"
                        f"Strategy: Swing Vault v4.2 (RSI Target: < {self.current_rsi_target})"
                    )
                    await self.telegram.send_message(telegram_msg)
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
                    
                    # Check if pending Tier 2 limit order has been filled
                    limit_id = trade.get('limit_order_id')
                    if limit_id:
                        try:
                            status_order = self.api.client.get_order(symbol=symbol, orderId=limit_id)
                            if status_order and status_order.get('status') == 'FILLED':
                                tier_1_qty = trade.get('tier_1_qty', trade['qty'])
                                tier_1_price = trade.get('tier_1_price', trade['entry_price'])
                                
                                # Use returned values from order status if available
                                tier_2_qty = float(status_order.get('executedQty', trade.get('limit_qty', 0.0)))
                                tier_2_price = float(status_order.get('price', trade.get('limit_price', 0.0)))
                                if tier_2_qty <= 0:
                                    tier_2_qty = float(trade.get('limit_qty', 0.0))
                                if tier_2_price <= 0:
                                    tier_2_price = float(trade.get('limit_price', 0.0))
                                    
                                total_qty = tier_1_qty + tier_2_qty
                                new_entry_price = ((tier_1_qty * tier_1_price) + (tier_2_qty * tier_2_price)) / total_qty
                                
                                trade['qty'] = total_qty
                                trade['entry_price'] = new_entry_price
                                trade['tier_2_filled'] = True
                                trade['limit_order_id'] = None # Clear
                                
                                # Recalculate stop-loss based on the new entry price
                                sl_distance = trade.get('sl_distance')
                                if sl_distance:
                                    trade['sl'] = new_entry_price - sl_distance
                                    trade['trailing_sl'] = trade['sl']
                                else:
                                    trade['sl'] = new_entry_price * 0.95
                                    trade['trailing_sl'] = trade['sl']
                                    
                                # Reset highest price to adjust trailing stop base
                                trade['highest_price'] = max(current_price, new_entry_price)
                                entry_p = new_entry_price  # Update local entry_p for subsequent logic
                                
                                self.add_log(f"⚡ [SWING DCA] Tier 2 Limit filled for {symbol}. New Average Entry: ${new_entry_price:.4f}, Total Qty: {total_qty:.6f}")
                                
                                await self.telegram.send_message(
                                    f"⚡ *SWING VAULT DCA FILLED / تفعيل تعزيز الاستثمار*\n"
                                    f"Asset: `{symbol}`\n"
                                    f"Tier 2 Price: `${tier_2_price:.4f}`\n"
                                    f"New Average Entry: `${new_entry_price:.4f}`\n"
                                    f"Total Position Size: `{total_qty:.6f}`\n"
                                    f"New Stop Loss: `${trade['sl']:.4f}`"
                                )
                            elif status_order and status_order.get('status') in ['CANCELED', 'REJECTED', 'EXPIRED']:
                                self.add_log(f"⚠️ [SWING DCA] Tier 2 Limit order for {symbol} was {status_order.get('status')}. Clearing tracking.")
                                trade['limit_order_id'] = None
                        except Exception as check_err:
                            self.add_log(f"⚠️ Error checking GTC limit order {limit_id} for {symbol}: {check_err}")

                    pnl_pct = (current_price - entry_p) / entry_p
                    trade['pnl_pct'] = pnl_pct
                    
                    if current_price > trade.get('highest_price', entry_p):
                        trade['highest_price'] = current_price
                    
                    highest_pct = (trade['highest_price'] - entry_p) / entry_p
                    
                    # 1. SMART SCALE-OUT LOGIC (Partial Take Profit at Fibonacci Levels)
                    if highest_pct >= 0.0382 and not trade.get('sold_tier_1', False):
                        qty_to_sell = trade['qty'] * 0.25 # Sell 25%
                        sell_order = self.api.place_market_order(symbol, 'SELL', qty_to_sell)
                        if sell_order and sell_order.get('status') == 'FILLED':
                            trade['qty'] -= float(sell_order['executedQty'])
                            trade['sold_tier_1'] = True
                            self.add_log(f"💰 [SCALE-OUT 1] Sold 25% of {symbol} at +{highest_pct*100:.2f}% profit!")
                            await self.telegram.send_message(f"💰 *SCALE-OUT 1 (25%)*: `{symbol}` locked at +{highest_pct*100:.2f}% profit (Fibonacci 0.382 target)!")

                    if highest_pct >= 0.0618 and not trade.get('sold_tier_2', False):
                        qty_to_sell = trade['qty'] * 0.333 # Sell 1/3 of remaining
                        sell_order = self.api.place_market_order(symbol, 'SELL', qty_to_sell)
                        if sell_order and sell_order.get('status') == 'FILLED':
                            trade['qty'] -= float(sell_order['executedQty'])
                            trade['sold_tier_2'] = True
                            self.add_log(f"💰 [SCALE-OUT 2] Sold another 25% of {symbol} at +{highest_pct*100:.2f}% profit!")
                            await self.telegram.send_message(f"💰 *SCALE-OUT 2 (25%)*: `{symbol}` locked at +{highest_pct*100:.2f}% profit (Fibonacci 0.618 target)!")

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
                    elif highest_pct >= 0.0382: # 3.82% profit reached -> Lock at +1.5%
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
                        
                        # Cancel any pending GTC limit buy order on exit
                        limit_id = trade.get('limit_order_id')
                        if limit_id:
                            try:
                                self.api.client.cancel_order(symbol=symbol, orderId=limit_id)
                                self.add_log(f"🧹 Cancelled pending limit buy order {limit_id} for {symbol} on exit")
                            except Exception as cancel_err:
                                self.add_log(f"⚠️ Failed to cancel pending limit order {limit_id}: {cancel_err}")
                        
                        # Execute Market Sell
                        close_order = self.api.place_market_order(symbol, 'SELL', trade['qty'])
                        if close_order and close_order['status'] == 'FILLED':
                            self.vault_trades.remove(trade)
                            net_profit = (current_price - entry_p) / entry_p * 100
                            
                            # Save to diagnostic snapshot & memory DB
                            try:
                                self.memory.log_trade(
                                    symbol=symbol,
                                    side='BUY',
                                    entry=entry_p,
                                    exit_p=current_price,
                                    entry_t=trade.get('timestamp', datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                                    exit_t=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                    pnl=net_profit,
                                    conf=0.99,
                                    health=self.main_bot.stats.get('market_health', 50) if self.main_bot else 50,
                                    sentiment=self.main_bot.stats.get('sentiment', 'NEUTRAL') if self.main_bot else 'NEUTRAL',
                                    strategy_used='SWING_VAULT',
                                    highest_peak=trade.get('highest_price', current_price)
                                )
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

    async def exit_vault_trade_by_symbol(self, symbol, reason="MANUAL EXIT"):
        """Manually exit a swing vault trade."""
        async with self.trade_lock:
            trade = next((t for t in self.vault_trades if t['symbol'] == symbol), None)
            if not trade:
                self.add_log(f"Manual Vault Close Error: No active swing trade found for {symbol}")
                return False
            
            try:
                # Cancel any pending GTC limit buy order first on manual exit
                limit_id = trade.get('limit_order_id')
                if limit_id:
                    try:
                        self.api.client.cancel_order(symbol=symbol, orderId=limit_id)
                        self.add_log(f"🧹 Cancelled pending limit buy order {limit_id} for {symbol} on manual exit")
                    except Exception as cancel_err:
                        self.add_log(f"⚠️ Failed to cancel pending limit order {limit_id}: {cancel_err}")

                current_price = float(self.api.get_symbol_ticker(symbol))
                if not current_price:
                    current_price = trade['entry_price']
                
                # Execute Market Sell
                close_order = self.api.place_market_order(symbol, 'SELL', trade['qty'])
                if close_order and close_order.get('status') == 'FILLED':
                    self.vault_trades.remove(trade)
                    self._save_state()
                    
                    entry_p = trade['entry_price']
                    net_profit = (current_price - entry_p) / entry_p * 100
                    
                    # Save to diagnostic snapshot & memory DB
                    try:
                        self.memory.log_trade(
                            symbol=symbol,
                            side='BUY',
                            entry=entry_p,
                            exit_p=current_price,
                            entry_t=trade.get('timestamp', datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                            exit_t=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            pnl=net_profit,
                            conf=0.99,
                            health=self.main_bot.stats.get('market_health', 50) if self.main_bot else 50,
                            sentiment=self.main_bot.stats.get('sentiment', 'NEUTRAL') if self.main_bot else 'NEUTRAL',
                            strategy_used='SWING_VAULT',
                            highest_peak=trade.get('highest_price', current_price)
                        )
                    except Exception as mem_e:
                        self.add_log(f"Memory save error: {mem_e}")
                    
                    # Notify Telegram
                    await self.telegram.send_message(
                        f"🔓 *SWING VAULT MANUAL EXIT / إغلاق صفقة الاستثمار يدوياً*\n"
                        f"Asset: `{symbol}`\n"
                        f"Exit Price: `${current_price:.4f}`\n"
                        f"Net PNL: `{net_profit:+.2f}%`"
                    )
                    return True
                else:
                    self.add_log(f"Manual Vault Close Error: Order placement failed on Binance for {symbol}")
                    return False
            except Exception as e:
                self.add_log(f"Manual Vault Close Exception for {symbol}: {e}")
                return False
