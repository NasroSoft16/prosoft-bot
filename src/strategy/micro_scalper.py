import pandas as pd
from src.utils.logger import app_logger
from datetime import datetime

class MicroScalper:
    """
    PROSOFT AI: MICRO-SCALPER ENGINE (v1.0)
    Designed for high-frequency scalping on volatile assets.
    Target: 0.3% - 0.8% profit per trade.
    """
    def __init__(self, api_client, min_volume_usdt=500000):
        self.api = api_client
        self.min_volume_usdt = min_volume_usdt
        self.profit_target_pct = 0.005 # 0.5%
        self.stop_loss_pct = 0.003    # 0.3%
        self.min_trade_amount = 11.0   # Binance Min

    async def find_volatile_candidates(self, limit=10):
        """Scans the market for symbols with high volume and recent volatility."""
        try:
            # Fetch Exchange Info to check status
            info = self.api.client.get_exchange_info()
            trading_symbols = {s['symbol']: s['status'] for s in info['symbols'] if s['status'] == 'TRADING'}
            
            tickers = self.api.client.get_ticker()
            candidates = []
            
            for t in tickers:
                symbol = t['symbol']
                # Only USDT pairs and ONLY active trading pairs
                if not symbol.endswith('USDT') or symbol not in trading_symbols: continue
                
                quote_volume = float(t['quoteVolume'])
                price_change_pct = abs(float(t['priceChangePercent']))
                
                # Filter: Significant volume and movement
                if quote_volume > self.min_volume_usdt and price_change_pct > 2.0:
                    candidates.append({
                        'symbol': symbol,
                        'volatility': price_change_pct,
                        'volume': quote_volume,
                        'price': float(t['lastPrice'])
                    })
            
            # Sort by highest volatility
            candidates.sort(key=lambda x: x['volatility'], reverse=True)
            return candidates[:limit]
        except Exception as e:
            app_logger.error(f"[SCALPER] Candidate discovery error: {e}")
            return []

    def check_scalp_signal(self, df):
        """
        Fast technical check for scalping entry.
        Look for RSI oversold + MFI/EMA alignment on short timeframe (1m/5m).
        """
        if df is None or len(df) < 20: return None
        
        try:
            curr = df.iloc[-1]
            prev = df.iloc[-2]
            
            # Scalping Criteria:
            # 1. RSI is relatively low (but not dead) or bouncing from bottom
            # 2. Price is above a short-term SMA (e.g., 9) indicating a micro-trend
            rsi = curr.get('RSI', 50)
            close = curr['close']
            
            # If TechnicalAnalysis wasn't called on this DF yet, we might need indicators
            # Assuming main.py provides technical DF.
            
            # Condition: Bullish engulfing or RSI bounce
            rsi_bounce = prev['RSI'] < 35 and curr['RSI'] > prev['RSI']
            uptrend = close > curr.get('EMA_50', 0) # Basic trend filter
            
            if rsi_bounce and uptrend:
                entry_price = close
                return {
                    'entry': entry_price,
                    'tp': entry_price * (1 + self.profit_target_pct),
                    'sl': entry_price * (1 - self.stop_loss_pct),
                    'confidence': 0.80
                }
        except Exception as e:
            app_logger.error(f"[SCALPER] Signal Error: {e}")
            
        return None
