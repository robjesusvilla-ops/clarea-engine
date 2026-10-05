"""Clarea web app: clients, monthly uploads and dashboards.

Run with:  clarea web            (needs: pip install -e ".[web]")
Protect it with CLAREA_WEB_USER and CLAREA_WEB_PASSWORD before exposing it
outside your computer: client metrics are business data.
"""
import base64
import json
import os
import urllib.parse
import secrets
from html import escape as e
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse, Response

from clarea import __version__
from clarea.core.parser import MetricParser
from clarea.delivery import whatsapp_link, whatsapp_message
from clarea.generators.html_dashboard import CSS, FONTS, STATUS, HtmlDashboard
from clarea.generators.report import ReportGenerator
from clarea.knowledge.hooks_library import INDUSTRIES
from clarea.pipeline import analyze
from clarea.workspace import Workspace

EXAMPLES = Path(__file__).resolve().parent.parent.parent / "examples"
TEMPLATE_HEADERS = "id,fecha,tipo,tema,alcance,impresiones,reacciones,comentarios,compartidos,guardados,clics,mensajes,texto\n"
MAX_UPLOAD_BYTES = 5 * 1024 * 1024

WEB_CSS = """
.nav{display:flex;gap:14px;align-items:center;flex-wrap:wrap;font-size:.9rem}
.nav a{color:var(--muted);text-decoration:none}
.nav a:hover{color:var(--text)}
a{color:var(--accent)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:12px}
.client{display:grid;gap:10px;text-decoration:none;color:var(--text)}
.client:hover{border-color:var(--accent)}
.status{display:inline-flex;align-items:center;gap:8px;font-size:.85rem;font-weight:600;color:var(--status)}
.status i{width:9px;height:9px;border-radius:50%;background:var(--status)}
form.stack{display:grid;gap:12px}
.fields{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px}
label.field{display:grid;gap:6px;font-size:.85rem;color:var(--muted)}
input,select{background:var(--surface-2);color:var(--text);border:1px solid var(--line);border-radius:10px;
  padding:10px 12px;font:inherit;width:100%}
input:focus-visible,select:focus-visible,button:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.btn{background:var(--accent);color:#0A0A0C;border:0;border-radius:999px;padding:10px 18px;font:inherit;
  font-weight:600;cursor:pointer;justify-self:start}
.btn.ghost{background:none;color:var(--muted);border:1px solid var(--line)}
.row-actions{display:flex;gap:10px;flex-wrap:wrap;align-items:center}
.notice{padding:12px 16px;border-radius:12px;background:var(--surface-2);border-left:3px solid var(--status)}
"""


def _q(text) -> str:
    return urllib.parse.quote(str(text))


def _check_auth(request: Request) -> None:
    user, password = os.environ.get("CLAREA_WEB_USER"), os.environ.get("CLAREA_WEB_PASSWORD")
    if not (user and password):
        return
    header = request.headers.get("authorization", "")
    if header.startswith("Basic "):
        try:
            given_user, _, given_pw = base64.b64decode(header[6:]).decode().partition(":")
        except Exception:
            given_user = given_pw = ""
        if secrets.compare_digest(given_user, user) and secrets.compare_digest(given_pw, password):
            return
    raise HTTPException(401, "Acceso restringido", headers={"WWW-Authenticate": 'Basic realm="Clarea"'})


def _page(title: str, body: str) -> HTMLResponse:
    return HTMLResponse(
        '<!doctype html><html lang="es"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f"<title>{e(title)}</title>{FONTS}<style>{CSS}{WEB_CSS}</style></head>"
        f'<body><div class="wrap">{body}</div></body></html>'
    )


def _header(crumbs: str = "") -> str:
    return (
        '<header><a class="brand" href="/" style="text-decoration:none;color:inherit"><div class="mark">C</div>'
        '<div><b>CLAREA</b><div class="tag">De métricas a decisiones</div></div></a>'
        f'<nav class="nav">{crumbs}<span class="tag chip">[ v{__version__} ]</span></nav></header>'
    )


def _status_pill(status: str) -> str:
    label, cls = STATUS[status]
    return f'<span class="status s-{cls}"><i></i>{label}</span>'


def _industry_options(selected: Optional[str] = None) -> str:
    opts = ['<option value="">Detectar automáticamente</option>']
    opts += [f'<option value="{k}"{" selected" if k == selected else ""}>{e(v["nombre"])}</option>'
             for k, v in INDUSTRIES.items()]
    return "".join(opts)


