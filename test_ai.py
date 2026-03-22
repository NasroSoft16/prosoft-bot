"""PROSOFT AI Direct Test — REST API (No SDK)"""
import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"

# Models to test (newest first)
TEST_MODELS = [
    'gemini-2.5-flash',
    'gemini-2.0-flash',
    'gemini-2.0-flash-lite',
    'gemini-1.5-flash',
    'gemini-1.5-pro',
]

def test_model(api_key, model_name):
    """Test a single model via direct REST call."""
    url = f"{GEMINI_API_BASE}/{model_name}:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": "قُل: تم الاتصال بنجاح. PROSOFT AI ONLINE."}]}],
        "generationConfig": {"maxOutputTokens": 50}
    }
    
    try:
        resp = requests.post(url, json=payload, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            candidates = data.get('candidates', [])
            if candidates:
                text = candidates[0].get('content', {}).get('parts', [{}])[0].get('text', '')
                return True, text.strip()[:80]
            return False, "Empty response"
        elif resp.status_code == 404:
            return False, "Model not found (404)"
        elif resp.status_code == 429:
            return False, "Rate limit (429)"
        else:
            error = resp.json().get('error', {}).get('message', resp.text[:100])
            return False, f"HTTP {resp.status_code}: {error[:60]}"
    except Exception as e:
        return False, str(e)[:60]

def audit_gemini():
    raw_keys = os.getenv('GEMINI_API_KEY', '')
    keys = [k.strip() for k in raw_keys.split(',') if k.strip()]
    
    if not keys:
        print("❌ لا يوجد مفتاح GEMINI_API_KEY في ملف .env")
        return
    
    print(f"\n{'='*60}")
    print(f"  PROSOFT AI CLUSTER AUDIT — DIRECT REST PROTOCOL")
    print(f"  Nodes: {len(keys)} | Method: REST API (No SDK)")
    print(f"{'='*60}\n")
    
    for i, key in enumerate(keys):
        masked = f"{key[:6]}...{key[-4:]}"
        print(f"🔑 Node {i+1} [{masked}]:")
        
        found_working = False
        for model in TEST_MODELS:
            success, result = test_model(key, model)
            status = "✅" if success else "❌"
            print(f"   {status} {model}: {result}")
            if success and not found_working:
                found_working = True
        
        if found_working:
            print(f"   🟢 Node {i+1}: OPERATIONAL\n")
        else:
            print(f"   🔴 Node {i+1}: ALL MODELS FAILED\n")
    
    print(f"{'='*60}")
    print(f"  Audit Complete. Deploy to Railway with confidence.")
    print(f"{'='*60}")

if __name__ == "__main__":
    audit_gemini()
