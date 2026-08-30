from typing import Dict, Any, List
from clarea.core.models import PeriodSummary, DiagnosticInsight
from clarea.core.analyzer import MetricAnalyzer

class DiagnosisEngine:
    """Generates the signature 'Interpretado por Clarea' business decision breakdown."""

    @staticmethod
    def generate_local_insight(summary: PeriodSummary) -> DiagnosticInsight:
        analyzer = MetricAnalyzer(summary)
        eng_rate = analyzer.calculate_engagement_rate()
        conv_rate = analyzer.calculate_message_conversion_rate()
        vanity_ratio = analyzer.calculate_vanity_vs_business_ratio()
        ranked_topics = analyzer.rank_topics_by_intent()
        ranked_formats = analyzer.rank_formats()

        best_topic = ranked_topics[0]["topic"] if ranked_topics else "General"
        best_format = ranked_formats[0]["format"] if ranked_formats else "Photo"

        # Construct diagnosis logic
        findings = []
        if summary.reach_growth_pct > 0:
            findings.append(f"El alcance total creció +{summary.reach_growth_pct:.1f}%, logrando {summary.total_reach:,} personas alcanzadas.")
        else:
            findings.append(f"El alcance total se situó en {summary.total_reach:,} personas alcanzadas.")

        if vanity_ratio > 3.0:
            bottleneck = "Conversión de atención a mensajes comerciales (fuga en el embudo de ventas)."
            findings.append(f"Ratio de vanidad elevado ({vanity_ratio}): alto volumen de 'likes' con baja tasa de solicitud de cotizaciones ({conv_rate}%).")
        else:
            bottleneck = "Escalabilidad de alcance para sostener la alta demanda de cotizaciones."
            findings.append(f"Excelente eficiencia de conversión comercial ({conv_rate}% de alcance convertido a mensajes).")

        summary_text = (
            f"{summary.brand_name} está capturando atención sólida en {summary.platform}, especialmente cuando publica contenido sobre '{best_topic}' en formato '{best_format}'. "
            f"Sin embargo, el principal desafío estratégico es {bottleneck.lower()} "
            f"Para el siguiente ciclo, se requiere priorizar ganchos orientados a deseo y llamados a la acción de fricción cero."
        )

        actions = [
            f"Duplicar la frecuencia de publicaciones sobre '{best_topic}' utilizando formato '{best_format}'.",
            "Sustituir llamados a la acción genéricos ('visita nuestro perfil') por CTAs directos a cotización en WhatsApp/Inbox.",
            "Crear contenidos educativos de dolor (costos, errores comunes, antes vs después) para filtrar prospectos calificados.",
            "Medir el retorno semanal por número de cotizaciones generadas en lugar de likes acumulados."
        ]

        from clarea.generators.hooks import HookGenerator
        hooks = HookGenerator.generate_hooks(best_topic, summary.brand_name)
        ctas = HookGenerator.generate_ctas(best_topic)

        return DiagnosticInsight(
            executive_summary=summary_text,
            vanity_vs_business_ratio=vanity_ratio,
            key_findings=findings,
            best_performing_format=best_format,
            best_performing_topic=best_topic,
            primary_growth_bottleneck=bottleneck,
            recommended_actions=actions,
            suggested_hooks=hooks,
            suggested_ctas=ctas
        )
