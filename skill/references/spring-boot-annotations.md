# Referencia: Anotaciones Spring Boot reconocidas

| Anotacion | Nivel | Significado para el Analyzer |
|---|---|---|
| `@RestController` | Clase | Marca la clase como controller de API REST. |
| `@RequestMapping("/base")` | Clase | Define el `basePath` de todos los endpoints de la clase. |
| `@GetMapping(...)` | Metodo | Endpoint `GET`. |
| `@PostMapping(...)` | Metodo | Endpoint `POST`. |
| `@PutMapping(...)` | Metodo | Endpoint `PUT`. |
| `@DeleteMapping(...)` | Metodo | Endpoint `DELETE`. |
| `@PatchMapping(...)` | Metodo | Endpoint `PATCH`. |
| `@RequestMapping(method = RequestMethod.X, ...)` | Metodo | Endpoint de metodo `X` (forma generica). Sin `method` explicito, se omite (ver `docs/07-Analisis.md`). |
| `@PathVariable` | Parametro | Parametro de path (`source = "path"`). |
| `@RequestParam` | Parametro | Parametro de query (`source = "query"`). |
| `@RequestBody` | Parametro | Cuerpo de la peticion (`source = "body"`). |

Anotaciones no listadas aqui (por ejemplo `@RequestHeader`, `@Valid`, anotaciones de seguridad)
no son reconocidas por el Analyzer en V0.1. Ver `docs/12-Roadmap.md` (V0.2) para su evaluacion
futura.
