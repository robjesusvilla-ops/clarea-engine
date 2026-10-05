"""Self-contained HTML dashboard ("Tech Premium & SaaS" design system from the brief)."""
import json
from html import escape

from clarea.core.analyzer import MetricAnalyzer
from clarea.core.models import DiagnosticInsight, PeriodSummary
from clarea.generators.manager_view import ManagerViewGenerator
from clarea.knowledge.hooks_library import (
    CTA_DEFINITION, CTA_TYPES, HOOK_DEFINITION, HOOK_TYPES, INDUSTRIES,
)

STATUS = {
    "saludable": ("Saludable", "ok"),
    "alerta": ("Alerta", "warn"),
    "critico": ("Crítico", "crit"),
}
SEVERITY = {
    "critico": ("Crítico", "crit"),
    "alerta": ("Alerta", "warn"),
    "oportunidad": ("Oportunidad", "ok"),
}
FORMAT_LABELS = {"photo": "Foto", "video": "Video", "reel": "Reel", "carousel": "Carrusel", "text": "Texto"}

CSS = """
:root{
  color-scheme:dark;
  --bg:#0A0A0C; --surface:rgba(255,255,255,.03); --surface-2:rgba(255,255,255,.055);
  --line:rgba(255,255,255,.08); --text:#EDEDF3; --muted:#8E8EA0; --faint:#5E5E70;
  --accent:#818CF8; --glow:rgba(99,102,241,.15);
  --ok:#10B981; --warn:#F59E0B; --crit:#EF4444;
  --display:"Bricolage Grotesque", "Inter", system-ui, sans-serif;
  --body:"Inter", system-ui, -apple-system, "Segoe UI", sans-serif;
}
*{box-sizing:border-box}
body{background:var(--bg);color:var(--text);font:15px/1.55 var(--body);margin:0;
  background-image:radial-gradient(60rem 30rem at 85% -10%, var(--glow), transparent 70%);}
.wrap{max-width:1120px;margin:0 auto;padding-inline:20px;padding-block:28px 64px;display:grid;gap:28px}
h1,h2,h3{font-family:var(--display);font-weight:600;letter-spacing:-.02em;margin:0;text-wrap:balance}
h2{font-size:1.35rem}
p{margin:0}
.tag{font-size:.7rem;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);font-weight:500}
.muted{color:var(--muted)}
.num{font-variant-numeric:tabular-nums}
.card{background:var(--surface);border:1px solid var(--line);border-radius:18px;padding:22px;
  backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px)}
section{display:grid;gap:14px}
.section-head{display:flex;justify-content:space-between;align-items:baseline;gap:12px;flex-wrap:wrap}

/* header */
header{display:flex;justify-content:space-between;align-items:center;gap:16px;flex-wrap:wrap}
.brand{display:flex;align-items:center;gap:12px}
.mark{width:34px;height:34px;border-radius:10px;display:grid;place-items:center;
  background:linear-gradient(135deg,#6366F1,#818CF8);font-family:var(--display);font-weight:700;color:#fff}
.brand b{font-family:var(--display);font-size:1.15rem;letter-spacing:.08em}
.tags{display:flex;gap:8px;flex-wrap:wrap}
.chip{border:1px solid var(--line);border-radius:6px;padding:4px 9px;white-space:nowrap}

/* manager view */
.hero{display:grid;gap:20px;position:relative;overflow:hidden}
.hero::before{content:"";position:absolute;inset:auto -20% -60% auto;width:60%;height:120%;
  background:radial-gradient(closest-side,var(--status-glow),transparent);pointer-events:none}
.hero-top{display:flex;justify-content:space-between;gap:16px;align-items:flex-start;flex-wrap:wrap}
.hero h1{font-size:clamp(1.6rem,3.6vw,2.4rem);line-height:1.1;max-width:22ch}
.light{display:inline-flex;align-items:center;gap:10px;border-radius:999px;padding:8px 16px 8px 12px;
  border:1px solid var(--status);color:var(--status);font-weight:600;background:rgba(0,0,0,.25)}
.light i{width:12px;height:12px;border-radius:50%;background:var(--status);box-shadow:0 0 14px var(--status)}
.s-ok{--status:var(--ok);--status-glow:rgba(16,185,129,.16)}
.s-warn{--status:var(--warn);--status-glow:rgba(245,158,11,.16)}
.s-crit{--status:var(--crit);--status-glow:rgba(239,68,68,.18)}
.verdicts{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;position:relative}
.verdict{border-top:1px solid var(--line);padding-top:14px;display:grid;gap:6px;align-content:start}

/* kpis */
.kpis{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}
.kpi{display:grid;gap:8px}
.kpi .value{font-family:var(--display);font-size:2rem;font-weight:600;line-height:1}
.delta{font-size:.85rem;font-weight:600}
.up{color:var(--ok)} .down{color:var(--crit)} .flat{color:var(--muted)}

/* funnel */
.funnel{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}
.stage{display:grid;gap:10px;position:relative}
.stage .value{font-family:var(--display);font-size:1.7rem;font-weight:600}
.bar{height:6px;border-radius:3px;background:var(--surface-2);overflow:hidden}
.bar span{display:block;height:100%;background:var(--accent);border-radius:3px}
.step{font-size:.8rem;color:var(--muted)}

/* two col */
.cols{display:grid;grid-template-columns:minmax(0,1.1fr) minmax(0,1fr);gap:12px}
.summary{font-size:1.02rem;line-height:1.6}
ul.clean{list-style:none;margin:0;padding:0;display:grid;gap:10px}
ul.clean li{padding-left:16px;position:relative}
ul.clean li::before{content:"";position:absolute;left:0;top:.65em;width:6px;height:6px;border-radius:50%;background:var(--accent)}
.finding{display:grid;gap:6px;padding:16px;border-radius:14px;background:var(--surface-2);border-left:3px solid var(--status)}
.finding .top{display:flex;justify-content:space-between;gap:10px;align-items:baseline;flex-wrap:wrap}
.pill{font-size:.7rem;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:var(--status)}
.empty{color:var(--muted);font-size:.95rem}

/* table */
.table-wrap{overflow-x:auto}
table{width:100%;border-collapse:collapse;min-width:640px}
th{text-align:left;font-size:.7rem;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);font-weight:500;padding:0 12px 10px}
td{padding:12px;border-top:1px solid var(--line);vertical-align:middle}
td.r,th.r{text-align:right}
.score{display:flex;align-items:center;gap:10px;min-width:120px}
.score .bar{flex:1}
.caption{color:var(--muted);font-size:.85rem;max-width:36ch}

/* actions */
ol.actions{margin:0;padding:0;list-style:none;display:grid;gap:10px;counter-reset:a}
ol.actions li{counter-increment:a;display:grid;grid-template-columns:32px 1fr;gap:12px;align-items:start}
ol.actions li::before{content:counter(a);font-family:var(--display);font-weight:600;width:28px;height:28px;border-radius:8px;
  display:grid;place-items:center;background:var(--glow);color:var(--accent)}

/* ideas */
.ideas-head{display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap}
select{background:var(--surface-2);color:var(--text);border:1px solid var(--line);border-radius:999px;
  padding:8px 14px;font:inherit;font-size:.9rem;cursor:pointer}
select:focus-visible,button:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.lesson{font-size:.92rem;color:var(--muted);border-left:2px solid var(--accent);padding-left:12px}
.ideas{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}
.idea-list{display:grid;gap:10px;align-content:start}
.idea{display:grid;gap:8px;padding:16px;border-radius:14px;background:var(--surface-2);border:1px solid transparent}
.idea:hover{border-color:var(--line)}
.idea .top{display:flex;justify-content:space-between;align-items:center;gap:8px}
.idea q{font-family:var(--display);font-size:1.05rem;font-weight:500;quotes:"“" "”"}
.why{font-size:.85rem;color:var(--muted)}
button.copy{background:none;border:1px solid var(--line);color:var(--muted);border-radius:999px;
  padding:4px 12px;font:inherit;font-size:.75rem;cursor:pointer}
button.copy:hover{color:var(--text);border-color:var(--accent)}

.verdict-card{display:grid;gap:12px;align-content:start;border-top:2px solid var(--status)}
.attr{display:grid;gap:6px;padding-block:10px;border-bottom:1px solid var(--line)}
.attr:last-child{border-bottom:0}
.attr .top{display:flex;justify-content:space-between;gap:8px;flex-wrap:wrap;align-items:baseline}
.attr .bar span{background:var(--status)}
footer{display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;color:var(--faint);font-size:.8rem}

@media (max-width:860px){
  .kpis{grid-template-columns:repeat(2,minmax(0,1fr))}
  .cols,.ideas,.verdicts,.funnel{grid-template-columns:1fr}
}
@media (max-width:420px){ .kpis{grid-template-columns:1fr} }
@media (prefers-reduced-motion:no-preference){ .bar span{transition:width .6s ease} }
"""

