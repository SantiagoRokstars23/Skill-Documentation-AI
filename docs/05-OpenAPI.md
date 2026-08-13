# 05 — OpenAPI

> V0.3 implementa el OpenAPI Generator (`generators/`). Este documento describe el
> comportamiento **real** de esa implementación. Lo que en V0.1/V0.2 era aspiracional
> ("V0.3 lo implementará") ahora está construido; las secciones de este documento se
> han actualizado para reflejarlo.

## OpenAPI como contrato de salida

La salida del pipeline es una especificación **OpenAPI 3.0.3**, generada a partir de
`analyzer.AnalysisResult` por `generators.generate()`. OpenAPI se eligió como
contrato de salida porque es un estándar ampliamente adoptado, herramienta-agnóstico,
y consumible por herramientas externas — sin que esas herramientas (Swagger UI,
validadores completos, generación de SDKs) formen parte del alcance de V0.3 (ver
Scope Lock, `prompts/V0.3-OPENAPI-GENERATOR.md` sección 4).

## Versión objetivo: OpenAPI 3.0.3

Se eligió **3.0.3** (no 3.1.x, a pesar de que versiones anteriores de este documento
lo mencionaban como aspiración) por:

- Mayor compatibilidad de herramientas para quien consuma el archivo generado.
- Palabras clave de schema más simples de construir a mano correctamente sin una
  librería de validación (`nullable`/`exclusiveMinimum` booleanos de 3.0, en vez de
  la alineación con JSON Schema 2020-12 de 3.1).
- Decisión autorizada explícitamente para V0.3; ver el reporte de Fase 2 de V0.3.

## Arquitectura del Generator

```text
analyzer.AnalysisResult
        |
        v
generators.generate(result) -> (documento: dict, diagnostics: list[Diagnostic])
        |
        +-- generators.openapi_types    (texto de tipo Java -> schema; Bean Validation -> keywords)
        +-- generators.openapi_schemas  (DTO -> components.schemas, $ref, deduplicacion por nombre)
        |
        v
generators.to_json(documento) / generators.to_yaml(documento)
```

El Generator **no** importa `javalang`, `analyzer.spring_boot_analyzer`,
`analyzer.ast_analyzer`, `analyzer.dto_analyzer` ni `analyzer.scanner`: consume
únicamente el modelo público de `analyzer` (`AnalysisResult`, `Endpoint`,
`Parameter`, `Response`, `DTO`, `Field`, `Validation`, `Diagnostic`). No se modificó
ningún archivo de `analyzer/` para implementar V0.3.

## Elementos generados

| Elemento OpenAPI | Fuente | Comportamiento |
|---|---|---|
| `paths` | `Endpoint.endpoint` | Ordenados alfabéticamente (determinismo, no orden de `AnalysisResult.endpoints`) |
| operations | `Endpoint.method` | Una por método HTTP resuelto; ordenadas alfabéticamente dentro de cada path |
| `operationId` | `Endpoint.controller` + `Endpoint.java_method`, o el path normalizado si `java_method` es `None` | Ver "operationId" más abajo |
| `tags` | `Endpoint.controller` | Un tag por operación, el nombre simple del controller |
| `parameters` (path/query/header) | `Endpoint.parameters` filtrados por `source` | Ordenados por `(in, name)` |
| `requestBody` | `Parameter` con `source = body` | Ver "Request body" |
| `responses` | `Endpoint.response` | Ver "Responses (política conservadora)" — **nunca asume `200 application/json` sin evidencia** |
| `components.schemas` | `DTO`/`Field` resueltos | `$ref` reutilizado por nombre, sin duplicar; ordenados alfabéticamente |
| `security` | `Endpoint.security` | **No** se usa el campo `security` de OpenAPI (requiere `securitySchemes` que no se pueden justificar con la evidencia disponible); se documenta como extensión `x-security-evidence` + `Diagnostic` |
| `consumes`/`produces` | `Endpoint.consumes` / `Endpoint.produces` | Mapeados a las claves de `content` de `requestBody`/`responses` (OpenAPI 3.0 no tiene `consumes`/`produces` de nivel superior como Swagger 2.0) |

## Responses (política conservadora — decisión explícitamente autorizada)

El Generator **nunca** asume `200 application/json` sin evidencia. Reglas exactas:

