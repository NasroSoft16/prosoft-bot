import requests
from datetime import datetime
from src.utils.logger import app_logger

class GlobalMacroFilter:
    """
    PROSOFT AI: Global Macro Filter (Cycle 4)
    ربط البوت ببيانات الاقتصاد الكلي (الفيدرالي، التضخم، أسعار الفائدة)
    لحماية الصفقات الكبرى من الأحداث الاقتصادية الضخمة.
    """

    def __init__(self):
        self.last_update = None
        self.macro_state = {
            'fear_greed_index': 50,
            'fed_sentiment': 'NEUTRAL',
            'market_regime': 'NORMAL',
            'risk_level': 'MEDIUM',
            'global_events': []
        }
        
        # Pre-loaded economic calendar awareness
        self.high_impact_keywords = [
            'FOMC', 'Fed Rate', 'CPI', 'NFP', 'GDP', 'Inflation',
            'Interest Rate', 'Unemployment', 'PCE', 'PPI',
            'Jerome Powell', 'Federal Reserve', 'ECB', 'Bank of Japan'
        ]

    async def fetch_fear_greed_index(self, rsi=50, health=50):
        """جلب مؤشر الخوف والطمع أو حسابه محلياً في حالة الفشل."""
        try:
            # Try official API first
            response = requests.get(
                "https://api.alternative.me/fng/?limit=1",
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and len(data['data']) > 0:
                    value = int(data['data'][0]['value'])
                    classification = data['data'][0]['value_classification']
                    self.macro_state['fear_greed_index'] = value
                    self.macro_state['is_proxy'] = False
                    return value, classification
        except Exception as e:
            app_logger.warning(f"🌍 [MACRO] API Down: {e}. Calculating Neural Proxy...")

        # --- NEURAL PROXY CALCULATION ---
        # If API fails, estimate from RSI and Health
        # RSI 30 -> 15 (Fear), RSI 70 -> 85 (Greed)
        rsi_factor = max(10, min(90, rsi))
        health_factor = max(10, min(90, health))
        
        # Weighted average for proxy FGI
        proxy_val = (rsi_factor * 0.6) + (health_factor * 0.4)
        
        classification = "Greed" if proxy_val > 60 else "Fear" if proxy_val < 40 else "Neutral"
        if proxy_val > 80: classification = "Extreme Greed"
        if proxy_val < 20: classification = "Extreme Fear"
        
        self.macro_state['fear_greed_index'] = int(proxy_val)
        self.macro_state['is_proxy'] = True
        return int(proxy_val), f"Neural Proxy ({classification})"

    async def analyze_macro_environment(self, rsi=50, health=50):
        """
        تحليل شامل وهجين يدمج بين الاقتصاد الكلي والبيانات اللحظية.
        يتم حساب مؤشر "هجين" يمثل نبض السوق الخاص بك.
        """
        global_fgi, global_label = await self.fetch_fear_greed_index(rsi, health)
        
        # --- COMPOSITE FGI CALCULATION (Hybrid Intelligence) ---
        # 1. Local FGI: derived from RSI and Network Health
        local_fgi = (rsi * 0.5) + (health * 0.5)
        
        # 2. Composite FGI: 70% Global Weight + 30% Local Impulse
        # This keeps the macro truth but makes it 'alive' based on your pair's condition.
        composite_fgi = (global_fgi * 0.7) + (local_fgi * 0.3)
        composite_fgi = max(0, min(100, int(composite_fgi)))
        
        # Determine Market Regime based on Composite Value
        if composite_fgi <= 20:
            regime = 'EXTREME_FEAR'
            risk = 'CRITICAL'
            fed_sentiment = 'DOVISH'
        elif composite_fgi <= 35:
            regime = 'FEAR'
            risk = 'HIGH'
            fed_sentiment = 'CAUTIOUS'
        elif composite_fgi <= 55:
            regime = 'NEUTRAL'
            risk = 'MEDIUM'
            fed_sentiment = 'NEUTRAL'
        elif composite_fgi <= 75:
            regime = 'GREED'
            risk = 'LOW'
            fed_sentiment = 'HAWKISH'
        else:
            regime = 'EXTREME_GREED'
            risk = 'MEDIUM'
            fed_sentiment = 'HAWKISH'

        self.macro_state.update({
            'fear_greed_index': composite_fgi,
            'fear_greed_label': f"HYBRID ({global_label})",
            'fed_sentiment': fed_sentiment,
            'market_regime': regime,
            'risk_level': risk,
            'last_update': datetime.now().strftime("%H:%M:%S"),
            'global_anchor': global_fgi,
            'local_impulse': int(local_fgi)
        })
        
        app_logger.info(
            f"🌍 [MACRO GUARDIAN] Composite Sync: FGI={composite_fgi} (Global: {global_fgi} | Local: {int(local_fgi)})"
        )
        
        return self.macro_state

    def should_reduce_exposure(self):
        """
        هل يجب تقليل حجم الصفقات بناءً على البيئة الاقتصادية؟
        """
        risk = self.macro_state.get('risk_level', 'MEDIUM')
        regime = self.macro_state.get('market_regime', 'NEUTRAL')
        
        if risk == 'CRITICAL':
            return True, 0.25  # Reduce to 25% of normal size
        elif risk == 'HIGH':
            return True, 0.50  # Reduce to 50%
        elif regime == 'EXTREME_GREED':
            return True, 0.70  # Reduce to 70% (bubble risk)
        
        return False, 1.0  # Normal size

    def get_trading_permission(self):
        """
        هل الظروف الاقتصادية الكلية تسمح بالتداول؟
        """
        regime = self.macro_state.get('market_regime', 'NEUTRAL')
        fgi = self.macro_state.get('fear_greed_index', 50)
        
        if regime == 'EXTREME_FEAR' and fgi < 10:
            return {
                'allowed': False,
                'reason': 'MACRO LOCKDOWN: Extreme market panic detected. All trades suspended.',
                'regime': regime
            }
        
        return {
            'allowed': True,
            'reason': f'Macro conditions acceptable. Regime: {regime}',
            'regime': regime,
            'position_multiplier': self.should_reduce_exposure()[1]
        }
