# 12 — Roadmap

Este roadmap refleja el orden incremental planeado para el proyecto. Cada version debe
completarse (criterios de aceptacion + Definition of Done) antes de iniciar la siguiente.

| Version | Nombre | Estado |
|---------|--------|--------|
| V0.1 | Foundation & Architecture | **En progreso / esta version** |
| V0.2 | Spring Boot Analyzer | Futuro |
| V0.3 | OpenAPI Generator | Futuro |
| V0.4 | Validator + Auditor | Futuro |
| V0.5 | LLM Providers | Futuro |
| V0.6 | CLI | Futuro |
| V0.7 | Confluence Integration | Futuro |
| V1.0 | Production | Futuro |
| V2.0 | Documentation Quality Gate | Futuro |
| V3.0 | Drift Detection | Futuro |

## Resumen por version

- **V0.1 — Foundation & Architecture:** estructura del proyecto, documentacion inicial, Skill
  inicial, interfaz de LLM Provider, Analyzer inicial funcional. Ver `prompts/V0.1-foundation.md`.
- **V0.2 — Spring Boot Analyzer:** profundizacion del Analyzer (mas anotaciones, mas robustez,
  posiblemente resolucion de DTOs y herencia entre controllers).
- **V0.3 — OpenAPI Generator:** transformacion de la evidencia del Analyzer (mediada por la Skill
  y el LLM Provider) en especificaciones OpenAPI.
- **V0.4 — Validator + Auditor:** validacion estructural/semantica de la especificacion generada y
  auditoria de trazabilidad/confidence.
- **V0.5 — LLM Providers:** implementaciones concretas de la interfaz `LLMProvider` (Claude,
  Gemini, OpenAI u otros).
- **V0.6 — CLI:** herramienta de linea de comandos que expone el pipeline completo.
- **V0.7 — Confluence Integration:** conexion de la salida OpenAPI con el proyecto Python
  existente que publica en Confluence.
- **V1.0 — Production:** endurecimiento, empaquetado y estabilizacion para uso en produccion.
- **V2.0 — Documentation Quality Gate:** control de calidad de documentacion como gate en flujos
  de desarrollo.
- **V3.0 — Drift Detection:** deteccion automatica de divergencias entre codigo y documentacion.

Ninguna de las versiones futuras se implementa, ni parcialmente, dentro de V0.1 (Scope Lock,
`prompts/V0.1-foundation.md` seccion 19).
