import asyncio
import json
import aiohttp
from src.utils.logger import app_logger

class HftDepthEngine:
    """
    PROSOFT SWARM: High-Frequency Depth Engine.
    Subscribes to Binance WebSockets depth stream, calculates Order Book Imbalance (OBI),
    registers institutional walls, and computes front-running ticks.
    """
    def __init__(self, bot, shared_state):
        self.bot = bot
        self.state = shared_state
        self.is_running = False
        self.current_symbol = None
        self.ws_task = None
        
        # Order book data
        self.bids = []
        self.asks = []
        self.obi = 0.0
        
    async def start(self, symbol="BTCUSDT"):
        self.is_running = True
        self.current_symbol = symbol.lower()
        self.ws_task = asyncio.create_task(self._connect_websocket())
        app_logger.info(f"⚡ HFT WebSockets Depth Engine STARTED for {symbol.upper()}.")
        
    async def stop(self):
        self.is_running = False
        if self.ws_task:
            self.ws_task.cancel()
            
    async def switch_symbol(self, symbol):
        """Dynamically subscribes to a new symbol's depth stream."""
        await self.stop()
        await self.start(symbol)
        
    async def _connect_websocket(self):
        url = f"wss://stream.binance.com:9443/ws/{self.current_symbol}@depth20@100ms"
        
        while self.is_running:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.ws_connect(url) as ws:
                        app_logger.info(f"[HFT DEPTH] Connected to Binance WebSockets stream for {self.current_symbol.upper()}")
                        
                        async for msg in ws:
                            if not self.is_running:
                                break
                                
                            if msg.type == aiohttp.WSMsgType.TEXT:
                                data = json.loads(msg.data)
                                await self._process_depth_update(data)
                            elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                                break
                                
            except asyncio.CancelledError:
                break
            except Exception as e:
                app_logger.error(f"[HFT DEPTH ERROR] Connection failed: {e}. Reconnecting in 5s...")
                await asyncio.sleep(5)
                
    async def _process_depth_update(self, data):
        """Processes raw L2 depth update and computes imbalance metrics."""
        try:
            # Parse bids and asks
            raw_bids = data.get('bids', [])
            raw_asks = data.get('asks', [])
            
            self.bids = [[float(b[0]), float(b[1])] for b in raw_bids]
            self.asks = [[float(a[0]), float(a[1])] for a in raw_asks]
            
            if not self.bids or not self.asks:
                return
                
            # 1. Calculate Order Book Imbalance (OBI)
            # Sum volume of top 10 price levels
            bid_vol = sum([b[1] for b in self.bids[:10]])
            ask_vol = sum([a[1] for a in self.asks[:10]])
            
            total_vol = bid_vol + ask_vol
            if total_vol > 0:
                self.obi = (bid_vol - ask_vol) / total_vol
            else:
                self.obi = 0.0
                
            # Log depth updates periodically in stats
            self.state.strategy_overrides['HFT_OBI'] = self.obi
            
        except Exception as e:
            app_logger.error(f"[HFT DEPTH ERROR] Failed to process update: {e}")
            
    def get_front_run_price(self, side, ticker_price):
        """
        HFT Wall Snatcher: returns the optimal front-running price
        by placing the order exactly 1 tick in front of the largest institutional wall.
        """
        try:
            if side == 'BUY':
                if not self.bids:
                    return ticker_price
                    
                # Find the largest buy wall (largest volume) in top 10 bids
                max_level = max(self.bids[:10], key=lambda x: x[1])
                wall_price = max_level[0]
                
                # Tick size approximation
                tick_size = 0.01 if ticker_price > 10.0 else 0.0001
                if ticker_price > 50000.0: tick_size = 0.1
                
                # Front-run by 1 tick (buy slightly higher than the wall)
                front_run = wall_price + tick_size
                return min(front_run, ticker_price * 1.001)  # cap at 0.1% slippage
                
            else: # SELL
                if not self.asks:
                    return ticker_price
                    
                # Find the largest sell wall in top 10 asks
                max_level = max(self.asks[:10], key=lambda x: x[1])
                wall_price = max_level[0]
                
                tick_size = 0.01 if ticker_price > 10.0 else 0.0001
                if ticker_price > 50000.0: tick_size = 0.1
                
                # Front-run by 1 tick (sell slightly lower than the wall)
                front_run = wall_price - tick_size
                return max(front_run, ticker_price * 0.999)  # cap at 0.1% slippage
                
        except Exception:
            return ticker_price
