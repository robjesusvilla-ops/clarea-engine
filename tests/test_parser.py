import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from clarea.core.classifier import infer_angle
from clarea.core.parser import MetricParser, UNCLASSIFIED_TOPIC, _to_int, growth_pct

EXAMPLES = Path(__file__).parent.parent / "examples"


class TestNumbers(unittest.TestCase):
    def test_thousand_separators_and_decimals(self):
        self.assertEqual(_to_int("9.200"), 9200)
        self.assertEqual(_to_int("9,200"), 9200)
        self.assertEqual(_to_int("1 234"), 1234)
        self.assertEqual(_to_int("12,5"), 12)
        self.assertEqual(_to_int(""), 0)
        self.assertEqual(_to_int(None), 0)

    def test_growth(self):
        self.assertEqual(growth_pct(120, 100), 20.0)
        self.assertEqual(growth_pct(5, 0), 0.0)


class TestCsv(unittest.TestCase):
    def test_clarea_template(self):
        s = MetricParser.load(EXAMPLES / "plantilla_metricas_mayo.csv", "Qhatai", "Mayo")
        self.assertEqual(s.posts_count, 8)
        self.assertEqual(s.posts[0].topic, "Proyectos Terminados")
        self.assertEqual(s.posts[1].content_type, "carousel")
        self.assertEqual(s.total_messages, sum(p.messages_inquired for p in s.posts))

    def test_meta_export_semicolon_spanish_headers(self):
        s = MetricParser.load(EXAMPLES / "export_meta_business_suite.csv", "Qhatai", "Mayo")
        self.assertEqual(s.posts_count, 8)
        self.assertEqual(s.posts[0].reach, 9200)
        self.assertEqual(s.posts[0].messages_inquired, 34)
        # No topic column: the angle is inferred from the text.
        self.assertEqual(s.posts[0].topic, "Resultados / Proyectos")
        # No interactions column: computed from reactions, comments and shares.
        self.assertEqual(s.posts[0].interactions, 560 + 64 + 42)

    def test_missing_reach_column_is_a_clear_error(self):
        with self.assertRaises(ValueError) as ctx:
            MetricParser.posts_from_csv_text("id,likes\n1,10\n")
        self.assertIn("alcance", str(ctx.exception))

    def test_unknown_text_stays_unclassified(self):
        posts = MetricParser.posts_from_csv_text("alcance,texto\n100,Hola\n")
        self.assertEqual(posts[0].topic, UNCLASSIFIED_TOPIC)

    def test_previous_period_fills_growth(self):
        cur = MetricParser.load(EXAMPLES / "plantilla_metricas_mayo.csv", "Q", "Mayo")
        prev = MetricParser.load(EXAMPLES / "plantilla_metricas_abril.csv", "Q", "Abril")
        MetricParser.apply_previous_period(cur, prev)
        self.assertGreater(cur.messages_growth_pct, 0)
        self.assertEqual(cur.reach_growth_pct, growth_pct(cur.total_reach, prev.total_reach))

    def test_unsupported_format(self):
        with self.assertRaises(ValueError):
            MetricParser.load("datos.xlsx")


class TestClassifier(unittest.TestCase):
    def test_angles(self):
        self.assertEqual(infer_angle("Oferta de temporada: 10% de descuento"), "Promoción / Venta")
        self.assertEqual(infer_angle("¿Cuánto cuesta mantener una piscina?"), "Educativo / Costos")
        self.assertEqual(infer_angle("Proyecto terminado en La Molina"), "Resultados / Proyectos")
        self.assertEqual(infer_angle("Feliz día a nuestro equipo"), "Institucional")
        self.assertIsNone(infer_angle("Hola"))
        self.assertIsNone(infer_angle(None))


if __name__ == "__main__":
    unittest.main()
