import os
import sys
import yaml
import argparse
from typing import Dict, Any

from engine.stages.research import run_research
from engine.stages.scriptwriter import generate_script
from engine.stages.voice import synthesize_audio
from engine.stages.shorts import cut_derived_shorts
from engine.stages.uploader import upload_fleet_videos

def load_channel_config(channel_slug: str) -> Dict[str, Any]:
    config_path = os.path.join("channels", f"{channel_slug}.yml")
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    if "slug" not in config:
        config["slug"] = channel_slug
    return config

def run_channel(channel_slug: str, job: str = "shorts_only", dry_run: bool = True):
    print(f"\n==========================================")
    print(f"=== Running Channel: {channel_slug} [Job: {job}] ===")
    print(f"=== Dry Run: {dry_run} ===")
    print(f"==========================================\n")

    channel_config = load_channel_config(channel_slug)
    
    # 1. Research
    print("\n--- [Stage 1: Research] ---")
    research_data = run_research(channel_config)
    print(f"Selected Topic: {research_data.get('topic')}")

    # 2. Scriptwriter
    print("\n--- [Stage 2: Scriptwriter] ---")
    lang = channel_config.get("language", "en")
    script_data = generate_script(channel_config, language=lang)
    print(f"Title: {script_data.get('title')}")
    print(f"Spoken text length: {len(script_data.get('body', ''))} characters")

    # 3. Voice Synthesis
    print("\n--- [Stage 3: Voice Synthesis] ---")
    audio_path = os.path.abspath("audio_output.mp3")
    synthesize_audio(channel_config, script_data, output_path=audio_path)
    if not os.path.exists(audio_path) or os.path.getsize(audio_path) == 0:
        raise RuntimeError(f"Voice generation failed: {audio_path} does not exist or is empty.")
    print(f"Audio ready: {audio_path} ({os.path.getsize(audio_path)} bytes)")

    # 4. Video & Shorts Generation
    print("\n--- [Stage 4: Shorts Assembly] ---")
    shorts_list = cut_derived_shorts(channel_config, script_data, audio_path=audio_path)
    
    if not shorts_list:
        raise RuntimeError("No shorts were returned by cut_derived_shorts.")

    for idx, s in enumerate(shorts_list):
        v_path = s.get("video_path")
        if not v_path or not os.path.exists(v_path):
            raise RuntimeError(f"Short {idx+1} video file was not generated: {v_path}")
        print(f"Short generated successfully: {v_path} ({os.path.getsize(v_path)} bytes)")

    # 5. Uploader
    print("\n--- [Stage 5: Uploader] ---")
    upload_fleet_videos(channel_config, shorts_list, dry_run=dry_run)
    print("\n=== Channel Run Completed Successfully ===")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="YouTube Fleet Automation Engine")
    parser.add_argument("--channel", type=str, required=True, help="Channel slug name (e.g., ai-tools-en)")
    parser.add_argument("--job", type=str, default="shorts_only", help="Job mode")
    parser.add_argument("--dry_run", action="store_true", help="Enable dry run")
    
    args = parser.parse_args()
    
    env_dry_run = os.environ.get("DRY_RUN", "true").lower() in ("true", "1", "yes")
    is_dry = args.dry_run or env_dry_run

    run_channel(args.channel, job=args.job, dry_run=is_dry)
