import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from clarea.generators.diagnosis import DiagnosisEngine
from clarea.generators.hooks import HookGenerator
from clarea.knowledge.hooks_library import CTA_TYPES, HOOK_TYPES, INDUSTRIES
from tests.test_rules import post, summary


class TestIndustryDetection(unittest.TestCase):
    def test_detects_from_brand_and_topics(self):
        self.assertEqual(HookGenerator.detect_industry(["Qhatai Piscinas", "Proyectos Terminados"]), "piscinas")
        self.assertEqual(HookGenerator.detect_industry(["Sushi Kenji", "Promos de la semana"]), "restaurante")
        self.assertEqual(HookGenerator.detect_industry(["Salón Bella", "Uñas acrílicas"]), "belleza")

    def test_unknown_falls_back_to_general(self):
        self.assertEqual(HookGenerator.detect_industry(["TESGA", "Solar Energy"]), "general")

    def test_keywords_match_word_start_only(self):
        # 'espacio' must not be read as 'spa' (belleza).
        self.assertEqual(HookGenerator.detect_industry(["Un espacio vacío"]), "general")

    def test_explicit_industry_wins(self):
        self.assertEqual(HookGenerator.resolve_industry("Belleza", ["Qhatai Piscinas"]), "belleza")

    def test_invalid_explicit_industry_is_detected_instead(self):
        self.assertEqual(HookGenerator.resolve_industry("astronautas", ["Qhatai Piscinas"]), "piscinas")


class TestLibrary(unittest.TestCase):
    def test_every_industry_covers_every_type(self):
        for key, data in INDUSTRIES.items():
            self.assertEqual(set(data["hooks"]), set(HOOK_TYPES), key)
            self.assertEqual(set(data["ctas"]), set(CTA_TYPES), key)

    def test_ideas_explain_why_and_fill_brand(self):
        ideas = HookGenerator.hook_ideas("Kenji", "restaurante")
        self.assertTrue(all(i.why_it_works for i in ideas))
        self.assertTrue(any("Kenji" in i.text for i in ideas))
        self.assertFalse(any("{brand}" in i.text for i in ideas))


class TestDiagnosisUsesIndustry(unittest.TestCase):
    def test_restaurant_account_gets_restaurant_ctas(self):
        s = summary([post("a", "Platos del día", 1000, likes=50, comments=5, messages=5),
                     post("b", "Menú ejecutivo", 1000, likes=50, comments=5, messages=5)])
        s.brand_name = "Sushi Kenji"
        insight = DiagnosisEngine.generate_local_insight(s)
        self.assertEqual(insight.industry, "restaurante")
        self.assertTrue(any("MENU" in c for c in insight.suggested_ctas))

    def test_summary_industry_field_overrides_detection(self):
        s = summary([post("a", "Piscinas", 1000, messages=5)])
        s.industry = "inmobiliaria"
        self.assertEqual(DiagnosisEngine.generate_local_insight(s).industry, "inmobiliaria")


if __name__ == "__main__":
    unittest.main()
