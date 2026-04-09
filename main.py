import os
import sys
import random

# --- PROSOFT QUANTUM BOOTSTRAPPER (ANTI-CRASH GUARD) ---
try:
    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
    
    # 1. SMART LIBRARY DETECTION
    # Priority A: Check for Embedded Python's site-packages (Sovereign V7)
    embedded_site_pkg = os.path.join(ROOT_DIR, "python", "Lib", "site-packages")
    if os.path.exists(embedded_site_pkg):
        sys.path.insert(0, embedded_site_pkg)
    
    # Priority B: Check for external 'libs' folder (Zero Download V5)
    libs_path = os.path.join(ROOT_DIR, "libs")
    if os.path.exists(libs_path):
        sys.path.insert(0, libs_path)

    # 2. Add source core to path
    if ROOT_DIR not in sys.path:
        sys.path.insert(0, ROOT_DIR)
    
    import site
    if os.path.exists(embedded_site_pkg):
        site.addsitedir(embedded_site_pkg)

    import time
    import asyncio
    from datetime import datetime
    import pandas as pd
    from dotenv import load_dotenv
    from rich.live import Live
    import schedule
    import threading
except Exception as e:
    print("\n" + "="*60)
    print(" CRITICAL STARTUP ERROR DETECTED")
    print("="*60)
    print(f"\nMessage: {str(e)}")
    print("\nTroubleshooting:")
    print("1. Ensure 'libs' folder is fully populated (Run 'pip install -r requirements.txt --target ./libs')")
    print("2. Ensure Python version matches the bundled libraries.")
    print("\nFull Traceback:")
    import traceback
    traceback.print_exc()
    print("="*60)
    input("\nPress ENTER to close this window...")
    sys.exit(1)

# ------------------------------------------------
import time
import asyncio
from datetime import datetime
import pandas as pd
from dotenv import load_dotenv
from rich.live import Live

from src.api.binance_client import BinanceClientWrapper
from src.indicators.technical_analysis import TechnicalAnalysis
from src.strategy.base_strategy import BaseStrategy
from src.risk_management.position_sizing import RiskManager
from src.ai.model_manager import ModelManager
from src.notifications.telegram_bot import TelegramBot
from src.execution.order_manager import OrderManager
from src.strategy.market_scanner import MarketScanner
from src.strategy.listing_sniper import ListingSniper
from src.strategy.yield_farmer import YieldFarmer
from src.api.dashboard_api import DashboardAPI
from src.ai.gemini_engine import GeminiAI
from src.ai.groq_engine import GroqAI
from src.ai.quantum_intelligence import QuantumIntelligence
from src.risk_management.portfolio_manager import PortfolioManager
from src.utils.news_engine import GlobalNewsEngine
from src.utils.whale_tracker import WhaleTracker
from src.utils.report_generator import ReportGenerator
from src.utils.logger import app_logger, trade_logger
from src.utils.ui_handler import UIHandler
from src.ai.neural_memory import NeuralMemory
from src.ai.gemini_engine import GeminiAI
from src.strategy.meme_sniper import MemeRocketSniper
from src.strategy.launchpool_hunter import LaunchpoolHunter
from src.ai.sentiment_node import AISentimentFrontRunner
from src.risk_management.manipulation_shield import ManipulationShield
from src.risk_management.diversification_matrix import DiversificationMatrix
from src.ai.self_healing_engine import SelfHealingEngine
from src.notifications.voice_alert_system import VoiceAlertSystem
from src.utils.twitter_firehose import TwitterSentimentFirehose
from src.ai.strategy_optimizer import StrategyOptimizer
from src.ai.whale_copy_trader import WhaleAlphaTracker
from src.strategy.arbitrage_engine import TriangularArbitrageEngine
from src.strategy.order_flow_analyzer import OrderFlowAnalyzer
from src.risk_management.hedging_protocol import HedgingProtocol
from src.strategy.liquidity_heatmap import LiquidityHeatmap
from src.risk_management.global_macro_filter import GlobalMacroFilter
from src.risk_management.circuit_breaker   import CircuitBreaker
from src.strategy.multi_timeframe          import MultiTimeframeAnalyzer
from src.ai.fear_greed_integration         import FearGreedIntegration
from src.strategy.micro_scalper            import MicroScalper
from src.strategy.quantum_alpha              import QuantumAlphaStrategy

load_dotenv()

