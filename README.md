# Skill-Documentation-AI

Motor de documentacion inteligente para microservicios Java/Spring Boot. Analiza codigo fuente,
extrae evidencia estructurada de su API, y genera una especificacion **OpenAPI 3.0.3**. En fases
futuras utilizara ademas una Skill especializada junto con un LLM intercambiable para completar,
actualizar y auditar esa documentacion.

## Problema

La documentacion de APIs suele quedar incompleta, desactualizada respecto al codigo e
inconsistente entre microservicios, lo que genera un trabajo manual elevado y dificulta mantener
documentacion empresarial consistente. Ver `docs/01-Modelo.md`.

## Objetivo

Reducir ese problema mediante automatizacion, analisis estatico deterministico del codigo, y
capacidades de LLM controladas por una Skill especializada, manteniendo el sistema independiente
de cualquier proveedor de LLM concreto. Ver `docs/02-Objetivos.md`.

## Estado actual — V1.0 (Production Readiness)

**Funcional y estable: el Analyzer, el OpenAPI Generator, el OpenAPI Quality Validator, la CLI
(`spring-doc`), la infraestructura de LLM Providers** (configuracion, errores, seleccion por
nombre, `FakeProvider` determinista, `AnthropicProvider` real via stdlib sin SDK), **la capa AI**
(`ai/`: `DocumentationContextBuilder` + `DocumentationPromptBuilder` + `DocumentationEngine` +
`ai/enrichment.py::apply_documentation`, que aplica documentacion generada por un LLM sobre un
documento OpenAPI ya construido) **y la Skill de documentacion** (`skills/spring-doc/SKILL.md`,
con un modo por defecto LLM/agente/motor-agnostico mas una seccion opcional que describe la
orquestacion end-to-end del motor `spring-doc`). V1.0 es un release de estabilizacion (sin cambios
funcionales en ningun paquete respecto a V0.9): verifico empaquetado (`python -m build` produce
sdist+wheel), instalacion limpia real (venv nuevo, wheel no editable, ejecutado fuera del
repositorio) y reproducibilidad del ejemplo incluido; ademas documento explicitamente la API
publica (ver mas abajo) y resolvio deuda documental heredada (ver `docs/13-Versionado.md` seccion
"V0.9.0 -> V1.0.0"). **Sin comandos de CLI nuevos, sin nuevos providers, sin CI/CD.** El Auditor y
las integraciones (Confluence) permanecen definidos y documentados, pero no implementados. Ver
`docs/12-Roadmap.md`.

Funcionalidad disponible hoy:

- Analisis estatico de un proyecto Java/Spring Boot mediante un **motor hibrido**: un parser AST
  (`javalang`) como motor principal, con el motor de V0.1 (regex + balance de brackets) como
  *fallback* automatico por archivo cuando el AST no puede parsear un archivo especifico (sintaxis
  no soportada o codigo malformado). Ver `docs/07-Analisis.md`.
- Deteccion de `@RestController`/`@Controller`, mappings HTTP (`@GetMapping`, `@PostMapping`,
  `@PutMapping`, `@DeleteMapping`, `@PatchMapping`, `@RequestMapping` — incluyendo multiples
  metodos HTTP y anotaciones fully-qualified), paths, `@PathVariable`, `@RequestParam`,
  `@RequestBody`, `@RequestHeader`.
- Resolucion de **DTOs** referenciados entre archivos del proyecto (campos, tipos, colecciones,
  DTOs anidados, enums) y de anotaciones de **Bean Validation** (`@NotBlank`, `@Size`, `@Email`,
  etc.) sobre campos y parametros.
- Analisis de **respuesta** (`ResponseEntity<T>`, colecciones, `@ResponseStatus`), de
  `consumes`/`produces`, y evidencia de **seguridad** (`@PreAuthorize`, `@Secured`).
- **Generacion de una especificacion OpenAPI 3.0.3** (`generators.generate`) a partir de la
  metadata del Analyzer: paths, operations, parameters, requestBody, responses, `components.schemas`
  con `$ref` reutilizado, mapeo de Bean Validation, `operationId` deterministico, y politicas
  conservadoras documentadas cuando falta evidencia (nunca `200 application/json` por defecto). Ver
  `docs/05-OpenAPI.md`.
