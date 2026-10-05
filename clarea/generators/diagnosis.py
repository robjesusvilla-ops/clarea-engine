from typing import Dict, Any, List
from clarea.core.models import PeriodSummary, DiagnosticInsight
from clarea.core.analyzer import MetricAnalyzer
from clarea.core.rules import evaluate_rules
from clarea.core.attribution import FORMAT_LABELS, attribute

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
        best_format = ranked_formats[0]["format"] if ranked_formats else "photo"
        best_format = FORMAT_LABELS.get(best_format, best_format).lower()
        rule_findings = evaluate_rules(summary)
        problem = next((f for f in rule_findings if f.severity in ("critico", "alerta")), None)

        # Construct diagnosis logic
        findings = []
        if summary.reach_growth_pct > 0:
            findings.append(f"El alcance total creció +{summary.reach_growth_pct:.1f}%, logrando {summary.total_reach:,} personas alcanzadas.")
        else:
            findings.append(f"El alcance total se situó en {summary.total_reach:,} personas alcanzadas.")

        if problem:
            # The rules engine is the source of truth for the bottleneck, so the
            # diagnosis and the Manager View never disagree.
            bottleneck = f"{problem.title} ({problem.diagnosis[0].lower() + problem.diagnosis[1:].rstrip('.')})."
            if vanity_ratio > 3.0:
                findings.append(f"Ratio de vanidad elevado ({vanity_ratio}): muchos 'likes' y pocas cotizaciones ({conv_rate}%).")
            else:
                findings.append(f"Conversión comercial de {conv_rate}% del alcance a mensajes.")
        elif vanity_ratio > 3.0:
            bottleneck = "Conversión de atención a mensajes comerciales (fuga en el embudo de ventas)."
            findings.append(f"Ratio de vanidad elevado ({vanity_ratio}): alto volumen de 'likes' con baja tasa de solicitud de cotizaciones ({conv_rate}%).")
        else:
            bottleneck = "Escalabilidad de alcance para sostener la alta demanda de cotizaciones."
            findings.append(f"Excelente eficiencia de conversión comercial ({conv_rate}% de alcance convertido a mensajes).")

        summary_text = (
            f"{summary.brand_name} está capturando atención sólida en {summary.platform}, especialmente cuando publica contenido sobre '{best_topic}' en formato '{best_format}'. "
            f"Sin embargo, el principal desafío estratégico es: {bottleneck[0].lower() + bottleneck[1:]} "
            f"Para el siguiente ciclo, se requiere priorizar ganchos orientados a deseo y llamados a la acción de fricción cero."
        )

        generic_actions = [
            f"Duplicar la frecuencia de publicaciones sobre '{best_topic}' utilizando formato '{best_format}'.",
            "Sustituir llamados a la acción genéricos ('visita nuestro perfil') por CTAs directos a cotización en WhatsApp/Inbox.",
            "Crear contenidos educativos de dolor (costos, errores comunes, antes vs después) para filtrar prospectos calificados.",
            "Medir el retorno semanal por número de cotizaciones generadas en lugar de likes acumulados."
        ]
        # Rule prescriptions come first; generic actions fill the gaps without
        # repeating advice a rule already gave about the best topic.
        actions = [f.prescription for f in rule_findings]
        topic_covered = any(best_topic in f.prescription for f in rule_findings)
        for action in generic_actions[1:] if topic_covered else generic_actions:
            if len(actions) >= 4:
                break
            if action not in actions:
                actions.append(action)

        from clarea.generators.hooks import HookGenerator
        texts = [summary.brand_name] + [f"{p.topic} {p.caption_preview or ''}" for p in summary.posts]
        industry = HookGenerator.resolve_industry(summary.industry, texts)
        hook_ideas = HookGenerator.hook_ideas(summary.brand_name, industry)
        cta_ideas = HookGenerator.cta_ideas(summary.brand_name, industry)

        return DiagnosticInsight(
            executive_summary=summary_text,
            vanity_vs_business_ratio=vanity_ratio,
            key_findings=findings,
            best_performing_format=best_format,
            best_performing_topic=best_topic,
            primary_growth_bottleneck=bottleneck,
            recommended_actions=actions,
            suggested_hooks=[i.text for i in hook_ideas],
            suggested_ctas=[i.text for i in cta_ideas],
            rule_findings=rule_findings,
            industry=industry,
            hook_ideas=hook_ideas,
            cta_ideas=cta_ideas,
            attribution=attribute(summary)
        )
