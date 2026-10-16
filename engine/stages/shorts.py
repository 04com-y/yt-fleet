import os
import asyncio
import textwrap
import subprocess
from typing import Dict, Any, List
from PIL import Image, ImageDraw, ImageFont

FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REGULAR_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

VOICE_MAP = {
    "en": "en-US-ChristopherNeural",
    "hi": "hi-IN-MadhurNeural",
    "es": "es-ES-AlvaroNeural",
    "pt": "pt-BR-AntonioNeural"
}

def load_font(font_path: str, size: int) -> ImageFont.ImageFont:
    if os.path.exists(font_path):
        return ImageFont.truetype(font_path, size)
    return ImageFont.load_default()

def draw_wrapped_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, 
                      start_pos: tuple, max_width: int, fill: tuple, line_spacing: int = 12) -> int:
    x, y = start_pos
    avg_char_w = max(int(font.size * 0.55), 1) if hasattr(font, 'size') else 10
    wrap_chars = max(int(max_width / avg_char_w), 12)
    
    for line in textwrap.wrap(text, width=wrap_chars):
        draw.text((x, y), line, font=font, fill=fill)
        bbox = draw.textbbox((x, y), line, font=font)
        y += (bbox[3] - bbox[1]) + line_spacing
    return y

def synthesize_short_audio(text: str, lang: str, out_path: str):
    clean_code = lang.split("-")[0].lower() if lang else "en"
    voice = VOICE_MAP.get(clean_code, "en-US-ChristopherNeural")
    try:
        import edge_tts
        async def _gen():
            c = edge_tts.Communicate(text, voice, rate="+6%")
            await c.save(out_path)
        asyncio.run(_gen())
    except Exception as e:
        print(f"[shorts] TTS fallback for {out_path} ({e})")
        subprocess.run(f'ffmpeg -y -f lavfi -i "sine=frequency=520:duration=15" -c:a aac {out_path}', shell=True, check=True)

def generate_shorts(channel_config: Dict[str, Any], script_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    channel_name = channel_config.get("name", "Channel")
    lang = channel_config.get("language", "en")
    scenes = script_data.get("scenes", [])
    shorts_output = []

    target_scenes = scenes[:3] if len(scenes) >= 3 else scenes

    font_header = load_font(FONT_PATH, 42)
    font_hook = load_font(FONT_PATH, 54)
    font_body = load_font(FONT_REGULAR_PATH, 44)
    font_cta = load_font(FONT_PATH, 38)

    for idx, scene in enumerate(target_scenes, 1):
        short_video_path = f"output_short_{idx}.mp4"
        short_slide_path = f"short_slide_{idx}.png"
        short_audio_path = f"short_audio_{idx}.mp3"

        scene_title = scene.get("title", f"Insight #{idx}")
        scene_narration = scene.get("narration", "").strip()

        spoken_text = (
            f"Here is what you need to know about {scene_title}. "
            f"{scene_narration} "
            f"Subscribe to {channel_name} for daily deep dives!"
        )

        synthesize_short_audio(spoken_text, lang, short_audio_path)

        img = Image.new("RGB", (1080, 1920), color=(10, 15, 28))
        draw = ImageDraw.Draw(img)

        # Border and Header
        draw.rectangle([(30, 30), (1050, 1890)], outline=(56, 189, 248), width=5)
        draw.rectangle([(30, 30), (1050, 180)], fill=(30, 41, 59))
        draw.text((70, 85), f"{channel_name.upper()} • SHORTS", font=font_header, fill=(56, 189, 248))

        # Hook Header
        curr_y = draw_wrapped_text(draw, scene_title.upper(), font_hook, (70, 320), max_width=940, fill=(255, 255, 255))
        draw.line([(70, curr_y + 20), (550, curr_y + 20)], fill=(56, 189, 248), width=6)
        curr_y += 60

        # Core Body
        draw.rectangle([(50, curr_y), (1030, min(curr_y + 700, 1550))], fill=(20, 30, 50), outline=(71, 85, 105), width=2)
        draw_wrapped_text(draw, scene_narration, font_body, (90, curr_y + 60), max_width=890, fill=(226, 232, 240), line_spacing=18)

        # Bottom CTA Card
        draw.rectangle([(50, 1620), (1030, 1780)], fill=(30, 41, 59), outline=(56, 189, 248), width=3)
        draw.text((90, 1680), "SUBSCRIBE FOR DAILY BREAKDOWNS", font=font_cta, fill=(56, 189, 248))

        img.save(short_slide_path, "PNG")

        cmd = [
            "ffmpeg", "-y", "-loop", "1", "-i", short_slide_path,
            "-i", short_audio_path, "-c:v", "libx264", "-tune", "stillimage",
            "-preset", "ultrafast", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", "-shortest", short_video_path
        ]
        subprocess.run(cmd, check=True)

        shorts_output.append({
            "short_index": idx,
            "title": f"{scene_title} #Shorts",
            "video_path": short_video_path,
            "resolution": "1080x1920"
        })

    return shorts_output