def create_app(workspace: Optional[Workspace] = None) -> FastAPI:
    ws = workspace or Workspace()
    app = FastAPI(title="Clarea", docs_url=None, redoc_url=None)

    @app.middleware("http")
    async def auth(request: Request, call_next):
        try:
            _check_auth(request)
        except HTTPException as exc:
            return PlainTextResponse(exc.detail, status_code=exc.status_code, headers=exc.headers)
        return await call_next(request)

    def run(slug: str, key: str):
        summary = ws.get_period(slug, key)
        return analyze(summary, ws.previous_period(slug, key))

    @app.get("/", response_class=HTMLResponse)
    def index(error: str = ""):
        cards = []
        for c in ws.list_clients():
            periods = ws.list_periods(c.slug)
            if periods:
                last = periods[-1]
                status = _status_pill(run(c.slug, last.key).manager_view.status)
                detail = f'<span class="muted">Último periodo: {e(last.label)}</span>{status}'
            else:
                detail = '<span class="muted">Sin datos todavía</span>'
            rubro = INDUSTRIES.get(c.industry or "", {}).get("nombre", "Rubro automático")
            cards.append(f'<a class="card client" href="/clients/{c.slug}"><h2>{e(c.name)}</h2>'
                         f'<span class="tag">{e(rubro)}</span>{detail}</a>')
        clients_html = "".join(cards) or '<p class="empty">Aún no tienes clientes. Crea el primero abajo.</p>'
        notice = f'<p class="notice s-crit">{e(error)}</p>' if error else ""
        return _page("Clarea · Clientes", f"""
{_header()}
<section><div class="section-head"><h2>Clientes</h2><span class="tag">{len(cards)} en total</span></div>
<div class="grid">{clients_html}</div></section>
<section class="card"><h2>Nuevo cliente</h2>{notice}
<form class="stack" method="post" action="/clients">
  <div class="fields">
    <label class="field" for="name">Nombre de la marca<input id="name" name="name" required placeholder="Ej. Qhatai Piscinas"></label>
    <label class="field" for="industry">Rubro<select id="industry" name="industry">{_industry_options()}</select></label>
    <label class="field" for="emails">Correos para el reporte (separados por coma)<input id="emails" name="emails" placeholder="dueño@empresa.com"></label>
  </div>
  <button class="btn" type="submit">Crear cliente</button>
</form></section>""")

    @app.post("/clients")
    def create_client(name: str = Form(...), industry: str = Form(""), emails: str = Form("")):
        try:
            client = ws.create_client(name, industry or None, [m.strip() for m in emails.split(",") if m.strip()])
        except ValueError as exc:
            return RedirectResponse(f"/?error={_q(exc)}", status_code=303)
        return RedirectResponse(f"/clients/{client.slug}", status_code=303)

    @app.get("/clients/{slug}", response_class=HTMLResponse)
    def client_page(slug: str, error: str = "", msg: str = ""):
        try:
            client = ws.get_client(slug)
        except (KeyError, ValueError):
            raise HTTPException(404, "Cliente no encontrado")
        rows = []
        periods = ws.list_periods(slug)
        for idx, p in reversed(list(enumerate(periods))):
            r = run(slug, p.key)
            s = r.summary
            growth = f"{s.messages_growth_pct:+.1f}%" if idx > 0 else "—"
            rows.append(
                f'<tr><td><a href="/clients/{slug}/periods/{p.key}"><strong>{e(p.label)}</strong></a>'
                f'<div class="caption">{e(p.key)}</div></td><td>{_status_pill(r.manager_view.status)}</td>'
                f'<td class="r num">{s.total_reach:,}</td><td class="r num">{s.total_messages:,}</td>'
                f'<td class="r num">{growth}</td></tr>'
            )
        table = ("<div class=\"table-wrap\"><table><thead><tr><th>Periodo</th><th>Estado</th><th class=\"r\">Alcance</th>"
                 "<th class=\"r\">Mensajes</th><th class=\"r\">vs anterior</th></tr></thead><tbody>"
                 + "".join(rows) + "</tbody></table></div>") if rows else '<p class="empty">Sube el primer periodo para ver su diagnóstico.</p>'
        notice = (f'<p class="notice s-crit">{e(error)}</p>' if error else "") + \
                 (f'<p class="notice s-ok">{e(msg)}</p>' if msg else "")
        rubro = INDUSTRIES.get(client.industry or "", {}).get("nombre", "Rubro automático")
        return _page(f"Clarea · {client.name}", f"""
{_header('<a href="/">Clientes</a>')}
<section><div class="section-head"><h1 style="font-size:2rem">{e(client.name)}</h1><span class="tag">{e(rubro)}</span></div>
{notice}
<div class="card">{table}</div></section>
<section class="card"><h2>Subir un periodo</h2>
<p class="muted">Sube el CSV que exportas de Meta Business Suite o la <a href="/plantilla.csv">plantilla de Clarea</a>. También acepta el JSON de <code>clarea fetch</code>.</p>
<form class="stack" method="post" action="/clients/{slug}/periods" enctype="multipart/form-data">
  <div class="fields">
    <label class="field" for="file">Archivo (.csv o .json)<input id="file" type="file" name="file" accept=".csv,.json" required></label>
    <label class="field" for="key">Mes<input id="key" type="month" name="key" required></label>
    <label class="field" for="label">Nombre del periodo<input id="label" name="label" placeholder="Mayo 2026"></label>
    <label class="field" for="followers">Seguidores nuevos<input id="followers" type="number" min="0" name="new_followers" value="0"></label>
  </div>
  <button class="btn" type="submit">Analizar</button>
</form></section>""")

    @app.post("/clients/{slug}/periods")
    async def upload_period(slug: str, file: UploadFile = File(...), key: str = Form(...),
                            label: str = Form(""), new_followers: int = Form(0)):
        try:
            client = ws.get_client(slug)
        except (KeyError, ValueError):
            raise HTTPException(404, "Cliente no encontrado")
        raw = await file.read(MAX_UPLOAD_BYTES + 1)
        try:
            if len(raw) > MAX_UPLOAD_BYTES:
                raise ValueError("El archivo supera los 5 MB.")
            text = raw.decode("utf-8-sig")
            name = (file.filename or "").lower()
            if name.endswith(".json"):
                summary = MetricParser.from_dict(json.loads(text))
                if label:
                    summary.period_label = label
            elif name.endswith(".csv"):
                posts = MetricParser.posts_from_csv_text(text)
                summary = MetricParser.summary_from_posts(posts, client.name, label or key, client.industry, new_followers)
            else:
                raise ValueError("Sube un archivo .csv o .json.")
            if new_followers and name.endswith(".json"):
                summary.new_followers = new_followers
            ws.save_period(slug, key, summary)
        except UnicodeDecodeError:
            return RedirectResponse(f"/clients/{slug}?error={_q('El archivo debe estar en UTF-8.')}", status_code=303)
        except Exception as exc:
            return RedirectResponse(f"/clients/{slug}?error={_q(str(exc)[:300])}", status_code=303)
        return RedirectResponse(f"/clients/{slug}/periods/{key}", status_code=303)

    @app.get("/clients/{slug}/periods/{key}", response_class=HTMLResponse)
    def period_page(slug: str, key: str):
        try:
            client = ws.get_client(slug)
            r = run(slug, key)
        except (KeyError, ValueError):
            raise HTTPException(404, "Periodo no encontrado")
        nav = (f'<nav class="nav"><a href="/">Clientes</a><span class="muted">/</span>'
               f'<a href="/clients/{slug}">{e(client.name)}</a><span class="muted">/</span>'
               f'<a href="/clients/{slug}/periods/{key}/reporte.md">Descargar reporte</a>'
               f'<a href="{e(whatsapp_link(whatsapp_message(r), client.whatsapp))}" target="_blank" rel="noopener">Compartir por WhatsApp</a>'
               f'<form method="post" action="/clients/{slug}/periods/{key}/send" style="margin:0">'
               f'<button class="copy" type="submit">Enviar por correo</button></form></nav>')
        html = HtmlDashboard.render(r.summary, r.insight, nav_html=nav)
        return HTMLResponse(html.replace("</style>", WEB_CSS + "</style>", 1))

    @app.get("/clients/{slug}/periods/{key}/reporte.md")
    def period_markdown(slug: str, key: str):
        try:
            r = run(slug, key)
        except (KeyError, ValueError):
            raise HTTPException(404, "Periodo no encontrado")
        return Response(ReportGenerator.to_markdown(r.summary, r.insight), media_type="text/markdown; charset=utf-8",
                        headers={"Content-Disposition": f'attachment; filename="clarea-{slug}-{key}.md"'})

    @app.post("/clients/{slug}/periods/{key}/send")
    def send_period(slug: str, key: str):
        from clarea.delivery import send_report
        try:
            client = ws.get_client(slug)
            r = run(slug, key)
            if not client.report_emails:
                raise ValueError("Este cliente no tiene correos para el reporte.")
            outcome = send_report(r, client.report_emails, ws.outbox_dir)
        except (KeyError, ValueError) as exc:
            return RedirectResponse(f"/clients/{slug}?error={_q(exc)}", status_code=303)
        param = "msg" if outcome.sent or outcome.eml_path else "error"
        return RedirectResponse(f"/clients/{slug}?{param}={_q(outcome.detail)}", status_code=303)

    @app.get("/plantilla.csv")
    def template_csv():
        sample = EXAMPLES / "plantilla_metricas_mayo.csv"
        body = sample.read_text(encoding="utf-8") if sample.exists() else TEMPLATE_HEADERS
        return Response(body, media_type="text/csv; charset=utf-8",
                        headers={"Content-Disposition": 'attachment; filename="plantilla_clarea.csv"'})

    return app
