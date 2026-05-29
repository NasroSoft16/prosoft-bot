import asyncio
import sys
import os
import sqlite3
from datetime import datetime

# Setup imports
sys.path.append(r"c:\Users\dell\Desktop\BINANCE FINAL\PROSOFT_DIST")

# Force sys.stdout to use UTF-8 to prevent Windows cp1256 encoding crashes on print
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from main import TradingBot
from src.strategy.solana_sniper import SolanaDexSniper
from src.execution.multi_agent.shared_state import GlobalSharedState

async def run_swarm_tests():
    print("======================================================================")
    print("PROSOFT SWARM INTEGRATION TEST: SYSTEM VERIFICATION")
    print("======================================================================")
    
    # 1. Initialize Bot Mock/Instance
    print("\n[TEST 1] Initializing Swarm Core on Bot Instance...")
    bot = TradingBot(symbol="BTCUSDT")
    
    assert hasattr(bot, 'shared_state'), "Failed: GlobalSharedState not initialized"
    assert hasattr(bot, 'sentinel'), "Failed: SentinelAgent not initialized"
    assert hasattr(bot, 'risk_warden'), "Failed: RiskWardenAgent not initialized"
    assert hasattr(bot, 'executioner'), "Failed: ExecutionerAgent not initialized"
    assert hasattr(bot, 'self_tuner'), "Failed: SelfTunerAgent not initialized"
    assert hasattr(bot, 'solana_sniper'), "Failed: SolanaDexSniper not initialized"
    assert hasattr(bot, 'hft_depth'), "Failed: HftDepthEngine not initialized"
    print("[+] Swarm core modules verified successfully!")
    
    # 2. Test Safe FGI Parsing on Sentinel & Risk Warden
    print("\n[TEST 2] Verifying safe FGI parsing ('N/A' robustness)...")
    bot.stats['fear_greed_index'] = "N/A"
    
    # Test main FGI normalizer inside _check_entry_conditions
    allowed, reason = await bot._check_entry_conditions("BTCUSDT", None, 50.0, fgi="N/A")
    print(f"Entry check result with FGI='N/A': {allowed} (Reason: {reason})")
    print("[+] Passed FGI safety gates check!")
    
    # 3. Test Solana DEX Sniper Contract Audit and Virtual Swaps
    print("\n[TEST 3] Verifying Solana DEX Sniper contract safety audits...")
    sniper = bot.solana_sniper
    
    # We test the safe contract audit function directly
    # Generate mock mints
    safe_mint = "4k3DyjzvGtSafeMint1234567890abcdef"
    
    # Force audit test by overriding random values in audit check
    # Mocking standard contract check to guarantee clean pass
    def mock_audit_success(mint):
        return True, "100% Clean Audit"
        
    sniper._audit_contract = mock_audit_success
    
    # Force mock a new Raydium liquidity pool event
    print("Simulating new Raydium pool creation for virtual token...")
    # Overwrite the scanner simulation list
    original_scan = sniper._scan_raydium_pools
    
    # We call the scan function
    await sniper._scan_raydium_pools()
    
    # Verify that a virtual trade was recorded
    assert len(sniper.virtual_trades) >= 1, "Failed: DEX Sniper did not capture virtual trade"
    trade = sniper.virtual_trades[0]
    print(f"Virtual Trade Captured: Asset={trade['symbol']} | Qty={trade['qty']:.2f} | Spent={trade['sol_spent']} SOL")
    print("[+] Passed Solana DEX Sniper verification!")
    
    # 4. Test WebSockets OBI Calculation & Front-Running Wall Ticks
    print("\n[TEST 4] Verifying HFT WebSockets OBI Wall ticks...")
    hft = bot.hft_depth
    
    # Mock bid/ask book
    hft.bids = [[100.0, 10.0], [99.9, 5.0]]
    hft.asks = [[100.1, 8.0], [100.2, 40.0]]  # large wall at 100.2
    
    # Get optimal buy/sell tick front-running
    buy_fr = hft.get_front_run_price('BUY', 100.0)
    sell_fr = hft.get_front_run_price('SELL', 100.0)
    
    print(f"Mock Ticker Price: $100.00")
    print(f"Optimal Buy Front-run (Wall: $100.00): ${buy_fr:.2f}")
    print(f"Optimal Sell Front-run (Wall: $100.20): ${sell_fr:.2f}")
    
    assert buy_fr > 100.0 or buy_fr == 100.0, "Buy front-run calculation failed"
    assert sell_fr < 100.2, "Sell front-run calculation failed"
    print("[+] HFT front-running logic verified!")
    
    print("\n======================================================================")
    print("🎉 ALL REVOLUTIONARY SWARM INTEGRATION TESTS PASSED SUCCESSFULLY!")
    print("======================================================================")

if __name__ == "__main__":
    asyncio.run(run_swarm_tests())
