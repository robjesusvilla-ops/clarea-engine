import csv
import io
import json
import re
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from clarea.core.classifier import infer_angle
from clarea.core.models import PeriodSummary, PostMetric

UNCLASSIFIED_TOPIC = "Sin clasificar"

# Column aliases, normalized (lowercase, no accents). The first alias that matches
# a CSV header wins. Covers our own template plus common Meta Business Suite
# export headers in Spanish and English.
COLUMN_ALIASES: Dict[str, List[str]] = {
    "id": ["id", "post id", "identificador de la publicacion", "id de la publicacion"],
    "content_type": ["content_type", "tipo", "formato", "tipo de publicacion", "post type", "type"],
    "topic": ["topic", "tema", "categoria", "category", "pilar"],
    "reach": ["reach", "alcance", "personas alcanzadas", "post reach"],
    "impressions": ["impressions", "impresiones", "visualizaciones", "views"],
    "interactions": ["interactions", "interacciones", "engagement", "post engagement"],
    "likes": ["likes", "reacciones", "me gusta", "reactions"],
    "comments": ["comments", "comentarios"],
    "shares": ["shares", "compartidos", "veces que se compartio", "veces compartido"],
    "saves": ["saves", "guardados", "veces que se guardo"],
    "clicks": ["clicks", "clics", "clics totales", "total clicks", "link clicks"],
    "messages": ["messages", "messages_inquired", "mensajes", "conversaciones iniciadas",
                 "conversaciones con mensajes iniciadas", "messaging conversations started", "cotizaciones"],
    "published_date": ["published_date", "fecha", "fecha de publicacion", "hora de publicacion", "publish time", "date"],
    "caption_preview": ["caption_preview", "texto", "descripcion", "titulo", "caption", "description", "title", "mensaje"],
}

CONTENT_TYPES = {
    "foto": "photo", "photo": "photo", "imagen": "photo", "image": "photo",
    "video": "video", "videos": "video",
    "reel": "reel", "reels": "reel",
    "carrusel": "carousel", "carousel": "carousel", "album": "carousel", "multi foto": "carousel",
    "texto": "text", "text": "text", "estado": "text", "status": "text", "enlace": "text", "link": "text",
}


