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


def load_env_file(path: Path = Path(".env")) -> None:
    """Loads KEY=value lines from .env without overriding variables already set."""
    import os
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.removeprefix("export ").partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


@app.callback()
def main():
    """Clarea: de métricas a decisiones."""
    load_env_file()


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
    ai: bool = typer.Option(False, "--ai", help="Que Claude redacte el diagnóstico y hooks a medida (necesita ANTHROPIC_API_KEY)"),
):
    """Analiza un archivo de métricas y entrega el diagnóstico de Clarea."""
    console.print(Panel(f"[bold cyan]Clarea Engine v{__version__}[/bold cyan] · Analizando [yellow]{file_path.name}[/yellow]", expand=False))
    summary = _load(file_path, brand, period, industry, new_followers)
    prev = _load(previous, brand, "Periodo anterior", industry) if previous else None
    result = run_analysis(summary, prev, use_ai=ai)
    if ai and result.ai_error:
        console.print(f"[yellow]Aviso:[/yellow] se usó el diagnóstico local. {result.ai_error}")
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
        title="🧠 Interpretado por Clarea" + (" · con Claude" if insight.ai_generated else ""), border_style="cyan",
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


client_app = typer.Typer(help="Gestiona clientes y su historial de periodos.")
app.add_typer(client_app, name="client")


@client_app.command("add")
def client_add(
    name: str = typer.Argument(..., help="Nombre de la marca"),
    industry: Optional[str] = typer.Option(None, "--industry", "-i", help="Rubro del negocio"),
    email: Optional[list[str]] = typer.Option(None, "--email", help="Correo que recibe el reporte (se puede repetir)"),
    whatsapp: Optional[str] = typer.Option(None, "--whatsapp", help="Número de WhatsApp del cliente, ej. +51999888777"),
):
    """Crea un cliente."""
    from clarea.workspace import Workspace
    try:
        c = Workspace().create_client(name, industry, email or [], whatsapp)
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)
    console.print(f"[bold green]✓[/bold green] Cliente creado: [cyan]{c.name}[/cyan] (id: {c.slug})")


@client_app.command("list")
def client_list():
    """Lista los clientes y sus periodos."""
    from clarea.workspace import Workspace
    ws = Workspace()
    clients = ws.list_clients()
    if not clients:
        console.print("Aún no hay clientes. Crea uno con: clarea client add \"Nombre\"")
        return
    table = Table(title="Clientes")
    table.add_column("Id", style="cyan")
    table.add_column("Nombre")
    table.add_column("Rubro")
    table.add_column("Periodos")
    for c in clients:
        table.add_row(c.slug, c.name, c.industry or "auto", ", ".join(p.key for p in ws.list_periods(c.slug)) or "-")
    console.print(table)


@client_app.command("import")
def client_import(
    slug: str = typer.Argument(..., help="Id del cliente (ver clarea client list)"),
    file_path: Path = typer.Argument(..., help="Archivo .csv o .json del periodo"),
    key: str = typer.Option(..., "--key", "-k", help="Mes del periodo, AAAA-MM (ej. 2026-05)"),
    label: Optional[str] = typer.Option(None, "--label", "-l", help="Nombre del periodo, ej. 'Mayo 2026'"),
    new_followers: int = typer.Option(0, "--new-followers", help="Seguidores nuevos del periodo"),
):
    """Guarda un periodo en el historial del cliente."""
    from clarea.workspace import Workspace
    ws = Workspace()
    try:
        client = ws.get_client(slug)
        summary = MetricParser.load(file_path, client.name, label or key, client.industry, new_followers)
        if label:
            summary.period_label = label
        ws.save_period(slug, key, summary)
    except (KeyError, ValueError) as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)
    console.print(f"[bold green]✓[/bold green] Periodo {key} guardado para [cyan]{client.name}[/cyan].")


