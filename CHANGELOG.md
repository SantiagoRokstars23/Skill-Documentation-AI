# Changelog

Todos los cambios relevantes de este proyecto se documentan en este archivo.

El formato sigue las convenciones de [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/)
y este proyecto sigue [Semantic Versioning](https://semver.org/lang/es/).

## [0.1.0] - 2026-08-13

### Added

- Estructura base del proyecto (`docs/`, `skill/`, `providers/`, `analyzer/`, `validators/`, `generators/`, `tests/`, `examples/`).
- Documentacion inicial completa en `docs/` (14 documentos: modelo, objetivos, arquitectura, skill, OpenAPI, LLM, analisis, validacion, auditoria, seguridad, integracion, roadmap, versionado, glosario).
- `README.md` orientado a desarrolladores.
- `CLAUDE.md` como documento de gobierno del desarrollo.
- Skill inicial de documentacion (`skill/SKILL.md`, reglas, referencias y plantillas), independiente de proveedor LLM.
- Interfaz conceptual de `LLMProvider` en `providers/base.py` (sin implementaciones concretas).
- Placeholders documentados para `validators/` (reservado para V0.4) y `generators/` (reservado para V0.3).
- Analyzer funcional para microservicios Java/Spring Boot: deteccion de `@RestController`, mappings HTTP (`@GetMapping`, `@PostMapping`, `@PutMapping`, `@DeleteMapping`, `@PatchMapping`, `@RequestMapping`), paths, `@PathVariable`, `@RequestParam` y `@RequestBody`.
- Modelo de metadata estructurado y serializable (`analyzer/models.py`) con soporte inicial para evidencia (archivo de origen).
- Suite de tests unitarios del Analyzer (casos normales, limite y estructuras incompletas).
- Ejemplo de microservicio Spring Boot en `examples/customer-service/` para validar el Analyzer.

### Scope

- No se implementa generacion de OpenAPI, validacion, auditoria, CLI, ni integracion con Confluence en esta version. Ver `docs/12-Roadmap.md`.
