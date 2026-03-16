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
    # ... rest of startup ...
    import asyncio
    from datetime import datetime
    import pandas as pd
    from dotenv import load_dotenv
    from rich.live import Live
    # ... rest of imports will follow ...
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
from src.risk_management.global_macro_filter import GlobalMacroFilter
from src.strategy.liquidity_heatmap import LiquidityHeatmap

load_dotenv()

class TradingBot:
    def __init__(self, symbol='BTCUSDT', timeframe='15m', interval_sec=20):
        self.symbol = os.getenv('SYMBOL', symbol)
        self.timeframe = os.getenv('TIMEFRAME', timeframe)
        self.interval_sec = int(interval_sec)
        self.ai_threshold = float(os.getenv('AI_CONFIDENCE_THRESHOLD', 0.75))
        
        self.execution_mode = os.getenv('EXECUTION_MODE', 'manual')
        self.voice_alerts = os.getenv('VOICE_ALERTS', 'on') == 'on'
        
        # Modules
        self.api = BinanceClientWrapper(testnet=False)
        self.ta = TechnicalAnalysis()
        self.strategy = BaseStrategy()
        self.risk = RiskManager()
        self.ai = ModelManager()
        self.gemini = GeminiAI()
        self.intel = QuantumIntelligence(gemini=self.gemini)
        self.portfolio = PortfolioManager(self.api)
        self.news = GlobalNewsEngine()
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
            'market_pulse': self.news.refresh_pulse(),
            'whale_alerts': [],
            'top_gems': [],
            'execution_mode': self.execution_mode,
            'voice_alerts': self.voice_alerts,
            'daily_pnl': 0.0,
            'trades_count': int(0),
            'active_count': int(0),
            'ai_accuracy_history': [],
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
            'last_periodic_sync': 0
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
        self.sentiment_front = AISentimentFrontRunner(self.gemini, self.news)
        self.twitter = TwitterSentimentFirehose() # Phase 1: Twitter Radar
        self.optimizer = StrategyOptimizer()      # Cycle 2: The Scientist
        self.alpha_tracker = WhaleAlphaTracker()  # Cycle 2: Shadow Protocol
        self.arbitrage = TriangularArbitrageEngine(self.api)  # Cycle 3: Arbitrage
        self.order_flow = OrderFlowAnalyzer(self.api)          # Cycle 3: Order Flow
        self.hedger = HedgingProtocol()                        # Cycle 4: Hedge Shield
        self.macro_filter = GlobalMacroFilter()                # Cycle 4: Macro Guardian
        self.heatmap = LiquidityHeatmap(self.api)              # Cycle 4: War Room
        self.memory = NeuralMemory()
        
        # --- NEW MODULES (v12.0) ---
        self.shield = ManipulationShield()        # درع التلاعب
        self.diversifier = DiversificationMatrix() # مصفوفة التنويع
        self.healer = SelfHealingEngine(self)      # محرك التصحيح الذاتي
        self.voice = VoiceAlertSystem(enabled=os.getenv('VOICE_ALERTS', 'on') == 'on')  # التنبيهات الصوتية
        
        # Performance & AI Evolution Tracking
        self.is_paused = False # Mode to stop all loops if Omega triggered
        
        # Dashboard API & Event Sync
        self.main_loop = asyncio.get_event_loop()
        self.wakeup_event = asyncio.Event()
        self.dashboard = DashboardAPI(self)
        self.dashboard.run(port=5000)
        
        # Active Trade Tracking
        # --- CLOUD RECOVERY: Load previous state if exists ---
        self.active_trade = self.healer.load_trade_state()
        if self.active_trade:
            self.symbol = self.active_trade['symbol']
            self.add_log(f"💾 SYSTEM RECOVERED: Restored active {self.active_trade['symbol']} trade.")
        else:
            self.active_trade = None # Stores {symbol, side, entry_price, qty, sl, tp, conf}
            
        self.omega_active = False # Protocol Omega State
        self.last_report_date = None # Track daily summary timestamp
        
        self.ui.update_ui(self.symbol, self.timeframe, self.stats, self.logs)

    def add_log(self, msg):
        now = datetime.now().strftime("%H:%M:%S")
        self.logs.append(f"[{now}] {msg}")
        app_logger.info(msg)

    def reconnect_binance(self, api_key, api_secret):
        """Live-updates Binance API credentials directly inside the existing wrapper so all modules instantly inherit it."""
        try:
            from binance.client import Client
            # Update the inner client inline - fixes Arbitrage and other modules using the old client reference
            self.api.client = Client(api_key, api_secret, testnet=False)
            self.api.client.ping() # Test connection
            self.api.api_key = api_key
            self.api.api_secret = api_secret
            
            self.add_log("System Protocol: Binance Gateway Re-connected and synced across all modules.")
            return True
        except Exception as e:
            self.add_log(f"Binance Reconnection Error: {str(e)}")
            return False

    def reconnect_telegram(self, token, chat_id):
        """Live-updates Telegram Bot credentials safely using the main event loop."""
        try:
            self.telegram = TelegramBot(token=token, chat_id=chat_id)
            
            # CRITICAL FIX: Use the main event loop for async task from Flask thread
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
        """Safely switches the bot's focus to a new asset pair and ensures USDT suffix."""
        if not new_symbol.endswith('USDT'):
            new_symbol = f"{new_symbol}USDT"
            
        old_symbol = self.symbol
        self.symbol = new_symbol
        self.add_log(f"⭐ STRATEGIC SWITCHOVER: {old_symbol} -> {self.symbol}")
        
        # Reset relative stats for the new coin
        self.stats['rsi'] = 0
        self.stats['ai_conf'] = 0
        
        # Clear UI cache for immediate update
        if hasattr(self, 'live_instance') and self.live_instance:
            self.live_instance.update(self.ui.update_ui(self.symbol, self.timeframe, self.stats, self.logs))

    async def perform_diagnostics(self):
        """Institutional startup sequence and health check."""
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
        
        # Dispatch a startup test notification
        await self.telegram.send_message("🚀 *PROSOFT QUANTUM PRIME SYSTEM STARTUP*\nEngines are online. Trading system engaged.")
        self.voice.alert_bot_started()
        self.voice.say("System diagnostics complete. Artificial Intelligence Core is online and trading operations have commenced.")
        self.add_log("--- SYSTEM STATUS: OPTIMAL | COMMENCING OPERATIONS ---")
        await asyncio.sleep(1)

    async def run(self):
        """Clean Main loop for TradingBot v11.2"""
        await self.perform_diagnostics()
        
        with Live(self.ui.layout, refresh_per_second=2, screen=True) as live:
            self.live_instance = live # Store for switch_symbol access
            loop_count = 0
            while True:
                loop_count += 1
                try:
                    # Update UI at the start of loop to show the "SCANNING" status
                    self._force_ui_update()
                    
                    # 0. Daily Financial Summary (Late Night)
                    await self._check_daily_report()
                    
                    # 0.1 Periodic Revenue Sync (Every 10 loops)
                    if loop_count % 10 == 0:
                        await self.farmer.sync_rewards(self.memory)
                        await self.funding_arb.log_funding_revenue(self.memory)
                        
                        # Phase 12.1: Funding Rate Arbitrage Scanner
                        arb_rates = await self.funding_arb.scan_opportunities()
                        self.stats['funding_rates'] = arb_rates
                        
                        # Update Live Stats for Dashboard
                        rev_totals = self.memory.get_revenue_totals()
                        
                        # Check for new revenue to alert
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
                    
                    # 0.3 Yield Farming: Put idle funds to work (Every 15 loops if no active trade)
                    if not self.active_trade and loop_count % 15 == 0:
                        await self.farmer.check_and_farm(threshold_usdt=25.0)
                        self.stats['yield_status'] = "FARMING" if self.farmer.is_farming else "IDLE"
                    
                    # 0.2 Update AI Accuracy (Every 5 loops)
                    if loop_count % 5 == 0:
                        self.update_accuracy_stats()

                    # 1. New Asset Sniper Check (Ultra-Fast)
                    new_asset = self.sniper.scan_for_new_listings()
                    if new_asset:
                        self.add_log(f"⚡ LISTING SNIPER TRIGGRED: {new_asset}")
                        if self.execution_mode == 'auto':
                            # Recall funds from Earn before sniping
                            await self.farmer.recall_funds()
                            
                            usdt_bal = self.api.get_account_balance('USDT')
                            # For new listings: use 15% of balance or $10 minimum
                            snipe_amt = max(10.5, usdt_bal * 0.15)
                            if usdt_bal >= snipe_amt:
                                self.add_log(f"⚡ LISTING SNIPER: Executing FLASH BUY on {new_asset} for ${snipe_amt:.2f}")
                                try:
                                    # Get current price for the new listing
                                    snipe_price = self.api.get_symbol_ticker(new_asset)
                                    if snipe_price and snipe_price > 0:
                                        snipe_qty = snipe_amt / snipe_price
                                        order_res = self.orders.place_market_buy(new_asset, snipe_qty)
                                        if order_res:
                                            # Set emergency SL/TP for sniper trades
                                            snipe_sl = snipe_price * 0.95   # 5% SL
                                            snipe_tp = snipe_price * 1.10   # 10% TP
                                            self.active_trade = {
                                                'symbol': new_asset,
                                                'side': 'BUY',
                                                'entry_price': snipe_price,
                                                'qty': snipe_qty,
                                                'sl': snipe_sl,
                                                'tp': snipe_tp,
                                                'conf': 1.0,
                                                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                            }
                                            self.voice.alert_sniper_hit(new_asset)
                                            self.add_log(f"⚡ SNIPE SUCCESS: Target {new_asset} engaged at {snipe_price}")
                                            self.switch_symbol(new_asset)
                                            self.stats['trades_count'] += 1
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

                    # 2. Main Price Monitoring
                    ticker = self.api.get_symbol_ticker(self.symbol)
                    if ticker is None:
                        self.add_log("Network Interruption: Attempting to re-stabilize link...")
                        await asyncio.sleep(5)
                        continue
                    self.stats['price'] = ticker
                    
                    # 2. Analysis & Intel (Every loop)
                    df = self.api.get_historical_klines(self.symbol, self.timeframe, limit=350)
                    if df is not None and not df.empty:
                        df = self.ta.calculate_indicators(df)
                    
                    if df is not None and not df.empty and len(df) >= 2:
                        curr = df.iloc[-1]
                        self.stats['ema50'] = curr['EMA_50']
                        self.stats['ema200'] = curr['EMA_200']
                        # --- AGGRESSIVE AI QUOTA MANAGEMENT (v12.2) ---
                        current_time = time.time()
                        last_ai_time = self.stats.get('last_ai_update', 0)
                        last_quota_hit = self.stats.get('last_ai_quota_hit', 0)
                        
                        # If we hit quota recently (within 1 hour), skip Gemini and use technical fallback
                        # Also use a 10-minute cache even if quota is fine to save tokens
                        use_ai = (current_time - last_quota_hit > 3600) and (current_time - last_ai_time > 600)
                        
                        # 1. Technical Confidence (Live update every loop)
                        self.stats['ai_conf'] = self.ai.calculate_confidence(curr)
                        
                        # 2. Market Health (Live update every loop, Gemini throttled)
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
                        
                        # Update cluster info EVERY loop for real-time visibility
                        self.stats['ai_cluster'] = self.gemini.get_quota_info()
                        
                        self.stats['rsi'] = curr['RSI']
                        self.stats['sentiment'] = self.intel.detect_sentiment(df)
                        pred = self.intel.predict_next_price(df)
                        self.stats['prediction'] = f"{pred['direction']} ({pred['change_pct']:+.1f}%)" if pred else "N/A"
                        self.last_df = df # Store for Dashboard Candlesticks

                        # --- NEW: MEME ROCKET SNIPER CHECK ---
                        rocket = self.rocket_sniper.detect_rocket(df, self.symbol)
                        if rocket and self.execution_mode == 'auto' and not self.active_trade:
                            self.add_log(f"🚀 MEME ROCKET ENGAGED: Executing scalp on {self.symbol}")
                            # Use aggressive rocket parameters
                            balance = self.api.get_account_balance('USDT')
                            # For rockets, use a fixed $20 or 15% of balance for speed
                            qty = max(20.0, balance * 0.15) / rocket['entry_price']
                            await self.execute_trade(self.symbol, 'BUY', qty, rocket['entry_price'], 
                                                     rocket['entry_price'] * (1 - rocket['emergency_sl']/100),
                                                     rocket['entry_price'] * (1 + rocket['target_profit']/100), 0.99)
                        elif rocket:
                            await self.telegram.send_message(
                                f"🚀 *MEME ROCKET ALERT / تنبيه صاروخ الميم* 🚀\n"
                                f"Asset / الأصل: `{self.symbol}`\n"
                                f"Status / الحالة: EXPLOSIVE VOLUME! / سيولة انفجارية\n"
                                f"Action / الإجراء: Manual scalp recommended. / ينصح بالسكالب اليدوي."
                            )
                    else:
                        self.add_log("Data Warning: Insufficient data for analysis. Waiting...")
                        if not self.active_trade:
                            await asyncio.sleep(self.interval_sec)
                            continue

                    # 3. Portfolio Sync (Every 5 loops)
                    if loop_count % 5 == 0:
                        try:
                            self.portfolio.update_portfolio()
                            summ = self.portfolio.get_summary()
                            self.stats['total_equity'] = summ.get('total_value', 0.0)
                            self.stats['balance'] = self.api.get_account_balance('USDT')
                            
                            if self.stats['total_equity'] > 0:
                                # Run yield farming/launchpool on idle USDT if no active trade
                                if not self.active_trade and self.execution_mode == 'auto':
                                    await self.farmer.check_and_farm(threshold_usdt=25.0)
                                    # LAUNCHPOOL INTEGRATION: Stake idle funds for free tokens
                                    if self.stats['balance'] > 50:
                                        await self.pool_hunter.auto_stake_for_farming(amount_usdt=20.0)
                                    
                                self.add_log(f"Portfolio Sync: Equity verified at ${self.stats['total_equity']:,.2f}")
                                
                                # --- NEW: LAUNCHPOOL & SENTIMENT SCAN ---
                                self.pool_hunter.scan_for_pools()
                                ai_lead = await self.sentiment_front.analyze_and_front_run()
                                if ai_lead and self.execution_mode == 'auto' and not self.active_trade:
                                    self.add_log(f"🧠 AI SENTIMENT FRONT-RUN: Switching to {ai_lead['symbol']} for early entry.")
                                    self.switch_symbol(ai_lead['symbol'])
                                    # Signal immediate loop restart to buy
                                    continue
                                elif ai_lead:
                                    await self.telegram.send_message(
                                        f"🧠 *AI SENTIMENT FRONT-RUNNER / استباق الذكاء الاصطناعي* 🧠\n"
                                        f"Lead / السبب: {ai_lead['reason']}\n"
                                        f"Action / الإجراء: Monitoring {ai_lead['symbol']} for early entry.\n"
                                        f"الإجراء: مراقبة {ai_lead['symbol']} للدخول المبكر."
                                    )
                            else:
                                self.add_log("Portfolio Sync: Connection active, but no significant assets found in Spot Wallet.")
                        except Exception as e:
                            self.add_log(f"Portfolio Sync Error: {str(e)}")

                    # 3.5 Auto-Rotation: Intelligent Market Hunting (Every 3 loops ~ 1 minute)
                    if not self.active_trade and loop_count > 0 and loop_count % 3 == 0:
                        try:
                            # 1. Scan for Top Candidates
                            scan_results = self.market_scanner.scan_market()
                            self.stats['top_gems'] = scan_results # Synchronize Dashboard
                            
                            if scan_results:
                                # 2. Fair Evaluation: Score the current symbol using the SAME benchmark
                                current_eval = self.market_scanner.analyze_symbol(self.symbol)
                                current_scanner_score = current_eval['score'] if current_eval else 40
                                
                                best_candidate = scan_results[0]
                                
                                # 3. Strategic Decision: Switch only for significant Alpha (+12 threshold)
                                # This prevents 'jitter' and ensures we only move for high-probability setups
                                if best_candidate['score'] > current_scanner_score + 12 and best_candidate['symbol'] != self.symbol:
                                    self.add_log(f"🧠 AI STRATEGIC PIVOT: {best_candidate['symbol']} (Score: {best_candidate['score']}) outperforms {self.symbol} (Score: {current_scanner_score})")
                                    
                                    # Send Professional Bilingual Alert
                                    try:
                                        msg = (f"🔄 *STRATEGIC ROTATION / تدوير استراتيجي* 🔄\n\n"
                                               f"Current / الحالي: `{self.symbol}` (Score: {current_scanner_score})\n"
                                               f"Superior Alpha / البديل الأقوى: `{best_candidate['symbol']}` (Score: {best_candidate['score']})\n\n"
                                               f"Reason: Multi-factor analysis detected terminal growth potential.\n"
                                               f"السبب: التحليل متعدد العوامل اكتشف إشارة انفجارية قوية.")
                                        await self.telegram.send_message(msg)
                                    except: pass
                                    
                                    self.switch_symbol(best_candidate['symbol'])
                                    continue # Restart loop with new focus
                        except Exception as e:
                            self.add_log(f"Auto-Rotation Protocol Latency: {e}")

                    # 4. Intelligence Sync & Periodic Pulse
                    # Sync whales/gems every 25 loops (Approx 8-10 minutes)
                    if loop_count % 25 == 0:
                        try:
                            # 4.1. Real-time Whale Alerts
                            new_whales = self.whales.get_latest_movements()
                            self.stats['whale_alerts'] = new_whales
                            for w in new_whales:
                                # High priority alerts send instantly to Telegram
                                if w['impact'] in ['CRITICAL', 'HIGH'] and w['msg'] != self.stats.get('last_tg_whale'):
                                    await self.telegram.send_message(f"🐋 *SMART MONEY ALERT / تنبيه الحيتان*\n{w['msg']}\nImpact: {w['impact']}")
                                    self.stats['last_tg_whale'] = w['msg']
                                    self.add_log(f"System Protocol: Instant Whale Warning transmitted.")
                            
                            # 4.1.2 Phase 1: Twitter Radar (X-Intelligence)
                            tweet_alert = self.twitter.scan_live_firehose()
                            if tweet_alert:
                                alert_msg = (f"🐦 *TWITTER RADAR ALERT / تنبيه تويتر* 🐦\n"
                                           f"Source: `{tweet_alert['source']}`\n"
                                           f"Tweet: {tweet_alert['tweet']}\n"
                                           f"Action: {tweet_alert['action_taken']}")
                                await self.telegram.send_message(alert_msg)
                                self.add_log(f"Twitter Radar: High-impact event from {tweet_alert['source']}")
                                # Update dashboard ticker
                                self.stats['news_highlight'] = f"{tweet_alert['source']}: {tweet_alert['tweet']}"
                            
                            # 4.2. Golden Opportunity Scout (Scan other top gems for high-conf signals)
                            top_gems = self.stats.get('top_gems', [])
                            for gem in top_gems[:3]: # Only check Top 3 gems to prevent lag
                                if gem['symbol'] != self.symbol:
                                    # Very light-weight check for explosive potential
                                    if gem.get('score', 0) > 85: # Only if score is elite
                                        alert_key = f"opp_{gem['symbol']}"
                                        if alert_key != self.stats.get('last_opp_alert'):
                                            await self.telegram.send_message(
                                                f"⭐ *GOLDEN CHANCE / فرصة ذهبية*\n"
                                                f"Asset: {gem['symbol']}\n"
                                                f"Momentum Score: {gem['score']}\n"
                                                f"Status: Explosive Liquidity Spike detected.\n"
                                                f"الحالة: تم اكتشاف ارتفاع هائل في السيولة."
                                            )
                                            self.stats['last_opp_alert'] = alert_key
                        except Exception as e:
                            self.add_log(f"Alert Service Latency: {str(e)}")

                    # 4.3 Cycle 2: Advanced Intelligent Protocols
                    if loop_count > 0:
                        # 4.3.1 Strategy Self-Refactoring (Every 100 loops ~ 30 mins)
                        if loop_count % 100 == 0:
                            self.add_log("🧠 System Protocol: Running AI Strategy Optimization cycle...")
                            optimization = self.optimizer.run_optimization_cycle()
                            if optimization and optimization.get('type') == 'ADJUST_THRESHOLD':
                                self.ai_threshold = optimization['value']
                                self.add_log(f"🧠 [OPTIMIZER] Auto-Refactoring: AI Confidence Threshold elevated to {self.ai_threshold}")

                        # 4.3.2 Alpha Shadow Tracking (Periodic scan)
                        if not self.active_trade and loop_count % 15 == 0:
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
                                    self.switch_symbol(lead['symbol'])

                    # Refresh News Pulse every 10 loops (~3 minutes) for a dynamic ticker
                    if loop_count % 10 == 0:
                        # Generate a dynamic AI Insight before refreshing
                        try:
                            rsi = self.stats.get('rsi', 50)
                            if rsi > 70:
                                self.news.inject_ai_insight("RSI Overbought: Consider partial profit taking.", "WARNING")
                            elif rsi < 30:
                                self.news.inject_ai_insight("RSI Oversold: Potential reversal zone detected.", "ADVICE")
                            else:
                                self.news.inject_ai_insight(f"Market Sentiment Stable. Analyzing {self.symbol} order flow.", "MARKET")
                        except: pass
                        
                        self.stats['market_pulse'] = self.news.refresh_pulse()

                    # 4.4 Cycle 3: Arbitrage & Order Flow Protocols
                    if loop_count == 1 or (loop_count > 0 and loop_count % 20 == 0):
                        try:
                            # 4.4.1 Triangular Arbitrage Scan
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
                                # Ensure UI is cleared if no opportunities exist
                                self.stats['arb_opportunities'] = []

                            # 4.4.2 Order Flow Deep Analysis
                            flow = self.order_flow.analyze_order_book(self.symbol)
                            if flow:
                                self.stats['order_flow'] = flow
                                if flow['bias'] in ['STRONG_BUY', 'STRONG_SELL']:
                                    self.add_log(f"📊 [ORDER FLOW] {self.symbol}: {flow['bias']} (Pressure: {flow['pressure_score']}%)")

                            # 4.4.3 Spoofing Detection
                            spoofs = self.order_flow.detect_whale_spoofing(self.symbol)
                            if spoofs:
                                self.stats['spoof_alerts'] = spoofs
                                self.add_log(f"⚠️ [SPOOF DETECT] {len(spoofs)} suspicious orders found on {self.symbol}!")
                        except Exception as e:
                            self.add_log(f"Cycle 3 Engine Error: {e}")

                    # 4.5 Cycle 4: Final Sovereignty Protocols
                    if loop_count > 0:
                        try:
                            # 4.5.1 Global Macro Filter (Aggressive Sync v12.2)
                            # 4.5.1 Global Macro Filter (Aggressive Sync v12.2)
                            if (loop_count == 1) or (loop_count % 10 == 0):
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
                                except Exception as e:
                                    self.add_log(f"⚠️ Macro Sync Warning: {str(e)[:50]}")
                                
                                # Check if macro conditions block trading
                                permission = self.macro_filter.get_trading_permission()
                                if not permission['allowed']:
                                    self.add_log(f"🚫 [MACRO LOCKDOWN] {permission['reason']}")
                                    await self.telegram.send_message(f"🚫 *MACRO LOCKDOWN*\n{permission['reason']}")

                            # 4.5.2 Real-time Hedging Protocol (Every Loop Sync)
                            try:
                                # Data extraction for risk engine
                                local_pnl = self.stats.get('session_pnl', 0)
                                net_health = self.stats.get('market_health', 50)
                                net_sentiment = self.stats.get('sentiment', 'neutral')
                                
                                # Safety-first FGI retrieval
                                m_state = self.stats.get('macro_state')
                                m_fgi = 50
                                if isinstance(m_state, dict):
                                    m_fgi = m_state.get('fear_greed_index', 50)
                                
                                # Evaluate Risk Score & Activation
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
                                    
                                # Continuous Recovery Watch
                                if self.stats.get('hedge_active') and self.hedger.check_recovery(local_pnl):
                                    self.add_log("✅ [HEDGE RECOVERY] Market stabilized. Shield deactivated.")
                                    await self.telegram.send_message("✅ *SHIELD DEACTIVATED / تم إلغاء التحوط*\nMarket environment stabilized.")
                                    self.stats['hedge_active'] = False
                                    
                            except Exception as e:
                                self.add_log(f"⚠️ Security Core Pulse Error: {e}")

                            # 4.5.3 War Room Heatmap (Every 30 loops)
                            if loop_count % 30 == 0:
                                heatmap = self.heatmap.generate_heatmap(self.symbol)
                                if heatmap:
                                    self.stats['heatmap'] = heatmap
                        except Exception as e:
                            self.add_log(f"Cycle 4 Sovereignty Error: {e}")
                        
                        # 4.6. PROSOFT INTELLIGENCE HEARTBEAT (Dynamic: 10m with trade / 25m idle)
                        current_time = time.time()
                        # 600s = 10m | 1500s = 25m
                        sync_threshold = 600 if self.active_trade else 1500
                        if (current_time - self.stats.get('last_periodic_sync', 0)) >= sync_threshold:
                            self.stats['last_periodic_sync'] = current_time
                            await self.dispatch_intelligence_heartbeat()

                    # 4.4. Flash Insight Service (Market Psychology & Wisdom) ~ Every 5 hours (Instead of 45 min) to save tokens
                    if loop_count > 0 and loop_count % 900 == 0:
                        try:
                            topics = ["market psychology", "risk management", "whale behavior", "technical trap warning"]
                            topic = random.choice(topics)
                            # Explicitly request Arabic & English in a structured format
                            p = (f"Generate a PRO-TRADER INSIGHT about {topic}. "
                                 f"Context: Market Health is {self.stats['market_health']}%. "
                                 "Format: 1-sentence in English, then 1-sentence in Arabic. Be elite.")
                            insight = await self.gemini.ask(p)
                            if insight:
                                await self.telegram.send_message(f"🧠 *PROSOFT FLASH INSIGHT*\n━━━━━━━━━━━━━━\n{insight}")
                        except: pass

                    # 4.5. High-Water Mark Alert (Breakout Detection)
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

                    # Background Market Scan (To update the sidebar) every 5 loops
                    if loop_count % 5 == 0:
                        self.stats['top_gems'] = self.market_scanner.scan_market()

                    # --- PROTOCOL OMEGA: Black Swan Guard ---
                    if self.stats['market_health'] < 15:
                        if not self.omega_active:
                            self.omega_active = True
                            await self.activate_protocol_omega("CRITICAL: Market Health has dropped to dangerous levels.")
                        await asyncio.sleep(self.interval_sec)
                        continue
                    
                    if self.omega_active and self.stats['market_health'] > 30:
                        self.omega_active = False
                        self.add_log("System Protocol: Market Stabilized. Protocol Omega Disengaged.")
                        await self.telegram.send_message("🛡️ *PROTOCOL OMEGA DISENGAGED* 🛡️\nMarket conditions have stabilized. Resuming standard operations.")

                    # --- Self-Healing: periodic health check (every 10 loops ~ 3 mins) ---
                    if loop_count > 0 and loop_count % 10 == 0:
                        await self.healer.run_health_check()

                    # 5. Signal Generation & Logic
                    # If we don't have an active trade, look for entries
                    if not self.active_trade:
                        signal = self.strategy.check_entry_signal(df)
                        target_symbol = self.symbol
                        target_df = df
                        target_signal = signal
                        
                        if target_signal['signal'] == 'WAIT':
                            import time as _t
                            _now = _t.time()
                            if not hasattr(self, '_last_noise_log') or (_now - self._last_noise_log) > 300:
                                self.add_log(f"Market Scan: {self.symbol} is currently in a noise zone. AI is waiting for high-velocity momentum.")
                                self._last_noise_log = _now
                        
                        # Single Symbol Focus Mode (Manual Selection only)
                        if target_signal['signal'] == 'BUY':
                            # --- Manipulation Shield Check ---
                            shield_result = self.shield.analyze(df)
                            if not shield_result['is_safe']:
                                self.add_log(f"🛡️ SHIELD BLOCKED: {shield_result['reason']}")
                                self.voice.alert_manipulation_detected()
                                target_signal = {'signal': 'WAIT'}  # Override to prevent entry
                            
                        if target_signal['signal'] == 'BUY':
                            # AI Filter & Memory Check
                            memory_warning = self.memory.analyze_past_mistakes(target_symbol)
                            if "Warning" in memory_warning:
                                self.add_log(f"Memory Check: {memory_warning}")

                            # Gemini Sovereign Confirmation
                            is_verified = True
                            if self.gemini and self.gemini.model:
                                v_prompt = (f"Market Context: Health={self.stats['market_health']:.0f}%, Sentiment={self.stats['sentiment']}. "
                                           f"System suggests a BUY on {target_symbol} @ ${target_signal['entry_price']:.2f}. "
                                           "Do you verify this signal? Analyze technicals and respond with 'VERIFIED' or 'BLOCKED' and a short reason.")
                                verification = await self.gemini.ask(v_prompt)
                                
                                # Safety net if Gemini fails to respond (None)
                                if verification is None:
                                    self.add_log(f"AI Filter: API Timeout/Error. Health is {self.stats['market_health']:.0f}%. Assumed Verified.")
                                    # Fallback: only verify if health is > 45
                                    if self.stats['market_health'] < 45:
                                        self.add_log("AI Filter: Fallback Blocked due to low market health.")
                                        is_verified = False
                                        
                                elif "BLOCKED" in verification.upper():
                                    self.add_log(f"AI Filter: Signal Blocked on {target_symbol}. Reason: {verification}")
                                    is_verified = False
                                else:
                                    self.add_log(f"AI Filter: Signal Verified. {verification}")

                            if is_verified:
                                # Recall funds from Earn before normal trade too
                                await self.farmer.recall_funds()
                                
                                # Calculate proper quantity for BOTH modes
                                balance = self.api.get_account_balance('USDT')
                                qty = self.risk.calculate_position_size(balance, target_signal['entry_price'], target_signal['stop_loss'])
                                
                                if qty <= 0 or (qty * target_signal['entry_price']) < 10:
                                    self.add_log(f"⚠️ Insufficient balance for trade. Balance: ${balance:.2f}, Min needed: $10.50")
                                elif self.execution_mode == 'auto':
                                    # AUTO-TRADE EXECUTION (with Diversification Matrix)
                                    balance = self.api.get_account_balance('USDT')
                                    safe_usdt = self.diversifier.get_safe_allocation(target_symbol, balance, self.stats.get('total_equity', balance))
                                    if safe_usdt < 10:
                                        self.add_log(f"⚠️ Diversification Matrix: Insufficient safe allocation (${safe_usdt:.2f}). Skipping trade.")
                                        exec_success = False
                                    else:
                                        self.voice.alert_buy_signal()
                                        exec_success = await self.execute_trade(target_symbol, 'BUY', qty, target_signal['entry_price'], target_signal['stop_loss'], target_signal['take_profit'], self.stats['ai_conf'])
                                    if not exec_success:
                                        self.add_log(f"Execution failed on {target_symbol}.")
                                else:
                                    # MANUAL APPROVAL PENDING (with real calculated qty)
                                    self.stats['pending_signal'] = {
                                        'symbol': target_symbol, 'side': 'BUY', 'price': target_signal['entry_price'], 
                                        'size': qty, 'sl': target_signal['stop_loss'], 'tp': target_signal['take_profit']
                                    }
                                    self.add_log(f"CORE EXECUTION: BUY {target_symbol} @ ${target_signal['entry_price']:.2f} | Qty: {qty:.6f} (${qty*target_signal['entry_price']:.2f})")
                                    try:
                                        await self.telegram.send_signal(target_symbol, target_signal['entry_price'], target_signal['stop_loss'], target_signal['take_profit'], self.stats['ai_conf'], 'BUY')
                                    except: pass
                    
                    # 6. Active Trade Management (Trailing Stop & Exit)
                    else:
                        trade = self.active_trade
                        curr_price = self.stats['price']
                        
                        # Check Stop Loss
                        if curr_price <= trade['sl']:
                            self.add_log(f"STOP LOSS HIT for {trade['symbol']} @ {curr_price}")
                            self.voice.alert_stop_loss()
                            await self.close_trade('SELL', curr_price, "SL")
                        # --- Partial Take Profit (TP1 = 50% position at midpoint) ---
                        elif 'tp1' in trade and curr_price >= trade['tp1'] and not trade.get('partial_done'):
                            tp1_price = trade['entry_price'] + (trade['tp'] - trade['entry_price']) * 0.5
                            if curr_price >= tp1_price:
                                self.add_log(f"💰 PARTIAL TP: Locking 50% profit on {trade['symbol']} @ {curr_price:.2f}")
                                self.voice.alert_partial_tp()
                                _, remaining = self.orders.partial_take_profit(trade['symbol'], trade['qty'], curr_price)
                                self.active_trade['qty'] = remaining
                                self.active_trade['partial_done'] = True
                                self.active_trade['sl'] = trade['entry_price'] * 1.001  # Move SL to break-even
                                self.add_log(f"🛡️ Break-even activated. Remaining qty: {remaining:.6f}")
                                try:
                                    await self.telegram.send_message(
                                        f"💰 *PARTIAL PROFIT LOCKED / جني أرباح جزئي* 💰\n"
                                        f"{trade['symbol']} @ ${curr_price:,.2f}\n"
                                        f"Status: Remaining position running to full TP.\n"
                                        f"الحالة: استمرار باقي الكمية نحو الهدف النهائي."
                                    )
                                except: pass
                        # Check Full Take Profit
                        elif curr_price >= trade['tp']:
                            self.add_log(f"TAKE PROFIT HIT for {trade['symbol']} @ {curr_price}")
                            self.voice.alert_take_profit()
                            await self.close_trade('SELL', curr_price, "TP")
                        # Update Trailing Stop & Break-Even
                        else:
                            # 1. AGGRESSIVE BREAK-EVEN: 
                            # Protect capital as soon as price covers 35% of the target distance
                            profit_target_dist = trade['tp'] - trade['entry_price']
                            trigger_price = trade['entry_price'] + (profit_target_dist * 0.35)
                            
                            if curr_price >= trigger_price and trade['sl'] < trade['entry_price']:
                                new_sl = trade['entry_price'] * 1.0015 # Entry + 0.15% to cover fees
                                self.active_trade['sl'] = new_sl
                                self.add_log(f"🛡️ SECURE LOCK: Break-even activated at {new_sl:.2f} (35% Target reached)")
                                try:
                                    await self.telegram.send_message(
                                        f"🛡️ *LIQUIDITY SHIELD / درع السيولة* 🛡️\n"
                                        f"Asset: `{trade['symbol']}`\n"
                                        f"Status: Capital protected at Entry (Break-even).\n"
                                        f"الحالة: حماية رأس المال عند نقطة الدخول."
                                    )
                                except: pass

                            # 2. OPTIMIZED TRAILING STOP
                            new_sl = self.orders.update_trailing_stop(trade['symbol'], curr_price, trade['entry_price'], trade['sl'], 
                                                                    trailing_pct_activation=0.015, # 1.5% profit activation
                                                                    trailing_distance=0.01)       # 1% distance
                            if new_sl > trade['sl']:
                                self.active_trade['sl'] = new_sl

                        # 7. Periodic Position Update (Moved to Heartbeat for reliability)
                        # Handled by dispatch_intelligence_heartbeat every 10 mins

                    # 8. Periodic PDF Report (Every 120 loops ~ 120 min)
                    if loop_count > 0 and loop_count % 120 == 0:
                        try:
                            self.add_log("System Protocol: Auto-dispatching Detailed PDF Intel...")
                            report_path = self.reporter.generate_daily_report(self.stats, self.logs)
                            await self.telegram.send_document(report_path, caption="📄 PROSOFT QUANTUM PRIME — 2-Hour Sector Intel Report")
                        except Exception as e:
                            self.add_log(f"Report Error: {str(e)}")

                    loop_count += 1
                    live.update(self.ui.update_ui(self.symbol, self.timeframe, self.stats, self.logs))
                    
                except Exception as e:
                    self.add_log(f"Loop Error: {str(e)}")
                
                # Intelligent Sleep: Wake up immediately if symbol is switched
                try:
                    await asyncio.wait_for(self.wakeup_event.wait(), timeout=self.interval_sec)
                    self.wakeup_event.clear()
                except asyncio.TimeoutError:
                    pass

    def _force_ui_update(self):
        """Thread-safe trigger for terminal UI redraw."""
        if hasattr(self, 'live_instance') and self.live_instance:
            self.live_instance.update(self.ui.update_ui(self.symbol, self.timeframe, self.stats, self.logs))

    def switch_symbol(self, new_symbol):
        """Dynamic Symbol Hot-Swap with Immediate Wakeup and Force Refresh."""
        self.symbol = new_symbol
        self.add_log(f"System Protocol: Switching primary asset to {new_symbol}...")
        
        # 1. Reset stats to clear old data
        self.stats['price'] = 0.0
        self.stats['ema50'] = 0.0
        self.stats['ema200'] = 0.0
        self.stats['rsi'] = 0.0
        self.stats['ai_conf'] = 0.0
        self.stats['market_health'] = 50.0
        self.stats['sentiment'] = "RE-SYNCING..."
        self.stats['prediction'] = "CALCULATING..."
        
        # 2. Trigger immediate UI refresh and Loop wakeup
        if self.main_loop and self.main_loop.is_running():
            self.main_loop.call_soon_threadsafe(self.wakeup_event.set)
            self.main_loop.call_soon_threadsafe(self._force_ui_update)
        
        self.add_log(f"Primary asset switched to {new_symbol}. Engines responding...")

    async def execute_trade(self, symbol, side, qty, price, sl, tp, conf):
        self.add_log(f"CORE EXECUTION: {side} {symbol} @ {price}")
        
        # --- OFFICIAL LAUNCH LOGIC: REAL BINANCE EXECUTION ---
        # The OrderManager handles the actual API call to Binance
        # If credentials are not set or incorrect, it will return None
        try:
            order_res = self.orders.place_market_buy(symbol, qty)
        except Exception as e:
            self.add_log(f"Execution Error: {str(e)}")
            order_res = None
        
        if order_res:
            # Fetch actual quantity bought (minus fees sometimes)
            executed_qty = sum(float(fill['qty']) for fill in order_res.get('fills', [])) if 'fills' in order_res else qty
            
            self.active_trade = {
                'symbol': symbol,
                'side': side,
                'entry_price': price,
                'qty': executed_qty,
                'sl': sl,
                'tp': tp,
                'conf': conf,
                'order_id': order_res.get('orderId', 'SIMULATED')
            }
            self.stats['active_count'] = 1
            
            # --- NEW: IRON-CLAD OCO (REAL TP/SL ON BINANCE) ---
            try:
                oco_res = self.orders.place_oco_order(symbol, executed_qty, tp, sl)
                if oco_res:
                    self.active_trade['oco_id'] = oco_res.get('orderListId')
                    self.add_log(f"🛡️ Iron-Clad Protection: OCO (TP/SL) set on Binance for {symbol}")
            except Exception as e:
                self.add_log(f"OCO Warning: Failed to set remote TP/SL. Bot will monitor locally. Error: {e}")

            self.stats['trades_count'] += 1
            # Notify Telegram
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

    async def close_trade(self, side, price, reason):
        if not self.active_trade: return
        
        trade = self.active_trade
        
        # --- NEW: CLEANUP PENDING OCO ORDERS ---
        if 'oco_id' in trade:
            try:
                # If we are closing manually or by trailing stop, cancel the remote OCO first
                self.api.client.cancel_order_list(symbol=trade['symbol'], orderListId=trade['oco_id'])
                self.add_log(f"Cleanup: Pending OCO orders for {trade['symbol']} cancelled.")
            except Exception as e:
                self.add_log(f"OCO Cancellation Error: {str(e)}") 

        pnl = (price - trade['entry_price']) * trade['qty']
        pnl_pct = (price / trade['entry_price'] - 1) * 100
        
        self.add_log(f"TRADE CLOSED ({reason}): {trade['symbol']} @ {price} | PNL: ${pnl:.2f} ({pnl_pct:.2f}%)")
    
        # --- PROSOFT EXIT PROTOCOL: AGGRESSIVE LIQUIDATION ---
        # Liquidate if in auto mode OR if triggered manually via dashboard OR if it's an automated exit (SL/TP)
        if self.execution_mode == 'auto' or "MANUAL" in reason or reason in ["SL", "TP", "TRAILING STOP"]:
            try:
                asset = trade['symbol'].replace('USDT', '')
                self.add_log(f"🔄 EXIT PROTOCOL: Converting {asset} back to USDT...")
                
                # 1. Forceful Order Cleanup
                try:
                    # Fix: Use the correct method to cancel all open orders for the symbol
                    self.api.client._cancel_all_open_orders(symbol=trade['symbol'])
                    await asyncio.sleep(1.5) # Wait for Binance to update locked status
                except Exception as e:
                    # Fallback if the private/specific method fails
                    try:
                        open_orders = self.api.client.get_open_orders(symbol=trade['symbol'])
                        for oo in open_orders:
                            self.api.client.cancel_order(symbol=trade['symbol'], orderId=oo['orderId'])
                    except:
                        self.add_log(f"Exit Cleanup: {e}")
                
                # 2. Complete Liquidation
                actual_free_balance = self.api.get_account_balance(asset, include_locked=False)
                
                if actual_free_balance > 0:
                    current_ticker = self.api.get_symbol_ticker(trade['symbol'])
                    est_value = actual_free_balance * current_ticker
                    
                    if est_value >= 1.0: # Attempt liquidation if worth at least $1 (some allow $1, others $5/$10)
                        self.add_log(f"Liquidation: Selling {actual_free_balance:.6f} {asset} (~${est_value:.2f})")
                        sell_order = self.orders.place_market_sell(trade['symbol'], actual_free_balance)
                        
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
                            self.add_log(f"⚠️ LIQUIDATION REJECTED: {asset} (~${est_value:.2f}) is likely below Binance minimum ($5-$10).")
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

        # Log to Neural Memory for self-learning
        entry_t = trade.get('timestamp', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        exit_t = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.memory.log_trade(trade['symbol'], trade['side'], trade['entry_price'], price, entry_t, exit_t, pnl, trade['conf'], self.stats['market_health'], self.stats['sentiment'])
        
        # Update Daily Stats
        self.risk.update_performance(pnl_pct / 100)
        self.stats['daily_pnl'] += pnl
        
        # Reset Active Trade & Clear Local State
        self.active_trade = None
        self.stats['active_count'] = 0
        self.healer.clear_trade_state()
        
        # Notify Telegram
        try:
            color_emoji = "🟢" if pnl > 0 else "🔴"
            status_text = "Profitable / رابحة" if pnl > 0 else "Loss / خسارة"
            await self.telegram.send_message(
                f"{color_emoji} *Position Closed / إغلاق المركز*\n"
                f"Reason / السبب: `{reason}`\n"
                f"{trade['symbol']} | Exit: ${price:,.2f}\n"
                f"Status / الحالة: {status_text}\n"
                f"PNL: ${pnl:.2f} ({pnl_pct:.2f}%)"
            )
        except: pass

    async def protocol_omega(self):
        """🚨 PROTOCOL OMEGA: THE ULTIMATE KILL SWITCH 🚨
        Immediate Liquidation | Recall Funds | Full System Halt
        """
        self.add_log("🚨🚨🚨 PROTOCOL OMEGA ACTIVATED: INITIATING FULL LIQUIDATION 🚨🚨🚨")
        self.voice.alert_protocol_omega()
        self.voice.say("Protocol Omega engaged. Initiating emergency liquidation and fund recall sequence.")
        
        # 1. Stop all execution
        self.is_paused = True
        
        # 2. Close Active Trade if any
        if self.active_trade:
            # Get current price
            try:
                curr_p = self.api.get_symbol_ticker(self.active_trade['symbol'])
                await self.close_trade('SELL', curr_p, "PROTOCOL OMEGA / قفل احترازي")
            except: pass
            
        # 3. Cancel ALL Open Orders for ALL symbols (aggressive)
        try:
            self.api.client._cancel_all_open_orders() # Using semi-private or specific endpoint if supported
            self.add_log("Omega: All open orders on Binance cancelled.")
        except:
            self.add_log("Omega: Individual order cleanup triggered.")

        # 4. Recall Staked Assets (Yield Farming)
        try:
            self.add_log("Omega: Recalling funds from Yield Farming...")
            await self.farmer.recall_funds()
        except: pass
        
        # 5. Final Report
        await self.telegram.send_message("🚨 *PROTOCOL OMEGA EXECUTED*\nFull Liquidation Complete. Funds secured in USDT. System is currently PAUSED.")
        self.add_log("🚨 PROTOCOL OMEGA COMPLETE: System Paused.")

    def update_accuracy_stats(self):
        """Update the accuracy evolution history."""
        try:
            import datetime
            memories = self.memory.get_recent_memories(limit=20)
            if memories:
                wins = len([m for m in memories if m['profit_loss'] > 0])
                acc = (wins / len(memories)) * 100
                if not isinstance(self.stats['ai_accuracy_history'], list):
                    self.stats['ai_accuracy_history'] = []
                    
                self.stats['ai_accuracy_history'].append({
                    'time': datetime.datetime.now().strftime("%H:%M"),
                    'accuracy': round(acc, 2)
                })
                # Keep last 15 points
                if len(self.stats['ai_accuracy_history']) > 15:
                    self.stats['ai_accuracy_history'].pop(0)
        except Exception as e:
            app_logger.error(f"Accuracy Update Error: {e}")

    async def _check_daily_report(self):
        """Compiles and sends a high-level summary of all revenue streams at 23:00."""
        try:
            now = datetime.now()
            today_str = now.strftime("%Y-%m-%d")
            
            # Dispatch once per day when hour is 23 (11 PM)
            if self.last_report_date != today_str and now.hour >= 23:
                data = self.memory.get_daily_report_data()
                if not data: return
                
                self.last_report_date = today_str
                
                # Passive Income Processing
                rev_total = 0
                rev_lines = ""
                for r in data['revenue']:
                    rev_total += r['total']
                    src_map = {
                        "YieldFarmer": "🌾 Yield Farming (زراعة)", 
                        "ListingSniper": "🚀 Listing Sniper (قنص)", 
                        "FundingArb": "⚖️ Funding Arb (تحكيم)"
                    }
                    src_label = src_map.get(r['source'], r['source'])
                    rev_lines += f"🔹 {src_label}: `+${r['total']:.4f}`\n"
                
                # Trading Performance Processing
                trade_stats = data.get('trades', {})
                trade_pnl = trade_stats.get('total_pnl', 0) if trade_stats else 0
                win_count = trade_stats.get('wins', 0) if trade_stats else 0
                total_pos = trade_stats.get('count', 0) if trade_stats else 0
                win_rate = (win_count / total_pos * 100) if total_pos > 0 else 0
                
                # Aggregate
                total_day = rev_total + trade_pnl
                p_emoji = "💎" if total_day >= 0 else "📉"
                
                report = (
                    f"📊 *DAILY INTELLIGENCE SUMMARY / ملخص ذكاء اليوم*\n"
                    f"📅 *Date / التاريخ:* `{today_str}`\n\n"
                    f"--- 🍃 *PASSIVE REVENUE / الدخل الخامل* ---\n"
                    f"{rev_lines if rev_lines else 'No passive records / لا توجد سجلات.'}\n"
                    f"--- 💹 *TRADING ENGINE / آداء التداول* ---\n"
                    f"🔢 *Positions / اجمالي الصفقات:* `{total_pos}`\n"
                    f"🏆 *Win Rate / نسبة النجاح:* `{win_rate:.1f}%`\n"
                    f"💵 *Trade PNL / ربح التداول:* `${trade_pnl:+.2f}`\n\n"
                    f"{p_emoji} *TOTAL DAILY PROFIT / إجمالي الربح اليومي:* `{total_day:+.2f}$`\n\n"
                    f"🤖 *PROSOFT QUANTUM PRIME AI is securing your assets.*"
                )
                
                await self.telegram.send_message(report)
                self.add_log(f"Daily Intelligence Summary dispatched. Total: ${total_day:.2f}")
        except Exception as e:
            app_logger.error(f"Daily Report Thread Error: {e}")

    async def dispatch_intelligence_heartbeat(self):
        """Consolidated Dynamic Heartbeat: 10m during trades / 25m idle."""
        try:
            self.add_log("System Protocol: Dispatching Intelligence Heartbeat...")
            
            # 1. System Connectivity
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

            # 2. Position Status (The core request)
            if self.active_trade:
                t = self.active_trade
                pnl_pct = (self.stats['price'] / t['entry_price'] - 1) * 100
                color = "🟢" if pnl_pct > 0 else "🔴"
                report += (
                    f"📈 *ACTIVE POSITION / الصفقة الحالية*\n"
                    f"Asset: `{t['symbol']}`\n"
                    f"Entry: `${t['entry_price']:,.2f}` | PNL: {color} `{pnl_pct:+.2f}%`\n"
                    f"SL: `${t['sl']:,.2f}` | TP: `${t['tp']:,.2f}`\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                )
            else:
                report += "🔍 *STATUS:* Scanning for institutional entries... / جاري البحث عن سيولة مؤسسية...\n━━━━━━━━━━━━━━━━━━━━\n"

            # 3. AI Global Insight
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
        """AI-Driven Emergency Halt and Mass Exit."""
        self.voice.alert_protocol_omega()
        self.add_log(f"🚨 ALERT: PROTOCOL OMEGA ACTIVATED! Reason: {reason}")
        
        # 1. Close Active Trades immediately
        if self.active_trade:
            await self.close_trade('SELL', self.stats['price'], "OMEGA EXIT")
            
        # 2. Cancel all pending orders (Simulated for this implementation)
        self.stats['pending_signal'] = None
        
        # 3. Generate Institutional Warning via Gemini
        warning = "System Halted. Extreme High Risk detected."
        if self.gemini and self.gemini.model:
            p = f"Reason: {reason}. Current Symbol: {self.symbol}. Generate a high-priority institutional emergency warning for customers. (AR/EN)"
            warning = await self.gemini.ask(p)
            
        # 4. Notify Telegram
        await self.telegram.send_message(
            f"🚫 *PROTOCOL OMEGA ACTIVATED / تفعيل بروتوكول أوميغا* 🚫\n\n"
            f"⚠️ *Emergency Status:* HALTED / توقف اضطراري\n"
            f"🚩 *Incident / السبب:* {reason}\n\n"
            f"{warning}"
        )


if __name__ == "__main__":
    bot = TradingBot()
    asyncio.run(bot.run())
