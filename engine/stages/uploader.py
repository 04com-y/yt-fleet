import os
import json
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

def get_youtube_client(channel_config: Dict[str, Any]):
    """Authenticate YouTube Data API using GitHub Secrets environment variables."""
    tokens_json = os.environ.get("YT_TOKENS_JSON")
    client_id = os.environ.get("YT_CLIENT_ID")
    client_secret = os.environ.get("YT_CLIENT_SECRET")

    if not tokens_json or not client_id or not client_secret:
        raise ValueError("Missing YT_TOKENS_JSON, YT_CLIENT_ID, or YT_CLIENT_SECRET in environment!")

    tokens_dict = json.loads(tokens_json)
    channel_slug = channel_config.get("slug", "ai-tools-en")
    
    # Extract channel specific token or default
    channel_token = tokens_dict.get(channel_slug, tokens_dict.get("default", tokens_dict))
    
    # If the token stored has credentials format
    creds_data = {
        "token": channel_token.get("access_token") if isinstance(channel_token, dict) else None,
        "refresh_token": channel_token.get("refresh_token") if isinstance(channel_token, dict) else channel_token,
        "token_uri": "https://oauth2.googleapis.com/token",
        "client_id": client_id,
        "client_secret": client_secret,
        "scopes": ["https://www.googleapis.com/auth/youtube.upload"]
    }
    
    creds = Credentials.from_authorized_user_info(creds_data)
    return build("youtube", "v3", credentials=creds)

def _upload_single_video(youtube, video_path: str, title: str, description: str, tags: List[str], is_short: bool = False) -> str:
    """Performs resumable 4MB chunk upload to YouTube."""
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found at: {video_path}")

    # Delay publish by 1 hour so HD processing & Content ID checks finish
    scheduled_time = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()

    full_title = f"{title[:90]} #Shorts" if is_short and "#Shorts" not in title else title[:100]
    
    body = {
        "snippet": {
            "title": full_title,
            "description": description + "\n\n---\nAutomated technical analysis and educational synthesis.",
            "tags": tags + (["Shorts", "YouTubeShorts"] if is_short else []),
            "categoryId": "28"  # Science & Technology
        },
        "status": {
            "privacyStatus": "private",
            "publishAt": scheduled_time,
            "selfDeclaredMadeForKids": False
        }
    }

    print(f"[uploader] Uploading {'SHORT' if is_short else 'LONG-FORM'}: '{full_title}' ({video_path})...")
    media = MediaFileUpload(video_path, chunksize=4 * 1024 * 1024, resumable=True, mimetype="video/mp4")
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"[uploader] Upload progress: {int(status.progress() * 100)}%")

    video_id = response.get("id")
    print(f"[uploader] Upload success! Video ID: {video_id}")
    return video_id

def upload_fleet_videos(channel_config: Dict[str, Any], long_video: Dict[str, Any], shorts: List[Dict[str, Any]], dry_run: bool = False) -> Dict[str, Any]:
    """Matches the exact signature called by engine/run.py."""
    if dry_run:
        print("[uploader] DRY RUN: Skipping actual YouTube API uploads.")
        return {
            "status": "dry_run_success",
            "long_form": long_video.get("video_path"),
            "shorts_count": len(shorts)
        }

    youtube = get_youtube_client(channel_config)
    results = {"long_form_id": None, "shorts_ids": []}

    # 1. Upload Long-Form (16:9) Video
    long_video_path = long_video.get("video_path")
    long_title = long_video.get("title", "Autonomous Tech Dispatch")
    if long_video_path and os.path.exists(long_video_path):
        v_id = _upload_single_video(
            youtube=youtube,
            video_path=long_video_path,
            title=long_title,
            description="Deep dive architectural analysis and developer breakdown.",
            tags=["AI", "Developer", "OpenSource", "Automation"],
            is_short=False
        )
        results["long_form_id"] = v_id

    # 2. Upload Derived 9:16 Shorts
    for short_item in shorts:
        s_path = short_item.get("video_path")
        s_title = short_item.get("title", "Quick Tech Insight")
        if s_path and os.path.exists(s_path):
            s_id = _upload_single_video(
                youtube=youtube,
                video_path=s_path,
                title=s_title,
                description="Quick technical insight from our weekly deep dive. #Shorts",
                tags=["AI", "Shorts", "Tech", "Coding"],
                is_short=True
            )
            results["shorts_ids"].append(s_id)
            # Sleep 5 seconds between uploads to respect API limits
            time.sleep(5)

    return results
