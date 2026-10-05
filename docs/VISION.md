# Visión de Clarea

> **Metricool te muestra los números. Clarea te dice qué significan, qué hacer después y te enseña a hacerlo.**

## El problema

Hoy hay muchos emprendedores con redes sociales, pero pocos saben manejarlas.
Las herramientas actuales (Meta Business Suite, Metricool, Hootsuite) muestran
gráficos de alcance, likes e impresiones, pero no responden lo que el dueño del
negocio realmente necesita saber:

- ¿Qué contenido debo hacer la próxima semana?
- ¿Por qué esta publicación funcionó y la otra no?
- ¿Qué es un *hook* o un *CTA* y cómo lo aplico a **mi** negocio?

## Qué hace distinta a Clarea

Clarea no es solo un panel de métricas. Tiene tres capas:

1. **Analiza.** Lee las métricas y separa las que son "de vanidad" (likes,
   alcance) de las que traen negocio (mensajes, cotizaciones, ventas).
2. **Aconseja.** Dice qué funcionó, qué no y qué hacer después, con acciones
   concretas.
3. **Enseña.** Explica los conceptos (hook, CTA, formato, frecuencia) con
   ejemplos adaptados al rubro del usuario, para que aprenda a hacerlo por su
   cuenta.

Los consejos y la parte de enseñanza vienen de la **experiencia real en manejo
de redes** del creador del proyecto. Ese criterio es el corazón de Clarea y lo
que no se copia fácilmente.

## Para quién es

- **Dueños de negocio y emprendedores** que manejan sus propias redes y no saben
  por dónde empezar.
- **Agencias** que manejan varios clientes y necesitan reportes claros y
  accionables para entregarles.

## Qué debe lograr el usuario

Después de usar Clarea, el usuario debe tener **una idea clara de qué contenido
hacer y cómo hacerlo**, no solo saber cómo le fue.

## Cómo se usará (visión final)

- **App web** donde el usuario conecta su cuenta y ve su diagnóstico.
- **Reportes automáticos** que le llegan por **correo o WhatsApp**.

## Decisiones tomadas

| Tema | Decisión | Por qué |
|------|----------|---------|
| Primera red | Facebook | Es más sencilla para probar; Instagram es más compleja. |
| Siguiente red | Instagram | Después de validar con Facebook. |
| Datos | CSV de Meta Business Suite y API oficial de Meta, solo lectura | Ver docs/CONECTAR_META.md. |
| Ritmo | Proyecto personal, paso a paso | Se trabaja en los tiempos disponibles. |

## Equipo

- **Robert Villa**: idea, producto y experiencia en redes sociales.
- **Hermano (programador)**: apoyo en desarrollo.

## Estado actual (octubre 2026)

- Motor en Python con las 6 reglas maestras, Vista Gerente con semáforo, qué funcionó y qué falló, ranking de posts y hooks/CTAs por rubro con su explicación.
- Lee el CSV que exporta Meta Business Suite y la plantilla propia; compara contra el periodo anterior.
- Conector de solo lectura con la API de Meta, diagnóstico opcional redactado con Claude.
- App web multi-cliente, dashboard HTML, reporte Markdown, envío por correo y mensaje para WhatsApp.
- **Pendiente:** validar con datos reales de Qhatai y ajustar umbrales y textos con esa experiencia.

## Hoja de ruta por fases

1. ✅ **Cerebro de Clarea**: reglas, Vista Gerente, hooks y CTAs por rubro.
2. ✅ **Facebook con datos reales**: CSV de Meta y API de solo lectura. Falta probar con Qhatai.
3. ✅ **Reportes** por correo y mensaje para WhatsApp (envío automático por WhatsApp pendiente).
4. ✅ **App web** multi-cliente.
5. ⬜ **Instagram**, roles agencia/cliente y pagos.

## Preguntas abiertas

- ¿Qué rubros de negocio se atienden primero?
- ¿Cómo es un buen reporte para un emprendedor que no sabe de marketing? (largo,
  tono, formato)
- ¿El modelo será gratuito, de pago o mixto?
