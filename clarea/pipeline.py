"""Single entry point that turns a PeriodSummary into every Clarea output.

The CLI, the web app, the MCP server and the report delivery all go through
here, so the analysis is identical wherever it is shown.
"""
from dataclasses import dataclass
from typing import Optional

from clarea.core.models import DiagnosticInsight, PeriodSummary
from clarea.generators.diagnosis import DiagnosisEngine
from clarea.generators.manager_view import ManagerView, ManagerViewGenerator


@dataclass
class AnalysisResult:
    summary: PeriodSummary
    insight: DiagnosticInsight
    manager_view: ManagerView
    ai_error: Optional[str] = None


def analyze(summary: PeriodSummary, previous: Optional[PeriodSummary] = None,
            use_ai: bool = False, ai_client=None) -> AnalysisResult:
    if previous is not None:
        from clarea.core.parser import MetricParser
        MetricParser.apply_previous_period(summary, previous)
    insight = DiagnosisEngine.generate_local_insight(summary)
    ai_error = None
    if use_ai:
        from clarea.ai.claude_diagnosis import enrich_insight
        insight, ai_error = enrich_insight(summary, insight, ai_client)
    return AnalysisResult(summary, insight, ManagerViewGenerator.generate(summary, insight), ai_error)
