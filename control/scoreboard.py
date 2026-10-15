import os
import json
from typing import Dict, Any

def generate_weekly_scoreboard(channels_dir: str = "channels", state_dir: str = "state") -> Dict[str, Any]:
    scoreboard = {
        "summary": "Weekly YouTube Fleet Performance",
        "channels": {}
    }
    
    # Process each channel state
    for file in os.listdir(channels_dir):
        if file.startswith("_") or not file.endswith(".yml"):
            continue
        slug = file.replace(".yml", "")
        # Dummy baseline metrics for demonstration
        scoreboard["channels"][slug] = {
            "status": "KEEP",
            "views_last_week": 1250,
            "subscribers_total": 85,
            "qa_pass_rate": 1.0,
            "recommendation": "Maintain posting cadence"
        }
        
    out_path = os.path.join(state_dir, "global", "scoreboard.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(scoreboard, f, indent=2)
    print(f"Scoreboard written to {out_path}")
    return scoreboard

if __name__ == "__main__":
    generate_weekly_scoreboard()
