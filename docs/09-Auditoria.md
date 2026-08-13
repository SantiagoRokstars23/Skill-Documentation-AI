# 09 — Auditoria

> La auditoria **no** esta implementada en V0.1 (reservada para V0.4, ver `docs/12-Roadmap.md`).
> Este documento define el vocabulario y las bases conceptuales, y describe que soporte deja
> preparado el Analyzer de V0.1 para esta fase futura.

## Trazabilidad

Capacidad de responder, para cualquier elemento de la documentacion generada, "¿de donde salio
esta informacion?". La trazabilidad conecta un elemento de la especificacion OpenAPI con la
evidencia del codigo fuente que la origino (o con la ausencia de evidencia, si fue inferida por
el LLM).

## Evidencia

Informacion extraida deterministicamente del codigo fuente, con referencia a su origen (archivo,
y en el futuro, linea). En V0.1, el Analyzer adjunta a cada `Endpoint` un campo `evidence.file`
con el archivo de origen (ver `docs/07-Analisis.md`). Este es el punto de partida para la
trazabilidad completa de fases futuras.

## Confidence

Medida (futura) de cuanta confianza tiene el sistema en un elemento de documentacion generado:
alta cuando proviene directamente de evidencia deterministica, baja cuando proviene de inferencia
del LLM sin respaldo claro en el codigo. No implementada en V0.1.

## Origen de informacion

Todo contenido de documentacion debera poder clasificarse, en fases futuras, segun su origen:

- **Evidencia deterministica** (Analyzer).
- **Interpretacion del LLM sobre evidencia existente** (Skill + LLM Provider).
- **Inferencia del LLM sin evidencia directa** (debe marcarse explicitamente como tal).

## Deteccion de incertidumbre

Cuando el Analyzer no puede determinar un dato con certeza (p. ej. un mapping sin metodo HTTP
explicito), no debe inventarlo: debe omitirlo y reportarlo como advertencia
(`AnalysisResult.warnings`). Esto preserva la incertidumbre en lugar de descartarla u ocultarla,
segun la regla de IA 4 (`prompts/V0.1-foundation.md` seccion 17).

## Auditoria futura

En fases futuras (V0.4), el Auditor debera:

- Recorrer la especificacion OpenAPI generada y clasificar cada elemento segun su origen y
  confidence.
- Producir un reporte de trazabilidad y cobertura de evidencia.
- Servir de base para la futura Deteccion de Divergencias (Drift Detection, V3.0).
