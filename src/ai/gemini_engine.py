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
        self.model_name = 'gemini-1.5-flash'
        self.model = True  # Dashboard flag (True = AI available)
        self.lock = asyncio.Lock()  # Protect against parallel scatter
        self.node_saturation_threshold = 25  # Move to next node after X requests
        self._is_exhausted = False  # SOVEREIGN FAILOVER FLAG (v41.2)

    def is_cluster_exhausted(self):
        """Returns True if ALL nodes in the cluster are currently hit by quota limits."""
        if not self.api_keys: return True
        # Check if all keys have 'limit_hit' flag active
        all_hit = all(self.usage_stats[i].get('limit_hit', False) for i in range(len(self.api_keys)))
        if all_hit:
            # Check if we've been in cooldown for less than 60s
            recent_hit_times = [self.usage_stats[i].get('last_hit_time', 0) for i in range(len(self.api_keys))]
            if recent_hit_times and (time.time() - max(recent_hit_times) < 60):
                self._is_exhausted = True
                return True
        
        self._is_exhausted = False
        return False
        
        # Ordered fallback: newest → oldest, all confirmed working with REST v1beta
        self.fallback_models = [
            'gemini-1.5-flash',         # Primary — stable
            'gemini-1.5-flash-8b',      # Fallback 1 — lightweight
            'gemini-pro',               # Fallback 2 — legacy but stable
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
        for i, key in enumerate(self.api_keys):
            stats = self.usage_stats.get(i, {})
            # Determine real-time visual status
            status = 'READY'
            if stats.get('suspended'): status = 'SUSPENDED'
            elif stats.get('limit_hit'): status = 'LIMIT HIT'
            elif stats.get('requests', 0) > 0 and stats.get('errors', 0) == 0: status = 'ONLINE'
            elif stats.get('errors', 0) > 0: status = f"ERROR {stats.get('last_code', '')}"

            info.append({
                'node': i + 1,
                'model': stats.get('active_model', self.model_name),
                'status': status,
                'requests': stats.get('requests', 0),
                'errors': stats.get('errors', 0),
                'limit_hit': stats.get('limit_hit', False),
                'suspended': stats.get('suspended', False)
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
        
        # MONITOR: Are ALL keys hit?
        all_hit = all(self.usage_stats[i]['limit_hit'] for i in range(max_tries))
        if all_hit:
            # Check if any have been reset recently (simple check: 60s cooldown)
            recent_hit_times = [self.usage_stats[i].get('last_hit_time', 0) for i in range(max_tries)]
            if recent_hit_times and (time.time() - max(recent_hit_times) < 60):
                # We are still in global cooldown
                return None

        while tries < max_tries:
            async with self.lock:
                idx = self.current_key_idx
                # CHECK: IF current node is flagged as limit_hit, move to next
                if self.usage_stats[idx]['limit_hit']:
                    self.rotate_key(force=True)
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
                    self.usage_stats[self.current_key_idx]['last_hit_time'] = time.time()
                    self.rotate_key(force=True)
                tries += 1
                
            except Exception as e:
                err_str = str(e)
                async with self.lock:
                    if "429" in err_str or "quota" in err_str.lower():
                        app_logger.warning(f"⚠️ [AI CLUSTER] Node {self.current_key_idx + 1} Limit. Shifting...")
                        self.usage_stats[self.current_key_idx]['limit_hit'] = True
                        self.usage_stats[self.current_key_idx]['last_hit_time'] = time.time()
                    else:
                        app_logger.error(f"❌ [AI CLUSTER] Node {self.current_key_idx + 1} Error: {e}")
                        self.usage_stats[self.current_key_idx]['errors'] += 1
                    
                    self.rotate_key(force=True)
                tries += 1
        
        # If we exit the loop, all nodes failed.
        app_logger.warning("🚨 [AI CLUSTER] Total Infrastructure Exhaustion. All nodes hit quota. Waiting for window reset...")
        return None

    async def get_macro_sentiment(self):
        """
        NEW v33.0: Institutional Macro Interceptor Protocol.
        Analyzes Global DXY, Bond Yields, and Geopolitical Risk.
        Returns structured sentiment for cross-asset validation.
        """
        prompt = (
            "Analyze current GLOBAL MACRO sentiment for an institutional trading bot. "
            "Specifically focus on: 1. US Dollar Index (DXY) strength. 2. US 10Y Bond Yields. "
            "3. Geopolitical tension. 4. Gold (XAU) vs Digital Gold (PAXG) liquidity risk. "
            "Return ONLY a JSON object: "
            '{"macro_bias": "BULLISH/BEARISH/NEUTRAL", "gold_safety": "HIGH/LOW", '
            '"dxy_pressure": "HIGH/LOW", "reason": "Short summary in Arabic"}'
        )
        
        raw_res = await self.ask(prompt, market_context="Corporate Intelligence Sweep")
        if not raw_res: return None
        
        try:
            # Extract JSON from potential markdown tags
            cleaned = raw_res.replace('```json', '').replace('```', '').strip()
            return json.loads(cleaned)
        except Exception as e:
            app_logger.warning(f"Macro Parse Error: {e}")
            return None
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