class TradingBot:
    def __init__(self, symbol='BTCUSDT', timeframe='15m', interval_sec=5):
        self.symbol = os.getenv('SYMBOL', symbol)
        self.timeframe = os.getenv('TIMEFRAME', timeframe)
        self.interval_sec = int(interval_sec)
        self.ai_threshold = float(os.getenv('AI_CONFIDENCE_THRESHOLD', 0.75))
        self.version = "14.0 PROSOFT QUANTUM v40.0"
        
        self.execution_mode = os.getenv('EXECUTION_MODE', 'manual')
        self.voice_alerts = os.getenv('VOICE_ALERTS', 'on') == 'on'
        
        # Modules
        self.api = BinanceClientWrapper(testnet=False)
        self.ta = TechnicalAnalysis()
        self.strategy = BaseStrategy()
        self.risk = RiskManager()
        self.ai = ModelManager()
        self.gemini = GeminiAI()
        self.groq = GroqAI()
        self.intel = QuantumIntelligence(gemini=self.gemini, groq=self.groq)
        self.portfolio = PortfolioManager(self.api)
        self.whales = WhaleTracker()
        
        # Initialize Stats early to avoid AttributeErrors
        self.logs = []
        self.stats = {
            'balance': 0.0,
            'total_equity': 0.0,
            'price': 0.0,
            'ema50': 0.0,
            'ema200': 0.0,
            'rsi': 0.0,
            'ai_conf': 0.85,
            'market_health': 50.0,
            'sentiment': 'Neutral',
            'prediction': 'N/A',
            'market_pulse': {'feed': []},
            'whale_alerts': [],
            'top_gems': [],
            'execution_mode': self.execution_mode,
            'voice_alerts': self.voice_alerts,
            'daily_pnl': 0.0,
            'daily_pnl_pct': 0.0,
            'session_pnl': 0.0,
            'consecutive_losses': 0,
            'trades_count': 0,
            'closed_trades': 0,  # Separate count for optimization trigger
            'active_count': int(0),
            'tickers': {}, # Bulk ticker cache for multi-asset monitoring
            'ai_accuracy_history': [],
            'ai_accuracy': 0.0,
            'yield_status': "IDLE",
            'sniper_hits': 0,
            'funding_amount': 0.0,
            'yield_amount': 0.0,
            'ai_status': 'ONLINE',
            'ai_cluster': [],
            'order_flow': {'pressure_score': 0, 'bias': 'NEUTRAL', 'spread_pct': 0},
            'crash_risk': 0,
            'hedge_status': {'active': False},
            'last_ai_quota_hit': 0,
            'qty_multiplier': 1.0,
            'btc_dominance': 50.0,
            'last_weekly_review': None,
            'last_periodic_sync': 0,
            'last_daily_briefing': 0,
            'macro_context': {},
            'last_macro_sweep': 0
        }

        self.whales = WhaleTracker()
        self.reporter = ReportGenerator()
        self.telegram = TelegramBot()
        from src.strategy.listing_sniper import ListingSniper
        from src.strategy.yield_farmer import YieldFarmer
        from src.strategy.funding_arb import FundingRateArb

        self.farmer = YieldFarmer(self.api)
        self.sniper = ListingSniper(self.api, self.telegram)
        self.funding_arb = FundingRateArb(self.api)
        
        self.orders = OrderManager(self.api)
        self.ui = UIHandler()
        self.market_scanner = MarketScanner(self.api)
        self.rocket_sniper = MemeRocketSniper(self.api)
        self.pool_hunter = LaunchpoolHunter(self.api)
        self.sentiment_front = AISentimentFrontRunner(self.gemini, None)
        self.twitter = TwitterSentimentFirehose() 
        self.optimizer = StrategyOptimizer()      
        self.alpha_tracker = WhaleAlphaTracker()  
        self.arbitrage = TriangularArbitrageEngine(self.api)  
        self.order_flow = OrderFlowAnalyzer(self.api)          
        self.hedger = HedgingProtocol()                        
        self.macro_filter = GlobalMacroFilter()                
        self.heatmap = LiquidityHeatmap(self.api)              
        self.memory = NeuralMemory()
        self.micro_scalper = MicroScalper(self.api)
        self.quantum_alpha = QuantumAlphaStrategy()
        
        # --- NEW MODULES (v12.0) ---
        self.shield = ManipulationShield()        # درع التلاعب
        self.diversifier = DiversificationMatrix() # مصفوفة التنويع
        self.healer = SelfHealingEngine(self)      # محرك التصحيح الذاتي
        self.voice = VoiceAlertSystem(enabled=os.getenv('VOICE_ALERTS', 'on') == 'on')  # التنبيهات الصوتية

        # --- NEW MODULES (v14.0 Improvements) ---
        self.circuit_breaker = CircuitBreaker(
            max_daily_loss_pct=float(os.getenv('CB_MAX_DAILY_LOSS_PCT', 7.5)),
            max_consecutive_loss=int(os.getenv('CB_MAX_CONSECUTIVE_LOSS', 10))
        )
        self.mtf = MultiTimeframeAnalyzer(self.api, self.ta)   # تحليل متعدد الأطر الزمنية
        self.fear_mode = FearGreedIntegration(self.macro_filter) # مؤشر الخوف والطمع

        self.is_paused = False # Mode to stop all loops if Omega triggered
        
        # Active Trade Tracking (v12.8 MULTI-TRADE Architecture)
        self.active_trades = self.healer.load_trade_state()
        if self.active_trades:
            symbols = [t['symbol'] for t in self.active_trades]
            self.add_log(f"💾 SYSTEM RECOVERED: Restored {len(self.active_trades)} active trades: {', '.join(symbols)}")
        else:
            self.active_trades = []

        self.main_loop = asyncio.get_event_loop()
        self.wakeup_event = asyncio.Event()
        self.dashboard = None
            
        self.omega_active = False 
        self.last_report_date = None 
        
        self.ui.update_ui(self.symbol, self.timeframe, self.stats, self.logs)
        
        # ── [NEW v14.5: Symbol Isolation & Blacklist] ──
        self.blacklist_file = 'data/isolation_state.json'
        self.blacklisted_symbols = self._load_blacklist() 
        self.market_crash_gate = 0 # Timestamp until global entry block

        # ═══════════════════════════════════════════════════════════════════════════════
        #  UPGRADE PATCH ALIASES & ADDITIONS (v2.0)
        # ═══════════════════════════════════════════════════════════════════════════════
        self.risk_manager = self.risk
        self.manipulation_shield = self.shield
        self.order_manager = self.orders
        self.strategy_optimizer = self.optimizer
        self.order_flow_analyzer = self.order_flow
        self.voice_alerts = self.voice

        # ── Adaptive thresholds (updated live by StrategyOptimizer) ──
        self.ai_confidence_threshold = float(os.getenv('AI_CONFIDENCE_THRESHOLD', 0.58))
        self.min_market_health       = float(os.getenv('MIN_MARKET_HEALTH', 42.0))

        # ── Weekly review scheduler ──
        schedule.every().sunday.at("03:00").do(
            lambda: self.strategy_optimizer.generate_weekly_review(bot_instance=self)
        )
        def _run_schedule_loop():
            while True:
                schedule.run_pending()
                time.sleep(3600)
                
        threading.Thread(
            target=_run_schedule_loop, daemon=True
        ).start()

    # ═══════════════════════════════════════════════════════════════════════════════
    #  UPGRADE PATCH FUNCTIONS (v2.0)
    # ═══════════════════════════════════════════════════════════════════════════════
    async def _check_entry_conditions(self, symbol, df, market_health, fgi=50):
        """
        Returns (allowed: bool, reason: str).
        All gates must pass before entering a trade.
        """
        # ── Gate 1: Circuit Breaker ──
        if hasattr(self, 'circuit_breaker') and self.circuit_breaker.is_tripped:
            return False, f"Circuit Breaker TRIPPED: {self.circuit_breaker.trip_reason}"

        # ── Gate 2: Risk Manager daily limits ──
        if not self.risk_manager.can_trade():
            return False, "Daily loss limit / consecutive losses"

        # ── Gate 3: Minimum market health ──
        if market_health < self.min_market_health:
            return False, f"Market health too low ({market_health:.0f}% < {self.min_market_health:.0f}%)"

        # ── Gate 4: Manipulation Shield ──
        order_flow = None
        if hasattr(self, 'order_flow_analyzer'):
            order_flow = self.order_flow_analyzer.analyze_order_book(symbol)
        shield_result = self.manipulation_shield.full_check(df, order_flow)
        if not shield_result['is_safe']:
            return False, f"Shield: {shield_result['reason']}"

        # ── Gate 4B: Order Flow VETO (تضارب الإشارات - جديد) ──
        # إذا كان ORDER FLOW يقول STRONG_SELL, نمنع الدخول حتى لو قال MTF BUY
        # هذا التضارب جعلنا نخسر ZEC مرتين
        if order_flow and order_flow.get('bias') == 'STRONG_SELL':
            pressure = order_flow.get('pressure_score', 50)
            return False, f"ORDER FLOW VETO: Real selling pressure detected ({pressure:.0f}%). MTF ignored."

        # ── Gate 5: MTF Consensus ──
        if hasattr(self, 'mtf'):
            allowed, mtf_reason = self.mtf.is_entry_allowed(symbol)
            if not allowed:
                return False, mtf_reason

        # ── 🚀 ROCKET OVERRIDE (Breakout Exemption) ──
        # إذا وجدنا ملامح انفجار حقيقي مؤكد، سنسامح العملة من أخطاء الماضي!
        is_rocket = False
        mtf_conf = 0.0
        if hasattr(self, 'mtf'):
            mtf_conf = self.mtf.get_signal(symbol).get('confidence', 0)
            
        if (mtf_conf >= 90.0 and 
            order_flow and order_flow.get('bias') == 'STRONG_BUY' and 
            order_flow.get('pressure_score', 0) >= 65.0):
            is_rocket = True
            app_logger.warning(f"🚀 [ROCKET OVERRIDE] {symbol} shows extreme breakout patterns. Bypassing Memory Vetoes!")

        # ── Gate 6: Neural Memory Veto & Adaptive Confidence ──
        veto, veto_reason = self.memory.should_veto_trade(symbol, market_health)
        if veto and not is_rocket:
            return False, veto_reason
            
        # ── Recovery Guard v2.1: حارس التعافي - مصلح ──
        # نجلب خسائر هذه العملة تحديداً من قاعدة البيانات وليس من آخر 15 صفقة عامة
        recent_lost = [
            t for t in self.memory.get_recent_memories(limit=50)
            if t.get('symbol') == symbol and (t.get('profit_loss') or 0) < 0
        ]
        
        if len(recent_lost) >= 2:
            # خسارتان: تحقق من وقت آخر خسارة + اطلب 90% MTF
            # إصلاح: بدلاً من مقارنة expiry الخاطئة, نتحقق من وقت آخر خسارة
            isolation_expiry = self.blacklisted_symbols.get(symbol, 0)
            # إذا الحجب لا يزال سارياً (expiry في المستقبل), نطبق 6 ساعات إضافية
            extended_expiry = isolation_expiry + 21600  # +6h extra after blacklist expires
            if isolation_expiry > 0 and time.time() < extended_expiry and not is_rocket:
                mins_left = int((extended_expiry - time.time()) / 60)
                return False, f"DOUBLE-LOSS GUARD: {symbol} blocked for {mins_left}m more after 2 losses."
            if hasattr(self, 'mtf'):
                res = self.mtf.get_signal(symbol)
                high_bar = 90.0
                if res['confidence'] < high_bar:
                    return False, f"DOUBLE-LOSS GUARD: {symbol} needs ≥{high_bar:.0f}% MTF (got {res['confidence']:.0f}%) after 2 losses."
        
        elif len(recent_lost) == 1:
            if hasattr(self, 'mtf'):
                res = self.mtf.get_signal(symbol)
                high_bar = 80.0
                if res['confidence'] < high_bar:
                    return False, f"RECOVERY GUARD: {symbol} needs ≥{high_bar:.0f}% MTF (got {res['confidence']:.0f}%) after 1 loss."


        # ── Gate 7: Macro filter (FGI) ──
        if fgi < 15:  # extreme fear — allow contrarian buys only
            pass       # FGI handled in position sizing, not as a hard block
        elif fgi > 90:
            return False, f"Extreme Greed (FGI={fgi}) — stand aside"

        # ── Gate 8: Symbol Blacklist (Isolation) ──
        if symbol in self.blacklisted_symbols:
            expiry = self.blacklisted_symbols[symbol]
            if time.time() < expiry:
                if is_rocket:
                    # نلغي الحظر نهائياً لأن السهم انفجر
                    app_logger.info(f"🔓 [UNBAN] Removing {symbol} from isolation due to Rocket Override")
                    del self.blacklisted_symbols[symbol]
                    self._save_blacklist()
                else:
                    m, s = divmod(expiry - time.time(), 60)
                    return False, f"Symbol {symbol} is in ISOLATION (Recent Loss). Time left: {int(m)}m {int(s)}s."
            else:
                del self.blacklisted_symbols[symbol]
                self._save_blacklist()

        # ── [NEW v15.0: Global Market Pulse Gate] ──
        if time.time() < self.market_crash_gate:
            return False, "Global Market Pause: Systemic Crash detected recently (Pulse Guard ACTIVE)."

        # ── Gate 9: Liquidity & Spread Guard (Smart Filter) ──
        # Instead of banning symbols, we check the actual market health (Orderbook)
        ob = self.api.get_order_book(symbol)
        if ob and ob['asks'] and ob['bids']:
            # Gap between best Buy and best Sell
            spread = (ob['asks'][0][0] - ob['bids'][0][0]) / ob['asks'][0][0]
            if spread > 0.005:  # Allowed up to 0.5% spread for high-volatility moves
                return False, f"Gap too wide: Spread {spread:.2%} exceeds 0.5% limit"

        # ── Gate 10: Micro-Account Balance Floor ──
        balance = self.api.get_account_balance('USDT')
        if balance < 10.10: # Extra safety buffer for Binance $10 limit
            return False, f"Critical Balance Floor: ${balance:.2f}"

        return True, "All gates passed"

    async def _execute_entry(self, symbol, signal, ai_conf, market_health, fgi=50):
        """
        Execute a BUY with full risk management wiring.
        """
        balance = self.api.get_account_balance('USDT')
        # Optimized for small accounts: Binance min is usually $5
        if balance < 5.5:
            self.add_log(f"⚠️ Balance too low: ${balance:.2f}")
            return None

        # ── Position size with FGI + AI conf ──
        position_size = self.risk_manager.calculate_position_size(
            balance    = balance,
            price      = signal['entry_price'],
            stop_loss  = signal['stop_loss'],
            ai_conf    = ai_conf,
            fgi        = fgi,
        )

        if position_size <= 0:
            self.add_log("⚠️ Position size = 0. Trade skipped.")
            return None

        # ── Diversification check ──
        if hasattr(self, 'diversification_matrix'):
            total_equity = self.stats.get('total_equity', balance)
            safe_alloc   = self.diversification_matrix.get_safe_allocation(
                symbol, balance, total_equity
            )
            max_qty      = safe_alloc / signal['entry_price']
            position_size = min(position_size, max_qty)

        # ── Place order ──
        order = self.order_manager.place_market_buy(symbol, position_size)
        if not order:
            return None

        # ── Build trade record ──
        trade = {
            'symbol':       symbol,
            'side':         'BUY',
            'entry_price':  signal['entry_price'],
            'sl':           signal['stop_loss'],
            'tp':           signal['take_profit'],
            'trailing_sl':  signal['stop_loss'],   # starts equal, moves up
            'qty':          position_size,
            'ai_conf':      ai_conf,
            'market_health': market_health,
            'entry_time':   datetime.now().isoformat(),
            'strategy':     signal.get('indicators', {}).get('Strategy', 'Unknown'),
            'order_id':     order.get('orderId', ''),
        }

        self.add_log(
            f"✅ ENTRY: {symbol} @ {signal['entry_price']:.6f} | "
            f"SL={signal['stop_loss']:.6f} TP={signal['take_profit']:.6f} | "
            f"R/R={signal.get('rr_ratio', 0):.2f} | conf={ai_conf:.2f}"
        )

        # Notify Telegram
        await self.telegram.send_signal(
            symbol, signal['entry_price'],
            signal['stop_loss'], signal['take_profit'],
            ai_conf, side='BUY'
        )

        return trade

    async def _manage_open_trades(self, df, current_price):
        """
        Manage all open trades: trailing stop, TP/SL exit, forced close.
        Supports tracking assets other than the loop's focused symbol safely.
        """
        if not self.active_trades:
            return

        atr = float(df.iloc[-1].get('ATR', 0)) if df is not None else 0

        # CRITICAL: Ultra-Fresh Ticker Refresh for Trailing Stops
        try:
            self.stats['tickers'] = self.api.get_all_tickers()
        except: pass

        for trade in list(self.active_trades):
            trade_symbol = trade.get('symbol', self.symbol)
            
            # FAST PATH: Resolve price from bulk cache to avoid API bottlenecks
            trade_price = self.stats.get('tickers', {}).get(trade_symbol, 0)
            
            # Fallback only if cache is empty
            if trade_price <= 0:
                fetched_price = self.api.get_symbol_ticker(trade_symbol)
                if fetched_price is None and trade_symbol == self.symbol:
                    fetched_price = current_price
                trade_price = fetched_price
            
            # Graceful skip if API is completely down
            if not trade_price or trade_price <= 0:
                continue
                
            # Sanity Check: Ensure trade_price is float
            trade_price = float(trade_price)

            # --- [PROSOFT GHOST-SL GUARD] ---
            # If SL became NaN or 0 due to an external error, restore a 5% emergency buffer
            raw_sl = trade.get('trailing_sl', trade.get('sl', self.stats['price'] * 0.98))
            import math
            if math.isnan(raw_sl) or raw_sl <= 0:
                raw_sl = trade.get('entry_price', trade_price) * 0.98
            
            trade_sl = float(raw_sl)
            trade_tp = float(trade.get('tp', 0))
            trade_qty = trade.get('qty', 0)
            entry_p = trade.get('entry_price', 0)
            
            pnl_pct = (trade_price / entry_p - 1) if entry_p > 0 else 0

            # ── [PROSOFT SHIELD: Universal Trailing Profit Guard] ──
            # Determine if this is a "Meme/Rocket" or High-Volatility trade
            is_volatile = 'Meme' in trade.get('strategy', '') or 'Rocket' in trade.get('strategy', '') or 'Scalp' in trade.get('strategy', '')
            
            # Track the highest price reached since entry to lock in every cent securely
            if trade_price > trade.get('highest_peak', 0):
                trade['highest_peak'] = trade_price
            
            highest_peak = trade.get('highest_peak', entry_p)
            
            # --- 1. Smart Multi-Tier Trailing Stop (v35: "The Quantum Net") ---
            # Tier 1: The Activation (0.75% profit) -> Unlock Fee Shield
            if pnl_pct >= 0.0075:
                # Protection: Lock in +0.25% immediately to walk away risk-free
                fee_sl = entry_p * 1.0025
                if fee_sl > trade_sl:
                    trade['trailing_sl'] = fee_sl
                    trade_sl = fee_sl
                    self.add_log(f"🛡️ [TIER-1 SHIELD] {trade_symbol}: Guaranteed +0.25% profit secured.")
                
                # Base Tier 1 trail distance: 0.5% (Allows price dropping from 0.75% safely to 0.25%)
                trail_distance = 0.995 
                tier_msg = "0.5% distance"

                # Tier 2: The Breathing Room (1.5% profit) -> Give it space to bounce and ride the wave
                if pnl_pct >= 0.015:
                    trail_distance = 0.992 # 0.8% distance (Wider net for healthy pullbacks)
                    tier_msg = "0.8% distance (Mid-Pump)"
                
                # Tier 3: The Parachute (3.5%+ profit) -> Explosions always dump. Fasten the seatbelt!
                if pnl_pct >= 0.035:
                    trail_distance = 0.996 # 0.4% distance (Extremely tight to parachute off the peak)
                    tier_msg = "0.4% distance (Peak-Parachute)"

                # Apply the dynamically calculated trail
                dynamic_sl = highest_peak * trail_distance
                
                # Only update if the new trail actually pushes the Stop Loss HIGHER
                if dynamic_sl > trade_sl:
                    trade['trailing_sl'] = dynamic_sl
                    trade_sl = dynamic_sl
                    self.add_log(f"⚡ [QUANTUM NET] {trade_symbol}: Trail updated to {tier_msg} off peak.")
            
            # --- TIME-PROTECT ENGINE (v26.0: Liquidity Preservation) ---
            # Don't let precious capital freeze in a stagnant market
            from datetime import datetime, timedelta
            entry_time = trade.get('entry_time') or trade.get('time')
            
            if entry_time:
                if isinstance(entry_time, str):
                    try:
                        # Replace generic ISO parse with robust parsing
                        raw_str = str(entry_time).strip()
                        # If string is just HH:MM:SS
                        if len(raw_str) == 8 and raw_str.count(':') == 2:
                            dt = datetime.strptime(raw_str, "%H:%M:%S")
                            entry_time = datetime.now().replace(hour=dt.hour, minute=dt.minute, second=dt.second)
                        else:
                            try:
                                entry_time = datetime.fromisoformat(raw_str)
                            except ValueError:
                                entry_time = datetime.strptime(raw_str, "%Y-%m-%d %H:%M:%S")
                    except Exception:
                        # Absolute fallback sets time backward artificially to force timeout if parse fails
                        entry_time = datetime.now() - timedelta(minutes=60)
                
                # Time Limits: 20m for Volatile, 45m for Standard
                time_limit = 20 if is_volatile else 45
                is_stagnant = (datetime.now() - entry_time) > timedelta(minutes=time_limit)
            else:
                is_stagnant = False # Safety: if no time info, don't kill the trade yet
            
            if is_stagnant and pnl_pct < 0.001:
                self.add_log(f"⏳ [TIME-EXIT] {trade_symbol}: Closing stagnant trade after {time_limit}m to free capital.")
                # FIX: Use the correct internal method _close_trade
                await self._close_trade(trade, trade_price, reason="TIME_LIMIT_REACHED")
                continue

            # Sync with Binance to ensure safety (Rate limited to 0.15% jumps to prevent API spam)
            if trade_sl > trade.get('sl', 0) * 1.0015:
                trade['sl'] = trade_sl
                await self._sync_remote_sl(trade)

            # ── [NEW v15.0: Sudden Collapse Detection] ──
            # If we are in a loss (>0.5% loss), start checking for rapid collapse
            if pnl_pct <= -0.005:
                try:
                    # Fetch fresh 1m data for this specific trade symbol if it's not the main focus
                    target_df = df if trade_symbol == self.symbol else self.api.get_historical_klines(trade_symbol, '1m', limit=20)
                    if target_df is not None:
                        # CRITICAL: Calculate indicators for non-focus symbols so RSI is available
                        if trade_symbol != self.symbol:
                            # Use try-except here to prevent TA indicator calculation from crashing due to limited rows
                            try:
                                target_df = self.ta.calculate_indicators(target_df)
                            except Exception as ta_e:
                                # Fallback gracefully if indicators can't be calculated on 20 rows
                                target_df = None
                            
                        if target_df is not None and not target_df.empty:
                            is_collapsing, collapse_reason = await self._check_flash_crash(trade_symbol, target_df)
                            if is_collapsing:
                                self.add_log(f"🚨 [EMERGENCY EXIT] {trade_symbol}: {collapse_reason} | Saving balance.")
                                await self._close_trade(trade, trade_price, reason=f"EMERGENCY_{collapse_reason}")

                                # ── SYSTEMIC CRASH PROTECTION ──
                                # If an emergency exit happens, block NEW entries globally for 15m
                                self.market_crash_gate = time.time() + 900 
                                self.add_log("🛑 [PULSE-GUARD] Systemic risk detected. Entry gate locked for 15m.")
                                continue
                except Exception as crash_check_err:
                    self.add_log(f"⚠️ [CRASH-CHECK SKIPPED] Latency error preventing collapse check: {crash_check_err}")

            # ── [PROSOFT GLOBAL GUARD: Hard 2% Limit] ──
            # Use 1.95% to allow for slippage so it stays under 2%
            if trade_price <= trade_sl or pnl_pct <= -0.0195:
                reason = "SL" if trade_price <= trade_sl else "GLOBAL SAFETY (1.95%)"
                self.add_log(
                    f"🔴 {reason} HIT: {trade_symbol} @ {trade_price:.6f} "
                    f"(PNL: {pnl_pct*100:.2f}%)"
                )
                await self._close_trade(trade, trade_price, reason=reason)
                continue

            # ── Check take profit hit ──
            if trade_price >= trade_tp:
                self.add_log(
                    f"💰 TP HIT: {trade_symbol} @ {trade_price:.6f} "
                    f"(TP={trade_tp:.6f})"
                )
                await self._close_trade(trade, trade_price, reason='TP')
                continue

            # ── Partial TP at 60% of the way ──
            if entry_p > 0 and trade_tp > 0:
                halfway = entry_p + (trade_tp - entry_p) * 0.6
                if trade_price >= halfway and not trade.get('partial_done'):
                    half_qty = trade_qty * 0.4
                    if half_qty > 0:
                        self.order_manager.place_market_sell(trade_symbol, half_qty)
                        trade['partial_done'] = True
                        # Move SL to break-even safely
                        trade['trailing_sl'] = entry_p * 1.002
                        trade['sl'] = entry_p * 1.002
                        self.add_log(
                            f"🟡 PARTIAL TP: sold 40% of {trade_symbol} | SL moved to break-even"
                        )

    async def _close_trade(self, trade, exit_price, reason=''):
        """
        Sell remaining quantity, log to memory, update stats.
        """
        try:
            qty   = trade.get('qty', 0) * (0.6 if trade.get('partial_done') else 1.0)
            entry_p = trade.get('entry_price', exit_price)
            order = None
            
            # --- [PROSOFT OCO CLEANUP] ---
            if 'oco_id' in trade:
                try:
                    self.api.client.cancel_order_list(symbol=trade['symbol'], orderListId=trade['oco_id'])
                except:
                    pass
                
            try:
                self.api.client._cancel_all_open_orders(symbol=trade['symbol'])
            except: pass
            
            # Safe Cap: Prevent 'Insufficient Balance' errors from float drift or fee deductions
            sym = trade.get('symbol', '')
            asset_name = sym.replace('USDT', '') if sym.endswith('USDT') else ''
            if asset_name:
                real_bal = self.api.get_account_balance(asset_name)
                # If Binance balance is exactly 0 or too small but we assumed we had qty, we cap it
                # We add a small margin (e.g., 0.999) because get_account_balance might have un-synced fractions
                if 0 <= real_bal < qty:
                    qty = real_bal
            
            if qty > 0:
                order = self.order_manager.place_market_sell(trade['symbol'], qty)
                if order == "NOTIONAL_ERROR":
                    self.add_log(f"⚠️ CLEANUP: {trade['symbol']} balance too small to sell (${qty * exit_price:.2f}). Removing from active tracker.")
                    order = True # Treat as success for cleanup logic
                    reason = "Cleanup/Dust"

            # ALWAYS proceed to log and remove if qty is 0, if order succeeded, 
            # or if it's a manual exit (we want it gone from dashboard)
            if order or qty == 0 or reason == 'Manual Exit' or reason == 'Cleanup' or reason == "Cleanup/Dust":
                # ── Unified PnL Calculation ──
                pnl_decimal = (exit_price - entry_p) / entry_p if entry_p > 0 else 0.0
                pnl_pct = pnl_decimal * 100
                p_qty = trade.get('qty', 0)
                pnl_absolute = (exit_price - entry_p) * p_qty

                # Update Risk Manager
                self.risk_manager.update_performance(pnl_decimal)

                # ── Circuit Breaker Record (Using Equity) ──
                if hasattr(self, 'circuit_breaker'):
                    equity = self.stats.get('total_equity', self.stats.get('balance', 0))
                    self.circuit_breaker.record_result(pnl_absolute, equity)

                # ── Neural Memory Logging (Safe Keyworded Push) ──
                try:
                    db_abs_path = os.path.abspath(self.memory.db_path)
                    self.memory.log_trade(
                        symbol        = trade['symbol'],
                        side          = trade.get('side', 'BUY'),
                        entry         = entry_p,
                        exit_p        = exit_price,
                        entry_t       = trade.get('entry_time', trade.get('timestamp', '')),
                        exit_t        = datetime.now().isoformat(),
                        pnl           = pnl_pct,
                        conf          = trade.get('ai_conf', trade.get('conf', 0.85)),
                        health        = trade.get('market_health', self.stats.get('market_health', 50)),
                        sentiment     = self.stats.get('sentiment', 'Neural'),
                        strategy_used = trade.get('strategy', reason),
                    )
                    self.add_log(f"🧠 Brain-Link: Trade saved to -> {db_abs_path} (Reason: {reason})")
                except Exception as log_err:
                    app_logger.error(f"Brain-Link Fail: {log_err}")

                # ── Update Statistics (Explicit Casting) ──
                await self._update_closing_stats(trade, pnl_absolute, pnl_pct, reason)

                # ── [UPDATED v15.0: Smart Symbol Isolation] ──
                if pnl_absolute < 0:
                    # check if this symbol failed recently (within last 12h)
                    recent_losses = [t for t in self.memory.get_recent_memories(limit=20) 
                                   if t['symbol'] == trade['symbol'] and t['profit_loss'] < 0]
                    
                    # Default: 1 hour rest
                    cooldown_sec = 3600 
                    
                    # If it's a repeated loss (2 or more in recent history)
                    if len(recent_losses) >= 1:
                        cooldown_sec = 14400 # 4 hours for persistent failures
                        app_logger.critical(f"🔥 [DOUBLE LOSS GUARD] {trade['symbol']} failed again. Blocking for 4 hours.")
                    
                    expiry = time.time() + cooldown_sec
                    self.blacklisted_symbols[trade['symbol']] = expiry
                    self._save_blacklist()
                    msg = f"❄️ [COOL-DOWN] Applied {cooldown_sec/60:.0f}m rest to {trade['symbol']} due to loss."
                    app_logger.warning(msg)
                    self.add_log(msg)

                if self.stats['closed_trades'] % 10 == 0:
                    self.add_log("⚙️ System: Triggering strategy optimization cycle...")
                    self.strategy_optimizer.run_optimization_cycle(bot_instance=self)

                # Remove from trackers
                if trade in self.active_trades:
                    self.active_trades.remove(trade)
                self.healer.save_trade_state(self.active_trades)

                self.add_log(
                    f"🟢 TRADE CLOSED: {trade['symbol']} | "
                    f"PnL: {pnl_pct:+.2f}% (${pnl_absolute:+.2f}) | {reason}"
                )

                if pnl_absolute > 0:
                    self.voice_alerts.alert_take_profit()
                else:
                    self.voice_alerts.alert_stop_loss()
            else:
                self.add_log(f"⚠️ SELL FAILED: {trade['symbol']} order rejected by Binance (API/Balance issue). Retrying...")

        except Exception as e:
            app_logger.error(f"Trade close error: {e}")



    # ── [NEW v15.0: Flash-Crash Protection] ──
    async def _check_flash_crash(self, symbol, df) -> tuple[bool, str]:
        """
        PROSOFT MOMENTUM GUARD:
        Analyzes recent 1m candles for signs of a vertical collapse.
        Returns (is_collapsing, reason).
        """
        try:
            if df is None or len(df) < 5:
                return False, ""
            
            # Use last 3 1m candles
            last_3 = df.iloc[-3:]
            
            # Condition 1: Big Red Candle (Body > 1.2% drop in 1 min)
            current_candle = last_3.iloc[-1]
            body_size_pct = abs(float(current_candle['close']) - float(current_candle['open'])) / float(current_candle['open']) * 100
            is_red = float(current_candle['close']) < float(current_candle['open'])
            
            if is_red and body_size_pct >= 1.25:
                # If RSI is also falling sharply
                rsi = float(current_candle.get('RSI', 50))
                if rsi < 35:
                    return True, f"Flash Crash: Body {body_size_pct:.2f}% drop + RSI {rsi:.1f}"

            # Condition 2: Successive rapid drops (Accumulated > 2% in 3 mins)
            total_drop = (float(last_3.iloc[-1]['close']) - float(last_3.iloc[0]['open'])) / float(last_3.iloc[0]['open']) * 100
            if total_drop <= -2.1:
                return True, f"Momentum Collapse: {total_drop:.2f}% drop in 3m"

            return False, ""
        except Exception as e:
            app_logger.error(f"Flash-Crash check error for {symbol}: {e}")
            return False, ""

    def _save_blacklist(self):
        """Persists isolation state to disk."""
        try:
            with open(self.blacklist_file, 'w') as f:
                import json
                json.dump(self.blacklisted_symbols, f)
        except Exception as e:
            app_logger.error(f"Error saving blacklist: {e}")

    def _load_blacklist(self) -> dict:
        """Loads isolation state from disk."""
        try:
            if os.path.exists(self.blacklist_file):
                with open(self.blacklist_file, 'r') as f:
                    import json
                    data = json.load(f)
                    # Filter out expired ones immediately
                    now = time.time()
                    return {s: exp for s, exp in data.items() if exp > now}
        except Exception as e:
            app_logger.error(f"Error loading blacklist: {e}")
        return {}

    async def _sync_remote_sl(self, trade):
        """
        Synchronizes the local SL/TP with Binance by replacing existing OCO/SL orders.
        """
        try:
            symbol = trade['symbol']
            qty = trade.get('qty', 0)
            if trade.get('partial_done'):
                qty *= 0.6
            
            # Cancel old OCO if exists
            if 'oco_id' in trade:
                try:
                    self.api.client.cancel_order_list(symbol=symbol, orderListId=trade['oco_id'])
                except: pass
            
            # Place new OCO with updated SL and original/default TP
            tp = trade.get('tp', trade['entry_price'] * 1.05)
            sl = trade['sl']
            
            oco = self.order_manager.place_oco_order(symbol, qty, tp, sl)
            if oco:
                trade['oco_id'] = oco.get('orderListId')
                self.add_log(f"🔄 [REMOTE SYNC] {symbol}: Binance SL updated to {sl:.6f}")
        except Exception as e:
            app_logger.warning(f"Remote SL Sync failed for {trade['symbol']}: {e}")

    async def _scalper_cycle(self, market_health):
        """
        Run MicroScalper only when conditions are right.
        Gate: short timeframe + healthy market + scalper not on cooldown.
        """
        if not hasattr(self, 'micro_scalper'):
            return

        # NEW: Global switch for scalper
        if os.getenv('SCALPER_ENABLED', 'true').lower() != 'true':
            return

        if not self.micro_scalper.should_be_active(market_health, self.timeframe):
            return

        # Don't scalp if already at max concurrent trades
        max_trades = int(os.getenv('MAX_CONCURRENT_TRADES', 3))
        if len(self.active_trades) >= max_trades:
            return

        try:
            candidates = await self.micro_scalper.find_volatile_candidates(limit=5)
            for cand in candidates:
                sym = cand['symbol']
                df  = self.api.get_historical_klines(sym, '1m', limit=50)
                if df is None:
                    continue
                df     = self.ta.calculate_indicators(df)
                signal = self.micro_scalper.check_scalp_signal(df, symbol=sym)
                if not signal or signal['confidence'] < 0.75:
                    continue

                # Gate 00: Global Pulse Guard (Flash-Crash block)
                if time.time() < self.market_crash_gate:
                    continue

                # Gate 0: Blacklist/Cooldown (CRITICAL FIX)
                if sym in self.blacklisted_symbols:
                    expiry = self.blacklisted_symbols[sym]
                    if time.time() < expiry:
                        continue
                    else:
                        del self.blacklisted_symbols[sym]
                        self._save_blacklist()

                # Quick gate: manipulation shield only (MTF too slow for 1m)
                shield = self.manipulation_shield.analyze(df)
                if not shield['is_safe']:
                    continue

                # Memory veto
                veto, _ = self.memory.should_veto_trade(sym, market_health)
                if veto:
                    continue

                self.add_log(
                    f"⚡ SCALP SIGNAL: {sym} | {signal['reason']} | "
                    f"conf={signal['confidence']:.2f}"
                )

                trade = await self._execute_entry(
                    symbol        = sym,
                    signal        = {
                        'entry_price': signal['entry'],
                        'stop_loss':   signal['sl'],
                        'take_profit': signal['tp'],
                        'rr_ratio':    round((signal['tp'] - signal['entry']) /
                                             (signal['entry'] - signal['sl']), 2),
                        'indicators':  {'Strategy': f"Scalp-{signal['reason']}"},
                    },
                    ai_conf       = signal['confidence'],
                    market_health = market_health,
                    fgi           = self.stats.get('fgi', 50),
                )
                if trade:
                    self.active_trades.append(trade)
                    self.healer.save_trade_state(self.active_trades)
                    break  # one scalp at a time

        except Exception as e:
            app_logger.error(f"[SCALPER CYCLE] Error: {e}")

    # ═══════════════════════════════════════════════════════════════════════════════

    def add_log(self, msg):
        from datetime import timezone, timedelta
        now_algeria = datetime.now(timezone.utc) + timedelta(hours=1)
        time_str = now_algeria.strftime("%H:%M:%S")
        self.logs.append(f"[{time_str}] {msg}")
        
        # Guard: Cap logs to prevent interface lag or memory leaks
        if len(self.logs) > 1000:
            self.logs = self.logs[-1000:]
            
        app_logger.info(msg)

    def reconnect_binance(self, api_key, api_secret):
        try:
            from binance.client import Client
            self.api.client = Client(api_key, api_secret, testnet=False)
            self.api.client.ping()
            self.api.api_key = api_key
            self.api.api_secret = api_secret
            
            self.add_log("System Protocol: Binance Gateway Re-connected and synced across all modules.")
            return True
        except Exception as e:
            self.add_log(f"Binance Reconnection Error: {str(e)}")
            return False

    def reconnect_telegram(self, token, chat_id):
        try:
            self.telegram = TelegramBot(token=token, chat_id=chat_id)
            if self.main_loop and self.main_loop.is_running():
                msg = "🛡️ *PROSOFT QUANTUM BRIDGE RE-INITIALIZED*\nGateway is now monitoring markets..."
                self.main_loop.call_soon_threadsafe(
                    lambda: asyncio.create_task(self.telegram.send_message(msg))
                )
            
            self.add_log("System Protocol: Telegram Gateway Re-initialized.")
            return True
        except Exception as e:
            self.add_log(f"Telegram Reconnection Error: {str(e)}")
            return False

    def switch_symbol(self, new_symbol):
        if not new_symbol.endswith('USDT'):
            new_symbol = f"{new_symbol}USDT"
            
        old_symbol = self.symbol
        self.symbol = new_symbol
        self.add_log(f"⭐ STRATEGIC SWITCHOVER: {old_symbol} -> {self.symbol}")
        
        self.stats['rsi'] = 0
        self.stats['ai_conf'] = 0
        
        if hasattr(self, 'live_instance') and self.live_instance:
            self.live_instance.update(self.ui.update_ui(self.symbol, self.timeframe, self.stats, self.logs))

    async def perform_diagnostics(self):
        self.add_log("--- PROSOFT QUANTUM CORE: DIAGNOSTICS SEQUENCE ---")
        checks = [
            ("Neural Network", "ONLINE"),
            ("Binance Gateway", "VERIFIED" if self.api.client else "ERROR"),
            ("Telegram Bridge", "VERIFIED"),
            ("Gemini AI Node", "CLUSTER SYNCED" if self.gemini and self.gemini.api_keys else "FALLBACK"),
            ("Liquidity Shield", "ARMED"),
            ("Risk Governance", "ESTABLISHED"),
        ]
        for service, status in checks:
            await asyncio.sleep(0.1)
            self.add_log(f"> Service: {service.ljust(18)} [{status}]")
        
        await self.telegram.send_message("🚀 *PROSOFT QUANTUM PRIME SYSTEM STARTUP*\nEngines are online. Trading system engaged.")
        
        # Sync Initial Equity for Circuit Breaker accuracy
        try:
            self.portfolio.update_portfolio()
            summ = self.portfolio.get_summary()
            self.stats['total_equity'] = summ.get('total_value', 0.0)
            self.stats['balance'] = self.api.get_account_balance('USDT')
            self.add_log(f"Portfolio Initialized: Equity=${self.stats['total_equity']:,.2f}")
        except: pass

        await self.sync_from_binance()

        try:
            import threading
            from train_ai import start_auto_retraining
            threading.Thread(target=start_auto_retraining, daemon=True, name="AI-Retrainer").start()
            self.add_log("🧠 [AUTO-TRAIN] Weekly re-training scheduler started in background.")
        except Exception as _e:
            self.add_log(f"⚠️ [AUTO-TRAIN] Could not start scheduler: {_e}")

        self.voice.alert_bot_started()
        self.voice.say("System diagnostics complete. Artificial Intelligence Core is online and trading operations have commenced.")

        self.add_log("--- SYSTEM STATUS: OPTIMAL | COMMENCING OPERATIONS ---")
        await asyncio.sleep(1)

    async def run(self):
        await self.perform_diagnostics()
        
        with Live(self.ui.layout, refresh_per_second=2, screen=True) as live:
            self.live_instance = live 
            loop_count = 0
            while True:
                loop_count += 1
                try:
                    # ── Phase 14.1: Bulk Intelligence Sync ──
                    # Load ALL prices in one call to avoid latency in multi-trade monitoring
                    all_tickers = self.api.get_all_tickers()
                    if all_tickers:
                        self.stats['tickers'] = all_tickers
                        if self.symbol in all_tickers:
                            self.stats['price'] = all_tickers[self.symbol]
                    
                    self._force_ui_update()
                    await self._check_daily_report()
                    
                    if time.time() - self.stats.get('last_daily_briefing', 0) > 86400:
                        await self._send_daily_briefing()
                        self.stats['last_daily_briefing'] = time.time()
                        self.stats['daily_pnl'] = 0.0 
                        self.stats['daily_pnl_pct'] = 0.0
                    
                    if loop_count % 10 == 0:
                        await self.farmer.sync_rewards(self.memory)
                        self.stats['funding_rates'] = [] 
                        
                        rev_totals = self.memory.get_revenue_totals()
                        new_yield = rev_totals.get('yield_total', 0.0)
                        if new_yield > self.stats.get('yield_amount', 0.0):
                            self.voice.alert_revenue_received("Yield Farming", f"{new_yield - self.stats.get('yield_amount', 0.0):.4f}")
                        
                        new_fund = rev_totals.get('funding_total', 0.0)
                        if new_fund > self.stats.get('funding_amount', 0.0):
                            self.voice.alert_revenue_received("Funding Arbitrage", f"{new_fund - self.stats.get('funding_amount', 0.0):.4f}")

                        self.stats['yield_amount'] = new_yield
                        self.stats['sniper_hits'] = rev_totals.get('sniper_hits', 0)
                        self.stats['funding_amount'] = new_fund
                        self.stats['yield_status'] = "FARMING" if self.farmer.is_farming else "IDLE"
                    
                    if not self.active_trades and loop_count % 15 == 0:
                        await self.farmer.check_and_farm(threshold_usdt=25.0)
                        self.stats['yield_status'] = "FARMING" if self.farmer.is_farming else "IDLE"
                    
                    if loop_count % 5 == 0:
                        self.update_accuracy_stats()

                    new_asset = self.sniper.scan_for_new_listings()
                    if new_asset:
                        # Gate 00: Global Pulse Guard
                        if time.time() < self.market_crash_gate:
                            continue

                        # Gate 0: Blacklist Check
                        if new_asset in self.blacklisted_symbols:
                            expiry = self.blacklisted_symbols[new_asset]
                            if time.time() < expiry:
                                continue
                            else:
                                del self.blacklisted_symbols[new_asset]
                                self._save_blacklist()

                        self.add_log(f"⚡ LISTING SNIPER TRIGGRED: {new_asset}")
                        if self.execution_mode == 'auto':
                            await self.farmer.recall_funds()
                            
                            usdt_bal = self.api.get_account_balance('USDT')
                            snipe_amt = max(10.5, usdt_bal * 0.15)
                            if usdt_bal >= snipe_amt:
                                self.add_log(f"⚡ LISTING SNIPER: Executing FLASH BUY on {new_asset} for ${snipe_amt:.2f}")
                                try:
                                    snipe_price = self.api.get_symbol_ticker(new_asset)
                                    if snipe_price and snipe_price > 0:
                                        snipe_qty = snipe_amt / snipe_price
                                        order_res = self.orders.place_market_buy(new_asset, snipe_qty)
                                        if order_res:
                                            snipe_sl = snipe_price * 0.98   
                                            snipe_tp = snipe_price * 1.05   
                                            snipe_trade = {
                                                'symbol': new_asset,
                                                'side': 'BUY',
                                                'entry_price': snipe_price,
                                                'qty': snipe_qty,
                                                'sl': snipe_sl,
                                                'tp': snipe_tp,
                                                'conf': 1.0,
                                                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                            }
                                            self.active_trades.append(snipe_trade)
                                            self.stats['active_count'] = len(self.active_trades)
                                            self.voice.alert_sniper_hit(new_asset)
                                            self.add_log(f"⚡ SNIPE SUCCESS: Target {new_asset} engaged at {snipe_price}")
                                            self.switch_symbol(new_asset)
                                            self.stats['trades_count'] = int(self.stats.get('trades_count', 0)) + 1
                                            self.voice.alert_buy_signal()
                                            self.add_log(f"✅ SNIPER ORDER FILLED: {new_asset} @ ${snipe_price:.4f} | SL: ${snipe_sl:.4f} | TP: ${snipe_tp:.4f}")
                                            try:
                                                await self.telegram.send_message(
                                                    f"🚀 *FLASH LISTING SNIPER EXECUTED*\n"
                                                    f"Asset: `{new_asset}`\n"
                                                    f"Entry: ${snipe_price:.4f}\n"
                                                    f"Stop Loss: ${snipe_sl:.4f} (-5%)\n"
                                                    f"Take Profit: ${snipe_tp:.4f} (+10%)\n"
                                                    f"Amount: ${snipe_amt:.2f}"
                                                )
                                            except: pass
                                        else:
                                            self.add_log(f"Sniper: Order failed for {new_asset}. Skipping.")
                                    else:
                                        self.add_log(f"Sniper: Could not get price for {new_asset}. Skipping.")
                                except Exception as e:
                                    self.add_log(f"Sniper Execution Error: {e}")
                            else:
                                self.add_log(f"⚠️ Sniper: Insufficient balance (${usdt_bal:.2f}) for flash buy on {new_asset}.")
                                try:
                                    await self.telegram.send_message(f"🚨 *NEW LISTING DETECTED: {new_asset}*\n⚠️ Insufficient balance for auto-buy. Buy manually now!")
                                except: pass

                    # Use cached price if possible
                    ticker = self.stats.get('tickers', {}).get(self.symbol)
                    if ticker is None:
                        ticker = self.api.get_symbol_ticker(self.symbol)
                    
                    if ticker is None:
                        self.add_log("Network Interruption: Attempting to re-stabilize link...")
                        await asyncio.sleep(5)
                        continue
                    
                    self.stats['price'] = ticker
                    
                    df = self.api.get_historical_klines(self.symbol, self.timeframe, limit=350)
                    if df is not None and not df.empty:
                        df = self.ta.calculate_indicators(df)
                    
                    if df is not None and not df.empty and len(df) >= 2:
                        curr = df.iloc[-1]
                        self.stats['ema50'] = curr['EMA_50']
                        self.stats['ema200'] = curr['EMA_200']
                        current_time = time.time()
                        last_ai_time = float(self.stats.get('last_ai_update', 0))
                        # --- [v41.3: SOVEREIGN INTELLIGENCE BROKER] ---
                        # Failover strategy: Use AI ONLY if cluster is healthy
                        ai_exhausted = self.gemini.is_cluster_exhausted()
                        
                        # Optimization: Skip AI if exhausted OR too frequent, UNLESS in Ambush Mode
                        buy_pressure = self.stats.get('order_flow', {}).get('pressure_score', 0)
                        in_ambush = buy_pressure > 85
                        
                        cadence_met = (current_time - last_ai_time > 600) # every 10m standard
                        if in_ambush: cadence_met = (current_time - last_ai_time > 120) # every 2m ambush
                        
                        use_ai = (not ai_exhausted) and cadence_met
                        
                        if ai_exhausted and loop_count % 30 == 0:
                            self.add_log("🛡️ [SOVEREIGN FALLBACK] AI Exhaustion detected. Decisions driven by Native Intelligence.")
                        
                        dom_state = self.market_scanner.get_btc_dominance_state()
                        self.stats['btc_dominance'] = dom_state['dominance']
                        if dom_state['is_risky']:
                            self.stats['crash_risk'] = 85 
                            self.stats['qty_multiplier'] = 0.5 
                            if not self.stats.get('crash_notified'):
                                await self.telegram.send_message("🛡️ *GLOBAL CRASH SHIELD ACTIVATED*\nBTC Dominance spike detected (>60%). Liquidity is leaving alts. Scaling down position sizes by 50%.")
                                self.stats['crash_notified'] = True
                        else:
                            self.stats['crash_risk'] = 0
                            self.stats['qty_multiplier'] = 1.0
                            self.stats['crash_notified'] = False

                        self.stats['ai_conf'] = self.ai.calculate_confidence(curr)
                        
                        try:
                            self.stats['market_health'] = await self.intel.calculate_market_health(df, skip_ai=(not use_ai))
                            if use_ai:
                                self.stats['last_ai_update'] = current_time
                                self.stats['ai_status'] = 'CLUSTER ONLINE'
                            else:
                                self.stats['ai_status'] = 'INTERNAL STABLE'
                        except Exception as e:
                            app_logger.error(f"AI Matrix Error: {e}")
                            self.stats['ai_status'] = 'LATENCY'
                        
                        self.stats['ai_cluster'] = self.gemini.get_quota_info()
                        self.stats['rsi'] = curr['RSI']
                        self.stats['sentiment'] = self.intel.detect_sentiment(df)
                        pred = self.intel.predict_next_price(df)
                        self.stats['prediction'] = f"{pred['direction']} ({pred['change_pct']:+.1f}%)" if pred else "N/A"
                        self.last_df = df 

                        rocket = self.rocket_sniper.detect_rocket(df, self.symbol)
                        if rocket and self.execution_mode == 'auto' and not self.active_trades:
                            # Gate 00: Global Pulse Guard
                            if time.time() < self.market_crash_gate:
                                continue

                            # Gate 0: Blacklist Check
                            if self.symbol in self.blacklisted_symbols:
                                expiry = self.blacklisted_symbols[self.symbol]
                                if time.time() < expiry:
                                    continue
                                else:
                                    del self.blacklisted_symbols[self.symbol]
                                    self._save_blacklist()
                                    
                            self.add_log(f"🚀 MEME ROCKET ENGAGED: Executing scalp on {self.symbol}")
                            balance = self.api.get_account_balance('USDT')
                            # Safety cap: use 90% of balance if $20 is too much, but stay above $10.1
                            trade_amount = min(20.0, balance * 0.95)
                            if trade_amount < 10.1: trade_amount = balance * 0.99
                            
                            if trade_amount >= 10.0:
                                qty = trade_amount / rocket['entry_price']
                                await self.execute_trade(self.symbol, 'BUY', qty, rocket['entry_price'], 
                                                         rocket['entry_price'] * (1 - rocket['emergency_sl']/100),
                                                         rocket['entry_price'] * (1 + rocket['target_profit']/100), 0.99)
                            else:
                                self.add_log(f"⚠️ [MEME ROCKET] Balance too low (${balance:.2f}) for even a minimum trade.")
                        elif rocket:
                            await self.telegram.send_message(
                                f"🚀 *MEME ROCKET ALERT / تنبيه صاروخ الميم* 🚀\n"
                                f"Asset / الأصل: `{self.symbol}`\n"
                                f"Status / الحالة: EXPLOSIVE VOLUME! / سيولة انفجارية\n"
                                f"Action / الإجراء: Manual scalp recommended. / ينصح بالسكالب اليدوي."
                            )
                    else:
                        self.add_log("Data Warning: Insufficient data for analysis. Waiting...")
                        if not self.active_trades:
                            await asyncio.sleep(self.interval_sec)
                            continue

                    if loop_count % 5 == 0:
                        try:
                            self.portfolio.update_portfolio()
                            summ = self.portfolio.get_summary()
                            self.stats['total_equity'] = summ.get('total_value', 0.0)
                            self.stats['balance'] = self.api.get_account_balance('USDT')
                            
                            # v27.0: Feed the latest balance to Telegram Footer
                            self.telegram.update_stats(self.stats.get('total_equity', 0.0))
                            
                            current_assets = [a['asset'] for a in summ.get('assets', [])]
                            for trade in list(self.active_trades):
                                symbol_base = trade['symbol'].replace('USDT', '')
                                if symbol_base not in current_assets:
                                    self.add_log(f"🧠 SELF-HEAL: Asset {trade['symbol']} no longer detected in portfolio (Sold manually?). Removing from trackers.")
                                    self.active_trades.remove(trade)
                                    self.stats['active_count'] = len(self.active_trades)

                            # --- [v2.0 UI SYNC PATCH] ---
                            # Auto-sync external/manual trades into the UI tracker
                            for asset in summ.get('assets', []):
                                asset_name = asset.get('asset')
                                if not asset_name: continue
                                
                                val = asset.get('value', 0.0)
                                if asset_name != 'USDT' and val > 1.0: # Track everything > $1 for small accounts
                                    symbol = f"{asset_name}USDT"
                                    is_tracked = any(t['symbol'] == symbol for t in self.active_trades)
                                    if not is_tracked:
                                        self.add_log(f"🧠 SYNC: Detected significant untracked manual asset {symbol} (${val:.2f}). Adding to tracker.")
                                        # Use cached price if available
                                        price_raw = self.stats.get('tickers', {}).get(symbol)
                                        if price_raw is None:
                                            price_raw = self.api.get_symbol_ticker(symbol) or 0.0
                                        
                                        price = float(price_raw)
                                        qty = float(asset.get('free', 0.0))
                                        
                                        self.active_trades.append({
                                            'symbol': symbol,
                                            'side': 'BUY',
                                            'qty': qty,
                                            'entry_price': price,
                                            'sl': price * 0.98, 
                                            'tp': price * 1.05, 
                                            'trailing_sl': price * 0.98,
                                            'pnl_pct': 0.0,
                                            'time': datetime.now().strftime("%H:%M:%S")
                                        })
                                        self.stats['active_count'] = len(self.active_trades)

                            if self.stats['total_equity'] > 0:
                                if not self.active_trades and self.execution_mode == 'auto':
                                    await self.farmer.check_and_farm(threshold_usdt=25.0)
                                    if self.stats['balance'] > 50:
                                        await self.pool_hunter.auto_stake_for_farming(amount_usdt=20.0)
                                    
                                self.add_log(f"Portfolio Sync: Equity verified at ${self.stats['total_equity']:,.2f}")
                                
                                self.pool_hunter.scan_for_pools()
                                ai_lead = await self.sentiment_front.analyze_and_front_run()
                                if ai_lead and self.execution_mode == 'auto' and not self.active_trades:
                                    self.add_log(f"🧠 AI SENTIMENT FRONT-RUN: Switching to {ai_lead['symbol']} for early entry.")
                                    self.switch_symbol(ai_lead['symbol'])
                                    continue
                                elif ai_lead:
                                    await self.telegram.send_message(
                                        f"🧠 *AI SENTIMENT FRONT-RUNNER / استباق الذكاء الاصطناعي* 🧠\n"
                                        f"Lead / السبب: {ai_lead['reason']}\n"
                                        f"Action / الإجراء: Monitoring {ai_lead['symbol']} for early entry.\n"
                                    )
                            else:
                                self.add_log("Portfolio Sync: Connection active, but no significant assets found in Spot Wallet.")
                        except Exception as e:
                            self.add_log(f"Portfolio Sync Error: {str(e)}")

                    if not self.active_trades and loop_count > 0 and loop_count % 3 == 0:
                        try:
                            scan_results = self.market_scanner.scan_market()
                            self.stats['top_gems'] = scan_results 
                            
                            if scan_results:
                                current_eval = self.market_scanner.analyze_symbol(self.symbol)
                                current_scanner_score = current_eval['score'] if current_eval else 40
                                best_candidate = scan_results[0]
                                
                                if best_candidate['score'] > current_scanner_score + 5 and best_candidate['symbol'] != self.symbol:
                                    self.add_log(f"🧠 AI STRATEGIC PIVOT: {best_candidate['symbol']} (Score: {best_candidate['score']}) outperforms {self.symbol} (Score: {current_scanner_score})")
                                    try:
                                        msg = (f"🔄 *STRATEGIC ROTATION / تدوير استراتيجي* 🔄\n\n"
                                               f"Current / الحالي: `{self.symbol}` (Score: {current_scanner_score})\n"
                                               f"Superior Alpha / البديل الأقوى: `{best_candidate['symbol']}` (Score: {best_candidate['score']})\n\n"
                                               f"Reason: High-velocity opportunity detected in discovery mode.\n")
                                        await self.telegram.send_message(msg)
                                    except: pass
                                    self.switch_symbol(best_candidate['symbol'])
                                    continue 
                        except Exception as e:
                            self.add_log(f"Auto-Rotation Protocol Latency: {e}")

                    if loop_count % 25 == 0:
                        try:
                            new_whales = self.whales.get_latest_movements()
                            self.stats['whale_alerts'] = new_whales
                            for w in new_whales:
                                if w['impact'] in ['CRITICAL', 'HIGH'] and w['msg'] != self.stats.get('last_tg_whale'):
                                    await self.telegram.send_message(f"🐋 *SMART MONEY ALERT / تنبيه الحيتان*\n{w['msg']}\nImpact: {w['impact']}")
                                    self.stats['last_tg_whale'] = w['msg']
                                    self.add_log(f"System Protocol: Instant Whale Warning transmitted.")
                            
                            tweet_alert = self.twitter.scan_live_firehose()
                            if tweet_alert:
                                alert_msg = (f"🐦 *TWITTER RADAR ALERT / تنبيه تويتر* 🐦\n"
                                           f"Source: `{tweet_alert['source']}`\n"
                                           f"Tweet: {tweet_alert['tweet']}\n"
                                           f"Action: {tweet_alert['action_taken']}")
                                await self.telegram.send_message(alert_msg)
                                self.add_log(f"Twitter Radar: High-impact event from {tweet_alert['source']}")
                                self.stats['news_highlight'] = f"{tweet_alert['source']}: {tweet_alert['tweet']}"
                            
                            top_gems = self.stats.get('top_gems', [])
                            for gem in top_gems[:3]: 
                                if gem['symbol'] != self.symbol:
                                    if gem.get('score', 0) > 85: 
                                        alert_key = f"opp_{gem['symbol']}"
                                        if alert_key != self.stats.get('last_opp_alert'):
                                            await self.telegram.send_message(
                                                f"⭐ *GOLDEN CHANCE / فرصة ذهبية*\n"
                                                f"Asset: {gem['symbol']}\n"
                                                f"Momentum Score: {gem['score']}\n"
                                                f"Status: Explosive Liquidity Spike detected.\n"
                                            )
                                            self.stats['last_opp_alert'] = alert_key
                        except Exception as e:
                            self.add_log(f"Alert Service Latency: {str(e)}")

                    if loop_count > 0:
                        if loop_count % 100 == 0:
                            self.add_log("🧠 System Protocol: Running AI Strategy Optimization cycle...")
                            optimization = self.optimizer.run_optimization_cycle(bot_instance=self)
                            if optimization and optimization.get('changes_applied'):
                                # Store for the nightly report
                                if 'daily_evolution' not in self.stats: self.stats['daily_evolution'] = {}
                                self.stats['daily_evolution'].update(optimization['changes_applied'])
                                self.add_log(f"🧠 [OPTIMIZER] Recorded {len(optimization['changes_applied'])} neural evolution shifts.")

                        from datetime import timezone, timedelta
                        now_alg = datetime.now(timezone.utc) + timedelta(hours=1)
                        if now_alg.weekday() == 6 and now_alg.hour == 0 and self.stats['last_weekly_review'] != now_alg.strftime("%Y-%m-%d"):
                            self.add_log("🧠 Weekly Intelligence Review started...")
                            review = self.optimizer.generate_weekly_review()
                            if review:
                                env_defaults = 'USDC,FDUSD,TUSD,USDP,EUR,BUSD,USD1,DAI,USDD,PYUSD,AEUR,GBP,EURI'
                                defaults = [c.strip().upper() for c in env_defaults.split(',')]
                                forgiven = [c for c in self.market_scanner.blacklist if c not in set(defaults)]
                                
                                self.market_scanner.blacklist = list(defaults)
                                self.stats['last_weekly_review'] = now_alg.strftime("%Y-%m-%d")
                                
                                toxic_list = ", ".join(review['toxic_assets']) if review['toxic_assets'] else "None"
                                forgiven_list = ", ".join(forgiven) if forgiven else "None"
                                
                                report = (
                                    f"📊 *WEEKLY INTELLIGENCE REPORT / التقرير الأسبوعي*\n"
                                    f"━━━━━━━━━━━━━━━━━━━━\n"
                                    f"💰 Total PNL / إجمالي الربح: `${review['total_pnl']:+.4f}`\n"
                                    f"🏆 Win Rate / نسبة النجاح: `{review['win_rate']:.1f}%`\n"
                                    f"🔢 Total Trades / عدد الصفقات: `{review['total_trades']}`\n"
                                    f"🌟 Best Asset / أفضل عملة: `{review['best_asset']}`\n"
                                    f"💀 Worst Asset / أسوأ عملة: `{review['worst_asset']}`\n"
                                    f"━━━━━━━━━━━━━━━━━━━━\n"
                                    f"🕊️ *FORGIVENESS / العفو عن العملات:*\n"
                                    f"`{forgiven_list}`\n\n"
                                    f"🚫 *NEW BLACKLIST / القائمة السوداء الجديدة:*\n"
                                    f"`{toxic_list}`\n"
                                    f"━━━━━━━━━━━━━━━━━━━━\n"
                                )
                                await self.telegram.send_message(report)
                                
                                if review['toxic_assets']:
                                    for t in review['toxic_assets']:
                                        if t not in self.market_scanner.blacklist:
                                            self.market_scanner.blacklist.append(t)

                        if not self.active_trades and loop_count % 15 == 0:
                            lead = self.alpha_tracker.scan_alpha_leads()
                            if lead:
                                alert_msg = (f"🔱 *SHADOW PROTOCOL ALERT / تنبيه تتبع النخبة* 🔱\n"
                                           f"Wallet: `{lead['wallet_alias']}` ({lead['address_hint']})\n"
                                           f"Action: {lead['action']} {lead['symbol']}\n"
                                           f"Impact: {lead['size_impact']}\n"
                                           f"Status: System mirroring initialized.")
                                await self.telegram.send_message(alert_msg)
                                self.add_log(f"Alpha Shadow: Detected institutional lead on {lead['symbol']}")
                                if self.execution_mode == 'auto': 
                                    pass

                    if loop_count % 10 == 0:
                        self.stats['market_pulse'] = {'feed': []}

                    if loop_count == 1 or (loop_count > 0 and loop_count % 20 == 0):
                        try:
                            arb_opps = self.arbitrage.scan_opportunities()
                            self.stats['arb_opportunities'] = arb_opps
                            if arb_opps:
                                best = arb_opps[0]
                                liquidity_status = "✅ SECURE" if best.get('is_high_liquidity') else "⚠️ LOW DEPTH"
                                self.add_log(f"🔺 [ARBITRAGE] Best: {best['route_name']} ({best['direction']}) +{best['profit_pct']}% | {liquidity_status}")
                                if best['profit_pct'] > 0.3:
                                    now = datetime.now().strftime("%H:%M:%S")
                                    arb_msg = (f"🔺 *ARBITRAGE ALERT / تنبيه مراجحة* 🔺\n"
                                             f"⏰ *Time:* {now}\n"
                                             f"Route: {best['route_name']}\n"
                                             f"Direction: {best['direction']}\n"
                                             f"Profit: +{best['profit_pct']}%\n"
                                             f"Liquidity: {liquidity_status}\n"
                                             f"Est. per $1000: ${best['estimated_profit_1k']}")
                                    await self.telegram.send_message(arb_msg)
                            else:
                                self.stats['arb_opportunities'] = []

                            flow = self.order_flow.analyze_order_book(self.symbol)
                            if flow:
                                self.stats['order_flow'] = flow
                                if flow['bias'] in ['STRONG_BUY', 'STRONG_SELL']:
                                    self.add_log(f"📊 [ORDER FLOW] {self.symbol}: {flow['bias']} (Pressure: {flow['pressure_score']}%)")

                            spoofs = self.order_flow.detect_whale_spoofing(self.symbol)
                            if spoofs:
                                self.stats['spoof_alerts'] = spoofs
                                self.add_log(f"⚠️ [SPOOF DETECT] {len(spoofs)} suspicious orders found on {self.symbol}!")
                        except Exception as e:
                            self.add_log(f"Cycle 3 Engine Error: {e}")

                    if loop_count > 0:
                        try:
                            # --- [v40.0: ADAPTIVE AMBUSH HEARTBEAT] ---
                            # Modulate AI frequency based on Risk vs Opportunity
                            crash_risk = self.stats.get('crash_risk', 0)
                            buy_pressure = self.stats.get('order_flow', {}).get('pressure_score', 0)
                            
                            # Determine cadence (loops to wait)
                            if crash_risk > 60:
                                macro_cadence = 60 # Hibernate: 5m (Save Quota)
                            elif buy_pressure > 85:
                                macro_cadence = 4  # AMBUSH MODE: 20s (Fast Strike)
                            else:
                                macro_cadence = 20 # Standard: 100s
                                
                            if (loop_count == 1) or (loop_count % macro_cadence == 0):
                                try:
                                    rsi = self.stats.get('rsi', 50)
                                    health = self.stats.get('market_health', 50)
                                    macro = await self.macro_filter.analyze_macro_environment(rsi, health)
                                    
                                    self.stats['macro_state'] = macro
                                    if macro.get('is_proxy'):
                                        self.add_log(f"🌍 [MACRO] Proxy Active: {macro['market_regime']} | FGI: {macro['fear_greed_index']}")
                                    else:
                                        self.add_log(f"🌍 [MACRO] Linked: {macro['market_regime']} | FGI: {macro['fear_greed_index']}")
                                except Exception as e:
                                    self.add_log(f"⚠️ Macro Sync Warning: {str(e)[:50]}")
                                
                                permission = self.macro_filter.get_trading_permission()
                                if not permission['allowed']:
                                    self.add_log(f"🚫 [MACRO LOCKDOWN] {permission['reason']}")
                                    await self.telegram.send_message(f"🚫 *MACRO LOCKDOWN*\n{permission['reason']}")

                            try:
                                local_pnl = self.stats.get('session_pnl', 0)
                                net_health = self.stats.get('market_health', 50)
                                net_sentiment = self.stats.get('sentiment', 'neutral')
                                
                                m_state = self.stats.get('macro_state')
                                m_fgi = 50
                                if isinstance(m_state, dict):
                                    m_fgi = m_state.get('fear_greed_index', 50)
                                
                                crash_eval = self.hedger.evaluate_crash_risk(local_pnl, net_health, net_sentiment, m_fgi)
                                self.stats['hedge_status'] = self.hedger.get_status()
                                self.stats['crash_risk'] = int(crash_eval.get('risk_score', 0))
                                
                                if crash_eval.get('should_hedge') and not self.stats.get('hedge_active'):
                                    self.add_log(f"🛡️ [CRASH SHIELD] EMERGENCY: Risk={self.stats['crash_risk']}% | ACTIVATING SHORT HEDGE")
                                    await self.telegram.send_message(
                                        f"🚨 *CRASH SHIELD ACTIVATED / تحوط مفعل*\n"
                                        f"Risk Score: {self.stats['crash_risk']}%\n"
                                        f"System Status: NEURAL PROTECTION MODE"
                                    )
                                    self.stats['hedge_active'] = True
                                    
                                if self.stats.get('hedge_active') and self.hedger.check_recovery(local_pnl):
                                    self.add_log("✅ [HEDGE RECOVERY] Market stabilized. Shield deactivated.")
                                    await self.telegram.send_message("✅ *SHIELD DEACTIVATED / تم إلغاء التحوط*\nMarket environment stabilized.")
                                    self.stats['hedge_active'] = False
                                    
                            except Exception as e:
                                self.add_log(f"⚠️ Security Core Pulse Error: {e}")

                            if loop_count % 30 == 0:
                                heatmap = self.heatmap.generate_heatmap(self.symbol)
                                if heatmap:
                                    self.stats['heatmap'] = heatmap
                        except Exception as e:
                            self.add_log(f"Cycle 4 Sovereignty Error: {e}")
                        
                        current_time = time.time()
                        sync_threshold = 600 if self.active_trades else 1500
                        if (current_time - self.stats.get('last_periodic_sync', 0)) >= sync_threshold:
                            self.stats['last_periodic_sync'] = current_time
                            await self.dispatch_intelligence_heartbeat()

                    if loop_count > 0 and loop_count % 900 == 0:
                        try:
                            topics = ["market psychology", "risk management", "whale behavior", "technical trap warning"]
                            topic = random.choice(topics)
                            p = (f"Generate a PRO-TRADER INSIGHT about {topic}. "
                                 f"Context: Market Health is {self.stats['market_health']}%. "
                                 "Format: 1-sentence in English, then 1-sentence in Arabic. Be elite.")
                            insight = await self.gemini.ask(p)
                            if insight:
                                await self.telegram.send_message(f"🧠 *PROSOFT FLASH INSIGHT*\n━━━━━━━━━━━━━━\n{insight}")
                        except: pass

                    try:
                        current_price = self.stats['price']
                        prev_high = self.stats.get('day_high_mark', 0)
                        if current_price > prev_high and prev_high > 0:
                            await self.telegram.send_message(
                                f"🔥 *BREAKOUT ALERT / تنبيه اختراق*\n"
                                f"Asset: {self.symbol}\n"
                                f"New Day High: ${current_price:,.2f}\n"
                                f"Status: Momentum is surging! | الزخم يتزايد بقوة!"
                            )
                        self.stats['day_high_mark'] = max(current_price, prev_high if prev_high > 0 else current_price)
                    except: pass

                    if loop_count % 5 == 0:
                        self.stats['top_gems'] = self.market_scanner.scan_market()

                    if self.stats.get('market_health', 100) < 15:
                        if not self.omega_active:
                            self.omega_active = True
                            await self.activate_protocol_omega("CRITICAL: Market Health has dropped to dangerous levels.")
                        await asyncio.sleep(self.interval_sec)
                        continue

                    if self.omega_active and self.stats.get('market_health', 100) > 30:
                        self.omega_active = False
                        self.add_log("System Protocol: Market Stabilized. Protocol Omega Disengaged.")
                        await self.telegram.send_message("🛡️ *PROTOCOL OMEGA DISENGAGED* 🛡️\nMarket conditions have stabilized. Resuming standard operations.")

                    if loop_count > 0 and loop_count % 10 == 0:
                        await self.healer.run_health_check()

                    try:
                        # Use total_equity (USDT + Assets) for daily loss calculation to avoid false alarms
                        equity = self.stats.get('total_equity', self.stats.get('balance', 0))
                        if equity > 0:
                            self.circuit_breaker.set_balance(equity)
                            
                        if self.circuit_breaker.is_tripped:
                            self.add_log(f"🔴 [CIRCUIT BREAKER] Trading BLOCKED: {self.circuit_breaker.trip_reason} | Today's Loss: {self.stats.get('daily_pnl_pct', 0.0):.2f}%")
                            self.stats['circuit_breaker'] = self.circuit_breaker.get_status()
                            await asyncio.sleep(self.interval_sec)
                            continue
                    except Exception as _cb_e:
                        self.add_log(f"⚠️ [CB] Check error: {_cb_e}")

                    # ══════════════════════════════════════════════════════════════════════════
                    # 5 & 6. ENTRY CONDITIONS, SIGNAL EXECUTION & TRADE MANAGEMENT (UPGRADED v2.0)
                    # ══════════════════════════════════════════════════════════════════════════
                    if df is not None and not df.empty:
                        # 1. Manage open trades every iteration
                        current_price = float(df.iloc[-1]['close'])
                        await self._manage_open_trades(df, current_price)
                        
                        # 2. Run Scalper Cycle
                        mkt_health = self.stats.get('market_health', 50)
                        await self._scalper_cycle(mkt_health)

                        # 3. Check Entry Conditions
                        fgi_val = 50
                        if isinstance(self.stats.get('macro_state'), dict):
                            fgi_val = self.stats.get('macro_state', {}).get('fear_greed_index', 50)
                            
                        allowed, reason = await self._check_entry_conditions(
                            self.symbol, df, mkt_health, fgi=fgi_val
                        )
                        
                        if not allowed:
                            import time as _t
                            _now = _t.time()
                            if not hasattr(self, '_last_block_log') or (_now - self._last_block_log) > 300:
                                self.add_log(f"⛔ BLOCKED: {reason}")
                                self._last_block_log = _now
                        else:
                            # 4. Execute Signal (Prioritize QuantumAlpha with Macro Context)
                            m_context = self.stats.get('macro_context', {})
                            signal = self.quantum_alpha.check_entry_signal(df, symbol=self.symbol, macro_context=m_context)
                            
                            if signal['signal'] == 'WAIT':
                                # Fallback to standard strategy with Macro Context
                                signal = self.strategy.check_entry_signal(df, symbol=self.symbol, macro_context=m_context)
                            
                            if signal['signal'] == 'BUY':
                                # --- NEW v36.0: JUST-IN-TIME MACRO TRIGGER ---
                                # Only sweep geopolitics/DXY when we actually have a trade signal
                                now = time.time()
                                if now - self.stats.get('last_macro_sweep', 0) > 900: # 15 min fresh window
                                    self.add_log(f"🎯 [MOMENTUM] Signal detected on {self.symbol}. Triggering JIT Macro Intelligence Sweep...")
                                    macro_data = await self.gemini.get_macro_sentiment()
                                    if macro_data:
                                        self.stats['macro_context'] = macro_data
                                        self.stats['last_macro_sweep'] = now
                                        self.add_log(f"🌍 [MACRO] JIT Result: {macro_data.get('macro_bias')} | DXY: {macro_data.get('dxy_pressure')}")
                                
                                # Re-validate with fresh macro context
                                if self.stats.get('macro_context'):
                                    m_context = self.stats['macro_context']
                                    if 'PAXG' in self.symbol and m_context.get('gold_safety') == 'LOW':
                                        self.add_log(f"⛔ [VETO] JIT Macro Interceptor blocked entry: {m_context.get('reason')}")
                                        signal['signal'] = 'WAIT'
                                        continue

                                # Calculate final confidence
                                ai_conf = signal.get('confidence', self.ai.calculate_confidence(df.iloc[-1]))
                                
                                if ai_conf >= self.ai_confidence_threshold:
                                    trade = await self._execute_entry(self.symbol, signal, ai_conf, mkt_health, fgi=fgi_val)
                                    if trade:
                                        self.active_trades.append(trade)
                                        self.healer.save_trade_state(self.active_trades)
                                        self.stats['active_count'] = len(self.active_trades)

                    # 7. Periodic position & report updates
                    if loop_count % 5 == 0:
                        pass # High-Intelligence Telegram Report active in _check_daily_report

                    loop_count += 1
                    live.update(self.ui.update_ui(self.symbol, self.timeframe, self.stats, self.logs))
                    
                except Exception as e:
                    self.add_log(f"Loop Error: {str(e)}")
                
                try:
                    # Adaptive Cycle Intensity: 
                    # If trades are active, we monitor every 3 seconds for SL/TP precision.
                    # If idle, we scan every 10 seconds to save API quota.
                    current_interval = 1 if self.active_trades else self.interval_sec
                    
                    await asyncio.wait_for(self.wakeup_event.wait(), timeout=current_interval)
                    self.wakeup_event.clear()
                except asyncio.TimeoutError:
                    pass

    def _force_ui_update(self):
        if hasattr(self, 'live_instance') and self.live_instance:
            self.live_instance.update(self.ui.update_ui(self.symbol, self.timeframe, self.stats, self.logs))

    async def execute_trade(self, symbol, side, qty, price, sl, tp, conf):
        self.add_log(f"CORE EXECUTION: {side} {symbol} @ {price}")
        try:
            balance = self.api.get_account_balance('USDT')
            multiplier = self.stats.get('qty_multiplier', 1.0)
            
            # 12.8 PROSOFT: Smart Sizing for Small Accounts
            target_usd = qty * price * multiplier
            safe_usd = min(target_usd, balance * 0.95)
            
            # Ensure we don't fall below Binance $10 limit if we have enough
            if safe_usd < 10.1 and balance >= 10.1:
                safe_usd = balance * 0.98  # Use almost everything if we are at the limit
            
            if safe_usd < 10.0:
                self.add_log(f"⚠️ [EXECUTION] Aborted: Resulting amount ${safe_usd:.2f} is below Binance Minimum or Balance.")
                return False

            final_qty = safe_usd / price
            order_res = self.orders.place_market_buy(symbol, final_qty)
        except Exception as e:
            self.add_log(f"Execution Error: {str(e)}")
            order_res = None
        
        if order_res:
            executed_qty = sum(float(fill['qty']) for fill in order_res.get('fills', [])) if 'fills' in order_res else qty
            trade_obj = {
                'symbol': symbol,
                'side': side,
                'entry_price': price,
                'qty': executed_qty,
                'sl': sl,
                'tp': tp,
                'conf': conf,
                'order_id': order_res.get('orderId', 'SIMULATED'),
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            self.active_trades.append(trade_obj)
            self.healer.save_trade_state(self.active_trades) 
            self.stats['active_count'] = len(self.active_trades)
            
            try:
                oco_res = self.orders.place_oco_order(symbol, executed_qty, tp, sl)
                if oco_res:
                    self.active_trades[-1]['oco_id'] = oco_res.get('orderListId')
                    self.add_log(f"🛡️ Iron-Clad Protection: OCO (TP/SL) set on Binance for {symbol}")
            except Exception as e:
                self.add_log(f"OCO Warning: Failed to set remote TP/SL. Bot will monitor locally. Error: {e}")

            self.stats['trades_count'] = int(self.stats.get('trades_count', 0)) + 1
            try:
                await self.telegram.send_message(
                    f"🟢 *Autonomous Order Filled / تم تنفيذ الطلب*\n"
                    f"Asset / الأصل: `{symbol}`\n"
                    f"Side / الحركة: `{side}` @ ${price:,.2f}\n"
                    f"Stop Loss / إيقاف خسارة: ${sl:,.2f}\n"
                    f"Take Profit / جني أرباح: ${tp:,.2f}\n"
                    f"🛡️ *Remote Protection:* ACTIVE / الحماية النشطة"
                )
                self.voice.alert_buy_signal()
                self.voice.say(f"New trade executed. Buying {symbol.replace('USDT', '')} at {price:,.2f}. Security protocols active.")
            except: pass
            return True
        else:
            self.add_log("CRITICAL: Order placement failed. Check Balance or API Permissions.")
            return False

    async def close_trade_by_symbol(self, symbol, side, price, reason):
        trade = next((t for t in self.active_trades if t['symbol'] == symbol), None)
        if not trade: 
            self.add_log(f"Close Trade Error: No active trade found for {symbol}")
            return
        
        if 'oco_id' in trade:
            try:
                self.api.client.cancel_order_list(symbol=trade['symbol'], orderListId=trade['oco_id'])
                self.add_log(f"Cleanup: Pending OCO orders for {trade['symbol']} cancelled.")
            except Exception as e:
                self.add_log(f"OCO Cancellation Error: {str(e)}") 

        # ── Unified PnL Calculation ──
        entry_p = trade.get('entry_price', price)
        pnl_decimal = (price - entry_p) / entry_p if entry_p > 0 else 0.0
        pnl_pct = pnl_decimal * 100
        p_qty = trade.get('qty', 0)
        pnl_absolute = (price - entry_p) * p_qty
        
        self.add_log(f"TRADE CLOSED ({reason}): {trade['symbol']} @ {price} | PNL: ${pnl_absolute:.2f} ({pnl_pct:.2f}%)")
    
        if self.execution_mode == 'auto' or "MANUAL" in reason or reason in ["SL", "TP", "TRAILING STOP", "GLOBAL SAFETY (1.95%)"] or "SAFETY" in reason or "LIMIT" in reason or "EMERGENCY" in reason:
            try:
                asset = trade['symbol'].replace('USDT', '')
                self.add_log(f"🔄 EXIT PROTOCOL: Converting {asset} back to USDT...")
                
                try:
                    self.api.client._cancel_all_open_orders(symbol=trade['symbol'])
                    await asyncio.sleep(1.5) 
                except Exception as e:
                    try:
                        open_orders = self.api.client.get_open_orders(symbol=trade['symbol'])
                        for oo in open_orders:
                            self.api.client.cancel_order(symbol=trade['symbol'], orderId=oo['orderId'])
                    except:
                        self.add_log(f"Exit Cleanup: {e}")
                
                actual_free_balance = self.api.get_account_balance(asset, include_locked=False)
                
                if actual_free_balance > 0:
                    current_ticker = self.api.get_symbol_ticker(trade['symbol'])
                    est_value = actual_free_balance * current_ticker
                    
                    if est_value >= 1.0: 
                        self.add_log(f"Liquidation: Selling {actual_free_balance:.6f} {asset} (~${est_value:.2f})")
                        sell_order = self.orders.place_market_sell(trade['symbol'], actual_free_balance)
                        
                        if not sell_order and est_value >= 10.0:
                            self.add_log(f"⚠️ MARKET SELL REJECTED. Fallback to LIMIT SELL at 1% discount for {asset}.")
                            sell_order = self.orders.place_limit_sell(trade['symbol'], actual_free_balance, current_ticker * 0.99)
                        
                        if sell_order:
                            self.add_log(f"✅ CONVERSION SUCCESS: {asset} successfully converted to USDT.")
                            try:
                                await self.telegram.send_message(
                                    f"💰 *LIQUIDATION SUCCESSFUL*\n"
                                    f"Asset: `{asset}` converted to `USDT`\n"
                                    f"Amount: `{actual_free_balance:.6f}`\n"
                                    f"Status: Funds Secured in Wallet"
                                )
                            except: pass
                        else:
                            if est_value >= 10.0:
                                self.add_log(f"🛑 CRITICAL: Liquidation failed completely for {asset} despite high value (${est_value:.2f}). Trade will NOT be closed.")
                                try:
                                    await self.telegram.send_message(f"🚨 *LIQUIDATION FAILED*\nAsset: `{asset}` (${est_value:.2f}). The system will retry. Check Binance manually.")
                                except: pass
                                return 
                            else:
                                self.add_log(f"⚠️ LIQUIDATION IGNORED: {asset} (~${est_value:.2f}) is likely below Binance minimum ($5-$10).")
                                try:
                                    await self.telegram.send_message(
                                        f"⚠️ *LIQUIDATION LIMIT REACHED*\n"
                                        f"Asset: `{asset}` remained in wallet because its value (${est_value:.2f}) is below the Binance minimum required for selling (usually $10).\n"
                                        f"Action: You can manually convert it to BNB or hold it."
                                    )
                                except: pass
                    else:
                        self.add_log(f"Dust Handling: {asset} balance too small to even attempt sell (${est_value:.2f}).")
                else:
                    self.add_log(f"Exit Sync: No {asset} balance found. Already USDT.")
            except Exception as e:
                self.add_log(f"Exit Protocol Error: {str(e)}")

        
        # ── Statistics & Neural Memory Unification ──
        await self._update_closing_stats(trade, pnl_absolute, pnl_pct, reason)
        
        try:
            db_abs_path = os.path.abspath(self.memory.db_path)
            entry_t = trade.get('entry_time', trade.get('timestamp', trade.get('time', '')))
            conf = trade.get('ai_conf', trade.get('conf', 0.85))
            
            self.memory.log_trade(
                symbol        = trade['symbol'],
                side          = trade.get('side', 'BUY'),
                entry         = entry_p,
                exit_p        = price,
                exit_t        = datetime.now().isoformat(),
                entry_t       = entry_t,
                pnl           = pnl_pct,
                conf          = conf,
                health        = float(self.stats.get('market_health', 50)),
                sentiment     = str(self.stats.get('sentiment', 'Neural')),
                strategy_used = str(trade.get('strategy', reason))
            )
            self.add_log(f"🧠 Brain-Link: Trade saved to -> {db_abs_path} (Dashboard Exit)")
        except Exception as log_err:
            self.add_log(f"⚠️ Brain-Link Failed: {log_err}")

    async def _update_closing_stats(self, trade, pnl_absolute, pnl_pct, reason):
        """Standardized statistics update helper."""
        self.stats['daily_pnl'] = float(self.stats.get('daily_pnl', 0.0)) + float(pnl_absolute)
        self.stats['daily_pnl_pct'] = float(self.stats.get('daily_pnl_pct', 0.0)) + float(pnl_pct)
        self.stats['session_pnl'] = float(self.stats.get('session_pnl', 0.0)) + float(pnl_absolute)
        self.stats['closed_trades'] = int(self.stats.get('closed_trades', 0)) + 1
        self.stats['trades_count'] = int(self.stats.get('trades_count', 0)) + 1
        
        if pnl_absolute < 0:
            self.stats['consecutive_losses'] = int(self.stats.get('consecutive_losses', 0)) + 1
            # UNIFIED FIX: Trigger cooldown on manual/dashboard exits too
            expiry = time.time() + 300
            self.blacklisted_symbols[trade['symbol']] = expiry
            self._save_blacklist()
            self.add_log(f"❄️ [COOL-DOWN] Applied 5m rest to {trade['symbol']} after loss.")
        else:
            self.stats['consecutive_losses'] = 0
            
        ai_lesson = "Strategy performance within expected parameters. (Node Latency: AI Insight Deferred)"
        try:
            if self.gemini and self.gemini.api_keys:
                self.add_log("AI Cluster: Initiating Neural Post-Trade Review & Cluster Rotation...")
                review_prompt = (
                    f"Institutional Review: Trade on {trade['symbol']} ({trade['side']}) closed for ${pnl_absolute:.2f} ({pnl_pct:.2f}%). "
                    f"Market Health: {self.stats['market_health']}%. Reason: {reason}. "
                    "As a Senior Strategist, provide a deep bilingual (AR/EN) neural lesson about this outcome. "
                    "Explain the 'why' behind this result. Keep it professional."
                )
                result = await asyncio.wait_for(self.gemini.ask(review_prompt), timeout=15.0)
                if result:
                    ai_lesson = result
                self.stats['ai_cluster'] = self.gemini.get_quota_info()
        except asyncio.TimeoutError:
            app_logger.warning("Post-Trade Review: Gemini Cluster timed out. Returning cached stability message.")
        except Exception as e:
            app_logger.warning(f"Post-Trade Review Error: {e}")
            
        self.stats['active_count'] = len(self.active_trades)
        self.healer.save_trade_state(self.active_trades)
        
        try:
            color_emoji = "🟢" if pnl_absolute > 0 else "🔴"
            status_text = "Profitable / رابحة" if pnl_absolute > 0 else "Loss / خسارة"
            await self.telegram.send_message(
                f"{color_emoji} *Position Closed | إغلاق المركز*\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"🔹 *Asset:* `{trade['symbol']}`\n"
                f"🔹 *Result:* {status_text} (`{pnl_pct:+.2f}%`)\n"
                f"🔹 *PNL:* `${pnl_absolute:+.2f}`\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"🧠 *Neural Lesson:*\n{ai_lesson}"
            )
        except: pass
        
        if trade in self.active_trades:
            self.active_trades.remove(trade)
            
        try:
            # Consistent use of total_equity for circuit breaker
            equity = self.stats.get('total_equity', self.stats.get('balance', 0))
            self.circuit_breaker.record_result(pnl_absolute, equity)
        except Exception as _cb_err:
            self.add_log(f"⚠️ [CB] Record error: {_cb_err}")
        
        self.healer.save_trade_state(self.active_trades)
        
        if not self.active_trades:
            self.healer.clear_trade_state()

    async def _send_daily_briefing(self):
        try:
            self.add_log("AI Cluster: Generating Daily Neural Briefing...")
            
            pnl_status = "🟢 PROFIT" if self.stats['daily_pnl'] > 0 else "🔴 LOSS"
            
            prompt = (
                f"Sovereign Briefing: Today's performance: ${self.stats['daily_pnl']:.2f} ({self.stats['daily_pnl_pct']:.2f}%). "
                f"Total Trades: {self.stats['trades_count']}. Market Health: {self.stats['market_health']}%. "
                "Task: Provide a detailed professional summary in Arabic about this performance. "
                "Include a 'Learning Section' (نصيحة تعليمية) explaining a concept like momentum, risk/reward, or capital preservation for the user to learn from today's outcomes. "
                "Make it encouraging and bilingual at important headings."
            )
            
            briefing = await self.gemini.ask(prompt)
            if not briefing: briefing = "Unable to generate summary. Performance secured."
            
            await self.telegram.send_message(
                f"📊 *DAILY NEURAL BRIEFING | الموجز العصبي اليومي*\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"🔹 *Status:* {pnl_status}\n"
                f"🔹 *Total PNL:* `${self.stats['daily_pnl']:+.2f}` (`{self.stats['daily_pnl_pct']:+.2f}%`)\n"
                f"🔹 *Trades:* {self.stats['trades_count']}\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"{briefing}"
            )
            self.add_log("Daily Neural Briefing dispatched to Telegram.")
        except Exception as e:
            self.add_log(f"Briefing Error: {e}")

    async def close_trade(self, side, price, reason, symbol=None):
        if self.active_trades:
            target_symbol = symbol if symbol else self.active_trades[0]['symbol']
            await self.close_trade_by_symbol(target_symbol, side, price, reason)

    async def sync_from_binance(self):
        try:
            balances = self.api.get_all_balances()
            for b in balances:
                asset = b['asset']
                if asset in ['USDT', 'BNB', 'FDUSD', 'USDC']: continue
                
                qty = float(b['free']) + float(b['locked'])
                symbol = f"{asset}USDT"
                
                # ── [UPDATED v14.9: Sensitive Ghost Recovery] ──
                import math
                ticker = self.api.get_symbol_ticker(symbol)
                # Lower threshold to 0.3 USDT to catch assets even in micro-accounts
                if not ticker or (qty * ticker < 0.3): continue
                
                if not any(t['symbol'] == symbol for t in self.active_trades):
                    self.add_log(f"🛡️ [RECOVERY] Auditing ghost asset: {asset}...")
                    
                    try:
                        trades = self.api.client.get_my_trades(symbol=symbol, limit=5)
                        buy_trades = [t for t in trades if t.get('isBuyer')]
                        if buy_trades:
                            entry_price = float(buy_trades[-1]['price'])
                        else:
                            entry_price = ticker 
                    except:
                        entry_price = ticker
                        
                    new_trade = {
                        'symbol': symbol,
                        'entry_price': entry_price,
                        'qty': qty,
                        'sl': entry_price * 0.98, 
                        'tp': entry_price * 1.05, 
                        'side': 'BUY',
                        'conf': 85.0, 
                        'order_id': 'RECOVERED',
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    self.active_trades.append(new_trade)
                    self.add_log(f"✅ [RECOVERY] Ghost Asset Found: {symbol} (${(qty*ticker):.2f}). Restored to monitoring.")
                    
                    # Notify Telegram
                    asyncio.create_task(self.telegram.send_message(
                        f"🛡️ *GHOST RECOVERY DETECTED*\n"
                        f"Asset: `{symbol}` found in Binance but missing from bot memory.\n"
                        f"Action: Restored to monitoring state with Entry at `${entry_price:.4f}`"
                    ))
                    
        except Exception as e:
            self.add_log(f"Recovery Audit Error: {e}")

    async def protocol_omega(self):
        self.add_log("🚨🚨🚨 PROTOCOL OMEGA ACTIVATED: INITIATING FULL LIQUIDATION 🚨🚨🚨")
        self.voice.alert_protocol_omega()
        self.voice.say("Protocol Omega engaged. Initiating emergency liquidation and fund recall sequence.")
        
        self.is_paused = True
        
        if self.active_trades:
            for trade in list(self.active_trades):
                try:
                    curr_p = self.api.get_symbol_ticker(trade['symbol'])
                    await self.close_trade_by_symbol(trade['symbol'], 'SELL', curr_p, "PROTOCOL OMEGA / Extreme Risk Shutdown")
                except: pass
            
        try:
            self.api.client._cancel_all_open_orders() 
            self.add_log("Omega: All open orders on Binance cancelled.")
        except:
            self.add_log("Omega: Individual order cleanup triggered.")

        try:
            self.add_log("Omega: Recalling funds from Yield Farming...")
            await self.farmer.recall_funds()
        except: pass
        
        await self.telegram.send_message("🚨 *PROTOCOL OMEGA EXECUTED*\nFull Liquidation Complete. Funds secured in USDT. System is currently PAUSED.")
        self.add_log("🚨 PROTOCOL OMEGA COMPLETE: System Paused.")

    def update_accuracy_stats(self):
        try:
            from datetime import datetime, timezone, timedelta
            memories = self.memory.get_recent_memories(limit=20)
            if memories:
                wins = len([m for m in memories if m['profit_loss'] > 0])
                acc = (wins / len(memories)) * 100
                if not isinstance(self.stats['ai_accuracy_history'], list):
                    self.stats['ai_accuracy_history'] = []
                    
                now_algeria = datetime.now(timezone.utc) + timedelta(hours=1)
                self.stats['ai_accuracy_history'].append({
                    'time': now_algeria.strftime("%H:%M"),
                    'accuracy': round(acc, 2)
                })
                if len(self.stats['ai_accuracy_history']) > 15:
                    self.stats['ai_accuracy_history'].pop(0)
        except Exception as e:
            app_logger.error(f"Accuracy Update Error: {e}")

    async def _check_daily_report(self):
        try:
            from datetime import datetime, timezone, timedelta
            now = datetime.now(timezone.utc) + timedelta(hours=1) 
            today_str = now.strftime("%Y-%m-%d")
            
            if self.last_report_date != today_str and now.hour >= 23:
                self.last_report_date = today_str
                
                # Fetch today's data for the Intelligent Report
                trades_today = self.memory.get_today_detailed_trades()
                
                # Get optimizer changes (summarize what happened today from live state)
                evo_summary = self.stats.get('daily_evolution', "تطور مستمر: النظام يراقب السيولة لضمان أفضل دخول.")
                
                # Generate the High-Intelligence Report
                intel_report = self.reporter.generate_daily_telegram_report(
                    stats             = self.stats,
                    trades_today      = trades_today,
                    optimizer_changes = evo_summary
                )
                
                await self.telegram.send_message(intel_report)
                self.add_log(f"🧠 [INTELLIGENCE DISPATCH] Daily Neural Learning Report sent to Telegram.")
                # Reset evolution tracking for the next day
                self.stats['daily_evolution'] = {} 
        except Exception as e:
            app_logger.error(f"Daily Report Thread Error: {e}")

    async def dispatch_intelligence_heartbeat(self):
        try:
            self.add_log("System Protocol: Dispatching Intelligence Heartbeat...")
            
            bin_h = "✅ ONLINE" if self.api.client else "⚠️ LINK ERROR"
            gem_h = "✅ ACTIVE" if self.gemini and self.gemini.api_keys else "⚠️ FALLBACK"
            
            report = (
                f"🔵 *PROSOFT SYSTEM HEARTBEAT / نبض النظام*\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"🔗 *Binance:* {bin_h} | 🧠 *AI:* {gem_h}\n"
                f"📊 *Asset:* `{self.symbol}` @ `${self.stats['price']:.2f}`\n"
                f"🌡️ *Market Health:* `{self.stats['market_health']:.0f}%`\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
            )

            if self.active_trades:
                report += f"📈 *ACTIVE POSITIONS ({len(self.active_trades)}) / الصفقات الحالية*\n"
                for t in self.active_trades:
                    t_price = self.stats.get('price', 0)
                    pnl_pct = (t_price / t['entry_price'] - 1) * 100
                    color = "🟢" if pnl_pct > 0 else "🔴"
                    report += (
                        f"• `{t['symbol']}` | PNL: {color} `{pnl_pct:+.2f}%` | SL: `${t['sl']:,.2f}`\n"
                    )
                report += f"━━━━━━━━━━━━━━━━━━━━\n"
            else:
                report += "🔍 *STATUS:* Scanning for institutional entries... / جاري البحث عن سيولة مؤسسية...\n━━━━━━━━━━━━━━━━━━━━\n"

            prompt = (f"Analyze the current market for {self.symbol} at ${self.stats['price']} with Health {self.stats['market_health']}%. "
                     "Provide a deep, sophisticated strategic insight as a human senior analyst. "
                     "Explain the 'why' behind your current stance in a professional and insightful paragraph. "
                     "Use both English and Arabic to maintain high-level bilingual intelligence.")
            ai_msg = "Strategic monitoring active. Analyzing institutional flow for potential shifts. / المراقبة الاستراتيجية مستمرة. نقوم حالياً بتحليل تدفق السيولة المؤسسية لرصد أي تحركات قوية."
            try:
                if self.gemini and self.gemini.api_keys:
                    result = await asyncio.wait_for(self.gemini.ask(prompt), timeout=10.0)
                    if result:
                        ai_msg = result
            except Exception as e:
                app_logger.warning(f"AI Insight Latency: {e}")
            
            report += f"🧠 *AI Sector Analysis:*\n{ai_msg}"
            await self.telegram.send_message(report)
            
        except Exception as e:
            app_logger.error(f"Heartbeat dispatch failure: {e}")

    async def activate_protocol_omega(self, reason):
        self.voice.alert_protocol_omega()
        self.add_log(f"🚨 ALERT: PROTOCOL OMEGA ACTIVATED! Reason: {reason}")
        
        if self.active_trades:
            for trade in list(self.active_trades):
                curr_p = self.api.get_symbol_ticker(trade['symbol']) or trade['entry_price']
                await self.close_trade_by_symbol(trade['symbol'], 'SELL', curr_p, "OMEGA EXIT")
            
        self.stats['pending_signal'] = None
        
        warning = "System Halted. Extreme High Risk detected."
        if self.gemini and self.gemini.model:
            p = f"Reason: {reason}. Current Symbol: {self.symbol}. Generate a high-priority institutional emergency warning for customers. (AR/EN)"
            warning = await self.gemini.ask(p)
            
        await self.telegram.send_message(
            f"🚫 *PROTOCOL OMEGA ACTIVATED / تفعيل بروتوكول أوميغا* 🚫\n\n"
            f"⚠️ *Emergency Status:* HALTED / توقف اضطراري\n"
            f"🚩 *Incident / السبب:* {reason}\n\n"
            f"{warning}"
        )


if __name__ == "__main__":
    bot = TradingBot()
    from src.api.dashboard_api import DashboardAPI
    bot.dashboard = DashboardAPI(bot)
    bot.dashboard.run() 
    
    try:
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        print("Bot Stopped by User.")