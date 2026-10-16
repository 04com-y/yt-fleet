import os
import sys
import json
import random
import requests
import subprocess
from typing import Dict, Any, List

def _get_audio_duration(audio_path: str) -> float:
    """Extracts duration in seconds using ffprobe."""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        audio_path
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        return float(res.stdout.strip())
    except Exception:
        return 10.0

def _generate_timed_srt(srt_path: str, text: str, total_duration: float):
    """Generates a guaranteed valid SRT file with word blocks."""
    words = text.split()
    if not words:
        words = ["KEY", "TECHNICAL", "INSIGHTS", "AND", "ANALYSIS"]

    chunk_size = 3
    chunks = [" ".join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]
    chunk_count = len(chunks)
    duration_per_chunk = total_duration / max(1, chunk_count)

    with open(srt_path, "w", encoding="utf-8") as f:
        for idx, chunk in enumerate(chunks, start=1):
            start_sec = (idx - 1) * duration_per_chunk
            end_sec = min(total_duration, idx * duration_per_chunk)

            s_h = int(start_sec // 3600)
            s_m = int((start_sec % 3600) // 60)
            s_s = int(start_sec % 60)
            s_ms = int((start_sec - int(start_sec)) * 1000)

            e_h = int(end_sec // 3600)
            e_m = int((end_sec % 3600) // 60)
            e_s = int(end_sec % 60)
            e_ms = int((end_sec - int(end_sec)) * 1000)

            f.write(f"{idx}\n")
            f.write(f"{s_h:02d}:{s_m:02d}:{s_s:02d},{s_ms:03d} --> {e_h:02d}:{e_m:02d}:{e_s:02d},{e_ms:03d}\n")
            f.write(f"{chunk.upper()}\n\n")

def fetch_pixabay_broll(query: str, count: int = 4) -> List[str]:
    """Downloads HD stock footage from Pixabay."""
    api_key = os.environ.get("PIXABAY_API_KEY")
    clips = []
    
    if api_key:
        try:
            url = f"https://pixabay.com/api/videos/?key={api_key}&q={requests.utils.quote(query)}&per_page=15"
            r = requests.get(url, timeout=15)
            if r.status_code == 200:
                hits = r.json().get("hits", [])
                random.shuffle(hits)
                for i, hit in enumerate(hits[:count]):
                    video_url = (
                        hit.get("videos", {}).get("large", {}).get("url")
                        or hit.get("videos", {}).get("medium", {}).get("url")
                    )
                    if video_url:
                        clip_name = f"clip_{i}_{hit['id']}.mp4"
                        print(f"[shorts] Downloading footage for '{query}': {clip_name}...")
                        v_data = requests.get(video_url, timeout=30).content
                        with open(clip_name, "wb") as f:
                            f.write(v_data)
                        clips.append(clip_name)
        except Exception as e:
            print(f"[shorts] Pixabay download failed: {e}")

    # Fallback solid background if API returns no clips
    if not clips:
        fallback_clip = "clip_fallback.mp4"
        cmd = [
            "ffmpeg", "-y", "-f", "lavfi",
            "-i", "color=c=0x0f172a:s=1080x1920:d=15",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            fallback_clip
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        clips.append(fallback_clip)

    return clips

def build_montage_short(idx: int, script_text: str, audio_path: str, channel_title: str, query: str = "technology") -> str:
    """Assembles 9:16 vertical short with multi-clip montage and subtitles."""
    duration = _get_audio_duration(audio_path)
    output_mp4 = f"output_short_{idx}.mp4"
    srt_path = os.path.abspath(f"short_{idx}.srt")

    # 1. Create and flush SRT file on disk
    _generate_timed_srt(srt_path, script_text, duration)

    # 2. Download footage
    clips = fetch_pixabay_broll(query, count=4)
    clip_duration = max(2.5, duration / max(1, len(clips)))

    # 3. Standardize clips to 1080x1920 30fps
    standardized_clips = []
    for i, clip in enumerate(clips):
        std_name = f"std_{idx}_{i}.mp4"
        cmd = [
            "ffmpeg", "-y", "-i", clip,
            "-t", str(clip_duration),
            "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30",
            "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
            "-an", std_name
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if os.path.exists(std_name):
            standardized_clips.append(std_name)

    # 4. Create concat playlist
    concat_txt = f"concat_{idx}.txt"
    with open(concat_txt, "w", encoding="utf-8") as f:
        for c in standardized_clips:
            f.write(f"file '{os.path.abspath(c)}'\n")

    # 5. Build filter string with safe relative subtitle filename
    rel_srt = f"short_{idx}.srt"
    vf_filters = [
        "eq=contrast=1.06:brightness=-0.03:saturation=1.12",
        "drawbox=y=0:color=black@0.30:width=iw:height=ih:t=fill",
        f"drawtext=text='⚡ {channel_title.upper()}':fontcolor=0x38bdf8:fontsize=36:x=(w-text_w)/2:y=180:box=1:boxcolor=0x0f172a@0.9:boxborderw=14",
        f"drawtext=text='INSIGHT #{idx}':fontcolor=white:fontsize=50:x=(w-text_w)/2:y=300:box=1:boxcolor=0x1e293b@0.9:boxborderw=18"
    ]

    # Only attach subtitles filter if file exists and has content
    if os.path.exists(srt_path) and os.path.getsize(srt_path) > 0:
        vf_filters.append(
            f"subtitles={rel_srt}:force_style='FontName=DejaVu Sans,FontSize=20,Bold=1,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BackColour=&H90000000,BorderStyle=3,Outline=3,Shadow=2,Alignment=2,MarginV=380'"
        )

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", concat_txt,
        "-i", audio_path,
        "-t", f"{duration:.3f}",
        "-vf", ",".join(vf_filters),
        "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        output_mp4
    ]

    subprocess.run(cmd, check=True)
    return output_mp4

def cut_derived_shorts(channel_config: Dict[str, Any], script_data: Dict[str, Any], long_video: Any = None, *args, **kwargs) -> List[Dict[str, Any]]:
    """Primary entry point called by engine/run.py."""
    channel_name = channel_config.get("name", "Tech Dispatch")
    segments = script_data.get("shorts_segments") or [
        {"title": script_data.get("title", "Key Breakdown"), "text": script_data.get("body", "Today's technical breakdown.")}
    ]

    results = []
    for idx, seg in enumerate(segments[:3], start=1):
        seg_title = seg.get("title", f"Insight #{idx}")
        seg_text = seg.get("text", script_data.get("body", ""))
        audio_file = f"short_audio_{idx}.mp3"

        if not os.path.exists(audio_file):
            if os.path.exists("audio_output.mp3"):
                audio_file = "audio_output.mp3"
            else:
                subprocess.run([
                    "ffmpeg", "-y", "-f", "lavfi", "-i", "anoisesrc=d=8:c=pink:r=24000:a=0.02",
                    "-c:a", "libmp3lame", "-b:a", "128k", audio_file
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        try:
            video_path = build_montage_short(
                idx=idx,
                script_text=seg_text,
                audio_path=audio_file,
                channel_title=channel_name,
                query="technology"
            )
            results.append({
                "title": f"{seg_title} - {channel_name}",
                "video_path": video_path
            })
        except Exception as e:
            print(f"[shorts] Error building short #{idx}: {e}")

    return results

def generate_shorts(channel_config: Dict[str, Any], script_data: Dict[str, Any], *args, **kwargs) -> List[Dict[str, Any]]:
    """Backwards compatibility alias."""
    return cut_derived_shorts(channel_config, script_data, *args, **kwargs)
