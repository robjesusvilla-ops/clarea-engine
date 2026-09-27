"""Motor de reglas de negocio: el "cerebro" de Clarea.

Cada regla detecta una situación en las métricas y devuelve un diagnóstico y
una prescripción, siguiendo las 6 reglas maestras del brief de producto.
Los umbrales son valores iniciales razonables y viven en `RuleThresholds`
para poder ajustarlos con datos reales.
"""
from dataclasses import dataclass
from typing import Callable, List, Optional

from clarea.core.models import PeriodSummary, PostMetric, RuleFinding

SEVERITY_ORDER = {"critico": 0, "alerta": 1, "oportunidad": 2}

SALES_KEYWORDS = (
    "oferta", "promo", "descuento", "precio", "compra", "cómpra", "venta",
    "rebaja", "liquidación", "liquidacion", "2x1", "sale",
)


@dataclass
class RuleThresholds:
    # Mínimos para que el análisis tenga sentido estadístico.
    min_reach: int = 1000
    min_likes: int = 100
    min_posts_per_topic: int = 2

    # Regla 1: mensajes / alcance por debajo de este % se considera "pocos".
    low_message_rate_pct: float = 0.10
    # Regla 2: likes por cada comentario a partir del cual el contenido es pasivo.
    passive_likes_per_comment: float = 30.0
    # Regla 3: un tema supera el benchmark si su tasa de mensajes es N veces la del resto.
    topic_outperform_factor: float = 1.5
    # Regla 4: guardados / alcance de un tema frente al resto del contenido.
    saves_outperform_factor: float = 2.0
    min_topic_saves_rate_pct: float = 1.0
    # Regla 5: seguidores nuevos mínimos y crecimiento de mensajes máximo.
    min_new_followers: int = 50
    max_messages_growth_pct: float = 5.0
    # Regla 6: engagement de posts de venta frente al resto.
    sales_engagement_drop_factor: float = 0.7


def _rate(part: int, whole: int) -> float:
    return (part / whole) * 100 if whole > 0 else 0.0


def _is_sales_post(post: PostMetric) -> bool:
    text = f"{post.topic} {post.caption_preview or ''}".lower()
    return any(k in text for k in SALES_KEYWORDS)


def _topics(summary: PeriodSummary) -> dict:
    grouped: dict = {}
    for p in summary.posts:
        grouped.setdefault(p.topic, []).append(p)
    return grouped


def rule_high_reach_low_messages(s: PeriodSummary, t: RuleThresholds) -> Optional[RuleFinding]:
    msg_rate = _rate(s.total_messages, s.total_reach)
    if s.total_reach < t.min_reach or msg_rate >= t.low_message_rate_pct:
        return None
    return RuleFinding(
        rule_id="R1",
        title="Alto alcance, pocos mensajes",
        severity="critico",
        diagnosis="El gancho atrae atención dispersa, pero la oferta o el puente comercial está roto.",
        prescription="Cambiar el CTA a fricción cero (WhatsApp directo con palabra clave) y filtrar la audiencia con contenido más específico.",
        evidence=f"{s.total_reach:,} de alcance y solo {s.total_messages} mensajes ({msg_rate:.3f}% del alcance).",
    )


def rule_likes_without_conversation(s: PeriodSummary, t: RuleThresholds) -> Optional[RuleFinding]:
    likes = sum(p.likes for p in s.posts)
    comments = sum(p.comments for p in s.posts)
    if likes < t.min_likes:
        return None
    ratio = likes / comments if comments else float("inf")
    if ratio < t.passive_likes_per_comment:
        return None
    ratio_txt = "sin comentarios" if comments == 0 else f"{ratio:.0f} likes por comentario"
    return RuleFinding(
        rule_id="R2",
        title="Muchos likes, casi sin conversación",
        severity="alerta",
        diagnosis="Contenido pasivo de entretenimiento o estética, sin tensión de compra.",
        prescription="Introducir preguntas de debate, encuestas de decisión o dilemas (ej. '¿Terraza abierta o techada?').",
        evidence=f"{likes:,} likes y {comments} comentarios ({ratio_txt}).",
    )


