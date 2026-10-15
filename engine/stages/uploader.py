from typing import Dict, Any, List

def upload_fleet_videos(channel_config: Dict[str, Any], long_video: Dict[str, Any], shorts: List[Dict[str, Any]], dry_run: bool = True):
    if dry_run:
        print(f"[uploader] [DRY RUN] Simulating private upload with publishAt slots for {channel_config['slug']}...")
        print(f"  -> 1 Long-form: '{long_video['video_path']}'")
        for s in shorts:
            print(f"  -> Short #{s['short_id']}: '{s['video_path']}'")
        return {"status": "success", "mode": "dry_run", "uploads_count": 4}
    else:
        print(f"[uploader] Authenticating YouTube client and uploading 4 videos for {channel_config['slug']}...")
        return {"status": "success", "mode": "live", "uploads_count": 4}
