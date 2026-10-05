import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from clarea.core.attribution import attribute
from clarea.generators.diagnosis import DiagnosisEngine
from clarea.generators.html_dashboard import HtmlDashboard
from clarea.generators.report import ReportGenerator
from tests.test_rules import post, summary


def account():
    return summary([
        post("a", "Obras", 1000, likes=50, messages=20),
        post("b", "Obras", 1000, likes=50, messages=18),
        post("c", "Renders", 1000, likes=80, messages=1),
        post("d", "Tips", 1000, likes=40, messages=10),
    ])


class TestAttribution(unittest.TestCase):
    def test_verdicts_by_topic(self):
        items = {(i.dimension, i.name): i for i in attribute(account())}
        self.assertEqual(items[("tema", "Obras")].verdict, "funciono")
        self.assertEqual(items[("tema", "Renders")].verdict, "fallo")
        self.assertIn("atención pero no clientes", items[("tema", "Renders")].reason)
        self.assertEqual(items[("tema", "Tips")].verdict, "neutral")

    def test_single_post_groups_are_preliminary(self):
        items = {i.name: i for i in attribute(account())}
        self.assertTrue(items["Renders"].preliminary)
        self.assertFalse(items["Obras"].preliminary)

    def test_single_group_dimension_is_skipped(self):
        # All posts share the same format, so there is nothing to compare.
        self.assertFalse([i for i in attribute(account()) if i.dimension == "formato"])

    def test_sorted_best_first(self):
        idx = [i.conversion_index for i in attribute(account())]
        self.assertEqual(idx, sorted(idx, reverse=True))

    def test_shown_in_reports(self):
        s = account()
        insight = DiagnosisEngine.generate_local_insight(s)
        self.assertIn("Qué Funcionó y Qué Falló", ReportGenerator.to_markdown(s, insight))
        self.assertIn("Qué funcionó y qué falló", HtmlDashboard.render(s, insight))


if __name__ == "__main__":
    unittest.main()
