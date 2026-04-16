import pandas as pd
from src.utils.logger import app_logger

class MemeRocketSniper:
    """
    PROSOFT AI: Hyper-Volatility & Meme Rocket Early-Ignition Sniper
    
    v2.0 PHILOSOPHY CHANGE:
    ========================
    OLD (BROKEN): Detect AFTER a +2% candle → buy at the TOP → guaranteed loss
    NEW (FIXED):  Detect the IGNITION PHASE (volume spike + small move) → buy EARLY
                  The rocket is still loading, not yet launched. We ride it UP.
    
    Entry Conditions (ALL must be true):
    1. Volume is building: current candle volume > 2.5x average (early surge)
    2. Price move is SMALL: 0.3% to 1.2% — still in ignition, not at the top
    3. Momentum confirmation: previous candle was ALSO green (trend building)
    4. RSI not overbought: RSI < 78 (if available) — don't buy into exhaustion
    5. Candle body strong: close > 60% of the candle range (buyers in control)
    """
    
    def __init__(self, api_wrapper):
        self.api = api_wrapper
        
    def detect_rocket(self, df, symbol):
        """
        Detects EARLY signs of a rocket BEFORE it fully launches.
        Catches the ignition phase, not the peak.
        """
        if df is None or len(df) < 25:
            return None
        
        # ── Data Extraction ──
        curr     = df.iloc[-1]
        prev     = df.iloc[-2]
        prev2    = df.iloc[-3]
        
        curr_open   = float(curr['open'])
        curr_close  = float(curr['close'])
        curr_high   = float(curr['high'])
        curr_low    = float(curr['low'])
        curr_volume = float(curr['volume'])
        
        prev_open   = float(prev['open'])
        prev_close  = float(prev['close'])
        prev_volume = float(prev['volume'])
        
        # Average volume over last 20 candles (excluding current)
        avg_volume = float(df.iloc[-21:-1]['volume'].mean())
        if avg_volume <= 0:
            return None
        
        # ── Core Metrics ──
        # How much price moved in current candle (%)
        curr_price_change = ((curr_close - curr_open) / curr_open) * 100 if curr_open > 0 else 0
        
        # Volume surge ratio
        vol_ratio = curr_volume / avg_volume
        
        # RSI guard (if indicator available)
        rsi = float(curr.get('RSI', 50))
        
        # Candle body strength: what % of the range is the body?
        candle_range = curr_high - curr_low
        candle_body  = abs(curr_close - curr_open)
        body_strength = (candle_body / candle_range) if candle_range > 0 else 0
        
        # Previous candle direction
        prev_is_green = prev_close > prev_open
        prev2_is_green = float(prev2['close']) > float(prev2['open'])
        
        # Previous candle volume also building?
        prev_vol_building = prev_volume > avg_volume * 1.5

        # ── 🚀 EARLY IGNITION DETECTION (The New Logic) ──
        # Condition 1: Volume is surging but price hasn't moved much yet
        volume_surging  = vol_ratio >= 2.5          # 250%+ volume - rocket fuel loading
        early_move      = 0.30 <= curr_price_change <= 1.20  # Small move = still early
        rsi_safe        = rsi < 78                  # Not already overbought
        body_ok         = body_strength >= 0.50     # Strong bullish body
        momentum_ok     = prev_is_green             # Previous candle was also green
        
        if volume_surging and early_move and rsi_safe and body_ok and momentum_ok:
            app_logger.critical(
                f"🚀 [EARLY IGNITION] {symbol}: "
                f"Vol ×{vol_ratio:.1f} | Move: +{curr_price_change:.2f}% | RSI: {rsi:.0f} | "
                f"Rocket is LOADING - Entering NOW before launch!"
            )
            # Tight SL since we're catching early momentum (0.35% is tight for fast memes)
            # TP is set to 1.5x the current move since it has more room to run
            projected_tp_pct = max(1.5, curr_price_change * 2.5)
            return {
                'signal': 'EARLY_IGNITION',
                'entry_price': curr_close,
                'target_profit': min(projected_tp_pct, 4.0),  # Cap at 4% TP
                'emergency_sl': 0.35,   # 0.35% SL - tight because we're entering early
            }

        # ── 🔥 SECONDARY: MOMENTUM CONTINUATION (2nd leg up) ──
        # If the first leg already happened but a SECOND leg is forming:
        # - Prev candle was a big green candle (the first rocket)
        # - Current candle is starting a second push with volume still high
        prev_big_move = ((prev_close - prev_open) / prev_open * 100) >= 1.0 if prev_open > 0 else False
        second_leg    = vol_ratio >= 1.8 and 0.20 <= curr_price_change <= 0.80
        
        if prev_big_move and prev_vol_building and second_leg and rsi_safe and body_ok:
            app_logger.critical(
                f"🔥 [2ND LEG] {symbol}: "
                f"First rocket confirmed. 2nd leg forming! "
                f"Vol ×{vol_ratio:.1f} | Move: +{curr_price_change:.2f}% | RSI: {rsi:.0f}"
            )
            return {
                'signal': 'SECOND_LEG',
                'entry_price': curr_close,
                'target_profit': 2.0,   # More modest TP for 2nd leg
                'emergency_sl': 0.40,   # Slightly wider for 2nd leg volatility
            }

        return None
