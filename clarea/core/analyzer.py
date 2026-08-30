from typing import Dict, Any, List
from collections import defaultdict
from clarea.core.models import PeriodSummary, PostMetric

class MetricAnalyzer:
    """Performs statistical, conversion, and business impact analysis on marketing data."""

    def __init__(self, summary: PeriodSummary):
        self.summary = summary

    def calculate_engagement_rate(self) -> float:
        if self.summary.total_reach == 0:
            return 0.0
        return round((self.summary.total_interactions / self.summary.total_reach) * 100, 2)

    def calculate_message_conversion_rate(self) -> float:
        if self.summary.total_reach == 0:
            return 0.0
        return round((self.summary.total_messages / self.summary.total_reach) * 100, 3)

    def calculate_vanity_vs_business_ratio(self) -> float:
        """
        Ratio of vanity engagement (likes/reactions) vs high-intent engagement (comments, shares, saves, messages).
        A high ratio (>5.0) indicates high vanity attention with low commercial conversion.
        """
        vanity_points = 0
        intent_points = 0
        for p in self.summary.posts:
            vanity_points += p.likes
            intent_points += (p.comments * 2) + (p.shares * 3) + (p.saves * 3) + (p.messages_inquired * 10)
        
        if intent_points == 0:
            return 9.99
        return round(vanity_points / float(intent_points), 2)

    def rank_topics_by_intent(self) -> List[Dict[str, Any]]:
        """Ranks content categories by business inquiry generation rather than just reach."""
        topic_stats = defaultdict(lambda: {"posts": 0, "reach": 0, "interactions": 0, "messages": 0})
        for p in self.summary.posts:
            t = topic_stats[p.topic]
            t["posts"] += 1
            t["reach"] += p.reach
            t["interactions"] += p.interactions
            t["messages"] += p.messages_inquired

        ranked = []
        for topic, stats in topic_stats.items():
            avg_reach = stats["reach"] // stats["posts"] if stats["posts"] > 0 else 0
            conv_rate = round((stats["messages"] / stats["reach"]) * 100, 3) if stats["reach"] > 0 else 0.0
            ranked.append({
                "topic": topic,
                "posts": stats["posts"],
                "total_messages": stats["messages"],
                "avg_reach": avg_reach,
                "conversion_rate": conv_rate
            })

        # Sort by total messages generated, then conversion rate
        ranked.sort(key=lambda x: (x["total_messages"], x["conversion_rate"]), reverse=True)
        return ranked

    def rank_formats(self) -> List[Dict[str, Any]]:
        """Ranks formats (photo, video, carousel, reel) by overall engagement and conversion."""
        format_stats = defaultdict(lambda: {"posts": 0, "reach": 0, "interactions": 0, "messages": 0})
        for p in self.summary.posts:
            f = format_stats[p.content_type]
            f["posts"] += 1
            f["reach"] += p.reach
            f["interactions"] += p.interactions
            f["messages"] += p.messages_inquired

        ranked = []
        for fmt, stats in format_stats.items():
            eng_rate = round((stats["interactions"] / stats["reach"]) * 100, 2) if stats["reach"] > 0 else 0.0
            ranked.append({
                "format": fmt,
                "posts": stats["posts"],
                "total_reach": stats["reach"],
                "engagement_rate": eng_rate,
                "total_messages": stats["messages"]
            })
        ranked.sort(key=lambda x: x["engagement_rate"], reverse=True)
        return ranked