- Serializacion a JSON (libreria estandar) y YAML (`PyYAML`).
- **Validacion de calidad del documento OpenAPI generado** (`validator.validate`): reglas
  estructurales (paths, metodos HTTP, `operationId` unico, parameters, requestBody, responses,
  schemas, `$ref` internos, components, security) clasificadas en ERROR/WARNING/INFO, mas
  deteccion de senales de calidad (descripciones ausentes, seguridad documentada solo como
  extension, schemas no referenciados). El Validator es de solo lectura y no vuelve a analizar
  Java. Ver `docs/05-OpenAPI.md`.
- Ni el Analyzer, ni el Generator, ni el Validator inventan informacion: cuando un dato no puede
  determinarse con confianza (p. ej. un nombre de DTO ambiguo, un endpoint sin evidencia de
  codigo de respuesta, un `$ref` que no resuelve), se registra un `Diagnostic` en vez de
  suponerse (ver `docs/09-Auditoria.md`).
- **CLI (`spring-doc`)** que orquesta los tres componentes anteriores: `analyze`, `generate`,
  `validate`, con salida humana o `--json` (reporte estructurado, independiente del `--format`
  del artefacto OpenAPI), `--strict`, `--quiet`, exit codes deterministas, y manejo diferenciado
  de errores de usuario vs. errores internos. Ver "Uso de la CLI" mas abajo.

## Arquitectura (resumen)

```text
Microservicio Spring Boot -> Analyzer -> Evidence/Metadata -> Skill -> LLM Provider
    -> OpenAPI Generator -> Validator -> Auditor -> OpenAPI
```

El proyecto implementa `Microservicio Spring Boot -> Analyzer -> Evidence/Metadata`,
`Evidence/Metadata -> OpenAPI Generator -> OpenAPI`, `OpenAPI -> Validator -> Diagnostics`, y,
desde V0.9, `Evidence/Metadata -> ai/ (LLM Provider) -> apply_documentation -> OpenAPI enriquecido`
como flujo adicional disponible programaticamente o via la seccion opcional de
`skills/spring-doc/SKILL.md` (la transformacion base a OpenAPI, sin embargo, sigue sin pasar por
la Skill conceptual de `docs/04-Skill.md`; el Auditor tampoco esta implementado). Detalle completo
en `docs/03-Arquitectura.md`.

## Stack

- **Lenguaje:** Python >= 3.11.
- **Dependencias de runtime:** `javalang` (parser AST de Java, motor principal del Analyzer desde
  V0.2) y `PyYAML` (serializacion YAML del OpenAPI Generator y parseo YAML del Validator, desde
  V0.3) — ver decisiones documentadas en `docs/03-Arquitectura.md`.
- **Dependencias de desarrollo:** `pytest` para testing.

## Estructura del proyecto

```text
Skill-Documentation-AI/
├── README.md
├── CLAUDE.md
├── LICENSE
├── CHANGELOG.md
├── pyproject.toml
├── docs/            Documentacion (arquitectura, skill, OpenAPI, LLM, analisis, seguridad, ...)
├── prompts/         Directrices de cada version del proyecto
├── skill/           Skill de documentacion (SKILL.md, rules/, references/, templates/) -- V0.1,
│                    componente conceptual del producto, no confundir con skills/ (ver abajo)
├── skills/spring-doc/  SKILL.md (V0.6, evolucionada V0.9): modo por defecto -- documentar un
│                    microservicio Spring Boot leyendo su codigo fuente, LLM/agente-agnostico --
│                    mas una seccion opcional de orquestacion end-to-end del motor spring-doc
├── providers/       LLM Provider: interfaz (V0.1) + config/errores/registry/FakeProvider (V0.6)
│                    + AnthropicProvider real via stdlib, sin SDK (V0.7)
├── analyzer/        Analyzer funcional para Java/Spring Boot (motor AST + fallback regex)
├── validators/       Placeholder sin uso (ver nota de nomenclatura en docs/03-Arquitectura.md)
├── generators/       OpenAPI Generator funcional (AnalysisResult -> OpenAPI 3.0.3)
├── validator/        OpenAPI Quality Validator funcional (documento OpenAPI -> Diagnostics)
├── cli/             CLI funcional (`spring-doc`): analyze / generate / validate
├── ai/              Capa AI: DocumentationContextBuilder / PromptBuilder / Engine (V0.8) --
│                    primer consumidor real de providers.LLMProvider -- + enrichment.py (V0.9):
│                    aplica la documentacion generada sobre un OpenAPI ya construido
├── tests/           Tests del Analyzer, del Generator, del Validator, de la CLI, de providers/ y de ai/
└── examples/        Microservicio Spring Boot de ejemplo (+ openapi.yaml/openapi.json generados)
```

