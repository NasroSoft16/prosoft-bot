import asyncio
import time
from src.utils.logger import app_logger

class RiskWardenAgent:
    """
    PROSOFT SWARM: Risk Warden Agent (The Portfolio Guardian).
    Background worker that continuously evaluates portfolio health, active drawdowns,
    computes Kelly Criterion position sizing, and authorizes/vetoes trade entry requests.
    """
    def __init__(self, bot, shared_state):
        self.bot = bot
        self.state = shared_state
        self.is_running = False
        self.poll_interval = 10  # Check portfolio metrics every 10 seconds
        
    async def start(self):
        self.is_running = True
        asyncio.create_task(self._run_loop())
        app_logger.info("🛡️ Risk Warden Agent (Portfolio-Guardian) STARTED successfully.")
        
    async def stop(self):
        self.is_running = False
        
    async def _run_loop(self):
        while self.is_running:
            try:
                # 1. Fetch current portfolio milestone details
                milestone = self.bot.milestone_state
                max_trades = self.bot.max_concurrent_trades
                
                # 2. Compute dynamic multiplier (Kelly Sizing)
                multiplier = 1.0
                current_health = self.state.market_health
                win_rate = self.bot.stats.get('ai_accuracy', 50)
                
                if win_rate >= 65 and current_health >= 55:
                    multiplier = 1.8  # Scale up sizing for high-probability setups
                elif win_rate <= 45 or current_health <= 40:
                    multiplier = 0.5  # Scale down sizing for risky regimes
                    
                # 3. Check for hedging triggers (e.g. if health is critically low and FGI is panic)
                hedging_needed = False
                if current_health < 33.0 and self.state.fgi < 35:
                    hedging_needed = True
                    
                # Sync rules to the shared state
                await self.state.update_risk_rules(
                    max_trades=max_trades,
                    multiplier=multiplier,
                    hedging=hedging_needed
                )
                
            except Exception as e:
                app_logger.error(f"[RISK WARDEN ERROR] Failed in portfolio assessment: {e}")
                
            await asyncio.sleep(self.poll_interval)
            
    async def evaluate_entry_clearance(self, symbol, signal, ai_conf):
        """
        Sync audit: evaluates whether a specific trade entry is allowed to execute.
        Returns (allowed: bool, reason: str).
        """
        # Layer 1: Max active trades check
        max_allowed = self.state.max_concurrent_trades
        if len(self.bot.active_trades) >= max_allowed:
            return False, f"Risk Warden: Max concurrent trades limit reached ({len(self.bot.active_trades)}/{max_allowed})"
            
        # Layer 2: Blacklist/Isolation check
        if symbol in self.bot.blacklisted_symbols:
            expiry = self.bot.blacklisted_symbols[symbol]
            if time.time() < expiry:
                return False, f"Risk Warden: Symbol {symbol} is currently in isolation"
                
        # Layer 3: Absolute panic floor checks
        health = self.state.market_health
        fgi = self.state.fgi
        
        # Micro-Account Iron Floor (Equity < $40)
        balance = self.bot.api.get_account_balance('USDT')
        equity = self.bot.stats.get('total_equity', balance)
        
        if equity < 40.0 and health < 35.0:
            return False, f"Risk Warden: Micro-Account Iron Floor triggered (Health {health:.1f}% < 35%)"
            
        if health < 33.0:
            return False, f"Risk Warden: Absolute Panic Gate triggered (Health {health:.1f}% < 33%)"
            
        # Check XGBoost Risk
        if hasattr(self.bot, 'xgb_shield') and self.bot.xgb_shield.is_trained:
            sentiment = self.state.sentiment
            prob_fakeout = self.bot.xgb_shield.predict_fakeout(
                ai_confidence=ai_conf,
                market_health=health,
                strategy_used="Squeeze" if "Rocket" not in signal.get('indicators', {}).get('Strategy', '') else "Rocket",
                sentiment=sentiment
            )
            if prob_fakeout > 0.75:
                return False, f"Risk Warden: XGBoost blocked - {prob_fakeout*100:.1f}% fakeout probability"
                
        return True, "Authorized"
