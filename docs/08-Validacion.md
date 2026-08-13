# 08 — Validacion

> La validacion **no** esta implementada (reservada para V0.4, ver `docs/12-Roadmap.md`). Este
> documento define el vocabulario y las bases conceptuales para esa fase futura.
>
> V0.2 introduce `DiagnosticSeverity` (`ERROR`/`WARNING`/`INFO`) a nivel del **Analyzer**
> (`docs/09-Auditoria.md`), que ya usa exactamente esta clasificacion de tres niveles para sus
> propios hallazgos (p. ej. `DTO_NAME_AMBIGUOUS` como WARNING). El futuro Validator podra
> reutilizar el mismo tipo `Diagnostic`/`DiagnosticSeverity` en vez de definir uno paralelo,
> aunque esa decision se toma cuando se implemente V0.4, no en V0.2.

## Validacion

Proceso deterministico que evalua si la documentacion generada (OpenAPI) es estructural y
semanticamente correcta respecto a la evidencia extraida por el Analyzer y respecto al estandar
OpenAPI.

## Clasificacion de hallazgos

- **Errores:** violaciones que invalidan la especificacion (p. ej. OpenAPI mal formado, un
  endpoint sin `responses`, un tipo de dato inexistente).
- **Warnings:** problemas que no invalidan la especificacion pero reducen su calidad (p. ej. una
  descripcion ausente, un ejemplo faltante).
- **Informacion:** observaciones neutras utiles para el desarrollador (p. ej. un endpoint fue
  documentado con baja confianza, ver `docs/09-Auditoria.md`).

## Validaciones OpenAPI (futuras)

- Conformidad estructural con el esquema OpenAPI (version objetivo, ver `docs/05-OpenAPI.md`).
- Presencia de campos obligatorios por operacion (`responses`, `parameters` requeridos, etc.).
- Consistencia entre `paths` y `schemas` referenciados.

## Validaciones internas (futuras)

- Consistencia entre la evidencia del Analyzer y el contenido generado (p. ej. que todo parametro
  detectado como `required = true` aparezca como requerido en la especificacion).
- Deteccion de contenido generado sin evidencia de respaldo (para ser reportado por el Auditor).

## Relacion con el resto del pipeline

El Validator opera exclusivamente sobre la salida del OpenAPI Generator y la evidencia original
del Analyzer; no invoca al LLM Provider. Es un mecanismo deterministico, en linea con la regla de
IA "la validacion final debe realizarse mediante mecanismos deterministicos cuando sea posible"
(`prompts/V0.1-foundation.md` seccion 17).
