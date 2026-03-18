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
        self.models = {}
        # TRACKING: Using index-based stats to ensure isolation
        self.usage_stats = {i: {'requests': 0, 'errors': 0, 'limit_hit': False, 'last_success': 0, 'session_reqs': 0} for i in range(len(self.api_keys))}
        self.model_name = 'gemini-1.5-flash-latest'
        self.model = True # Dashboard flag
        self.lock = asyncio.Lock() # Protect against parallel scatter
        self.node_saturation_threshold = 25 # Move to next node after X requests for orderly dash
        self._initialize_all()
    
    def _initialize_all(self):
        if not self.api_keys:
            app_logger.warning("No Gemini API Keys detected. AI will operate in fallback mode.")
            return
        
        try:
            # Mask keys for logging to help user verify diversity
            for i, key in enumerate(self.api_keys):
                masked = f"{key[:4]}...{key[-4:]}"
                app_logger.info(f"🔑 [AI CLUSTER] Node {i+1} Ready: ID {masked}")
            app_logger.info(f"🚀 [AI CLUSTER] Initialized {len(self.api_keys)} nodes (SEQUENTIAL PULSE MODE).")
        except: pass

    def reload(self, raw_keys):
        """Reload system with new keys."""
        self.raw_keys = raw_keys
        self.api_keys = [k.strip() for k in self.raw_keys.split(',') if k.strip()]
        self.current_key_idx = 0
        self.usage_stats = {i: {'requests': 0, 'errors': 0, 'limit_hit': False, 'last_success': 0, 'session_reqs': 0} for i in range(len(self.api_keys))}
        self._initialize_all()

    def get_active_key(self):
        if not self.api_keys: return None
        return self.api_keys[self.current_key_idx]

    def rotate_key(self, force=True):
        """Rotate to next node. If not 'force', will only happen if saturated."""
        if len(self.api_keys) <= 1: return False
        
        idx = self.current_key_idx
        # Reset current session count on rotation
        self.usage_stats[idx]['session_reqs'] = 0
        
        # Move to next
        self.current_key_idx = (self.current_key_idx + 1) % len(self.api_keys)
        app_logger.info(f"🔄 [AI CLUSTER] Pulse Shift: Moving to Node {self.current_key_idx + 1}/{len(self.api_keys)}")
        return True

    def get_quota_info(self):
        """Dashboard data feed."""
        if not self.api_keys: return []
        info = []
        for i in range(len(self.api_keys)):
            stats = self.usage_stats.get(i, {})
            info.append({
                'id': i + 1,
                'status': 'LIMIT HIT' if stats.get('limit_hit') else 'ONLINE',
                'requests': stats.get('requests', 0),
                'active': i == self.current_key_idx
            })
        return info

    async def ask(self, question, market_context=None):
        """Ask Gemini with Sequential Pulse strategy (User Request)."""
        import google.generativeai as genai
        
        fallback_models = [self.model_name, 'gemini-1.5-flash-latest', 'gemini-1.5-pro-latest', 'gemini-1.5-flash', 'gemini-1.5-pro']
        fallback_models = list(dict.fromkeys(fallback_models))

        tries = 0
        max_tries = len(self.api_keys) if self.api_keys else 1
        
        while tries < max_tries:
            async with self.lock:
                idx = self.current_key_idx
                # CHECK: IF current node saturated, move pulse to next BEFORE starting
                if self.usage_stats[idx]['session_reqs'] >= self.node_saturation_threshold:
                    app_logger.info(f"📢 [AI CLUSTER] Node {idx+1} saturated ({self.node_saturation_threshold} reqs). Shifting...")
                    self.rotate_key(force=True)
                    idx = self.current_key_idx
                
                active_key = self.api_keys[idx]
            
            try:
                genai.configure(api_key=active_key)
                response = None
                
                # Model selection loop
                for m_name in fallback_models:
                    try:
                        model = genai.GenerativeModel(m_name)
                        
                        prompt = question
                        if market_context:
                            system_prompt = "You are PROSOFT AI Senior Strategist. Reply in user's language (AR/EN)."
                            prompt = f"{system_prompt}\nContext: {market_context}\nQ: {question}"

                        # ATOMIC TRACKING
                        self.usage_stats[idx]['requests'] += 1
                        self.usage_stats[idx]['session_reqs'] += 1
                        
                        response = await asyncio.to_thread(
                            model.generate_content,
                            prompt,
                            request_options={"timeout": 12.0}
                        )
                        if response:
                            if self.model_name != m_name: self.model_name = m_name
                            break
                    except Exception as e:
                        if "404" in str(e) or "not found" in str(e).lower(): continue
                        raise e

                if response and hasattr(response, 'text'):
                    self.usage_stats[idx]['limit_hit'] = False
                    self.usage_stats[idx]['last_success'] = time.time()
                    return response.text.strip()
                
                # If empty, rotate immediately
                async with self.lock: self.rotate_key(force=True)
                tries += 1

            except Exception as e:
                err_str = str(e)
                async with self.lock:
                    if "429" in err_str or "quota" in err_str.lower():
                        app_logger.warning(f"⚠️ [AI CLUSTER] Node {self.current_key_idx + 1} Limit. Shifting...")
                        self.usage_stats[self.current_key_idx]['limit_hit'] = True
                    else:
                        app_logger.error(f"❌ [AI CLUSTER] Node {self.current_key_idx + 1} Error: {e}")
                        self.usage_stats[self.current_key_idx]['errors'] += 1
                    
                    self.rotate_key(force=True)
                tries += 1
        
        return None

    def analyze_image(self, image_bytes, question="Analyze this chart."):
        """Visual analysis protocol."""
        import google.generativeai as genai
        active_key = self.get_active_key()
        if not active_key: return "Link Failure"
        
        try:
            genai.configure(api_key=active_key)
            model = genai.GenerativeModel(self.model_name)
            image_part = {"mime_type": "image/png", "data": image_bytes}
            response = model.generate_content([question, image_part])
            return response.text
        except Exception as e:
            return f"Cluster Error: {e}"

