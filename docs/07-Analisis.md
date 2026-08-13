# 07 — Analisis (Analyzer)

## Analisis de codigo

El Analyzer (`analyzer/`) realiza analisis **estatico** y **deterministico** del codigo fuente de
un microservicio Java/Spring Boot para producir evidencia estructurada sobre su API. No utiliza
ningun LLM: toda la informacion que produce proviene directamente del codigo fuente.

## Spring Boot

El Analyzer reconoce anotaciones de Spring MVC / Spring Boot sobre clases y metodos Java. No
ejecuta el codigo ni requiere un entorno Java: procesa el texto fuente de los archivos `.java`.

## Controllers

Se detectan clases anotadas con `@RestController`. El nombre del controller es el nombre de la
clase Java (`Endpoint.controller`).

Si una clase anotada con `@RestController` tambien tiene `@RequestMapping("/base")` a nivel de
clase, ese valor se usa como prefijo (`basePath`) de todos los endpoints definidos en sus metodos.

## Mappings

Dentro de una clase controller, se detectan metodos anotados con:

- `@GetMapping`, `@PostMapping`, `@PutMapping`, `@DeleteMapping`, `@PatchMapping`
- `@RequestMapping(method = RequestMethod.X, ...)` (forma generica)

El path de cada mapping se extrae del atributo `value`/`path` de la anotacion (o del valor
posicional, p. ej. `@GetMapping("/customers")`). El path final del endpoint es la concatenacion
del `basePath` de la clase (si existe) con el path del metodo.

Si un metodo esta anotado con `@RequestMapping` sin un atributo `method` explicito, el Analyzer
**no** asume un metodo HTTP por defecto (evitar inventar informacion, regla de IA 2): el mapping
se omite y se registra un warning en `AnalysisResult.warnings`.

## HTTP methods

Se detectan `GET`, `POST`, `PUT`, `DELETE`, `PATCH` a partir de la anotacion utilizada (ver
seccion anterior).

## Paths

Los paths se obtienen exclusivamente de los valores literales presentes en las anotaciones
(`@RequestMapping`, `@GetMapping`, etc.). No se infieren paths no declarados explicitamente.

## Parametros

Por cada parametro del metodo, el Analyzer determina su `source` segun la anotacion presente:

### Path variables (`@PathVariable`)

- `source = "path"`.
- Nombre: valor explicito de la anotacion (`@PathVariable("id")` o `@PathVariable(name="id")`) si
  existe; en caso contrario, el nombre del propio parametro Java (comportamiento estandar de
  Spring cuando la informacion de nombres de parametros esta disponible).
- `required`: `true` salvo que la anotacion indique explicitamente `required = false`.

### Query parameters (`@RequestParam`)

- `source = "query"`.
- Nombre: igual criterio que `@PathVariable`.
- `required`: `true` por defecto. Es `false` si la anotacion indica `required = false`, o si
  define `defaultValue` (comportamiento estandar de Spring: un valor por defecto implica que el
  parametro es opcional).

### Request body (`@RequestBody`)

- `source = "body"`.
- Nombre: nombre del parametro Java (no hay nombre explicito en la anotacion).
- Tipo: tipo Java declarado del parametro (p. ej. `CustomerRequest`).
- `required`: `true` por defecto. Es `false` si la anotacion indica explicitamente
  `required = false`.

## Evidencia

Cada `Endpoint` incluye un campo `evidence` con, como minimo, el archivo de origen
(`Evidence.file`). Esto deja preparado el diseño para trazabilidad completa en fases futuras (ver
`docs/09-Auditoria.md` y seccion 15 de `prompts/V0.1-foundation.md`). V0.1 no implementa
trazabilidad a nivel de linea de codigo de forma exhaustiva, pero el modelo es extensible sin
romper compatibilidad (`Evidence.line` existe como campo opcional).

## Metadata

La salida del Analyzer es la estructura `AnalysisResult` (`analyzer/models.py`), compuesta por una
lista de `Endpoint`, cada uno con su lista de `Parameter`. Ver `docs/14-Glosario.md` para las
definiciones de estos terminos y la seccion 14 de `prompts/V0.1-foundation.md` para el modelo de
referencia conceptual.

## Limitaciones conocidas (V0.1)

- El analisis se basa en expresiones regulares y balance de brackets/parentesis sobre el texto
  fuente, no en un Abstract Syntax Tree completo de Java. Es robusto frente a literales de texto
  y comentarios (se ignoran al balancear brackets), pero no cubre construcciones Java exoticas
  (por ejemplo, clases anonimas o anotaciones con expresiones complejas anidadas).
- No resuelve herencia entre controllers, ni anotaciones definidas mediante meta-anotaciones
  personalizadas.
- No analiza DTOs en profundidad: el tipo de un parametro es el texto literal declarado en la
  firma del metodo, no una resolucion completa de su estructura interna.
- Las anotaciones deben usarse por su nombre simple (`@RestController`, `@GetMapping`, ...), tal
  como se importan habitualmente en codigo Spring Boot real. No se reconocen anotaciones
  referenciadas por su nombre completamente calificado (p. ej.
  `@org.springframework.web.bind.annotation.RestController`).
- La deteccion de metodos requiere un modificador de acceso explicito (`public`, `private` o
  `protected`) antes del tipo de retorno; esto evita falsos positivos al escanear el cuerpo de los
  metodos y es consistente con la convencion de Spring Boot de declarar los metodos de un
  controller como `public`.

Estas limitaciones son aceptables para V0.1 (Foundation) y quedan documentadas para ser evaluadas
en V0.2 (Spring Boot Analyzer), donde el Analyzer se profundiza.
