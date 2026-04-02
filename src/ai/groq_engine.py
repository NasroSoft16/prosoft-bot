import os
import asyncio
import time
import json
import aiohttp
from src.utils.logger import app_logger

# PROSOFT QUANTUM GROQ ENGINE v42.0 — HYPER-FAST REST PROTOCOL
# Using Meta Llama 3.1 via Groq LPU (The Fastest AI on Earth)

GROQ_API_BASE = "https://api.groq.com/openai/v1/chat/completions"

class GroqAI:
    """PROSOFT AI: Quantum Multi-Node Groq Cluster — Llama 3.1 Acceleration."""
    
    def __init__(self):
        self.raw_keys = os.getenv('GROQ_API_KEYS', '')
        self.api_keys = [k.strip() for k in self.raw_keys.split(',') if k.strip()]
        self.current_key_idx = 0
        self.usage_stats = {i: {'requests': 0, 'errors': 0, 'limit_hit': False, 'last_success': 0} for i in range(len(self.api_keys))}
        self.model_name = 'llama-3.1-70b-versatile'
        self.lock = asyncio.Lock()
        self._http_session = None
        self._is_exhausted = False
        
        self.fallback_models = [
            'llama-3.1-70b-versatile',
            'llama-3.1-8b-instant',
            'mixtral-8x7b-32768'
        ]

    async def _get_session(self):
        if self._http_session is None or self._http_session.closed:
            timeout = aiohttp.ClientTimeout(total=10, connect=5)
            self._http_session = aiohttp.ClientSession(timeout=timeout)
        return self._http_session

    def is_cluster_exhausted(self):
        if not self.api_keys: return True
        all_hit = all(self.usage_stats[i].get('limit_hit', False) for i in range(len(self.api_keys)))
        if all_hit:
            self._is_exhausted = True
            return True
        self._is_exhausted = False
        return False

    def get_quota_info(self):
        if not self.api_keys: return []
        info = []
        for i, key in enumerate(self.api_keys):
            stats = self.usage_stats.get(i, {})
            status = 'READY'
            if stats.get('limit_hit'): status = 'LIMIT HIT'
            elif stats.get('requests', 0) > 0: status = 'ONLINE'

            info.append({
                'node': i + 1,
                'model': 'Llama 3.1',
                'status': status,
                'requests': stats.get('requests', 0),
                'errors': stats.get('errors', 0)
            })
        return info

    async def ask(self, question):
        if not self.api_keys: return None
        
        tries = 0
        max_tries = len(self.api_keys)
        
        while tries < max_tries:
            idx = self.current_key_idx
            if self.usage_stats[idx]['limit_hit']:
                self.current_key_idx = (self.current_key_idx + 1) % len(self.api_keys)
                tries += 1
                continue
                
            active_key = self.api_keys[idx]
            
            payload = {
                "model": self.model_name,
                "messages": [{"role": "user", "content": question}],
                "temperature": 0.5,
                "max_tokens": 512
            }
            
            headers = {"Authorization": f"Bearer {active_key}", "Content-Type": "application/json"}
            
            try:
                session = await self._get_session()
                async with session.post(GROQ_API_BASE, json=payload, headers=headers) as resp:
                    self.usage_stats[idx]['requests'] += 1
                    
                    if resp.status == 200:
                        data = await resp.json()
                        result = data['choices'][0]['message']['content'].strip()
                        self.usage_stats[idx]['limit_hit'] = False
                        self.usage_stats[idx]['last_success'] = time.time()
                        return result
                    
                    elif resp.status == 429:
                        app_logger.warning(f"⚠️ [GROQ CLUSTER] Node {idx+1} Rate Limited. Shifting...")
                        self.usage_stats[idx]['limit_hit'] = True
                        self.current_key_idx = (self.current_key_idx + 1) % len(self.api_keys)
                    else:
                        self.usage_stats[idx]['errors'] += 1
                        
            except Exception as e:
                app_logger.error(f"❌ [GROQ CLUSTER] Error: {e}")
                self.usage_stats[idx]['errors'] += 1
            
            tries += 1
            self.current_key_idx = (self.current_key_idx + 1) % len(self.api_keys)
            
        return None
