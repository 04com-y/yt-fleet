import os
import sys
import json
from typing import Dict, Any, List

def upload_short(video_item: Dict[str, Any], channel_config: Dict[str, Any], dry_run: bool = False) -> Dict[str, Any]:
    """Uploads a generated Short to YouTube with viral title, description, and tags."""
    title = video_item.get("title", "Next-Gen Tech Leaks Revealed ⚡ #TexhNews")
    description = video_item.get(
        "seo_description",
        video_item.get("description", "Daily breaking tech news and hardware leaks from Texh News.\n\n#TexhNews #Hardware #Shorts")
    )
    tags = video_item.get("tags", ["Texh News", "Technology", "Hardware", "Shorts"])
    category_id = str(channel_config.get("category_id", "28"))
    video_path = video_item.get("video_path")

    print(f"\n[uploader] ===== PREPARING YOUTUBE UPLOAD =====")
    print(f"[uploader] Title:       {title}")
    print(f"[uploader] Video File:  {video_path}")
    print(f"[uploader] Category ID: {category_id}")
    print(f"[uploader] Tags:        {', '.join(tags)}")
    print(f"[uploader] Dry Run:     {dry_run}")
    print(f"[uploader] =====================================\n")

    if dry_run or not video_path or not os.path.exists(video_path):
        print(f"[uploader] Dry run active or missing file. Skipping live API call.")
        return {
            "status": "dry_run_success",
            "title": title,
            "video_path": video_path
        }

    try:
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
        from google.oauth2.credentials import Credentials

        token_json = os.environ.get("YT_TOKENS_JSON") or os.environ.get("YOUTUBE_TOKEN_JSON")

        if not token_json:
            print("[uploader] Warning: YouTube token secret missing. Skipping upload.")
            return {"status": "skipped_no_token"}

        creds = Credentials.from_authorized_user_info(json.loads(token_json))
        youtube = build("youtube", "v3", credentials=creds)

        body = {
            "snippet": {
                "title": title[:100],
                "description": description,
                "tags": tags,
                "categoryId": category_id
            },
            "status": {
                "privacyStatus": "public",
                "selfDeclaredMadeForKids": False
            }
        }

        media = MediaFileUpload(
            video_path,
            chunksize=-1,
            resumable=True,
            mimetype="video/mp4"
        )

        request = youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media
        )

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f"[uploader] Upload progress: {int(status.progress() * 100)}%")

        video_id = response.get("id")
        print(f"[uploader] Video uploaded successfully: https://youtube.com/shorts/{video_id}")
        return {"status": "uploaded", "video_id": video_id}

    except Exception as e:
        print(f"[uploader] Upload execution failed: {e}")
        return {"status": "error", "error": str(e)}

def upload_fleet_videos(channel_config: Dict[str, Any], shorts_list: List[Dict[str, Any]], dry_run: bool = False, *args, **kwargs) -> List[Dict[str, Any]]:
    """Primary upload function expected by engine/run.py."""
    results = []
    if not shorts_list:
        print("[uploader] No shorts provided to upload.")
        return results

    for item in shorts_list:
        res = upload_short(item, channel_config, dry_run=dry_run)
        results.append(res)
    return results

# Aliases for backwards compatibility
publish_shorts = upload_fleet_videos
upload_videos = upload_fleet_videos
