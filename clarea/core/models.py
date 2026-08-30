from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class PostMetric(BaseModel):
    id: str
    content_type: str = Field(..., description="photo, video, reel, carousel, text")
    topic: str = Field(..., description="Topic or category of the post")
    reach: int = Field(default=0, ge=0)
    impressions: int = Field(default=0, ge=0)
    interactions: int = Field(default=0, ge=0)
    likes: int = Field(default=0, ge=0)
    comments: int = Field(default=0, ge=0)
    shares: int = Field(default=0, ge=0)
    saves: int = Field(default=0, ge=0)
    clicks: int = Field(default=0, ge=0)
    messages_inquired: int = Field(default=0, ge=0, description="Direct sales inquiries or message starts")
    published_date: Optional[str] = None
    caption_preview: Optional[str] = None

class PeriodSummary(BaseModel):
    brand_name: str
    platform: str = "Facebook"
    period_label: str
    total_reach: int
    reach_growth_pct: float
    total_interactions: int
    interactions_growth_pct: float
    total_messages: int
    messages_growth_pct: float
    new_followers: int
    posts_count: int
    posts: List[PostMetric] = []

class DiagnosticInsight(BaseModel):
    executive_summary: str
    vanity_vs_business_ratio: float
    key_findings: List[str]
    best_performing_format: str
    best_performing_topic: str
    primary_growth_bottleneck: str
    recommended_actions: List[str]
    suggested_hooks: List[str]
    suggested_ctas: List[str]