JS = """
(function(){
  var lib = JSON.parse(document.getElementById('clarea-library').textContent);
  var sel = document.getElementById('industry');
  function card(item){
    var d = document.createElement('div'); d.className = 'idea';
    var top = document.createElement('div'); top.className = 'top';
    var t = document.createElement('span'); t.className = 'tag'; t.textContent = item.type;
    var b = document.createElement('button'); b.className = 'copy'; b.type = 'button'; b.textContent = 'Copiar';
    b.addEventListener('click', function(){
      var done = function(){ b.textContent = 'Copiado'; setTimeout(function(){ b.textContent = 'Copiar'; }, 1400); };
      if (navigator.clipboard) { navigator.clipboard.writeText(item.text).then(done, function(){ b.textContent = 'Selecciona y copia'; }); }
    });
    top.appendChild(t); top.appendChild(b);
    var q = document.createElement('q'); q.textContent = item.text;
    var w = document.createElement('p'); w.className = 'why'; w.textContent = 'Por qué funciona: ' + item.why;
    d.appendChild(top); d.appendChild(q); d.appendChild(w);
    return d;
  }
  function render(key){
    ['hooks','ctas'].forEach(function(kind){
      var box = document.getElementById(kind + '-list'); box.innerHTML = '';
      lib.industries[key][kind].forEach(function(item){ box.appendChild(card(item)); });
    });
  }
  sel.addEventListener('change', function(){ render(sel.value); });
  render(sel.value);
})();
"""


