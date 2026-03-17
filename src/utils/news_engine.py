import random
from datetime import datetime
from src.utils.logger import app_logger

class GlobalNewsEngine:
    """PROSOFT AI: Real-Time Global News & Sentiment Engine (Dynamic generation)."""
    
    def __init__(self):
        self.dynamic_insights = []
        self.current_feed = []

    def inject_ai_insight(self, title, type="ADVICE"):
        """Injects a real-time AI generated insight into the ticker."""
        insight = {
            "type": type,
            "impact": "HIGH",
            "source": "PROSOFT AI",
            "title": title,
            "sentiment": 0.7 if type == "ADVICE" else 0.4,
            "time": datetime.now().strftime("%H:%M")
        }
        self.dynamic_insights.insert(0, insight)
        if len(self.dynamic_insights) > 10:
            self.dynamic_insights.pop()

    def generate_market_context_news(self, stats):
        """Generates real-time news based on the bot's current status."""
        symbol = stats.get('symbol', 'BTC')
        price = stats.get('price', 0)
        rsi = stats.get('rsi', 50)
        health = stats.get('market_health', 50)
        
        context_news = []
        
        # Rule-based news generation in Arabic and English
        if rsi > 70:
            context_news.append({"type": "MARKET", "source": "QUANTUM AI", "title": f"ALERT: {symbol} RSI at {rsi:.1f} (Overbought). Probability of correction: HIGH.", "sentiment": 0.3})
            context_news.append({"type": "MARKET", "source": "كوانتوم AI", "title": f"تنبيه: مؤشر RSI لعملة {symbol} عند {rsi:.1f} (تشبع شراء). احتمالية التصحيح: عالية.", "sentiment": 0.3})
        elif rsi < 30:
            context_news.append({"type": "MARKET", "source": "QUANTUM AI", "title": f"OPPORTUNITY: {symbol} RSI at {rsi:.1f} (Oversold). Heavy accumulation detected.", "sentiment": 0.8})
            context_news.append({"type": "MARKET", "source": "كوانتوم AI", "title": f"فرصة: مؤشر RSI لعملة {symbol} عند {rsi:.1f} (تشبع بيع). رصد عمليات تجميع ضخمة.", "sentiment": 0.8})

        if health < 30:
            context_news.append({"type": "BREAKING", "source": "SHIELD", "title": "CRITICAL: Market Health dropping. Manipulation Shield active.", "sentiment": 0.2})
            context_news.append({"type": "BREAKING", "source": "نظام الحماية", "title": "عاجل: انخفاض صحة السوق. تفعيل درع حماية التلاعب فوراً.", "sentiment": 0.2})
        
        if stats.get('whale_alerts'):
            whale = stats['whale_alerts'][0]
            context_news.append({"type": "WHALE", "source": "RADAR", "title": f"WHALE ALERT: {whale}", "sentiment": 0.5})
            context_news.append({"type": "WHALE", "source": "رادار", "title": f"تنبيه حيتان: {whale}", "sentiment": 0.5})

        return context_news

    def refresh_pulse(self, stats=None):
        """Generates a rich and diverse set of global events."""
        stats = stats or {}
        market_news = self.generate_market_context_news(stats)
        
        # Combine dynamic constant news with real-time extracted news
        selected = self.dynamic_insights + market_news
        
        # Add basic fallback if empty
        if not selected:
            selected = [{"type": "INFO", "source": "SYSTEM", "title": "Scanning global order books for institutional signals...", "sentiment": 0.5}]
        
        self.current_feed = []
        avg_sentiment = 0
        
        for item in selected:
            pulse_item = item.copy()
            pulse_item['time'] = datetime.now().strftime("%H:%M")
            self.current_feed.append(pulse_item)
            # Ensure sentiment is a float (defaults to 0.5)
            val = item.get('sentiment', 0.5)
            avg_sentiment += float(val)
            
        mood = avg_sentiment / len(selected) if selected else 0.5
        return {
            'feed': self.current_feed,
            'mood_score': mood * 100,
            'status': "BULLISH" if mood > 0.7 else ("NEUTRAL" if mood > 0.5 else "BEARISH")
        }
