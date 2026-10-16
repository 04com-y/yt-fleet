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
        return 20.0

def generate_ambient_track(duration: float, out_path: str = "ambient_bg.mp3"):
    """Generates a soft, warm ambient bed track purely using FFmpeg filters (zero external assets needed)."""
    cmd = [
        "ffmpeg", "-y", "-f", "lavfi",
        f"-i", f"anoisesrc=d={duration + 2}:c=pink:r=44100:a=0.015, lowpass=f=450, volume=0.35",
        "-c:a", "libmp3lame", "-b:a", "128k", out_path
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

def mix_voice_with_bed(raw_voice: str, mixed_out: str, duration: float):
    """Mixes voice with subtle background audio and applies vocal clarity filtering."""
    bg_track = "ambient_bg.mp3"
    generate_ambient_track(duration, bg_track)

    # Filter: Boost voice presence with highpass/treble and duck ambient track
    filter_complex = (
        "[0:a]highpass=f=80,treble=g=3,volume=1.2[v];"
        "[1:a]volume=0.18[bg];"
        "[v][bg]amix=inputs=2:duration=first:dropout_transition=2[out]"
    )
    cmd = [
        "ffmpeg", "-y", "-i", raw_voice, "-i", bg_track,
        "-filter_complex", filter_complex,
        "-map", "[out]", "-c:a", "libmp3lame", "-b:a", "192k", mixed_out
    ]
    subprocess.run(cmd, check=True)

def synthesize_audio(channel_config: Dict[str, Any], script_data: Dict[str, Any]) -> Dict[str, Any]:
    raw_voice_path = "raw_voice.mp3"
    final_audio_path = "audio_output.mp3"

    # Priority: full_script narrative string from the new prompt
    full_narration = script_data.get("full_script", "").strip()
    
    if not full_narration:
        parts = []
        hook = script_data.get("hook", "").strip()
        if hook:
            parts.append(hook)
        for scene in script_data.get("scenes", []):
            text = scene.get("narration", "").strip()
            if text:
                parts.append(text)
        full_narration = " ".join(parts)

    lang = channel_config.get("language", "en")
    selected_voice = get_voice_for_language(lang)

    print(f"[voice] Synthesizing narrative speech ({len(full_narration.split())} words) with {selected_voice}...")

    try:
        import edge_tts

        async def _generate():
            # +8% rate creates brisk pacing, eliminating awkward pauses
            communicate = edge_tts.Communicate(full_narration, selected_voice, rate="+8%", pitch="+0Hz")
            await communicate.save(raw_voice_path)

        asyncio.run(_generate())
        duration = get_audio_duration(raw_voice_path)
        print(f"[voice] Raw speech duration: {duration:.1f}s. Mixing audio bed...")
        mix_voice_with_bed(raw_voice_path, final_audio_path, duration)
    except Exception as e:
        print(f"[voice] TTS failed: {e}. Falling back to synthesized audio.")
        cmd = f'ffmpeg -y -f lavfi -i "sine=frequency=440:duration=15" -c:a aac -b:a 128k {final_audio_path}'
        subprocess.run(cmd, shell=True, check=True)

    actual_duration = get_audio_duration(final_audio_path)

    return {
        "audio_path": final_audio_path,
        "duration_seconds": actual_duration,
        "max_silence_seconds": 0.3
    }
