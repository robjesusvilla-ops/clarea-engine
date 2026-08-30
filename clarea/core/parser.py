import json
import csv
from typing import Dict, Any, Union
from pathlib import Path
from clarea.core.models import PeriodSummary, PostMetric

class MetricParser:
    """Parses raw marketing metrics from JSON, CSV or Meta Graph API payloads."""

    @staticmethod
    def from_json_file(file_path: Union[str, Path]) -> PeriodSummary:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return PeriodSummary(**data)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> PeriodSummary:
        return PeriodSummary(**data)

    @staticmethod
    def from_csv_file(file_path: Union[str, Path], brand_name: str, period_label: str) -> PeriodSummary:
        posts = []
        total_reach = 0
        total_interactions = 0
        total_messages = 0

        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for idx, row in enumerate(reader):
                reach = int(row.get("reach", 0))
                interactions = int(row.get("interactions", 0))
                messages = int(row.get("messages", 0))
                
                total_reach += reach
                total_interactions += interactions
                total_messages += messages

                post = PostMetric(
                    id=row.get("id", f"post_{idx+1}"),
                    content_type=row.get("content_type", "photo"),
                    topic=row.get("topic", "general"),
                    reach=reach,
                    impressions=int(row.get("impressions", reach)),
                    interactions=interactions,
                    likes=int(row.get("likes", 0)),
                    comments=int(row.get("comments", 0)),
                    shares=int(row.get("shares", 0)),
                    saves=int(row.get("saves", 0)),
                    clicks=int(row.get("clicks", 0)),
                    messages_inquired=messages,
                    published_date=row.get("published_date", None),
                    caption_preview=row.get("caption_preview", None)
                )
                posts.append(post)

        return PeriodSummary(
            brand_name=brand_name,
            platform="Facebook",
            period_label=period_label,
            total_reach=total_reach,
            reach_growth_pct=0.0,
            total_interactions=total_interactions,
            interactions_growth_pct=0.0,
            total_messages=total_messages,
            messages_growth_pct=0.0,
            new_followers=0,
            posts_count=len(posts),
            posts=posts
        )
