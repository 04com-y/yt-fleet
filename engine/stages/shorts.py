import os
import sys
import json
import urllib.parse
import requests
import subprocess
from typing import Dict, Any, List

def _get_audio_duration(audio_path: str) -> float:
    """Measures precise audio length in seconds using ffprobe."""
    if not os.path.exists(audio_path) or os.path.getsize(audio_path) == 0:
        return 30.0
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        audio_path
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        val = float(res.stdout.strip())
        return val if val > 0 else 30.0
    except Exception:
        return 30.0

def _generate_kinetic_srt(srt_path: str, text: str, total_duration: float):
    """Generates rapid 2-word subtitle cards styled for mobile retention."""
    words = text.replace('"', '').replace("'", "").replace("\n", " ").split()
    if not words:
        words = ["TEXH", "NEWS", "BREAKING", "TODAY"]

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
    print(f"[shorts] Kinetic SRT created at: {srt_path} ({chunk_count} word-cards)")

def fetch_real_scene_image(query: str, scene_idx: int) -> str:
    """Downloads authentic tech imagery using multi-source fallbacks (Wikimedia & Unsplash)."""
    headers = {"User-Agent": "TexhNewsBot/1.0 (contact@texhnews.local) Mozilla/5.0"}
    out_file = os.path.abspath(f"scene_{scene_idx}.jpg")
    cleaned_query = query.replace("leak", "").replace("render", "").strip()

    # Source 1: Wikimedia Commons API (Never blocked on GitHub Actions)
    try:
        wiki_url = (
            f"https://commons.wikimedia.org/w/api.php?action=query&generator=search"
            f"&gsrsearch={urllib.parse.quote(cleaned_query)}&gsrnamespace=6&gsrlimit=3"
            f"&prop=imageinfo&iiprop=url&iiurlwidth=1280&format=json"
        )
        r = requests.get(wiki_url, headers=headers, timeout=6)
        if r.status_code == 200:
            pages = r.json().get("query", {}).get("pages", {})
            for pid, pdata in pages.items():
                imageinfo = pdata.get("imageinfo", [])
                if imageinfo:
                    img_url = imageinfo[0].get("thumburl") or imageinfo[0].get("url")
                    if img_url and not img_url.endswith(".svg"):
                        img_res = requests.get(img_url, headers=headers, timeout=8)
                        if img_res.status_code == 200 and len(img_res.content) > 10000:
                            with open(out_file, "wb") as f:
                                f.write(img_res.content)
                            print(f"[shorts] Downloaded Wikimedia image for scene {scene_idx} ({len(img_res.content)} bytes)")
                            return out_file
    except Exception as e:
        print(f"[shorts] Wikimedia lookup error: {e}")

    # Source 2: Curated Direct Hardware Image Feed
    try:
        curated_urls = [
            "https://images.unsplash.com/photo-1591799264318-7e6ef8ddb7ea?w=1280&q=80",  # AMD/Intel CPU Die
            "https://images.unsplash.com/photo-1587202372775-e229f172b9d7?w=1280&q=80",  # GPU Graphics Card
            "https://images.unsplash.com/photo-1555680202-c86f0e12f086?w=1280&q=80",  # Motherboard Circuitry
            "https://images.unsplash.com/photo-1526738549149-8e07eca6c147?w=1280&q=80"   # Hardware Tech Setup
        ]
        chosen_url = curated_urls[scene_idx % len(curated_urls)]
        img_res = requests.get(chosen_url, headers=headers, timeout=8)
        if img_res.status_code == 200 and len(img_res.content) > 10000:
            with open(out_file, "wb") as f:
                f.write(img_res.content)
            print(f"[shorts] Downloaded curated photo for scene {scene_idx} ({len(img_res.content)} bytes)")
            return out_file
    except Exception as e:
        print(f"[shorts] Direct download error: {e}")

    # Fallback solid color frame
    cmd = [
        "ffmpeg", "-y", "-f", "lavfi",
        "-i", "color=c=0x0a0f1d:s=1080x1920:d=1",
        "-vframes", "1", out_file
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return out_file

def build_montage_short(idx: int, script_data: Dict[str, Any], audio_path: str, channel_title: str) -> str:
    workspace = os.getcwd()
    duration = _get_audio_duration(audio_path)
    output_mp4 = os.path.join(workspace, f"output_short_{idx}.mp4")
    srt_path = os.path.join(workspace, f"short_{idx}.srt")
    
    full_text = script_data.get("body", "")
    scenes = script_data.get("scenes", [])
    if not scenes:
        scenes = [
            {"spoken_line": full_text, "image_query": "graphics card gpu computer"}
        ]

    # 1. Generate kinetic subtitles
    _generate_kinetic_srt(srt_path, full_text, duration)

    # 2. Source real images
    scene_images = []
    for s_idx, scene in enumerate(scenes):
        query = scene.get("image_query", "microchip hardware")
        img = fetch_real_scene_image(query, s_idx)
        scene_images.append(img)

    time_per_scene = duration / max(1, len(scene_images))
    total_frames = max(1, int(time_per_scene * 30))

    # 3. Build Ken Burns motion clips with blurred background canvas
    standardized_clips = []
    for i, img in enumerate(scene_images):
        clip_name = os.path.join(workspace, f"clip_{idx}_{i}.mp4")
        mode = i % 3

        if mode == 0:
            zoom_expr = f"zoompan=z='min(zoom+0.0015,1.20)':d={total_frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=30"
        elif mode == 1:
            zoom_expr = f"zoompan=z='1.12':d={total_frames}:x='if(eq(on,1),0,x+1.2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=30"
        else:
            zoom_expr = f"zoompan=z='max(1.18-0.0015*on,1.0)':d={total_frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=30"

        vf = (
            f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=20:5[bg];"
            f"[0:v]scale=1080:1920:force_original_aspect_ratio=decrease[fg];"
            f"[bg][fg]overlay=(W-w)/2:(H-h)/2,{zoom_expr},crop=1080:1920,setsar=1,fps=30[outv]"
        )

        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-i", img,
            "-t", f"{time_per_scene:.3f}",
            "-filter_complex", vf,
            "-map", "[outv]",
            "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
            clip_name
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if os.path.exists(clip_name) and os.path.getsize(clip_name) > 0:
            standardized_clips.append(clip_name)

    # 4. Playlist concatenation
    concat_txt = os.path.join(workspace, f"concat_{idx}.txt")
    with open(concat_txt, "w", encoding="utf-8") as f:
        for c in standardized_clips:
            f.write(f"file '{c}'\n")

    # 5. Composite branding badges & burn kinetic subtitles
    vf_filters = [
        "drawbox=y=0:color=black@0.35:width=iw:height=ih:t=fill",
        f"drawtext=text='⚡ {channel_title.upper()}':fontcolor=0x38bdf8:fontsize=38:x=(w-text_w)/2:y=180:box=1:boxcolor=0x0b132b@0.90:boxborderw=14",
        "drawtext=text='HARDWARE DISPATCH':fontcolor=0xfacc15:fontsize=44:x=(w-text_w)/2:y=270:box=1:boxcolor=0x1e293b@0.90:boxborderw=16"
    ]

    if os.path.exists(srt_path) and os.path.getsize(srt_path) > 0:
        escaped_srt = srt_path.replace("\\", "/").replace(":", "\\:")
        vf_filters.append(
            f"subtitles={escaped_srt}:force_style='FontName=DejaVu Sans,FontSize=24,Bold=1,PrimaryColour=&H0000FFFF,OutlineColour=&H00000000,BackColour=&H80000000,BorderStyle=3,Outline=2.5,Shadow=3,Alignment=2,MarginV=420'"
        )

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", concat_txt,
        "-i", audio_path,
        "-t", f"{duration:.3f}",
        "-vf", ",".join(vf_filters),
        "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        output_mp4
    ]
    subprocess.run(cmd, check=True)
    return output_mp4

def cut_derived_shorts(channel_config: Dict[str, Any], script_data: Dict[str, Any], long_video: Any = None, *args, **kwargs) -> List[Dict[str, Any]]:
    channel_name = channel_config.get("name", "Texh News")
    title = script_data.get("title", "Breaking Hardware Leaks")
    audio_file = os.path.abspath("audio_output.mp3")

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
        print(f"[shorts] Video generation failed: {e}")

    return results

def generate_shorts(channel_config: Dict[str, Any], script_data: Dict[str, Any], *args, **kwargs) -> List[Dict[str, Any]]:
    return cut_derived_shorts(channel_config, script_data, *args, **kwargs)
