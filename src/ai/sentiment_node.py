from src.utils.logger import app_logger

class AISentimentFrontRunner:
    """PROSOFT AI: Quantum Sentiment Front-Runner"""
    
    def __init__(self, gemini_engine, news_engine):
        self.gemini = gemini_engine
        self.news_engine = news_engine
        
    async def analyze_and_front_run(self):
        """
        Analyzes the latest news feed via Gemini and decides if a 'Front-Run' buy is needed.
        """
        if not self.gemini or not self.news_engine: return None
        
        pulse = self.news_engine.refresh_pulse()
        latest_news = pulse['feed'][0]['title'] if pulse['feed'] else "No news"
        
        prompt = (
            f"LATEST CRYPTO NEWS: '{latest_news}'\n"
            "As an elite AI trader, is this news powerful enough to cause a 5% pump in 10 minutes? "
            "If YES, name the likely target symbol (e.g., BTC, ETH, SOL) and respond ONLY with 'ACTION:SYMBOL'. "
            "If NO, respond with 'NO_ACTION'."
        )
        
        decision = await self.gemini.ask(prompt)
        
        if decision and "ACTION:" in decision.upper():
            symbol = decision.split(":")[1].strip().upper()
            if not symbol.endswith('USDT'): symbol += 'USDT'
            
            app_logger.critical(f"🧠 [AI FRONT-RUNNER] DECISION: BUY {symbol} BASED ON NEWS: {latest_news}")
            return {
                'symbol': symbol,
                'reason': latest_news,
                'confidence': 0.95
            }
            
        return None
