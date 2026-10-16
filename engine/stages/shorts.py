import os
import random
import requests
import asyncio
import subprocess
from typing import Dict, Any, List

VOICE_MAP = {
    "en": "en-US-JennyNeural",
    "en-us": "en-US-JennyNeural",
    "en-in": "en-IN-NeerjaNeural",
    "hi": "hi-IN-SwaraNeural",
    "es": "es-ES-ElviraNeural",
    "pt": "pt-BR-FranciscaNeural"
}

# Curated queries for cinematic tech & AI B-roll
CINEMATIC_QUERIES = [
    "artificial intelligence",
    "technology",
    "matrix code",
    "cyberpunk",
    "computer server",
    "coding"
]

def fetch_pixabay_videos(query: str, api_key: str, count: int = 4) -> List[str]:
    """Downloads real high-definition B-roll footage clips using Pixabay API."""
    downloaded_files = []
    if not api_key:
        print("[shorts] PIXABAY_API_KEY missing in environment.")
        return downloaded_files

    url = f"https://pixabay.com/api/videos/?key={api_key}&q={requests.utils.quote(query)}&per_page=15"

    try:
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            hits = r.json().get("hits", [])
            random.shuffle(hits)

            for item in hits:
                if len(downloaded_files) >= count:
                    break
                videos = item.get("videos", {})
                # Prioritize medium/large progressive MP4 streams
                target_video = videos.get("medium", {}) or videos.get("large", {}) or videos.get("small", {})
                v_url = target_video.get("url")

                if v_url:
                    clip_name = f"clip_{len(downloaded_files)}_{random.randint(100, 999)}.mp4"
                    print(f"[shorts] Downloading footage for '{query}': {clip_name}...")
                    c_data = requests.get(v_url, timeout=35).content
                    with open(clip_name, "wb") as f_out:
                        f_out.write(c_data)
                    downloaded_files.append(clip_name)
    except Exception as e:
        print(f"[shorts] Pixabay download failed: {e}")

    return downloaded_files

