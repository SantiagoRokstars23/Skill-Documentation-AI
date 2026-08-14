# 02 — Objetivos

## Objetivo general del proyecto

Construir un motor de documentacion inteligente capaz de analizar microservicios Java/Spring
Boot, extraer evidencia estructurada de su API, utilizar una Skill especializada junto con un LLM
intercambiable para generar documentacion OpenAPI, validarla, auditarla y — en fases futuras —
detectar divergencias entre codigo y documentacion e integrarse con sistemas externos como
Confluence.

## Objetivos especificos

1. Analizar microservicios Java/Spring Boot.
2. Identificar endpoints y elementos relevantes de la API (controllers, mappings, parametros).
3. Extraer evidencia estructurada del codigo (con trazabilidad al origen).
4. Definir y utilizar una Skill especializada en documentacion de APIs.
5. Definir una interfaz de LLM Provider intercambiable.
6. Generar documentacion OpenAPI a partir de la evidencia (fase futura).
7. Validar la documentacion generada (fase futura).
8. Auditar la calidad y trazabilidad de la documentacion (fase futura).
9. Detectar divergencias entre codigo y documentacion (fase futura).
10. Integrarse con sistemas externos como Confluence (fase futura).

## Objetivos de V0.1 (Foundation & Architecture)

V0.1 se limita a establecer las bases del proyecto:

- Arquitectura y estructura de proyecto definidas y documentadas.
- Documentacion inicial completa (`README.md`, `CLAUDE.md`, reglas globales, `docs/`).
- Skill inicial (estructura, reglas, referencias, plantillas), independiente del proveedor LLM.
- Estructura para proveedores LLM (interfaz conceptual, sin implementaciones concretas).
- Analyzer inicial funcional para Java/Spring Boot, con metadata estructurada de endpoints.
- Tests unitarios del Analyzer.
- Ejemplo de microservicio para validar el Analyzer.
- Roadmap, versionado y CHANGELOG.

Ver criterios de aceptacion detallados en `prompts/V0.1-foundation.md` seccion 22.

## Objetivos futuros (fuera de V0.1)

> Nota: las asignaciones de version de esta lista corresponden al roadmap original de V0.1. Varias
> se reprogramaron durante el desarrollo real del proyecto; ver `docs/12-Roadmap.md` para las
> reasignaciones documentadas y el estado actual de cada una.

- Generacion completa de especificaciones OpenAPI (V0.3).
- Validacion deterministica de documentacion OpenAPI (V0.4 acoto el alcance original de este punto
  al OpenAPI Quality Validator; la auditoria de trazabilidad/confidence quedo sin version
  asignada).
- CLI del proyecto (V0.5; el roadmap original la ubicaba en V0.6).
- Infraestructura de LLM Providers y primer provider real (V0.6/V0.7; "implementacion completa de
  multiples proveedores LLM" no fue el objetivo perseguido -- se prioriza un unico provider
  comercial real mas la abstraccion intercambiable).
- Integracion con Confluence (originalmente V0.7; reprogramada sin numero de version fijo).
- Deteccion de divergencias (drift) entre codigo y documentacion (V3.0).
- Quality Gate de documentacion (V2.0).

Ver `docs/12-Roadmap.md` para el detalle completo y las reasignaciones de version.

## Funcionalidades fuera de alcance (V0.1)

Segun el Scope Lock de `prompts/V0.1-foundation.md` seccion 19, V0.1 NO implementa:

- Generacion completa de OpenAPI.
- Integracion con Confluence.
- Modificacion del proyecto Python existente de integracion con Confluence.
- CI/CD (Jenkins, GitLab u otros).
- Interfaz web o chatbot.
- Entrenamiento de modelos o modelo propio.
- PSD2.
- Quality Gate.
- Automatizacion de Pull Requests.
- Deteccion de divergencias (Drift Detection).
- Publicacion automatica de documentacion.
- Soporte completo para lenguajes distintos de Java.
- Soporte completo para frameworks distintos de Spring Boot.
- Implementacion completa de multiples proveedores LLM.
