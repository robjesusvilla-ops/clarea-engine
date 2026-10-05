import json
import unittest
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).parent.parent))

from clarea.ai.claude_diagnosis import CUSTOM_HOOK_TYPE, enrich_insight
from clarea.core.prompts import build_diagnosis_prompt
from clarea.core.analyzer import MetricAnalyzer
from clarea.generators.diagnosis import DiagnosisEngine
from clarea.pipeline import analyze
from tests.test_rules import post, summary

AI_PAYLOAD = {
    "executive_summary": "Resumen escrito por Claude.",
    "key_findings": ["Hallazgo 1", "Hallazgo 2", "Hallazgo 3"],
    "primary_growth_bottleneck": "Pocos mensajes por cada persona alcanzada.",
    "recommended_actions": ["Acción 1", "Acción 2", "Acción 3", "Acción 4"],
    "custom_hooks": [{"text": "¿Tu patio podría ser esto?", "why_it_works": "Despierta deseo."}],
}


class FakeClient:
    """Mimics client.beta.messages.create and records the request."""

    def __init__(self, text=None, stop_reason="end_turn", raises=None):
        self.kwargs = None
        self._text = json.dumps(AI_PAYLOAD) if text is None else text
        self._stop = stop_reason
        self._raises = raises
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.kwargs = kwargs
        if self._raises:
            raise self._raises
        return SimpleNamespace(stop_reason=self._stop,
                               content=[SimpleNamespace(type="text", text=self._text)])


def account():
    return summary([post("a", "Obras", 20000, likes=50, comments=5, messages=5, caption="Piscina terminada")])


class TestAIDiagnosis(unittest.TestCase):
    def test_merges_ai_text_and_keeps_rules(self):
        s = account()
        local = DiagnosisEngine.generate_local_insight(s)
        enriched, error = enrich_insight(s, local, FakeClient())
        self.assertIsNone(error)
        self.assertTrue(enriched.ai_generated)
        self.assertEqual(enriched.executive_summary, "Resumen escrito por Claude.")
        self.assertEqual(enriched.rule_findings, local.rule_findings)
        self.assertEqual(enriched.hook_ideas[0].type_name, CUSTOM_HOOK_TYPE)
        self.assertEqual(len(enriched.hook_ideas), len(local.hook_ideas) + 1)

    def test_request_uses_structured_output_and_fallbacks(self):
        fake = FakeClient()
        enrich_insight(account(), DiagnosisEngine.generate_local_insight(account()), fake)
        self.assertEqual(fake.kwargs["model"], "claude-opus-5-5")
        self.assertEqual(fake.kwargs["fallbacks"], "default")
        self.assertIn("server-side-fallback-2026-07-01", fake.kwargs["betas"])
        self.assertEqual(fake.kwargs["output_config"]["format"]["type"], "json_schema")
        self.assertIn("Alto alcance, pocos mensajes", fake.kwargs["messages"][0]["content"])

    def test_failures_fall_back_to_local(self):
        s = account()
        local = DiagnosisEngine.generate_local_insight(s)
        for fake in (FakeClient(raises=RuntimeError("sin red")), FakeClient(stop_reason="refusal"),
                     FakeClient(text="no es json"), FakeClient(stop_reason="max_tokens")):
            result, error = enrich_insight(s, local, fake)
            self.assertIs(result, local)
            self.assertTrue(error)

    def test_pipeline_flag(self):
        result = analyze(account(), use_ai=True, ai_client=FakeClient())
        self.assertTrue(result.insight.ai_generated)
        self.assertIsNone(result.ai_error)
        self.assertFalse(analyze(account()).insight.ai_generated)

    def test_prompt_contains_numbers_and_top_posts(self):
        s = account()
        insight = DiagnosisEngine.generate_local_insight(s)
        prompt = build_diagnosis_prompt(s, insight, MetricAnalyzer(s).rank_posts()[:3])
        self.assertIn("20,000", prompt)
        self.assertIn("Piscina terminada", prompt)


if __name__ == "__main__":
    unittest.main()
