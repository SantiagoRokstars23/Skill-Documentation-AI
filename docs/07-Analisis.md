# 07 — Analisis (Analyzer)

## Analisis de codigo

El Analyzer (`analyzer/`) realiza analisis **estatico** y **deterministico** del codigo fuente de
un microservicio Java/Spring Boot para producir evidencia estructurada sobre su API. No utiliza
ningun LLM: toda la informacion que produce proviene directamente del codigo fuente.

**Principio fundamental (V0.2):** el Analyzer produce **evidencia, no inferencias**. Cuando un
dato no puede determinarse de forma suficientemente confiable a partir del codigo analizado,
queda como desconocido (`None`/vacio) y, cuando corresponde, se registra un `Diagnostic`
(`docs/09-Auditoria.md`) — nunca se completa por suposicion. Esta regla gobierna cada decision de
diseño descrita en este documento, porque la metadata producida aqui es la que un LLM consumira
en fases futuras para documentar el microservicio: debe reflejar lo que **realmente existe** en el
codigo, no lo que "probablemente" existe.

## Dos motores de analisis (V0.2)

V0.1 tenia un unico motor basado en expresiones regulares y balance de brackets/parentesis. V0.2
evalua formalmente esa estrategia frente a un parser AST de Java (evaluacion documentada en
`docs/03-Arquitectura.md`, decision arquitectonica 1) y adopta un **motor hibrido**:

1. **Motor AST (principal, V0.2):** `analyzer/ast_backend.py` + `analyzer/ast_analyzer.py` +
   `analyzer/dto_analyzer.py`, basado en la libreria `javalang`. Parsea cada archivo `.java` como
   un arbol de sintaxis real, lo que permite reconocer construcciones que el motor de V0.1 no
   podia (anotaciones fully-qualified, metodos package-private, `@RequestMapping` con multiples
   `RequestMethod`, genericos, DTOs referenciados en otros archivos, etc. — ver "Capacidades
   V0.2" mas abajo).
2. **Motor regex (fallback, V0.1, sin modificar):** `analyzer/spring_boot_analyzer.py`. Se usa
   **por archivo**, unicamente cuando el motor AST no puede parsear ese archivo especifico (ver
   "Cuando se usa el fallback").

`analyzer/__init__.py::analyze_project` orquesta ambos motores. Ningun archivo del proyecto
analizado necesita ser "todo AST" o "todo regex": la decision se toma archivo por archivo.

### Cuando se usa el fallback

El motor AST falla para un archivo completo (no solo para la construccion problematica) cuando:

- El archivo no puede leerse (error de E/S o de codificacion).
- El archivo tiene un error de sintaxis Java en cualquier punto (`javalang` no puede parsear un
  archivo con un solo error de sintaxis, sin importar donde este).
- El archivo usa sintaxis Java posterior a 2020 no soportada por `javalang` (p. ej. `record`,
  ver limitacion documentada mas abajo).

En cualquiera de estos casos, `analyze_project` recurre al motor de V0.1 **sin ninguna
modificacion** para ese archivo, y registra un `Diagnostic` (`code="AST_PARSE_FALLBACK"`,
severidad `INFO`) indicando el motivo. El comportamiento del motor de fallback es exactamente el
de V0.1: recupera endpoints de construcciones validas dentro de un archivo con errores localizados
(p. ej. un metodo con parentesis sin cerrar entre otros metodos validos), pero **no** recupera
nada si la clase controller en si no cierra correctamente (limitacion ya existente en V0.1, ver
`tests/test_edge_cases.py::test_malformed_class_without_closing_brace_does_not_crash`).

Los endpoints producidos por el motor de fallback tienen la misma forma que en V0.1
(`java_method`, `consumes`, `produces`, `response`, `security` quedan en sus valores por defecto,
ya que el motor regex no los extrae) — ver "Compatibilidad" en `docs/13-Versionado.md`.

## Spring Boot

El Analyzer reconoce anotaciones de Spring MVC / Spring Boot y de Bean Validation sobre clases,
metodos, parametros y campos Java. No ejecuta el codigo ni requiere un entorno Java.

## Controllers

Se detectan clases anotadas con `@RestController`, y clases anotadas con `@Controller` que ademas
tengan al menos un metodo con una anotacion de mapping HTTP reconocida (para excluir controllers
MVC/vista sin relevancia para el modelo de API, seccion 5.1 de `prompts/V0.2-...`). El motor AST
reconoce estas anotaciones tanto por su nombre simple como completamente calificado (p. ej.
`@org.springframework.web.bind.annotation.RestController`), y detecta clases anidadas (no solo de
nivel superior).

Cada clase controller detectada se representa como un `Controller` (`analyzer/models.py`), con sus
anotaciones, modificadores, `base_path` (extraido de `@RequestMapping` a nivel de clase) y
evidencia. `Endpoint.controller` sigue siendo el nombre simple de la clase (compatibilidad con
V0.1); `AnalysisResult.controllers` da acceso al detalle completo.

## Mappings

Dentro de una clase controller, se detectan metodos anotados con:

- `@GetMapping`, `@PostMapping`, `@PutMapping`, `@DeleteMapping`, `@PatchMapping`
- `@RequestMapping(method = RequestMethod.X, ...)`, incluyendo la forma con **multiples metodos**
  (`method = {RequestMethod.GET, RequestMethod.POST}`): el Analyzer produce **un `Endpoint` por
  cada metodo HTTP resuelto**, todos con el mismo path y parametros (asi es como OpenAPI
  representa multiples operaciones sobre el mismo path).

El path de cada mapping se extrae del atributo `value`/`path` de la anotacion. El path final del
endpoint es la concatenacion del `base_path` de la clase (si existe) con el path del metodo.

Si un metodo esta anotado con `@RequestMapping` sin ningun `RequestMethod` resoluble, el Analyzer
**no** asume un metodo HTTP por defecto: el mapping se omite y se registra un `Diagnostic`
(`code="AST_MAPPING_WITHOUT_HTTP_METHOD"` en el motor AST, o el warning equivalente del motor de
fallback), reflejado tambien en `AnalysisResult.warnings` por compatibilidad con V0.1.

## HTTP methods

Se detectan `GET`, `POST`, `PUT`, `DELETE`, `PATCH`. Otros valores de `RequestMethod` (p. ej.
`HEAD`, `OPTIONS`, `TRACE`) no estan contemplados en el alcance de V0.2 (seccion 5.2 de la
directriz) y se descartan sin inventar un metodo equivalente.

## Paths

Los paths se obtienen exclusivamente de los valores literales presentes en las anotaciones. No se
infieren paths no declarados explicitamente.

## Consumes / Produces (V0.2)

Se extraen los atributos `consumes`/`produces` de `@RequestMapping` y de las anotaciones
`@*Mapping`, tanto en forma de valor unico como de arreglo. Si el metodo no los declara, se usa el
valor de `@RequestMapping` a nivel de clase (si existe) como valor por defecto — el metodo tiene
prioridad sobre la clase.

## Parametros

Por cada parametro del metodo, el Analyzer determina su `source` segun la anotacion presente. Un
parametro sin ninguna de las anotaciones reconocidas se excluye de la metadata (no se inventa un
origen).

### Path variables (`@PathVariable`)

- `source = "path"`. Nombre explicito o nombre del parametro Java. `required` es `true` salvo
  `required = false` explicito.

### Query parameters (`@RequestParam`)

- `source = "query"`. `required` es `true` por defecto, `false` si hay `required = false` o si
  existe `defaultValue` (el valor de `defaultValue` se conserva en `Parameter.default_value`).

### Headers (`@RequestHeader`, V0.2)

- `source = "header"`. Mismo criterio de nombre/`required`/`default_value` que `@RequestParam`.

### Request body (`@RequestBody`)

- `source = "body"`. Tipo Java declarado del parametro. `required` es `true` por defecto, `false`
  si hay `required = false` explicito.
- **Resolucion de DTO (V0.2):** si el tipo del parametro corresponde a una clase/enum del propio
  proyecto (indexada por `analyzer/dto_analyzer.py`), `Parameter.dto` contiene su estructura
  resuelta (ver "DTOs" mas abajo). Si el tipo no es una clase/enum del proyecto (p. ej. `String`,
  un tipo de una libreria externa), `Parameter.dto` queda en `None` — no es un error, es lo
  esperado.

### Validaciones (V0.2)

Cualquier parametro (de cualquier `source`) puede llevar anotaciones de Bean Validation
reconocidas (ver "Validaciones" mas abajo); se capturan en `Parameter.validations`.

## DTOs (V0.2)

El Analyzer indexa todas las clases y enums de los archivos que pudo parsear como AST (por nombre
simple) y resuelve referencias de tipo hacia esa estructura cuando aparecen como cuerpo de
peticion (`@RequestBody`) o como cuerpo de respuesta (ver "Response" mas abajo), incluyendo:

- Campos (`Field`): nombre, tipo (texto reconstruido, con genericos y nombres calificados), si es
  una coleccion de un unico argumento (`List`/`Set`/`Collection`/`Iterable`/`Optional`),
  validaciones, y el DTO anidado resuelto (si el tipo del campo tambien es una clase/enum del
  proyecto).
- Enums: se representan con `kind = "enum"` y sus constantes.
- Campos `static` se excluyen (no forman parte de la forma serializada de una instancia).

**Reglas de evidencia aplicadas a la resolucion de DTOs** (regla fundamental de V0.2, ver arriba):

- Si el mismo nombre simple de clase/enum aparece en **mas de un archivo** del proyecto, es
  ambiguo: el Analyzer **no elige uno al azar**. Devuelve `None` y registra un `Diagnostic`
  (`code="DTO_NAME_AMBIGUOUS"`, severidad `WARNING`).
- Si dos DTOs se referencian mutuamente (ciclo), la expansion anidada se detiene en el punto de
  ciclo (sin recursion infinita) y se registra un `Diagnostic` (`code="DTO_CYCLE_DETECTED"`,
  severidad `INFO`).
- No se realiza resolucion de `import`s ni de classpath: la indexacion es por nombre simple dentro
  del propio proyecto analizado. Un tipo de una libreria externa (incluida la libreria estandar de
  Java) nunca se resuelve como DTO.
- Genericos con mas de un argumento de tipo (p. ej. `Map<String, Object>`) no se desenvuelven: se
  conserva el texto del tipo, pero no se intenta adivinar cual argumento representa el DTO
  relevante.
- Solo se indexan clases/enums de archivos que el motor AST pudo parsear; un DTO definido en un
  archivo que cayo al fallback no puede resolverse como DTO anidado (limitacion documentada mas
  abajo).

## Validaciones (V0.2)

Se reconoce un conjunto ampliable de anotaciones de Bean Validation
(`analyzer/dto_analyzer.py::KNOWN_VALIDATIONS`): `@NotNull`, `@NotBlank`, `@NotEmpty`, `@Size`,
`@Min`, `@Max`, `@Email`, `@Pattern`, `@Positive`, `@PositiveOrZero`, `@Negative`,
`@NegativeOrZero`. Cada una se registra como `Validation` (nombre, argumentos crudos como texto,
evidencia), sin interpretar su semantica (el Analyzer no valida datos, solo registra que
validaciones existen en el codigo). No es necesario soportar todas las anotaciones de Bean
Validation existentes; agregar un nombre al conjunto es suficiente para reconocer una anotacion
adicional.

## Response (V0.2)

Para cada endpoint, se analiza el tipo de retorno del metodo Java:

- Si el tipo es `ResponseEntity<T>` (con un unico argumento de tipo), `wrapper = "ResponseEntity"`
  y el cuerpo se analiza a partir de `T`. En cualquier otro caso, `wrapper = None` y el cuerpo es
  el tipo de retorno mismo.
- El cuerpo se desenvuelve si es una coleccion de un unico argumento (mismo criterio que en DTOs),
  marcando `is_collection = True` y preservando el texto completo del tipo en `body_type`.
- Si el tipo (desenvuelto) corresponde a un DTO del proyecto, `Response.dto` contiene su
  estructura resuelta.
- Si el metodo retorna `void`, `wrapper` y `body_type` quedan en `None` explicitamente (no se
  inventa un cuerpo vacio como si fuera evidencia de un contrato real).
- `@ResponseStatus` (si esta presente en el metodo) se captura como texto en `Response.status`
  (p. ej. `"HttpStatus.CREATED"`), sin interpretar su significado numerico.

## Security (V0.2)

Se captura evidencia minima de `@PreAuthorize` y `@Secured`, tanto a nivel de clase (aplica a
todos los endpoints del controller) como de metodo, como texto (p. ej.
`"PreAuthorize(hasRole('ADMIN'))"`). El Analyzer **no** implementa un analizador de Spring
Security: solo registra que estas anotaciones existen y su expresion literal, no evalua reglas de
autorizacion.

## Evidencia

Ver `docs/09-Auditoria.md`. `Evidence` (V0.2) incluye `file`, `line`, `symbol` y `type`, y se usa
consistentemente para endpoints, controllers, parametros, DTOs, campos, validaciones y respuestas.

## Metadata

La salida del Analyzer es `AnalysisResult` (`analyzer/models.py`): `endpoints`, `controllers`,
`files_analyzed`, `warnings` (compatibilidad V0.1) y `diagnostics` (V0.2). Ver
`docs/14-Glosario.md`.

## Limitaciones conocidas (V0.2)

Del motor AST (`javalang`):

- `javalang` no tiene releases desde marzo de 2020 y **no soporta sintaxis Java posterior**
  (verificado: falla al parsear `record`). Un archivo con esa sintaxis cae al motor de fallback
  para todo el archivo, perdiendo las capacidades exclusivas del motor AST (DTOs, validaciones,
  response, headers, security) para ese archivo especifico.
- Un unico error de sintaxis en cualquier parte de un archivo hace fallar el parseo de **todo el
  archivo** (no solo la construccion afectada); en ese caso se recurre al motor de fallback, que
  tiene su propia limitacion conocida de V0.1 (una clase cuyo propio cuerpo no cierra correctamente
  no se recupera en absoluto).
- No se realiza resolucion de `import`s/classpath: nombres de tipo ambiguos entre archivos del
  proyecto no se resuelven (ver "DTOs" arriba).
- Genericos con mas de un argumento de tipo no se desenvuelven.
- No se soportan atributos de `@RequestMapping` distintos de `value`/`path`/`method`/
  `consumes`/`produces` (p. ej. `headers`, `params`).
- Metodos HTTP distintos de GET/POST/PUT/DELETE/PATCH (p. ej. HEAD, OPTIONS) no se reconocen.

Del motor de fallback (heredadas de V0.1, sin cambios — ver historial en el reporte de V0.1):
anotaciones fully-qualified, metodos package-private y `RequestMapping` con multiples metodos
**si estan resueltas cuando el archivo se analiza via el motor AST**; si ese mismo archivo cae al
fallback (por otro motivo), esas limitaciones de V0.1 vuelven a aplicar para ese archivo.

Estas limitaciones estan documentadas para evaluarse en V0.3 y siguientes; ver `docs/12-Roadmap.md`.