1. Si `Endpoint.response` es `None` (endpoint producido por el motor de fallback de
   V0.1, sin metadata de respuesta): se genera `{"default": {"description": "..."}}`
   sin `content`, y se agrega un `Diagnostic` (`OPENAPI_RESPONSE_NO_EVIDENCE`,
   `WARNING`).
2. Si existe `Response` pero no hay `@ResponseStatus` reconocible (`status` es `None`
   o su texto no corresponde a una constante `HttpStatus` conocida): la clave de
   respuesta es `"default"` (no un número supuesto), y se agrega un `Diagnostic`
   (`OPENAPI_RESPONSE_STATUS_UNKNOWN`, `WARNING`). Esto ocurrirá con frecuencia — la
   mayoría de los endpoints Spring reales no declaran `@ResponseStatus`
   explícitamente — y es el comportamiento **esperado**, no un error.
3. Si `Response.status` corresponde a una constante `HttpStatus` reconocida (tabla
   `_HTTP_STATUS_CODES` en `generators/openapi_generator.py`, ampliable), se usa el
   código numérico como clave.
4. El cuerpo (`content`) solo se agrega cuando hay evidencia de tipo de respuesta
   (`Response.body_type` distinto de `None`/`"void"`); si el tipo no es resoluble
   (punto "Tipos no resueltos" más abajo) no se publica ningún `content`.
5. `description` es siempre el mismo texto genérico (`"Respuesta generada
   automaticamente (sin descripcion disponible en la evidencia)."`) — el Analyzer no
   captura comentarios/Javadoc, por lo que no existe ninguna fuente de descripción
   real; el campo es estructuralmente obligatorio en OpenAPI y se rellena con este
   texto explícitamente marcado como no-evidencia, nunca con una descripción inventada.

## Request body

Se genera cuando existe un `Parameter` con `source = body`. El `schema` se construye
igual que cualquier otro tipo (ver "Tipos Java → OpenAPI"); `required` viene
directamente de `Parameter.required` (ya calculado por el Analyzer a partir de
`@RequestBody(required = ...)`).

## Tipos Java → OpenAPI

Tabla completa en `generators/openapi_types.py::PRIMITIVE_TYPES`. Resumen:

| Java | OpenAPI |
|---|---|
| `String`, `char`/`Character` | `string` |
| `boolean`/`Boolean` | `boolean` |
| `int`/`Integer`, `short`/`Short` | `integer` / `int32` |
| `long`/`Long` | `integer` / `int64` |
| `float`/`Float` | `number` / `float` |
| `double`/`Double` | `number` / `double` |
| `BigDecimal` | `number` (sin `format`) |
| `BigInteger` | `integer` (sin `format`) |
| `UUID` | `string` / `uuid` |
| `LocalDate` | `string` / `date` |
| `LocalDateTime`, `Instant`, `ZonedDateTime`, `OffsetDateTime` | `string` / `date-time` |
| enum (`DTO.kind == "enum"`) | `string` con `enum: [...]` |
| `T[]`, `List<T>`, `Set<T>`, `Collection<T>`, `Iterable<T>` | `array` con `items` según `T` |
| `Optional<T>` | Se desenvuelve de forma transparente: el schema de `T` directamente (no es un `array`) |
| `Map<K,V>` | `type: object` genérico, **sin** `additionalProperties` tipado (V0.2 no desenvuelve genéricos de más de un argumento; sin evidencia suficiente) |
| `void`/`Void` | Sin cuerpo |

### Tipos no resueltos

Un tipo que no es un primitivo de la tabla anterior y para el cual el Analyzer no
resolvió un DTO (`dto`/`nested_dto` es `None`) se representa como `schema: {}` y
genera un `Diagnostic` (`OPENAPI_UNKNOWN_TYPE`, `WARNING`) — nunca se supone su
estructura. Esto incluye deliberadamente: tipos de librerías externas no
reconocidas, nombres de DTO ambiguos entre archivos (ya detectados por el Analyzer,
ver `docs/07-Analisis.md`), y genéricos anidados más allá del único nivel que el
Analyzer desenvuelve (p. ej. `List<Optional<CustomerResponse>>`: el Analyzer solo
resuelve DTO para el argumento inmediato de un único envoltorio, no de forma
recursiva; el Generator respeta esa misma limitación en vez de reinterpretar Java
por su cuenta, conforme al Scope Lock).

## Bean Validation → OpenAPI

