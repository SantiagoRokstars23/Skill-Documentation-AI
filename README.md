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

## Estado actual — V0.6 (LLM Providers & AI Foundation)

**Funcional: el Analyzer, el OpenAPI Generator, el OpenAPI Quality Validator, la CLI
(`spring-doc`) y la infraestructura de LLM Providers** (configuracion, errores, seleccion por
nombre, y un `FakeProvider` determinista — **sin ningun proveedor comercial real todavia**). El
resto de componentes (Skill como motor ejecutable, Auditor, integraciones) estan definidos y
documentados, pero no implementados. Ver `docs/12-Roadmap.md`.

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
`Evidence/Metadata -> OpenAPI Generator -> OpenAPI`, y `OpenAPI -> Validator -> Diagnostics`
(la transformacion a OpenAPI no pasa todavia por la Skill ni por un LLM Provider, que no tienen
implementacion concreta; el Auditor tampoco esta implementado). Detalle completo en
`docs/03-Arquitectura.md`.

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
├── skills/spring-doc/  SKILL.md (V0.6): como documentar un microservicio Spring Boot leyendo su
│                    codigo fuente, LLM/agente/herramienta-agnostico, independiente de spring-doc
├── providers/       LLM Provider: interfaz (V0.1) + config/errores/registry/FakeProvider (V0.6)
├── analyzer/        Analyzer funcional para Java/Spring Boot (motor AST + fallback regex)
├── validators/       Placeholder sin uso (ver nota de nomenclatura en docs/03-Arquitectura.md)
├── generators/       OpenAPI Generator funcional (AnalysisResult -> OpenAPI 3.0.3)
├── validator/        OpenAPI Quality Validator funcional (documento OpenAPI -> Diagnostics)
├── cli/             CLI funcional (`spring-doc`): analyze / generate / validate
├── tests/           Tests del Analyzer, del Generator, del Validator, de la CLI y de providers/
└── examples/        Microservicio Spring Boot de ejemplo (+ openapi.yaml/openapi.json generados)
```

## Instalacion

Requiere Python 3.11 o superior.

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -e ".[dev]"
```

Esto deja disponible el comando `spring-doc` (entry point definido en `[project.scripts]`).

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
proyecto Spring Boot, a cualquier LLM. No requiere `spring-doc` ni ninguna otra herramienta; puede
mencionarla como opcion, nunca como requisito. No debe confundirse con `skill/` (singular, V0.1),
el componente conceptual de la arquitectura del producto — ver `docs/03-Arquitectura.md`.

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
- `providers/` tiene la interfaz (V0.1) y la infraestructura completa (V0.6: configuracion,
  errores, seleccion por nombre), pero **ningun proveedor comercial real** — solo `FakeProvider`,
  pensado para tests. Ningun comando de la CLI (`analyze`/`generate`/`validate`) usa `providers/`
  en absoluto: no hace falta configurar nada de esto para usar `spring-doc`.

## Roadmap

Ver `docs/12-Roadmap.md`. Resumen: V0.7 Confluence Integration, V1.0 Production, V2.0
Documentation Quality Gate, V3.0 Drift Detection. (El Auditor, originalmente agrupado con el
Validator en V0.4, queda sin version asignada; LLM Providers, originalmente V0.5, se reprogramo
sin numero fijo cuando V0.5 se reasigno a CLI & Developer Experience, y V0.6 lo retomo con
directriz propia.)

## Futuras integraciones

Integracion con Confluence a traves de un proyecto Python existente (fuera de este repositorio),
consumiendo la especificacion OpenAPI generada en fases futuras. Ver `docs/11-Integracion.md`.

## Licencia

MIT. Ver `LICENSE`.
