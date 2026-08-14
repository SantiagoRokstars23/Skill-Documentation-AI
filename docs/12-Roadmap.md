# 12 — Roadmap

Este roadmap refleja el orden incremental planeado para el proyecto. Cada version debe
completarse (criterios de aceptacion + Definition of Done) antes de iniciar la siguiente.

| Version | Nombre | Estado |
|---------|--------|--------|
| V0.1 | Foundation & Architecture | Completada (`v0.1.0`) |
| V0.2 | Spring Boot Analyzer (Advanced) | Completada (`v0.2.0`) |
| V0.3 | OpenAPI Generator | Completada (`v0.3.0`) |
| V0.4 | OpenAPI Quality Validator | Completada (`v0.4.0`) |
| V0.5 | CLI & Developer Experience | Completada (`v0.5.0`) |
| V0.6 | LLM Providers & AI Foundation | Completada (`v0.6.0`) |
| V0.7 | LLM Real Provider & AI Foundation | Completada (`v0.7.0`) |
| V0.8 | AI Documentation Foundation | Completada (`v0.8.0`) |
| V0.9 | Skill + End-to-End Documentation | **Completada / esta version** |
| V1.0 | Production | Futuro |
| V2.0 | Documentation Quality Gate | Futuro |
| V3.0 | Drift Detection | Futuro |
| — | Confluence Integration | Futuro, sin numero de version asignado (ver nota mas abajo) |

**Nota (V0.7):** el roadmap tenia asignado V0.7 a "Confluence Integration". La directriz real
recibida para V0.7 (`prompts/V0.7—LLM-REAL-PROVIDER-&-AI-FOUNDATION.md`) prioriza el primer
provider LLM real, confirmado explicitamente por el responsable del proyecto. "Confluence
Integration" se reprograma sin numero fijo, mismo patron ya usado con "LLM Providers" entre V0.5
y V0.6.

**Nota (V0.5):** el roadmap original asignaba V0.5 a "LLM Providers" y V0.6 a "CLI". La
directriz real recibida para V0.5 (`prompts/V0.5—CLI-&-DEVELOPER-EXPERIENCE.md`) prioriza la CLI,
confirmada explicitamente por el responsable del proyecto. "LLM Providers" se reprogramo sin
numero fijo momentaneamente; V0.6 lo retoma con directriz propia
(`prompts/V0.6—LLM-PROVIDERS-&-AI-FOUNDATION.md`), ocupando el hueco que quedo libre en la tabla
sin reabrir el conflicto de numeracion anterior.

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
- **V0.6 — LLM Providers & AI Foundation:** infraestructura desacoplada de proveedores LLM
  (`providers/config.py`, `providers/errors.py`, `providers/fake.py`, `providers/registry.py`),
  sin modificar el contrato existente de `LLMProvider` (V0.1). Unico provider concreto: un
  `FakeProvider` determinista para tests — ningun proveedor comercial real (decision explicita,
  ver `prompts/V0.6—LLM-PROVIDERS-&-AI-FOUNDATION.md`). Analyzer/Generator/Validator/CLI no se
  modificaron y siguen funcionando sin ninguna configuracion de LLM (verificado por tests de
  aislamiento). Se agrega ademas `skills/spring-doc/SKILL.md`: conocimiento LLM-agnostico y
  agente-agnostico para documentar un microservicio Spring Boot leyendo su codigo fuente
  directamente — independiente de `spring-doc` (la CLI), de `providers/`, y de cualquier
  proveedor LLM concreto; no describe la arquitectura interna del proyecto. Ver
  `docs/03-Arquitectura.md` y `docs/06-LLM.md`.
- **V0.7 — LLM Real Provider & AI Foundation:** primer provider LLM real, `AnthropicProvider`
  (`providers/anthropic.py`), implementado unicamente con stdlib (`urllib.request`/`urllib.error`/
  `json` — sin el SDK `anthropic`, cero dependencias nuevas). Reutiliza `ProviderConfig`/
  `get_provider`/`providers.errors` de V0.6 sin modificar el contrato de `LLMProvider`;
  `ProviderConfig` gana un campo aditivo (`timeout`). `FakeProvider` y el registry siguen
  funcionando igual que antes. Ninguna excepcion de `urllib` se propaga al consumidor: todo se
  traduce a `providers.errors`. Sin integracion con Analyzer/Generator/Validator/CLI/Skill (eso es
  V0.8). Ver `prompts/V0.7—LLM-REAL-PROVIDER-&-AI-FOUNDATION.md` y `docs/06-LLM.md`.
