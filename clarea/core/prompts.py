"""Prompts for the AI layer. The rules engine stays the source of truth:
Claude explains and expands it for a business owner, it never overrides it."""
from typing import List

from clarea.core.models import DiagnosticInsight, PeriodSummary

SYSTEM_PROMPT = """Eres Clarea, un estratega de marketing en redes sociales para negocios pequeños y agencias en Latinoamérica.
Tu lector es el dueño de un negocio que no sabe de marketing: escríbele en español claro, directo y concreto, sin tecnicismos.
Si usas un término como hook, CTA o engagement, explícalo en pocas palabras.

Reglas de trabajo:
- Las "situaciones detectadas" vienen del motor de reglas de Clarea, basado en la experiencia de un consultor. Son verdad: explícalas y construye sobre ellas, nunca las contradigas.
- Usa solo los números que te damos. No inventes cifras, porcentajes ni comparaciones con otras marcas.
- Separa siempre atención (alcance, likes) de intención comercial (mensajes, cotizaciones). Lo que importa es lo segundo.
- Las recomendaciones deben poder hacerse la semana siguiente, con el contenido y el rubro de este negocio.
- Los hooks a medida deben inspirarse en las publicaciones que mejor convirtieron y sonar naturales para el rubro."""


def _fmt_list(items: List[str]) -> str:
    return "\n".join(f"- {i}" for i in items) or "- (ninguna)"


def build_diagnosis_prompt(summary: PeriodSummary, insight: DiagnosticInsight, top_posts: List[dict]) -> str:
    findings = _fmt_list([f"[{f.severity}] {f.title}. {f.diagnosis} Dato: {f.evidence} Qué hacer: {f.prescription}"
                          for f in insight.rule_findings])
    attribution = _fmt_list([f"{a.verdict.upper()} · {a.dimension} '{a.name}': {a.reason}"
                             for a in insight.attribution if a.verdict != "neutral"])
    posts = _fmt_list([f"{r['post'].topic} ({r['post'].content_type}): \"{r['post'].caption_preview or ''}\" — "
                       f"alcance {r['post'].reach:,}, mensajes {r['post'].messages_inquired}, score {r['score']}/100"
                       for r in top_posts])
    return f"""Analiza el periodo "{summary.period_label}" de {summary.brand_name} en {summary.platform} (rubro: {insight.industry}).

MÉTRICAS DEL PERIODO
- Alcance: {summary.total_reach:,} ({summary.reach_growth_pct:+.1f}% vs periodo anterior)
- Interacciones: {summary.total_interactions:,} ({summary.interactions_growth_pct:+.1f}%)
- Mensajes de venta: {summary.total_messages:,} ({summary.messages_growth_pct:+.1f}%)
- Seguidores nuevos: {summary.new_followers:,}
- Publicaciones: {summary.posts_count}
- Ratio vanidad/negocio: {insight.vanity_vs_business_ratio} (menor es mejor)

SITUACIONES DETECTADAS POR EL MOTOR DE REGLAS
{findings}

QUÉ FUNCIONÓ Y QUÉ FALLÓ
{attribution}

PUBLICACIONES CON MEJOR SCORE
{posts}

Entrega:
1. executive_summary: 3 a 4 frases. Qué pasó, por qué, y cuál es la brecha comercial.
2. key_findings: 3 a 5 hallazgos concretos con sus números.
3. primary_growth_bottleneck: una frase con el principal freno para conseguir más clientes.
4. recommended_actions: 4 acciones para la próxima semana, de la más a la menos importante. Incluye las prescripciones de las situaciones detectadas.
5. custom_hooks: 3 hooks escritos para este negocio, cada uno con una explicación corta de por qué funciona."""
