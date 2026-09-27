import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from clarea.core.analyzer import MetricAnalyzer
from clarea.generators.diagnosis import DiagnosisEngine
from clarea.generators.html_dashboard import HtmlDashboard
from tests.test_rules import post, summary


class TestHtmlDashboard(unittest.TestCase):
    def setUp(self):
        self.s = summary([
            post("a", "Obras <b>", 1000, likes=80, comments=10, messages=12, caption="Piscina lista"),
            post("b", "Saludos", 1000, likes=40, comments=2, messages=1),
        ])
        self.s.brand_name = "Qhatai Piscinas"
        self.insight = DiagnosisEngine.generate_local_insight(self.s)

    def test_full_document_has_all_modules(self):
        html = HtmlDashboard.render(self.s, self.insight)
        self.assertTrue(html.startswith("<!doctype html>"))
        for block in ("Vista Gerente", "Embudo comercial", "Interpretado por Clarea",
                      "Situaciones detectadas", "Ranking de publicaciones", "Hooks y CTAs"):
            self.assertIn(block, html)

    def test_fragment_has_no_document_wrapper(self):
        html = HtmlDashboard.render(self.s, self.insight, full_document=False)
        self.assertNotIn("<!doctype", html)
        self.assertIn("<title>", html)

    def test_user_text_is_escaped(self):
        html = HtmlDashboard.render(self.s, self.insight)
        self.assertIn("Obras &lt;b&gt;", html)

    def test_detected_industry_is_preselected(self):
        html = HtmlDashboard.render(self.s, self.insight)
        self.assertIn('value="piscinas" selected', html)


class TestPostRanking(unittest.TestCase):
    def test_best_converting_post_scores_highest(self):
        s = summary([post("low", "A", 1000, messages=1), post("high", "B", 1000, messages=20)])
        ranked = MetricAnalyzer(s).rank_posts()
        self.assertEqual(ranked[0]["post"].id, "high")
        self.assertLessEqual(ranked[0]["score"], 100)


if __name__ == "__main__":
    unittest.main()
