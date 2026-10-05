"""Módulo 4: qué funcionó y qué falló, por formato y por tema.

Each group is compared against the account average. Conversion to messages
decides the verdict; engagement only breaks ties, because Clarea measures
business, not applause.
"""
from collections import defaultdict
from typing import List

from clarea.core.models import AttributionItem, PeriodSummary

WORKED_INDEX = 1.25   # converts 25%+ better than the account average
FAILED_INDEX = 0.6    # converts 40%+ worse than the account average
FORMAT_LABELS = {"photo": "Foto", "video": "Video", "reel": "Reel", "carousel": "Carrusel", "text": "Texto"}


def _rate(part: int, whole: int) -> float:
    return part / whole * 100 if whole else 0.0


def attribute(summary: PeriodSummary) -> List[AttributionItem]:
    posts = summary.posts
    reach = sum(p.reach for p in posts)
    account_conv = _rate(sum(p.messages_inquired for p in posts), reach)
    account_eng = _rate(sum(p.interactions for p in posts), reach)
    items: List[AttributionItem] = []

    for dimension, key, label in (("formato", lambda p: p.content_type, lambda k: FORMAT_LABELS.get(k, k)),
                                  ("tema", lambda p: p.topic, lambda k: k)):
        groups = defaultdict(list)
        for p in posts:
            groups[key(p)].append(p)
        if len(groups) < 2:
            continue  # nothing to compare against
        for name, group in groups.items():
            g_reach = sum(p.reach for p in group)
            conv = _rate(sum(p.messages_inquired for p in group), g_reach)
            eng = _rate(sum(p.interactions for p in group), g_reach)
            conv_idx = conv / account_conv if account_conv else 0.0
            eng_idx = eng / account_eng if account_eng else 0.0

            if account_conv and conv_idx >= WORKED_INDEX:
                verdict = "funciono"
                reason = f"Convierte {conv_idx:.1f}x más que el promedio de la cuenta ({conv:.2f}% vs {account_conv:.2f}%)."
            elif account_conv and conv_idx <= FAILED_INDEX:
                verdict = "fallo"
                reason = f"Convierte {conv_idx:.1f}x el promedio ({conv:.2f}% vs {account_conv:.2f}%)"
                reason += ": genera atención pero no clientes." if eng_idx >= 1 else ": no genera atención ni mensajes."
            elif not account_conv and eng_idx >= WORKED_INDEX:
                verdict = "funciono"
                reason = f"Engagement {eng_idx:.1f}x el promedio, aunque aún sin mensajes."
            else:
                verdict = "neutral"
                reason = f"Rinde cerca del promedio ({conv:.2f}% de conversión)."

            items.append(AttributionItem(
                dimension=dimension, name=label(name), posts=len(group), reach=g_reach,
                conversion_rate=round(conv, 3), engagement_rate=round(eng, 2),
                conversion_index=round(conv_idx, 2), verdict=verdict, reason=reason,
                preliminary=len(group) < 2,
            ))

    items.sort(key=lambda i: i.conversion_index, reverse=True)
    return items
