import os
import json
from typing import Optional, Dict, Any

def get_channel_token(channel_slug: str) -> Optional[Dict[str, Any]]:
    tokens_json = os.environ.get("YT_TOKENS_JSON")
    if not tokens_json:
        return None
    try:
        data = json.loads(tokens_json)
        return data.get(channel_slug)
    except Exception as e:
        print(f"[tokens] Error parsing YT_TOKENS_JSON: {e}")
        return None
