import os
import ta
from src.utils.logger import app_logger
from src.ai.quantum_intelligence import QuantumIntelligence
import random # Added for WhaleTracker simulation

class MarketScanner:
    def __init__(self, api_wrapper):
        self.api = api_wrapper
        self.intel = QuantumIntelligence()
        
        # Load user-defined blacklist from env, or use default stablecoin list
        env_blacklist = os.getenv('BLACKLISTED_COINS', 'USDC,FDUSD,TUSD,USDP,EUR,BUSD,USD1,DAI,USDD,PYUSD,AEUR,GBP,EURI,RLUSD')
        self.blacklist = [coin.strip().upper() for coin in env_blacklist.split(',')]
        self.crash_shield_active = False

    def get_btc_dominance_state(self):
        """Proxies market dominance by comparing BTC volume to top Alts."""
        try:
            tickers = self.api.client.get_ticker()
            btc_vol = 0
            alts_vol = 0
            for t in tickers:
                if t['symbol'] == 'BTCUSDT':
                    btc_vol = float(t['quoteVolume'])
                elif t['symbol'].endswith('USDT'):
                    alts_vol += float(t['quoteVolume'])
            
            # Dominance proxy (BTC Vol / Total USDT Vol)
            total_vol = btc_vol + alts_vol
            dom = (btc_vol / total_vol) * 100 if total_vol > 0 else 50
            
            # If BTC Vol is > 65% of total top volume, it often signals a liquidity drain from alts (Crash Risk)
            is_risky = dom > 60
            return {"dominance": dom, "is_risky": is_risky}
        except:
            return {"dominance": 50, "is_risky": False}

    def get_top_pairs(self, limit=25):
        """Fetches explosive momentum pairs from Binance (High Change + Solid Liquidity)."""
        try:
            tickers = self.api.client.get_ticker()
            # Filter USDT pairs with minimum volume ($15M) to avoid slippage traps
            usdt_pairs = []
            for t in tickers:
                sym = t['symbol']
                if sym.endswith('USDT') and float(t['quoteVolume']) > 15000000:
                    # Check if any blacklisted token is part of the symbol
                    is_blacklisted = any(blocked in sym for blocked in self.blacklist)
                    if not is_blacklisted:
                        usdt_pairs.append(t)
                        
            # Sort by 24h price percentage change to catch explosive momentum (Pumps)
            sorted_pairs = sorted(usdt_pairs, key=lambda x: float(x.get('priceChangePercent', 0)), reverse=True)
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
            
            # --- DYNAMIC VOLATILITY FILTER (Stablecoin/Dead Coin Detector) ---
            recent_high = df['high'].tail(20).max()
            recent_low = df['low'].tail(20).min()
            if recent_low > 0:
                volatility_ratio = (recent_high - recent_low) / recent_low
                if volatility_ratio < 0.005:  # Less than 0.5% movement in 20 candles
                    # print(f"Skipping {symbol}: Dead Volume/Stablecoin (Volatility={volatility_ratio:.4f})")
                    return None
            # -----------------------------------------------------------------
            
            # Indicators
            df['EMA_20'] = ta.trend.ema_indicator(df['close'], window=20)
            df['EMA_50'] = ta.trend.ema_indicator(df['close'], window=50)
            df['RSI'] = ta.momentum.rsi(df['close'], window=14)
            
            curr = df.iloc[-1]
            
            # Intelligence (Lighter version for fast scanning)
            prediction = self.intel.predict_next_price(df)
            
            # Momentum Upgrades (v12.5)
            df['VOL_EMA'] = df['volume'].rolling(window=20).mean()
            vol_spike = curr['volume'] > (df['VOL_EMA'].iloc[-1] * 1.5) # Loosened from 1.8 to 1.5
            
            # RSI Slope (Acceleration)
            rsi_prev = df['RSI'].iloc[-5]
            rsi_slope = (curr['RSI'] - rsi_prev) / 5
            
            # Scoring
            score = 30 # Base
            if curr['close'] > curr['EMA_20']: score += 15 # More weighted towards fast EMA
            if curr['close'] > curr['EMA_50']: score += 10
            if rsi_slope > 1.5: score += 20     # Loosened acceleration
            if vol_spike: score += 25          # More reward for volume
            if 35 <= curr['RSI'] <= 65: score += 10 # Wider active RSI zone
            elif curr['RSI'] < 35: score += 15 # Bounce potential broadened
            
            # Prediction bonus
            if prediction and prediction['direction'] == 'UP': score += 15

            # Reasons
            reasons = []
            if vol_spike: reasons.append("Institutional Vol Spike")
            if rsi_slope > 1.5: reasons.append("Zheng Acceleration")
            if curr['close'] > curr['EMA_20']: reasons.append("Price above EMA20")

            return {
                'symbol': symbol,
                'price': float(curr['close']),
                'rsi': float(curr['RSI']),
                'score': int(score),
                'health': int(score), # Sync health to momentum for scan mode
                'sentiment': "BULLISH ACCEL" if rsi_slope > 1.5 else "SCANNING",
                'prediction': prediction,
                'reasoning': reasons
            }
        except Exception as e:
            app_logger.error(f"Error analyzing {symbol}: {e}")
            return None

    def scan_market(self):
        """Scans multiple pairs for opportunities."""
        symbols = self.get_top_pairs(limit=25)
        results = []
        for sym in symbols:
            analysis = self.analyze_symbol(sym)
            # Relaxed threshold to ensure list is not empty (Dropped from 50 to 40)
            if analysis and analysis['score'] >= 40:
                results.append(analysis)
        return sorted(results, key=lambda x: x['score'], reverse=True)
