<div align="center">

# ⚡ Clarea

### De métricas a decisiones

[![CI](https://github.com/robjesusvilla-ops/clarea-engine/actions/workflows/ci.yml/badge.svg)](https://github.com/robjesusvilla-ops/clarea-engine/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-Compatible-purple.svg)](https://modelcontextprotocol.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

> **Metricool te muestra los datos. Clarea te dice qué significan y qué hacer después.**

</div>

Clarea analiza las métricas de redes sociales de un negocio y entrega lo que un dueño o una agencia necesita para decidir: un semáforo de salud, qué funcionó y qué no, qué hacer la próxima semana y los hooks y CTAs para hacerlo. Separa la atención (alcance, likes) de la intención comercial (mensajes, cotizaciones), porque lo que importa es lo segundo.

## Qué hace

| Módulo | Qué entrega |
|---|---|
| **Vista Gerente** | Semáforo 🟢🟡🔴, logro principal, cuello de botella y próxima decisión, en una pantalla |
| **KPIs y embudo** | Alcance, interacciones, mensajes y seguidores con su variación, y el embudo Atención → Interés → Intención comercial |
| **Interpretado por Clarea** | Diagnóstico en lenguaje de negocio (local, o redactado con Claude) |
| **Motor de reglas** | Las 6 reglas expertas: alto alcance y pocos mensajes, likes sin conversación, tema que supera el promedio, muchos guardados, seguidores sin clientes, caída en posts de venta |
| **Ranking de publicaciones** | Score Clarea de 0 a 100: 70 % conversión a mensajes, 30 % engagement |
| **Qué funcionó y qué falló** | Cada formato y tema comparado contra el promedio de la cuenta |
| **Hooks y CTAs** | Por rubro, con su explicación de por qué funcionan; con Claude, también a medida |
| **Reportes** | Dashboard HTML, reporte Markdown, correo con adjuntos y mensaje listo para WhatsApp |

## Instalación

```bash
git clone https://github.com/robjesusvilla-ops/clarea-engine.git
cd clarea-engine
pip install -e ".[web,ai]"      # o solo "pip install -e ." para el motor
```

## Uso rápido

```bash
# Analizar el ejemplo incluido y generar el dashboard
clarea analyze examples/sample_facebook_metrics.json --html dashboard.html -o reporte.md

# Analizar un CSV exportado de Meta Business Suite, comparando con el mes anterior
clarea analyze mayo.csv -b "Qhatai Piscinas" -p "Mayo 2026" --previous abril.csv --new-followers 210 --html dashboard.html
```

**Datos que acepta:**
- El CSV que exporta **Meta Business Suite** (Estadísticas → Contenido → Exportar). Reconoce columnas en español o inglés, separadas por coma o punto y coma.
- La [plantilla de Clarea](examples/plantilla_metricas_mayo.csv), con una columna `tema` opcional.
- El JSON que genera `clarea fetch` desde la API de Meta.

Si el archivo no trae el tema de cada post, Clarea lo deduce del texto: resultados, educativo, promoción, diseño, detrás de escena o institucional.

## App web

```bash
clarea web          # abre http://127.0.0.1:8000
```

Crea clientes, sube el CSV de cada mes y mira el dashboard de cada periodo, comparado contra el mes anterior. Desde ahí descargas el reporte, lo envías por correo o lo compartes por WhatsApp.

Antes de abrirla a otros equipos o a internet, ponle contraseña:

```bash
export CLAREA_WEB_USER=robert CLAREA_WEB_PASSWORD="una-clave-larga"
clarea web --host 0.0.0.0
```

Los datos de los clientes se guardan en la carpeta `clarea_data/` (o en `CLAREA_DATA_DIR`), que no se sube a GitHub.

## Varios clientes desde la terminal

```bash
clarea client add "Qhatai Piscinas" -i piscinas --email gerencia@qhatai.pe --whatsapp "+51 999 888 777"
clarea client import qhatai-piscinas abril.csv -k 2026-04 -l "Abril 2026"
clarea client import qhatai-piscinas mayo.csv  -k 2026-05 -l "Mayo 2026" --new-followers 210
clarea client report qhatai-piscinas --html dashboard.html
clarea client send qhatai-piscinas
clarea client list
```

## Envío de reportes

**Correo.** Configura una cuenta SMTP con variables de entorno. Con Gmail usa una [contraseña de aplicación](https://support.google.com/accounts/answer/185833), no tu contraseña normal.

```bash
export CLAREA_SMTP_HOST=smtp.gmail.com CLAREA_SMTP_PORT=587
export CLAREA_SMTP_USER=tu-correo@gmail.com CLAREA_SMTP_PASSWORD="contraseña-de-aplicación"
```

Sin `CLAREA_SMTP_HOST`, Clarea no envía nada: guarda el correo en `clarea_data/outbox/` para que lo revises.

**WhatsApp.** Clarea arma un mensaje corto y un enlace `wa.me` que abre WhatsApp con el texto escrito; tú solo pulsas enviar. El envío totalmente automático necesitaría la API de WhatsApp Business, que no está incluida.

## Conectar con la API de Meta

```bash
export META_PAGE_TOKEN="..."   # token de página con permisos de solo lectura
export META_PAGE_ID="..."
clarea fetch --since 2026-05-01 --until 2026-05-31 -p "Mayo 2026" -o mayo.json
clarea analyze mayo.json --html dashboard.html
```

Paso a paso, permisos y límites de la API en [docs/CONECTAR_META.md](docs/CONECTAR_META.md).

## Diagnóstico con Claude (opcional)

```bash
export ANTHROPIC_API_KEY="..."
clarea analyze mayo.csv --ai --html dashboard.html
```

Con `--ai`, Claude redacta el resumen, los hallazgos y las acciones, y agrega 3 hooks a medida a partir de los posts que mejor convirtieron. El motor de reglas sigue mandando: Claude explica y amplía las situaciones detectadas, nunca las contradice. Si no hay clave o la API falla, Clarea usa el diagnóstico local y te avisa.

## Servidor MCP para Claude

Agrega Clarea a la configuración de Claude Desktop o Claude Code:

```json
{
  "mcpServers": {
    "clarea": {
      "command": "python",
      "args": ["-m", "clarea.mcp_server"],
      "cwd": "/ruta/a/clarea-engine"
    }
  }
}
```

Claude puede usar `clarea_analyze_metrics` (diagnóstico completo, Vista Gerente, reglas y qué funcionó) y `clarea_generate_hooks_and_ctas` (por rubro).

## Ajustar el cerebro de Clarea

Aquí entra la experiencia en redes, sin tocar el resto del código:

- **Umbrales de las 6 reglas:** `RuleThresholds` en [`clarea/core/rules.py`](clarea/core/rules.py). Por ejemplo, desde qué porcentaje de mensajes sobre el alcance se consideran "pocos".
- **Hooks y CTAs por rubro:** [`clarea/knowledge/hooks_library.py`](clarea/knowledge/hooks_library.py). Para agregar un rubro, copia uno existente y cambia sus textos y palabras clave.
- **Ángulos de contenido:** las palabras clave que clasifican cada post están en [`clarea/core/classifier.py`](clarea/core/classifier.py).

## Estructura

```
clarea/
  core/          modelos, lectura de datos, clasificador, analizador, reglas, qué funcionó
  generators/    diagnóstico, Vista Gerente, hooks, reporte Markdown, dashboard HTML
  knowledge/     biblioteca de hooks y CTAs por rubro
  connectors/    API de Meta (solo lectura)
  ai/            capa opcional con Claude
  web/           app web (FastAPI)
  workspace.py   clientes e historial de periodos
  delivery.py    correo y WhatsApp
  pipeline.py    punto único de análisis
  cli.py         comandos de terminal
  mcp_server.py  servidor MCP
```

Para desarrollar: `pip install -e ".[web,ai,dev]"` y `python -m pytest`.

## Hoja de ruta

- [x] Lectura de CSV de Meta y plantilla propia, con comparación contra el periodo anterior
- [x] Motor con las 6 reglas, Vista Gerente, qué funcionó y qué falló, ranking de posts
- [x] Hooks y CTAs por rubro, con explicación
- [x] Dashboard HTML, reporte Markdown, correo y WhatsApp
- [x] App web multi-cliente
- [x] Conector de solo lectura con la API de Meta (Facebook)
- [x] Diagnóstico redactado con Claude
- [ ] Validación con datos reales de Qhatai y 3 agencias
- [ ] Instagram (API de Meta)
- [ ] Roles agencia / cliente y pagos recurrentes

## Licencia

MIT. Ver [LICENSE](LICENSE).

Desarrollado por **Robert Villa**.