## Instalacion

### Requisitos

- **Python 3.11 o superior** (`requires-python = ">=3.11"` en `pyproject.toml`; no se afirma
  soporte para versiones anteriores).
- **pip.**
- Para construir el paquete (wheel/sdist): el paquete `build` (`python -m pip install build`).

### Nombres: que es que

Estos cuatro nombres **no son el mismo string** y conviene distinguirlos antes de instalar nada:

| Concepto | Valor real |
|---|---|
| Repositorio / carpeta del proyecto | `Skill-Documentation-AI` |
| Nombre de distribucion Python (`pyproject.toml` -> `[project].name`, lo que muestra `pip show`) | `skill-documentation-ai` |
| Nombre de archivo del **wheel** generado (con guiones bajos -- normalizacion automatica de `pip`/`build`, no un nombre distinto a recordar) | `skill_documentation_ai-<version>-py3-none-any.whl` |
| Nombre de archivo del **sdist** generado | `skill_documentation_ai-<version>.tar.gz` |
| Comando de CLI instalado (`[project.scripts]`) | `spring-doc` |

El nombre del wheel/sdist **no** es `spring_doc-...`: el paquete distribuible se llama
`skill-documentation-ai` (asi lo confirma `pyproject.toml` y asi lo reporta `pip show`); `spring-doc`
es unicamente el nombre del comando que queda disponible despues de instalar. El sufijo de version
en el nombre del archivo cambia en cada release -- no asumir que sera siempre `1.0.0`.

### Instalacion para desarrollo (editable)

Para modificar el codigo del proyecto:

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

# opcional, no obligatorio para que la instalacion funcione:
python -m pip install --upgrade pip

python -m pip install -e ".[dev]"
```

Esto deja disponible el comando `spring-doc` apuntando directamente al codigo fuente del
repositorio (cualquier cambio en `analyzer/`/`generators/`/etc. se refleja sin reinstalar).

### Construir e instalar desde una distribucion (wheel/sdist)

Este es el camino que reproduce como instalaria el paquete alguien externo al repositorio (no
requiere `-e`, ni mantener el repositorio clonado despues de instalar):

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

python -m pip install build
python -m build
```

Esto genera los artefactos dentro de `dist/`, por ejemplo (V1.0.0):

```text
dist/
├── skill_documentation_ai-1.0.0-py3-none-any.whl
└── skill_documentation_ai-1.0.0.tar.gz
```

Estos nombres cambian con la version -- verificar siempre el contenido real de `dist/` antes de
instalar:

```bash
# Windows
dir dist
# Linux/macOS
ls dist
```

Instalar el wheel real (sustituir `<wheel-generado>` por el archivo que aparecio en `dist/`):

```bash
python -m pip install dist/<wheel-generado>.whl
```

