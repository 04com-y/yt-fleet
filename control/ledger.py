import os
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any

class TopicLedger:
    def __init__(self, ledger_path: str = "state/global/topics_ledger.jsonl"):
        self.ledger_path = ledger_path
        os.makedirs(os.path.dirname(ledger_path), exist_ok=True)
        if not os.path.exists(ledger_path):
            with open(ledger_path, "w") as f:
                pass

    def is_topic_allowed(self, topic: str, days_window: int = 14) -> bool:
        normalized = topic.lower().strip()
        cutoff_date = datetime.utcnow() - timedelta(days=days_window)

        with open(self.ledger_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                entry = json.loads(line)
                entry_date = datetime.fromisoformat(entry.get("timestamp"))
                if entry_date >= cutoff_date:
                    if entry.get("topic", "").lower().strip() == normalized:
                        return False
        return True

    def record_topic(self, channel_slug: str, topic: str, video_title: str):
        entry = {
            "channel": channel_slug,
            "topic": topic.strip(),
            "title": video_title.strip(),
            "timestamp": datetime.utcnow().isoformat()
        }
        with open(self.ledger_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
