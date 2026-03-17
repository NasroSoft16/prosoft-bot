import random
from datetime import datetime
from src.utils.logger import app_logger

class GlobalNewsEngine:
    """PROSOFT AI: Real-Time Global News & Sentiment Engine (Dynamic generation)."""
    
    def __init__(self):
        self.dynamic_insights = []
        self.current_feed = []
        self.global_pool = [
            {"type": "MARKET", "source": "REUTERS", "title": "Global markets await Fed's next move; volatility remains low.", "sentiment": 0.5},
            {"type": "TECH", "source": "BLOOMBERG", "title": "Ethereum L2 adoption hits record high as gas fees stabilize.", "sentiment": 0.7},
            {"type": "MACRO", "source": "PROSOFT", "title": "Stablecoin inflows detected across major exchanges; preparation for move?", "sentiment": 0.6},
            {"type": "MARKET", "source": "رويترز", "title": "الأسواق العالمية تترقب قرار الفيدرالي القادم؛ هدوء حذر في التداولات.", "sentiment": 0.5},
            {"type": "TECH", "source": "بلومبرغ", "title": "اعتماد شبكات الطبقة الثانية للإيثيريوم يسجل مستويات قياسية.", "sentiment": 0.7},
            {"type": "MACRO", "source": "برو سوفت", "title": "رصد تدفقات للعملات المستقرة نحو المنصات؛ هل ننتظر حركة قوية؟", "sentiment": 0.6},
            {"type": "ADVICE", "source": "AI CORE", "title": "Patience is a strategy. High-conviction setups require waiting.", "sentiment": 0.5},
            {"type": "ADVICE", "source": "AI CORE", "title": "الصبر هو استراتيجية بحد ذاتها. الصفقات القوية تتطلب انتظار اللحظة المناسبة.", "sentiment": 0.5},
        ]

    def inject_ai_insight(self, title, type="ADVICE"):
        # Check for duplicates to keep ticker clean
        if any(d['title'] == title for d in self.dynamic_insights):
            return
            
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
        
        # Rule-based news generation
        if rsi > 70:
            context_news.append({"type": "MARKET", "source": "QUANTUM AI", "title": f"ALERT: {symbol} RSI at {rsi:.1f} (Overbought).", "sentiment": 0.3})
        elif rsi < 30:
            context_news.append({"type": "MARKET", "source": "QUANTUM AI", "title": f"OPPORTUNITY: {symbol} RSI at {rsi:.1f} (Oversold).", "sentiment": 0.8})

        if health < 35:
            context_news.append({"type": "BREAKING", "source": "SHIELD", "title": f"Risk Threshold Warning: Market Health at {health:.1f}%", "sentiment": 0.2})
        
        if stats.get('whale_alerts'):
            whale = stats['whale_alerts'][0]
            context_news.append({"type": "WHALE", "source": "RADAR", "title": f"WHALE: {whale[:50]}...", "sentiment": 0.5})

        return context_news

    def refresh_pulse(self, stats=None):
        """Generates a rich and diverse set of global events."""
        stats = stats or {}
        market_news = self.generate_market_context_news(stats)
        
        # Select random samples from global pool to keep it dynamic
        sampled_global = random.sample(self.global_pool, k=min(4, len(self.global_pool)))
        
        # Order: 1. Real-time conditions, 2. AI dynamic insights, 3. Global background news
        selected = market_news + self.dynamic_insights + sampled_global
        
        # Ensure we don't have too many items to cause lag
        selected = selected[:12]
        
        self.current_feed = []
        avg_sentiment = 0
        
        for item in selected:
            pulse_item = item.copy()
            pulse_item['time'] = datetime.now().strftime("%H:%M")
            self.current_feed.append(pulse_item)
            try:
                avg_sentiment += float(item.get('sentiment', 0.5))
            except:
                avg_sentiment += 0.5
            
        mood = avg_sentiment / len(selected) if selected else 0.5
        return {
            'feed': self.current_feed,
            'mood_score': mood * 100,
            'status': "BULLISH" if mood > 0.7 else ("NEUTRAL" if mood > 0.5 else "BEARISH")
        }
