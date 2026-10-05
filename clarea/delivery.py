"""Report delivery: email (SMTP) and a WhatsApp-ready message.

Email settings come from environment variables, never from code:
  CLAREA_SMTP_HOST, CLAREA_SMTP_PORT (587), CLAREA_SMTP_USER,
  CLAREA_SMTP_PASSWORD, CLAREA_SMTP_FROM (defaults to the user)
With Gmail use an "app password", not your normal password.
Without CLAREA_SMTP_HOST the email is saved as a .eml file in the outbox
folder instead of being sent, so nothing leaves the computer by accident.

WhatsApp: the message is short plain text plus a wa.me link that opens
WhatsApp with the text already written; the person taps send. Fully
automatic sending needs the WhatsApp Business Cloud API (not included).
"""
import os
import re
import smtplib
import urllib.parse
from dataclasses import dataclass
from datetime import datetime
from email.message import EmailMessage
from html import escape as e
from pathlib import Path
from typing import List, Optional

from clarea.generators.html_dashboard import HtmlDashboard
from clarea.generators.report import ReportGenerator
from clarea.pipeline import AnalysisResult

STATUS_TEXT = {"saludable": "🟢 Saludable", "alerta": "🟡 Alerta", "critico": "🔴 Crítico"}
STATUS_COLOR = {"saludable": "#10B981", "alerta": "#F59E0B", "critico": "#EF4444"}
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@dataclass
class DeliveryResult:
    sent: bool
    detail: str
    eml_path: Optional[Path] = None


def whatsapp_message(result: AnalysisResult) -> str:
    s, v = result.summary, result.manager_view
    actions = "\n".join(f"{i}. {a}" for i, a in enumerate(result.insight.recommended_actions[:3], 1))
    return (
        f"*Clarea · {s.brand_name} · {s.period_label}*\n"
        f"Estado: {STATUS_TEXT[v.status]}\n\n"
        f"🏆 {v.main_achievement}\n"
        f"🚧 {v.bottleneck}\n"
        f"🎯 *Próxima decisión:* {v.next_decision}\n\n"
        f"Alcance {s.total_reach:,} ({s.reach_growth_pct:+.1f}%) · "
        f"Mensajes {s.total_messages:,} ({s.messages_growth_pct:+.1f}%)\n\n"
        f"*Esta semana:*\n{actions}"
    )


def whatsapp_link(message: str, phone: Optional[str] = None) -> str:
    number = re.sub(r"\D", "", phone or "")
    return f"https://wa.me/{number}?text={urllib.parse.quote(message)}"


def _email_html(result: AnalysisResult) -> str:
    s, v, insight = result.summary, result.manager_view, result.insight
    color = STATUS_COLOR[v.status]
    actions = "".join(f"<li style='margin:0 0 8px'>{e(a)}</li>" for a in insight.recommended_actions)
    kpis = "".join(
        f"<td style='padding:12px;border:1px solid #e5e5ef'><div style='font-size:12px;color:#666'>{label}</div>"
        f"<div style='font-size:22px;font-weight:700'>{value}</div><div style='font-size:12px;color:#666'>{delta}</div></td>"
        for label, value, delta in (
            ("Alcance", f"{s.total_reach:,}", f"{s.reach_growth_pct:+.1f}%"),
            ("Interacciones", f"{s.total_interactions:,}", f"{s.interactions_growth_pct:+.1f}%"),
            ("Mensajes de venta", f"{s.total_messages:,}", f"{s.messages_growth_pct:+.1f}%"),
        )
    )
    return f"""<!doctype html><html><body style="margin:0;background:#f4f4f8;font-family:Arial,Helvetica,sans-serif;color:#1a1a22">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr><td align="center" style="padding:24px 12px">
<table role="presentation" width="600" cellpadding="0" cellspacing="0" style="max-width:600px;background:#ffffff;border-radius:12px">
<tr><td style="padding:24px 24px 8px"><div style="font-size:12px;letter-spacing:2px;color:#6366F1;font-weight:700">CLAREA</div>
<h1 style="margin:8px 0 4px;font-size:22px">{e(s.brand_name)} · {e(s.period_label)}</h1>
<div style="display:inline-block;margin-top:8px;padding:6px 12px;border-radius:999px;border:1px solid {color};color:{color};font-weight:700">{STATUS_TEXT[v.status]}</div>
<p style="margin:12px 0 0">{e(v.status_reason)}</p></td></tr>
<tr><td style="padding:16px 24px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse"><tr>{kpis}</tr></table></td></tr>
<tr><td style="padding:0 24px 8px">
<p><strong>🏆 Logro principal:</strong> {e(v.main_achievement)}</p>
<p><strong>🚧 Cuello de botella:</strong> {e(v.bottleneck)}</p>
<p><strong>🎯 Próxima decisión:</strong> {e(v.next_decision)}</p></td></tr>
<tr><td style="padding:0 24px 8px"><h2 style="font-size:16px">Qué hacer la próxima semana</h2><ol style="padding-left:20px">{actions}</ol></td></tr>
<tr><td style="padding:8px 24px 24px;font-size:13px;color:#666">El dashboard completo y el reporte van adjuntos. Abre <strong>dashboard.html</strong> en tu navegador.</td></tr>
</table></td></tr></table></body></html>"""