def _norm(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", text.strip().lower())


def _to_int(value: Any) -> int:
    """Parses '1,234', '1.234', '1 234' or '' into an int (metrics are whole numbers)."""
    text = str(value or "").strip()
    text = re.sub(r"[.,]\d{1,2}$", "", text)  # drop decimals such as '12,5' or '12.50'
    digits = re.sub(r"[^\d-]", "", text)
    return int(digits) if digits not in ("", "-") else 0


def _content_type(value: str) -> str:
    return CONTENT_TYPES.get(_norm(value), _norm(value) or "photo")


def _map_columns(headers: List[str]) -> Dict[str, str]:
    normalized = {_norm(h): h for h in headers if h}
    mapping = {}
    for field, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            if alias in normalized:
                mapping[field] = normalized[alias]
                break
    return mapping


def growth_pct(current: float, previous: float) -> float:
    if previous == 0:
        return 0.0
    return round((current - previous) / previous * 100, 1)


class MetricParser:
    """Parses raw marketing metrics from JSON, CSV or Meta Graph API payloads."""

    @staticmethod
    def from_json_file(file_path: Union[str, Path]) -> PeriodSummary:
        with open(file_path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
        return PeriodSummary(**data)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> PeriodSummary:
        return PeriodSummary(**data)

    @staticmethod
    def posts_from_csv_text(text: str) -> List[PostMetric]:
        sample = text[:4096]
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
        except csv.Error:
            dialect = csv.excel
        reader = csv.DictReader(io.StringIO(text), dialect=dialect)
        cols = _map_columns(reader.fieldnames or [])
        if "reach" not in cols:
            raise ValueError(
                "El CSV necesita al menos una columna de alcance ('alcance' o 'reach'). "
                f"Columnas encontradas: {', '.join(reader.fieldnames or [])}"
            )

        def get(row, field, default=""):
            col = cols.get(field)
            return row.get(col, default) if col else default

        posts = []
        for idx, row in enumerate(reader):
            if not any((v or "").strip() for v in row.values()):
                continue
            likes, comments = _to_int(get(row, "likes")), _to_int(get(row, "comments"))
            shares, saves = _to_int(get(row, "shares")), _to_int(get(row, "saves"))
            interactions = _to_int(get(row, "interactions")) or (likes + comments + shares + saves)
            reach = _to_int(get(row, "reach"))
            caption = (get(row, "caption_preview") or "").strip()
            topic = (get(row, "topic") or "").strip() or infer_angle(caption) or UNCLASSIFIED_TOPIC
            posts.append(PostMetric(
                id=(get(row, "id") or f"post_{idx + 1}").strip(),
                content_type=_content_type(get(row, "content_type", "photo")),
                topic=topic,
                reach=reach,
                impressions=_to_int(get(row, "impressions")) or reach,
                interactions=interactions,
                likes=likes,
                comments=comments,
                shares=shares,
                saves=saves,
                clicks=_to_int(get(row, "clicks")),
                messages_inquired=_to_int(get(row, "messages")),
                published_date=(get(row, "published_date") or None),
                caption_preview=(caption[:160] or None),
            ))
        return posts

    @staticmethod
    def summary_from_posts(posts: List[PostMetric], brand_name: str, period_label: str,
                           industry: Optional[str] = None, new_followers: int = 0,
                           platform: str = "Facebook") -> PeriodSummary:
        """Builds a period summary when only post-level data exists.

        Page-level reach (unique people) is not available from post rows, so the
        sum of post reach is used as an approximation.
        """
        return PeriodSummary(
            brand_name=brand_name,
            platform=platform,
            industry=industry,
            period_label=period_label,
            total_reach=sum(p.reach for p in posts),
            reach_growth_pct=0.0,
            total_interactions=sum(p.interactions for p in posts),
            interactions_growth_pct=0.0,
            total_messages=sum(p.messages_inquired for p in posts),
            messages_growth_pct=0.0,
            new_followers=new_followers,
            posts_count=len(posts),
            posts=posts,
        )

    @staticmethod
    def from_csv_file(file_path: Union[str, Path], brand_name: str, period_label: str,
                      industry: Optional[str] = None, new_followers: int = 0) -> PeriodSummary:
        text = Path(file_path).read_text(encoding="utf-8-sig")
        posts = MetricParser.posts_from_csv_text(text)
        return MetricParser.summary_from_posts(posts, brand_name, period_label, industry, new_followers)

    @staticmethod
    def load(file_path: Union[str, Path], brand_name: str = "Brand", period_label: str = "Periodo actual",
             industry: Optional[str] = None, new_followers: int = 0) -> PeriodSummary:
        """Loads a .json or .csv metrics file."""
        path = Path(file_path)
        suffix = path.suffix.lower()
        if suffix == ".json":
            summary = MetricParser.from_json_file(path)
            if industry:
                summary.industry = industry
            return summary
        if suffix == ".csv":
            return MetricParser.from_csv_file(path, brand_name, period_label, industry, new_followers)
        raise ValueError(f"Formato no soportado: {suffix}. Usa .json o .csv")

    @staticmethod
    def apply_previous_period(current: PeriodSummary, previous: PeriodSummary) -> PeriodSummary:
        """Fills the growth percentages by comparing against the previous period."""
        current.reach_growth_pct = growth_pct(current.total_reach, previous.total_reach)
        current.interactions_growth_pct = growth_pct(current.total_interactions, previous.total_interactions)
        current.messages_growth_pct = growth_pct(current.total_messages, previous.total_messages)
        return current
