# Changelog

Todos los cambios relevantes de este proyecto se documentan en este archivo.

El formato sigue las convenciones de [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/)
y este proyecto sigue [Semantic Versioning](https://semver.org/lang/es/).

## [0.3.0] - 2026-08-13

### Added

- OpenAPI Generator (`generators/`): transforma `analyzer.AnalysisResult` en un documento OpenAPI **3.0.3** (`generators.generate`), sin modificar ni depender de los motores internos del Analyzer.
- `generators/openapi_types.py`: parser del texto de tipo producido por el Analyzer (`ParsedType`/`parse_type_text`), tabla de tipos Java → OpenAPI (`PRIMITIVE_TYPES`), mapeo de Bean Validation (`@NotNull`/`@NotBlank`/`@NotEmpty`/`@Size`/`@Min`/`@Max`/`@Positive`/`@PositiveOrZero`/`@Negative`/`@NegativeOrZero`/`@Email`/`@Pattern`) a keywords de schema.
- `generators/openapi_schemas.py`: construcción de `components.schemas` a partir de `DTO`, con deduplicación por nombre y reutilización de `$ref` (sin lógica propia de detección de ciclos: el árbol de DTOs que entrega el Analyzer ya es acíclico).
- `generators/openapi_generator.py`: paths/operations/parameters/requestBody/responses/security/consumes-produces, estrategia determinista de `operationId` (con resolución de colisiones por sufijo numérico, nunca hashes), orden explícito de `paths`/schemas/parameters para generación determinista, serialización `to_json`/`to_yaml`.
- Política conservadora de `responses`: nunca asume `200 application/json` sin evidencia; usa la clave `"default"` cuando no hay `@ResponseStatus` reconocible o no hay `Response` en absoluto (endpoints del motor de fallback), siempre acompañado de un `Diagnostic`.
- Política conservadora de `security`: la evidencia de `@PreAuthorize`/`@Secured` se documenta como extensión `x-security-evidence` (nunca como un `securityScheme` inventado), con `Diagnostic`.
- Tipos no resueltos (no primitivos, sin DTO resoluble) generan `schema: {}` + `Diagnostic` (`OPENAPI_UNKNOWN_TYPE`), nunca una estructura supuesta. `Map<K,V>` se representa como `type: object` genérico sin `additionalProperties` tipado.
- Artefactos de ejemplo `examples/customer-service/openapi.yaml` y `openapi.json`, generados a partir del proyecto de ejemplo.
- 65 tests nuevos (84 → 149), organizados por capacidad (tipos, schemas, paths, parameters, request body, responses, consumes/produces, security, operationId con colisiones, serialización, golden-files limitados sobre el proyecto de ejemplo).

### Changed

- `pyproject.toml`: versión `0.2.0` → `0.3.0`; se agrega la dependencia de runtime `PyYAML>=6.0,<7.0` (MIT, usada exclusivamente para serialización YAML).
- `docs/05-OpenAPI.md`: reescrito para describir el comportamiento real implementado (antes era puramente aspiracional). Versión objetivo fijada en OpenAPI 3.0.3 (revirtiendo la aspiración de 3.1.x escrita en V0.1).
- `generators/__init__.py`: deja de ser un placeholder y expone la API pública del Generator.

### Scope

- No se implementó Swagger UI/Editor, un validador OpenAPI completo, generación de código cliente/servidor/SDK, documentación HTML, UI, CLI, CI/CD, Docker, Confluence, ni ningún proveedor LLM. Ver `docs/12-Roadmap.md`.
- `analyzer/` no se modificó: `models.py`, `__init__.py`, `ast_analyzer.py`, `ast_backend.py`, `dto_analyzer.py` y `spring_boot_analyzer.py` quedaron intactos; los 84 tests de V0.2 no se modificaron y continúan pasando.

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
