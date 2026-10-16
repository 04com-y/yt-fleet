from typing import Dict, Any, List
import os

def upload_fleet_videos(channel_config: Dict[str, Any], long_video: Dict[str, Any], shorts: List[Dict[str, Any]], dry_run: bool = True):
    slug = channel_config["slug"]
    if dry_run:
        print(f"[uploader] [DRY RUN] Simulating upload for {slug}...")
        return {"status": "success", "mode": "dry_run", "uploads_count": 4}

    print(f"[uploader] [LIVE] Connecting to YouTube API for '{slug}'...")
    from control.tokens import get_channel_token
    token_data = get_channel_token(slug)
    if not token_data:
        print(f"[uploader] [ERROR] No token found for '{slug}' in YT_TOKENS_JSON!")
        return {"status": "failed", "reason": f"No token for {slug}"}

    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload

        client_id = os.environ.get("YT_CLIENT_ID") or token_data.get("client_id")
        client_secret = os.environ.get("YT_CLIENT_SECRET") or token_data.get("client_secret")

        creds = Credentials(
            token=token_data.get("token"),
            refresh_token=token_data.get("refresh_token"),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret,
            scopes=token_data.get("scopes") or ["https://www.googleapis.com/auth/youtube.upload"]
        )

        youtube = build("youtube", "v3", credentials=creds)
        uploaded_ids = []

        # 1. Upload Long-form Video
        long_path = long_video.get("video_path")
        if long_path and os.path.exists(long_path):
            title = long_video.get("title", f"{channel_config['name']} Weekly Review")
            print(f"[uploader] Uploading long-form: '{title}'...")
            body = {
                "snippet": {
                    "title": title[:95],
                    "description": f"Educational review for {channel_config['name']}.\\n\\n#Technology #AI #Education",
                    "tags": [channel_config["slug"], "Technology", "Education"],
                    "categoryId": "28"
                },
                "status": {
                    "privacyStatus": "private",
                    "selfDeclaredMadeForKids": False
                }
            }
            media = MediaFileUpload(long_path, mimetype="video/mp4", resumable=True)
            res = youtube.videos().insert(part="snippet,status", body=body, media_body=media).execute()
            vid_id = res.get("id")
            uploaded_ids.append(vid_id)
            print(f"[uploader] [SUCCESS] Long-form uploaded! ID: {vid_id} (https://youtu.be/{vid_id})")

        # 2. Upload Shorts
        for s in shorts:
            s_path = s.get("video_path")
            if s_path and os.path.exists(s_path):
                s_title = (s.get("title", f"{channel_config['name']} Tip") + " #Shorts")[:95]
                print(f"[uploader] Uploading Short #{s['short_id']}: '{s_title}'...")
                body = {
                    "snippet": {
                        "title": s_title,
                        "description": f"Quick insight for {channel_config['name']}. #Shorts #Tech",
                        "tags": [channel_config["slug"], "Shorts"],
                        "categoryId": "28"
                    },
                    "status": {
                        "privacyStatus": "private",
                        "selfDeclaredMadeForKids": False
                    }
                }
                media = MediaFileUpload(s_path, mimetype="video/mp4", resumable=True)
                res = youtube.videos().insert(part="snippet,status", body=body, media_body=media).execute()
                sid = res.get("id")
                uploaded_ids.append(sid)
                print(f"[uploader] [SUCCESS] Short #{s['short_id']} uploaded! ID: {sid} (https://youtu.be/{sid})")

        return {"status": "success", "mode": "live", "uploaded_ids": uploaded_ids, "uploads_count": len(uploaded_ids)}
    except Exception as e:
        print(f"[uploader] [ERROR] Upload failed: {e}")
        return {"status": "failed", "error": str(e)}