@client_app.command("report")
def client_report(
    slug: str = typer.Argument(..., help="Id del cliente"),
    key: Optional[str] = typer.Option(None, "--key", "-k", help="Periodo AAAA-MM (por defecto, el último)"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Guardar el reporte en Markdown"),
    html: Optional[Path] = typer.Option(None, "--html", help="Guardar el dashboard en HTML"),
    ai: bool = typer.Option(False, "--ai", help="Diagnóstico redactado con Claude"),
):
    """Genera el reporte de un periodo, comparado contra el periodo anterior."""
    from clarea.workspace import Workspace
    ws = Workspace()
    try:
        periods = ws.list_periods(slug)
        if not periods:
            raise ValueError("Este cliente no tiene periodos. Súbelos con: clarea client import")
        key = key or periods[-1].key
        result = run_analysis(ws.get_period(slug, key), ws.previous_period(slug, key), use_ai=ai)
    except (KeyError, ValueError) as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)
    if ai and result.ai_error:
        console.print(f"[yellow]Aviso:[/yellow] se usó el diagnóstico local. {result.ai_error}")
    view = result.manager_view
    console.print(f"{STATUS_LABELS[view.status]} · {view.status_reason}\n🎯 {view.next_decision}")
    if output:
        output.write_text(ReportGenerator.to_markdown(result.summary, result.insight), encoding="utf-8")
        console.print(f"[bold green]✓[/bold green] Reporte guardado en [cyan]{output}[/cyan]")
    if html:
        html.write_text(HtmlDashboard.render(result.summary, result.insight), encoding="utf-8")
        console.print(f"[bold green]✓[/bold green] Dashboard guardado en [cyan]{html}[/cyan]")


@client_app.command("send")
def client_send(
    slug: str = typer.Argument(..., help="Id del cliente"),
    key: Optional[str] = typer.Option(None, "--key", "-k", help="Periodo AAAA-MM (por defecto, el último)"),
    to: Optional[list[str]] = typer.Option(None, "--to", help="Correo de destino (por defecto, los del cliente)"),
    ai: bool = typer.Option(False, "--ai", help="Diagnóstico redactado con Claude"),
):
    """Envía el reporte por correo y prepara el mensaje de WhatsApp."""
    from clarea.delivery import send_report, whatsapp_link, whatsapp_message
    from clarea.workspace import Workspace
    ws = Workspace()
    try:
        client = ws.get_client(slug)
        periods = ws.list_periods(slug)
        if not periods:
            raise ValueError("Este cliente no tiene periodos.")
        key = key or periods[-1].key
        result = run_analysis(ws.get_period(slug, key), ws.previous_period(slug, key), use_ai=ai)
        recipients = list(to or client.report_emails)
        if recipients:
            outcome = send_report(result, recipients, ws.outbox_dir)
            color = "green" if outcome.sent else "yellow"
            console.print(f"[{color}]{outcome.detail}[/{color}]" + (f" Archivo: {outcome.eml_path}" if outcome.eml_path else ""))
        else:
            console.print("[yellow]El cliente no tiene correos.[/yellow] Agrégalos con --to.")
    except (KeyError, ValueError) as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)
    message = whatsapp_message(result)
    console.print(Panel(message, title="Mensaje para WhatsApp", border_style="green"))
    console.print(f"Ábrelo listo para enviar: {whatsapp_link(message, client.whatsapp)}")


@app.command()
def web(
    host: str = typer.Option("127.0.0.1", help="Dirección donde escuchar"),
    port: int = typer.Option(8000, help="Puerto"),
):
    """Abre la app web de Clarea (clientes, subida de datos y dashboards)."""
    try:
        import uvicorn
        from clarea.web.app import create_app
    except ImportError:
        console.print('[red]Error:[/red] falta instalar la app web: pip install -e ".[web]"')
        raise typer.Exit(code=1)
    import os
    if host not in ("127.0.0.1", "localhost") and not os.environ.get("CLAREA_WEB_PASSWORD"):
        console.print("[yellow]Aviso:[/yellow] la app queda abierta a la red sin contraseña. "
                      "Define CLAREA_WEB_USER y CLAREA_WEB_PASSWORD.")
    console.print(f"Clarea en [cyan]http://{host}:{port}[/cyan] (Ctrl+C para salir)")
    uvicorn.run(create_app(), host=host, port=port, log_level="warning")


if __name__ == "__main__":
    app()
