# Ejemplos

## customer-service

Microservicio Spring Boot minimo (solo codigo fuente, sin build ni dependencias reales — no esta
pensado para compilarse ni ejecutarse) usado para validar el Analyzer. Incluye:

- `CustomerController` (`@RequestMapping("/api/customers")`): `GET` (lista con `@RequestParam`
  opcionales y con `defaultValue`), `GET /{id}` (`@PathVariable`), `POST` (`@RequestBody`),
  `PUT /{id}` (`@PathVariable` con nombre explicito + `@RequestBody`), `PATCH /{id}/status`
  (`@RequestBody(required = false)`), `DELETE /{id}`.
- `OrderController`: un mapping generico `@RequestMapping(method = RequestMethod.GET)` y un
  mapping sin metodo HTTP explicito (caso limite: debe omitirse con un warning, ver
  `docs/07-Analisis.md`).

Uso:

```python
from analyzer import analyze_project

result = analyze_project("examples/customer-service")
print(result.to_json())
```
