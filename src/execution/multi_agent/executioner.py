import asyncio
import time
from src.utils.logger import app_logger

class ExecutionerAgent:
    """
    PROSOFT SWARM: Execution Agent.
    Background worker that monitors the shared entry queue, obtains final authorization
    from the Risk Warden, and executes trades with millisecond-speed priority.
    """
    def __init__(self, bot, shared_state, risk_warden):
        self.bot = bot
        self.state = shared_state
        self.risk_warden = risk_warden
        self.is_running = False
        
    async def start(self):
        self.is_running = True
        asyncio.create_task(self._queue_worker())
        app_logger.info("⚡ Execution Agent (Order-Executioner) STARTED successfully.")
        
    async def stop(self):
        self.is_running = False
        
    async def _queue_worker(self):
        while self.is_running:
            try:
                # 1. Fetch pending entry request from queue (non-blocking wait)
                request = await self.state.entry_queue.get()
                
                symbol = request['symbol']
                signal = request['signal']
                ai_conf = request['ai_conf']
                reply_future = request['reply_future']
                
                # 2. Query Risk Warden for clearance
                allowed, reason = await self.risk_warden.evaluate_entry_clearance(symbol, signal, ai_conf)
                
                if not allowed:
                    app_logger.warning(f"🚫 [SWARM ENTRY BLOCKED] {symbol} rejected by Risk Warden: {reason}")
                    reply_future.set_result((False, reason))
                    self.state.entry_queue.task_done()
                    continue
                    
                # 3. All gates passed -> execute order via standard engine
                app_logger.info(f"🚀 [SWARM ENTRY AUTHORIZED] {symbol}: Risk Warden cleared. Executing now...")
                
                # We call the main bot's unified entry logic
                trade = await self.bot._execute_entry(
                    symbol=symbol,
                    signal=signal,
                    ai_conf=ai_conf,
                    market_health=self.state.market_health,
                    fgi=self.state.fgi
                )
                
                if trade:
                    reply_future.set_result((True, trade))
                else:
                    reply_future.set_result((False, "Execution failure inside broker API"))
                    
                self.state.entry_queue.task_done()
                
            except Exception as e:
                app_logger.error(f"[EXECUTIONER ERROR] Queue loop crash: {e}")
                await asyncio.sleep(1)
