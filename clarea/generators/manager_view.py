from typing import List, Optional
from pydantic import BaseModel

from clarea.core.models import PeriodSummary, DiagnosticInsight, RuleFinding

STATUS_LABELS = {"saludable": "🟢 Saludable", "alerta": "🟡 Alerta", "critico": "🔴 Crítico"}

# A drop in inquiries this large is critical even if no rule fired.
CRITICAL_MESSAGES_DROP_PCT = -20.0


class ManagerView(BaseModel):
    """One-page executive view: traffic light + achievement + bottleneck + next decision."""
    brand_name: str
    period_label: str
    status: str  # saludable, alerta, critico
    status_reason: str
    main_achievement: str
    bottleneck: str
    next_decision: str
    key_numbers: List[str]


class ManagerViewGenerator:

    @staticmethod
    def _status(summary: PeriodSummary, findings: List[RuleFinding]) -> tuple:
        severities = {f.severity for f in findings}
        if "critico" in severities:
            f = next(f for f in findings if f.severity == "critico")
            return "critico", f.title
        if summary.messages_growth_pct <= CRITICAL_MESSAGES_DROP_PCT:
            return "critico", f"Los mensajes de venta cayeron {summary.messages_growth_pct:+.1f}%."
        if "alerta" in severities:
            f = next(f for f in findings if f.severity == "alerta")
            return "alerta", f.title
        if summary.messages_growth_pct < 0:
            return "alerta", f"Los mensajes de venta bajaron {summary.messages_growth_pct:+.1f}%."
        return "saludable", "La cuenta genera mensajes de venta de forma sostenida."

    @staticmethod
    def _achievement(summary: PeriodSummary, findings: List[RuleFinding]) -> str:
        opportunity: Optional[RuleFinding] = next((f for f in findings if f.severity == "oportunidad"), None)
        if summary.messages_growth_pct > 0:
            return f"Los mensajes de venta crecieron {summary.messages_growth_pct:+.1f}% ({summary.total_messages} en el periodo)."
        if opportunity:
            return f"{opportunity.title}: {opportunity.evidence}"
        if summary.reach_growth_pct > 0:
            return f"El alcance creció {summary.reach_growth_pct:+.1f}% ({summary.total_reach:,} personas)."
        return "Sin logros destacados en este periodo."

    @staticmethod
    def generate(summary: PeriodSummary, insight: DiagnosticInsight) -> ManagerView:
        findings = insight.rule_findings
        status, reason = ManagerViewGenerator._status(summary, findings)
        problem = next((f for f in findings if f.severity in ("critico", "alerta")), None)
        top = findings[0] if findings else None

        return ManagerView(
            brand_name=summary.brand_name,
            period_label=summary.period_label,
            status=status,
            status_reason=reason,
            main_achievement=ManagerViewGenerator._achievement(summary, findings),
            bottleneck=f"{problem.title}. {problem.diagnosis}" if problem else insight.primary_growth_bottleneck,
            next_decision=top.prescription if top else insight.recommended_actions[0],
            key_numbers=[
                f"Alcance: {summary.total_reach:,} ({summary.reach_growth_pct:+.1f}%)",
                f"Mensajes de venta: {summary.total_messages:,} ({summary.messages_growth_pct:+.1f}%)",
                f"Seguidores nuevos: {summary.new_followers:,}",
            ],
        )

    @staticmethod
    def to_markdown(view: ManagerView) -> str:
        md = [
            f"## 🚦 Vista Gerente — {view.brand_name} ({view.period_label})",
            "",
            f"**Estado: {STATUS_LABELS[view.status]}** — {view.status_reason}",
            "",
            "| | |",
            "| :--- | :--- |",
            f"| 🏆 **Logro principal** | {view.main_achievement} |",
            f"| 🚧 **Cuello de botella** | {view.bottleneck} |",
            f"| 🎯 **Próxima decisión** | {view.next_decision} |",
            "",
            " · ".join(view.key_numbers),
        ]
        return "\n".join(md)
