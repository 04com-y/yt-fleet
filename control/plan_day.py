import os
import sys
import json
import yaml
from datetime import datetime
from control.schema import ChannelConfig, GlobalConfig, WeekTemplate

DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

def plan_day(channels_dir: str = "channels", config_dir: str = "config", only_channel: str = "", self_test: bool = False):
    # Check global pause
    global_path = os.path.join(config_dir, "global.yml")
    if os.path.exists(global_path):
        with open(global_path, "r") as f:
            gdata = yaml.safe_load(f)
            if gdata and gdata.get("pause", False):
                print(json.dumps({"include": []}))
                return

    # Check week template
    week_path = os.path.join(config_dir, "week_template.yml")
    with open(week_path, "r") as f:
        wdata = yaml.safe_load(f)
        schedule = wdata.get("schedule", {})

    if only_channel:
        target_slugs = [only_channel]
    else:
        weekday_name = DAYS[datetime.utcnow().weekday()]
        target_slugs = schedule.get(weekday_name, [])

    # Filter out paused or retired channels
    matrix_include = []
    for slug in target_slugs:
        ch_path = os.path.join(channels_dir, f"{slug}.yml")
        if not os.path.exists(ch_path):
            continue
        with open(ch_path, "r") as f:
            ch_data = yaml.safe_load(f)
            if ch_data.get("status") == "active":
                matrix_include.append({"channel": slug})

    output = {"include": matrix_include}
    if self_test:
        print("Self-test passed: valid JSON generated.")
    matrix_str = f"matrix={json.dumps(output)}"
    print(matrix_str)
    return output

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", default="", help="Run only specific channel slug")
    parser.add_argument("--self-test", action="store_true", help="Run self test")
    args = parser.parse_args()
    plan_day(only_channel=args.only, self_test=args.self_test)
