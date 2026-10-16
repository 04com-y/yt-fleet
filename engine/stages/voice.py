import os
import sys
import asyncio
import edge_tts
from typing import Dict, Any

async def _synthesize_edge_voice(text: str, voice: str, output_path: str):
    """Generates soft, natural neural audio with an +8% cadence boost for fast pacing."""
    communicate = edge_tts.Communicate(text, voice, rate="+8%")
    await communicate.save(output_path)

def synthesize_audio(channel_config: Dict[str, Any], script_data: Dict[str, Any], output_path: str = "audio_output.mp3") -> str:
    """Main voiceover generation pipeline expected by engine/run.py."""
    voice = channel_config.get("voice", "en-US-JennyNeural")
    full_text = script_data.get("body", "")
    
    if not full_text:
        full_text = "Here is today's technical hardware update from Texh News."

    print(f"[voice] Generating soft neural voice using '{voice}' ({len(full_text)} chars)...")
    
    try:
        asyncio.run(_synthesize_edge_voice(full_text, voice, output_path))
        print(f"[voice] Audio saved successfully to {output_path}")
    except Exception as e:
        print(f"[voice] Edge-TTS error: {e}. Generating silent fallback audio...")
        cmd = f"ffmpeg -y -f lavfi -i anullsrc=r=44100:cl=mono -t 30 -q:a 9 -acodec libmp3lame {output_path}"
        os.system(cmd)

    return output_path

# Alias so both function names work interchangeably
generate_voiceover = synthesize_audio
