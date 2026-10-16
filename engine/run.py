import os
import sys
import yaml
import argparse
from control.ledger import TopicLedger
from control.qa_gate import QAGate
from engine.stages.research import run_research
from engine.stages.scriptwriter import generate_script
from engine.stages.voice import synthesize_audio
from engine.stages.render import render_long_form
from engine.stages.shorts import cut_derived_shorts
from engine.stages.uploader import upload_fleet_videos

def run_channel(slug: str, job: str = "shorts_only", dry_run: bool = True, channels_dir: str = "channels"):
    ch_path = os.path.join(channels_dir, f"{slug}.yml")
    if not os.path.exists(ch_path):
        raise FileNotFoundError(f"Channel config not found: {ch_path}")

    with open(ch_path, "r", encoding="utf-8") as f:
        channel_config = yaml.safe_load(f)

    print(f"=== Running Channel: {channel_config['name']} ({slug}) [Mode: {job}] ===")

    # 1. Research
    research_data = run_research(channel_config)
    
    # 2. Topic ledger check
    ledger = TopicLedger()
    if not ledger.is_topic_allowed(research_data["topic"]):
        print(f"[ledger] Topic covered within 14 days. Generating fresh angle...")
        research_data["topic"] = f"{research_data['topic']} Part 2 (Fresh Insights)"

    # 3. Script generation
    script = generate_script(channel_config, research_data)

    # 4. QA Gate
    qa = QAGate()
    script_ok, errors = qa.validate_script(script, channel_config.get("rules", {}))
    if not script_ok:
        print(f"[qa_gate] QA failed: {errors}. Aborting run.")
        return

    # 5. Audio synthesis
    audio = synthesize_audio(channel_config, script)

    # 6. Video Rendering based on chosen --job format
    long_video = None
    shorts = []

    if job in ("long_only", "long_and_shorts"):
        print("[render] Rendering 16:9 Long-Form Video...")
        long_video = render_long_form(channel_config, script, audio)

    if job in ("shorts_only", "long_and_shorts"):
        print("[render] Rendering 9:16 Vertical Shorts...")
        shorts = cut_derived_shorts(channel_config, script, long_video)

    # 7. Upload / Dry Run
    res = upload_fleet_videos(channel_config, long_video, shorts, dry_run=dry_run)
    
    # Record topic in ledger
    ledger.record_topic(slug, research_data["topic"], script["title"])
    print(f"=== Channel Run Complete for {slug}: {res} ===")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--channel", required=True, help="Channel slug to run")
    parser.add_argument("--dry-run", action="store_true", default=False, help="Skip real uploads")
    parser.add_argument(
        "--job", 
        default="shorts_only", 
        choices=["shorts_only", "long_only", "long_and_shorts"], 
        help="Job production format"
    )
    args = parser.parse_args()
    
    # Check DRY_RUN environment variable from GitHub Actions
    env_dry_run = os.environ.get("DRY_RUN", "true").lower() == "true"
    is_dry_run = True if "--dry-run" in sys.argv else env_dry_run
    
    print(f"[engine] Executing with dry_run = {is_dry_run}, job = {args.job}")
    run_channel(args.channel, job=args.job, dry_run=is_dry_run)