Ejemplo real para V1.0.0 (Windows, con `\` en la ruta):

```cmd
python -m pip install dist\skill_documentation_ai-1.0.0-py3-none-any.whl
```

Se usa `python -m pip install ...` (no `pip install ...` a secas) para asegurar que el `pip` que
se ejecuta pertenece al interprete/entorno virtual activo, no a otro Python del sistema.

**Desarrollo vs. instalacion desde distribucion:**

```text
python -m pip install -e .          python -m build
        |                                   |
        v                                   v
  desarrollo local              dist/<wheel>.whl + dist/<sdist>.tar.gz
                                             |
                                             v
                              python -m pip install dist/<wheel>.whl
                                             |
                                             v
                        prueba tal como lo instalaria un usuario externo
```

### Quick start desde un clone limpio

```bash
git clone https://github.com/SantiagoRokstars23/Skill-Documentation-AI.git
cd Skill-Documentation-AI

python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

python -m pip install build
python -m build

# Windows
dir dist
# Linux/macOS
ls dist

python -m pip install dist/<wheel-generado>.whl

spring-doc --version
spring-doc --help
```

### Verificacion

```bash
spring-doc --version
spring-doc --help
```

Salida esperada (Example output for V1.0.0; en versiones futuras el numero cambia):

```text
spring-doc 1.0.0
```

### Solucion de problemas comunes

**`dist\...whl` no existe / "looks like a filename, but the file does not exist":**

```text
WARNING: Requirement 'dist\....whl' looks like a filename,
but the file does not exist
```

Mismo mensaje para dos causas distintas (verificado): `dist/` todavia no existe porque el paquete
no fue construido, **o** el nombre de archivo escrito no coincide con el que realmente generó
`python -m build`. Solucion en ambos casos:

```bash
python -m build
# Windows
dir dist
# Linux/macOS
ls dist
```

... y usar exactamente el nombre de archivo que aparece ahi.

**`No module named build`:**

```bash
python -m pip install build
python -m build
```

**`spring-doc` no se reconoce como comando** (Windows: mensaje similar a `'spring-doc' is not
recognized as an internal or external command`; Linux/macOS: `spring-doc: command not found`):
casi siempre significa que el entorno virtual donde se instalo no esta activo. Verificar:

```bash
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate

python -m pip show skill-documentation-ai
```

Si `pip show` no encuentra el paquete, la instalacion no se completo correctamente en ese entorno
-- repetir el paso de `python -m pip install ...` (editable o desde wheel, segun corresponda).

**Se instalo una version distinta a la esperada:**

```bash
spring-doc --version
python -m pip show skill-documentation-ai
```

`pip show` reporta la version realmente instalada en el entorno activo; si no coincide con el
`dist/*.whl` que se intento instalar, confirmar que el entorno virtual activo es el correcto.

## Uso de la CLI

Tras instalar el paquete (ver "Instalacion"), queda disponible el comando `spring-doc` (tambien
invocable como `python -m cli`).

```bash
# Analiza un proyecto Spring Boot (resumen humano).
spring-doc analyze ./mi-servicio

# Analiza y ademas genera+valida el OpenAPI (Analyzer -> Generator -> Validator).
spring-doc analyze ./mi-servicio --openapi --format yaml --output openapi.yaml

# Genera el OpenAPI directamente (a stdout, o a un archivo con --output).
spring-doc generate ./mi-servicio --format yaml
spring-doc generate ./mi-servicio --format json --output openapi.json

# Valida un documento OpenAPI ya existente.
spring-doc validate openapi.yaml

# Reporte estructurado para automatizacion (nunca incluye el documento OpenAPI,
# solo conteos y, si aplica, la ruta donde se escribio):
spring-doc analyze ./mi-servicio --json

# Los warnings tambien fallan el proceso (exit code 1):
spring-doc validate openapi.yaml --strict

# Version del paquete instalado:
spring-doc --version
```

`--format` controla el formato del **artefacto** OpenAPI (`json`/`yaml`); `--json` controla el
formato del **reporte** de la CLI sobre la operacion — son opciones independientes, nunca la
misma cosa. Exit codes: `0` exito, `1` diagnostics que fallan el run (`ERROR` siempre, `WARNING`
solo bajo `--strict`), `2` error de uso (proyecto/archivo inexistente, ruta de salida invalida,
opcion desconocida), `3` error interno inesperado. Detalle completo de opciones, formas exactas
del reporte `--json` y decisiones de diseno en `docs/03-Arquitectura.md` (decision 10) y
`docs/13-Versionado.md`.

## Uso como libreria

El Analyzer, el Generator y el Validator tambien se pueden usar directamente como libreria
Python (la CLI es una capa de orquestacion sobre las mismas APIs, sin logica propia):

```python
from analyzer import analyze_project
from generators import generate, to_yaml, to_json
from validator import validate

result = analyze_project("examples/customer-service")

for endpoint in result.endpoints:
    print(endpoint.method, endpoint.endpoint, "->", endpoint.controller)

print(result.to_json())

document, diagnostics = generate(result)
print(to_yaml(document))
for diagnostic in diagnostics:
    print(diagnostic.severity.value, diagnostic.code, diagnostic.message)

for diagnostic in validate(document):
    print(diagnostic.severity.value, diagnostic.code, diagnostic.message)
```

### API publica (V1.0)

El contrato estable de cada paquete es exactamente lo que declara en su `__all__` de nivel
superior -- nada mas. Import recomendado: siempre desde el paquete, nunca desde un submodulo
interno.

| Paquete | Import publico (`__all__`) |
|---|---|
| `analyzer` | `analyze_project`, `analyze_file`, `discover_java_files`, `AnalysisResult`, `Controller`, `Endpoint`, `Parameter`, `ParameterSource`, `HttpMethod`, `DTO`, `Field`, `Response`, `Validation`, `Diagnostic`, `DiagnosticSeverity`, `Evidence` |
| `generators` | `generate`, `to_json`, `to_yaml`, `OPENAPI_VERSION` |
| `validator` | `validate`, `validate_json`, `validate_yaml` |
| `providers` | `LLMProvider`, `ProviderConfig`, `get_provider`, `FakeProvider`, `AnthropicProvider`, `LLMProviderError` y sus 6 subclases (`ProviderNotConfiguredError`, `UnknownProviderError`, `MissingCredentialError`, `InvalidModelError`, `ProviderTimeoutError`, `ProviderRequestError`, `InvalidResponseError`) |
| `ai` | `DocumentationContextBuilder`, `DocumentationPromptBuilder`, `DocumentationEngine`, `apply_documentation`, `DocumentationContext`, `DocumentationResult` y sus dataclasses (`EndpointContext`, `ParameterContext`, `DTOContext`, `DTOFieldContext`, `ResponseContext`, `EndpointDocumentation`, `ParameterDocumentation`, `DTODocumentation`, `ResponseDocumentation`), `DocumentationError`, `DocumentationParseError`, `PROMPT_VERSION` |
| `cli` | uso previsto via el entry point instalado `spring-doc` (o `python -m cli`), no como libreria importable |

**Internos, no importar directamente** (pueden cambiar sin aviso, incluso dentro de la misma
version): `analyzer.ast_analyzer`, `analyzer.ast_backend`, `analyzer.dto_analyzer`,
`analyzer.spring_boot_analyzer`, `analyzer.scanner`; `generators.openapi_types`,
`generators.openapi_schemas`, `generators.openapi_generator`; `validator.openapi_rules`,
`validator.openapi_validator`; `providers.base`, `providers.config`, `providers.errors`,
`providers.fake`, `providers.anthropic`, `providers.registry`; `ai.models`, `ai.context`,
`ai.prompts`, `ai.parsing`, `ai.errors`, `ai.documentation`, `ai.enrichment`; todo `cli.*` como
modulo (`cli.main`, `cli.commands`, `cli.output`, `cli.errors`).

## Capa AI (`ai/`)

Genera documentacion tecnica con un LLM a partir de un `AnalysisResult`, sin invocar la CLI ni
modificar el Generator/Validator. Se usa programaticamente, inyectando el provider por
constructor:

```python
from analyzer import analyze_project
from providers import FakeProvider  # o get_provider(ProviderConfig(...)) para AnthropicProvider
from ai import DocumentationContextBuilder, DocumentationPromptBuilder, DocumentationEngine

result = analyze_project("examples/customer-service")

engine = DocumentationEngine(
    provider=FakeProvider(response='{"project_description": "..."}'),  # o AnthropicProvider real
    context_builder=DocumentationContextBuilder(),
    prompt_builder=DocumentationPromptBuilder(),
)
documentation = engine.generate(result)
print(documentation.to_json())
```

Cambiar `FakeProvider` por un `AnthropicProvider` real (via `providers.get_provider`) no requiere
modificar `ai/` en absoluto -- es exactamente el punto de depender solo de la abstraccion
`LLMProvider`. No existe ningun comando de CLI para esto (`spring-doc ai`/similares no existen).

**Aplicando la documentacion sobre el OpenAPI (`ai/enrichment.py`, V0.9):** una vez generado un
`DocumentationResult`, `apply_documentation` lo combina con el documento OpenAPI ya construido por
el Generator, escribiendo unicamente en campos de texto libre (nunca en estructura):

```python
from generators import generate, to_yaml
from ai import apply_documentation

document, _ = generate(result)
context = DocumentationContextBuilder().build(result)

enriched_document, enrichment_diagnostics = apply_documentation(document, documentation, context)
print(to_yaml(enriched_document))
for message in enrichment_diagnostics:
    print(message)
```

`enriched_document` sigue siendo un documento OpenAPI 3.0.3 valido (verificable con
`validator.validate`); cualquier desajuste entre `documentation` y `document` (un `endpoint_id`
que ya no existe, un DTO desconocido) queda en `enrichment_diagnostics`, nunca lanza una
excepcion.

## Skill de documentacion para LLMs (`skills/spring-doc/SKILL.md`)

`skills/spring-doc/SKILL.md` es un documento de conocimiento independiente — LLM-agnostico,
agente-agnostico y no ligado a `spring-doc` ni a ningun otro componente de este proyecto — que
ensena a un LLM como documentar el API HTTP de un microservicio Java/Spring Boot leyendo su
codigo fuente directamente: que buscar (controllers, mappings, parametros, DTOs, respuestas
-incluyendo el trazado de errores desde las excepciones que el codigo realmente lanza, no solo el
camino de exito-, seguridad -verificando que este realmente activa antes de documentarla-,
`tags`/`summary`/`description`, y campos "codigo de catalogo" fijos vs. dinamicos), como tratar la
ambiguedad y la informacion faltante sin inventar, y como estructurar el resultado. Se puede copiar
como un `.md` suelto y entregarse, junto con el codigo fuente de un
proyecto Spring Boot, a cualquier LLM. Este modo por defecto no requiere `spring-doc` ni ninguna
otra herramienta. No debe confundirse con `skill/` (singular, V0.1), el componente conceptual de
la arquitectura del producto — ver `docs/03-Arquitectura.md`.

**Seccion opcional de orquestacion end-to-end (V0.9):** delimitada por el encabezado `## Optional:
end-to-end orchestration using the spring-doc engine`, describe en 9 pasos como un agente puede
usar el motor `spring-doc` de punta a punta cuando esta disponible (`analyze` -> `generate` ->
`validate` -> `DocumentationEngine` -> `apply_documentation` -> `validate` final), siempre en
lenguaje neutral frente al LLM/agente que la ejecute y siempre explicitamente marcada como mejora
opcional, nunca como requisito: el modo por defecto sigue funcionando igual sin el motor
instalado y sin ningun LLM de pago disponible.

## Ejecucion de tests

```bash
pytest
```

## Ejemplo

El directorio `examples/customer-service/` contiene un microservicio Spring Boot minimo con
varios tipos de endpoint (`GET`, `POST`, `PUT`, `DELETE`, `PATCH`, `@PathVariable`,
`@RequestParam`, `@RequestBody`, `@RequestHeader`), DTOs con validaciones, DTOs anidados,
colecciones, un enum, seguridad, `consumes`/`produces`, y un archivo que demuestra el motor de
fallback (sintaxis Java invalida a proposito). Ver `examples/README.md`.

## Limitaciones

- El motor AST (`javalang`) falla el archivo completo ante cualquier error de sintaxis, y no
  soporta sintaxis Java posterior a 2020 (p. ej. `record`); en esos casos se usa el motor de
  fallback (V0.1), con sus propias limitaciones conocidas. Ver `docs/07-Analisis.md`.
- La resolucion de DTOs es por nombre simple de clase dentro del proyecto (sin resolucion de
  `import`s/classpath); nombres ambiguos entre archivos no se resuelven (se registra un
  diagnostic en vez de adivinar).
- El Generator nunca asume un codigo de respuesta (`200`, etc.) sin evidencia de `@ResponseStatus`;
  cuando falta, usa la clave `"default"` y registra un `Diagnostic` — esto ocurrira con frecuencia
  en proyectos reales, ya que la mayoria de los endpoints Spring no declaran `@ResponseStatus`
  explicitamente. Ver `docs/05-OpenAPI.md`.
- La evidencia de seguridad (`@PreAuthorize`/`@Secured`) no se traduce a un `securityScheme` de
  OpenAPI (no hay evidencia suficiente para elegir uno); se documenta como extension
  `x-security-evidence`.
- `Map<K,V>` se representa como `type: object` generico, sin `additionalProperties` tipado.
- El Validator no resuelve `$ref` externos (los detecta y los declara como `INFO`, sin
  descargarlos ni validarlos), no implementa `allOf`/`oneOf`/`anyOf`, ni valida flujos OAuth2 en
  profundidad. Contra el documento real de `examples/customer-service` produce 0 diagnostics
  ERROR pero un volumen considerable de WARNING/INFO (sin `description` en ningun lado, sin
  `security` real) — comportamiento esperado, no un indicio de error. Ver `docs/05-OpenAPI.md`.
- No hay auditoria ni integracion con Confluence todavia.
- `providers/` tiene la interfaz (V0.1), la infraestructura completa (V0.6) y un provider real,
  `AnthropicProvider` (V0.7, via stdlib, sin SDK). Ningun comando de la CLI (`analyze`/`generate`/
  `validate`) usa `providers/` ni `ai/`: no hace falta configurar nada de esto para usar
  `spring-doc`.
- `ai/` genera documentacion usando `LLMProvider` (real o `FakeProvider`)
  (`DocumentationEngine(provider, context_builder, prompt_builder).generate(analysis_result)`) y,
  desde V0.9, `ai/enrichment.py::apply_documentation` la combina con un documento OpenAPI ya
  generado, escribiendo solo en campos de texto libre. **Sigue sin haber ningun comando de CLI**
  para este flujo (`spring-doc ai`/similares no existen); se usa programaticamente o siguiendo la
  seccion opcional de `skills/spring-doc/SKILL.md`.

## Roadmap

Ver `docs/12-Roadmap.md`. Resumen: V1.0 Production Readiness (release de estabilizacion, sin
funcionalidades nuevas), V2.0 Documentation Quality Gate, V3.0 Drift Detection. (El Auditor,
originalmente agrupado con el Validator en V0.4, queda sin version asignada; LLM Providers,
originalmente V0.5, se reprogramo sin numero fijo cuando V0.5 se reasigno a CLI & Developer
Experience, y V0.6 lo retomo con directriz propia; Confluence Integration, originalmente V0.7, se
reprogramo sin numero fijo cuando V0.7 se reasigno a LLM Real Provider & AI Foundation. V0.9
conecto `ai/` con un documento OpenAPI ya generado -- `apply_documentation` -- y evoluciono la
Skill con una seccion opcional de orquestacion end-to-end del motor `spring-doc`. V1.0 verifica
empaquetado/instalacion limpia, documenta la API publica y resuelve deuda documental heredada,
sin cambios funcionales en ningun paquete.)

## Futuras integraciones

Integracion con Confluence a traves de un proyecto Python existente (fuera de este repositorio),
consumiendo la especificacion OpenAPI generada en fases futuras. Ver `docs/11-Integracion.md`.

## Licencia

MIT. Ver `LICENSE`.
