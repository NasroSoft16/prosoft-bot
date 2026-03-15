from datetime import datetime
from src.utils.logger import app_logger

class HedgingProtocol:
    """
    PROSOFT AI: Long/Short Hedging Protocol (Cycle 4)
    تفعيل وضعية التحوط لفتح صفقات حماية عند الانهيارات.
    
    المبدأ: عندما يكتشف البوت انهياراً محتملاً، يفتح صفقة Short (بيع) 
    على العقود الآجلة لتعويض خسائر صفقة الـ Spot.
    """

    def __init__(self):
        self.hedge_active = False
        self.hedge_ratio = 0.5  # نسبة التحوط: 50% من حجم الصفقة
        self.crash_threshold = -5.0  # إذا انخفض السعر 5% = انهيار محتمل
        self.recovery_threshold = 2.0  # إذا ارتفع 2% بعد التحوط = تعافي
        self.hedge_history = []
        
    def evaluate_crash_risk(self, price_change_pct, market_health, sentiment, macro_fgi=50):
        """
        تقييم فائق الدقة لخطر الانهيار (نسخة المؤسسات v4.2).
        يدمج بين صدمة السعر، صحة النظام، والذعر العالمي.
        """
        risk_score = 0
        
        # 1. LATENT RISK BASELINE (Safety Margin)
        # إذا كان المؤشر العالمي في حالة ذعر شديد، هناك خطر مستتر دائماً
        if macro_fgi < 20:
            risk_score = 30  # خط أساس للمخاطر في وضع EXTREME FEAR
        elif macro_fgi < 35:
            risk_score = 15  # خط أساس لوضع FEAR
            
        # 2. Price Drop Shock (Weight: 45%) - الحساسية للصدمات السعرية
        if price_change_pct < -1.0:
            risk_score += min(45, abs(price_change_pct) * 15)
        
        # 3. Neural Health Degradation (Weight: 25%) - تدهور صحة الشبكة العصبية
        if market_health < 45:
            risk_score += (45 - market_health)
        
        # 4. Global Fear Multiplier (Weight: 15%) - تأثير الذعر العالمي الإضافي
        if macro_fgi < 30:
            risk_score += (30 - macro_fgi) * 0.8
            
        risk_score = min(100, int(risk_score))
        should_hedge = risk_score >= 65 and not self.hedge_active
        
        if should_hedge:
            app_logger.critical(
                f"🛡️ [HEDGE PROTOCOL] CRASH RISK DETECTED! "
                f"Score: {risk_score}/100 | "
                f"Activating Hedging Shield..."
            )
        
        return {
            'risk_score': risk_score,
            'should_hedge': should_hedge,
            'price_impact': price_change_pct,
            'health': market_health,
            'sentiment': sentiment
        }

    def activate_hedge(self, symbol, current_price, position_size):
        """
        تفعيل التحوط: حساب حجم صفقة الحماية.
        """
        hedge_size = position_size * self.hedge_ratio
        
        self.hedge_active = True
        hedge_record = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'symbol': symbol,
            'entry_price': current_price,
            'hedge_size': hedge_size,
            'status': 'ACTIVE',
            'type': 'SHORT_HEDGE'
        }
        self.hedge_history.append(hedge_record)
        
        app_logger.critical(
            f"🛡️ [HEDGE ACTIVATED] {symbol} SHORT @ ${current_price} | "
            f"Hedge Size: {hedge_size:.4f} ({self.hedge_ratio*100}% of position)"
        )
        
        return hedge_record

    def check_recovery(self, price_change_pct):
        """
        فحص ما إذا كان السوق تعافى لإغلاق صفقة التحوط.
        """
        if not self.hedge_active:
            return False
            
        if price_change_pct > self.recovery_threshold:
            self.hedge_active = False
            if self.hedge_history:
                self.hedge_history[-1]['status'] = 'CLOSED_RECOVERY'
            app_logger.info(
                f"✅ [HEDGE CLOSED] Market recovered +{price_change_pct:.1f}%. "
                f"Shield deactivated."
            )
            return True
        return False

    def get_status(self):
        """حالة بروتوكول التحوط الحالية."""
        return {
            'active': self.hedge_active,
            'ratio': self.hedge_ratio,
            'total_hedges': len(self.hedge_history),
            'last_hedge': self.hedge_history[-1] if self.hedge_history else None
        }
