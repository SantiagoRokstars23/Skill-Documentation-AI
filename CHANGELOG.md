# Changelog

Todos los cambios relevantes de este proyecto se documentan en este archivo.

El formato sigue las convenciones de [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/)
y este proyecto sigue [Semantic Versioning](https://semver.org/lang/es/).

## [0.2.0] - 2026-08-13

### Added

- Motor de analisis AST (`analyzer/ast_backend.py`, `analyzer/ast_analyzer.py`) basado en `javalang`, motor principal del Analyzer, con el motor de V0.1 (`analyzer/spring_boot_analyzer.py`, sin modificar) reutilizado como fallback automatico por archivo cuando el AST no puede parsear un archivo.
- Resolucion de DTOs entre archivos del proyecto (`analyzer/dto_analyzer.py`): indice de clases/enums por nombre simple, campos con tipo/coleccion/anidamiento, deteccion de nombres ambiguos y de referencias ciclicas (ambos como `Diagnostic`, nunca resueltos por suposicion).
- Deteccion ampliada de Controllers: `@Controller` (ademas de `@RestController`) cuando tiene mappings HTTP, anotaciones fully-qualified, clases anidadas, metodos package-private.
- `@RequestMapping` con multiples `RequestMethod` (produce un `Endpoint` por metodo resuelto).
- `@RequestHeader` como nuevo origen de parametro (`ParameterSource.HEADER`).
- Reconocimiento de anotaciones de Bean Validation (`@NotNull`, `@NotBlank`, `@NotEmpty`, `@Size`, `@Min`, `@Max`, `@Email`, `@Pattern`, `@Positive`, `@PositiveOrZero`, `@Negative`, `@NegativeOrZero`) sobre campos de DTO y parametros.
- Analisis de respuesta (`Response`: wrapper `ResponseEntity`, tipo de cuerpo, coleccion, DTO resuelto, `@ResponseStatus`).
- `consumes`/`produces` desde `@RequestMapping` y las anotaciones `@*Mapping` (con fallback al valor de clase).
- Evidencia de seguridad (`@PreAuthorize`, `@Secured`) a nivel de clase y de metodo.
- Modelo de datos ampliado en `analyzer/models.py`, de forma aditiva (compatible con V0.1): `Controller`, `DTO`, `Field`, `Response`, `Validation`, `Diagnostic`, `DiagnosticSeverity`; `Evidence` gana `symbol`/`type`; `Parameter` gana `default_value`/`validations`/`dto`; `Endpoint` gana `java_method`/`consumes`/`produces`/`response`/`security`; `AnalysisResult` gana `controllers`/`diagnostics`.
- Ejemplo `examples/customer-service/` ampliado: DTOs con validaciones, DTO anidado (`Address`), enum (`CustomerStatus`), coleccion, endpoint con headers/seguridad/consumes/produces/`@ResponseStatus`, y un controller con sintaxis Java invalida a proposito para demostrar el motor de fallback.
- 44 tests nuevos (40 -> 84), cubriendo el modelo de datos ampliado, `dto_analyzer.py`, `ast_analyzer.py`, la orquestacion AST+fallback de `analyze_project`, y las nuevas capacidades del ejemplo.

### Changed

- `pyproject.toml`: version `0.1.0` -> `0.2.0`; se agrega la dependencia de runtime `javalang>=0.13.0,<0.14.0` (justificacion documentada en `docs/03-Arquitectura.md`).
- La forma exacta de `to_dict()` en `Parameter`/`Endpoint`/`Evidence` gano claves nuevas (ver `docs/13-Versionado.md`, seccion "V0.1.0 -> V0.2.0"). Dos tests de V0.1 que comparaban el dict exacto se actualizaron para reflejarlo, sin reducir su cobertura.

### Scope

- No se implementa generacion de OpenAPI, validacion, auditoria, CLI, integracion con Confluence, ni ningun proveedor LLM concreto en esta version. Ver `docs/12-Roadmap.md`.

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
