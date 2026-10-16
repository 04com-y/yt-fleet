import os
import sys
import json
import random
import requests
import subprocess
from typing import Dict, Any, List
from duckduckgo_search import DDGS

def _get_audio_duration(audio_path: str) -> float:
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
        return 30.0

def _generate_kinetic_srt(srt_path: str, text: str, total_duration: float):
    """Generates rapid 2-word subtitle cards styled for high retention."""
    words = text.replace('"', '').replace("'", "").split()
    if not words:
        words = ["BREAKING", "TEXH", "UPDATE", "TODAY"]

    chunk_size = 2
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

def fetch_real_scene_image(query: str, scene_idx: int) -> str:
    """Downloads high-res news photo for the exact scene query."""
    headers = {"User-Agent": "Mozilla/5.0"}
    ddgs = DDGS()
    out_file = f"scene_{scene_idx}.jpg"

    print(f"[shorts] Sourcing real photo for: '{query}'")
    try:
        results = list(ddgs.images(query, max_results=6))
        for item in results:
            img_url = item.get("image")
            if not img_url:
                continue
            try:
                r = requests.get(img_url, headers=headers, timeout=8)
                if r.status_code == 200 and len(r.content) > 15000:
                    with open(out_file, "wb") as f:
                        f.write(r.content)
                    return out_file
            except Exception:
                continue
    except Exception as e:
        print(f"[shorts] Image query failed for '{query}': {e}")

    # Fallback high-tech procedural frame if web query fails
    cmd = [
        "ffmpeg", "-y", "-f", "lavfi",
        "-i", "color=c=0x0b132b:s=1080x1920:d=1",
        "-vframes", "1", out_file
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return out_file

def build_montage_short(idx: int, script_data: Dict[str, Any], audio_path: str, channel_title: str) -> str:
    duration = _get_audio_duration(audio_path)
    output_mp4 = f"output_short_{idx}.mp4"
    srt_path = os.path.abspath(f"short_{idx}.srt")
    
    full_text = script_data.get("body", "")
    scenes = script_data.get("scenes", [])
    if not scenes:
        scenes = [
            {"spoken_line": full_text, "image_query": "Nvidia silicon microchip"}
        ]

    # 1. Generate kinetic subtitles
    _generate_kinetic_srt(srt_path, full_text, duration)

    # 2. Download exact photos for each scene
    scene_images = []
    for s_idx, scene in enumerate(scenes):
        query = scene.get("image_query", "microchip technology")
        img = fetch_real_scene_image(query, s_idx)
        scene_images.append(img)

    time_per_scene = duration / max(1, len(scene_images))

    # 3. Create animated Ken Burns clips with blurred background canvas
    standardized_clips = []
    for i, img in enumerate(scene_images):
        clip_name = f"kenburns_{idx}_{i}.mp4"
        mode = i % 3

        if mode == 0:
            zoom_filter = f"zoompan=z='min(zoom+0.0016,1.20)':d={int(time_per_scene*30)}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920"
        elif mode == 1:
            zoom_filter = f"zoompan=z='1.12':d={int(time_per_scene*30)}:x='if(eq(on,1),0,x+1.5)':y='ih/2-(ih/zoom/2)':s=1080x1920"
        else:
            zoom_filter = f"zoompan=z='max(1.18-0.0016*on,1.0)':d={int(time_per_scene*30)}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920"

        # Dual-layer filtergraph: blurred 9:16 background + animated sharp foreground
        vf = (
            f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=25:5[bg];"
            f"[0:v]scale=1080:1920:force_original_aspect_ratio=decrease[fg];"
            f"[bg][fg]overlay=(W-w)/2:(H-h)/2,{zoom_filter},crop=1080:1920,setsar=1,fps=30"
        )

        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-i", img,
            "-t", str(time_per_scene),
            "-filter_complex", vf,
            "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
            clip_name
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if os.path.exists(clip_name):
            standardized_clips.append(clip_name)

    # 4. Playlist concatenation
    concat_txt = f"concat_{idx}.txt"
    with open(concat_txt, "w", encoding="utf-8") as f:
        for c in standardized_clips:
            f.write(f"file '{os.path.abspath(c)}'\n")

    # 5. Composite Header Badges & Kinetic Burn-in Subtitles
    rel_srt = f"short_{idx}.srt"
    vf_filters = [
        "drawbox=y=0:color=black@0.30:width=iw:height=ih:t=fill",
        f"drawtext=text='⚡ {channel_title.upper()}':fontcolor=0x38bdf8:fontsize=36:x=(w-text_w)/2:y=180:box=1:boxcolor=0x0b132b@0.90:boxborderw=14",
        "drawtext=text='HARDWARE DISPATCH':fontcolor=0xfacc15:fontsize=44:x=(w-text_w)/2:y=270:box=1:boxcolor=0x1e293b@0.90:boxborderw=16"
    ]

    if os.path.exists(srt_path) and os.path.getsize(srt_path) > 0:
        vf_filters.append(
            f"subtitles={rel_srt}:force_style='FontName=DejaVu Sans,FontSize=24,Bold=1,PrimaryColour=&H0000FFFF,OutlineColour=&H00000000,BackColour=&H80000000,BorderStyle=3,Outline=2.5,Shadow=3,Alignment=2,MarginV=420'"
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
    channel_name = channel_config.get("name", "Texh News")
    title = script_data.get("title", "Breaking Tech")
    audio_file = "audio_output.mp3"

    results = []
    try:
        video_path = build_montage_short(
            idx=1,
            script_data=script_data,
            audio_path=audio_file,
            channel_title=channel_name
        )
        results.append({
            "title": title,
            "description": script_data.get("seo_description", ""),
            "tags": script_data.get("tags", []),
            "video_path": video_path
        })
    except Exception as e:
        print(f"[shorts] Video assembly failed: {e}")

    return results

def generate_shorts(channel_config: Dict[str, Any], script_data: Dict[str, Any], *args, **kwargs) -> List[Dict[str, Any]]:
    return cut_derived_shorts(channel_config, script_data, *args, **kwargs)
