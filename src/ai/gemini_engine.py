import os
import asyncio
import time
import warnings
from src.utils.logger import app_logger

# Suppress technical noise for a cleaner institutional startup
warnings.filterwarnings("ignore", category=FutureWarning)

class GeminiAI:
    """PROSOFT AI: Quantum Multi-Node Gemini Cluster for Continuous Intelligence."""
    
    def __init__(self):
        self.raw_keys = os.getenv('GEMINI_API_KEY', '')
        self.api_keys = [k.strip() for k in self.raw_keys.split(',') if k.strip()]
        self.current_key_idx = 0
        self.models = {}  # Cache models for each key
        self.usage_stats = {key: {'requests': 0, 'errors': 0, 'limit_hit': False, 'last_success': 0} for key in self.api_keys}
        self.model_name = 'gemini-1.5-flash-latest' # Optimal for fast trading analysis
        self.model = True # Compatibility flag for dashboard checks
        self._initialize_all()
    
    def _initialize_all(self):
        if not self.api_keys:
            app_logger.warning("No Gemini API Keys detected. AI will operate in fallback mode.")
            return

        try:
            import google.generativeai as genai
            for key in self.api_keys:
                try:
                    # We don't configure globally here to allow per-call or per-instance keys if needed,
                    # but the SDK mostly uses global config. We'll use a wrapper approach.
                    self.models[key] = genai.GenerativeModel(self.model_name)
                except Exception as e:
                    app_logger.error(f"Error prepping node for key {key[:8]}...: {e}")
            
            app_logger.info(f"🚀 [AI CLUSTER] Initialized {len(self.models)} intelligence nodes.")
        except ImportError:
            app_logger.warning("google-generativeai not installed.")

    def reload(self, raw_keys):
        """Reload with a new set of API keys."""
        self.raw_keys = raw_keys
        self.api_keys = [k.strip() for k in self.raw_keys.split(',') if k.strip()]
        self.current_key_idx = 0
        self.models = {}
        self.usage_stats = {key: {'requests': 0, 'errors': 0, 'limit_hit': False, 'last_success': 0} for key in self.api_keys}
        self._initialize_all()

    def get_active_key(self):
        if not self.api_keys: return None
        return self.api_keys[self.current_key_idx]

    def rotate_key(self):
        if len(self.api_keys) <= 1: return False
        self.current_key_idx = (self.current_key_idx + 1) % len(self.api_keys)
        app_logger.info(f"🔄 [AI CLUSTER] Rotating to Node {self.current_key_idx + 1}/{len(self.api_keys)}")
        return True

    def get_quota_info(self):
        """Calculate estimated usage for dashboard."""
        if not self.api_keys: return []
        info = []
        for i, key in enumerate(self.api_keys):
            stats = self.usage_stats.get(key, {})
            # Free tier usually has 15-20 RPM or 1500 RPD. We'll estimate based on usage.
            info.append({
                'id': i + 1,
                'status': 'LIMIT HIT' if stats.get('limit_hit') else 'ONLINE',
                'requests': stats.get('requests', 0),
                'active': i == self.current_key_idx
            })
        return info

    async def ask(self, question, market_context=None):
        """Ask Gemini with automatic key rotation on 429."""
        import google.generativeai as genai
        
        tries = 0
        max_tries = len(self.api_keys) if self.api_keys else 1
        
        while tries < max_tries:
            active_key = self.get_active_key()
            if not active_key: return None
            
            try:
                genai.configure(api_key=active_key)
                model = self.models.get(active_key) or genai.GenerativeModel(self.model_name)
                
                # Build prompt
                if market_context:
                    system_prompt = (
                        "You are PROSOFT AI, a highly sophisticated institutional trading partner and neural strategist. "
                        "Your goal is to provide deep, clear, and human-like insights that inspire confidence. "
                        "Do not be robotic or overly brief; instead, offer sophisticated reasoning as if you are a professional mentor. "
                        "CRITICAL: Detect the user's language. If the user asks in Arabic, reply in a warm, clear, and professional Arabic tone. "
                        "If in English, provide a refined institutional perspective. Be more than a bot; be a strategist."
                    )
                    ctx = f"\nMarket Context: Asset={market_context.get('symbol')}, Price=${market_context.get('price')}, AI Confidence={market_context.get('ai_conf')}%, Market Health={market_context.get('market_health')}%"
                    full_prompt = f"{system_prompt}{ctx}\n\nUser Question: {question}"
                else:
                    full_prompt = f"Detect user language and reply in it. User: {question}"

                # Track usage
                self.usage_stats[active_key]['requests'] += 1
                
                response = await asyncio.to_thread(
                    model.generate_content,
                    full_prompt,
                    request_options={"timeout": 12.0}
                )
                
                if response and hasattr(response, 'text'):
                    self.usage_stats[active_key]['limit_hit'] = False
                    self.usage_stats[active_key]['last_success'] = time.time()
                    return response.text.strip()
                
                return None

            except Exception as e:
                err_str = str(e)
                if "429" in err_str or "quota" in err_str.lower():
                    app_logger.warning(f"⚠️ [AI CLUSTER] Node {self.current_key_idx + 1} Quota hit. Rotating...")
                    self.usage_stats[active_key]['limit_hit'] = True
                    if not self.rotate_key(): break # Only 1 key
                    tries += 1
                else:
                    app_logger.error(f"Gemini Node {self.current_key_idx + 1} Error: {e}")
                    self.usage_stats[active_key]['errors'] += 1
                    break 
        
        return None

    def analyze_image(self, image_bytes, question="Analyze this chart."):
        """Synchronous version for dashboard uploads."""
        import google.generativeai as genai
        active_key = self.get_active_key()
        if not active_key: return "No API Key"
        
        try:
            genai.configure(api_key=active_key)
            model = genai.GenerativeModel(self.model_name)
            image_part = {"mime_type": "image/png", "data": image_bytes}
            response = model.generate_content([question, image_part])
            return response.text
        except Exception as e:
            return f"Cluster Error: {e}"

