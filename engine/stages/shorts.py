import os
import asyncio
import textwrap
import subprocess
from typing import Dict, Any, List
from PIL import Image, ImageDraw, ImageFont

FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REGULAR_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

VOICE_MAP = {
    "en": "en-US-JennyNeural",
    "en-us": "en-US-JennyNeural",
    "en-in": "en-IN-NeerjaNeural",
    "hi": "hi-IN-SwaraNeural",
    "es": "es-ES-ElviraNeural",
    "pt": "pt-BR-FranciscaNeural"
}

def load_font(font_path: str, size: int) -> ImageFont.ImageFont:
    if os.path.exists(font_path):
        return ImageFont.truetype(font_path, size)
    return ImageFont.load_default()

def draw_wrapped_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, 
                      start_pos: tuple, max_width: int, fill: tuple, line_spacing: int = 14) -> int:
    x, y = start_pos
    avg_char_w = max(int(font.size * 0.52), 1) if hasattr(font, 'size') else 10
    wrap_chars = max(int(max_width / avg_char_w), 12)
    
    for line in textwrap.wrap(text, width=wrap_chars):
        draw.text((x, y), line, font=font, fill=fill)
        bbox = draw.textbbox((x, y), line, font=font)
        y += (bbox[3] - bbox[1]) + line_spacing
    return y

def synthesize_short_audio(text: str, lang: str, out_path: str):
    clean_code = lang.split("-")[0].lower() if lang else "en"
    voice = VOICE_MAP.get(clean_code, "en-US-JennyNeural")
    raw_path = f"raw_{out_path}"
    
    try:
        import edge_tts
        async def _gen():
            # +4% rate keeps speech clear and engaging without clipping
            c = edge_tts.Communicate(text, voice, rate="+4%", pitch="+0Hz")
            await c.save(raw_path)
        asyncio.run(_gen())

        # Layer subtle ambient acoustic noise bed under voice
        filter_complex = (
            "[0:a]highpass=f=80,treble=g=2.5,volume=1.2[v];"
            "[1:a]volume=0.14[bg];"
            "[v][bg]amix=inputs=2:duration=first:dropout_transition=2[out]"
        )
        cmd = [
            "ffmpeg", "-y", "-i", raw_path,
            "-f", "lavfi", "-i", "anoisesrc=d=60:c=pink:r=44100:a=0.012, lowpass=f=400",
            "-filter_complex", filter_complex,
            "-map", "[out]", "-c:a", "libmp3lame", "-b:a", "192k", out_path
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        if os.path.exists(raw_path):
            os.remove(raw_path)
    except Exception as e:
        print(f"[shorts] TTS fallback for {out_path} ({e})")
        subprocess.run(f'ffmpeg -y -f lavfi -i "sine=frequency=480:duration=15" -c:a aac {out_path}', shell=True, check=True)

def create_gradient_canvas(width: int, height: int, top_color: tuple, bottom_color: tuple) -> Image.Image:
    """Generates a deep vertical background gradient to replace flat blocks."""
    base = Image.new("RGB", (width, height), top_color)
    top_r, top_g, top_b = top_color
    bot_r, bot_g, bot_b = bottom_color
    
    draw = ImageDraw.Draw(base)
    for y in range(height):
        ratio = y / float(height)
        r = int(top_r + (bot_r - top_r) * ratio)
        g = int(top_g + (bot_g - top_g) * ratio)
        b = int(top_b + (bot_b - top_b) * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    return base

def generate_shorts(channel_config: Dict[str, Any], script_data: Dict[str, Any], *args, **kwargs) -> List[Dict[str, Any]]:
    channel_name = channel_config.get("name", "Channel")
    lang = channel_config.get("language", "en")
    scenes = script_data.get("scenes", [])
    shorts_output = []

    target_scenes = scenes[:3] if len(scenes) >= 3 else scenes

    font_badge = load_font(FONT_PATH, 34)
    font_title = load_font(FONT_PATH, 58)
    font_body = load_font(FONT_REGULAR_PATH, 44)
    font_cta = load_font(FONT_PATH, 36)

    for idx, scene in enumerate(target_scenes, 1):
        short_video_path = f"output_short_{idx}.mp4"
        short_slide_path = f"short_slide_{idx}.png"
        short_audio_path = f"short_audio_{idx}.mp3"

        scene_title = scene.get("title", f"Insight #{idx}")
        scene_narration = scene.get("narration", "").strip()

        spoken_text = (
            f"{scene_title}. "
            f"{scene_narration} "
            f"Follow for more."
        )

        synthesize_short_audio(spoken_text, lang, short_audio_path)

        # 1. Gradient Canvas (Dark Navy to Midnight Indigo)
        img = create_gradient_canvas(1080, 1920, (15, 23, 42), (8, 11, 22))
        draw = ImageDraw.Draw(img)

        # 2. Glowing Accent Border
        draw.rectangle([(25, 25), (1055, 1895)], outline=(56, 189, 248), width=4)

        # 3. Top Channel Badge
        draw.rounded_rectangle([(70, 90), (450, 165)], radius=35, fill=(30, 41, 59), outline=(56, 189, 248), width=2)
        draw.text((105, 110), f"⚡ {channel_name.upper()}", font=font_badge, fill=(56, 189, 248))

        # 4. Large Bold Hook Title (Centered with highlight underline)
        curr_y = draw_wrapped_text(draw, scene_title.upper(), font_title, (70, 310), max_width=940, fill=(255, 255, 255), line_spacing=16)
        draw.line([(70, curr_y + 20), (520, curr_y + 20)], fill=(244, 63, 94), width=6)  # Coral red line
        curr_y += 75

        # 5. Core Content Card
        card_top = curr_y
        card_bottom = min(curr_y + 760, 1540)
        draw.rounded_rectangle([(60, card_top), (1020, card_bottom)], radius=24, fill=(22, 32, 53), outline=(51, 65, 85), width=2)

        # Highlight bullet tag
        draw.rounded_rectangle([(90, card_top + 45), (280, card_top + 105)], radius=15, fill=(15, 23, 42))
        draw.text((115, card_top + 60), "THE BREAKTHROUGH", font=load_font(FONT_PATH, 24), fill=(148, 163, 184))

        # Narration Text inside Card
        draw_wrapped_text(draw, scene_narration, font_body, (95, card_top + 140), max_width=830, fill=(241, 245, 249), line_spacing=20)

        # 6. Bottom Sticky CTA
        draw.rounded_rectangle([(60, 1640), (1020, 1780)], radius=20, fill=(15, 23, 42), outline=(56, 189, 248), width=3)
        draw.text((160, 1690), "TAP FOLLOW FOR DAILY INSIGHTS", font=font_cta, fill=(56, 189, 248))

        img.save(short_slide_path, "PNG")

        # 7. Render Video with subtle zoom effect
        cmd = [
            "ffmpeg", "-y", "-loop", "1", "-i", short_slide_path,
            "-i", short_audio_path,
            "-vf", "scale=1080:1920,format=yuv420p",
            "-c:v", "libx264", "-tune", "stillimage",
            "-preset", "ultrafast",
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

def cut_derived_shorts(channel_config: Dict[str, Any], script_data: Dict[str, Any], *args, **kwargs) -> List[Dict[str, Any]]:
    return generate_shorts(channel_config, script_data, *args, **kwargs)
