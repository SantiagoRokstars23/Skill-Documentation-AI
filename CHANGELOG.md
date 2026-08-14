# Changelog

Todos los cambios relevantes de este proyecto se documentan en este archivo.

El formato sigue las convenciones de [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/)
y este proyecto sigue [Semantic Versioning](https://semver.org/lang/es/).

## [1.0.0] - 2026-08-14

### Added

- Seccion "API publica" en `README.md`: contrato estable de cada paquete derivado 1:1 de sus `__all__` reales (`analyzer`, `generators`, `validator`, `providers`, `ai`), mas la lista explicita de submodulos internos que no deben importarse directamente. Verificado programaticamente contra el codigo, cero discrepancias.
- Bloque de estado en `docs/04-Skill.md` que resuelve explicitamente la diferencia historica entre `skill/` (diseño conceptual de V0.1, nunca implementado como codigo ejecutable -- cero consumidores reales, verificado con `git grep` sobre todos los `.py` trackeados) y `skills/spring-doc/SKILL.md` (el artefacto que si funciona end-to-end desde V0.6).
- Decision explicita registrada en `docs/03-Arquitectura.md` sobre `validators/`: confirmado sin ninguna referencia real en el repositorio; se mantiene como paquete historico/reservado por la gobernanza ya establecida en `CLAUDE.md`, no se elimina sin autorizacion separada.

### Changed

- `pyproject.toml`: version `0.9.0` -> `1.0.0`. Ninguna dependencia nueva, runtime ni dev.
- `docs/12-Roadmap.md`: fila de V0.9 corregida (`Completada / esta version` -> `Completada (\`v0.9.0\`)`); V1.0 renombrada de "Production" a "Production Readiness"; bullet completo con el resultado de la auditoria de Fase 1.
- `docs/09-Auditoria.md`, `docs/11-Integracion.md`: corregidas referencias a versiones ya reasignadas (Auditor ya no "V0.4"; Confluence ya no "V0.7") -- desactualizadas desde hace 6 y 3 versiones respectivamente.
- `docs/02-Objetivos.md`: corregidas asignaciones de version obsoletas en "Objetivos futuros" (CLI listada como V0.6 -> V0.5; Confluence como V0.7 -> sin numero fijo; "implementacion completa de multiples proveedores LLM" nunca fue el objetivo perseguido, se corrigio la afirmacion ademas del numero).
- `README.md`: "Estado actual" actualizado de V0.9 a V1.0 (Production Readiness); resumen de Roadmap actualizado.
- `docs/13-Versionado.md`: nueva seccion "V0.9.0 -> V1.0.0" documentando la auditoria de Fase 1 (build/instalacion limpia/reproducibilidad verificados) y las correcciones documentales de Fase 3.

### Scope

- **Release de estabilizacion, no un ciclo de funcionalidades nuevas** (Scope Lock explicito de `prompts/V1.0—PRODUCTION-READINESS.md`). Cero cambios en `analyzer/`, `generators/`, `validator/`, `cli/`, `providers/`, `ai/` ni `skills/spring-doc/SKILL.md` -- verificado por `git diff --stat` (solo archivos `.md`/`pyproject.toml`/`CHANGELOG.md`) y por la suite completa, que permanece en 482 tests sin cambios.
- No se implemento CI/CD, nuevos providers, nuevos comandos de CLI, ni ninguna de las funcionalidades explicitamente excluidas por la seccion 23 de la directriz (RAG, embeddings, agentes, Confluence, Auditor, Drift Detection, Quality Gate, web UI, Docker, cloud, autenticacion, etc.).
- Auditoria de Fase 1 (solo inspeccion, sin modificar archivos) confirmo: `python -m build` produce sdist+wheel limpiamente; instalacion no editable desde el wheel, en un venv nuevo y un directorio ajeno al repositorio, ejecuta la CLI y el flujo completo `analyze --openapi -> validate` contra `examples/customer-service` sin errores; los artefactos de ejemplo son reproducibles (JSON exacto, YAML con el cuerpo exacto); no hay secretos reales en el repositorio; cada paquete ya declaraba `__all__` explicito.
- **No entraron en V1.0** (registrados como mejora futura, categoria D de la auditoria): empaquetar `skills/spring-doc/SKILL.md` como data file distribuible via `pip`; comando exacto reproducible en `examples/README.md`; tests de permisos de lectura para `analyze`/`generate` (asimetria con `validate`, que ya los tiene desde V0.6); verificacion de compatibilidad real contra Python 3.11; `classifiers`/`authors`/URL de repositorio en `pyproject.toml`; CI/CD.

## [0.9.0] - 2026-08-14

### Added

- `ai/enrichment.py`: `apply_documentation(document, documentation, context) -> (dict, list[str])`, mismo patron de firma que `generators.generate() -> (document, diagnostics)`. Aplica un `DocumentationResult` sobre un documento OpenAPI ya generado, escribiendo exclusivamente en campos de texto libre (`info.description`, `summary`/`description` de operacion, `description` de parametro, `description` de response -- solo si coincide con el placeholder fijo conocido del Generator --, `description` de schema). Nunca toca paths, metodos, parametros estructurales, tipos, status codes ni `$ref` -- garantia estructural, no solo de comportamiento, ya que los tipos de `ai/models.py` que recibe no tienen ningun campo capaz de representar esa informacion. Cualquier desajuste (`endpoint_id`/DTO/parametro que ya no existe) se reporta como diagnostic, nunca como excepcion. No muta el documento de entrada (`copy.deepcopy`). Reutiliza por convencion (sin importar `validator/`) el mismo texto de placeholder de respuesta que `validator/openapi_rules.py` ya detecta desde V0.4.
- `ai/models.py`: `EndpointDocumentation` gana el campo obligatorio `summary: str` (corto, siempre presente, distinto de `description`, que puede seguir vacia). `ai/prompts.py`/`ai/parsing.py` actualizados en consecuencia.
- `skills/spring-doc/SKILL.md` evolucionada (no reemplazada): el contenido original (V0.6/V0.7, LLM/agente/motor-agnostico) se mantiene intacto como modo por defecto. Se agrega, delimitada por el encabezado `## Optional: end-to-end orchestration using the spring-doc engine`, una seccion nueva y explicitamente opcional que documenta un flujo de 9 pasos usando la CLI `spring-doc` (`analyze`/`generate`/`validate`) y las abstracciones publicas del motor (`ProviderConfig`/`get_provider`), terminando en `apply_documentation`. Esta seccion nunca nombra un LLM/agente/proveedor concreto (Claude Code, OpenCode, Codex, ChatGPT, Anthropic, Gemini, OpenAI): usa siempre lenguaje neutral ("the agent", "an LLM provider"), y declara explicitamente que el motor y el LLM son mejoras opcionales, nunca requisitos.
- `tests/test_e2e_documentation.py`: integracion end-to-end completa (`analyze_project -> generate -> DocumentationContextBuilder -> DocumentationEngine -> apply_documentation -> validate`) contra `examples/customer-service`, con un doble de prueba local (no `FakeProvider`, para poder responder distinto a un prompt de proyecto que a uno de endpoint).
- 32 tests nuevos (450 -> 482): `ai/enrichment.py` (inmutabilidad, aplicacion y no-sobrescritura de cada campo de texto libre, `endpoint_id`/DTO desconocido como diagnostic no como excepcion, reemplazo de placeholder de response sin tocar texto real, reconciliacion del status `"unknown"` con la clave `"default"` del Generator, diagnostic explicito para un status ausente del documento, parametro `source="body"` sin corromper el documento, ausencia total de paths/operaciones agregados o eliminados, test de no invencion sobre los campos del dataclass, paso completo por `validator` sin nuevos errores, determinismo, resultado vacio sin diagnostics), integracion end-to-end (5 tests), y reescritura de `tests/test_skill_spring_doc.py` para el esquema de dos modos (division del archivo por el encabezado de la seccion opcional, verificacion de que la seccion opcional referencia la CLI/API publica, de que se declara explicitamente opcional con fallback documentado, y de que ninguno de los dos modos nombra un LLM/proveedor concreto).
- **Correccion en revision de codigo (Fase 5):** `ai/enrichment.py` buscaba la respuesta LLM-documentada por la clave literal `"unknown"` (`ai/parsing.py::status_label()`, V0.8, usada cuando no hay evidencia de `@ResponseStatus`), pero el documento OpenAPI real usa `"default"` para ese mismo caso (convencion del Generator, V0.3) -- la descripcion generada se perdia en silencio para la mayoria de los endpoints de un proyecto real (7/8 en `examples/customer-service`). Corregido con `_resolve_response_key()`, que reintenta con `"default"` cuando la clave literal es `UNKNOWN_STATUS_LABEL`; un status que sigue sin coincidir ahora se reporta como diagnostic en vez de perderse sin explicacion.

### Changed

- `pyproject.toml`: version `0.8.0` -> `0.9.0`. Ninguna dependencia de runtime ni dev nueva (`ai/enrichment.py` usa exclusivamente `copy`, libreria estandar).
- `docs/03-Arquitectura.md`, `docs/06-LLM.md`, `docs/12-Roadmap.md`, `docs/13-Versionado.md`, `README.md`: actualizados para reflejar `ai/enrichment.py` y la evolucion de doble modo de la Skill.

### Scope

- No se implemento RAG, embeddings, vector databases, agentes, multi-agente, MCP, tool/function calling, memoria conversacional, chat, historial, streaming, generacion de imagenes, fine-tuning, integracion con Confluence/Jira/GitHub, CI/CD, Docker, cloud, autenticacion, GUI, servidor HTTP, generacion de SDK. Ver `docs/12-Roadmap.md`.
- **Sin comandos de CLI nuevos**: `cli/` no se modifico; la orquestacion end-to-end descrita en la seccion opcional de la Skill es un proceso para que el agente ejecute paso a paso, no una nueva funcionalidad de la CLI existente.
- `analyzer/`, `generators/`, `validator/`, `cli/` y `providers/` no se modificaron. Verificado por tests de aislamiento existentes (`tests/test_ai_isolation.py`, cuya cobertura basada en `glob` cubre automaticamente `ai/enrichment.py` sin tests nuevos de aislamiento) y por grep manual (`ai/enrichment.py` solo importa `copy` y `.models`).
- La Skill conceptual (`skill/`, singular, V0.1) sigue sin relacion con `skills/spring-doc/` ni con `ai/`.

## [0.8.0] - 2026-08-14

### Added

- Paquete nuevo `ai/`: primera capa que conecta el motor determinista con un LLM real como consumidor (`AnalysisResult -> DocumentationContext -> prompt -> LLMProvider -> DocumentationResult`).
- `ai/models.py`: `DocumentationContext`/`DocumentationResult` y dataclasses anidadas (`ParameterContext`, `DTOFieldContext`, `DTOContext`, `ResponseContext`, `EndpointContext`, `ParameterDocumentation`, `ResponseDocumentation`, `DTODocumentation`, `EndpointDocumentation`), todas `frozen=True` con campos `tuple[...]`, mismo patron que `analyzer/models.py`.
- `ai/context.py`: `DocumentationContextBuilder.build(analysis_result, openapi_document=None)`. Recorrido determinista, DTOs deduplicados y ordenados alfabeticamente, colisiones de `endpoint_id` desambiguadas con sufijo numerico. `project_name` queda siempre en `None`: la unica fuente candidata (`openapi_document["info"]["title"]`) es la convencion fija del Generator ("Generated API", V0.3), no evidencia real.
- `ai/prompts.py`: `DocumentationPromptBuilder` (`build_project_prompt`/`build_endpoint_prompt`), `PROMPT_VERSION = "1.0"`, instrucciones anti-alucinacion centralizadas.
- `ai/parsing.py`: separa parseo/validacion (`parse_project_response`/`parse_endpoint_response`). Tolera un unico fence de markdown que envuelva la respuesta completa (regex anclada, nunca busca contenido embebido). Rechaza como posible alucinacion (`DocumentationParseError`) cualquier clave de `parameters`/`responses`/`dtos` que no este en el contexto entregado.
- `ai/errors.py`: `DocumentationError` (base) + `DocumentationParseError`. Un error de `providers.errors` nunca se envuelve ni se mezcla con estos.
- `ai/documentation.py`: `DocumentationEngine(provider, context_builder, prompt_builder)`, inyeccion por constructor. Estrategia de llamadas hibrida (una de proyecto + una por endpoint, nunca global) para no requerir modificar `AnthropicProvider` (que fija `max_tokens=1024` de salida, V0.7, no configurable). DTOs documentados dentro de la llamada del endpoint que los referencia, agregados deduplicados en el resultado final.
- 70 tests nuevos (380 -> 450): modelos, context builder (contra `examples/customer-service`, determinismo, ausencia de mutacion sobre `AnalysisResult`/documento OpenAPI, proyecto vacio, DTOs anidados, colision de id), prompt builder, parsing (JSON valido/invalido, fence tolerado/parcial no tolerado, claves no reconocidas, status `null`), `DocumentationEngine` (`FakeProvider` en el caso minimo, flujo completo con un doble de prueba local para casos con multiples respuestas distintas, agregacion de DTOs, error de provider propagado sin envolver, error de parseo, determinismo, inmutabilidad), integracion end-to-end con `examples/customer-service` y `FakeProvider`, aislamiento (verificado por introspeccion de `ast` sobre imports reales, no busqueda de texto, para evitar falsos positivos con los propios docstrings de `ai/`), y una regresion de revision de codigo sobre DTOs anidados (ver mas abajo).
- **Correccion en revision de codigo (Fase 5):** `ai/prompts.py`/`ai/parsing.py` solo resolvian los DTOs referenciados directamente por un endpoint, no los DTOs anidados dentro de esos DTOs (p. ej. `Address` dentro de `CustomerRequest`), aunque `DocumentationContextBuilder` ya los recolectaba recursivamente en `DocumentationContext.dtos`. Un DTO anidado nunca llegaba al prompt, y si el LLM lo describia igual, el parser lo rechazaba como alucinacion. Corregido con `DTOFieldContext.nested_dto_name` (campo aditivo) y `DocumentationContext.referenced_dto_names()` (resolucion transitiva con proteccion contra ciclos) como fuente unica de verdad compartida entre `ai/prompts.py` y `ai/parsing.py`.

### Changed

- `pyproject.toml`: version `0.7.0` -> `0.8.0`; se agrega `ai` a `tool.hatch.build.targets.wheel.packages`. Ninguna dependencia de runtime ni dev nueva.
- `docs/03-Arquitectura.md`, `docs/06-LLM.md`, `docs/12-Roadmap.md`, `docs/13-Versionado.md`, `README.md`: actualizados para reflejar la capa `ai/`.

### Scope

- No se implemento RAG, embeddings, vector databases, agentes, multi-agente, MCP, tool/function calling, memoria conversacional, chat, historial, streaming, generacion de imagenes, analisis semantico avanzado, fine-tuning, entrenamiento de modelos, integracion con Confluence/Jira/GitHub, CI/CD, Docker, cloud, autenticacion, GUI, servidor HTTP, generacion de SDK, ni soporte para proveedores adicionales. Ver `docs/12-Roadmap.md`.
- **Sin integracion con ningun consumidor real**: `analyzer/`, `generators/`, `validator/` y `cli/` no se modificaron y no importan `ai/`; la Skill (`skill/`, `skills/spring-doc/SKILL.md`) sigue completamente independiente. La CLI no gana comandos nuevos (`spring-doc ai`/`chat`/`ask`/`document` no existen).
- `AnthropicProvider` no se modifico (decision explicita de Fase 2 para resolver la limitacion de `max_tokens` sin tocarlo).

## [0.7.0] - 2026-08-14

### Added

- `providers/anthropic.py`: `AnthropicProvider`, primer provider LLM real del proyecto, implementando `LLMProvider.generate(prompt: str) -> str` sin cambios de contrato. Contra el endpoint de Mensajes de Anthropic (`POST https://api.anthropic.com/v1/messages`), unicamente con `urllib.request`/`urllib.error`/`json` de la libreria estandar — sin el SDK `anthropic`, cero dependencias nuevas.
- Requiere `api_key` y `model` explicitos en `ProviderConfig`, validados en la construccion (falla antes de cualquier llamada de red): `MissingCredentialError`/`InvalidModelError`. Sin modelo por defecto hardcodeado (decision explicita de Fase 2).
- `ProviderConfig` gana un campo aditivo, `timeout: float | None = None`, leible desde `SPRING_DOC_LLM_TIMEOUT` (parseo tolerante: valor ausente/invalido queda en `None`, nunca lanza). `AnthropicProvider` aplica un default seguro (60s) cuando no hay uno configurado o no es positivo.
- Toda excepcion de `urllib` (`TimeoutError`, `HTTPError`, `URLError`) y toda respuesta malformada (JSON invalido, sin bloques de texto) se traduce a `providers.errors` (`ProviderTimeoutError`, `ProviderRequestError`, `InvalidResponseError`) — el consumidor nunca ve una excepcion de `urllib` ni del formato de respuesta de Anthropic.
- `providers/registry.py`: nueva entrada `"anthropic"`. `"fake"` sigue resolviendo a `FakeProvider` exactamente igual que en V0.6.
- 28 tests nuevos (352 -> 380): `AnthropicProvider` (construccion, credencial/modelo ausente, request/headers/payload, respuesta valida/sin contenido/JSON invalido, timeout de lectura y de conexion, HTTP 4xx/5xx, error de conexion, credencial nunca expuesta, registry resuelve `"anthropic"`, `FakeProvider` sigue funcionando, timeout configurado/default/no positivo), `ProviderConfig.timeout`, y aislamiento ampliado (`skill/`/`skills/` tampoco importan `providers`, importar `providers/` no dispara `urlopen`). Ningun test hace una llamada de red real.
- **Correccion en revision pre-commit:** un timeout durante la fase de conexion/envio de la request (a diferencia de uno durante la lectura de la respuesta) llega envuelto por `urllib` como `URLError(reason=TimeoutError(...))`, no como `TimeoutError` directo — el `except TimeoutError` no lo capturaba, y se clasificaba incorrectamente como `ProviderRequestError` en vez de `ProviderTimeoutError`. Corregido en `providers/anthropic.py` inspeccionando `exc.reason` dentro del handler de `URLError`, con test de regresion dedicado.

### Changed

- `pyproject.toml`: version `0.6.0` -> `0.7.0`. Ninguna dependencia de runtime ni dev nueva.
- `providers/__init__.py`, `providers/base.py`: docstrings actualizados; `AnthropicProvider` exportado.
- `docs/12-Roadmap.md`, `docs/13-Versionado.md`, `docs/03-Arquitectura.md`, `docs/06-LLM.md`, `README.md`: actualizados para reflejar el primer provider LLM real.

### Scope

- No se implemento RAG, embeddings, vector databases, agentes, MCP, tool calling, memoria, chat, Confluence, Jira, GitHub, CI/CD, generacion automatica de documentacion mediante LLM, GUI, entrenamiento/fine-tuning de modelos. Ver `docs/12-Roadmap.md`.
- **Sin integracion del LLM con ningun consumidor real**: `analyzer/`, `generators/`, `validator/`, `cli/`, `skill/` y `skills/` no se modificaron y siguen sin importar `providers/` (verificado por grep y por tests de aislamiento ampliados). La CLI no gana comandos nuevos (`spring-doc ai`/`chat`/`ask`/`document` no existen) ni cambia el comportamiento de `analyze`/`generate`/`validate`. Esa integracion pertenece a V0.8.
- Un solo provider real (Anthropic) — no se implementaron multiples proveedores comerciales solo para demostrar compatibilidad.
- **Reasignacion de version autorizada explicitamente:** el roadmap tenia asignado V0.7 a "Confluence Integration". La directriz real de V0.7 prioriza el primer provider LLM real; "Confluence Integration" se reprograma sin numero de version fijo (ver `docs/12-Roadmap.md`).

## [0.6.0] - 2026-08-14

### Added

- Infraestructura de LLM Providers (`providers/`), alrededor de la interfaz `LLMProvider` existente desde V0.1 (`providers/base.py`, sin cambios de contrato: `generate(self, prompt: str) -> str`).
- `providers/config.py`: `ProviderConfig` (dataclass inmutable: `provider`, `model`, `api_key`), con `from_env()` leyendo `SPRING_DOC_LLM_PROVIDER`/`_MODEL`/`_API_KEY`. `api_key` se excluye de `repr()`/`str()` para que nunca aparezca en logs por accidente.
- `providers/errors.py`: jerarquia propia de excepciones (`LLMProviderError` + `ProviderNotConfiguredError`, `UnknownProviderError`, `MissingCredentialError`, `InvalidModelError`, `ProviderTimeoutError`, `ProviderRequestError`, `InvalidResponseError`), para que ningun consumidor futuro necesite conocer excepciones de un SDK concreto.
- `providers/fake.py`: `FakeProvider`, unica implementacion concreta de `LLMProvider` en V0.6 — determinista, sin red, sin credenciales, pensada para tests.
- `providers/registry.py`: `get_provider(config) -> LLMProvider`, seleccion por nombre sobre un `dict[str, Callable]` (no una clase Factory ni un sistema de plugins — patron minimo justificado en Fase 2).
- `skills/spring-doc/SKILL.md` (autorizado explicitamente junto con la Fase 3, ademas del alcance original de la directriz): conocimiento/proceso LLM-agnostico, agente-agnostico y motor-agnostico para documentar el API HTTP de un microservicio Java/Spring Boot leyendo su codigo fuente directamente (que buscar en controllers/mappings/parametros/DTOs/respuestas/seguridad, como tratar ambiguedad e informacion faltante sin inventar, como estructurar el resultado). No depende de `spring-doc` (la CLI), no la requiere, y no describe la arquitectura interna de este proyecto (`providers/`, `analyzer/`, `generators/`, `validator/`, `cli/`); puede mencionar `spring-doc` una vez, de forma generica, como herramienta externa opcional, nunca como requisito. Pensado para copiarse solo y entregarse, junto con un proyecto Spring Boot, a cualquier LLM. **Correccion de alcance:** la primera implementacion documentaba como invocar la CLI `spring-doc`; se reescribio por completo a pedido explicito del responsable del proyecto para eliminar esa dependencia.
- `skills/spring-doc/SKILL.md` ampliado con cobertura explicita de completitud OpenAPI (regla de evidencia sin cambios, solo mas exhaustiva sobre que capturar): trazado de respuestas de error a partir de excepciones lanzadas por el codigo (metodo + llamadas a metodos privados/protegidos y colaboradores inyectados, mas el fallback generico de un manejador global si existe) en vez de documentar solo la respuesta de exito; `tags`/`summary` obligatorios y `description` cuando la operacion tiene logica real; descripcion y ejemplo por cada campo de DTO tanto en request como en response; distincion explicita entre campos "codigo de catalogo" de valores fijos (documentables directamente) y de valores dinamicos/externos (nunca hardcodear, documentar donde consultarlos); verificacion de que un requisito de seguridad este realmente activo en el codigo antes de documentarlo como tal; mencion de URLs reales por ambiente a nivel de proyecto si el codigo las declara. Sigue sin depender de `spring-doc` ni describir la arquitectura interna del proyecto.
- 44 tests nuevos (308 -> 352): `ProviderConfig` (construccion, `from_env`, inmutabilidad, `api_key` nunca en `repr`/`str`), jerarquia de errores, `FakeProvider` (determinismo, contrato), registro (resolucion por nombre, provider desconocido, sin configurar), aislamiento (Analyzer/Generator/Validator/CLI funcionan sin ninguna variable `SPRING_DOC_LLM_*`, y ninguno de esos paquetes importa `providers`), validaciones sobre `skills/spring-doc/SKILL.md` (frontmatter valido, no referencia la arquitectura interna del proyecto ni sintaxis de la CLI, no se dirige a un agente/proveedor concreto, menciones de `spring-doc` -si las hay- quedan enmarcadas como opcionales, ensena los principios de evidencia esperados y la cobertura de completitud OpenAPI descrita arriba, es autocontenido), y una regresion en `cli/commands.py::run_validate` (ver mas abajo).

### Changed

- `pyproject.toml`: version `0.5.0` -> `0.6.0`. Ninguna dependencia de runtime ni dev nueva (toda la infraestructura usa exclusivamente la libreria estandar).
- `providers/__init__.py`, `providers/base.py`: docstrings actualizados; API publica del paquete ampliada con `ProviderConfig`, `get_provider`, `FakeProvider` y la jerarquia de `providers.errors`.
- `docs/12-Roadmap.md`, `docs/13-Versionado.md`, `docs/03-Arquitectura.md`, `docs/06-LLM.md`, `README.md`: actualizados para reflejar la infraestructura de providers y `skills/spring-doc/SKILL.md`.

### Scope

- No se implemento RAG, embeddings, vector databases, agentes, MCP, tool calling avanzado, memoria, aprendizaje, fine-tuning, chat UI, generacion inteligente de documentacion, analisis semantico via LLM, explicacion automatica de diagnostics, Auditor avanzado, Drift Detection, Confluence, Jira, GitHub integration, CI/CD, Docker, ni cloud deployment. Ver `docs/12-Roadmap.md`.
- **No se implemento ningun provider comercial real** (Anthropic, OpenAI, Gemini, etc.): se evaluo explicitamente un `AnthropicProvider` via `urllib` (stdlib, sin SDK, costo en dependencias nulo) en Fase 2, y se descarto por decision explicita del responsable del proyecto, priorizando la superficie minima. Solo `FakeProvider` existe.
- `analyzer/`, `generators/` y `validator/` no se modificaron. `cli/` recibio una unica excepcion puntual autorizada explicitamente: `cli/commands.py::run_validate` no protegia la lectura del archivo (`path.read_text` sin capturar `OSError`/`UnicodeDecodeError`), a diferencia de `write_output_file`; un archivo no-UTF-8 o sin permisos de lectura producia exit code 3 ("error interno") en vez de 2 ("error de uso"). Corregido con el mismo patron ya usado en `write_output_file`, mas un test de regresion — ningun otro comportamiento de la CLI cambio. Los 308 tests previos a V0.6 no se modificaron y continuan pasando. Verificado por grep y por `tests/test_providers_isolation.py` que `cli/` (y los demas tres paquetes) no importan `providers`.
- **Nota de nomenclatura:** `skills/spring-doc/` (plural, nuevo en V0.6) no debe confundirse con `skill/` (singular, desde V0.1) — son artefactos distintos sin relacion entre si. Ver `docs/03-Arquitectura.md`.

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
- 48 tests nuevos (260 -> 308): parser (help/version/comando desconocido/argumentos invalidos), cada comando, exit codes, `--strict`/`--quiet`/`--json`, separacion `--format`/`--json`, `--openapi`, escritura a archivo, integracion real contra `examples/customer-service`, determinismo, portabilidad de rutas (`pathlib`/`tmp_path`), verificacion por grep de que `cli/` no importa modulos internos de Analyzer/Generator/Validator ni `javalang`, y una regresion encontrada en revision pre-commit (`_symbol()` evaluaba siempre la codificacion de `sys.stdout` aunque el banner fuera a stderr).

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
