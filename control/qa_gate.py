from typing import Dict, Any, List

class QAGate:
    def __init__(self, min_sourced_claims: int = 3, max_silence_seconds: float = 2.5):
        self.min_sourced_claims = min_sourced_claims
        self.max_silence_seconds = max_silence_seconds

    def validate_script(self, script_data: Dict[str, Any], channel_rules: Dict[str, Any]) -> (bool, List[str]):
        errors = []
        # Check original value
        if channel_rules.get("require_original_value", True):
            if not script_data.get("original_value"):
                errors.append("Script missing required original_value")

        # Check sourced claims count
        claims = script_data.get("claims", [])
        min_claims = channel_rules.get("min_sourced_claims", self.min_sourced_claims)
        if len(claims) < min_claims:
            errors.append(f"Expected at least {min_claims} claims, found {len(claims)}")

        # Check banned topics
        banned = channel_rules.get("banned_topics", [])
        title_lower = script_data.get("title", "").lower()
        for b in banned:
            if b.lower() in title_lower:
                errors.append(f"Title contains banned topic keyword: {b}")

        return (len(errors) == 0, errors)

    def validate_media(self, duration_audio: float, duration_video: float, max_silence: float = 0.0) -> (bool, List[str]):
        errors = []
        if abs(duration_audio - duration_video) > max(duration_audio, duration_video) * 0.10:
            errors.append(f"Audio and video duration mismatch beyond 10%: audio={duration_audio}s, video={duration_video}s")
        if max_silence > self.max_silence_seconds:
            errors.append(f"Silence threshold exceeded: max silence {max_silence}s > {self.max_silence_seconds}s")
        return (len(errors) == 0, errors)
