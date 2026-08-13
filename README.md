# Skill-Documentation-AI

Motor de documentacion inteligente para microservicios Java/Spring Boot. Analiza codigo fuente,
extrae evidencia estructurada de su API y (en fases futuras) utiliza una Skill especializada junto
con un LLM intercambiable para generar, completar, actualizar y auditar especificaciones OpenAPI.

## Problema

La documentacion de APIs suele quedar incompleta, desactualizada respecto al codigo e
inconsistente entre microservicios, lo que genera un trabajo manual elevado y dificulta mantener
documentacion empresarial consistente. Ver `docs/01-Modelo.md`.

## Objetivo

Reducir ese problema mediante automatizacion, analisis estatico deterministico del codigo, y
capacidades de LLM controladas por una Skill especializada, manteniendo el sistema independiente
de cualquier proveedor de LLM concreto. Ver `docs/02-Objetivos.md`.

## Estado actual — V0.2 (Advanced Spring Boot Analyzer)

**Lo unico funcional del proyecto es el Analyzer.** El resto de componentes (Skill, LLM Provider,
OpenAPI Generator, Validator, Auditor, CLI, integraciones) estan definidos y documentados, pero no
implementados. Ver `docs/12-Roadmap.md`.

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
- Generacion de metadata estructurada y serializable (JSON) de endpoints, controllers, DTOs y
  diagnostics.
- El Analyzer **nunca inventa informacion**: cuando un dato no puede determinarse con confianza
  (p. ej. un nombre de DTO ambiguo entre archivos), se registra un `Diagnostic` en vez de
  suponerse (ver `docs/09-Auditoria.md`).

## Arquitectura (resumen)

```text
Microservicio Spring Boot -> Analyzer -> Evidence/Metadata -> Skill -> LLM Provider
    -> OpenAPI Generator -> Validator -> Auditor -> OpenAPI
```

El proyecto implementa unicamente el tramo `Microservicio Spring Boot -> Analyzer ->
Evidence/Metadata`. Detalle completo en `docs/03-Arquitectura.md`.

## Stack

- **Lenguaje:** Python >= 3.11.
- **Dependencias de runtime:** `javalang` (parser AST de Java, motor principal del Analyzer desde
  V0.2 — ver decision documentada en `docs/03-Arquitectura.md`).
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
├── skill/           Skill de documentacion (SKILL.md, rules/, references/, templates/)
├── providers/       Interfaz de LLM Provider (sin implementaciones concretas)
├── analyzer/        Analyzer funcional para Java/Spring Boot (motor AST + fallback regex)
├── validators/       Placeholder, reservado para V0.4
├── generators/       Placeholder, reservado para V0.3
├── tests/           Tests unitarios del Analyzer
└── examples/        Microservicio Spring Boot de ejemplo
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

## Ejecucion

No hay una CLI todavia (reservada para V0.6). El Analyzer se usa como libreria Python:

```python
from analyzer import analyze_project

result = analyze_project("examples/customer-service")

for endpoint in result.endpoints:
    print(endpoint.method, endpoint.endpoint, "->", endpoint.controller)

print(result.to_json())
```

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
- No hay generacion de OpenAPI, validacion, auditoria, CLI ni integracion con Confluence todavia.
- No existen implementaciones concretas de proveedores LLM; solo la interfaz (`providers/base.py`).

## Roadmap

Ver `docs/12-Roadmap.md`. Resumen: V0.3 OpenAPI Generator, V0.4 Validator + Auditor, V0.5 LLM
Providers, V0.6 CLI, V0.7 Confluence Integration, V1.0 Production, V2.0 Documentation Quality
Gate, V3.0 Drift Detection.

## Futuras integraciones

Integracion con Confluence a traves de un proyecto Python existente (fuera de este repositorio),
consumiendo la especificacion OpenAPI generada en fases futuras. Ver `docs/11-Integracion.md`.

## Licencia

MIT. Ver `LICENSE`.
