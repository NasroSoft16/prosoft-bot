import pandas as pd
from src.utils.logger import app_logger
from src.indicators.technical_analysis import TechnicalAnalysis

class QuantumAlphaStrategy:
    """
    PROSOFT QUANTUM ALPHA (v2.0)
    High-Intelligence momentum strategy using VWAP, CMF, and StochRSI.
    Designed to replace basic MTF with sophisticated institutional-level entries.
    """
    
    def __init__(self, rsi_min=30, rsi_max=75):
        self.ta = TechnicalAnalysis()
        self.rsi_min = rsi_min
        self.rsi_max = rsi_max
        self.name = "Quantum Alpha"

    def check_entry_signal(self, df, symbol: str = '', macro_context: dict = None):
        """
        Calculates institutional-grade entry signals — NEW v33.0 "Macro Interceptor".
        Returns BUY/WAIT with full risk parameters.
        """
        try:
            # ── [MACRO INTERCEPTOR: ALPHA SHIELD] ──
            if macro_context:
                gold_safety = macro_context.get('gold_safety', 'HIGH')
                reason = macro_context.get('reason', '')

                # Hard Veto for Gold in this Alpha strategy as well
                if 'PAXG' in symbol and gold_safety == 'LOW':
                    app_logger.warning(f"⛔ [QUANTUM VETO] PAXG rejected by Macro Interceptor: {reason}")
                    return {'signal': 'WAIT', 'reason': f'Macro Shield Veto: {reason}'}

            if df is None or len(df) < 50:
                return {'signal': 'WAIT', 'reason': 'Warming up engine...'}
            
            curr = df.iloc[-1]
            prev = df.iloc[-2]
            
            # --- EXTRACT INDICATORS ---
            close = float(curr['close'])
            vwap = float(curr.get('VWAP', close))
            cmf = float(curr.get('CMF', 0))
            stoch_rsi = float(curr.get('STOCH_RSI', 0.5))
            rsi = float(curr.get('RSI', 50))
            ema_20 = float(curr.get('EMA_20', 0))
            ema_50 = float(curr.get('EMA_50', 0))
            atr = float(curr.get('ATR', close * 0.01))
            
            # --- INSTITUTIONAL ALIGNMENT ---
            is_bullish_trend = close > vwap and close > ema_20 > ema_50
            is_money_flowing = cmf > 0.05  # Positive money flow
            is_stoch_oversold = stoch_rsi < 0.2
            is_stoch_recovering = stoch_rsi > prev.get('STOCH_RSI', 0) and stoch_rsi > 0.1
            
            # --- THE "QUANTUM" SETUP ---
            # 1. Trend Ride (Institutional bias + momentum)
            is_quantum_buy = (
                is_bullish_trend 
                and is_money_flowing 
                and (is_stoch_recovering or 0.3 < stoch_rsi < 0.7)
                and rsi < 70
            )
            
            # 2. Reversal (Extreme oversold + money flow pivot)
            is_reversal_buy = (
                is_stoch_oversold 
                and rsi < 35 
                and cmf > -0.05 
                and close > prev.get('close', 0)
            )
            
            # 3. Explosive Breakout (Momentum Pumps)
            is_momentum_buy = (
                close > ema_20
                and cmf > 0.10      # Strong liquidity inflow confirming the pump
                and 65 <= rsi <= 85 # Momentum surge zone (previously rejected!)
                and close > prev.get('close', 0) * 1.002 # Meaningful upward tick
            )

            signal_type = None
            confidence = 0.0
            
            if is_momentum_buy:
                signal_type = "Quantum Rocket (Breakout)"
                confidence = 0.85
            elif is_quantum_buy:
                signal_type = "Quantum Pulse (Trend)"
                confidence = 0.88 if cmf > 0.15 else 0.82
            elif is_reversal_buy:
                signal_type = "Quantum Pivot (Reversal)"
                confidence = 0.78
            
            if not signal_type:
                return {'signal': 'WAIT', 'reason': 'Market not in High-Alpha zone'}

            app_logger.info(f"🌌 [QUANTUM ALPHA] Entry Found: {signal_type} | Conf: {confidence:.0%}")

            # --- DYNAMIC EXPERT RISK (v24.0: Quantum Adaptive) ---
            # Adaptive SLR based on signal confidence + market volatility (ATR)
            sl_mult = 1.9 if "Trend" in signal_type else 1.4
            
            # Use Signal-Specific Capping: Trend is safer (1.5%), Reversal is tighter (1.1%)
            max_p_cap = 0.015 if "Trend" in signal_type else 0.011
            
            # The Final SL Distance (ATR-Driven vs Percentage-Capped)
            sl_distance = min(atr * sl_mult, close * max_p_cap)
            stop_loss = close - sl_distance
            
            # TP = Risk * 2.5 (Reward/Risk focus)
            risk = close - stop_loss
            take_profit = close + (risk * 2.5)

            return {
                'signal': 'BUY',
                'entry_price': close,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'rr_ratio': round(risk * 2.5 / risk, 2) if risk > 0 else 0,
                'confidence': confidence,
                'strategy': self.name,
                'indicators': {
                    'Source': 'QuantumAlpha',
                    'Strategy': signal_type,  # مطلوب لقاعدة البيانات
                    'CMF': round(cmf, 3),
                    'VWAP_DIST': round((close/vwap-1)*100, 2),
                    'Pattern': signal_type
                }
            }

        except Exception as e:
            app_logger.error(f"QuantumAlpha Strategy Error: {e}")
            return {'signal': 'ERROR', 'reason': str(e)}
