import re
from typing import Iterable, List, Optional

from clarea.core.models import ContentIdea
from clarea.knowledge.hooks_library import CTA_TYPES, HOOK_TYPES, INDUSTRIES

DEFAULT_INDUSTRY = "general"


class HookGenerator:
    """Generates hooks and CTAs adapted to the brand's industry."""

    @staticmethod
    def detect_industry(texts: Iterable[str]) -> str:
        """Picks the industry whose keywords appear most often in the given texts."""
        blob = " ".join(t for t in texts if t).lower()
        best, best_hits = DEFAULT_INDUSTRY, 0
        for key, data in INDUSTRIES.items():
            hits = sum(len(re.findall(r"\b" + re.escape(k), blob)) for k in data["keywords"])
            if hits > best_hits:
                best, best_hits = key, hits
        return best

    @staticmethod
    def resolve_industry(industry: Optional[str], texts: Iterable[str] = ()) -> str:
        if industry and industry.lower() in INDUSTRIES:
            return industry.lower()
        return HookGenerator.detect_industry(texts)

    @staticmethod
    def hook_ideas(brand_name: str, industry: str) -> List[ContentIdea]:
        hooks = INDUSTRIES[industry]["hooks"]
        return [
            ContentIdea(text=hooks[t].format(brand=brand_name),
                        type_name=HOOK_TYPES[t]["nombre"], why_it_works=HOOK_TYPES[t]["por_que"])
            for t in HOOK_TYPES
        ]

    @staticmethod
    def cta_ideas(brand_name: str, industry: str) -> List[ContentIdea]:
        ctas = INDUSTRIES[industry]["ctas"]
        return [
            ContentIdea(text=ctas[t].format(brand=brand_name),
                        type_name=CTA_TYPES[t]["nombre"], why_it_works=CTA_TYPES[t]["por_que"])
            for t in CTA_TYPES
        ]

    @staticmethod
    def generate_hooks(topic: str, brand_name: str, industry: Optional[str] = None) -> List[str]:
        ind = HookGenerator.resolve_industry(industry, [topic, brand_name])
        return [i.text for i in HookGenerator.hook_ideas(brand_name, ind)]

    @staticmethod
    def generate_ctas(topic: str, industry: Optional[str] = None, brand_name: str = "") -> List[str]:
        ind = HookGenerator.resolve_industry(industry, [topic, brand_name])
        return [i.text for i in HookGenerator.cta_ideas(brand_name, ind)]