def synthesize_audio_and_srt(text: str, lang: str, audio_path: str, srt_path: str):
    """Synthesizes soft neural female voice with synchronized word-level captions."""
    clean_code = lang.split("-")[0].lower() if lang else "en"
    voice = VOICE_MAP.get(clean_code, "en-US-JennyNeural")
    raw_audio = f"raw_{audio_path}"

    import edge_tts
    async def _gen():
        communicate = edge_tts.Communicate(text, voice, rate="+5%", pitch="+0Hz")
        sub_maker = edge_tts.SubMaker()
        with open(raw_audio, "wb") as f_audio:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    f_audio.write(chunk["data"])
                elif chunk["type"] == "WordBoundary":
                    sub_maker.feed(chunk)
        
        with open(srt_path, "w", encoding="utf-8") as f_sub:
            f_sub.write(sub_maker.get_srt())

    asyncio.run(_gen())

    # Vocal clarity filtering + subtle warm background noise bed
    filter_complex = (
        "[0:a]highpass=f=80,treble=g=2.5,volume=1.2[v];"
        "[1:a]volume=0.14[bg];"
        "[v][bg]amix=inputs=2:duration=first:dropout_transition=2[out]"
    )
    cmd = [
        "ffmpeg", "-y", "-i", raw_audio,
        "-f", "lavfi", "-i", "anoisesrc=d=60:c=pink:r=44100:a=0.012, lowpass=f=400",
        "-filter_complex", filter_complex,
        "-map", "[out]", "-c:a", "libmp3lame", "-b:a", "192k", audio_path
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    if os.path.exists(raw_audio):
        os.remove(raw_audio)

def get_duration(file_path: str) -> float:
    try:
        cmd = [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", file_path
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        return float(res.stdout.strip())
    except Exception:
        return 15.0

def build_montage_short(video_path: str, clips: List[str], audio_path: str, srt_path: str, title: str, channel_name: str, total_duration: float):
    """
    Assembles real footage cuts into a 9:16 vertical short:
    - Crops & fills 1080x1920
    - Applies cinematic color grading
    - Burns bold centered subtitles
    """
    clean_title = title.replace("'", "").replace('"', '').upper()
    clean_channel = channel_name.replace("'", "").replace('"', '').upper()

    style = (
        "FontName=DejaVu Sans,FontSize=20,Bold=1,"
        "PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BackColour=&H90000000,"
        "BorderStyle=3,Outline=3,Shadow=2,Alignment=2,MarginV=380"
    )

    if clips and len(clips) > 0:
        segment_duration = max(total_duration / len(clips), 2.5)
        clip_segments = []

        for i, clip in enumerate(clips):
            seg_out = f"seg_{i}.mp4"
            # Crop to vertical 1080x1920 seamlessly
            scale_cmd = [
                "ffmpeg", "-y", "-i", clip,
                "-t", str(segment_duration),
                "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30",
                "-c:v", "libx264", "-preset", "ultrafast", "-an", seg_out
            ]
            subprocess.run(scale_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            clip_segments.append(seg_out)

        concat_list = "clips_concat.txt"
        with open(concat_list, "w") as f:
            for seg in clip_segments:
                f.write(f"file '{seg}'\n")

        base_video_input = ["-f", "concat", "-safe", "0", "-i", concat_list]
    else:
        # Fallback dynamic procedural visual if API returned no files
        base_video_input = ["-f", "lavfi", "-i", "cellauto=s=1080x1920:r=30,format=yuv420p,hue=s=0.6:h=215"]

    vf = (
        f"eq=contrast=1.06:brightness=-0.03:saturation=1.12,"
        f"drawbox=y=0:color=black@0.30:width=iw:height=ih:t=fill,"
        f"drawtext=text='⚡ {clean_channel}':fontcolor=0x38bdf8:fontsize=36:x=(w-text_w)/2:y=180:box=1:boxcolor=0x0f172a@0.9:boxborderw=14,"
        f"drawtext=text='{clean_title[:32]}':fontcolor=white:fontsize=50:x=(w-text_w)/2:y=300:box=1:boxcolor=0x1e293b@0.9:boxborderw=18,"
        f"subtitles={srt_path}:force_style='{style}'"
    )

    cmd = [
        "ffmpeg", "-y",
        *base_video_input,
        "-i", audio_path,
        "-t", str(total_duration),
        "-vf", vf,
        "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        video_path
    ]
    subprocess.run(cmd, check=True)

    # Cleanup temporary segment files
    if clips:
        for i in range(len(clips)):
            seg_file = f"seg_{i}.mp4"
            if os.path.exists(seg_file):
                os.remove(seg_file)
        if os.path.exists("clips_concat.txt"):
            os.remove("clips_concat.txt")

def generate_shorts(channel_config: Dict[str, Any], script_data: Dict[str, Any], *args, **kwargs) -> List[Dict[str, Any]]:
    channel_name = channel_config.get("name", "Channel")
    lang = channel_config.get("language", "en")
    pixabay_key = os.environ.get("PIXABAY_API_KEY", "")
    scenes = script_data.get("scenes", [])
    shorts_output = []

    target_scenes = scenes[:3] if len(scenes) >= 3 else scenes

    for idx, scene in enumerate(target_scenes, 1):
        short_video_path = f"output_short_{idx}.mp4"
        short_audio_path = f"short_audio_{idx}.mp3"
        short_srt_path = f"short_{idx}.srt"

        scene_title = scene.get("title", f"Insight #{idx}")
        scene_narration = scene.get("narration", "").strip()
        spoken_text = f"{scene_title}. {scene_narration} Follow for daily deep dives."

        # 1. Synthesize soft female voice + word-synced subtitles
        synthesize_audio_and_srt(spoken_text, lang, short_audio_path, short_srt_path)
        duration = get_duration(short_audio_path)

        # 2. Fetch real HD tech B-roll clips from Pixabay
        query = CINEMATIC_QUERIES[idx % len(CINEMATIC_QUERIES)]
        broll_clips = fetch_pixabay_videos(query, pixabay_key, count=4)

        # 3. Assemble dynamic multi-clip video montage
        build_montage_short(
            video_path=short_video_path,
            clips=broll_clips,
            audio_path=short_audio_path,
            srt_path=short_srt_path,
            title=scene_title,
            channel_name=channel_name,
            total_duration=duration
        )

        # Clean raw downloads
        for clip in broll_clips:
            if os.path.exists(clip):
                os.remove(clip)

        shorts_output.append({
            "short_index": idx,
            "title": f"{scene_title} #Shorts",
            "video_path": short_video_path,
            "resolution": "1080x1920"
        })

    return shorts_output

def cut_derived_shorts(channel_config: Dict[str, Any], script_data: Dict[str, Any], *args, **kwargs) -> List[Dict[str, Any]]:
    return generate_shorts(channel_config, script_data, *args, **kwargs)
