import os
import aiohttp
import asyncio
import time
from src.utils.logger import app_logger

GROQ_API_BASE = "https://api.groq.com/openai/v1/chat/completions"

class GroqAI:
    """PROSOFT AI: Groq High-Speed Node Cluster — Direct REST Protocol"""
    
    def __init__(self):
        # Support both singular and plural env variable names
        self.raw_keys = os.getenv('GROQ_API_KEYS', os.getenv('GROQ_API_KEY', ''))
        self.api_keys = [k.strip() for k in self.raw_keys.split(',') if k.strip()]
        self.current_key_idx = 0
        
        self.usage_stats = {i: {'requests': 0, 'errors': 0, 'limit_hit': False, 'last_success': 0, 'session_reqs': 0} for i in range(len(self.api_keys))}
        self.model_name = 'llama3-70b-8192'
        self.model = True
        self.lock = asyncio.Lock()
        
        self.fallback_models = [
            'llama3-70b-8192',
            'llama3-8b-8192',
            'mixtral-8x7b-32768'
        ]
        
        self._http_session = None
        self._cache = {}
        self._initialize_all()

    def _initialize_all(self):
        if not self.api_keys:
            app_logger.warning("No Groq API Keys detected. Lightning-AI will sleep.")
            return
        
        try:
            for i, key in enumerate(self.api_keys):
                masked = f"gsk_...{key[-4:]}" if len(key) > 8 else "INVALID"
                app_logger.info(f"⚡ [GROQ CLUSTER] Node {i+1} Ready: ID {masked}")
            app_logger.info(f"🚀 [GROQ CLUSTER] Initialized {len(self.api_keys)} Lightning Nodes.")
        except: pass

    async def _get_session(self):
        if self._http_session is None or self._http_session.closed:
            timeout = aiohttp.ClientTimeout(total=10, connect=3)
            self._http_session = aiohttp.ClientSession(timeout=timeout)
        return self._http_session

    def rotate_key(self, force=True):
        if len(self.api_keys) <= 1: return False
        self.usage_stats[self.current_key_idx]['session_reqs'] = 0
        self.current_key_idx = (self.current_key_idx + 1) % len(self.api_keys)
        app_logger.info(f"🔄 [GROQ CLUSTER] Pulse Shift: Moving to Node {self.current_key_idx + 1}/{len(self.api_keys)}")
        return True
        
    def get_quota_info(self):
        if not self.api_keys: return []
        info = []
        for i in range(len(self.api_keys)):
            stats = self.usage_stats[i]
            status = 'READY'
            if stats['limit_hit']: status = 'LIMIT HIT'
            elif stats['errors'] > 5: status = 'ERROR'
            elif stats['requests'] > 0: status = 'ONLINE'
            
            info.append({
                'id': i+1,
                'status': status,
                'requests': stats['requests'],
                'errors': stats['errors']
            })
        return info

    async def ask(self, question, market_context=None):
        if not self.api_keys:
            return None
            
        prompt = question
        if market_context:
            prompt = f"Context: {market_context}\nQ: {question}"

        now = time.time()
        self._cache = {k: v for k, v in getattr(self, '_cache', {}).items() if now - v['time'] < 300}
        if prompt in self._cache:
            return self._cache[prompt]['response']

        max_tries = len(self.api_keys)
        tries = 0

        while tries < max_tries:
            async with self.lock:
                idx = self.current_key_idx
                if self.usage_stats[idx]['limit_hit'] or self.usage_stats[idx].get('errors', 0) >= 3:
                    self.rotate_key(force=True)
                    idx = self.current_key_idx
                    
                active_key = self.api_keys[idx]
                
            url = GROQ_API_BASE
            headers = {
                "Authorization": f"Bearer {active_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": self.model_name,
                "messages": [
                    {"role": "system", "content": "You are PROSOFT AI, an elite crypto trading strategist. Be extremely concise. Reply with a single number if asked."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.5,
                "max_tokens": 512
            }

            try:
                session = await self._get_session()
                async with session.post(url, headers=headers, json=payload) as resp:
                    async with self.lock:
                        self.usage_stats[idx]['requests'] += 1
                        
                    if resp.status == 200:
                        data = await resp.json()
                        response_text = data['choices'][0]['message']['content'].strip()
                        
                        async with self.lock:
                            self.usage_stats[idx]['limit_hit'] = False
                            self._cache[prompt] = {'response': response_text, 'time': time.time()}
                        return response_text
                        
                    elif resp.status == 429:
                        async with self.lock:
                            app_logger.warning(f"⚡ [GROQ CLUSTER] Node {idx+1} Quota Limit. Shifting...")
                            self.usage_stats[idx]['limit_hit'] = True
                            self.rotate_key()
                        tries += 1
                        continue
                        
                    else:
                        async with self.lock:
                            self.usage_stats[idx]['errors'] += 1
                            app_logger.warning(f"⚡ [GROQ CLUSTER] Node {idx+1} Error ({resp.status}). Shifting...")
                            self.rotate_key()
                        tries += 1
                        continue
                        
            except Exception as e:
                async with self.lock:
                    self.usage_stats[idx]['errors'] += 1
                    app_logger.warning(f"⚡ [GROQ CLUSTER] Node {idx+1} Exception. Shifting...")
                    self.rotate_key()
                tries += 1
                
        return None
