import os
import ta
from src.utils.logger import app_logger
from src.ai.quantum_intelligence import QuantumIntelligence

class MarketScanner:
    def __init__(self, api_wrapper):
        self.api = api_wrapper
        self.intel = QuantumIntelligence()
        
        # Load user-defined blacklist from env, or use default stablecoin list
        env_blacklist = os.getenv('BLACKLISTED_COINS', 'USDC,FDUSD,TUSD,USDP,EUR,BUSD,USD1,DAI,USDD,PYUSD,AEUR,GBP,EURI')
        self.blacklist = [coin.strip().upper() for coin in env_blacklist.split(',')]

    def get_top_pairs(self, limit=20):
        """Fetches top volume pairs from Binance."""
        try:
            tickers = self.api.client.get_ticker()
            # Filter USDT pairs with positive volume AND ensure they are not in the blacklist
            usdt_pairs = []
            for t in tickers:
                sym = t['symbol']
                if sym.endswith('USDT') and float(t['quoteVolume']) > 0:
                    # Check if any blacklisted token is part of the symbol (e.g., USDCUSDT)
                    is_blacklisted = any(blocked in sym for blocked in self.blacklist)
                    if not is_blacklisted:
                        usdt_pairs.append(t)
                        
            # Sort by volume
            sorted_pairs = sorted(usdt_pairs, key=lambda x: float(x['quoteVolume']), reverse=True)
            return [t['symbol'] for t in sorted_pairs[:limit]]
        except Exception as e:
            app_logger.error(f"Error fetching top pairs: {e}")
            return ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'ADAUSDT']

    def analyze_symbol(self, symbol, timeframe='1h'):
        """Analyzes a specific symbol and returns score."""
        try:
            df = self.api.get_historical_klines(symbol, timeframe, limit=100)
            if df is None or len(df) < 50:
                return None
            
            # Indicators
            df['EMA_20'] = ta.trend.ema_indicator(df['close'], window=20)
            df['EMA_50'] = ta.trend.ema_indicator(df['close'], window=50)
            df['RSI'] = ta.momentum.rsi(df['close'], window=14)
            
            curr = df.iloc[-1]
            
            # Intelligence (Lighter version for fast scanning)
            prediction = self.intel.predict_next_price(df)
            
            # Momentum Upgrades (v12.5)
            df['VOL_EMA'] = df['volume'].rolling(window=20).mean()
            vol_spike = curr['volume'] > (df['VOL_EMA'].iloc[-1] * 1.8) # 80% volume spike
            
            # RSI Slope (Acceleration)
            rsi_prev = df['RSI'].iloc[-5]
            rsi_slope = (curr['RSI'] - rsi_prev) / 5
            
            # Scoring
            score = 30 # Base
            if curr['close'] > curr['EMA_20'] > curr['EMA_50']: score += 20
            if rsi_slope > 2: score += 25 # Rapidly growing momentum
            if vol_spike: score += 20     # Liquid influx
            if 40 <= curr['RSI'] <= 60: score += 10
            elif curr['RSI'] < 30: score += 15 # Bounce potential
            
            # Prediction bonus
            if prediction and prediction['direction'] == 'UP': score += 10

            # Reasons
            reasons = []
            if vol_spike: reasons.append("Institutional Vol Spike")
            if rsi_slope > 2: reasons.append("Zheng Acceleration")
            if curr['close'] > curr['EMA_20']: reasons.append("Price above EMA20")

            return {
                'symbol': symbol,
                'price': float(curr['close']),
                'rsi': float(curr['RSI']),
                'score': int(score),
                'health': int(score), # Sync health to momentum for scan mode
                'sentiment': "BULLISH ACCEL" if rsi_slope > 2 else "SCANNING",
                'prediction': prediction,
                'reasoning': reasons
            }
        except Exception as e:
            app_logger.error(f"Error analyzing {symbol}: {e}")
            return None

    def scan_market(self):
        """Scans multiple pairs for opportunities."""
        symbols = self.get_top_pairs(limit=15)
        results = []
        for sym in symbols:
            analysis = self.analyze_symbol(sym)
            # Relaxed threshold to ensure list is not empty
            if analysis and analysis['score'] >= 50:
                results.append(analysis)
        return sorted(results, key=lambda x: x['score'], reverse=True)
