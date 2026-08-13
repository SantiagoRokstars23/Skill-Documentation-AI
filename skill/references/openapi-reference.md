# Referencia: Estructura OpenAPI objetivo

Ver `docs/05-OpenAPI.md` para el detalle completo. Resumen del vocabulario que debera producir el
futuro OpenAPI Generator (V0.3) a partir de la metadata del Analyzer:

- `paths[endpoint]` — uno por cada `Endpoint.endpoint` distinto.
- `paths[endpoint][method]` — una operation por cada `Endpoint.method`.
- `parameters` — uno por cada `Parameter` con `source` en `path`/`query`, incluyendo `required`.
- `requestBody` — derivado de los `Parameter` con `source = "body"`.
- `responses` — solo cuando exista evidencia; en caso contrario, marcado como pendiente.
- `schemas` — derivados de los tipos declarados en `Parameter.type`.

Version objetivo: OpenAPI 3.1 (ver `docs/05-OpenAPI.md`).
