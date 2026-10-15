from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class VoiceConfig(BaseModel):
    engine: str = "kokoro"
    id: str
    speed: float = 1.0

class CadenceConfig(BaseModel):
    long_form_per_week: int = 1
    derived_shorts_per_long: int = 3
    standalone_shorts_per_week: int = 0
    publish_slots_utc: List[str] = ["13:30"]

class SourcesConfig(BaseModel):
    allow_domains: List[str]

class RulesConfig(BaseModel):
    banned_topics: List[str] = []
    require_original_value: bool = True
    min_sourced_claims: int = 3

class ChannelConfig(BaseModel):
    slug: str
    name: str
    language: str
    niche: str
    audience: str
    tier: str = "B"
    wave: int = 1
    status: str = "active"  # active, paused, retired
    formats: List[str]
    visual_skin: str
    voice: VoiceConfig
    cadence: CadenceConfig
    sources: SourcesConfig
    rules: RulesConfig
    monetization: Optional[Dict[str, Any]] = None

class GlobalConfig(BaseModel):
    pause: bool = False
    dry_run_default: bool = True
    max_parallel_channels: int = 3
    upload_bucket_daily_limit: int = 100
    llm_budget_daily_limit: int = 30

class WeekTemplate(BaseModel):
    schedule: Dict[str, List[str]]
