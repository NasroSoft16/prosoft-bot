import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from src.utils.logger import app_logger

class QuantumIntelligence:
    """The advanced brain of the Trading Entity."""
    
    def __init__(self, gemini=None):
        self.reg_model = LinearRegression()
        self.gemini = gemini

    async def calculate_market_health(self, df, skip_ai=False):
        """Calculates a health score using technical indicators and Gemini AI for context."""
        try:
            if len(df) < 10:
                return 45.0
                
            # 1. Technical Health (Recalibrated for Stability)
            ema20 = df['close'].ewm(span=20).mean()
            # Calculate slope over 10 periods
            slope_pct = ((ema20.iloc[-1] - ema20.iloc[-10]) / ema20.iloc[-10]) * 100
            
            # RSI factor: If RSI is 0 or 100, it's usually bad data or extreme volatility
            rsi = df.get('RSI', pd.Series([50])).iloc[-1]
            if rsi <= 0 or rsi >= 100:
                rsi_health = 25 # Penalty for extreme/bad data
            else:
                rsi_health = 50 - abs(50 - rsi) # Best (50) at RSI 50
            
            # Base of 55 (slightly positive). Slope impact reduced from 30x to 15x
            tech_health = 55 + (slope_pct * 15) + (rsi_health * 0.4)
            tech_health = max(15, min(90, tech_health)) # New floor is 15% for technicals
            
            # 2. AI Enhancement
            if not skip_ai and self.gemini and self.gemini.api_keys:
                prompt = (f"Market Context: Trend={slope_pct:.2f}%, RSI={rsi:.1f}. "
                         f"Recent Closes: {df['close'].tail(5).tolist()}. "
                         "Rate market health 0-100 (Safety score). Return ONLY number.")
                ai_score = await self.gemini.ask(prompt)
                try: 
                    import re
                    match = re.search(r"(\d+\.?\d*)", str(ai_score))
                    if match:
                        ai_val = float(match.group(1))
                        # Weighted: 70% Technical (Real Data), 30% AI (Sentiment)
                        return max(0, min(100, (tech_health * 0.7) + (ai_val * 0.3)))
                except: pass
            
            return tech_health
        except Exception as e:
            app_logger.error(f"Health Calculation Error: {e}")
            return 45.0

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
