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

## Estado actual — V0.1 (Foundation & Architecture)

Esta version establece las bases del proyecto. **Lo unico funcional en V0.1 es el Analyzer.** El
resto de componentes (Skill, LLM Provider, OpenAPI Generator, Validator, Auditor, CLI,
integraciones) estan definidos y documentados, pero no implementados. Ver `docs/12-Roadmap.md`.

Funcionalidad disponible hoy:

- Analisis estatico de un proyecto Java/Spring Boot.
- Deteccion de `@RestController`, mappings HTTP (`@GetMapping`, `@PostMapping`, `@PutMapping`,
  `@DeleteMapping`, `@PatchMapping`, `@RequestMapping`), paths, `@PathVariable`, `@RequestParam` y
  `@RequestBody`.
- Generacion de metadata estructurada y serializable (JSON) de los endpoints detectados.

## Arquitectura (resumen)

```text
Microservicio Spring Boot -> Analyzer -> Evidence/Metadata -> Skill -> LLM Provider
    -> OpenAPI Generator -> Validator -> Auditor -> OpenAPI
```

V0.1 implementa unicamente el tramo `Microservicio Spring Boot -> Analyzer -> Evidence/Metadata`.
Detalle completo en `docs/03-Arquitectura.md`.

## Stack

- **Lenguaje:** Python >= 3.11.
- **Dependencias de runtime:** ninguna (solo libreria estandar).
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
├── providers/       Interfaz de LLM Provider (sin implementaciones concretas en V0.1)
├── analyzer/        Analyzer funcional para Java/Spring Boot
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

V0.1 no incluye una CLI (reservada para V0.6). El Analyzer se usa como libreria Python:

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
`@RequestParam`, `@RequestBody`) pensado para validar el Analyzer. Ver `examples/README.md`.

## Limitaciones

- El Analyzer se basa en analisis de texto (regex + balance de brackets), no en un AST completo de
  Java; ver limitaciones detalladas en `docs/07-Analisis.md`.
- No hay generacion de OpenAPI, validacion, auditoria, CLI ni integracion con Confluence en esta
  version.
- No existen implementaciones concretas de proveedores LLM en esta version; solo la interfaz
  (`providers/base.py`).

## Roadmap

Ver `docs/12-Roadmap.md`. Resumen: V0.2 Spring Boot Analyzer, V0.3 OpenAPI Generator, V0.4
Validator + Auditor, V0.5 LLM Providers, V0.6 CLI, V0.7 Confluence Integration, V1.0 Production,
V2.0 Documentation Quality Gate, V3.0 Drift Detection.

## Futuras integraciones

Integracion con Confluence a traves de un proyecto Python existente (fuera de este repositorio),
consumiendo la especificacion OpenAPI generada en fases futuras. Ver `docs/11-Integracion.md`.

## Licencia

MIT. Ver `LICENSE`.
