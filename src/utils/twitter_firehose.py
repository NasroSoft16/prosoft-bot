import requests
from datetime import datetime
from src.utils.logger import app_logger

class TwitterSentimentFirehose:
    """PROSOFT AI: Real-time news & Twitter aggregation via CryptoPanic (FREE)."""
    
    def __init__(self):
        # Public API - No key required for basic feed
        self.api_url = "https://cryptopanic.com/api/v1/posts/?public=true"
        self.last_seen_id = None
        
    def scan_live_firehose(self):
        """Fetches the latest high-impact news and tweets from CryptoPanic."""
        try:
            response = requests.get(self.api_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                
                if not results:
                    return None
                
                latest = results[0]
                post_id = latest.get('id')
                
                # Check if this is a new post to avoid duplicates
                if post_id == self.last_seen_id:
                    return None
                
                self.last_seen_id = post_id
                
                # Filter for "High" importance or specific keywords if needed
                # For now, we take the absolute latest to ensure user sees real activity
                title = latest.get('title', 'No Title')
                source = latest.get('source', {}).get('title', 'Global Feed')
                url = latest.get('url', '')
                votes = latest.get('votes', {})
                
                # Basic sentiment based on CryptoPanic votes
                positive = votes.get('positive', 0)
                negative = votes.get('negative', 0)
                sentiment = "BULLISH" if positive > negative else ("BEARISH" if negative > positive else "NEUTRAL")
                
                alert = {
                    'timestamp': datetime.now().strftime("%H:%M:%S"),
                    'source': f"{source} (via CryptoPanic)",
                    'tweet': title,
                    'sentiment_score': 0.8 if sentiment == "BULLISH" else (0.2 if sentiment == "BEARISH" else 0.5),
                    'action_taken': f"ACTION_RECOMMENDED ({sentiment})" if (positive + negative) > 5 else "MONITORING"
                }
                
                app_logger.info(f"📰 [FRESH NEWS] {source}: {title} | Votes: +{positive}/-{negative}")
                return alert
        except Exception as e:
            app_logger.error(f"CryptoPanic Radar Error: {e}")
            
        return None
