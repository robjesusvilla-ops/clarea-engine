import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from clarea.generators.diagnosis import DiagnosisEngine
from clarea.generators.manager_view import ManagerViewGenerator
from tests.test_rules import post, summary, HEALTHY


def view_for(s):
    return ManagerViewGenerator.generate(s, DiagnosisEngine.generate_local_insight(s))


class TestManagerView(unittest.TestCase):
    def test_healthy_account_is_green(self):
        v = view_for(summary(HEALTHY, messages_growth_pct=10.0))
        self.assertEqual(v.status, "saludable")
        self.assertIn("+10.0%", v.main_achievement)

    def test_critical_rule_turns_red_and_drives_decision(self):
        s = summary([post("a", "A", 20000, likes=50, comments=5, messages=5)])
        v = view_for(s)
        self.assertEqual(v.status, "critico")
        self.assertIn("pocos mensajes", v.status_reason)
        self.assertIn("WhatsApp", v.next_decision)

    def test_alert_rule_turns_yellow(self):
        v = view_for(summary(HEALTHY, new_followers=300, messages_growth_pct=0.0))
        self.assertEqual(v.status, "alerta")
        self.assertIn("seguidores", v.bottleneck.lower())

    def test_big_drop_in_messages_is_critical_without_rules(self):
        v = view_for(summary(HEALTHY, messages_growth_pct=-35.0))
        self.assertEqual(v.status, "critico")

    def test_small_drop_in_messages_is_alert(self):
        v = view_for(summary(HEALTHY, messages_growth_pct=-5.0))
        self.assertEqual(v.status, "alerta")

    def test_markdown_contains_all_blocks(self):
        md = ManagerViewGenerator.to_markdown(view_for(summary(HEALTHY)))
        for block in ("Vista Gerente", "Estado:", "Logro principal", "Cuello de botella", "Próxima decisión"):
            self.assertIn(block, md)


if __name__ == "__main__":
    unittest.main()