- **V0.8 — AI Documentation Foundation:** primera capa que conecta el motor determinista con un
  LLM real como consumidor: `ai/` (`DocumentationContextBuilder`, `DocumentationPromptBuilder`,
  `DocumentationEngine`, `DocumentationContext`/`DocumentationResult`). Estrategia de llamadas
  hibrida (una llamada de proyecto + una por endpoint, nunca una llamada global) para no requerir
  modificar `AnthropicProvider` (que fija `max_tokens=1024` de salida, V0.7). Depende
  exclusivamente de la abstraccion `providers.LLMProvider`; nunca de `AnthropicProvider`/
  `urllib`/ningun SDK. Regla de evidencia extendida al LLM: el contexto entregado es la unica
  fuente permitida, y el parser rechaza (`DocumentationParseError`) cualquier clave de
  `parameters`/`responses`/`dtos` que el LLM devuelva sin estar en el contexto (indicio de
  alucinacion), en vez de aceptarla. Sin integracion con Analyzer/Generator/Validator/CLI (no se
  modifico ninguno) ni con la Skill (sigue independiente). Sin comandos nuevos de CLI. Ver
  `prompts/V0.8—AI-DOCUMENTATION-FOUNDATION.md` y `docs/03-Arquitectura.md`. Evolucion conceptual
  futura (sin numero de version asignado todavia): AI Documentation Enhancement, integracion de
  la capa AI con la CLI, interoperabilidad Skill/Engine.
- **V0.9 — Skill + End-to-End Documentation:** conecta las piezas de V0.1-V0.8 en un flujo
  completo. `ai/enrichment.py::apply_documentation(document, documentation, context) -> (dict,
  list[str])` aplica un `DocumentationResult` sobre un OpenAPI ya generado, escribiendo
  exclusivamente en campos de texto libre (`summary`/`description`) -- nunca en paths, metodos,
  parametros estructurales, tipos, status codes ni `$ref`; cualquier desajuste se reporta como
  diagnostic, nunca como excepcion ni corrupcion silenciosa. `EndpointDocumentation` gana el
  campo `summary` junto al `description` ya existente desde V0.8. `skills/spring-doc/SKILL.md`
  se evoluciona (no se reemplaza): el modo por defecto (lectura directa de codigo, V0.6/V0.7)
  queda intacto, y se agrega una seccion nueva y claramente delimitada, "Optional: end-to-end
  orchestration using the spring-doc engine", que documenta el flujo de 9 pasos (inspeccion,
  analisis, generacion, validacion, contexto, enriquecimiento, integracion, validacion final,
  reporte) usando la CLI `spring-doc` y las abstracciones publicas del motor
  (`ProviderConfig`/`get_provider`) -- siempre en lenguaje neutral respecto al LLM/agente ("the
  agent", "an LLM provider"), sin mencionar ni depender de Claude Code/OpenCode/Codex/ChatGPT/
  Anthropic/Gemini/OpenAI en ningun momento. El motor sigue siendo util sin ningun LLM
  configurado (el contrato base de `spring-doc generate`/`validate` es ya documentacion completa
  y valida por si sola). Sin cambios en Analyzer/Generator/Validator/CLI/providers. Sin comandos
  de CLI nuevos. Ver `prompts/V0.9—SKILL-&-END-TO-END-DOCUMENTATION.md` y
  `docs/03-Arquitectura.md`.
- **Confluence Integration:** conexion de la salida OpenAPI con el proyecto Python existente que
  publica en Confluence. Sin numero de version asignado (ver nota de la tabla de arriba).
- **V1.0 — Production:** endurecimiento, empaquetado y estabilizacion para uso en produccion.
- **V2.0 — Documentation Quality Gate:** control de calidad de documentacion como gate en flujos
  de desarrollo.
- **V3.0 — Drift Detection:** deteccion automatica de divergencias entre codigo y documentacion.

Ninguna de las versiones futuras se implementa, ni parcialmente, dentro de V0.1 (Scope Lock,
`prompts/V0.1-foundation.md` seccion 19).
