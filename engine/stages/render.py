from typing import Dict, Any

def render_long_form(channel_config: Dict[str, Any], script_data: Dict[str, Any], audio_data: Dict[str, Any]) -> Dict[str, Any]:
    print(f"[render] Assembling 16:9 1080p long-form video using skin '{channel_config.get('visual_skin')}'...")
    return {
        "video_path": "output_long_form.mp4",
        "duration_seconds": 180.0,
        "resolution": "1920x1080"
    }
