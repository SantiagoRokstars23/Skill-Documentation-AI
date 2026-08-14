# 12 — Roadmap

Este roadmap refleja el orden incremental planeado para el proyecto. Cada version debe
completarse (criterios de aceptacion + Definition of Done) antes de iniciar la siguiente.

| Version | Nombre | Estado |
|---------|--------|--------|
| V0.1 | Foundation & Architecture | Completada (`v0.1.0`) |
| V0.2 | Spring Boot Analyzer (Advanced) | Completada (`v0.2.0`) |
| V0.3 | OpenAPI Generator | Completada (`v0.3.0`) |
| V0.4 | OpenAPI Quality Validator | Completada (`v0.4.0`) |
| V0.5 | CLI & Developer Experience | **Completada / esta version** |
| V0.7 | Confluence Integration | Futuro |
| V1.0 | Production | Futuro |
| V2.0 | Documentation Quality Gate | Futuro |
| V3.0 | Drift Detection | Futuro |
| — | LLM Providers | Futuro, sin numero de version asignado (ver nota mas abajo) |

**Nota (V0.5):** el roadmap original asignaba V0.5 a "LLM Providers" y V0.6 a "CLI". La
directriz real recibida para V0.5 (`prompts/V0.5—CLI-&-DEVELOPER-EXPERIENCE.md`) prioriza la CLI,
confirmada explicitamente por el responsable del proyecto. "LLM Providers" se reprograma para una
version futura sin numero fijo todavia, para no forzar la numeracion antigua; se decidira su
posicion exacta en el roadmap cuando se aborde. "CLI" deja de tener su propio hueco en V0.6 porque
ya se implemento aqui, en V0.5.

## Resumen por version

- **V0.1 — Foundation & Architecture:** estructura del proyecto, documentacion inicial, Skill
  inicial, interfaz de LLM Provider, Analyzer inicial funcional. Ver `prompts/V0.1-foundation.md`.
- **V0.2 — Spring Boot Analyzer (Advanced):** motor hibrido AST (`javalang`) + fallback regex de
  V0.1; Controllers/Endpoints/Parameters ampliados (fully-qualified, package-private, multiples
  `RequestMethod`, headers, consumes/produces, seguridad); resolucion de DTOs entre archivos
  (campos, validaciones, anidamiento, colecciones, enums); `Response` (wrapper/body/status);
  `Diagnostic` estructurado. Ver `prompts/V0.2-ADVANCED-SPRING-BOOT-ANALYZER.md` y
  `docs/07-Analisis.md`. Herencia entre controllers **no** se resolvio (queda para una version
  futura, ver limitaciones en `docs/07-Analisis.md`).
- **V0.3 — OpenAPI Generator:** transformacion de `analyzer.AnalysisResult` en un documento
  OpenAPI 3.0.3 (`generators.generate`), con politicas conservadoras documentadas para responses
  sin evidencia de status, tipos no resueltos, y evidencia de seguridad sin scheme concreto. Sin
  modificaciones al Analyzer. Ver `prompts/V0.3-OPENAPI-GENERATOR.md` y `docs/05-OpenAPI.md`. La
  transformacion **no** pasa por la Skill ni por un LLM Provider (ninguno de los dos existe
  todavia como implementacion): consume directamente la metadata del Analyzer.
- **V0.4 — OpenAPI Quality Validator:** capa propia de validacion estructural y de calidad
  (`validator.validate`/`validate_json`/`validate_yaml`) sobre documentos OpenAPI 3.0.3 ya
  construidos, sin volver a analizar Java ni depender de una libreria de validacion externa.
  Reutiliza `Diagnostic`/`DiagnosticSeverity`/`Evidence` del Analyzer (`Evidence.file` como JSON
  Pointer RFC 6901). Ver `prompts/V0.4-OPENAPI-VALIDATOR.md` y `docs/05-OpenAPI.md`. **Nota:** el
  roadmap original agrupaba "Validator + Auditor" en V0.4; la directriz real de V0.4 acoto el
  alcance unicamente al Validator de OpenAPI — la Auditoria de trazabilidad/confidence permanece
  sin version asignada, pendiente de una futura directriz.
- **V0.5 — CLI & Developer Experience:** herramienta de linea de comandos (`spring-doc`) que
  orquesta Analyzer -> Generator -> Validator mediante sus APIs publicas (`analyze`, `generate`,
  `validate`), con salida humana y `--json` (reporte estructurado, independiente del `--format`
  del artefacto OpenAPI), exit codes deterministas, `--strict`/`--quiet`, y manejo de errores de
  usuario vs. errores internos. Ver `prompts/V0.5—CLI-&-DEVELOPER-EXPERIENCE.md` y
  `docs/03-Arquitectura.md`. No implementa ningun proveedor LLM (movido fuera de esta version, ver
  nota de la tabla de arriba).
- **V0.7 — Confluence Integration:** conexion de la salida OpenAPI con el proyecto Python
  existente que publica en Confluence.
- **V1.0 — Production:** endurecimiento, empaquetado y estabilizacion para uso en produccion.
- **V2.0 — Documentation Quality Gate:** control de calidad de documentacion como gate en flujos
  de desarrollo.
- **V3.0 — Drift Detection:** deteccion automatica de divergencias entre codigo y documentacion.

Ninguna de las versiones futuras se implementa, ni parcialmente, dentro de V0.1 (Scope Lock,
`prompts/V0.1-foundation.md` seccion 19).
