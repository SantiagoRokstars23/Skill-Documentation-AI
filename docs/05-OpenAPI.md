# 05 — OpenAPI

> Este documento describe el contrato de salida objetivo del sistema. La generacion de OpenAPI
> **no** esta implementada (ni en V0.1 ni en V0.2, ver Scope Lock de ambas directrices); este
> documento existe para dejar el diseño y el vocabulario preparados para V0.3.
>
> V0.2 amplio el modelo de metadata del Analyzer (`docs/07-Analisis.md`) especificamente pensando
> en cerrar la brecha hacia estos elementos (seccion 14 de `prompts/V0.2-...`), sin implementar
> ninguno de ellos todavia. Ver la columna "Fuente en V0.2" mas abajo.

## OpenAPI como contrato de salida

La salida final del pipeline (fases futuras) es una especificacion **OpenAPI**, formato estandar
e independiente de proveedor para describir APIs REST. OpenAPI se elige como contrato de salida
porque:

- Es un estandar ampliamente adoptado y herramienta-agnostico.
- Permite validacion estructural automatica (`docs/08-Validacion.md`).
- Es consumible por herramientas externas (documentacion, mocks, clientes, Confluence).

## Version objetivo

**OpenAPI 3.1** (compatible con 3.0 cuando sea razonable). La version concreta debe fijarse
explicitamente en el Generator cuando se implemente (V0.3) y documentarse en este archivo.

## Elementos que se deberan generar (fases futuras)

| Elemento OpenAPI | Fuente en V0.2 (Analyzer) |
|---|---|
| **paths** | `Endpoint.endpoint` |
| **operations** | `Endpoint.method` (una por metodo HTTP; `RequestMapping` con multiples metodos ya produce un `Endpoint` por metodo, ver `docs/07-Analisis.md`) |
| **parameters** (path/query/header) | `Endpoint.parameters` filtrados por `Parameter.source` (`path`/`query`/`header`), con `type`/`required`/`default_value` |
| **requestBody** | `Parameter` con `source = body`; `Parameter.dto` ya trae la estructura del cuerpo cuando es resoluble |
| **responses** | `Endpoint.response` (`wrapper`, `body_type`, `dto`, `status`); si `dto`/`status` es `None`, no hay evidencia suficiente y no debe inventarse (ver `docs/09-Auditoria.md`) |
| **schemas** | `DTO`/`Field` (nombre, tipo, `is_collection`, `nested_dto`, `enum_constants`) |
| **security** | `Endpoint.security` (evidencia de `@PreAuthorize`/`@Secured`, sin interpretar reglas de autorizacion) |
| **headers** | `Parameter` con `source = header` |
| **content types** (`consumes`/`produces`) | `Endpoint.consumes` / `Endpoint.produces` |
| **tags** | No hay fuente en V0.2; `Controller.name` es el candidato mas cercano pero no se ha decidido una regla de agrupacion |
| **examples** | Sin fuente deterministica; se generan por el LLM Provider siguiendo la Skill, siempre marcados como generados (no como evidencia) |

Ningun elemento de esta tabla se genera en V0.2: la tabla documenta de donde **podra** leerse cada
uno quando exista el Generator (V0.3), no una implementacion actual.

## Reglas futuras

- Ningun elemento de la especificacion debe presentarse como determinista si proviene de
  inferencia del LLM; debe quedar identificable su origen (evidencia vs. generado).
- La especificacion generada debe ser validable estructuralmente antes de auditarse.
- El Generator debe ser independiente del LLM Provider utilizado para producir el contenido.
