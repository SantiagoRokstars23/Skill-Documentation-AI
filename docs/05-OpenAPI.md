# 05 — OpenAPI

> Este documento describe el contrato de salida objetivo del sistema. La generacion de OpenAPI
> **no** esta implementada en V0.1 (ver Scope Lock, `prompts/V0.1-foundation.md` seccion 19); este
> documento existe para dejar el diseño y el vocabulario preparados para V0.3.

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

- **paths:** una entrada por endpoint detectado (`Endpoint.endpoint`).
- **operations:** una operacion por combinacion path + metodo HTTP (`Endpoint.method`).
- **parameters:** derivados de `Parameter` (path, query), incluyendo tipo y si son requeridos.
- **requestBody:** derivado de parametros con `source = body`.
- **responses:** estructura minima (codigos de estado) cuando exista evidencia suficiente;
  cuando no exista evidencia, debe marcarse como incierto en vez de inventarse (ver
  `docs/09-Auditoria.md`).
- **schemas:** derivados de los tipos de los parametros y del cuerpo de la peticion/respuesta.
- **security:** derivado de evidencia de seguridad en el codigo (p. ej. anotaciones de
  autenticacion), cuando exista. No implementado en V0.1.
- **headers:** derivados de evidencia explicita en el codigo (p. ej. `@RequestHeader`). No
  implementado en V0.1.
- **examples:** generados por el LLM Provider siguiendo la Skill, siempre marcados como generados
  (no como evidencia deterministica).

## Reglas futuras

- Ningun elemento de la especificacion debe presentarse como determinista si proviene de
  inferencia del LLM; debe quedar identificable su origen (evidencia vs. generado).
- La especificacion generada debe ser validable estructuralmente antes de auditarse.
- El Generator debe ser independiente del LLM Provider utilizado para producir el contenido.
