# 09 — Auditoria

> El Auditor como componente **no** esta implementado y **no tiene version de roadmap asignada
> todavia** (el roadmap original lo agrupaba con el Validator en V0.4; la directriz real de V0.4
> acoto el alcance unicamente al OpenAPI Quality Validator, y el Auditor quedo pendiente de una
> futura directriz -- ver la nota correspondiente en `docs/12-Roadmap.md`). Este documento define
> el vocabulario y las bases conceptuales, y describe que soporte deja preparado el Analyzer
> (V0.1 y V0.2) para esta fase futura: evidencia estructurada (`Evidence`) y diagnostics
> (`Diagnostic`), ambos ya implementados como parte del Analyzer, no del Auditor.

## Trazabilidad

Capacidad de responder, para cualquier elemento de la documentacion generada, "¿de donde salio
esta informacion?". La trazabilidad conecta un elemento de la especificacion OpenAPI con la
evidencia del codigo fuente que la origino (o con la ausencia de evidencia, si fue inferida por
el LLM).

## Evidencia

Informacion extraida deterministicamente del codigo fuente, con referencia a su origen. `Evidence`
(`analyzer/models.py`) tiene cuatro campos: `file`, `line`, `symbol` (el nombre del elemento Java
concreto: clase, metodo, parametro, campo) y `type` (el tipo de elemento:
`"controller"`/`"endpoint"`/`"parameter"`/`"dto"`/`"field"`/`"validation"`/`"response"`). Se usa
consistentemente en `Controller`, `Endpoint`, `Parameter`, `DTO`, `Field`, `Validation` y
`Response`. Ejemplo real (motor AST, `examples/customer-service`):

```json
{
  "file": ".../CustomerController.java",
  "line": 37,
  "symbol": "createCustomer",
  "type": "endpoint"
}
```

Cuando un endpoint proviene del motor de fallback (V0.1, ver `docs/07-Analisis.md`), su evidencia
solo incluye `file` y `line` (`symbol`/`type` quedan en `None`): el motor regex no tiene la misma
resolucion de simbolos que el motor AST. Esto es una diferencia de riqueza, no un error — se
prefiere `None` explicito a inventar un valor.

## Diagnostics (V0.2)

`Diagnostic` (`analyzer/models.py`) es el canal estructurado de hallazgos del Analyzer, con
`severity` (`ERROR`/`WARNING`/`INFO`), `code` (identificador estable, p. ej.
`"DTO_NAME_AMBIGUOUS"`), `message` y `evidence`. Complementa (no reemplaza) el canal
`AnalysisResult.warnings: list[str]` heredado de V0.1, que se mantiene por compatibilidad y se
deriva de los `Diagnostic` de severidad `WARNING`.

Codigos producidos actualmente por el Analyzer:

| Codigo | Severidad | Origen | Significado |
|---|---|---|---|
| `AST_MAPPING_WITHOUT_HTTP_METHOD` | WARNING | `ast_analyzer.py` | Un `@RequestMapping` no tiene ningun `RequestMethod` resoluble; el endpoint se omite. |
| `DTO_NAME_AMBIGUOUS` | WARNING | `dto_analyzer.py` | Dos o mas clases/enums del proyecto comparten el mismo nombre simple; no se resuelve el DTO. |
| `DTO_CYCLE_DETECTED` | INFO | `dto_analyzer.py` | Referencia ciclica entre DTOs; se detiene la expansion anidada en ese punto. |
| `AST_PARSE_FALLBACK` | INFO | `analyzer/__init__.py` | Un archivo no pudo parsearse como AST; se uso el motor de fallback de V0.1 para ese archivo. |
| `LEGACY_ENGINE_WARNING` | WARNING | `analyzer/__init__.py` | Envoltorio como `Diagnostic` de un warning de texto plano producido por el motor de fallback. |

Esta lista es ampliable: agregar un nuevo `code` no rompe el modelo (regla global 12 de V0.1,
seccion 5.11 de la directriz V0.2 exige poder ampliarla).

## Confidence

Medida (futura) de cuanta confianza tiene el sistema en un elemento de documentacion generado:
alta cuando proviene directamente de evidencia deterministica, baja cuando proviene de inferencia
del LLM sin respaldo claro en el codigo. No implementada como campo explicito todavia; los
`Diagnostic` de V0.2 son un precursor directo (un elemento con un `Diagnostic` asociado es, por
definicion, de menor confianza que uno sin ninguno).

## Origen de informacion

Todo contenido de documentacion debera poder clasificarse, en fases futuras, segun su origen:

- **Evidencia deterministica** (Analyzer, motor AST o motor de fallback).
- **Interpretacion del LLM sobre evidencia existente** (Skill + LLM Provider).
- **Inferencia del LLM sin evidencia directa** (debe marcarse explicitamente como tal).

## Deteccion de incertidumbre

Regla fundamental del Analyzer (ver `docs/03-Arquitectura.md`, decision 4, y
`docs/07-Analisis.md`): cuando un dato no puede determinarse con confianza suficiente, no se
inventa. Se omite y se registra un `Diagnostic` (o, en el motor de fallback heredado de V0.1, un
warning de texto). Ejemplos concretos ya implementados: un mapping sin metodo HTTP resoluble, un
nombre de DTO ambiguo entre archivos, una referencia ciclica entre DTOs, un archivo que no pudo
analizarse con el motor AST.

## Auditoria futura

En fases futuras (V0.4), el Auditor debera:

- Recorrer la especificacion OpenAPI generada y clasificar cada elemento segun su origen y
  confidence, apoyandose en `Evidence` y `Diagnostic` ya producidos por el Analyzer.
- Producir un reporte de trazabilidad y cobertura de evidencia.
- Servir de base para la futura Deteccion de Divergencias (Drift Detection, V3.0).
