import os
import asyncio
import time
import json
import aiohttp
from src.utils.logger import app_logger

# PROSOFT QUANTUM AI ENGINE v14.0 — DIRECT REST API (Zero SDK Dependency)
# This engine communicates directly with Google's Gemini REST API
# No SDK needed. No deprecation risk. Maximum stability.

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"

class GeminiAI:
    """PROSOFT AI: Quantum Multi-Node Gemini Cluster — Direct REST Protocol."""
    
    def __init__(self):
        self.raw_keys = os.getenv('GEMINI_API_KEY', '')
        self.api_keys = [k.strip() for k in self.raw_keys.split(',') if k.strip()]
        self.current_key_idx = 0
        self.models = {}
        # TRACKING: Using index-based stats to ensure isolation
        self.usage_stats = {i: {'requests': 0, 'errors': 0, 'limit_hit': False, 'last_success': 0, 'session_reqs': 0} for i in range(len(self.api_keys))}
        self.model_name = 'gemini-2.5-flash'
        self.model = True  # Dashboard flag (True = AI available)
        self.lock = asyncio.Lock()  # Protect against parallel scatter
        self.node_saturation_threshold = 25  # Move to next node after X requests
        
        # Ordered fallback: newest → oldest, all confirmed working with REST v1beta
        self.fallback_models = [
            'gemini-2.5-flash',         # Primary — confirmed working
            'gemini-2.0-flash',         # Fallback 1 — exists but may rate-limit
            'gemini-1.5-flash-8b',      # Fallback 2 — lightweight alternative
        ]
        
        self._http_session = None  # Reusable aiohttp session
        self._initialize_all()
    
    def _initialize_all(self):
        if not self.api_keys:
            app_logger.warning("No Gemini API Keys detected. AI will operate in fallback mode.")
            return
        
        try:
            for i, key in enumerate(self.api_keys):
                masked = f"{key[:4]}...{key[-4:]}"
                app_logger.info(f"🔑 [AI CLUSTER] Node {i+1} Ready: ID {masked}")
            app_logger.info(f"🚀 [AI CLUSTER] Initialized {len(self.api_keys)} nodes (DIRECT REST PROTOCOL).")
        except: pass

    async def _get_session(self):
        """Lazy-init a reusable aiohttp session for connection pooling."""
        if self._http_session is None or self._http_session.closed:
            timeout = aiohttp.ClientTimeout(total=15, connect=5)
            self._http_session = aiohttp.ClientSession(timeout=timeout)
        return self._http_session

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
        """Rotate to next node."""
        if len(self.api_keys) <= 1: return False
        
        idx = self.current_key_idx
        self.usage_stats[idx]['session_reqs'] = 0
        
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

    async def _call_gemini_rest(self, model_name, prompt_text, api_key):
        """Direct REST API call to Gemini — Zero SDK dependency."""
        url = f"{GEMINI_API_BASE}/{model_name}:generateContent?key={api_key}"
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt_text}]
            }],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 1024,
            },
            "safetySettings": [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]
        }
        
        session = await self._get_session()
        async with session.post(url, json=payload) as resp:
            if resp.status == 200:
                data = await resp.json()
                # Extract text from response
                candidates = data.get('candidates', [])
                if candidates:
                    parts = candidates[0].get('content', {}).get('parts', [])
                    if parts:
                        return parts[0].get('text', '').strip()
                return None
            
            elif resp.status == 404:
                # Model not found — will try next fallback
                raise ModelNotFoundError(f"Model {model_name} not found (404)")
            
            elif resp.status == 429:
                # Rate limit — rotate key
                raise QuotaExceededError(f"Rate limit hit (429)")
            
            else:
                error_body = await resp.text()
                raise Exception(f"HTTP {resp.status}: {error_body[:200]}")

    async def ask(self, question, market_context=None):
        """Ask Gemini with Sequential Pulse strategy — DIRECT REST."""
        if not self.api_keys:
            return None
        
        tries = 0
        max_tries = len(self.api_keys)
        
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
                # Build prompt
                prompt = question
                if market_context:
                    system_prompt = "أنت كبير الاستراتيجيين في PROSOFT AI. فكر بعمق وقدم تحليلاً عصبياً دقيقاً. رد دائماً باللغة العربية (Arabic)."
                    prompt = f"{system_prompt}\nContext: {market_context}\nQ: {question}"
                
                # ATOMIC TRACKING
                self.usage_stats[idx]['requests'] += 1
                self.usage_stats[idx]['session_reqs'] += 1
                
                # Try each model in order until one works
                response_text = None
                for m_name in self.fallback_models:
                    try:
                        response_text = await self._call_gemini_rest(m_name, prompt, active_key)
                        if response_text:
                            if self.model_name != m_name:
                                self.model_name = m_name
                                app_logger.info(f"🧠 [AI CLUSTER] Active Model: {m_name}")
                            break
                    except ModelNotFoundError:
                        continue  # Try next model
                    except QuotaExceededError:
                        raise  # Propagate to outer handler for key rotation
                
                if response_text:
                    self.usage_stats[idx]['limit_hit'] = False
                    self.usage_stats[idx]['last_success'] = time.time()
                    return response_text
                
                # All models failed for this key, rotate
                async with self.lock: self.rotate_key(force=True)
                tries += 1

            except QuotaExceededError:
                async with self.lock:
                    app_logger.warning(f"⚠️ [AI CLUSTER] Node {self.current_key_idx + 1} Quota Limit. Shifting...")
                    self.usage_stats[self.current_key_idx]['limit_hit'] = True
                    self.rotate_key(force=True)
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
        """Visual analysis protocol — Synchronous REST for image analysis."""
        import base64
        import requests
        
        active_key = self.get_active_key()
        if not active_key: return "Link Failure"
        
        try:
            b64_image = base64.b64encode(image_bytes).decode('utf-8')
            
            url = f"{GEMINI_API_BASE}/{self.model_name}:generateContent?key={active_key}"
            
            payload = {
                "contents": [{
                    "parts": [
                        {"text": question},
                        {"inline_data": {"mime_type": "image/png", "data": b64_image}}
                    ]
                }]
            }
            
            resp = requests.post(url, json=payload, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get('candidates', [])
                if candidates:
                    parts = candidates[0].get('content', {}).get('parts', [])
                    if parts:
                        return parts[0].get('text', 'No analysis generated.')
            
            return f"API Error: HTTP {resp.status_code}"
        except Exception as e:
            return f"Cluster Error: {e}"


# Custom lightweight exceptions (no SDK dependency)
class ModelNotFoundError(Exception):
    pass

class QuotaExceededError(Exception):
    pass
