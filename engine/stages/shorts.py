from typing import Dict, Any, List

def cut_derived_shorts(channel_config: Dict[str, Any], script_data: Dict[str, Any], long_video_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    print(f"[shorts] Slicing 3 vertical 9:16 Shorts from long-form video timeline...")
    shorts = []
    for i in range(1, 4):
        shorts.append({
            "short_id": i,
            "title": f"{channel_config['name']} Quick Tip #{i} #Shorts",
            "video_path": f"output_short_{i}.mp4",
            "duration_seconds": 45.0,
            "resolution": "1080x1920"
        })
    return shorts
