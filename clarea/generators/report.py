from typing import Optional
from clarea.core.models import PeriodSummary, DiagnosticInsight
from clarea.core.analyzer import MetricAnalyzer
from clarea.generators.manager_view import ManagerViewGenerator
from clarea.knowledge.hooks_library import CTA_DEFINITION, HOOK_DEFINITION, INDUSTRIES

class ReportGenerator:
    """Compiles structured Markdown and Executive B2B reports for agencies and managers."""

    @staticmethod
    def to_markdown(summary: PeriodSummary, insight: DiagnosticInsight) -> str:
        analyzer = MetricAnalyzer(summary)
        eng_rate = analyzer.calculate_engagement_rate()
        conv_rate = analyzer.calculate_message_conversion_rate()
        ranked_topics = analyzer.rank_topics_by_intent()

        md = []
        md.append(f"# 📊 Reporte de Inteligencia de Decisiones: {summary.brand_name}")
        md.append(f"**Plataforma:** {summary.platform} | **Periodo Analizado:** {summary.period_label}")
        md.append("")
        md.append("---")
        md.append("")
        md.append(ManagerViewGenerator.to_markdown(ManagerViewGenerator.generate(summary, insight)))
        md.append("")
        md.append("---")
        md.append("")
        md.append("## 📈 1. Métricas Principales de Rendimiento")
        md.append("")
        md.append("| Métrica | Valor Total | Variación vs Anterior | Interpretación Rápida |")
        md.append("| :--- | :--- | :--- | :--- |")
        md.append(f"| **Alcance Total** | `{summary.total_reach:,}` | `{summary.reach_growth_pct:+.1f}%` | Volumen de usuarios únicos que vieron la marca. |")
        md.append(f"| **Interacciones** | `{summary.total_interactions:,}` | `{summary.interactions_growth_pct:+.1f}%` | Nivel de respuesta de la audiencia (`{eng_rate}%` engagement). |")
        md.append(f"| **Mensajes / Cotizaciones** | `{summary.total_messages:,}` | `{summary.messages_growth_pct:+.1f}%` | Tasa de conversión a intención comercial (`{conv_rate}%`). |")
        md.append(f"| **Publicaciones** | `{summary.posts_count}` | — | Frecuencia de contenido en el periodo. |")
        md.append("")
        md.append("---")
        md.append("")
        md.append("## 🧠 2. Diagnóstico Estratégico (Interpretado por Clarea)")
        md.append("")
        md.append(f"> **Resumen Ejecutivo:**  \n> {insight.executive_summary}")
        md.append("")
        md.append("### 🔍 Hallazgos Clave:")
        for f in insight.key_findings:
            md.append(f"- {f}")
        md.append(f"- **Cuello de Botella Principal:** {insight.primary_growth_bottleneck}")
        md.append("")
        if insight.rule_findings:
            icons = {"critico": "🔴", "alerta": "🟡", "oportunidad": "🟢"}
            md.append("### 🧩 Situaciones Detectadas:")
            for f in insight.rule_findings:
                md.append(f"- {icons.get(f.severity, '•')} **{f.title}** — {f.diagnosis}  ")
                md.append(f"  *Dato:* {f.evidence}  ")
                md.append(f"  *Qué hacer:* {f.prescription}")
            md.append("")
        md.append("---")
        md.append("")
        md.append("## 🏆 3. Ranking de Contenido por Intención Comercial")
        md.append("")
        md.append("| Categoría / Tema | Posts | Mensajes Generados | Alcance Promedio | Tasa de Conversión |")
        md.append("| :--- | :--- | :--- | :--- | :--- |")
        for t in ranked_topics:
            md.append(f"| **{t['topic']}** | {t['posts']} | **{t['total_messages']}** | {t['avg_reach']:,} | `{t['conversion_rate']}%` |")
        md.append("")
        md.append("---")
        md.append("")
        md.append("## ⚡ 4. Recomendaciones Accionables (Semana Siguiente)")
        md.append("")
        for idx, act in enumerate(insight.recommended_actions, 1):
            md.append(f"{idx}. {act}")
        md.append("")
        md.append("---")
        md.append("")
        md.append("## 🎯 5. Banco de Hooks & CTAs de Alta Conversión")
        md.append("")
        md.append(f"*Adaptados al rubro: **{INDUSTRIES[insight.industry]['nombre']}***")
        md.append("")
        md.append("### 🪝 Ganchos (Hooks) Sugeridos:")
        md.append(f"> 💡 {HOOK_DEFINITION}")
        md.append("")
        for h in insight.hook_ideas:
            md.append(f"- **{h.type_name}:** *\"{h.text}\"*  ")
            md.append(f"  ↳ Por qué funciona: {h.why_it_works}")
        md.append("")
        md.append("### 📣 Llamados a la Acción (CTAs) Sugeridos:")
        md.append(f"> 💡 {CTA_DEFINITION}")
        md.append("")
        for c in insight.cta_ideas:
            md.append(f"- **{c.type_name}:** {c.text}  ")
            md.append(f"  ↳ Por qué funciona: {c.why_it_works}")
        md.append("")
        md.append("---")
        md.append("*Generado automáticamente por [Clarea Engine](https://github.com/robjesusvilla-ops/clarea-engine) — De Métricas a Decisiones.*")

        return "\n".join(md)
