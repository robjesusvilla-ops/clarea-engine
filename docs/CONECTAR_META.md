# Conectar Clarea con la API de Meta

Hay dos formas de darle datos a Clarea. Empieza por la primera.

## Opción 1: exportar el CSV (sin permisos ni tokens)

1. Entra a **Meta Business Suite** → **Estadísticas** → **Contenido**.
2. Elige el periodo (por ejemplo, el mes anterior) y pulsa **Exportar datos**.
3. Analiza el archivo:

   ```bash
   clarea analyze export.csv -b "Mi marca" -p "Mayo 2026" --html dashboard.html
   ```

   O súbelo en la app web, dentro del cliente.

Clarea reconoce las columnas de la exportación en español o en inglés. Si una columna falta (por ejemplo, guardados), esa métrica queda en 0 y las reglas que dependen de ella no se activan.

## Opción 2: la API de Meta (automático)

Clarea solo **lee**: no puede publicar, borrar ni responder mensajes.

### 1. Crear la app

1. Entra a [developers.facebook.com](https://developers.facebook.com) con la cuenta que administra la página.
2. Crea una app de tipo **Empresa** (Business).
3. Agrega el producto que da acceso a páginas (en el panel suele aparecer como *Facebook Login for Business* o como acceso a la API de páginas).

Meta cambia los nombres de su panel con frecuencia; si algo no coincide, busca en su documentación "Page access token".

### 2. Pedir los permisos de lectura

- `pages_read_engagement`: publicaciones, reacciones, comentarios.
- `read_insights`: alcance, impresiones, clics y estadísticas de la página.
- `pages_show_list`: para elegir la página.

Mientras la app esté en **modo desarrollo**, funciona con las páginas que tú administras. Para conectar páginas de clientes, Meta pide una **revisión de la app** (App Review).

### 3. Obtener el token de página y el ID

1. En el **Explorador de la API Graph**, elige tu app, pide los permisos de arriba y genera un **token de usuario**.
2. Consulta `me/accounts`: cada página trae su `id` y su `access_token` (el token de página).
3. Un token de usuario de corta duración dura horas. Para uso continuo, cámbialo por uno de **larga duración** antes de pedir el token de página.

### 4. Guardarlos sin exponerlos

El token es como una contraseña. **Nunca** lo pongas en el código, en GitHub ni en un chat. Guárdalo como variable de entorno:

```bash
export META_PAGE_TOKEN="EAAB..."
export META_PAGE_ID="1234567890"
```

En Claude Code en la web, agrégalas en la configuración del entorno (menú del entorno → Edit). En tu computadora, puedes ponerlas en un archivo `.env` (ya está en `.gitignore`).

### 5. Descargar y analizar

```bash
clarea fetch --since 2026-05-01 --until 2026-05-31 -p "Mayo 2026" -o mayo.json -i piscinas
clarea analyze mayo.json --html dashboard.html
# o guardarlo en el historial del cliente
clarea client import qhatai-piscinas mayo.json -k 2026-05
```

## Límites de la API que conviene saber

- **Los mensajes no se pueden asignar a cada publicación.** La API da el total de conversaciones nuevas de la página, no cuántas generó cada post. Por eso, con datos de la API, las reglas por tema (R3) y el ranking por conversión pierden precisión. Si anotas los mensajes por post en la plantilla CSV, el análisis es completo.
- **Meta retira y renombra métricas** entre versiones de la API. Clarea pide cada métrica por separado: si Meta deja de dar una, esa queda en 0 y el resto del análisis sigue funcionando. Los nombres de las métricas están al inicio de `clarea/connectors/meta_graph.py`.
- **El alcance total del periodo** se aproxima sumando el alcance de cada post, porque una misma persona puede ver varios posts.
