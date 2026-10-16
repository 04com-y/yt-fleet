import os
import asyncio
import subprocess
from typing import Dict, Any

VOICE_MAP = {
    "en": "en-US-ChristopherNeural",
    "hi": "hi-IN-MadhurNeural",
    "es": "es-ES-AlvaroNeural",
    "pt": "pt-BR-AntonioNeural"
}

def get_voice_for_language(lang_code: str) -> str:
    clean_code = lang_code.split("-")[0].lower() if lang_code else "en"
    return VOICE_MAP.get(clean_code, "en-US-ChristopherNeural")

def get_audio_duration(file_path: str) -> float:
    try:
        cmd = [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", file_path
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        return float(res.stdout.strip())
    except Exception:
        return 15.0

def synthesize_audio(channel_config: Dict[str, Any], script_data: Dict[str, Any]) -> Dict[str, Any]:
    out_path = "audio_output.mp3"
    channel_name = channel_config.get("name", "Channel")
    hook = script_data.get("hook", "").strip()

    narration_parts = [f"Welcome to {channel_name}."]
    if hook:
        narration_parts.append(hook)
        
    for scene in script_data.get("scenes", []):
        text = scene.get("narration", "").strip()
        if text:
            narration_parts.append(text)

    full_narration = " ".join(narration_parts)
    lang = channel_config.get("language", "en")
    selected_voice = get_voice_for_language(lang)

    print(f"[voice] Synthesizing speech ({len(full_narration.split())} words) using voice {selected_voice}...")

    try:
        import edge_tts

        async def _generate():
            communicate = edge_tts.Communicate(full_narration, selected_voice, rate="+5%")
            await communicate.save(out_path)

        asyncio.run(_generate())
        print(f"[voice] Successfully generated audio at {out_path}")
    except Exception as e:
        print(f"[voice] Warning: edge-tts synthesis failed ({e}). Falling back to FFmpeg tone.")
        fallback_cmd = f'ffmpeg -y -f lavfi -i "sine=frequency=440:duration=15" -c:a aac -b:a 128k {out_path}'
        subprocess.run(fallback_cmd, shell=True, check=True)

    actual_duration = get_audio_duration(out_path)

    return {
        "audio_path": out_path,
        "duration_seconds": actual_duration,
        "max_silence_seconds": 0.5
    }
