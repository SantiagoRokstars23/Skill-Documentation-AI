# 13 — Versionado

## Estrategia de versionado

El proyecto sigue [Semantic Versioning](https://semver.org/lang/es/) (`MAJOR.MINOR.PATCH`), con
una particularidad: durante la fase inicial (`0.x`), cada incremento de `MINOR` corresponde a una
fase completa del roadmap (ver `docs/12-Roadmap.md`), no a cambios menores arbitrarios.

## Significado de major/minor/patch

- **MAJOR (`X.0.0`):** cambios que rompen compatibilidad con la metadata, la Skill, o la interfaz
  de `LLMProvider` establecidas en versiones anteriores. Tambien marca hitos de madurez del
  proyecto (p. ej. V1.0 Production).
- **MINOR (`0.X.0`):** una fase completa del roadmap (p. ej. V0.2 Spring Boot Analyzer). Anade
  funcionalidad de forma retrocompatible con la metadata y estructuras publicas de versiones
  `0.x` anteriores.
- **PATCH (`0.0.X`):** correcciones de bugs o ajustes menores que no anaden funcionalidad ni
  rompen compatibilidad.

## Relacion entre versiones y funcionalidades

Cada version del roadmap tiene una directriz propia (ver `prompts/`) que define exactamente su
alcance (Scope Lock). El numero de version del paquete Python (`pyproject.toml`) debe
corresponder a la version de la directriz completada mas recientemente.

## Compatibilidad

- Mientras el proyecto se mantenga en `0.x`, las estructuras publicas (`Endpoint`, `Parameter`,
  `AnalysisResult`, la interfaz `LLMProvider`) pueden extenderse con nuevos campos opcionales sin
  romper compatibilidad, pero no deben eliminarse ni renombrarse campos existentes sin justificar
  el cambio y documentarlo (regla global 9).
- Un cambio que elimine o modifique el significado de un campo existente de la metadata requiere
  una entrada explicita en `CHANGELOG.md` y, si aplica, un incremento de versionado MAJOR una vez
  el proyecto alcance `1.0.0`.

### V0.1.0 -> V0.2.0

Todos los campos nuevos de `Endpoint`, `Parameter` y `Evidence` (V0.2) tienen valores por defecto:
el codigo que construye estas estructuras posicionalmente/por palabra clave como en V0.1 sigue
funcionando sin cambios (`analyzer/spring_boot_analyzer.py`, el motor de fallback, no se modifico).
`AnalysisResult` gano `controllers` y `diagnostics`; `warnings` se mantiene con el mismo
comportamiento observable.

**Excepcion documentada (Regla 7 de la directriz V0.2):** la forma exacta del diccionario devuelto
por `to_dict()` en `Parameter`/`Endpoint` **si** cambio (se agregaron claves nuevas:
`default_value`, `validations`, `dto` en `Parameter`; `symbol`/`type` en `Evidence`; `java_method`,
`consumes`, `produces`, `response`, `security` en `Endpoint`). Cualquier consumidor que compare el
resultado de `to_dict()` contra un diccionario exacto (en vez de leer claves especificas) vera mas
claves de las que existian en V0.1. Esto es intencional: es precisamente la funcionalidad que V0.2
debia agregar (seccion 5 de `prompts/V0.2-ADVANCED-SPRING-BOOT-ANALYZER.md`). Los dos tests de
V0.1 que hacian esa comparacion exacta (`tests/test_models.py`) se actualizaron para reflejar la
forma completa, sin reducir lo que verifican.
