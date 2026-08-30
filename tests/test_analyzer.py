import pytest
from clarea.core.models import PeriodSummary, PostMetric
from clarea.core.analyzer import MetricAnalyzer
from clarea.generators.diagnosis import DiagnosisEngine
from clarea.generators.hooks import HookGenerator

@pytest.fixture
def sample_summary():
    posts = [
        PostMetric(
            id="p1",
            content_type="photo",
            topic="Case Studies",
            reach=1000,
            impressions=1200,
            interactions=100,
            likes=70,
            comments=10,
            shares=10,
            saves=10,
            messages_inquired=20
        ),
        PostMetric(
            id="p2",
            content_type="video",
            topic="Company Updates",
            reach=1000,
            impressions=1100,
            interactions=50,
            likes=45,
            comments=2,
            shares=2,
            saves=1,
            messages_inquired=1
        )
    ]
    return PeriodSummary(
        brand_name="Test Brand",
        platform="Facebook",
        period_label="Q1 2026",
        total_reach=2000,
        reach_growth_pct=15.0,
        total_interactions=150,
        interactions_growth_pct=10.0,
        total_messages=21,
        messages_growth_pct=25.0,
        new_followers=30,
        posts_count=2,
        posts=posts
    )

def test_engagement_rate(sample_summary):
    analyzer = MetricAnalyzer(sample_summary)
    assert analyzer.calculate_engagement_rate() == 7.5

def test_message_conversion_rate(sample_summary):
    analyzer = MetricAnalyzer(sample_summary)
    assert analyzer.calculate_message_conversion_rate() == 1.05

def test_vanity_ratio(sample_summary):
    analyzer = MetricAnalyzer(sample_summary)
    ratio = analyzer.calculate_vanity_vs_business_ratio()
    assert ratio > 0.0

def test_topic_ranking(sample_summary):
    analyzer = MetricAnalyzer(sample_summary)
    ranked = analyzer.rank_topics_by_intent()
    assert len(ranked) == 2
    assert ranked[0]["topic"] == "Case Studies"
    assert ranked[0]["total_messages"] == 20

def test_diagnosis_generation(sample_summary):
    insight = DiagnosisEngine.generate_local_insight(sample_summary)
    assert insight.best_performing_topic == "Case Studies"
    assert len(insight.recommended_actions) >= 4
    assert len(insight.suggested_hooks) >= 5

def test_hook_generator():
    hooks = HookGenerator.generate_hooks("Solar Energy", "TESGA")
    assert len(hooks) == 5
    assert "Solar Energy" in hooks[0] or "solar energy" in hooks[0].lower()
