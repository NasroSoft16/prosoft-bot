from flask import Flask, jsonify, request, send_file, session
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import threading
import time
import os
import json
import asyncio
import hashlib
from datetime import datetime
from src.utils.logger import app_logger

CREDENTIALS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'credentials.json')

def load_credentials():
    if os.path.exists(CREDENTIALS_FILE):
        with open(CREDENTIALS_FILE, 'r') as f:
            return json.load(f)
    # Default credentials
    return {'username': 'admin', 'password_hash': hashlib.sha256('prosoft2026'.encode()).hexdigest()}

def save_credentials(creds):
    with open(CREDENTIALS_FILE, 'w') as f:
        json.dump(creds, f)

from src.security.license_manager import LicenseManager

import sys

def get_resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

class DashboardAPI:
    def __init__(self, bot_instance):
        self.app = Flask(__name__)
        self.app.secret_key = 'quantum_prime_secure_nexus_2026' # Required for session persistence
        self.bot = bot_instance
        self.license = LicenseManager()
        CORS(self.app, supports_credentials=True) # Support session cookies
        # Explicitly use threading mode for maximum compatibility with the asyncio bot loop
        self.socketio = SocketIO(self.app, cors_allowed_origins="*", manage_session=True, async_mode='threading')
        self._setup_routes()
        self._start_background_emitter()

    def _start_background_emitter(self):
        """Starts a background thread to push periodic updates via Socket.IO."""
        def emit_loop():
            while True:
                try:
                    # Collect current status
                    status_data = {
                        'bot_stats': self.bot.stats,
                        'current_symbol': self.bot.symbol,
                        'active_trades': self.bot.active_trades, # List of all positions
                        'equity': self.bot.stats.get('total_equity', 0)
                    }
                    self.socketio.emit('status_update', status_data)
                    
                    # Push latest logs if any
                    if self.bot.logs:
                        latest_log = self.bot.logs[-1]
                        self.socketio.emit('new_log', latest_log)
                        
                except Exception as e:
                    app_logger.error(f"Socket Emitter Error: {e}")
                
                time.sleep(3) # Emit every 3 seconds
        
        thread = threading.Thread(target=emit_loop)
        thread.daemon = True
        thread.start()

    def _setup_routes(self):
        @self.app.route('/', methods=['GET'])
        def index():
            # Support both dev and single-EXE execution
            dash_path = get_resource_path('dashboard.html')
            if not os.path.exists(dash_path):
                # Fallback to local
                dash_path = os.path.abspath(os.path.join(os.getcwd(), 'dashboard.html'))
            return send_file(dash_path)

        @self.app.route('/mobile', methods=['GET'])
        def mobile():
            # Dedicated mobile view
            mob_path = get_resource_path('mobile.html')
            if not os.path.exists(mob_path):
                mob_path = os.path.abspath(os.path.join(os.getcwd(), 'mobile.html'))
            return send_file(mob_path)

        @self.app.route('/health', methods=['GET'])
        def health():
            return "OK", 200

        @self.app.route('/api/login', methods=['POST'])
        def login():
            data = request.json
            username = data.get('username', '')
            password = data.get('password', '')
            pw_hash = hashlib.sha256(password.encode()).hexdigest()
            creds = load_credentials()
            if username == creds['username'] and pw_hash == creds['password_hash']:
                session['authenticated'] = True
                self.bot.add_log(f"Security: User '{username}' authenticated successfully.")
                return jsonify({'status': 'success', 'message': 'Access Granted.'})
            return jsonify({'status': 'error', 'message': 'Invalid Credentials.'}), 401

        @self.app.route('/api/auth_check', methods=['GET'])
        def auth_check():
            if session.get('authenticated'):
                return jsonify({'authenticated': True})
            return jsonify({'authenticated': False}), 401

        @self.app.route('/api/change_password', methods=['POST'])
        def change_password():
            data = request.json
            current = data.get('current_password', '')
            new_pass = data.get('new_password', '')
            new_user = data.get('new_username', '')
            creds = load_credentials()
            curr_hash = hashlib.sha256(current.encode()).hexdigest()
            if curr_hash != creds['password_hash']:
                return jsonify({'status': 'error', 'message': 'Current password is incorrect.'}), 401
            if new_pass and len(new_pass) >= 4:
                creds['password_hash'] = hashlib.sha256(new_pass.encode()).hexdigest()
            if new_user:
                creds['username'] = new_user
            save_credentials(creds)
            self.bot.add_log("Security: Credentials updated successfully.")
            return jsonify({'status': 'success', 'message': 'Credentials updated.'})

        @self.app.route('/api/load_config', methods=['GET'])
        def load_config():
            """Load saved API keys from .env so user doesn't re-enter them."""
            return jsonify({
                'api_key': os.getenv('BINANCE_API_KEY', ''),
                'api_secret': os.getenv('BINANCE_API_SECRET', ''),
                'telegram_token': os.getenv('TELEGRAM_BOT_TOKEN', ''),
                'telegram_chat': os.getenv('TELEGRAM_CHAT_ID', ''),
                'gemini_key': os.getenv('GEMINI_API_KEY', ''),
                'execution_mode': os.getenv('EXECUTION_MODE', 'manual'),
                'voice_alerts': os.getenv('VOICE_ALERTS', 'on')
            })
            
        @self.app.route('/api/stats', methods=['GET'])
        def get_stats():
            # Inject current prices for all active trades to ensure accurate PNL in dashboard
            active_trades = []
            for t in self.bot.active_trades:
                try:
                    t_copy = t.copy()
                    ticker = self.bot.api.get_symbol_ticker(t['symbol'])
                    if ticker:
                        t_copy['current_price'] = ticker
                    active_trades.append(t_copy)
                except:
                    active_trades.append(t)

            return jsonify({
                'bot_stats': self.bot.stats,
                'current_symbol': self.bot.symbol,
                'active_trades': active_trades,
                'logs': list(self.bot.logs[-50:]),
                'historical_bars': self.bot.last_df.tail(60).to_dict('records') if hasattr(self.bot, 'last_df') and hasattr(self.bot.last_df, 'tail') else [],
                'gemini_cluster': self.bot.gemini.get_quota_info() if hasattr(self.bot, 'gemini') else [],
                'groq_cluster': self.bot.groq.get_quota_info() if hasattr(self.bot, 'groq') else []
            })

        @self.app.route('/api/accuracy', methods=['GET'])
        def get_accuracy():
            """Fetch AI Accuracy Evolution data."""
            history = self.bot.stats.get('ai_accuracy_history', [])
            return jsonify(history if isinstance(history, list) else [])

        @self.app.route('/api/omega', methods=['POST'])
        def trigger_omega():
            """Execute Protocol Omega Kill Switch."""
            self.bot.add_log("DASHBOARD: Manual Protocol Omega Signal Received.")
            # Run in separate thread to avoid blocking Flask
            threading.Thread(target=lambda: asyncio.run(self.bot.protocol_omega())).start()
            return jsonify({'status': 'success', 'message': 'PROTOCOL OMEGA ENGAGED.'})

        @self.app.route('/api/portfolio', methods=['GET'])
        def get_portfolio():
            summary = self.bot.portfolio.get_summary()
            return jsonify(summary)

        @self.app.route('/api/test_binance', methods=['POST'])
        def test_binance():
            data = request.json
            api_key = data.get('api_key')
            api_secret = data.get('api_secret')
            if not api_key or not api_secret:
                return jsonify({'status': 'error', 'message': 'Missing API keys'}), 400
            try:
                from binance.client import Client
                test_client = Client(api_key, api_secret, testnet=False)
                test_client.get_account()
                self.bot.add_log("System Protocol: Binance Gateway Connection TEST SUCCESSFUL.")
                return jsonify({'status': 'success', 'message': 'Connection Secure & Verified.'})
            except Exception as e:
                return jsonify({'status': 'error', 'message': str(e)}), 400

        @self.app.route('/api/test_telegram', methods=['POST'])
        def test_telegram():
            data = request.json
            tg_token = data.get('telegram_token')
            tg_chat = data.get('telegram_chat')
            if not tg_token or not tg_chat:
                return jsonify({'status': 'error', 'message': 'Missing Telegram Details'}), 400
            try:
                def send_test():
                    from telegram import Bot
                    import asyncio
                    test_bot = Bot(token=tg_token)
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(test_bot.send_message(chat_id=tg_chat, text="🔌 *PROSOFT QUANTUM PRIME* Test Connection Successful!", parse_mode='MARKDOWN'))
                    loop.close()
                threading.Thread(target=send_test).start()
                self.bot.add_log("System Protocol: Telegram Node Ping SENT.")
                return jsonify({'status': 'success', 'message': 'Ping Securely Sent.'})
            except Exception as e:
                return jsonify({'status': 'error', 'message': str(e)}), 400

        @self.app.route('/api/test_gemini', methods=['POST'])
        def test_gemini():
            """Test Gemini connection using Direct REST API (No SDK)."""
            import requests as http_req
            
            data = request.json
            raw_keys = data.get('gemini_key', '').strip()
            if not raw_keys:
                return jsonify({'status': 'error', 'message': 'Missing API Key'}), 400
            
            keys = [k.strip() for k in raw_keys.split(',') if k.strip()]
            results = []
            test_models = ['gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-2.0-flash-lite', 'gemini-1.5-flash']
            api_base = "https://generativelanguage.googleapis.com/v1beta/models"
            
            try:
                for i, key in enumerate(keys):
                    success = False
                    used_model = "NONE"
                    
                    for m_name in test_models:
                        try:
                            url = f"{api_base}/{m_name}:generateContent?key={key}"
                            payload = {
                                "contents": [{"parts": [{"text": "ping"}]}],
                                "generationConfig": {"maxOutputTokens": 5}
                            }
                            resp = http_req.post(url, json=payload, timeout=8)
                            if resp.status_code == 200:
                                success = True
                                used_model = m_name
                                break
                            elif resp.status_code == 404:
                                continue  # Try next model
                            elif resp.status_code == 429:
                                used_model = "LIMIT HIT"
                                break
                            else:
                                used_model = f"ERR {resp.status_code}"
                                break
                        except Exception as e: 
                            used_model = "TIMEOUT"
                            break
                    
                    if success:
                        results.append(f"Node {i+1}: {used_model}")
                    else:
                        if used_model in ["NONE", "TIMEOUT"]:
                            results.append(f"Node {i+1}: FAIL")
                        else:
                            results.append(f"Node {i+1}: {used_model}")
                
                summary = " | ".join(results)
                if any(not (r.endswith("FAIL") or r.endswith("ERR")) for r in results):
                    self.bot.add_log(f"AI Matrix: Cluster Verified (REST). {summary}")
                    return jsonify({'status': 'success', 'message': summary})
                
                return jsonify({'status': 'error', 'message': f"All Failed: {summary}"}), 400
            except Exception as e:
                return jsonify({'status': 'error', 'message': f"Critical: {str(e)[:25]}"}), 400

        @self.app.route('/api/config', methods=['POST'])
        def update_config():
            data = request.json
            api_key = data.get('api_key')
            api_secret = data.get('api_secret')
            tg_token = data.get('telegram_token')
            tg_chat = data.get('telegram_chat')
            gemini_key = data.get('gemini_key')
            
            self.bot.execution_mode = data.get('execution_mode', self.bot.execution_mode)
            self.bot.voice_alerts = data.get('voice_alerts', self.bot.voice_alerts)
            
            # Update .env file locally
            env_content = [
                f"BINANCE_API_KEY={api_key if api_key else os.getenv('BINANCE_API_KEY', '')}",
                f"BINANCE_API_SECRET={api_secret if api_secret else os.getenv('BINANCE_API_SECRET', '')}",
                f"TELEGRAM_BOT_TOKEN={tg_token if tg_token else os.getenv('TELEGRAM_BOT_TOKEN', '')}",
                f"TELEGRAM_CHAT_ID={tg_chat if tg_chat else os.getenv('TELEGRAM_CHAT_ID', '')}",
                f"GEMINI_API_KEY={gemini_key if gemini_key else os.getenv('GEMINI_API_KEY', '')}",
                f"SYMBOL={self.bot.symbol}",
                f"TIMEFRAME={self.bot.timeframe}",
                f"AI_CONFIDENCE_THRESHOLD={self.bot.ai_threshold}",
                f"EXECUTION_MODE={self.bot.execution_mode}",
                f"VOICE_ALERTS={'on' if self.bot.voice_alerts else 'off'}"
            ]
            with open(".env", "w") as f:
                f.write("\n".join(env_content) + "\n")
            
            # Update Bot runtime (CRITICAL FIX: Live-update clients)
            new_api = api_key or os.getenv('BINANCE_API_KEY')
            new_secret = api_secret or os.getenv('BINANCE_API_SECRET')
            if new_api and new_secret:
                self.bot.reconnect_binance(new_api, new_secret)

            new_token = tg_token or os.getenv('TELEGRAM_BOT_TOKEN')
            new_chat = tg_chat or os.getenv('TELEGRAM_CHAT_ID')
            if new_token and new_chat:
                self.bot.reconnect_telegram(new_token, new_chat)
            
            # Update Gemini if key provided
            new_gemini = gemini_key or os.getenv('GEMINI_API_KEY')
            if new_gemini and hasattr(self.bot, 'gemini'):
                os.environ['GEMINI_API_KEY'] = new_gemini
                self.bot.gemini.reload(new_gemini)
                self.bot.add_log("System Protocol: Gemini AI Engine Re-initialized.")
            
            self.bot.stats['execution_mode'] = self.bot.execution_mode
            self.bot.stats['voice_alerts'] = self.bot.voice_alerts
            
            self.bot.add_log(f"System Protocol: Configuration updated & Engines Reconnected.")
            return jsonify({'status': 'success', 'message': 'Configuration updated & Engines Reconnected.'})

        @self.app.route('/api/execute_manual', methods=['POST'])
        def execute_manual():
            pending = self.bot.stats.get('pending_signal')
            if pending:
                # Use a separate thread or async task to execute
                # For simplicity in this demo, we'll try to call the bot's execute_trade
                # Note: main loop is async, so we might need to handle this carefully
                threading.Thread(target=lambda: asyncio.run(self.bot.execute_trade(
                    pending['symbol'], pending['side'], pending['size'], 
                    pending['price'], pending['sl'], pending['tp'], 1.0
                ))).start()
                self.bot.stats['pending_signal'] = None
                return jsonify({'status': 'success', 'message': 'Manual Order Sent!'})
            return jsonify({'status': 'error', 'message': 'No pending signal.'}), 400

        @self.app.route('/api/close_trade', methods=['POST'])
        def close_trade():
            if not self.bot.active_trades:
                return jsonify({'status': 'error', 'message': 'No active trade to close.'}), 400
            
            data = request.json or {}
            symbol = data.get('symbol')
            if isinstance(symbol, dict): # Shield against JS event objects
                symbol = None
            
            def do_close():
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    # Pass the symbol if provided
                    loop.run_until_complete(self.bot.close_trade('SELL', self.bot.stats.get('price', 0), "MANUAL DASHBOARD", symbol=symbol))
                    loop.close()
                except Exception as e:
                    self.bot.add_log(f"Manual Close Error: {str(e)}")
            
            threading.Thread(target=do_close).start()
            return jsonify({'status': 'success', 'message': f"Manual exit signal sent {'for ' + symbol if symbol else ''}."})

        @self.app.route('/api/execute_arbitrage', methods=['POST'])
        def execute_arbitrage():
            """Phase 3: Real-time Arbitrage Execution."""
            data = request.json
            route_name = data.get('route_name')
            direction = data.get('direction')
            amount = data.get('amount') # Defaults to None, which triggers Max Balance logic
            
            if not route_name or not direction:
                return jsonify({'status': 'error', 'message': 'Missing parameters'}), 400
            
            self.bot.add_log(f"🔺 ARBITRAGE TRIGGER: Initiating {route_name} ({direction}) with ${amount}")
            
            def run_async_exec():
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                try:
                    res = new_loop.run_until_complete(self.bot.arbitrage.execute_arbitrage(route_name, direction, amount))
                    if res.get('success'):
                        self.bot.add_log(f"✅ ARBITRAGE SUCCESS: {route_name} (+{res.get('profit_pct', 0):.2f}%)")
                        new_loop.run_until_complete(self.bot.telegram.send_message(
                            f"✅ *MANUAL ARBITRAGE SUCCESS*\nRoute: {route_name}\nProfit: {res.get('profit_pct', 0):.3f}%"
                        ))
                    else:
                        error_msg = res.get('message', 'Unknown Error')
                        self.bot.add_log(f"❌ ARBITRAGE REJECTED: {error_msg}")
                except Exception as e:
                    self.bot.add_log(f"❌ ARBITRAGE THREAD ERROR: {str(e)}")
                    app_logger.error(f"API Arbitrage Thread Error: {e}")
                finally:
                    new_loop.close()

            threading.Thread(target=run_async_exec).start()
            return jsonify({'status': 'success', 'message': 'Arbitrage sequence engaged.'})

        @self.app.route('/api/sync', methods=['POST'])
        def manual_sync():
            """Triggers an immediate Deep Sync and Health Check."""
            try:
                # Run health check effectively calling deep_sync
                threading.Thread(target=lambda: asyncio.run(self.bot.healer.run_health_check())).start()
                self.bot.add_log("System Protocol: User-initiated Deep Sync sequence started.")
                return jsonify({'status': 'success', 'message': 'Deep Sync Initiated.'})
            except Exception as e:
                return jsonify({'status': 'error', 'message': str(e)}), 500

        @self.app.route('/api/convert_dust', methods=['POST'])
        def convert_dust():
            """Phase 3: Dust-to-Gold Conversion."""
            try:
                balances = self.bot.api.get_all_balances()
                ticker_prices = {}
                dust_assets = []
                liquidated_count = 0
                errors = []
                for b in balances:
                    asset = b['asset']
                    if asset in ['USDT', 'BNB']: continue
                    
                    qty = float(b['free'])
                    if qty <= 0.000001: continue
                    
                    # Estimate value in USDT
                    val = 0
                    try:
                        p = self.bot.api.get_symbol_ticker(f"{asset}USDT")
                        if not p:
                            # Fallback to BTC then BNB to estimate value
                            p_btc = self.bot.api.get_symbol_ticker(f"{asset}BTC")
                            btc_usdt = self.bot.api.get_symbol_ticker("BTCUSDT")
                            if p_btc and btc_usdt:
                                p = p_btc * btc_usdt
                        
                        if p:
                            val = qty * p
                            ticker_prices[asset] = p
                    except: pass
                    
                    # Decision Logic:
                    # 1. If > $10, try to SELL for USDT directly
                    if val >= 10.0:
                        try:
                            # Use OrderManager to sell
                            from src.execution.order_manager import OrderManager
                            om = OrderManager(self.bot.api)
                            res = om.create_market_order(f"{asset}USDT", "SELL", qty)
                            if res: liquidated_count += 1
                        except Exception as sell_err:
                            errors.append(f"Sell {asset}: {str(sell_err)}")
                    
                    # 2. If < $10 or No USDT pair found, mark as DUST for BNB conversion
                    else:
                        dust_assets.append(asset)
                
                msg_parts = []
                if liquidated_count > 0:
                    msg_parts.append(f"Liquidated {liquidated_count} assets to USDT.")
                
                if dust_assets:
                    try:
                        # Convert to BNB
                        success = self.bot.api.convert_dust_to_bnb(dust_assets)
                        if success:
                            msg_parts.append(f"Converted {len(dust_assets)} small assets to BNB.")
                        else:
                            msg_parts.append(f"Failed to convert {len(dust_assets)} assets to BNB.")
                    except Exception as dust_err:
                        errors.append(f"Dust Error: {str(dust_err)}")
                
                if not msg_parts and not errors:
                    return jsonify({'status': 'info', 'message': 'No assets found for liquidation.'})
                
                final_msg = " | ".join(msg_parts)
                if errors:
                    final_msg += " (Note: " + ", ".join(errors)[:100] + ")"
                
                return jsonify({'status': 'success', 'message': final_msg})
            except Exception as e:
                app_logger.error(f"Liquidation Error: {e}")
                return jsonify({'status': 'error', 'message': f"Liquidation Failed: {str(e)}"}), 500

        @self.app.route('/api/test_report', methods=['POST'])
        def test_report():
            try:
                self.bot.add_log("System Protocol: User requested manual test report...")
                report_path = self.bot.reporter.generate_daily_report(self.bot.stats, self.bot.logs)
                
                def send_async():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(self.bot.telegram.send_document(
                        report_path, 
                        "PROSOFT QUANTUM PRIME - Daily Intel Report"
                    ))
                    loop.close()
                
                threading.Thread(target=send_async).start()
                return jsonify({'status': 'success', 'message': 'Report generated and sending to Telegram...'})
            except Exception as e:
                return jsonify({'status': 'error', 'message': str(e)}), 500

        @self.app.route('/api/download_report')
        def download_report():
            """Generate and download PDF report directly from browser."""
            try:
                report_path = self.bot.reporter.generate_daily_report(self.bot.stats, self.bot.logs)
                return send_file(report_path, as_attachment=True, download_name=os.path.basename(report_path))
            except Exception as e:
                return jsonify({'status': 'error', 'message': str(e)}), 500

        @self.app.route('/api/download_brain')
        def download_brain():
            """Precision neural backup using the bot's live memory path."""
            try:
                import os
                # Priority 1: Use the path the bot is actually using
                target_path = getattr(self.bot.memory, 'db_path', None)
                
                # Priority 2: Standard fallbacks
                if not target_path or not os.path.exists(target_path):
                    possible_paths = [
                        os.path.join(os.getcwd(), 'brain.db'),
                        os.path.join(os.getcwd(), 'data', 'brain.db'),
                        '/data/brain.db', # Confirmed from User Image
                        '/app/data/brain.db'
                    ]
                    for path in possible_paths:
                        if os.path.exists(path):
                            target_path = path
                            break
                
                if target_path and os.path.exists(target_path):
                    return send_file(target_path, as_attachment=True, download_name=f"PROSOFT_BRAIN_BACKUP_{datetime.now().strftime('%Y%m%d')}.db")
                
                return jsonify({"status": "error", "message": f"Neural Core not found at {target_path if target_path else 'standard paths'}"}), 404
            except Exception as e:
                return jsonify({"status": "error", "message": str(e)}), 500

        @self.app.route('/api/scanner', methods=['GET'])
        def get_scanner():
            # Use cached results from main loop
            return jsonify(self.bot.stats.get('top_gems', []))

        @self.app.route('/api/analytics', methods=['GET'])
        def get_analytics():
            """Phase 6: Performance Analytics Suite."""
            try:
                history = self.bot.memory.get_recent_memories(limit=100)
                if not history:
                    return jsonify({'win_rate': 0, 'total': 0, 'history': []})
                
                wins = len([t for t in history if t['profit_loss'] > 0])
                total = len(history)
                win_rate = (wins / total) * 100 if total > 0 else 0
                
                return jsonify({
                    'win_rate': round(win_rate, 2),
                    'total_trades': total,
                    'history': history,
                    'avg_pn_l': round(sum(t['profit_loss'] for t in history) / total, 2) if total > 0 else 0
                })
            except Exception as e:
                return jsonify({'status': 'error', 'message': str(e)}), 500

        @self.app.route('/api/switch_symbol', methods=['POST'])
        def switch_symbol():
            try:
                data = request.json
                new_symbol = data.get('symbol', '').upper()
                if not new_symbol:
                    return jsonify({'status': 'error', 'message': 'Symbol required'}), 400
                
                # Update .env for persistence
                env_path = ".env"
                env_content = []
                if os.path.exists(env_path):
                    with open(env_path, "r") as f:
                        lines = f.readlines()
                        found = False
                        for line in lines:
                            if line.startswith("SYMBOL="):
                                env_content.append(f"SYMBOL={new_symbol}\n")
                                found = True
                            else:
                                env_content.append(line)
                        if not found:
                            env_content.append(f"SYMBOL={new_symbol}\n")
                else:
                    env_content = [f"SYMBOL={new_symbol}\n"]
                
                try:
                    with open(env_path, "w") as f:
                        f.writelines(env_content)
                except Exception as env_err:
                    app_logger.warning(f"Could not update .env file: {str(env_err)}")
                
                self.bot.switch_symbol(new_symbol)
                return jsonify({'status': 'success', 'message': f'Switched to {new_symbol}'})
            except Exception as e:
                app_logger.error(f"Switch Symbol API Error: {str(e)}")
                return jsonify({'status': 'error', 'message': str(e)}), 500

        @self.app.route('/api/license_status', methods=['GET'])
        def license_status():
            is_active, days_left, hwid = self.license.check_license_status()
            return jsonify({
                'is_active': is_active,
                'days_left': days_left,
                'hwid': hwid
            })

        @self.app.route('/api/activate', methods=['POST'])
        def activate_license():
            data = request.json
            key = data.get('license_key')
            success, msg = self.license.activate(key)
            return jsonify({'status': 'success' if success else 'error', 'message': msg})

        @self.app.route('/api/memory', methods=['GET'])
        def get_memory():
            """Fetch the system's neural memory for the Subconscious Dashboard."""
            if hasattr(self.bot, 'memory'):
                memories = self.bot.memory.get_recent_memories(limit=1000)
                app_logger.info(f"🧠 [DASHBOARD API] Memory Fetch: Found {len(memories)} records in {self.bot.memory.db_path}")
                return jsonify(memories)
            app_logger.warning("🧠 [DASHBOARD API] Memory Fetch Failed: Bot has no memory attribute.")
            return jsonify([])

        @self.app.route('/api/maintenance/wipe', methods=['POST'])
        def wipe_database():
            """Hard-reset the database history (Trade & Revenue memory)."""
            try:
                import sqlite3
                conn = sqlite3.connect(self.bot.memory.db_path)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM trade_memory")
                cursor.execute("DELETE FROM revenue_memory")
                cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('trade_memory', 'revenue_memory')")
                conn.commit()
                conn.close()
                return jsonify({'status': 'success'})
            except Exception as e:
                return jsonify({'status': 'error', 'message': str(e)}), 500

        @self.app.route('/api/maintenance/clear_trades', methods=['POST'])
        def clear_active_trades():
            """Wipe all active trade trackers (doesn't sell them, just clears the UI/memory)."""
            try:
                self.bot.active_trades = []
                self.bot.healer.clear_trade_state()
                self.bot.add_log("🛠️ SYSTEM: All active trade trackers have been manually cleared.")
                return jsonify({'status': 'success'})
            except Exception as e:
                return jsonify({'status': 'error', 'message': str(e)}), 500

        @self.app.route('/api/maintenance/delete_trade', methods=['POST'])
        def delete_active_trade():
            """Delete a specific trade from trackers by symbol."""
            try:
                data = request.get_json()
                symbol = data.get('symbol')
                if not symbol:
                    return jsonify({'status': 'error', 'message': 'Symbol required.'}), 400
                
                initial_count = len(self.bot.active_trades)
                self.bot.active_trades = [t for t in self.bot.active_trades if t.get('symbol') != symbol]
                
                if len(self.bot.active_trades) < initial_count:
                    self.bot.healer.save_trade_state(self.bot.active_trades)
                    self.bot.add_log(f"🛠️ SYSTEM: Trade tracker for {symbol} has been manually removed.")
                    return jsonify({'status': 'success'})
                return jsonify({'status': 'error', 'message': 'Trade not found.'}), 404
            except Exception as e:
                return jsonify({'status': 'error', 'message': str(e)}), 500

        @self.app.route('/api/accuracy_chart', methods=['GET'])
        def get_accuracy_chart():
            """Returns cumulative performance progress for the dashboard chart."""
            try:
                if not hasattr(self.bot, 'memory'):
                    return jsonify([])
                # Fetch order by ID ascending to build cumulative sum over time
                # We'll fetch the last 20 trades
                import sqlite3
                import pandas as pd
                conn = sqlite3.connect(self.bot.memory.db_path)
                df = pd.read_sql_query("SELECT exit_time, profit_loss FROM trade_memory ORDER BY id DESC LIMIT 100", conn)
                conn.close()
                
                if df.empty:
                    return jsonify([])
                
                # Reverse to chronological order
                df = df.iloc[::-1].reset_index(drop=True)
                
                # Calculate Cumulative PNL
                df['cumulative_pnl'] = df['profit_loss'].cumsum()
                
                history = []
                for _, row in df.iterrows():
                    time_str = str(row['exit_time']).split(' ')[1][:5] if ' ' in str(row['exit_time']) else str(row['exit_time'])
                    history.append({
                        'time': time_str,
                        'accuracy': round(row['cumulative_pnl'], 2)
                    })
                return jsonify(history)
            except Exception as e:
                app_logger.error(f"Accuracy Chart API Error: {str(e)}")
                return jsonify([])

        @self.app.route('/api/maintenance/delete_record', methods=['POST'])
        def delete_specific_record():
            """Delete a single specific record by ID and table name."""
            try:
                data = request.get_json()
                table = data.get('table') # 'trade_memory' or 'revenue_memory'
                row_id = data.get('id')

                if table not in ['trade_memory', 'revenue_memory']:
                    return jsonify({'status': 'error', 'message': 'Invalid table source.'}), 400

                import sqlite3
                conn = sqlite3.connect(self.bot.memory.db_path)
                cursor = conn.cursor()
                cursor.execute(f"DELETE FROM {table} WHERE id = ?", (row_id,))
                conn.commit()
                conn.close()
                
                self.bot.add_log(f"🛠️ SYSTEM: Specific {table} record (ID: {row_id}) manually pruned.")
                return jsonify({'status': 'success', 'message': f'Record {row_id} deleted.'})
            except Exception as e:
                return jsonify({'status': 'error', 'message': str(e)}), 500

        @self.app.route('/api/revenue', methods=['GET'])
        def get_revenue():
            """Fetch the revenue stream history."""
            if hasattr(self.bot, 'memory'):
                revenue = self.bot.memory.get_revenue_history(limit=20)
                return jsonify(revenue)
            return jsonify([])

        @self.app.route('/api/chat', methods=['POST'])
        def chat_with_ai():
            """Chat with AI assistant - Gemini-powered with fallback."""
            try:
                data = request.json
                user_msg = data.get('message', '')
                self.bot.add_log(f"AI Matrix: Processing user query...")
                
                # Try Gemini AI first
                if hasattr(self.bot, 'gemini') and self.bot.gemini.model:
                    market_ctx = {
                        'symbol': self.bot.symbol,
                        'price': self.bot.stats.get('price', 0),
                        'ai_conf': self.bot.stats.get('ai_conf', 0),
                        'rsi': self.bot.stats.get('rsi', 50),
                        'market_health': self.bot.stats.get('market_health', 50),
                        'sentiment': self.bot.stats.get('sentiment', 'N/A'),
                        'prediction': self.bot.stats.get('prediction', 'N/A'),
                        'total_equity': self.bot.stats.get('total_equity', 0),
                    }
                    # Run the async Gemini call safely
                    import asyncio
                    try:
                        # Shared helper for async execution in sync Flask
                        def run_async(coro):
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            try:
                                return loop.run_until_complete(coro)
                            finally:
                                loop.close()

                        import threading
                        from concurrent.futures import ThreadPoolExecutor
                        
                        with ThreadPoolExecutor() as executor:
                            future = executor.submit(run_async, self.bot.gemini.ask(user_msg, market_ctx))
                            gemini_response = future.result(timeout=15.0) # 15s absolute timeout
                    except Exception as ai_err:
                        self.bot.add_log(f"AI Chat Engine Error: {str(ai_err)}")
                        gemini_response = None
                    
                    if gemini_response:
                        return jsonify({'response': gemini_response, 'engine': 'gemini'})
                
                # Fallback to rule-based
                response = self._get_ai_response(user_msg)
                return jsonify({'response': response, 'engine': 'local'})
            except Exception as e:
                self.bot.add_log(f"Chat Error: {str(e)}")
                return jsonify({'response': "I encountered a neural hiccup. Please try again."}), 500

        @self.app.route('/api/analyze_image', methods=['POST'])
        def analyze_image():
            """Analyze a chart image using Gemini Vision."""
            try:
                if 'image' not in request.files:
                    return jsonify({'response': 'No image uploaded.'}), 400
                
                file = request.files['image']
                image_bytes = file.read()
                question = request.form.get('question', 'Analyze this crypto chart.')
                
                if hasattr(self.bot, 'gemini') and self.bot.gemini.model:
                    result = self.bot.gemini.analyze_image(image_bytes, question)
                    return jsonify({'response': result})
                else:
                    return jsonify({'response': 'Gemini AI not configured. Add your API key in Protocols to enable image analysis.'}), 400
            except Exception as e:
                return jsonify({'response': f'Error: {str(e)}'}), 500

        @self.app.route('/api/reboot', methods=['POST'])
        def reboot_bot():
            """Gracefully exit and let the supervisor restart the process."""
            self.bot.add_log("SYSTEM: Remote Reboot Signal Received. Shutting down...")
            def shutdown():
                time.sleep(2)
                os._exit(0)
            threading.Thread(target=shutdown).start()
            return jsonify({'status': 'success', 'message': 'Rebooting system...'})

        @self.app.route('/api/scan_now', methods=['POST'])
        def trigger_scan():
            """Triggers an immediate market scanning cycle."""
            self.bot.add_log("SYSTEM: Manual Market Scan Triggered.")
            threading.Thread(target=lambda: asyncio.run(self.bot.market_scanner.scan_market())).start()
            return jsonify({'status': 'success', 'message': 'Scanning initiated...'})

    def _get_ai_response(self, query):
        """Quantum Neural Reasoning: High-level interactive strategist."""
        q = query.lower()
        is_ar = any(char in 'ابتثجحخدذرزسشصضطظعغفقكلمنهوي' for char in query)
        
        # Market Context Variables
        price = self.bot.stats.get('price', 0)
        health = self.bot.stats.get('market_health', 50)
        sentiment = self.bot.stats.get('sentiment', 'Neutral')
        sym = self.bot.symbol
        top_gems = self.bot.stats.get('top_gems') or []
        
        # 1. Trading Recommendations / Suggestions
        if any(w in q for w in ["suggest", "trade", "buy", "توصية", "صفقة", "شراء", "انصح"]):
            if top_gems:
                best = top_gems[0]
                if is_ar:
                    return (f"أهلاً بك يا صديقي. بصفتي شريكك الاستراتيجي، راقبت السوق بدقة وأرى أن {best['symbol']} هي الجوهرة الأبرز حالياً. "
                            f"سعرها الآن {best['price']:.4f} مع مؤشر ثقة قوي يصل إلى {best['score']}%. "
                            f"السيولة تتدفق بشكل مؤسسي، مما يجعلها صفقة ذات احتمالية عالية جداً. هل ترغب في أن أعمق لك التحليل الفني لهذا المسار؟")
                return (f"Welcome to the high-stakes game. I've been monitoring the pulse, and {best['symbol']} is showing a rare institutional alignment. "
                        f"At ${best['price']:.4f}, my neural score is {best['score']}%. The order flow bias is strong. "
                        f"This isn't just a trade; it's a strategic entry. Shall we dive deeper into the volume profile?")

        # 2. Detailed Market Analysis Requests
        if any(w in q for w in ["report", "analyze", "tech", "وضع", "تحليل", "خبرني"]):
            trend = "صاعد وقوي" if health > 60 else "عرضي متذبذب" if health > 40 else "هابط وخطير"
            if is_ar:
                return (f"إليك رؤيتي العميقة لوضع {sym} حالياً: السعر مستقر عند ${price:,.2f}، وصحة المسار الفني تبلغ {health:.1f}% وهو ما أعتبره مساراً {trend}. "
                        f"المعنويات العامة هي {sentiment}. لاحظت تحركات 'حيتان' في الخلفية توحي بتجميع سيولة. "
                        f"بصفتي خبيرك الخاص، أنصحك بالتركيز على مستويات الـ RSI الحالية ({self.bot.stats.get('rsi', 50):.1f}) لأنها مفتاح الحركة القادمة.")
            return (f"Here is my deep strategic breakdown for {sym}: We are hovering at ${price:,.2f} with a neural health of {health:.1f}%. "
                    f"The market regime is currently {sentiment}. I'm seeing significant hidden liquidity clusters on the order book. "
                    f"In my professional view, you should watch this space closely as a secondary expansion is brewing. Ready for more data?")

        # 3. Scanner / Opportunities
        if any(w in q for w in ["scan", "gems", "opportunities", "فرص", "عملات"]):
            if top_gems:
                gem_text = "\n".join([f"• {g['symbol']} (قوة {g['score']}%)" if is_ar else f"• {g['symbol']} (Score: {g['score']}%)" for g in top_gems[:4]])
                if is_ar:
                    return f"لقد قمت بمسح آلاف البيانات اللحظية، وهذه هي الفرص التي 'تصرخ' بالربح الآن:\n{gem_text}\nأي واحدة منها تثير اهتمامك لأعطيك تفاصيل دخولها؟"
                return f"My scanners are red hot. These candidates are showing prime institutional setups:\n{gem_text}\nWhich one of these gems would you like a full risk-assessment for?"

        # 4. Human-like Default interaction (The "Warmth" factor)
        if is_ar:
            return ("أنا هنا معك، أراقب كل نبضة في السوق كأنها نبضاتي. أنت لا تتعامل مع مجرد 'بوت'، "
                    "بل مع محرك ذكاء اصطناعي مصمم لنجاحك. اسألني عن أي عملة، أو اطلب مني تحليل وضع السوق، "
                    "وسأعطيك خلاصة الخبرة المؤسسية بوضوح تام.")
        return ("I'm right here with you, tracking every tick and order flow like it's my own pulse. "
                "Think of me not as a bot, but as your senior tactical advisor. Ask me for a specific symbol, "
                "a technical breakdown, or the overall market health, and I'll give you a masterclass in trading intel.")

    def run(self, host='0.0.0.0', port=None):
        """Starts the Flask-SocketIO server in a way that works locally and on Railway."""
        try:
            # FORCE Port 5000 to strictly match the user's Railway Networking settings
            if port is None:
                port = 5000
            
            app_logger.info(f"🚀 INITIALIZING DASHBOARD ON PORT: {port}")
            
            # Use threading mode for maximum compatibility with the bot's asyncio loop
            def start_server():
                try:
                    # Explicitly set async_mode to threading to avoid library conflicts on Railway
                    self.socketio.async_mode = 'threading'
                    # allow_unsafe_werkzeug is REQUIRED on Railway for background thread execution
                    self.socketio.run(self.app, host=host, port=port, debug=False, use_reloader=False, allow_unsafe_werkzeug=True)
                except Exception as e:
                    app_logger.critical(f"❌ DASHBOARD CRITICAL FAILURE: {str(e)}")

            thread = threading.Thread(target=start_server, daemon=True)
            thread.start()
            
            app_logger.info(f"✅ DASHBOARD LIVE AT: http://{host}:{port} (Mode: Threading)")
            
        except Exception as e:
            app_logger.error(f"❌ Error during Dashboard startup: {str(e)}")
