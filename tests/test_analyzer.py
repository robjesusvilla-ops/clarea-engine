import unittest
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from clarea.core.models import PeriodSummary, PostMetric
from clarea.core.analyzer import MetricAnalyzer
from clarea.generators.diagnosis import DiagnosisEngine
from clarea.generators.hooks import HookGenerator

class TestClareaEngine(unittest.TestCase):
    def setUp(self):
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
        self.summary = PeriodSummary(
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

    def test_engagement_rate(self):
        analyzer = MetricAnalyzer(self.summary)
        self.assertEqual(analyzer.calculate_engagement_rate(), 7.5)

    def test_message_conversion_rate(self):
        analyzer = MetricAnalyzer(self.summary)
        self.assertEqual(analyzer.calculate_message_conversion_rate(), 1.05)

    def test_vanity_ratio(self):
        analyzer = MetricAnalyzer(self.summary)
        ratio = analyzer.calculate_vanity_vs_business_ratio()
        self.assertGreater(ratio, 0.0)

    def test_topic_ranking(self):
        analyzer = MetricAnalyzer(self.summary)
        ranked = analyzer.rank_topics_by_intent()
        self.assertEqual(len(ranked), 2)
        self.assertEqual(ranked[0]["topic"], "Case Studies")
        self.assertEqual(ranked[0]["total_messages"], 20)

    def test_diagnosis_generation(self):
        insight = DiagnosisEngine.generate_local_insight(self.summary)
        self.assertEqual(insight.best_performing_topic, "Case Studies")
        self.assertGreaterEqual(len(insight.recommended_actions), 4)
        self.assertGreaterEqual(len(insight.suggested_hooks), 5)

    def test_hook_generator(self):
        hooks = HookGenerator.generate_hooks("Solar Energy", "TESGA")
        self.assertEqual(len(hooks), 5)
        self.assertTrue("Solar Energy" in hooks[0] or "solar energy" in hooks[0].lower())

if __name__ == "__main__":
    unittest.main()
