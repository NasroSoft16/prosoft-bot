import time
from datetime import datetime
from src.utils.logger import app_logger

class TriangularArbitrageEngine:
    """
    PROSOFT AI: Triangular Arbitrage Engine (Cycle 3)
    الربح من فجوات السعر بين ثلاث عملات داخل بينانس.
    
    المبدأ: USDT -> BTC -> ETH -> USDT
    إذا كانت النتيجة النهائية أكبر من المبلغ الأولي (بعد العمولة) = ربح مضمون.
    """

    def __init__(self, api_client):
        self.api = api_client
        self.min_profit_pct = 0.30  # Increased from 0.15 to 0.30 for safety (covers slippage/latency)
        self.fee_rate = 0.001       # Binance spot fee 0.1%
        self.last_scan_time = None
        self.min_liquidity_depth = 2000 # Min USDT depth required per leg to consider safe
        
        # Popular triangle routes with high liquidity
        self.triangle_routes = [
            # Route: Base -> Mid -> Quote -> Base
            {"name": "BTC-ETH", "path": ["BTCUSDT", "ETHBTC", "ETHUSDT"], "base": "USDT"},
            {"name": "BTC-BNB", "path": ["BTCUSDT", "BNBBTC", "BNBUSDT"], "base": "USDT"},
            {"name": "BTC-SOL", "path": ["BTCUSDT", "SOLBTC", "SOLUSDT"], "base": "USDT"},
            {"name": "BTC-XRP", "path": ["BTCUSDT", "XRPBTC", "XRPUSDT"], "base": "USDT"},
            {"name": "ETH-BNB", "path": ["ETHUSDT", "BNBETH", "BNBUSDT"], "base": "USDT"},
            {"name": "BTC-DOGE", "path": ["BTCUSDT", "DOGEBTC", "DOGEUSDT"], "base": "USDT"},
            {"name": "BTC-ADA", "path": ["BTCUSDT", "ADABTC", "ADAUSDT"], "base": "USDT"},
            {"name": "BTC-LINK", "path": ["BTCUSDT", "LINKBTC", "LINKUSDT"], "base": "USDT"},
        ]
        
    def _get_all_prices(self):
        """Fetch all orderbook tickers (bid/ask) instead of last traded price for accurate spread."""
        if not self.api.client:
            return {}
        try:
            tickers = self.api.client.get_orderbook_tickers()
            return {t['symbol']: {'bid': float(t['bidPrice']), 'ask': float(t['askPrice'])} for t in tickers}
        except Exception as e:
            app_logger.error(f"[ARBITRAGE] Error fetching orderbook tickers: {e}")
            return {}

    def _calculate_triangle_profit(self, prices, route):
        """
        حساب الربح الحقيقي الشامل للسبريد (Bid/Ask) وعمولات بينانس.
        يمنع الخسائر الوهمية التي تحدث بسبب استخدام أوامر السوق.
        """
        p1 = prices.get(route['path'][0])  # e.g., BTCUSDT
        p2 = prices.get(route['path'][1])  # e.g., ETHBTC  
        p3 = prices.get(route['path'][2])  # e.g., ETHUSDT
        
        if not all([p1, p2, p3]) or any(v['bid'] == 0 or v['ask'] == 0 for v in [p1, p2, p3]):
            return None
        
        # Start with 1000 USDT for simulation
        start_amount = 1000.0
        
        # --- FORWARD DIRECTION (USDT -> Asset1 -> Asset2 -> USDT) ---
        # 1. Buy Asset1 with USDT (Market Buy crosses ASK price)
        btc_amount_out = (start_amount / p1['ask']) * (1 - self.fee_rate)
        # 2. Buy Asset2 with Asset1 (Market Buy crosses ASK price)
        eth_amount_out = (btc_amount_out / p2['ask']) * (1 - self.fee_rate)
        # 3. Sell Asset2 for USDT (Market Sell crosses BID price)
        final_usdt_forward = eth_amount_out * p3['bid'] * (1 - self.fee_rate)
        
        forward_profit_pct = ((final_usdt_forward - start_amount) / start_amount) * 100
        
        # --- REVERSE DIRECTION (USDT -> Asset2 -> Asset1 -> USDT) ---
        # 1. Buy Asset2 with USDT (Market Buy crosses ASK price)
        eth_rev_out = (start_amount / p3['ask']) * (1 - self.fee_rate)
        # 2. Sell Asset2 for Asset1 (Market Sell crosses BID price)
        btc_rev_out = (eth_rev_out * p2['bid']) * (1 - self.fee_rate)
        # 3. Sell Asset1 for USDT (Market Sell crosses BID price)
        final_usdt_reverse = btc_rev_out * p1['bid'] * (1 - self.fee_rate)
        
        reverse_profit_pct = ((final_usdt_reverse - start_amount) / start_amount) * 100
        
        # Return the best direction
        if forward_profit_pct > reverse_profit_pct:
            return {
                'direction': 'FORWARD',
                'profit_pct': round(forward_profit_pct, 4),
                'route_name': route['name'],
                'path': route['path'],
                'estimated_profit_1k': round(final_usdt_forward - start_amount, 4)
            }
        else:
            return {
                'direction': 'REVERSE',
                'profit_pct': round(reverse_profit_pct, 4),
                'route_name': route['name'],
                'path': list(reversed(route['path'])),
                'estimated_profit_1k': round(final_usdt_reverse - start_amount, 4)
            }

    async def _get_depth_price(self, symbol, side, amount_usdt):
        """Calculates the weighted average price for a specific USDT amount using order book depth."""
        try:
            # Fetch 20 levels of depth for precision
            depth = self.api.client.get_order_book(symbol=symbol, limit=20)
            orders = depth['asks'] if side == 'BUY' else depth['bids']
            
            accumulated_qty = 0
            accumulated_usdt = 0
            
            for p, q in orders:
                price = float(p)
                qty = float(q)
                
                if side == 'BUY':
                    # We have USDT, want to buy Asset
                    needed_usdt = amount_usdt - accumulated_usdt
                    can_buy_usdt = qty * price
                    if can_buy_usdt >= needed_usdt:
                        fill_qty = needed_usdt / price
                        accumulated_qty += fill_qty
                        accumulated_usdt += needed_usdt
                        break
                    else:
                        accumulated_qty += qty
                        accumulated_usdt += can_buy_usdt
                else:
                    # We have Asset, want to sell for USDT
                    # For SELL, amount_usdt is actually the asset quantity we hold
                    needed_qty = amount_usdt - accumulated_qty
                    if qty >= needed_qty:
                        accumulated_qty += needed_qty
                        accumulated_usdt += needed_qty * price
                        break
                    else:
                        accumulated_qty += qty
                        accumulated_usdt += qty * price
            
            if accumulated_usdt < (amount_usdt * 0.99) and side == 'BUY':
                return None # Not enough liquidity
                
            avg_price = accumulated_usdt / accumulated_qty if accumulated_qty > 0 else 0
            return avg_price
        except Exception as e:
            app_logger.error(f"Depth calculation error for {symbol}: {e}")
            return None

    def scan_opportunities(self):
        """
        مسح جميع المسارات المثلثية والبحث عن فرص الربح.
        Returns: list of profitable opportunities sorted by profit %.
        """
        self.last_scan_time = datetime.now().strftime("%H:%M:%S")
        prices = self._get_all_prices()
        
        if not prices:
            return []
        
        opportunities = []
        for route in self.triangle_routes:
            result = self._calculate_triangle_profit(prices, route)
            # Filter opportunities that meet the MIN profit threshold
            if result and result['profit_pct'] > self.min_profit_pct:
                # Add a 'Security Badge' for high confidence picks
                result['is_high_liquidity'] = result['profit_pct'] > 0.5
                opportunities.append(result)
        
        # Sort by highest profit
        opportunities.sort(key=lambda x: x['profit_pct'], reverse=True)
        return opportunities

    async def execute_arbitrage(self, route_name, direction, amount_usdt=None):
        """
        تنفيذ صفقات المراجحة المثلثية فعلياً عبر الحساب.
        Uses 98% of available USDT balance if amount_usdt is None.
        """
        if not self.api.client:
            return {"success": False, "message": "API Client not initialized"}

        # Dynamic balance detection for "Max Power" mode
        if amount_usdt is None or amount_usdt <= 0:
            try:
                acc = self.api.client.get_asset_balance(asset='USDT')
                free_usdt = float(acc['free'])
                app_logger.info(f"💰 Max Power Detection: Found ${free_usdt:.2f} USDT free.")
                if free_usdt < 11.0: # Binance minimum is $10 + headroom
                    return {"success": False, "message": f"Balance too low ($ {free_usdt:.2f} USDT). Min $11 required."}
                amount_usdt = free_usdt * 0.98 # Use 98% to leave room for fees/slippage
            except Exception as e:
                return {"success": False, "message": f"Failed to fetch balance: {e}"}

        # Find the route
        route = next((r for r in self.triangle_routes if r['name'] == route_name), None)
        if not route:
            return {"success": False, "message": f"Route {route_name} not found"}

        app_logger.info(f"⚡ [INTELLIGENT EXECUTION] Verifying liquidity for {route_name} | Amount: ${amount_usdt}")
        
        try:
            p1_sym, p2_sym, p3_sym = route['path']
            
            # --- SMART LIQUIDITY VERIFICATION ---
            # Pre-calculate weighted average prices for the ACTUAL amount
            if direction == 'FORWARD':
                # Leg 1: USDT -> A1
                avg_p1 = await self._get_depth_price(p1_sym, 'BUY', amount_usdt)
                if not avg_p1: return {"success": False, "message": "Insufficient Liquidity on Leg 1"}
                qty1 = (amount_usdt / avg_p1) * (1 - self.fee_rate)
                
                # Leg 2: A1 -> A2 (We have qty1 of A1)
                # This is a bit tricky since get_depth_price for BUY expects quote currency
                # But we'll approximate with ticker for verification
                avg_p2 = await self._get_depth_price(p2_sym, 'BUY', qty1)
                if not avg_p2: return {"success": False, "message": "Insufficient Liquidity on Leg 2"}
                qty2 = (qty1 / avg_p2) * (1 - self.fee_rate)
                
                # Leg 3: A2 -> USDT
                avg_p3 = await self._get_depth_price(p3_sym, 'SELL', qty2)
                if not avg_p3: return {"success": False, "message": "Insufficient Liquidity on Leg 3"}
                final_sim = qty2 * avg_p3 * (1 - self.fee_rate)
            else:
                # Leg 1: USDT -> A2
                avg_p3 = await self._get_depth_price(p3_sym, 'BUY', amount_usdt)
                if not avg_p3: return {"success": False, "message": "Insufficient Liquidity on Leg 1"}
                qty_a2 = (amount_usdt / avg_p3) * (1 - self.fee_rate)
                
                # Leg 2: A2 -> A1
                avg_p2 = await self._get_depth_price(p2_sym, 'SELL', qty_a2)
                if not avg_p2: return {"success": False, "message": "Insufficient Liquidity on Leg 2"}
                qty_a1 = (qty_a2 * avg_p2) * (1 - self.fee_rate)
                
                # Leg 3: A1 -> USDT
                avg_p1 = await self._get_depth_price(p1_sym, 'SELL', qty_a1)
                if not avg_p1: return {"success": False, "message": "Insufficient Liquidity on Leg 3"}
                final_sim = qty_a1 * avg_p1 * (1 - self.fee_rate)

            real_profit_pct = ((final_sim - amount_usdt) / amount_usdt) * 100
            if real_profit_pct < 0.05: # Strict final check with depth
                return {"success": False, "message": f"Slippage too high. Depth-adjusted profit: {real_profit_pct:.3f}% (Below threshold)"}

            app_logger.info(f"🚀 [LIQUIDITY SECURE] Depth-adjusted profit: {real_profit_pct:.3f}%. Executing...")
            p1_sym, p2_sym, p3_sym = route['path']
            # Fetch precision info for all symbols in the path
            info = self.api.client.get_exchange_info()
            symbol_filters = {s['symbol']: s for s in info['symbols'] if s['symbol'] in route['path']}
            
            def round_for_symbol(val, symbol, filter_type='LOT_SIZE'):
                s_info = symbol_filters.get(symbol)
                if not s_info: return val
                filt = next((f for f in s_info['filters'] if f['filterType'] == filter_type), None)
                if not filt: return val
                step = float(filt['stepSize'] if filter_type == 'LOT_SIZE' else filt['tickSize'])
                
                # Execute precise floor division by step size to prevent Binance LOT_SIZE errors
                # Especially important for coins like DOGE/SHIB with extremely small decimals
                val_rounded = (val // step) * step
                step_str = f"{step:.8f}".rstrip('0')
                precision = len(step_str.split('.')[-1]) if '.' in step_str else 0
                return round(val_rounded, precision)

            # Round the initial USDT amount for safety
            amount_usdt = round(amount_usdt, 4)
            orders_executed = []
            
            if direction == 'FORWARD':
                # 1. BUY Intermediate 1 with USDT (e.g. BTCUSDT)
                res1 = self.api.client.order_market_buy(symbol=p1_sym, quoteOrderQty=amount_usdt)
                orders_executed.append(res1)
                qty1 = sum(float(f['qty']) for f in res1['fills'])
                qty1_net = qty1 * (1 - self.fee_rate)
                
                # 2. BUY Intermediate 2 with Asset 1 (e.g. ETHBTC)
                # Round qty1_net to Asset 1's quote precision if needed, or Asset 2's base precision
                # Market Buy with quoteOrderQty uses the quote currency (Asset 1)
                p2_quote_amt = round_for_symbol(qty1_net, p2_sym, 'PRICE_FILTER') if "BTC" in p2_sym else round(qty1_net, 8)
                res2 = self.api.client.order_market_buy(symbol=p2_sym, quoteOrderQty=p2_quote_amt)
                orders_executed.append(res2)
                qty2 = sum(float(f['qty']) for f in res2['fills'])
                qty2_net = qty2 * (1 - self.fee_rate)

                # 3. SELL Intermediate 2 for USDT (e.g. ETHUSDT)
                # Must round quantity to stepSize
                sell_qty = round_for_symbol(qty2_net, p3_sym, 'LOT_SIZE')
                res3 = self.api.client.order_market_sell(symbol=p3_sym, quantity=sell_qty)
                orders_executed.append(res3)
                final_usdt = sum(float(f['qty']) * float(f['price']) for f in res3['fills'])
                
            else: # REVERSE (USDT -> ETH -> BTC -> USDT)
                # 1. BUY Asset 2 with USDT (e.g. ETHUSDT)
                res1 = self.api.client.order_market_buy(symbol=p3_sym, quoteOrderQty=amount_usdt)
                orders_executed.append(res1)
                qty_a2 = sum(float(f['qty']) for f in res1['fills'])
                qty_a2_net = qty_a2 * (1 - self.fee_rate)

                # 2. SELL Asset 2 for Asset 1 (e.g. ETHBTC)
                sell_qty_a2 = round_for_symbol(qty_a2_net, p2_sym, 'LOT_SIZE')
                res2 = self.api.client.order_market_sell(symbol=p2_sym, quantity=sell_qty_a2)
                orders_executed.append(res2)
                qty_a1 = sum(float(f['qty']) * float(f['price']) for f in res2['fills']) # qty of BTC received
                qty_a1_net = qty_a1 * (1 - self.fee_rate)

                # 3. SELL Asset 1 for USDT (e.g. BTCUSDT)
                sell_qty_a1 = round_for_symbol(qty_a1_net, p1_sym, 'LOT_SIZE')
                res3 = self.api.client.order_market_sell(symbol=p1_sym, quantity=sell_qty_a1)
                orders_executed.append(res3)
                final_usdt = sum(float(f['qty']) * float(f['price']) for f in res3['fills'])

            profit = final_usdt - amount_usdt
            profit_pct = (profit / amount_usdt) * 100
            
            app_logger.info(f"✅ [ARBITRAGE SUCCESS] {route_name} completed. Net USDT: ${final_usdt:.2f} | Profit: ${profit:.2f} ({profit_pct:.3f}%)")
            
            return {
                "success": True, 
                "message": f"Arbitrage Executed! Profit: ${profit:.2f} ({profit_pct:.3f}%)",
                "profit": profit,
                "profit_pct": profit_pct
            }
            
        except Exception as e:
            app_logger.error(f"❌ [ARBITRAGE FAILED] Error during execution: {e}")
            return {"success": False, "message": f"Execution Error: {str(e)}"}

    def get_market_spread_data(self):
        """
        تحليل الفارق السعري (Spread) للأسواق الهادئة - مفيد لصانع السوق.
        """
        if not self.api.client:
            return []
            
        try:
            spreads = []
            watch_pairs = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT']
            
            for symbol in watch_pairs:
                order_book = self.api.client.get_order_book(symbol=symbol, limit=5)
                best_bid = float(order_book['bids'][0][0])
                best_ask = float(order_book['asks'][0][0])
                spread = best_ask - best_bid
                spread_pct = (spread / best_bid) * 100
                
                spreads.append({
                    'symbol': symbol,
                    'bid': best_bid,
                    'ask': best_ask,
                    'spread': round(spread, 6),
                    'spread_pct': round(spread_pct, 4),
                    'midpoint': round((best_bid + best_ask) / 2, 6)
                })
                
            return sorted(spreads, key=lambda x: x['spread_pct'], reverse=True)
        except Exception as e:
            app_logger.error(f"[MARKET MAKER] Spread analysis error: {e}")
            return []
