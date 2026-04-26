import time
from datetime import datetime
from src.utils.logger import app_logger

class VShapeHunter:
    """
    PROSOFT AI: V-Shape Snatcher (Flash Crash Hunter)
    ==================================================
    Uses "Virtual Limit Orders" to catch extreme market dumps (-12% to -15%)
    WITHOUT locking up actual USDT balance on the exchange.
    
    If the price doesn't crash, the virtual net automatically expires 
    and repositions itself relative to the new price (Smart Cancellation).
    """
    def __init__(self):
        # Dictionary to hold our virtual limit orders
        # format: { 'DOGEUSDT': {'target_price': 0.15, 'anchor_price': 0.18, 'placed_at': 169...} }
        self.virtual_nets = {}
        
        # ── Configuration ──
        self.target_drop_pct = 0.12     # We want a sudden -12% drop to trigger
        self.net_expiry_seconds = 21600 # 6 hours expiry before recalculating anchor
        
        # Dynamic active symbols (updated by main bot)
        self.active_symbols = ['SOLUSDT', 'BTCUSDT', 'ETHUSDT'] # Fallback baseline

    def update_nets(self, current_prices, dynamic_top_symbols=None):
        """
        Maintains the virtual nets. Places new ones and cancels/updates old ones.
        If dynamic_top_symbols is provided, it updates its hunting pool.
        """
        now = time.time()
        
        # Sync the hunting list to where the liquidity is
        if dynamic_top_symbols and len(dynamic_top_symbols) > 0:
            self.active_symbols = dynamic_top_symbols
            
            # Cleanup nets for coins that are no longer in the top volume list
            for sym in list(self.virtual_nets.keys()):
                if sym not in self.active_symbols:
                    del self.virtual_nets[sym]
                    app_logger.info(f"🕸️ [V-SHAPE HUNTER] Removed net for {sym} (Fell out of top liquidity radar).")
        
        for sym in self.active_symbols:
            current_price = current_prices.get(sym)
            if not current_price:
                continue
                
            # If no net exists for this symbol, or it has expired -> Create/Update it
            if sym not in self.virtual_nets or (now - self.virtual_nets[sym]['placed_at'] > self.net_expiry_seconds):
                target_price = current_price * (1 - self.target_drop_pct)
                
                # Log only if it's an update (cancellation of old net)
                if sym in self.virtual_nets:
                    app_logger.debug(f"🕸️ [V-SHAPE HUNTER] Cancelling old net for {sym}. Repositioning to new anchor.")
                
                self.virtual_nets[sym] = {
                    'anchor_price': current_price,
                    'target_price': target_price,
                    'placed_at': now
                }

    def check_triggers(self, current_prices):
        """
        Checks if any coin has crashed into our virtual nets.
        Returns a list of signals for the main bot to execute immediately.
        """
        triggered_signals = []
        now = time.time()
        
        for sym, net in list(self.virtual_nets.items()):
            current_price = current_prices.get(sym)
            if not current_price:
                continue
                
            # Has it crashed to our target?
            if current_price <= net['target_price']:
                drop_pct = (current_price - net['anchor_price']) / net['anchor_price'] * 100
                
                app_logger.critical(
                    f"💥 [V-SHAPE TRIGGER] {sym} flash crashed {drop_pct:.1f}%! "
                    f"Caught in the net at ${current_price:.6f}. Executing Market Buy!"
                )
                
                # Create a specialized signal for execution
                signal = {
                    'symbol': sym,
                    'strategy': 'V_SHAPE_CATCHER',
                    'entry_price': current_price,
                    'take_profit': current_price * 1.05,  # +5% quick bounce target
                    'stop_loss': current_price * 0.96,    # -4% absolute disaster stop
                    'confidence': 0.99,                   # Maximum confidence for extreme fear buying
                    'rr_ratio': 1.25
                }
                triggered_signals.append(signal)
                
                # Delete the net so we don't double-trigger
                del self.virtual_nets[sym]

        return triggered_signals

    def get_status_string(self):
        """Returns a string representing active nets for UI/Logs"""
        if not self.virtual_nets:
            return "No active nets"
        
        parts = []
        for sym, net in self.virtual_nets.items():
            parts.append(f"{sym}: ${net['target_price']:.4f}")
        return " | ".join(parts)
