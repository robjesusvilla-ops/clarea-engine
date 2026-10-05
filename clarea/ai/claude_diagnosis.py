"""Optional AI layer: Claude writes the diagnosis on top of the rules engine.

Needs the `anthropic` package (pip install -e ".[ai]") and credentials in
ANTHROPIC_API_KEY. Without them, or on any API failure, the local diagnosis is
returned unchanged, so Clarea never stops working because of the AI.
"""
import json
import os
from typing import List, Optional, Tuple

from pydantic import BaseModel, ValidationError

from clarea.core.analyzer import MetricAnalyzer
from clarea.core.models import ContentIdea, DiagnosticInsight, PeriodSummary
from clarea.core.prompts import SYSTEM_PROMPT, build_diagnosis_prompt

MODEL = os.environ.get("CLAREA_AI_MODEL", "claude-opus-5-5")
CUSTOM_HOOK_TYPE = "A medida (IA)"


class _Hook(BaseModel):
    text: str
    why_it_works: str


class AIDiagnosis(BaseModel):
    executive_summary: str
    key_findings: List[str]
    primary_growth_bottleneck: str
    recommended_actions: List[str]
    custom_hooks: List[_Hook]


OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "executive_summary": {"type": "string"},
        "key_findings": {"type": "array", "items": {"type": "string"}},
        "primary_growth_bottleneck": {"type": "string"},
        "recommended_actions": {"type": "array", "items": {"type": "string"}},
        "custom_hooks": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"text": {"type": "string"}, "why_it_works": {"type": "string"}},
                "required": ["text", "why_it_works"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["executive_summary", "key_findings", "primary_growth_bottleneck",
                 "recommended_actions", "custom_hooks"],
    "additionalProperties": False,
}


def _default_client():
    try:
        import anthropic
    except ImportError:
        return None, "Falta el paquete 'anthropic'. Instálalo con: pip install -e \".[ai]\""
    try:
        return anthropic.Anthropic(), None
    except Exception as e:  # missing credentials raise at construction in some setups
        return None, f"No se pudo iniciar el cliente de Claude: {e}"


def request_ai_diagnosis(summary: PeriodSummary, insight: DiagnosticInsight,
                         client=None) -> Tuple[Optional[AIDiagnosis], Optional[str]]:
    """Returns (diagnosis, None) on success or (None, reason) when the AI is unavailable."""
    if client is None:
        client, error = _default_client()
        if client is None:
            return None, error

    top_posts = MetricAnalyzer(summary).rank_posts()[:3]
    try:
        response = client.beta.messages.create(
            model=MODEL,
            max_tokens=16000,
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            system=SYSTEM_PROMPT,
            output_config={"effort": "medium", "format": {"type": "json_schema", "schema": OUTPUT_SCHEMA}},
            messages=[{"role": "user", "content": build_diagnosis_prompt(summary, insight, top_posts)}],
        )
    except Exception as e:
        if "authentication" in str(e).lower() or "api_key" in str(e).lower():
            return None, "No hay credenciales de Claude. Guarda tu clave en la variable ANTHROPIC_API_KEY."
        return None, f"La API de Claude falló ({type(e).__name__}): {e}"

    if response.stop_reason == "refusal":
        return None, "Claude declinó la solicitud."
    if response.stop_reason == "max_tokens":
        return None, "La respuesta de Claude quedó incompleta."
    text = next((b.text for b in response.content if b.type == "text"), "")
    try:
        return AIDiagnosis.model_validate(json.loads(text)), None
    except (json.JSONDecodeError, ValidationError) as e:
        return None, f"La respuesta de Claude no tenía el formato esperado: {e}"


def enrich_insight(summary: PeriodSummary, insight: DiagnosticInsight,
                   client=None) -> Tuple[DiagnosticInsight, Optional[str]]:
    """Merges Claude's diagnosis into the local insight. Rule findings and metrics are kept."""
    ai, error = request_ai_diagnosis(summary, insight, client)
    if ai is None:
        return insight, error
    enriched = insight.model_copy(update={
        "executive_summary": ai.executive_summary,
        "key_findings": ai.key_findings or insight.key_findings,
        "primary_growth_bottleneck": ai.primary_growth_bottleneck,
        "recommended_actions": ai.recommended_actions or insight.recommended_actions,
        "hook_ideas": [ContentIdea(text=h.text, type_name=CUSTOM_HOOK_TYPE, why_it_works=h.why_it_works)
                       for h in ai.custom_hooks] + insight.hook_ideas,
        "ai_generated": True,
    })
    return enriched, None
