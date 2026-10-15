#!/usr/bin/env python3
"""
Interactive YouTube OAuth Desktop Script
Run this locally once per Google account to generate the refresh token.
"""
import os
import sys
import json

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly"
]

def authenticate_channel(channel_slug: str):
    print(f"\n=== Authenticating Channel: {channel_slug} ===")
    client_id = os.environ.get("YT_CLIENT_ID") or input("Enter YT_CLIENT_ID: ").strip()
    client_secret = os.environ.get("YT_CLIENT_SECRET") or input("Enter YT_CLIENT_SECRET: ").strip()

    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
        flow = InstalledAppFlow.from_client_config(
            {
                "installed": {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token"
                }
            },
            scopes=SCOPES
        )
        credentials = flow.run_local_server(port=0)
        token_data = {
            "token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "token_uri": credentials.token_uri,
            "client_id": credentials.client_id,
            "client_secret": credentials.client_secret,
            "scopes": credentials.scopes
        }
        print("\n[SUCCESS] Token obtained! Add this entry into your YT_TOKENS_JSON GitHub Secret:")
        print(json.dumps({channel_slug: token_data}, indent=2))
    except ImportError:
        print("\n[NOTE] google-auth-oauthlib not installed locally. Run: pip install google-auth-oauthlib")

if __name__ == "__main__":
    slug = sys.argv[1] if len(sys.argv) > 1 else input("Enter channel slug (e.g. ai-tools-en): ").strip()
    authenticate_channel(slug)
