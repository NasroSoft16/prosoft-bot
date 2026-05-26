import pandas as pd
import numpy as np
import sys
import os

from src.strategy.meme_sniper import MemeRocketSniper

def generate_mock_df(size=60, vol_ratio=1.8, price_change=1.2, is_second_leg=False):
    """Generates a perfectly flat deterministic mock dataframe for testing signals."""
    opens = [100.0] * size
    closes = [100.0] * size
    highs = [100.0] * size
    lows = [100.0] * size
    volumes = [10.0] * size
    
    df = pd.DataFrame({
        'open': opens,
        'high': highs,
        'low': lows,
        'close': closes,
        'volume': volumes,
        'RSI': [50.0] * size
    })
    
    if is_second_leg:
        # Prev candle was a big green candle (the first rocket)
        # Prev candle: open=100.0, close=101.5 (+1.5% move), high=101.5, low=100.0, volume=18.0 (1.8x average)
        df.loc[df.index[-2], 'open'] = 100.0
        df.loc[df.index[-2], 'close'] = 101.5
        df.loc[df.index[-2], 'high'] = 101.5
        df.loc[df.index[-2], 'low'] = 100.0
        df.loc[df.index[-2], 'volume'] = 18.0
        
        # Current candle: open=101.5, close=102.1 (+0.59% move), high=102.1, low=101.5, volume = 10.0 * vol_ratio
        df.loc[df.index[-1], 'open'] = 101.5
        df.loc[df.index[-1], 'close'] = 102.1
        df.loc[df.index[-1], 'high'] = 102.1
        df.loc[df.index[-1], 'low'] = 101.5
        df.loc[df.index[-1], 'volume'] = 10.0 * vol_ratio
        df.loc[df.index[-1], 'RSI'] = 65.0
        
    else:
        # Current candle: open=100.0, close=100.0+price_change, high=100.0+price_change, low=100.0, volume=10.0 * vol_ratio
        df.loc[df.index[-1], 'open'] = 100.0
        df.loc[df.index[-1], 'close'] = 100.0 + price_change
        df.loc[df.index[-1], 'high'] = 100.0 + price_change
        df.loc[df.index[-1], 'low'] = 100.0
        df.loc[df.index[-1], 'volume'] = 10.0 * vol_ratio
        df.loc[df.index[-1], 'RSI'] = 60.0
        
    return df

def run_tests():
    print("======================================================================")
    print("PROSOFT SHIELD TEST: FEAR MARKET MOMENTUM SHIELD")
    print("======================================================================")
    
    sniper = MemeRocketSniper(api_wrapper=None)
    
    # ── TEST CASE 1: EARLY IGNITION (FGI=50 - Normal Regime) ──
    print("\n[TEST 1] Early Ignition under NORMAL market (FGI=50)...")
    # Vol ratio = 1.8x, price change = 1.2% (passes standard rules)
    df_normal = generate_mock_df(vol_ratio=1.8, price_change=1.2)
    sig_normal = sniper.detect_rocket(df_normal, "TESTUSDT", fgi=50)
    print(f"Result (FGI=50): {sig_normal}")
    assert sig_normal is not None and sig_normal['signal'] == 'EARLY_IGNITION', "Failed TEST 1: Should trigger EARLY_IGNITION"
    print("[+] Passed!")
    
    # ── TEST CASE 2: EARLY IGNITION BLOCK (FGI=30 - Fear Regime) ──
    print("\n[TEST 2] Early Ignition under FEAR market (FGI=30)...")
    # Same parameters (1.8x vol, 1.2% pump) should be BLOCKED because:
    # 1. 1.8x vol < 2.2x required in Fear
    # 2. 1.2% pump > 1.0% max allowed in Fear
    sig_fear = sniper.detect_rocket(df_normal, "TESTUSDT", fgi=30)
    print(f"Result (FGI=30): {sig_fear}")
    assert sig_fear is None, "Failed TEST 2: Should block weak breakout in fear market"
    print("[+] Passed!")

    # ── TEST CASE 3: EARLY IGNITION TIGHTENED (FGI=30 - Fear Regime - Strong signal) ──
    print("\n[TEST 3] Tightened Early Ignition under FEAR market (FGI=30)...")
    # Strong parameters (2.5x vol, 0.8% pump) should PASS because they satisfy the tightened criteria:
    # 1. 2.5x vol >= 2.2x required
    # 2. 0.8% pump <= 1.0% max allowed
    df_strong = generate_mock_df(vol_ratio=2.5, price_change=0.8)
    sig_strong = sniper.detect_rocket(df_strong, "TESTUSDT", fgi=30)
    print(f"Result (FGI=30, Strong): {sig_strong}")
    assert sig_strong is not None and sig_strong['signal'] == 'EARLY_IGNITION', "Failed TEST 3: Strong signal should pass in fear"
    print("[+] Passed!")

    # ── TEST CASE 4: SECOND LEG (FGI=50 - Normal Regime) ──
    print("\n[TEST 4] Second Leg under NORMAL market (FGI=50)...")
    df_2nd_normal = generate_mock_df(vol_ratio=2.0, is_second_leg=True)
    sig_2nd_normal = sniper.detect_rocket(df_2nd_normal, "TESTUSDT", fgi=50)
    print(f"Result (FGI=50, 2nd Leg): {sig_2nd_normal}")
    assert sig_2nd_normal is not None and sig_2nd_normal['signal'] == 'SECOND_LEG', "Failed TEST 4: Should trigger SECOND_LEG"
    print("[+] Passed!")

    # ── TEST CASE 5: SECOND LEG BLOCKED (FGI=30 - Fear Regime) ──
    print("\n[TEST 5] Second Leg under FEAR market (FGI=30)...")
    # Should be completely disabled to prevent buying bull traps
    sig_2nd_fear = sniper.detect_rocket(df_2nd_normal, "TESTUSDT", fgi=30)
    print(f"Result (FGI=30, 2nd Leg): {sig_2nd_fear}")
    assert sig_2nd_fear is None, "Failed TEST 5: Should disable SECOND_LEG entirely in fear"
    print("[+] Passed!")
    
    print("\n======================================================================")
    print("ALL TESTS PASSED SUCCESSFULLY! FEAR SHIELD IS 100% OPERATIONAL!")
    print("======================================================================")

if __name__ == "__main__":
    run_tests()
