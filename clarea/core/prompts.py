from typing import Dict, Any
from clarea.core.models import PeriodSummary

class PromptOrchestrator:
    """Builds structured, deterministic prompts for Claude Code / Claude API."""

    @staticmethod
    def build_diagnosis_prompt(summary: PeriodSummary, analysis_data: Dict[str, Any]) -> str:
        return f"""You are the Clarea Decision Engine, an elite AI marketing strategist.
Your task is to analyze the marketing performance data for '{summary.brand_name}' ({summary.platform}) during the period '{summary.period_label}' and produce an authoritative, actionable business diagnosis.

DATA OVERVIEW:
- Total Reach: {summary.total_reach:,} ({summary.reach_growth_pct:+.1f}% vs prev)
- Total Interactions: {summary.total_interactions:,} ({summary.interactions_growth_pct:+.1f}% vs prev)
- Direct Inquiries / Messages: {summary.total_messages:,} ({summary.messages_growth_pct:+.1f}% vs prev)
- Total Published Posts: {summary.posts_count}
- Overall Engagement Rate: {analysis_data.get('engagement_rate', 0)}%
- Vanity-to-Business Ratio: {analysis_data.get('vanity_ratio', 0)} (Lower is better)

TOP PERFORMING CONTENT CATEGORIES:
{analysis_data.get('ranked_topics_str', 'N/A')}

TOP PERFORMING FORMATS:
{analysis_data.get('ranked_formats_str', 'N/A')}

INSTRUCTIONS:
1. Deliver a sharp, executive-level diagnosis ("Interpretado por Clarea") explaining WHAT happened, WHY it happened, and the commercial gap.
2. Differentiate clearly between vanity attention (likes/reach) and commercial intent (inquiries/quotes).
3. Provide 4 concrete strategic recommendations for the upcoming week.
4. Generate 5 high-converting Hooks tailored to the top-performing topic.
5. Generate 5 direct-response CTAs designed to drive inquiries into sales conversations.

Output in clear, structured Markdown format without fluff.
"""
