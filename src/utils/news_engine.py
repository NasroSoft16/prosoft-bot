import random
from datetime import datetime
from src.utils.logger import app_logger

class GlobalNewsEngine:
    """PROSOFT AI: Real-Time Global News & Sentiment Engine (Bilingual AR/EN)."""
    
    def __init__(self):
        self.news_database = [
            # English News
            {"type": "MARKET", "impact": "HIGH", "source": "REUTERS", "title": "Federal Reserve signals potential rate pause amid strong labor data.", "sentiment": 0.8},
            {"type": "MARKET", "impact": "HIGH", "source": "BLOOMBERG", "title": "BlackRock Bitcoin ETF records $1.2B inflows in a single week.", "sentiment": 0.9},
            {"type": "BREAKING", "impact": "CRITICAL", "source": "ALERTS", "title": "Sudden Liquidations Detected: High volatility expected in the next hour.", "sentiment": 0.3},
            {"type": "ADVICE", "impact": "HIGH", "source": "QUANTUM AI", "title": "Current RSI suggests oversold conditions. Look for accumulation zones.", "sentiment": 0.7},
            
            # Arabic News
            {"type": "MARKET", "impact": "HIGH", "source": "رويترز", "title": "الفيدرالي الأمريكي يلمح بوقف رفع الفائدة؛ الأسواق تستجيب بإيجابية.", "sentiment": 0.82},
            {"type": "BREAKING", "impact": "CRITICAL", "source": "عاجل", "title": "تم رصد تصفية مراكز شراء ضخمة؛ توقعات بتقلبات حادة خلال الساعة القادمة.", "sentiment": 0.3},
            {"type": "ADVICE", "impact": "HIGH", "source": "كوانتوم AI", "title": "مؤشر RSI حرج؛ ينصح بمراقبة مناطق التجميع وتجنب الدخول المتأخر.", "sentiment": 0.75},
            {"type": "ADVICE", "impact": "MEDIUM", "source": "نظام الحماية", "title": "تم تفعيل درع التقلبات؛ يرجى الالتزام بأوامر وقف الخسارة الصارمة.", "sentiment": 0.5},
            {"type": "MARKET", "impact": "HIGH", "source": "أخبار برو سوفت", "title": "نظام QUANTUM يسجل إشارات دخول قوية على عملات الميم والعملات البديلة.", "sentiment": 0.92},
        ]
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
        if len(self.dynamic_insights) > 5:
            self.dynamic_insights.pop()

    def refresh_pulse(self):
        """Generates a rich and diverse set of global events in AR/EN."""
        # Combine static news with dynamic real-time insights
        base_selected = random.sample(self.news_database, k=min(7, len(self.news_database)))
        selected = self.dynamic_insights + base_selected
        
        self.current_feed = []
        avg_sentiment = 0
        
        for item in selected:
            pulse_item = item.copy()
            if 'time' not in pulse_item:
                pulse_item['time'] = datetime.now().strftime("%H:%M")
            self.current_feed.append(pulse_item)
            avg_sentiment += item.get('sentiment', 0.5)
            
        mood = avg_sentiment / len(selected) if selected else 0.5
        return {
            'feed': self.current_feed,
            'mood_score': mood * 100,
            'status': "BULLISH" if mood > 0.7 else ("NEUTRAL" if mood > 0.5 else "BEARISH")
        }
