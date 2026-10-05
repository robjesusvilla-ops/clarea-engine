import sys
from pathlib import Path
from typing import Optional

import typer

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from clarea import __version__
from clarea.core.analyzer import MetricAnalyzer
from clarea.core.parser import MetricParser
from clarea.generators.html_dashboard import HtmlDashboard
from clarea.generators.manager_view import STATUS_LABELS
from clarea.generators.report import ReportGenerator
from clarea.pipeline import analyze as run_analysis

app = typer.Typer(help="Clarea: de métricas a decisiones. Convierte métricas de redes en diagnósticos y acciones.")
console = Console()


@app.callback()
def main():
    """Clarea: de métricas a decisiones."""


def _load(path: Path, brand: str, period: str, industry: Optional[str], new_followers: int = 0):
    if not path.exists():
        console.print(f"[red]Error:[/red] no existe el archivo '{path}'.")
        raise typer.Exit(code=1)
    try:
        return MetricParser.load(path, brand, period, industry, new_followers)
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)


@app.command()
def analyze(
    file_path: Path = typer.Argument(..., help="Archivo de métricas .json o .csv"),
    brand: str = typer.Option("Mi marca", "--brand", "-b", help="Nombre de la marca (para CSV)"),
    period: str = typer.Option("Periodo actual", "--period", "-p", help="Nombre del periodo (para CSV), ej. 'Mayo 2026'"),
    previous: Optional[Path] = typer.Option(None, "--previous", help="Archivo del periodo anterior, para calcular el crecimiento"),
    new_followers: int = typer.Option(0, "--new-followers", help="Seguidores nuevos del periodo (para CSV)"),
    industry: Optional[str] = typer.Option(None, "--industry", "-i", help="Rubro: piscinas, restaurante, belleza, inmobiliaria, retail, servicios, general (se detecta si no se indica)"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Guardar el reporte en Markdown"),
    html: Optional[Path] = typer.Option(None, "--html", help="Guardar el dashboard interactivo en HTML"),
):
    """Analiza un archivo de métricas y entrega el diagnóstico de Clarea."""
    console.print(Panel(f"[bold cyan]Clarea Engine v{__version__}[/bold cyan] · Analizando [yellow]{file_path.name}[/yellow]", expand=False))
    summary = _load(file_path, brand, period, industry, new_followers)
    prev = _load(previous, brand, "Periodo anterior", industry) if previous else None
    result = run_analysis(summary, prev)
    summary, insight, view = result.summary, result.insight, result.manager_view
    analyzer = MetricAnalyzer(summary)

    border = {"saludable": "green", "alerta": "yellow", "critico": "red"}[view.status]
    console.print(Panel(
        f"[bold]Estado: {STATUS_LABELS[view.status]}[/bold] — {view.status_reason}\n\n"
        f"[bold]🏆 Logro principal:[/bold] {view.main_achievement}\n"
        f"[bold]🚧 Cuello de botella:[/bold] {view.bottleneck}\n"
        f"[bold]🎯 Próxima decisión:[/bold] {view.next_decision}",
        title="🚦 Vista Gerente", border_style=border,
    ))

    table = Table(title=f"📊 {summary.brand_name} · {summary.platform} · {summary.period_label}")
    table.add_column("Métrica", style="cyan", no_wrap=True)
    table.add_column("Valor", style="magenta")
    table.add_column("vs anterior", style="green")
    table.add_row("Alcance", f"{summary.total_reach:,}", f"{summary.reach_growth_pct:+.1f}%")
    table.add_row("Interacciones", f"{summary.total_interactions:,}", f"{summary.interactions_growth_pct:+.1f}%")
    table.add_row("Mensajes de venta", f"{summary.total_messages:,}", f"{summary.messages_growth_pct:+.1f}%")
    table.add_row("Engagement", f"{analyzer.calculate_engagement_rate()}%", "-")
    table.add_row("Ratio vanidad/negocio", f"{analyzer.calculate_vanity_vs_business_ratio()}", "menor es mejor")
    console.print(table)

    console.print(Panel(
        f"{insight.executive_summary}\n\n[bold yellow]Cuello de botella:[/bold yellow] {insight.primary_growth_bottleneck}",
        title="🧠 Interpretado por Clarea", border_style="cyan",
    ))

    report_md = ReportGenerator.to_markdown(summary, insight)
    if html:
        html.write_text(HtmlDashboard.render(summary, insight), encoding="utf-8")
        console.print(f"[bold green]✓[/bold green] Dashboard HTML guardado en [cyan]{html}[/cyan]")
    if output:
        output.write_text(report_md, encoding="utf-8")
        console.print(f"[bold green]✓[/bold green] Reporte guardado en [cyan]{output}[/cyan]")
    if not html and not output:
        console.print(Markdown(report_md))


@app.command()
def fetch(
    since: str = typer.Option(..., help="Fecha inicial, AAAA-MM-DD"),
    until: str = typer.Option(..., help="Fecha final, AAAA-MM-DD"),
    period: str = typer.Option(..., "--period", "-p", help="Nombre del periodo, ej. 'Mayo 2026'"),
    output: Path = typer.Option(..., "--output", "-o", help="Archivo .json donde guardar las métricas"),
    page_id: Optional[str] = typer.Option(None, "--page-id", help="ID de la página (o variable META_PAGE_ID)"),
    brand: Optional[str] = typer.Option(None, "--brand", "-b", help="Nombre de la marca (por defecto, el de la página)"),
    industry: Optional[str] = typer.Option(None, "--industry", "-i", help="Rubro del negocio"),
):
    """Descarga las métricas de una página de Facebook con la API de Meta (solo lectura).

    Necesita el token de página en la variable de entorno META_PAGE_TOKEN.
    """
    from clarea.connectors.meta_graph import MetaGraphClient, MetaGraphError
    try:
        summary = MetaGraphClient().fetch_period(page_id, since, until, period, brand, industry)
    except MetaGraphError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)
    output.write_text(summary.model_dump_json(indent=2), encoding="utf-8")
    console.print(f"[bold green]✓[/bold green] {summary.posts_count} publicaciones de [cyan]{summary.brand_name}[/cyan] "
                  f"guardadas en [cyan]{output}[/cyan]. Analízalas con: clarea analyze {output}")


if __name__ == "__main__":
    app()
