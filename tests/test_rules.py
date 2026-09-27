import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from clarea.core.models import PeriodSummary, PostMetric
from clarea.core.rules import evaluate_rules


def post(pid, topic, reach, likes=0, comments=0, saves=0, messages=0, interactions=None, caption=None):
    return PostMetric(
        id=pid, content_type="photo", topic=topic, reach=reach,
        likes=likes, comments=comments, saves=saves, messages_inquired=messages,
        interactions=interactions if interactions is not None else likes + comments + saves,
        caption_preview=caption,
    )


def summary(posts, new_followers=0, messages_growth_pct=10.0):
    return PeriodSummary(
        brand_name="Test", period_label="Test",
        total_reach=sum(p.reach for p in posts),
        reach_growth_pct=0.0,
        total_interactions=sum(p.interactions for p in posts),
        interactions_growth_pct=0.0,
        total_messages=sum(p.messages_inquired for p in posts),
        messages_growth_pct=messages_growth_pct,
        new_followers=new_followers,
        posts_count=len(posts),
        posts=posts,
    )


def fired(s):
    return {f.rule_id for f in evaluate_rules(s)}


# A balanced account where no rule should trigger.
HEALTHY = [
    post("a", "Tema A", 1000, likes=50, comments=5, saves=5, messages=5),
    post("b", "Tema B", 1000, likes=50, comments=5, saves=5, messages=5),
]


class TestRules(unittest.TestCase):
    def test_healthy_account_triggers_nothing(self):
        self.assertEqual(fired(summary(HEALTHY)), set())

    def test_r1_high_reach_low_messages(self):
        s = summary([post("a", "A", 20000, likes=50, comments=5, messages=5)])
        self.assertIn("R1", fired(s))

    def test_r2_likes_without_comments(self):
        s = summary([post("a", "A", 2000, likes=400, comments=5, messages=10)])
        self.assertIn("R2", fired(s))

    def test_r3_topic_outperforms_rest(self):
        s = summary([
            post("a", "Obras", 1000, messages=20),
            post("b", "Obras", 1000, messages=20),
            post("c", "Saludos", 2000, messages=4),
        ])
        findings = evaluate_rules(s)
        r3 = next(f for f in findings if f.rule_id == "R3")
        self.assertIn("Obras", r3.title)

    def test_r3_needs_more_than_one_post(self):
        s = summary([
            post("a", "Obras", 1000, messages=20),
            post("c", "Saludos", 2000, messages=4),
        ])
        self.assertNotIn("R3", fired(s))

    def test_r4_high_saves(self):
        s = summary([
            post("a", "Costos", 1000, saves=30, messages=5),
            post("b", "Saludos", 1000, saves=2, messages=5),
        ])
        self.assertIn("R4", fired(s))

    def test_r5_followers_without_leads(self):
        s = summary(HEALTHY, new_followers=300, messages_growth_pct=0.0)
        self.assertIn("R5", fired(s))

    def test_r5_not_triggered_when_leads_grow(self):
        s = summary(HEALTHY, new_followers=300, messages_growth_pct=25.0)
        self.assertNotIn("R5", fired(s))

    def test_r6_sales_posts_drop(self):
        s = summary([
            post("a", "Obras", 1000, likes=80, messages=5),
            post("b", "Promo", 1000, likes=10, messages=5, caption="Descuento de temporada"),
        ])
        self.assertIn("R6", fired(s))

    def test_findings_sorted_by_severity(self):
        s = summary([post("a", "A", 20000, likes=400, comments=2, messages=5)],
                    new_followers=300, messages_growth_pct=0.0)
        severities = [f.severity for f in evaluate_rules(s)]
        self.assertEqual(severities[0], "critico")


if __name__ == "__main__":
    unittest.main()
