import pandas as pd
from src.utils.logger import app_logger
from src.indicators.technical_analysis import TechnicalAnalysis


class BaseStrategy:
    """
    PROSOFT Elite Entry Engine.
    ATR-based SL/TP, real trailing stop, adaptive thresholds.
    """

    def __init__(
        self,
        rsi_min=25, rsi_max=80,
        volume_multiplier=1.2,
        atr_multiplier_sl=2.0,
        atr_multiplier_tp=5.5,
    ):
        self.ta                 = TechnicalAnalysis()
        self.rsi_min            = rsi_min
        self.rsi_max            = rsi_max
        self.volume_multiplier  = volume_multiplier
        self.atr_multiplier_sl  = atr_multiplier_sl if atr_multiplier_sl != 2.0 else 1.5
        self.atr_multiplier_tp  = atr_multiplier_tp

    # ── Trailing stop ─────────────────────────────────────────────────────

    def calculate_trailing_stop(self, current_price, atr, side='LONG', multiplier=2.0):
        """
        ATR-based trailing stop.
        For LONG: only ever moves UP — caller must enforce that.
        Returns the new SL price.
        """
        if side == 'LONG':
            return current_price - (atr * multiplier)
        else:
            return current_price + (atr * multiplier)

    def update_trailing_stop(self, active_trade: dict, current_price: float, atr: float):
        """
        Safely advance the trailing stop for an open LONG trade.
        Includes Smart Breakeven Lock for scalping protection.
        """
        if not active_trade:
            return active_trade

        entry_price = active_trade.get('entry_price', active_trade.get('entry', 0))
        old_sl = active_trade.get('trailing_sl', active_trade.get('sl', 0))

        # ── Smart Breakeven (Risk-Free Lock) ──
        # If profit hits +0.4%, immediately lock Stop Loss at Entry + 0.15% (covers Binance fees)
        if entry_price > 0:
            profit_pct = (current_price - entry_price) / entry_price
            if profit_pct >= 0.004: 
                breakeven_sl = entry_price * 1.0015 
                if breakeven_sl > old_sl:
                    active_trade['trailing_sl'] = breakeven_sl
                    active_trade['sl'] = breakeven_sl
                    app_logger.info(f"🛡️ [RISK-FREE] Breakeven Lock! SL moved to {breakeven_sl:.6f} (Securing Entry + Fees).")
                    return active_trade

        new_sl = self.calculate_trailing_stop(current_price, atr, side='LONG')

        if new_sl > old_sl:
            active_trade['trailing_sl'] = new_sl
            active_trade['sl'] = new_sl
            app_logger.info(
                f"📈 [TRAIL] SL raised: {old_sl:.6f} → {new_sl:.6f} "
                f"(price={current_price:.6f})"
            )
        return active_trade

    # ── Entry signal ─────────────────────────────────────────────────────

    def check_entry_signal(self, df, symbol: str = '', macro_context: dict = None, performance_context: dict = None):
        """
        PROSOFT Elite Adaptive Entry — NEW v33.1 "Pulse Exit Control".
        Returns BUY signal with entry, SL, TP, and reasoning OR WAIT.
        """
        try:
            # ── [MASTER ADAPTIVE EXIT CONTROL] ──
            # Default multipliers
            tp_mult = getattr(self, 'atr_multiplier_tp', 5.5)
            sl_mult = getattr(self, 'atr_multiplier_sl', 1.5)

            if performance_context:
                win_rate = performance_context.get('win_rate', 0.50)
                streak = performance_context.get('consecutive_wins', 0)
                losses = performance_context.get('consecutive_losses', 0)

                # Reward Phase: Stretch targets during winning streaks
                if win_rate >= 0.70 or streak >= 3:
                    tp_mult += 0.7  # Target 6.2x ATR
                    sl_mult += 0.2  # Allow standard breathing room
                
                # Shield Phase: Tighten targets during drawdowns
                if win_rate < 0.45 or losses >= 2:
                    tp_mult -= 0.5  # Settle for 5.0x ATR to exit safely
                    sl_mult -= 0.3  # Tighten SL to 1.7x ATR to cut bleed
                    
            # ── [MACRO INTERCEPTOR: CORPORATE-GRADE SHIELD] ──
            if macro_context:
                bias = macro_context.get('macro_bias', 'NEUTRAL')
                gold_safety = macro_context.get('gold_safety', 'HIGH')
                dxy_pressure = macro_context.get('dxy_pressure', 'LOW')
                reason = macro_context.get('reason', 'ظروف الماكرو مستقرة')

                # Hard Veto for Gold if DXY is mooning or AI detects a trap
                if 'PAXG' in symbol and gold_safety == 'LOW':
                    app_logger.warning(f"⛔ [MACRO VETO] Gold (PAXG) rejected: {reason}")
                    return {'signal': 'WAIT', 'reason': f'Macro Shield Veto: {reason}'}

                # Global Risk-Off: If DXY pressure is too high, require more RSI stability
                if dxy_pressure == 'HIGH' and bias == 'BEARISH':
                    self.rsi_min = 35 # Tighten oversold entry window
                    self.rsi_max = 75 # Tighten overbought entry window
            
            if len(df) < 30:
                return {'signal': 'WAIT', 'reason': 'Insufficient history'}

            curr = df.iloc[-1]
            prev = df.iloc[-2]

            rsi       = float(curr.get('RSI',       50))
            ema_20    = float(curr.get('EMA_20',      0))
            ema_50    = float(curr.get('EMA_50',      0))
            ema_200   = float(curr.get('EMA_200',     0))
            macd_hist = float(curr.get('MACD_HIST',   0))
            atr       = float(curr.get('ATR',         0))
            close     = float(curr['close'])
            bb_width  = float(curr.get('BB_WIDTH',  0.02))

            # ── Condition 1: Momentum Breakout ──
            is_breakout = (
                close > prev['high']
                and close > ema_20
                and ema_20 > ema_50        # trend confirmation
                and self.rsi_min <= rsi <= self.rsi_max
                and macd_hist > 0
            )

            # ── Condition 2: Oversold Knife-Catch ──
            rsi_bounce  = float(prev.get('RSI', 50)) < 32 and rsi > float(prev.get('RSI', 50))
            is_knife    = rsi < 30 and close > prev['close'] and close > ema_50

            # ── Condition 3: BB Squeeze Breakout ──
            is_squeeze  = bb_width < 0.018 and close > ema_20 and rsi > 50

            # ── Condition 4: Trend-Ride (EMA golden cross area) ──
            is_trend    = (
                ema_50 > ema_200
                and close > ema_50
                and 48 <= rsi <= 68
                and macd_hist > 0
            )

            # ── Condition 5: Velocity Guard & Climax Filter (v29.0) ──
            is_climax = bool(curr.get('IS_CLIMAX', False))
            velocity  = float(curr.get('VELOCITY', 0))
            
            # ── Volume confirmation ──
            vol_ok = self.ta.is_volume_spike(df, multiplier=self.volume_multiplier)

            # ── Final decision ──
            signal_type = None
            
            # EXPERT VETO: If it's a parabolic climax, we do NOT enter.
            if is_climax or velocity > 2.5: # Reject if spike > 2.5% in ONE candle
                return {
                    'signal': 'WAIT', 
                    'reason': f'Climax Spike Detected ({velocity:.2f}%). Entry unsafe.'
                }

            if is_breakout and vol_ok:
                signal_type = "Momentum Breakout"
            elif is_knife:
                signal_type = "Knife Catch"
            elif is_squeeze and vol_ok:
                signal_type = "BB Squeeze Break"
            elif is_trend:
                signal_type = "Trend Ride"

            if not signal_type:
                reasons = []
                if rsi >= self.rsi_max: reasons.append(f"RSI overbought ({rsi:.1f})")
                if close < ema_20:      reasons.append("Price below EMA20")
                if macd_hist < 0:       reasons.append("MACD negative")
                return {'signal': 'WAIT', 'reason': ', '.join(reasons) or 'No pattern'}

            app_logger.info(f"🎯 PROSOFT SIGNAL: {signal_type} | RSI={rsi:.1f} | Adaptive TP/SL: {tp_mult:.1f}x / {sl_mult:.1f}x")

            # ── Dynamic SL multiplier assignment ──
            final_sl_mult = sl_mult * 1.3 if signal_type == "Knife Catch" else sl_mult
            final_tp_mult = tp_mult

            if atr <= 0:
                return {'signal': 'WAIT', 'reason': 'ATR=0 (no volatility data)'}

            # --- EXPERT ADAPTIVE STOP LOSS (v24.0) ---
            # Instead of a static percentage, we calculate based on Volatility (ATR)
            dynamic_sl_dist = atr * 1.5 
            
            # Smart Cap based on Performance context
            smart_cap_pct = 0.008 # Baseline 0.8%
            if performance_context:
                win_rate = performance_context.get('win_rate', 0.5)
                if win_rate < 0.45:
                    smart_cap_pct = 0.005 # Tighten cap to 0.5% when losing
                elif win_rate > 0.65:
                    smart_cap_pct = 0.012 # Relax cap to 1.2% when winning
                    
            price_percentage_limit = close * smart_cap_pct
            
            # The Stop Loss is the closer of the two (Safety First)
            sl_distance = min(atr * final_sl_mult, price_percentage_limit)
            stop_loss = close - sl_distance
            take_profit = close + (atr * final_tp_mult)

            # Sanity: TP/SL ratio must be > 1.2 (Adjusted for adaptive logic)
            risk   = close - stop_loss
            reward = take_profit - close
            if risk <= 0 or (reward / risk) < 1.2:
                return {'signal': 'WAIT', 'reason': f'Poor R/R ratio ({reward/risk:.2f})'}

            return {
                'signal':      'BUY',
                'entry_price': close,
                'stop_loss':   stop_loss,
                'take_profit': take_profit,
                'rr_ratio':    round(reward / risk, 2),
                'indicators':  {
                    'RSI':      rsi,
                    'ATR':      atr,
                    'MACD_H':   macd_hist,
                    'Strategy': signal_type,
                }
            }

        except Exception as e:
            app_logger.error(f"Entry signal error: {e}")
            return {'signal': 'ERROR', 'error': str(e)}
