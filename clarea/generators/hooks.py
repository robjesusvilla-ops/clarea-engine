from typing import List

class HookGenerator:
    """Generates high-converting hooks and CTAs based on content categories."""

    @staticmethod
    def generate_hooks(topic: str, brand_name: str) -> List[str]:
        return [
            f"¿Cuánto cambia una propiedad cuando agregas un proyecto de {topic.lower()}?",
            f"Antes de invertir en {topic.lower()}, mira este detalle que el 90% ignora.",
            f"3 errores críticos que debes evitar al contratar servicios de {topic.lower()}.",
            f"Así es como transformamos un espacio vacío en un resultado premium con {brand_name}.",
            f"Lo que nadie te dice sobre los costos y el mantenimiento real en {topic.lower()}."
        ]

    @staticmethod
    def generate_ctas(topic: str) -> List[str]:
        return [
            f"Escríbenos '{topic.upper()}' al mensaje directo y te enviamos la guía de cotización.",
            "Agenda una evaluación técnica sin costo enviándonos una foto de tu espacio.",
            "Comenta 'INFO' y nuestro equipo te comparte 3 opciones adaptadas a tu presupuesto.",
            "Solicita una cotización personalizada con tiempo estimado de entrega aquí.",
            "Escríbenos por WhatsApp para hablar directamente con el especialista a cargo."
        ]
