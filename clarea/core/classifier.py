"""Infers a post's communication angle from its text when no topic was given."""
import re
import unicodedata
from typing import Optional

# Order matters: the first angle with a keyword match wins.
ANGLES = [
    ("Promoción / Venta", ["oferta", "descuento", "promo", "rebaja", "liquidacion", "2x1", "precio especial",
                           "solo por hoy", "ultimos cupos", "aprovecha"]),
    ("Educativo / Costos", ["cuanto cuesta", "cuanto sale", "costo", "errores", "error", "consejo", "tips",
                            "guia", "como elegir", "como mantener", "debes saber", "antes de", "mantenimiento",
                            "te explicamos", "aprende"]),
    ("Resultados / Proyectos", ["terminad", "entregad", "antes y despues", "resultado", "proyecto", "obra",
                                "transformacion", "asi quedo", "caso", "cliente feliz", "testimonio"]),
    ("Diseño / Renders", ["render", "3d", "diseno", "asi quedaria", "maqueta", "plano"]),
    ("Detrás de escena", ["detras", "proceso", "paso a paso", "nuestro equipo trabajando", "en obra", "asi hacemos"]),
    ("Institucional", ["feliz dia", "aniversario", "saludos", "felicidades", "navidad", "año nuevo", "ano nuevo",
                       "nuestro equipo", "gracias a"]),
]


def _norm(text: str) -> str:
    return unicodedata.normalize("NFKD", text.lower()).encode("ascii", "ignore").decode()


def infer_angle(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    blob = _norm(text)
    for angle, keywords in ANGLES:
        if any(re.search(r"\b" + re.escape(_norm(k)), blob) for k in keywords):
            return angle
    return None
