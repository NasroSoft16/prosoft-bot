import asyncio
import time

class GlobalSharedState:
    """
    PROSOFT SWARM: Global Shared State.
    Thread-safe and async-safe container for exchanging data, signals, and vetoes between agents.
    """
    def __init__(self):
        self.lock = asyncio.Lock()
        
        # Macro indicators updated by Sentinel
        self.market_health = 50.0
        self.fgi = 50
        self.btc_dominance = 50.0
        self.sentiment = "NEUTRAL"
        self.vix = 18.0
        self.dxy_change = 0.0
        self.ndq_change = 0.0
        self.last_macro_update = 0.0
        
        # Risk thresholds managed by Risk Warden
        self.max_concurrent_trades = 1
        self.qty_multiplier = 1.0
        self.is_hedging_active = False
        
        # Self-tuner overrides
        self.strategy_overrides = {}
        
        # Queue for pending entry requests from strategies to Execution Agent
        self.entry_queue = asyncio.Queue()
        
        # Active trades list (shared reference)
        self.active_trades = []
        
    async def update_macro(self, health, fgi, btc_dom, sentiment, vix=18.0, dxy_change=0.0, ndq_change=0.0):
        async with self.lock:
            self.market_health = float(health)
            self.fgi = int(fgi)
            self.btc_dominance = float(btc_dom)
            self.sentiment = str(sentiment)
            self.vix = float(vix)
            self.dxy_change = float(dxy_change)
            self.ndq_change = float(ndq_change)
            self.last_macro_update = time.time()
            
    async def update_risk_rules(self, max_trades, multiplier, hedging):
        async with self.lock:
            self.max_concurrent_trades = int(max_trades)
            self.qty_multiplier = float(multiplier)
            self.is_hedging_active = bool(hedging)
            
    async def set_strategy_override(self, strategy_name, overrides):
        async with self.lock:
            self.strategy_overrides[strategy_name] = overrides
            
    async def request_entry(self, symbol, signal, ai_conf):
        """Called by strategies to request entry clearance."""
        request = {
            'symbol': symbol,
            'signal': signal,
            'ai_conf': ai_conf,
            'timestamp': time.time(),
            'reply_future': asyncio.get_running_loop().create_future()
        }
        await self.entry_queue.put(request)
        return await request['reply_future']