def build_email(result: AnalysisResult, recipients: List[str], sender: str) -> EmailMessage:
    bad = [r for r in recipients if not EMAIL_RE.match(r)]
    if not recipients or bad:
        raise ValueError("Correo de destino inválido: " + (", ".join(bad) or "no hay destinatarios"))
    s, v = result.summary, result.manager_view
    msg = EmailMessage()
    msg["Subject"] = f"Clarea · {s.brand_name} · {s.period_label}: {STATUS_TEXT[v.status]}"
    msg["From"] = sender
    msg["To"] = ", ".join(recipients)
    msg.set_content(whatsapp_message(result).replace("*", "") +
                    "\n\nEl dashboard completo y el reporte van adjuntos.")
    msg.add_alternative(_email_html(result), subtype="html")
    base = re.sub(r"[^a-z0-9]+", "-", f"{s.brand_name}-{s.period_label}".lower()).strip("-")
    msg.add_attachment(HtmlDashboard.render(s, result.insight).encode("utf-8"), maintype="text",
                       subtype="html", filename=f"dashboard-{base}.html")
    msg.add_attachment(ReportGenerator.to_markdown(s, result.insight).encode("utf-8"), maintype="text",
                       subtype="markdown", filename=f"reporte-{base}.md")
    return msg


def send_report(result: AnalysisResult, recipients: List[str], outbox: Path) -> DeliveryResult:
    host = os.environ.get("CLAREA_SMTP_HOST")
    user = os.environ.get("CLAREA_SMTP_USER", "")
    sender = os.environ.get("CLAREA_SMTP_FROM") or user or "clarea@localhost"
    msg = build_email(result, recipients, sender)
    if not host:
        outbox.mkdir(parents=True, exist_ok=True)
        path = outbox / f"{datetime.now():%Y%m%d-%H%M%S}-{re.sub(r'[^a-z0-9]+', '-', result.summary.brand_name.lower())}.eml"
        path.write_bytes(bytes(msg))
        return DeliveryResult(False, "No hay SMTP configurado: el correo se guardó para revisarlo, no se envió.", path)
    port = int(os.environ.get("CLAREA_SMTP_PORT", "587"))
    try:
        if port == 465:
            server = smtplib.SMTP_SSL(host, port, timeout=30)
        else:
            server = smtplib.SMTP(host, port, timeout=30)
            server.starttls()
        with server:
            if user:
                server.login(user, os.environ.get("CLAREA_SMTP_PASSWORD", ""))
            server.send_message(msg)
    except (smtplib.SMTPException, OSError) as exc:
        return DeliveryResult(False, f"No se pudo enviar el correo: {exc}")
    return DeliveryResult(True, f"Reporte enviado a {', '.join(recipients)}.")
