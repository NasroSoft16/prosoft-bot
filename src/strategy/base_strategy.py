import pandas as pd
from src.utils.logger import app_logger
from src.indicators.technical_analysis import TechnicalAnalysis

class BaseStrategy:
    def __init__(self, rsi_min=25, rsi_max=80, volume_multiplier=1.2, atr_multiplier_sl=2.2, atr_multiplier_tp=5.0):
        self.ta = TechnicalAnalysis()
        self.rsi_min = rsi_min
        self.rsi_max = rsi_max
        self.volume_multiplier = volume_multiplier
        self.atr_multiplier_sl = atr_multiplier_sl
        self.atr_multiplier_tp = atr_multiplier_tp

    def calculate_trailing_stop(self, current_price, atr, side='LONG', multiplier=2.5):
        """Calculates a trailing stop loss based on ATR with increased buffer."""
        if side == 'LONG':
            return current_price - (atr * multiplier)
        else:
            return current_price + (atr * multiplier)
            
    def check_entry_signal(self, df):
        """Checks if the technical indicators signal a buy with optimized sensitivity."""
        try:
            if len(df) < 50: # Increased minimum history for better EMA/ATR accuracy
                return {'signal': 'WAIT'}
                
            current_row = df.iloc[-1]
            prev_row = df.iloc[-2]
            
            # --- PROSOFT ELITE ADAPTIVE LOGIC ---
            # Condition 1: Strong Breakout (Surging above high of previous candle)
            is_breakout = current_row['close'] > prev_row['high'] and current_row['close'] > current_row['EMA_50']
            
            # Condition 2: Confidence Zone (Avoid extreme overbought RSI > 85)
            is_momentum = 55 <= current_row['RSI'] <= 82
            
            # Condition 3: Professional Knife Catch (Deep Mean Reversion)
            is_knife_catch = current_row['RSI'] < 20 and current_row['close'] > prev_row['close']
            
            # Condition 4: Volume confirmation (Enhanced sensitivity)
            is_volume_valid = self.ta.is_volume_spike(df, multiplier=self.volume_multiplier)
            
            # Aggregate Signal Logic
            signal_valid = (is_breakout and is_momentum and is_volume_valid) or is_knife_catch
            
            if signal_valid:
                strat_type = "Elite Knife Catch" if is_knife_catch else "Momentum Breakout"
                app_logger.info(f"🎯 PROSOFT SIGNAL: {strat_type} Confirmed.")
                
                entry_price = current_row['close']
                atr = current_row['ATR']
                
                # ADAPTIVE RISK: Wider stops for Knife Catch, standard for Breakout
                sl_mult = self.atr_multiplier_sl * 1.2 if is_knife_catch else self.atr_multiplier_sl
                tp_mult = self.atr_multiplier_tp
                
                stop_loss = entry_price - (atr * sl_mult)
                take_profit = entry_price + (atr * tp_mult)
                
                return {
                    'signal': 'BUY',
                    'entry_price': entry_price,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'indicators': {
                        'RSI': current_row['RSI'],
                        'ATR': current_row['ATR'],
                        'Volume': current_row['volume'],
                        'Strategy': strat_type
                    }
                }
            
            return {'signal': 'WAIT'}
        except Exception as e:
            app_logger.error(f"Error checking entry signal: {e}")
            return {'signal': 'ERROR', 'error': str(e)}
