# Ejemplos

## customer-service

Microservicio Spring Boot minimo (solo codigo fuente, sin build ni dependencias reales — no esta
pensado para compilarse ni ejecutarse) usado para validar el Analyzer.

### Controllers

- `CustomerController` (`@RequestMapping("/api/customers")`): `GET` (lista con `@RequestParam`
  opcionales y con `defaultValue`), `GET /{id}` (`@PathVariable`), `POST` (`@RequestBody`),
  `PUT /{id}` (`@PathVariable` con nombre explicito + `@RequestBody`), `PATCH /{id}/status`
  (`@RequestBody(required = false)`), `DELETE /{id}`, y `POST /{id}/notes` (V0.2:
  `@RequestHeader`, `@PreAuthorize`, `consumes`/`produces` explicitos, `@ResponseStatus`).
- `OrderController`: un mapping generico `@RequestMapping(method = RequestMethod.GET)` y un
  mapping sin metodo HTTP explicito (caso limite: debe omitirse con un diagnostic, ver
  `docs/07-Analisis.md`).
- `LegacyReportController` (V0.2): incluye un metodo con sintaxis Java invalida a proposito, para
  demostrar el motor de fallback (el AST no puede parsear el archivo completo; el motor de V0.1
  recupera el endpoint valido y omite el metodo malformado). Ver `docs/07-Analisis.md`.

### DTOs (V0.2)

- `CustomerRequest`: campos con Bean Validation (`@NotBlank`, `@Size`, `@Email`), un campo enum
  (`CustomerStatus`), un DTO anidado (`Address`) y una coleccion (`List<String> tags`).
- `Address`: DTO anidado referenciado desde `CustomerRequest`, con su propia validacion.
- `CustomerStatus`: enum referenciado desde `CustomerRequest`.
- `CustomerResponse`, `OrderResponse`: DTOs de respuesta, resueltos automaticamente a partir del
  tipo de retorno (`ResponseEntity<CustomerResponse>`, etc.).

Uso:

```python
from analyzer import analyze_project

result = analyze_project("examples/customer-service")
print(result.to_json())
```
