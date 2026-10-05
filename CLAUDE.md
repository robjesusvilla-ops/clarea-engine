# Clarea: notas de desarrollo

Motor en Python que convierte métricas de redes (Facebook primero) en diagnósticos y acciones para dueños de negocio y agencias. Todo el texto visible para el usuario va en español; el código y los commits, en inglés.

## Comandos

- Instalar: `pip install -e ".[web,ai,dev]"`
- Tests: `python -m pytest -q` (deben pasar antes de cada push)
- Probar de punta a punta: `clarea analyze examples/sample_facebook_metrics.json --html /tmp/d.html -o /tmp/r.md`
- App web: `clarea web`

## Arquitectura

- Todo análisis pasa por `clarea/pipeline.py::analyze`. CLI, web, MCP y envío lo usan; no dupliques lógica en esas capas.
- `core/rules.py` es la fuente de verdad del diagnóstico. La capa de IA (`ai/claude_diagnosis.py`) redacta sobre las reglas y nunca las reemplaza; ante cualquier fallo vuelve al diagnóstico local.
- `knowledge/hooks_library.py` y `RuleThresholds` contienen la experiencia del negocio: cambios ahí son decisiones de producto, consúltalos con Robert.
- Los datos de clientes viven en `clarea_data/` (ignorado por git). Nunca subas métricas reales ni tokens.

## Reglas

- Credenciales solo por variables de entorno (`.env.example` lista todas). El token de Meta va en el header `Authorization`, nunca en URLs.
- Cada función nueva lleva su test. Para APIs externas (Meta, Claude, SMTP) usa dobles de prueba, como en `tests/test_meta_graph.py` y `tests/test_ai_diagnosis.py`.
- Fuera del MVP (no construir): programación de publicaciones, bandeja de entrada unificada, redes fuera de Meta, apps móviles nativas, compra de pauta.
