# Changelog

Todos los cambios relevantes de este proyecto se documentan en este archivo.

El formato sigue las convenciones de [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/)
y este proyecto sigue [Semantic Versioning](https://semver.org/lang/es/).

## [0.5.0] - 2026-08-14

### Added

- CLI (`cli/`): comando instalable `spring-doc` (`[project.scripts]`, tambien invocable como `python -m cli`) que orquesta `analyzer` -> `generators` -> `validator` mediante sus APIs publicas, sin reimplementar analisis, generacion ni validacion.
- Tres subcomandos: `spring-doc analyze <project>` (con `--openapi` para ademas generar y validar el OpenAPI, ejecutando Analyzer -> Generator -> Validator en una sola invocacion), `spring-doc generate <project>` (Analyzer -> Generator), `spring-doc validate <openapi-file>` (Validator, independiente).
- `cli/main.py`: parser `argparse` (stdlib, sin dependencias nuevas), `--version`, exit codes deterministas (`0` exito, `1` diagnostics que fallan el run, `2` error de uso, `3` error interno inesperado sin traceback).
- `cli/commands.py`: orquestacion y calculo de `status`/conteos por severidad; `--strict` hace que los `WARNING` tambien fallen el run (ademas de los `ERROR`, que siempre fallan); conteo de DTOs distintos (incluyendo anidados) derivado de la API publica existente, sin modificar `analyzer/models.py`.
- `cli/output.py`: dos formatos de salida independientes y explicitamente separados — `--format json|yaml` controla el **artefacto** OpenAPI generado; `--json` controla el **reporte** de la CLI sobre la operacion (conteos por severidad y, cuando aplica, la ruta del artefacto bajo `outputs`). El reporte `--json` nunca incluye el documento OpenAPI embebido. Combinar `--json` con generacion de OpenAPI sin `--output` es un error de uso (el reporte y el documento no pueden compartir stdout).
- `--quiet` suprime el resumen humano solo cuando el resultado es `ok` (un fallo causado por `--strict` sigue mostrando el detalle, para no ocultar por que fallo).
- `--output` crea directorios padres faltantes automaticamente; sigue siendo error de uso si el destino no es escribible (p. ej. apunta a un directorio existente).
- `cli/errors.py`: `CliUsageError`, unica excepcion propia de la CLI, distingue errores de entrada del usuario (exit 2) de errores internos inesperados (exit 3, capturados en el punto de entrada).
- 47 tests nuevos (260 -> 307): parser (help/version/comando desconocido/argumentos invalidos), cada comando, exit codes, `--strict`/`--quiet`/`--json`, separacion `--format`/`--json`, `--openapi`, escritura a archivo, integracion real contra `examples/customer-service`, determinismo, portabilidad de rutas (`pathlib`/`tmp_path`), y verificacion por grep de que `cli/` no importa modulos internos de Analyzer/Generator/Validator ni `javalang`.

### Changed

- `pyproject.toml`: version `0.4.0` -> `0.5.0`; se agrega `cli` a `tool.hatch.build.targets.wheel.packages` y `[project.scripts]` con el entry point `spring-doc`. Ninguna dependencia de runtime nueva (`argparse` es libreria estandar).
- `docs/12-Roadmap.md`, `docs/13-Versionado.md`, `docs/03-Arquitectura.md`, `README.md`: actualizados para reflejar la CLI implementada.

### Scope

- No se implemento ningun proveedor LLM, RAG, MCP, agentes, Confluence, CI/CD, Docker, API HTTP, Swagger UI, generacion de SDK/clientes/servidores, base de datos, interfaz grafica, autenticacion, cloud, Auditor avanzado, ni Drift Detection. Ver `docs/12-Roadmap.md`.
- `analyzer/`, `generators/` y `validator/` no se modificaron: los 260 tests previos a V0.5 no se modificaron y continuan pasando.
- **Reasignacion de version autorizada explicitamente:** el roadmap original asignaba V0.5 a "LLM Providers" y V0.6 a "CLI". La directriz real de V0.5 prioriza la CLI; "LLM Providers" se reprograma sin numero de version fijo (ver `docs/12-Roadmap.md`).

## [0.4.0] - 2026-08-13

### Added

- OpenAPI Quality Validator (`validator/`): analiza un documento OpenAPI 3.0.3 ya construido (`validate(document: dict) -> list[Diagnostic]`, más `validate_json`/`validate_yaml`), sin volver a analizar Java ni depender del Generator.
- `validator/openapi_rules.py`: catálogo de reglas por sección del documento (raíz, paths/métodos HTTP, `operationId` con detección de colisiones, parameters, requestBody, responses/status codes, schemas incluidos array/object/string/number/enum, `$ref` internos, components, security), clasificadas ERROR/WARNING/INFO reutilizando `analyzer.Diagnostic`/`DiagnosticSeverity`.
- `validator/openapi_validator.py`: orquestador con recorrido determinista explícito (paths/métodos/parameters/schemas siempre por clave ordenada, nunca por el orden de inserción del dict de entrada).
- `Evidence` reutilizado sin modificar `analyzer/models.py`: `Evidence.file` contiene un JSON Pointer (RFC 6901) que ubica el hallazgo dentro del documento (p. ej. `/paths/~1api~1customers/get/responses`).
- `$ref` externos (no `#/...`) detectados y declarados explícitamente (`OPENAPI_REF_EXTERNAL_SKIPPED`, INFO) en vez de ignorarse en silencio; nunca se resuelven ni se descargan.
- Heurísticas de detección de convenciones fijas del Generator V0.3 por comparación literal de texto (`OPENAPI_GENERATOR_DEFAULT_RESPONSE_DESCRIPTION`, `OPENAPI_GENERATOR_PLACEHOLDER_INFO`), documentadas explícitamente como específicas de este proyecto, no como inferencia general de OpenAPI.
- El Validator es de solo lectura: nunca modifica el documento recibido (verificado con tests de inmutabilidad).
- 111 tests nuevos (149 → 260) en 4 archivos, organizados por área (documento/paths/operationId, parameters/requestBody/responses, schemas/`$ref`/components/security, parseo JSON-YAML + integración + determinismo + inmutabilidad sobre `examples/customer-service`).

### Changed

- `pyproject.toml`: versión `0.3.0` → `0.4.0`; se agrega `validator` a `tool.hatch.build.targets.wheel.packages`. Ninguna dependencia de runtime nueva (se reutiliza `PyYAML`, ya presente desde V0.3).

### Scope

- No se implementó Swagger UI/Editor, un validador OpenAPI completo, resolución de `$ref` externos, validación exhaustiva de flujos OAuth2, rangos de status code (`2XX`/`3XX`), CLI, CI/CD, Docker, Confluence, ni ningún proveedor LLM. Ver `docs/12-Roadmap.md`.
- `analyzer/` y `generators/` no se modificaron: los 149 tests de V0.3 no se modificaron y continúan pasando.
- **Nota:** el roadmap original agrupaba "Validator + Auditor" en V0.4; la directriz real de V0.4 acotó el alcance únicamente al OpenAPI Quality Validator. El Auditor queda sin versión asignada, pendiente de una futura directriz. El paquete `validators/` (plural, placeholder desde V0.1) no es el paquete de V0.4 — la directriz nombró el paquete nuevo `validator/` (singular); `validators/` permanece intacto y sin uso.

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