def rule_topic_outperforms(s: PeriodSummary, t: RuleThresholds) -> Optional[RuleFinding]:
    best = None
    for topic, posts in _topics(s).items():
        rest = [p for p in s.posts if p.topic != topic]
        if len(posts) < t.min_posts_per_topic or not rest:
            continue
        rate = _rate(sum(p.messages_inquired for p in posts), sum(p.reach for p in posts))
        rest_rate = _rate(sum(p.messages_inquired for p in rest), sum(p.reach for p in rest))
        if rest_rate > 0 and rate >= rest_rate * t.topic_outperform_factor and (best is None or rate > best[1]):
            best = (topic, rate, rest_rate)
    if best is None:
        return None
    topic, rate, rest_rate = best
    return RuleFinding(
        rule_id="R3",
        title=f"'{topic}' supera el promedio de la cuenta",
        severity="oportunidad",
        diagnosis="La prueba social y el resultado visible generan credibilidad inmediata.",
        prescription=f"Duplicar la frecuencia de '{topic}' con estructura 'Antes / Proceso / Entrega final'.",
        evidence=f"Convierte {rate:.2f}% del alcance en mensajes vs {rest_rate:.2f}% del resto del contenido ({rate / rest_rate:.1f}x).",
    )


def rule_high_saves(s: PeriodSummary, t: RuleThresholds) -> Optional[RuleFinding]:
    best = None
    for topic, posts in _topics(s).items():
        rest = [p for p in s.posts if p.topic != topic]
        if not rest:
            continue
        rate = _rate(sum(p.saves for p in posts), sum(p.reach for p in posts))
        rest_rate = _rate(sum(p.saves for p in rest), sum(p.reach for p in rest))
        if (rest_rate > 0
                and rate >= t.min_topic_saves_rate_pct
                and rate >= rest_rate * t.saves_outperform_factor
                and (best is None or rate > best[1])):
            best = (topic, rate, rest_rate)
    if best is None:
        return None
    topic, rate, rest_rate = best
    return RuleFinding(
        rule_id="R4",
        title=f"Muchos guardados en '{topic}'",
        severity="oportunidad",
        diagnosis="La audiencia está investigando y comparando proveedores activamente.",
        prescription="Publicar guías de costos, comparativas de materiales y checklists de errores comunes antes de contratar.",
        evidence=f"{rate:.2f}% del alcance guarda este contenido vs {rest_rate:.2f}% en el resto.",
    )


def rule_followers_without_leads(s: PeriodSummary, t: RuleThresholds) -> Optional[RuleFinding]:
    if s.new_followers < t.min_new_followers or s.messages_growth_pct > t.max_messages_growth_pct:
        return None
    return RuleFinding(
        rule_id="R5",
        title="Crecen seguidores, no crecen los clientes potenciales",
        severity="alerta",
        diagnosis="Crecimiento de vanidad desconectado del perfil del comprador calificado.",
        prescription="Publicar ofertas directas, contenido que derribe objeciones y garantías comerciales.",
        evidence=f"+{s.new_followers} seguidores nuevos, pero los mensajes variaron {s.messages_growth_pct:+.1f}%.",
    )


def rule_sales_posts_drop(s: PeriodSummary, t: RuleThresholds) -> Optional[RuleFinding]:
    sales = [p for p in s.posts if _is_sales_post(p)]
    others = [p for p in s.posts if not _is_sales_post(p)]
    if not sales or not others:
        return None
    sales_eng = _rate(sum(p.interactions for p in sales), sum(p.reach for p in sales))
    other_eng = _rate(sum(p.interactions for p in others), sum(p.reach for p in others))
    if other_eng == 0 or sales_eng >= other_eng * t.sales_engagement_drop_factor:
        return None
    return RuleFinding(
        rule_id="R6",
        title="Caída de engagement en publicaciones de venta directa",
        severity="alerta",
        diagnosis="El público rechaza la venta agresiva sin contexto de valor previo.",
        prescription="Pasar de 'Cómpranos hoy' a contenido de deseo, solución de problemas y prueba de retorno de inversión.",
        evidence=f"Posts de venta: {sales_eng:.1f}% de engagement vs {other_eng:.1f}% en el resto ({len(sales)} de {len(s.posts)} posts).",
    )


RULES: List[Callable[[PeriodSummary, RuleThresholds], Optional[RuleFinding]]] = [
    rule_high_reach_low_messages,
    rule_likes_without_conversation,
    rule_topic_outperforms,
    rule_high_saves,
    rule_followers_without_leads,
    rule_sales_posts_drop,
]


def evaluate_rules(summary: PeriodSummary, thresholds: Optional[RuleThresholds] = None) -> List[RuleFinding]:
    """Runs every rule and returns the triggered ones, most severe first."""
    t = thresholds or RuleThresholds()
    findings = [f for rule in RULES if (f := rule(summary, t)) is not None]
    return sorted(findings, key=lambda f: SEVERITY_ORDER[f.severity])