| Anotación | Representación |
|---|---|
| `@NotNull`, `@NotBlank`, `@NotEmpty` | Agregan el campo a `required` del objeto contenedor (DTO). No generan una keyword de `schema` propia salvo lo indicado abajo. |
| `@NotBlank` | Además: `minLength: 1` |
| `@NotEmpty` | Además: `minItems: 1` (si el campo es una colección) o `minLength: 1` (si no) |
| `@Size(min, max)` | `minLength`/`maxLength` (no colección) o `minItems`/`maxItems` (colección) |
| `@Min(n)` / `@Max(n)` | `minimum` / `maximum` |
| `@Positive` / `@Negative` | `minimum: 0` + `exclusiveMinimum: true` / `maximum: 0` + `exclusiveMaximum: true` |
| `@PositiveOrZero` / `@NegativeOrZero` | `minimum: 0` / `maximum: 0` |
| `@Email` | `format: email` |
| `@Pattern(regexp = ...)` | `pattern` |

`required` a nivel de **parámetro** (path/query/header) usa `Parameter.required`
(semántica Spring MVC), no Bean Validation — un parámetro no es un objeto con
"campos requeridos" en el mismo sentido que un DTO.

## Security (representación conservadora — decisión explícitamente autorizada)

`Endpoint.security` (texto libre, p. ej. `"PreAuthorize(hasRole('ADMIN'))"`) **no**
se traduce a `security`/`components.securitySchemes` de OpenAPI: no hay evidencia
suficiente para determinar un esquema concreto (OAuth2, API key, HTTP Bearer, etc.)
a partir de una expresión SpEL de `@PreAuthorize`. En su lugar, se adjunta como
extensión `x-security-evidence: [...]` en la operación (las extensiones `x-*` son
parte del estándar OpenAPI para información adicional no cubierta por el spec) y se
genera un `Diagnostic` (`OPENAPI_SECURITY_EVIDENCE_ONLY`, `WARNING`). El Generator
**no** implementa un analizador de Spring Security.

## `components.schemas` y `$ref`

Cada `DTO` se registra una única vez en `components.schemas.<nombre>`, indexado por
`DTO.name`. Todas las referencias posteriores al mismo nombre reutilizan `$ref` en
vez de duplicar el schema inline. El árbol `DTO`/`Field.nested_dto` que entrega el
Analyzer **ya es acíclico** — el corte de ciclos ocurre en
`analyzer/dto_analyzer.py` antes de llegar al Generator (evento
`DTO_CYCLE_DETECTED`) — por lo que `generators/openapi_schemas.py` no necesita su
propia lógica de detección de ciclos, solo deduplicar por nombre.

## `info`

`info.title` (`"Generated API"`) e `info.version` (`"0.0.0"`) son valores fijos: no
existe ninguna fuente de evidencia para el nombre o la versión de la API en
`AnalysisResult`. Son estructuralmente obligatorios en OpenAPI 3.0.3, por lo que se
usa un valor claramente genérico en vez de omitir el campo o inventar un nombre de
proyecto.

## operationId

Estrategia determinista (nunca hashes ni valores aleatorios), autorizada
explícitamente para V0.3:

1. Si `Endpoint.java_method` existe (endpoint producido por el motor AST):
   `{http_method}{Controller}{JavaMethod}` (p. ej. `getCustomerControllerGetCustomer`).
2. Si `java_method` es `None` (endpoint del motor de fallback):
   `{http_method}{PathNormalizado}` (p. ej. `/orders/{orderId}` → `OrdersByOrderId`).
3. Colisiones (mismo id base) se resuelven con sufijo numérico determinista
   aplicado en el orden estable de iteración (`_2`, `_3`, ...), nunca con hashes.

## Salidas

`generators.to_json(documento)` (vía `json` de la librería estándar) y
`generators.to_yaml(documento)` (vía `PyYAML`, única dependencia nueva de V0.3 —
ver `docs/03-Arquitectura.md`). Ambas producen un resultado determinista para el
mismo documento de entrada (orden de claves preservado, sin `sort_keys`).

`examples/customer-service/openapi.yaml` y `openapi.json` son artefactos de ejemplo
generados a partir del proyecto de ejemplo (ver `examples/README.md`); no se
comparan byte a byte en los tests (`tests/test_openapi_example_project.py` valida
hechos estructurales, no el archivo literal).

## Excluido explícitamente de V0.3

Swagger UI, Swagger Editor, un validador OpenAPI completo, generación de código
cliente/servidor/SDK, documentación HTML, UI. Ver Scope Lock completo en
`prompts/V0.3-OPENAPI-GENERATOR.md` sección 4.
