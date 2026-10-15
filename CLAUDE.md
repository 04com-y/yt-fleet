# Project: 15-channel YouTube engine (config-driven, GitHub Actions only)

## What this repo is
A control repo plus a modular engine that researches, scripts, renders, QA-checks and uploads
videos for up to 15 YouTube channels. Each channel is one file in channels/. Everything runs
on GitHub Actions. The owner's PC is only for building and initial authentication.

## Non-negotiable rules
1. Never commit secrets or tokens. Tokens live in the GitHub secret YT_TOKENS_JSON.
2. Reuse before writing: check existing engines, MoneyPrinterTurbo and Kokoro first.
3. Never publish a video that failed QA. Fail closed: skip the item, never skip the check.
4. Idempotent stages: check the ledger first, write it last. One upload per channel+video hash.
5. No channel may reuse or translate another channel's script. Respect state/global/topics_ledger.jsonl.
6. Every video needs original value and sourced claims.
7. Stay inside the daily LLM budget in config/providers.yml. Batch requests.
8. Official YouTube API only for upload and analytics. No browser automation of YouTube Studio.
9. One Google Cloud project only. Never add projects to get more quota.
10. Never commit media files. If config/global.yml has pause: true, every job exits at once.
11. Per-channel behaviour lives in channels/<slug>.yml and prompts/. Do not hard-code it.

## Commands
- python3 -m control.plan_day (prints today's job matrix as JSON)
- python3 -m engine.run --channel <slug> --dry-run (simulates run, uploads nothing)
- python3 -m unittest discover tests (runs test suite)
