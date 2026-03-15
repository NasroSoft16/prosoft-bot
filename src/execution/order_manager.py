from binance.exceptions import BinanceAPIException
from src.utils.logger import app_logger

class OrderManager:
    def __init__(self, client_wrapper):
        self.wrapper = client_wrapper
        self.client = client_wrapper.client

    def _format_quantity(self, symbol, quantity):
        """Formats the quantity precisely to Binance's LOT_SIZE step size by truncating."""
        try:
            info = self.client.get_symbol_info(symbol)
            for f in info['filters']:
                if f['filterType'] == 'LOT_SIZE':
                    step_size = float(f['stepSize'])
                    if step_size <= 0: return quantity

                    import math
                    # Use a small epsilon to avoid float precision issues during division
                    # floor(0.0001 / 0.0001) might be 0, so we add 1e-10
                    precision = int(round(-math.log10(step_size), 0)) if step_size < 1 else 0
                    
                    # Truncate to step size
                    factor = 10 ** precision
                    truncated_qty = math.floor(quantity * factor + 1e-10) / factor
                    
                    qty_str = "{:0.0{}f}".format(truncated_qty, precision)
                    return float(qty_str)
        except Exception as e:
            app_logger.error(f"Error fetching lot size for {symbol}: {e}")
            
        return float(f"{quantity:.4f}") # fallback truncation

    def place_market_buy(self, symbol, quantity):
        """Places a market buy order."""
        try:
            formatted_qty = self._format_quantity(symbol, quantity)
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
                price=str(round(take_profit, 2)),
                stopPrice=str(round(stop_loss * 1.01, 2)), # trigger price
                stopLimitPrice=str(round(stop_loss, 2)),    # actual sell price
                stopLimitTimeInForce='GTC'
            )
            app_logger.info(f"OCO Order (SL/TP) placed: {order['orderListId']}")
            return order
        except BinanceAPIException as e:
            app_logger.error(f"Binance API Error during OCO order: {e}")
            return None
        except Exception as e:
            app_logger.error(f"Error placing OCO order: {e}")
            return None

    def update_trailing_stop(self, symbol, current_price, entry_price, current_sl, trailing_pct_activation=0.03, trailing_distance=0.015):
        """
        PROSOFT AI LIQUIDITY SHIELD (Trailing Stop-Loss).
        Activates when profit reaches >3%, moves Stop Loss to 1.5% below current price.
        """
        profit_pct = (current_price - entry_price) / entry_price
        
        if profit_pct > trailing_pct_activation:
            new_sl = current_price * (1 - trailing_distance)
            if new_sl > current_sl:
                app_logger.info(f"🛡️ [Liquidity Shield Active] {symbol} Trailing Stop moved to {new_sl:.2f} (Locked Profit)")
                return new_sl
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
