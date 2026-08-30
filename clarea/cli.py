import typer
import json
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown

from clarea.core.parser import MetricParser
from clarea.core.analyzer import MetricAnalyzer
from clarea.generators.diagnosis import DiagnosisEngine
from clarea.generators.report import ReportGenerator

app = typer.Typer(help="Clarea Engine CLI - Transform raw marketing metrics into strategic business decisions.")
console = Console()

@app.command()
def analyze(
    file_path: Path = typer.Argument(..., help="Path to JSON or CSV metrics file"),
    brand: str = typer.Option("Brand", help="Brand name (required if using CSV)"),
    period: str = typer.Option("Current Period", help="Period label (required if using CSV)"),
    output: Path = typer.Option(None, "--output", "-o", help="Path to save the Markdown report")
):
    """Analyze a marketing dataset and produce an executive decision diagnosis."""
    if not file_path.exists():
        console.print(f"[red]Error:[/red] File '{file_path}' does not exist.")
        raise typer.Exit(code=1)

    console.print(Panel(f"[bold cyan]Clarea Engine v0.1.0[/bold cyan] - Processing [yellow]{file_path.name}[/yellow]", expand=False))

    if file_path.suffix.lower() == ".json":
        summary = MetricParser.from_json_file(file_path)
    elif file_path.suffix.lower() == ".csv":
        summary = MetricParser.from_csv_file(file_path, brand_name=brand, period_label=period)
    else:
        console.print(f"[red]Unsupported format:[/red] {file_path.suffix}. Please provide .json or .csv")
        raise typer.Exit(code=1)

    analyzer = MetricAnalyzer(summary)
    insight = DiagnosisEngine.generate_local_insight(summary)

    # 1. Metric Overview Table
    table = Table(title=f"📊 Performance Overview: {summary.brand_name} ({summary.platform})")
    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Value", style="magenta")
    table.add_column("Growth vs Prev", style="green")

    table.add_row("Total Reach", f"{summary.total_reach:,}", f"{summary.reach_growth_pct:+.1f}%")
    table.add_row("Interactions", f"{summary.total_interactions:,}", f"{summary.interactions_growth_pct:+.1f}%")
    table.add_row("Inquiries (Messages)", f"{summary.total_messages:,}", f"{summary.messages_growth_pct:+.1f}%")
    table.add_row("Engagement Rate", f"{analyzer.calculate_engagement_rate()}%", "-")
    table.add_row("Vanity Ratio", f"{analyzer.calculate_vanity_vs_business_ratio()}", "Lower is better")

    console.print(table)

    # 2. Executive Diagnosis Panel
    console.print(Panel(
        f"[bold green]Diagnóstico Inteligente (Interpretado por Clarea):[/bold green]\n\n{insight.executive_summary}\n\n"
        f"[bold yellow]Cuello de Botella Principal:[/bold yellow] {insight.primary_growth_bottleneck}",
        title="🧠 Strategic Insights",
        border_style="cyan"
    ))

    # 3. Save or Print Report
    report_md = ReportGenerator.to_markdown(summary, insight)
    if output:
        with open(output, "w", encoding="utf-8") as f:
            f.write(report_md)
        console.print(f"[bold green]✓[/bold green] Executive report saved to [cyan]{output}[/cyan]")
    else:
        console.print(Markdown(report_md))

if __name__ == "__main__":
    app()
