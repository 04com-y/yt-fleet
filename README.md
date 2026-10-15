# yt-fleet: 15-Channel YouTube Automation Engine

A free-tier, reuse-first multi-channel automated video production fleet running on GitHub Actions.

## Key Features
- **15 Channels, 1 Engine**: Config-driven architecture (`channels/*.yml`).
- **100% Cloud-Executed**: Runs entirely on GitHub Actions with zero local compute required.
- **Shorts Repurposing**: 1 long-form script produces 3 vertical Shorts, keeping LLM calls minimal.
- **Topic Collision Guard**: Anti-collision ledger prevents channels from covering overlapping topics within 14 days.
- **Automated QA Gate**: Verifies sourced claims, audio quality, video specs, and synthetic disclosure before upload.

## Quickstart
1. Set up your Google Cloud project and download Desktop OAuth client credentials.
2. Run `python scripts/auth_youtube.py` to authenticate your channels.
3. Paste keys into GitHub Secrets:
   - `YT_CLIENT_ID`, `YT_CLIENT_SECRET`, `YT_TOKENS_JSON`
   - `GEMINI_API_KEY`, `GROQ_API_KEY`
4. The engine will run automatically every day at 00:17 UTC via `.github/workflows/daily-dispatch.yml`.
