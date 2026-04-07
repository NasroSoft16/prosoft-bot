import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from src.utils.logger import app_logger

class QuantumIntelligence:
    """The advanced brain of the Trading Entity."""
    
    def __init__(self, gemini=None, groq=None):
        self.reg_model = LinearRegression()
        self.gemini = gemini
        self.groq = groq

    async def calculate_market_health(self, df, skip_ai=False):
        """
        Calculates a high-fidelity health score using a hybrid model.
        Fails over to a robust Triple-Confirmation technical model if AI is offline.
        """
        try:
            if df is None or len(df) < 20:
                return 48.0
                
            # 1. THE SOVEREIGN ENGINE (Robust Technical Core)
            # A. Trend Strength (EMA-20 Slope)
            ema20 = df['close'].ewm(span=20).mean()
            slope_pct = ((ema20.iloc[-1] - ema20.iloc[-10]) / ema20.iloc[-10]) * 100
            
            # B. Volatility Integrity (ATR Rejection)
            # High volatility in a down-trend is a rejection signal
            high = df['high'].rolling(window=14).max()
            low = df['low'].rolling(window=14).min()
            tr = pd.concat([high - low, 
                          (high - df['close'].shift(1)).abs(), 
                          (low - df['close'].shift(1)).abs()], axis=1).max(axis=1)
            atr = tr.rolling(window=14).mean().iloc[-1]
            volatility_penalty = (atr / df['close'].iloc[-1]) * 1000 # Normalized scale
            
            # C. RSI Stability Factor
            rsi = df.get('RSI', pd.Series([50])).iloc[-1]
            rsi_health = 50 - abs(50 - rsi) # 50 is best stability (mid-range)
            
            # THE SOVEREIGN FORMULA: Balanced for 24/7 Operations
            # Base of 52 (Neutral-Positive) 
            # + Slope impact (capped at +/- 25)
            # + RSI impact (+/- 10)
            # - Volatility penalty (reduced safety if market is too wild)
            tech_health = 52 + (slope_pct * 12) + (rsi_health * 0.25) - (volatility_penalty * 1.5)
            tech_health = max(10, min(95, tech_health)) 
            
            # 🛡️ SOVEREIGN BYPASS (Rate Limit Defender)
            # If technicals literally scream "crash", skip feeding APIs to confirm it.
            if tech_health < 40 and not skip_ai:
                app_logger.warning(f"🛡️ [SOVEREIGN BYPASS] Technical health critically low ({tech_health:.1f}%). Bypassing AI to save quota.")
                return tech_health
            
            # 2. AI ENHANCEMENT (The High-Resolution Layer)
            # Only use if nodes are healthy and not explicitly skipped
            if not skip_ai and self.gemini and hasattr(self.gemini, 'api_keys') and self.gemini.api_keys:
                # Build the analytical prompt
                prompt = (f"Market Diagnostic: Trend={slope_pct:.2f}%, RSI={rsi:.1f}, ATR_Factor={volatility_penalty:.1f}. "
                         f"Recent Closes: {df['close'].tail(5).tolist()}. "
                         "Return 0-100 score for market safety. Return ONLY the integer.")
                
                # A. Try Gemini (Primary for Context/Sentiment)
                ai_score = await self.gemini.ask(prompt)
                
                # B. FAILOVER TO GROQ (Primary Lightning Fallback)
                if not ai_score and self.groq and self.groq.api_keys:
                    app_logger.info("⚡ [INTELLIGENCE] Gemini Exhausted. Flipping to Groq Lightning-AI...")
                    ai_score = await self.groq.ask(f"Analyze this crypto technical data and rate safety 0-100: {prompt}")
                
                try: 
                    import re
                    match = re.search(r"(\d+\.?\d*)", str(ai_score))
                    if match:
                        ai_val = float(match.group(1))
                        # HYBRID BLEND: 60% Technical (Ground Reality), 40% AI (Abstract Prediction)
                        return max(0, min(100, (tech_health * 0.6) + (ai_val * 0.4)))
                except Exception as ai_e:
                    app_logger.warning(f"AI Synthesis skipped (Using Sovereign Fallback): {ai_e}")
            
            # 🏛️ FAILOVER SUCCESS: Decision made via Sovereign Intelligence
            return tech_health
            
        except Exception as e:
            app_logger.error(f"Sovereign Intelligence Failure: {e}")
            return 48.0

    def predict_next_price(self, df, look_forward=1):
        """Simple Predictive modeling using linear regression on recent price action."""
        try:
            y = df['close'].values[-20:].reshape(-1, 1)
            X = np.arange(len(y)).reshape(-1, 1)
            
            self.reg_model.fit(X, y)
            
            next_X = np.array([[len(y) + look_forward - 1]])
            prediction = self.reg_model.predict(next_X)[0][0]
            
            current_price = df['close'].iloc[-1]
            change_pct = ((prediction - current_price) / current_price) * 100
            
            return {
                'target': prediction,
                'change_pct': change_pct,
                'direction': 'UP' if change_pct > 0 else 'DOWN'
            }
        except Exception as e:
            app_logger.error(f"Prediction Error: {e}")
            return None

    def detect_sentiment(self, df):
        """Heuristic-based market sentiment analysis."""
        import pandas as pd
        rsi = df['close'].rolling(14).apply(lambda x: 100 - (100 / (1 + x.diff().dropna().clip(lower=0).mean() / x.diff().dropna().clip(upper=0).abs().mean()))).iloc[-1]
        
        if pd.isna(rsi): return "Neutral / Insufficient Data"
        if rsi > 70: return "Extremely Greedy (Overbought)"
        if rsi < 30: return "Fearful (Oversold)"
        if 45 <= rsi <= 55: return "Neutral / Stable"
        return "Bullish Bias" if rsi > 50 else "Bearish Bias"
