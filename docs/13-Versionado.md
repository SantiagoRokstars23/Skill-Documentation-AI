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
