# 01 — Modelo

## Que es Skill-Documentation-AI

Skill-Documentation-AI es un motor de documentacion inteligente que automatiza y mejora la
documentacion tecnica de microservicios Java/Spring Boot mediante analisis estatico de codigo
combinado con una Skill especializada y un LLM intercambiable.

El sistema analiza el codigo fuente de un microservicio, extrae evidencia estructurada sobre su
API (controllers, endpoints, parametros, etc.) y utiliza esa evidencia — junto con una Skill de
documentacion — para generar, completar, actualizar y auditar especificaciones OpenAPI.

## Problema

La documentacion de APIs en organizaciones con multiples microservicios tiende a degradarse con
el tiempo: queda incompleta, desactualizada respecto al codigo, o inconsistente entre servicios.
Mantenerla manualmente es costoso y propenso a errores. Ver `docs/02-Objetivos.md` para el
detalle del problema y `prompts/V0.1-foundation.md` seccion 2 para el listado completo.

## Solucion

Un pipeline conceptual que combina:

1. **Analisis deterministico** del codigo fuente (Analyzer) para extraer evidencia objetiva.
2. Una **Skill especializada** que encapsula el conocimiento de como documentar APIs correctamente.
3. Un **LLM intercambiable** que interpreta la evidencia y genera contenido siguiendo la Skill.
4. Mecanismos deterministicos de **validacion** y **auditoria** sobre el resultado.

## Proposito

Reducir el trabajo manual de documentacion, aumentar la cobertura y consistencia de las
especificaciones OpenAPI, y mantener trazabilidad entre el codigo fuente y la documentacion
generada.

## Flujo general

```text
Microservicio Spring Boot
        |
     Analyzer
        |
Evidence / Metadata
        |
Skill de documentacion
        |
   LLM Provider
        |
OpenAPI Generator
        |
     Validator
        |
     Auditor
        |
      OpenAPI
```

La integracion con Confluence es un flujo posterior e independiente (ver `docs/11-Integracion.md`)
y no forma parte de V0.1:

```text
OpenAPI
   |
Proyecto Python existente
   |
Confluence
```

## Entradas

- Codigo fuente de un microservicio Java/Spring Boot (V0.1: analisis via codigo fuente estatico).

## Procesamiento

- Analisis estatico del codigo para producir metadata estructurada (evidence).
- Interpretacion de esa evidencia por una Skill + LLM para producir documentacion (fases futuras).
- Validacion y auditoria deterministica del resultado (fases futuras).

## Salidas

- V0.1: metadata estructurada de endpoints (JSON-serializable), producida por el Analyzer.
- Fases futuras: especificacion OpenAPI (YAML/JSON), reportes de validacion y auditoria.

## Principios fundamentales

1. El sistema es independiente del proveedor de LLM (ver `docs/06-LLM.md`).
2. La evidencia deterministica tiene prioridad sobre la inferencia del LLM.
3. Ninguna inferencia se presenta como hecho sin trazabilidad a su origen.
4. La incertidumbre se conserva explicitamente, no se descarta ni se inventa informacion.
5. Cada componente mantiene una responsabilidad unica y limites claros (ver `docs/03-Arquitectura.md`).
