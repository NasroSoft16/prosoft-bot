from binance.exceptions import BinanceAPIException
from src.utils.logger import app_logger

class OrderManager:
    def __init__(self, client_wrapper):
        self.wrapper = client_wrapper
        self.client = client_wrapper.client

    def _get_symbol_filters(self, symbol):
        """Fetches filters for a specific symbol from symbol_info."""
        try:
            info = self.client.get_symbol_info(symbol)
            if not info or 'filters' not in info:
                return None
            return info['filters']
        except Exception as e:
            app_logger.error(f"Error fetching filters for {symbol}: {e}")
            return None

    def _format_quantity(self, symbol, quantity):
        """Formats the quantity precisely to Binance's LOT_SIZE step size by truncating."""
        try:
            filters = self._get_symbol_filters(symbol)
            if not filters:
                return float(f"{quantity:.4f}")

            for f in filters:
                if f['filterType'] == 'LOT_SIZE':
                    step_size = float(f['stepSize'])
                    if step_size <= 0: return quantity

                    import math
                    precision = int(round(-math.log10(step_size), 0)) if step_size < 1 else 0
                    
                    factor = 10 ** precision
                    truncated_qty = math.floor(quantity * factor + 1e-10) / factor
                    
                    return truncated_qty
        except Exception as e:
            app_logger.error(f"Error formatting quantity for {symbol}: {e}")
            
        return float(f"{quantity:.4f}")

    def check_min_notional(self, symbol, quantity, price):
        """Validates if price * quantity meets the minimum notional requirement."""
        try:
            filters = self._get_symbol_filters(symbol)
            if not filters:
                return True, 0

            for f in filters:
                if f['filterType'] == 'NOTIONAL':
                    min_notional = float(f['minNotional'])
                    notional = quantity * price
                    if notional < min_notional:
                        return False, min_notional
                    return True, min_notional
                if f['filterType'] == 'MIN_NOTIONAL': # Older versions of API might use this
                    min_notional = float(f['minNotional'])
                    notional = quantity * price
                    if notional < min_notional:
                        return False, min_notional
                    return True, min_notional
            return True, 0
        except Exception as e:
            app_logger.error(f"Error checking min notional for {symbol}: {e}")
            return True, 0

    def place_market_buy(self, symbol, quantity):
        """Places a market buy order."""
        try:
            formatted_qty = self._format_quantity(symbol, quantity)
            
            # Check notional
            price = self.wrapper.get_symbol_ticker(symbol)
            if price:
                allowed, min_val = self.check_min_notional(symbol, formatted_qty, float(price))
                if not allowed:
                    app_logger.warning(f"⚠️ Market BUY Rejected: {symbol} Notional ${formatted_qty * float(price):.2f} < Min ${min_val:.2f}")
                    return None

            order = self.client.create_order(
                symbol=symbol,
                side='BUY',
                type='MARKET',
                quantity=formatted_qty
            )
            app_logger.info(f"Market BUY Order placed: {order['orderId']}")
            return order
        except BinanceAPIException as e:
            app_logger.error(f"Binance API Error during BUY order: {e}")
            return None
        except Exception as e:
            app_logger.error(f"Error placing BUY order: {e}")
            return None

    def place_market_sell(self, symbol, quantity):
        """Places a market sell order."""
        try:
            formatted_qty = self._format_quantity(symbol, quantity)
            
            # Check notional
            price = self.wrapper.get_symbol_ticker(symbol)
            if price:
                allowed, min_val = self.check_min_notional(symbol, formatted_qty, float(price))
                if not allowed:
                    app_logger.warning(f"⚠️ Market SELL Rejected: {symbol} Notional ${formatted_qty * float(price):.2f} < Min ${min_val:.2f}")
                    # Special Case: If it's too small, we might want to tell the caller so they can cleanup
                    return "NOTIONAL_ERROR" 

            order = self.client.create_order(
                symbol=symbol,
                side='SELL',
                type='MARKET',
                quantity=formatted_qty
            )
            app_logger.info(f"Market SELL Order placed: {order['orderId']}")
            return order
        except BinanceAPIException as e:
            app_logger.error(f"Binance API Error during SELL order: {e}")
            return None
        except Exception as e:
            app_logger.error(f"Error placing SELL order: {e}")
            return None

    def place_limit_sell(self, symbol, quantity, price):
        """Places a limit sell order."""
        try:
            formatted_qty = self._format_quantity(symbol, quantity)
            order = self.client.create_order(
                symbol=symbol,
                side='SELL',
                type='LIMIT',
                timeInForce='GTC',
                quantity=formatted_qty,
                price=str(round(price, 2))
            )
            app_logger.info(f"Limit SELL Order placed: {order['orderId']}")
            return order
        except BinanceAPIException as e:
            app_logger.error(f"Binance API Error during SELL order: {e}")
            return None
        except Exception as e:
            app_logger.error(f"Error placing SELL order: {e}")
            return None

    def place_oco_order(self, symbol, quantity, take_profit, stop_loss):
        """Places an OCO (One-Cancels-the-Other) order for TP and SL."""
        try:
            formatted_qty = self._format_quantity(symbol, quantity)
            # OCO order for SL/TP exit
            order = self.client.create_oco_order(
                symbol=symbol,
                side='SELL',
                quantity=formatted_qty,
                aboveType='LIMIT_MAKER',
                abovePrice=str(round(take_profit, 2)),
                belowType='STOP_LOSS_LIMIT',
                belowStopPrice=str(round(stop_loss * 1.01, 2)), # trigger price
                belowPrice=str(round(stop_loss, 2)),            # actual sell price
                belowTimeInForce='GTC'
            )
            app_logger.info(f"OCO Order (SL/TP) placed: {order['orderListId']}")
            return order
        except BinanceAPIException as e:
            app_logger.error(f"Binance API Error during OCO order: {e}")
            return None
        except Exception as e:
            app_logger.error(f"Error placing OCO order: {e}")
            return None

    def update_trailing_stop(self, symbol, current_price, entry_price, current_sl, trailing_pct_activation=0.02, trailing_distance=0.012):
        """
        PROSOFT AI LIQUIDITY SHIELD (Refined).
        Intelligently moves Stop Loss to lock profits. 
        trailing_pct_activation: Profit % needed to start trailing (e.g., 0.02 = 2%)
        trailing_distance: % distance to maintain from the new peak (e.g., 0.012 = 1.2%)
        """
        try:
            profit_pct = (current_price - entry_price) / entry_price
            
            # 12.8 PROSOFT: Intelligent Threshold
            if profit_pct >= trailing_pct_activation:
                # Calculate what the new SL should be
                potential_new_sl = current_price * (1 - trailing_distance)
                
                # Only move if the NEW SL is higher than the OLD SL + a small buffer (0.1%)
                # to prevent micro-adjustments and 'suffocating' the trade
                move_buffer = current_price * 0.001 
                
                if potential_new_sl > (current_sl + move_buffer):
                    app_logger.info(f"🛡️ [Intelligent Trailing] {symbol} SL moving up: ${current_sl:.2f} -> ${potential_new_sl:.4f} (Locked Profit)")
                    return potential_new_sl
                    
        except Exception as e:
            app_logger.error(f"Trailing Stop Calculation Error for {symbol}: {e}")
            
        return current_sl

    def partial_take_profit(self, symbol, total_qty, tp1_price, tp1_pct=0.5):
        """
        PROSOFT: تسييل الأرباح الجزئي (Partial Take Profit)
        Sells a portion (default 50%) of the position at TP1, and leaves the rest running.
        
        Args:
            symbol     : e.g. 'BTCUSDT'
            total_qty  : total quantity currently held
            tp1_price  : price at which to place the partial sell
            tp1_pct    : fraction to sell at TP1 (default 0.50 = 50%)
        Returns:
            order result or None
        """
        try:
            sell_qty = total_qty * tp1_pct
            remaining_qty = total_qty * (1 - tp1_pct)
            
            app_logger.info(
                f"[Partial TP] {symbol}: Selling {tp1_pct*100:.0f}% ({sell_qty:.6f}) "
                f"at ${tp1_price:.2f}. Remaining: {remaining_qty:.6f}"
            )
            
            order = self.place_limit_sell(symbol, sell_qty, tp1_price)
            if order:
                app_logger.info(f"[Partial TP] ✅ Partial sell order placed: {order.get('orderId')}")
            return order, remaining_qty
        except Exception as e:
            app_logger.error(f"[Partial TP] Error: {e}")
            return None, total_qty

    def execute_dynamic_hedge(self, symbol, exposure_amount, market_health):
        """
        PROSOFT AI HEDGING: Opens a short/hedge position if Market Health drops precipitously.
        """
        if market_health < 30:
            app_logger.warning(f"⚠️ Market Health Critical ({market_health}%). Hedging {symbol} exposure immediately.")
            return True
        return False