def _delta(pct: float) -> str:
    cls = "up" if pct > 0 else "down" if pct < 0 else "flat"
    arrow = "▲" if pct > 0 else "▼" if pct < 0 else "•"
    return f'<span class="delta {cls} num">{arrow} {pct:+.1f}%</span>'


def _library(brand: str) -> dict:
    industries = {}
    for key, data in INDUSTRIES.items():
        industries[key] = {
            "name": data["nombre"],
            "hooks": [{"type": HOOK_TYPES[t]["nombre"], "why": HOOK_TYPES[t]["por_que"],
                       "text": data["hooks"][t].format(brand=brand)} for t in HOOK_TYPES],
            "ctas": [{"type": CTA_TYPES[t]["nombre"], "why": CTA_TYPES[t]["por_que"],
                      "text": data["ctas"][t].format(brand=brand)} for t in CTA_TYPES],
        }
    return {"industries": industries}


class HtmlDashboard:

    @staticmethod
    def render(summary: PeriodSummary, insight: DiagnosticInsight, full_document: bool = True) -> str:
        e = escape
        analyzer = MetricAnalyzer(summary)
        view = ManagerViewGenerator.generate(summary, insight)
        status_label, status_cls = STATUS[view.status]
        conv = analyzer.calculate_message_conversion_rate()
        eng = analyzer.calculate_engagement_rate()

        kpis = [
            ("Alcance", f"{summary.total_reach:,}", _delta(summary.reach_growth_pct), "Personas únicas que vieron la marca"),
            ("Interacciones", f"{summary.total_interactions:,}", _delta(summary.interactions_growth_pct), f"{eng}% de engagement"),
            ("Mensajes de venta", f"{summary.total_messages:,}", _delta(summary.messages_growth_pct), f"{conv}% del alcance escribió"),
            ("Seguidores nuevos", f"{summary.new_followers:,}", '<span class="delta flat">en el periodo</span>', f"{summary.posts_count} publicaciones"),
        ]
        kpi_html = "".join(
            f'<div class="card kpi"><span class="tag">{e(label)}</span>'
            f'<span class="value num">{value}</span>{delta}<span class="muted" style="font-size:.85rem">{e(note)}</span></div>'
            for label, value, delta, note in kpis
        )

        # 3-level funnel from the brief: Atención -> Interés -> Intención comercial.
        interest = sum(p.comments + p.shares + p.clicks for p in summary.posts)
        stages = [
            ("Nivel 1 · Atención", summary.total_reach, "Alcance total"),
            ("Nivel 2 · Interés", interest, "Comentarios, compartidos y clics"),
            ("Nivel 3 · Intención comercial", summary.total_messages, "Mensajes y cotizaciones"),
        ]
        funnel_html = ""
        for i, (label, value, note) in enumerate(stages):
            width = 100 if i == 0 else max(2, round(value / stages[0][1] * 100, 1)) if stages[0][1] else 0
            step = ""
            if i > 0 and stages[i - 1][1]:
                step = f'<span class="step num">{value / stages[i - 1][1] * 100:.1f}% pasa del nivel anterior</span>'
            funnel_html += (
                f'<div class="card stage"><span class="tag">{e(label)}</span>'
                f'<span class="value num">{value:,}</span>'
                f'<div class="bar" aria-hidden="true"><span style="width:{width}%"></span></div>'
                f'<span class="muted" style="font-size:.85rem">{e(note)}</span>{step}</div>'
            )

        findings_html = "".join(
            f'<div class="finding s-{SEVERITY[f.severity][1]}"><div class="top"><h3 style="font-size:1rem">{e(f.title)}</h3>'
            f'<span class="pill">{SEVERITY[f.severity][0]}</span></div>'
            f'<p>{e(f.diagnosis)}</p><p class="muted" style="font-size:.88rem">Dato: {e(f.evidence)}</p>'
            f'<p style="font-size:.92rem"><strong>Qué hacer:</strong> {e(f.prescription)}</p></div>'
            for f in insight.rule_findings
        ) or '<p class="empty">Ninguna situación de riesgo u oportunidad superó los umbrales en este periodo.</p>'

        rows = ""
        for idx, r in enumerate(analyzer.rank_posts(), 1):
            p = r["post"]
            rows += (
                f'<tr><td class="num muted">{idx}</td>'
                f'<td><strong>{e(p.topic)}</strong><div class="caption">{e(p.caption_preview or "")}</div></td>'
                f'<td>{e(FORMAT_LABELS.get(p.content_type, p.content_type))}</td>'
                f'<td class="r num">{p.reach:,}</td><td class="r num">{p.messages_inquired}</td>'
                f'<td class="r num">{r["conversion_rate"]:.2f}%</td>'
                f'<td><div class="score"><div class="bar"><span style="width:{r["score"]}%"></span></div>'
                f'<span class="num">{r["score"]}</span></div></td></tr>'
            )

        def attr_list(verdict):
            items = [a for a in insight.attribution if a.verdict == verdict]
            if not items:
                return '<p class="empty">Nada destacable en este periodo.</p>'
            return "".join(
                f'<div class="attr"><div class="top"><strong>{e(a.name)}</strong>'
                f'<span class="tag">{e(a.dimension)} · {a.posts} post{"s" if a.posts != 1 else ""}</span></div>'
                f'<p class="why">{e(a.reason)}{" Dato preliminar." if a.preliminary else ""}</p>'
                f'<div class="bar" aria-hidden="true"><span style="width:{min(100, a.conversion_index * 50):.0f}%"></span></div></div>'
                for a in items
            )
        attribution_html = ""
        if insight.attribution:
            attribution_html = (
                '<section><div class="section-head"><h2>Qué funcionó y qué falló</h2>'
                '<span class="tag">Por formato y tema · vs promedio de la cuenta</span></div>'
                '<div class="cols">'
                f'<div class="card s-ok verdict-card"><span class="pill">Funcionó</span>{attr_list("funciono")}</div>'
                f'<div class="card s-crit verdict-card"><span class="pill">Falló</span>{attr_list("fallo")}</div>'
                '</div></section>'
            )

        findings_list = "".join(f"<li>{e(x)}</li>" for x in insight.key_findings)
        actions = "".join(f"<li><span>{e(a)}</span></li>" for a in insight.recommended_actions)
        options = "".join(
            f'<option value="{k}"{" selected" if k == insight.industry else ""}>{e(v["nombre"])}</option>'
            for k, v in INDUSTRIES.items()
        )
        library = json.dumps(_library(summary.brand_name), ensure_ascii=False).replace("</", "<\\/")
        period_tag = f"{summary.platform} // {summary.period_label}".upper()

        body = f"""
<div class="wrap">
  <header>
    <div class="brand"><div class="mark">C</div><div><b>CLAREA</b><div class="tag">De métricas a decisiones</div></div></div>
    <div class="tags"><span class="tag chip">[ {e(summary.brand_name.upper())} ]</span><span class="tag chip">[ {e(period_tag)} ]</span></div>
  </header>

  <section class="card hero s-{status_cls}" aria-labelledby="gerente">
    <div class="hero-top">
      <div style="display:grid;gap:10px">
        <span class="tag" id="gerente">Vista Gerente</span>
        <h1>{e(view.status_reason)}</h1>
      </div>
      <span class="light"><i></i>{status_label}</span>
    </div>
    <div class="verdicts">
      <div class="verdict"><span class="tag">Logro principal</span><p>{e(view.main_achievement)}</p></div>
      <div class="verdict"><span class="tag">Cuello de botella</span><p>{e(view.bottleneck)}</p></div>
      <div class="verdict"><span class="tag">Próxima decisión</span><p><strong>{e(view.next_decision)}</strong></p></div>
    </div>
  </section>

  <section aria-label="Indicadores principales"><div class="kpis">{kpi_html}</div></section>

  <section>
    <div class="section-head"><h2>Embudo comercial</h2><span class="tag">Atención → Interés → Conversión</span></div>
    <div class="funnel">{funnel_html}</div>
  </section>

  <section class="cols">
    <div class="card" style="display:grid;gap:16px;align-content:start">
      <div class="section-head"><h2>Interpretado por Clarea</h2><span class="tag">{"Diagnóstico · redactado con Claude" if insight.ai_generated else "Diagnóstico"}</span></div>
      <p class="summary">{e(insight.executive_summary)}</p>
      <ul class="clean">{findings_list}</ul>
    </div>
    <div class="card" style="display:grid;gap:12px;align-content:start">
      <div class="section-head"><h2>Situaciones detectadas</h2><span class="tag">Motor de reglas</span></div>
      {findings_html}
    </div>
  </section>

  <section class="card">
    <div class="section-head"><h2>Ranking de publicaciones</h2><span class="tag">Score Clarea: 70% conversión · 30% engagement</span></div>
    <div class="table-wrap"><table>
      <thead><tr><th>#</th><th>Publicación</th><th>Formato</th><th class="r">Alcance</th><th class="r">Mensajes</th><th class="r">Conversión</th><th>Score</th></tr></thead>
      <tbody>{rows}</tbody>
    </table></div>
  </section>

  {attribution_html}

  <section class="card" style="display:grid;gap:16px">
    <div class="section-head"><h2>Qué hacer la próxima semana</h2><span class="tag">Recomendaciones</span></div>
    <ol class="actions">{actions}</ol>
  </section>

  <section style="gap:16px">
    <div class="ideas-head">
      <h2>Hooks y CTAs para tu próxima parrilla</h2>
      <label class="tag" for="industry" style="display:flex;align-items:center;gap:10px">Rubro <select id="industry">{options}</select></label>
    </div>
    <div class="ideas">
      <div class="idea-list"><p class="lesson"><strong>Hook.</strong> {e(HOOK_DEFINITION)}</p><div class="idea-list" id="hooks-list"></div></div>
      <div class="idea-list"><p class="lesson"><strong>CTA.</strong> {e(CTA_DEFINITION)}</p><div class="idea-list" id="ctas-list"></div></div>
    </div>
  </section>

  <footer><span>Generado por Clarea Engine</span><span>[ 2026 ]</span></footer>
</div>
<script type="application/json" id="clarea-library">{library}</script>
<script>{JS}</script>
"""
        head = (
            f"<title>Clarea · {e(summary.brand_name)}</title>"
            '<link rel="preconnect" href="https://fonts.googleapis.com">'
            '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
            '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500;12..96,600;12..96,700&family=Inter:wght@400;500;600&display=swap">'
            f"<style>{CSS}</style>"
        )
        if not full_document:
            return head + body
        return (
            '<!doctype html><html lang="es"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            f"{head}</head><body>{body}</body></html>"
        )
