# 03 — Arquitectura

## Vision general

La arquitectura es conceptual y por capas: cada componente tiene una responsabilidad unica y se
comunica con el siguiente mediante estructuras de datos bien definidas, no mediante acoplamiento
directo de implementacion.

```text
Skill-Documentation-AI
|
+-- Analyzer
|
+-- Skill
|
+-- LLM Provider
|
+-- OpenAPI Generator
|
+-- Validator
|
+-- Auditor
|
+-- CLI
|
+-- Integraciones futuras
```

Relacion conceptual entre componentes:

```text
                    Skill-Documentation-AI
                             |
              +--------------+--------------+
              |                             |
           Analyzer                       Skill
              |                             |
              +--------------+--------------+
                             v
                       LLM Provider
                             |
               +-------------+-------------+
               v             v             v
            Claude        Gemini        OpenAI
               |             |             |
               +-------------+-------------+
                             v
                    OpenAPI Generator
                             v
                         Validator
                             v
                          Auditor
                             v
                      OpenAPI YAML/JSON
```

**Importante:** esta arquitectura es conceptual para todo el proyecto. A la fecha (V0.6), estan
implementados el **Analyzer** (V0.1, ampliado en V0.2), el **OpenAPI Generator** (V0.3), el
**OpenAPI Quality Validator** (V0.4), la **CLI** (V0.5, `spring-doc`) y la **infraestructura de
LLM Providers** (V0.6: configuracion, errores, seleccion por nombre, y un `FakeProvider`
determinista — sin ningun provider comercial concreto). El resto de componentes (Skill como motor
ejecutable, Auditor, Integraciones) permanecen delimitados y documentados, pero no implementados
(ver estado por componente mas abajo).

## Componentes

### Analyzer (implementado en V0.1, ampliado en V0.2)

- **Responsabilidad:** analizar codigo fuente Java/Spring Boot y producir evidencia y metadata
  estructurada sobre la API (controllers, endpoints, metodos HTTP, parametros, DTOs, respuestas,
  validaciones, seguridad, consumes/produces — ver `docs/07-Analisis.md`).
- **Entrada:** ruta a un proyecto Java/Spring Boot.
- **Salida:** estructuras serializables (`Endpoint`, `Parameter`, `Controller`, `DTO`, `Field`,
  `Response`, `Validation`, `Diagnostic`) agregadas en `AnalysisResult`.
- **Dependencias externas:** `javalang` (parser AST de Java, ver decision arquitectonica 1 mas
  abajo). Ninguna dependencia hacia otros componentes del sistema (Skill, LLM Provider,
  Generator, Validator, Auditor): sigue siendo la base del pipeline, sin conocer nada de lo que
  hay rio abajo.
- **Estructura interna (V0.2):**
  - `analyzer/scanner.py` — descubrimiento de archivos `.java` (sin cambios desde V0.1).
  - `analyzer/ast_backend.py` — aisla la dependencia `javalang`: parseo, traduccion de sus
    excepciones a `AstParseError`, y utilidades genericas de extraccion de valores (tipos,
    argumentos de anotacion, literales). Ningun otro modulo invoca `javalang` directamente.
  - `analyzer/dto_analyzer.py` — indice de clases/enums del proyecto y resolucion de DTOs
    (campos, validaciones, anidamiento, colecciones, deteccion de ambiguedad y ciclos).
  - `analyzer/ast_analyzer.py` — construye Controllers/Endpoints/Parameters/Response/Security a
    partir de una unidad de compilacion ya parseada y del indice de DTOs. Motor principal.
  - `analyzer/spring_boot_analyzer.py` — motor de V0.1 (regex + balanceo de brackets), **sin
    modificar**. Actua como motor de *fallback* por archivo (ver mas abajo).
  - `analyzer/models.py` — modelo de datos (ver `docs/07-Analisis.md` y este documento, seccion
    "Modelo de datos").
  - `analyzer/__init__.py::analyze_project` — orquesta ambos motores.
- Detalle en `docs/07-Analisis.md`.

### Skill (estructura definida en V0.1)

- **Responsabilidad:** encapsular el conocimiento sobre como documentar APIs correctamente:
  reglas, principios, formato OpenAPI, manejo de incertidumbre.
- **Entrada:** evidencia/metadata producida por el Analyzer.
- **Salida:** instrucciones/comportamiento esperado para el LLM Provider.
- **Dependencias:** consume la salida del Analyzer; no depende de ningun LLM concreto.
- Detalle en `docs/04-Skill.md`.

### LLM Provider (interfaz definida en V0.1, infraestructura V0.6, primer provider real en V0.7)

- **Responsabilidad:** exponer una interfaz uniforme para invocar un LLM, independientemente del
  proveedor concreto (Claude, Gemini, OpenAI, u otros compatibles).
- **Entrada:** prompt/contexto construido a partir de la Skill y la evidencia.
- **Salida:** contenido generado por el LLM (texto/estructura, interpretado por el Generator).
- **Dependencias:** ninguna dependencia arquitectonica de componentes superiores hacia un
  proveedor especifico. Ver `docs/06-LLM.md`.
- **Contrato (`providers/base.py`):** `LLMProvider.generate(self, prompt: str) -> str`. Sin
  cambios desde V0.1 — ni V0.6 ni V0.7 modificaron esta interfaz.
- **Estructura interna:**
  - `providers/config.py` — `ProviderConfig` (dataclass inmutable: `provider`, `model`,
    `api_key`, `timeout` desde V0.7), con `from_env()` leyendo variables de entorno
    (`SPRING_DOC_LLM_PROVIDER`/`_MODEL`/`_API_KEY`/`_TIMEOUT`). `api_key` nunca aparece en
    `repr()`/`str()`.
  - `providers/errors.py` — jerarquia propia (`LLMProviderError` + 7 subclases) para que ningun
    consumidor necesite conocer excepciones de un SDK concreto ni de `urllib`.
  - `providers/fake.py` — `FakeProvider`: implementacion determinista sin red ni credenciales,
    pensada para tests (V0.6).
  - `providers/anthropic.py` — `AnthropicProvider` (V0.7): primer provider LLM real, contra el
    endpoint de Mensajes de Anthropic, implementado solo con `urllib.request`/`urllib.error`/
    `json` (stdlib, sin el SDK `anthropic`). Requiere `api_key`/`model` explicitos (sin modelo por
    defecto), falla en la construccion si faltan. Traduce toda excepcion de `urllib` y toda
    respuesta malformada a `providers.errors`.
  - `providers/registry.py` — `get_provider(config) -> LLMProvider`: seleccion por nombre sobre
    un `dict[str, Callable]` (deliberadamente no una clase Factory ni un sistema de plugins).
    Resuelve `"fake"` → `FakeProvider`, `"anthropic"` → `AnthropicProvider`.
- **Estado en V0.7:** infraestructura completa y probada, con un provider comercial real
  (`AnthropicProvider`) ademas del `FakeProvider` de V0.6 (decision de alcance explicita: un solo
  provider real, ver `docs/13-Versionado.md` seccion "V0.6.0 -> V0.7.0" y decision arquitectonica
  12 mas abajo). Ningun otro componente (`analyzer/`, `generators/`, `validator/`, `cli/`,
  `skill/`, `skills/`) importa `providers/` — verificado por grep y por tests de aislamiento.
  Ningun consumidor real usa todavia `AnthropicProvider` (eso es V0.8).

### OpenAPI Generator (implementado en V0.3)

- **Responsabilidad:** transformar `analyzer.AnalysisResult` en un documento OpenAPI 3.0.3
  (`generators.generate`), y serializarlo a JSON/YAML (`generators.to_json`/`generators.to_yaml`).
- **Entrada:** exclusivamente el modelo publico de `analyzer` (`AnalysisResult`, `Endpoint`,
  `Parameter`, `Response`, `DTO`, `Field`, `Validation`, `Diagnostic`). No analiza Java.
- **Salida:** `dict` (documento OpenAPI) + `list[Diagnostic]` propios del Generator.
- **Dependencias externas:** `PyYAML` (unicamente para serializacion YAML). Ninguna dependencia
  hacia `javalang` ni hacia los motores internos del Analyzer (`spring_boot_analyzer.py`,
  `ast_analyzer.py`, `dto_analyzer.py`, `scanner.py` — prohibido explicitamente por el Scope Lock
  de V0.3).
- **Estructura interna:**
  - `generators/openapi_types.py` — parseo del texto de tipo producido por el Analyzer, tabla de
    tipos Java -> OpenAPI, mapeo de Bean Validation a keywords de schema.
  - `generators/openapi_schemas.py` — construccion de `components.schemas` a partir de `DTO`,
    con deduplicacion por nombre (`$ref`).
  - `generators/openapi_generator.py` — orquestador: paths/operations/parameters/requestBody/
    responses/security/operationId/orden deterministico/serializacion.
  - `generators/__init__.py` — API publica (`generate`, `to_json`, `to_yaml`, `OPENAPI_VERSION`).
- Detalle completo (incluidas las politicas conservadoras de responses/security/tipos no
  resueltos) en `docs/05-OpenAPI.md`.
- **No modifico ningun archivo de `analyzer/`** durante su implementacion (ver decision 8 mas
  abajo): la Regla de la seccion 6 de `prompts/V0.3-OPENAPI-GENERATOR.md` exigia demostrar que
  cada dato faltante era realmente necesario antes de tocar el modelo del Analyzer, y en ningun
  caso lo fue.

### OpenAPI Quality Validator (implementado en V0.4)

- **Responsabilidad:** analizar un documento OpenAPI 3.0.3 ya construido (`validator.validate`)
  y clasificar hallazgos en ERROR/WARNING/INFO. No analiza Java, no llama al Analyzer ni al
  Generator, y nunca modifica el documento recibido (solo lectura).
- **Entrada:** un `dict` (documento OpenAPI), o texto JSON/YAML (`validate_json`/`validate_yaml`).
- **Salida:** `list[Diagnostic]`, reutilizando `analyzer.Diagnostic`/`DiagnosticSeverity`/
  `Evidence` sin ninguna modificacion a `analyzer/models.py` (`Evidence.file` como JSON Pointer
  RFC 6901, ver `docs/05-OpenAPI.md`).
- **Dependencias externas:** ninguna nueva; reutiliza `PyYAML` (ya presente desde V0.3) para
  `validate_yaml`. Sin libreria de validacion OpenAPI externa (Scope Lock explicito de V0.4).
- **Estructura interna:**
  - `validator/openapi_rules.py` — funciones de regla agrupadas por seccion del documento
    (raiz, paths/metodos, operationId, parameters, requestBody, responses, schemas/enum, `$ref`,
    components, security).
  - `validator/openapi_validator.py` — orquestador: `validate`/`validate_json`/`validate_yaml`,
    recorrido deterministico del documento.
  - `validator/__init__.py` — API publica.
- Detalle completo (catalogo de reglas, severidades, politica de `$ref` externos, heuristicas de
  deteccion de convenciones del Generator) en `docs/05-OpenAPI.md`.
- **No se modifico `analyzer/models.py` ni `generators/`** durante su implementacion (mismo
  proceso obligatorio que V0.3, ver decision 9 mas abajo).
- **Nota de nomenclatura:** V0.1 habia reservado el paquete `validators/` (plural) como
  placeholder generico para un futuro "Validator". La directriz real de V0.4 nombra el paquete
  nuevo `validator/` (singular). Ambos coexisten: `validators/` permanece exactamente como
  placeholder vacio (sin uso, no se elimino sin autorizacion); `validator/` es el paquete
  funcional real de V0.4.

### Auditor (no implementado)

- **Responsabilidad futura:** evaluar trazabilidad, evidencia y confianza (confidence) de la
  documentacion generada.
- El roadmap original lo agrupaba junto con el Validator en V0.4; la directriz real de V0.4 acoto
  el alcance unicamente al OpenAPI Quality Validator (ver arriba). El Auditor queda sin version
  asignada, pendiente de una futura directriz. Ver `docs/09-Auditoria.md` y `docs/12-Roadmap.md`.

### CLI (implementado en V0.5)

- **Responsabilidad:** exponer el pipeline `analyzer -> generators -> validator` como herramienta
  de linea de comandos (`spring-doc`), sin reimplementar analisis, generacion ni validacion.
- **Entrada:** argumentos de linea de comandos (`analyze <project>`, `generate <project>`,
  `validate <openapi-file>`, mas opciones).
- **Salida:** resumen humano por stdout/stderr, o reporte estructurado (`--json`) — nunca el
  documento OpenAPI embebido en el reporte JSON, solo una referencia a su ruta (`outputs`).
- **Dependencias externas:** ninguna nueva; `argparse` es libreria estandar (decision de Fase 2,
  ver mas abajo). Ninguna dependencia hacia `javalang` ni hacia los modulos internos de Analyzer/
  Generator/Validator: solo sus APIs publicas (`analyzer.analyze_project`,
  `generators.generate`/`to_json`/`to_yaml`, `validator.validate`/`validate_json`/`validate_yaml`).
- **Estructura interna:**
  - `cli/main.py` — parser `argparse` (subcomandos `analyze`/`generate`/`validate`, `--version`),
    despacho, calculo de exit code, manejo de errores de uso vs. errores internos.
  - `cli/commands.py` — orquestacion: llama a `analyzer`/`generators`/`validator` y produce un
    resultado interno (`AnalyzeOutcome`/`GenerateOutcome`/`ValidateOutcome`); calculo de
    conteos por severidad y del `status` (`ok`/`error`, sensible a `--strict`).
  - `cli/output.py` — dos formateadores independientes (humano y `--json`), sin logica de negocio.
  - `cli/errors.py` — `CliUsageError`, unica excepcion propia de la CLI (errores de entrada del
    usuario, exit code 2).
- Detalle completo (opciones, exit codes, formas exactas del reporte `--json`) en
  `prompts/V0.5—CLI-&-DEVELOPER-EXPERIENCE.md` (reportes de Fase 2/3) y `docs/13-Versionado.md`.
- **No se modifico `analyzer/`, `generators/` ni `validator/`** durante su implementacion (mismo
  proceso obligatorio que V0.3/V0.4, ver decision 10 mas abajo).

### Integraciones futuras (no implementadas en V0.1)

- Integracion con Confluence y con el proyecto Python existente. Reservado para V0.7. Ver
  `docs/11-Integracion.md`.

### `skills/spring-doc/SKILL.md` (agregado en V0.6, no es un componente del pipeline)

- **Responsabilidad:** conocimiento/proceso, independiente de LLM/agente/herramienta, para
  documentar el API HTTP de un microservicio Java/Spring Boot leyendo su codigo fuente
  directamente (que buscar en controllers/mappings/parametros/DTOs/respuestas/seguridad, como
  tratar la ambiguedad y la informacion faltante, como estructurar el resultado). **No depende de
  `spring-doc` (la CLI), no la requiere, y no describe la arquitectura interna de este proyecto**
  (`providers/`, `analyzer/`, `generators/`, `validator/`, `cli/` no se mencionan dentro del
  archivo — verificado por test). Puede mencionar `spring-doc` una vez, de forma generica, como
  herramienta externa opcional, nunca como requisito. No es codigo Python, no se importa, no
  participa del pipeline `Analyzer -> Skill -> LLM Provider -> Generator -> Validator -> Auditor
  -> CLI` — es un documento de conocimiento autocontenido, pensado para poder copiarse solo y
  entregarse a cualquier LLM junto con un proyecto Java/Spring Boot.
- **Nota de nomenclatura (evitar confusion con `skill/`, singular):** `skills/spring-doc/` (plural)
  **no** es el componente conceptual "Skill" de la arquitectura del producto descrito arriba
  (`skill/`, singular, desde V0.1 — conocimiento para que un LLM Provider documente APIs a partir
  de evidencia ya extraida por el Analyzer, ver `docs/04-Skill.md`). Son artefactos distintos con
  un supuesto de entrada diferente: `skill/` asume metadata ya extraida por el Analyzer de este
  proyecto; `skills/spring-doc/SKILL.md` asume que el LLM lee el codigo fuente Java directamente,
  sin ningun Analyzer de por medio. Conviven sin relacion de dependencia entre si.

## Flujo de informacion (V0.4)

```text
Codigo fuente Java/Spring Boot
        |
        v
   analyzer.scanner              (descubre archivos .java)
        |
        v
   analyzer.ast_backend.parse_file   (intenta AST por archivo)
        |                    \
        | (exito)             \ (AstParseError)
        v                       v
analyzer.dto_analyzer      analyzer.spring_boot_analyzer
  build_class_index          (motor de fallback V0.1, sin cambios)
        |                       |
        v                       |
analyzer.ast_analyzer            |
  analyze_compilation_unit       |
        |                       |
        +-----------+-----------+
                    v
   analyzer.models.AnalysisResult   (metadata estructurada, serializable)
        |
        v
   generators.generate(result)      (V0.3 — OpenAPI Generator)
        |
        v
   documento OpenAPI (dict) -> generators.to_json / generators.to_yaml
        |
        v
   validator.validate(documento)    (V0.4 — Quality Validator, solo lectura)
        |
        v
   list[Diagnostic]   (ERROR/WARNING/INFO sobre el documento)
```

El resultado del Analyzer fue diseñado en V0.1/V0.2 para ser consumido por un futuro OpenAPI
Generator sin necesidad de romper compatibilidad (ver `docs/07-Analisis.md` y
`docs/13-Versionado.md`); V0.3 confirma esa expectativa: no fue necesario modificar ningun campo
de `analyzer/models.py` para implementar el Generator. V0.4 confirma lo mismo para el Validator:
tampoco fue necesario modificar `analyzer/models.py` (reutiliza `Diagnostic`/`Evidence` tal como
estaban) ni `generators/` (el Validator consume el `dict` de salida, no llama a `generate()`).

## Limites entre componentes

- El Analyzer **no** conoce la Skill, el LLM Provider, ni OpenAPI. Solo produce metadata.
- La Skill **no** depende de un LLM concreto ni contiene instrucciones exclusivas de Claude.
- El LLM Provider es una interfaz; ningun componente superior debe importar un SDK de un
  proveedor especifico directamente.
- `validators/` (placeholder, sin uso desde V0.1) existe como paquete reservado sin logica de
  negocio. `generators/` (V0.3) y `validator/` (V0.4) ya tienen implementacion real.
- Dentro del Analyzer (V0.2): unicamente `analyzer/ast_backend.py` importa `javalang`. Los demas
  modulos (`ast_analyzer.py`, `dto_analyzer.py`, `__init__.py`) solo conocen el resultado de sus
  utilidades (texto, dicts, nodos ya normalizados via `annotation_args`/`literal_text`/
  `type_to_text`), salvo por el recorrido directo del arbol (`javalang.tree.*` para isinstance),
  que se acepta como acoplamiento controlado (ver decision 5 mas abajo).
- (V0.3) El Generator (`generators/`) **no** importa `javalang`, `analyzer.spring_boot_analyzer`,
  `analyzer.ast_analyzer`, `analyzer.dto_analyzer` ni `analyzer.scanner` — solo el modelo publico
  de `analyzer` (verificado por grep sobre `generators/*.py`, ver reporte de revision de V0.3).
  Este limite es la contraparte, del lado del Generator, del limite ya existente "el Analyzer no
  conoce la Skill/LLM/OpenAPI": ninguno de los dos componentes conoce los detalles internos del
  otro, solo la estructura de datos que los conecta (`AnalysisResult`).
- (V0.4) El Validator (`validator/`) **no** importa `javalang` ni ningun modulo interno del
  Analyzer, y tampoco importa `generators/` (no llama a `generate()`). El Generator, a su vez, no
  llama al Validator automaticamente. Ambos son componentes independientes que solo comparten el
  `dict` del documento OpenAPI como interfaz (verificado por grep sobre `validator/*.py`).
- (V0.5) La CLI (`cli/`) **no** importa `javalang` ni ningun modulo interno de Analyzer
  (`ast_analyzer`, `ast_backend`, `dto_analyzer`, `spring_boot_analyzer`, `analyzer.scanner`),
  Generator (`openapi_types`, `openapi_schemas`) ni Validator (`openapi_rules`) — solo las APIs
  publicas de los tres paquetes (verificado por grep sobre `cli/*.py`, cubierto ademas por un test
  de regresion en `tests/test_cli_integration.py`). Es la misma disciplina de limites ya aplicada
  en V0.3/V0.4, extendida a la capa de orquestacion.
- (V0.6) `providers/` **no** es importado por `analyzer/`, `generators/`, `validator/` ni `cli/`
  — el limite se verifica ahora en ambas direcciones (ya se sabia que el Analyzer no conoce a la
  Skill/LLM Provider; V0.6 confirma que tampoco lo hacen Generator/Validator/CLI, verificado por
  grep y por `tests/test_providers_isolation.py`). Ningun componente existente adquirio una
  dependencia implicita sobre Providers.
- (V0.7) El mismo limite se sostiene con `AnthropicProvider` disponible: agregar un provider real
  no cambio el aislamiento en absoluto — `analyzer/`, `generators/`, `validator/`, `cli/`,
  `skill/` y `skills/` siguen sin referenciar `providers/` (verificado por grep, extendido ahora
  tambien a `skill/`/`skills/`), y el proyecto funciona igual sin ninguna variable
  `SPRING_DOC_LLM_*` configurada. Instalar el paquete o importar `providers/` nunca dispara una
  llamada de red (verificado por test dedicado que mockea `urllib.request.urlopen` y comprueba que
  no se invoca solo por importar).

## Decisiones arquitectonicas relevantes

1. **V0.1 — Analisis deterministico basado en expresiones regulares y balance de
   brackets/parentesis**, en lugar de un parser Java completo. Motivo original: evitar una
   dependencia adicional pesada, suficiente para detectar anotaciones Spring MVC basicas.
   **Reevaluado en V0.2** (ver punto 2): se mantiene como motor de *fallback*, ya no como unico
   motor.

2. **V0.2 — Motor hibrido: `javalang` (AST) como motor principal, con el motor regex de V0.1 como
   *fallback* por archivo.** Evaluacion formal documentada en el reporte de Fase 2 de V0.2
   (`prompts/V0.2-ADVANCED-SPRING-BOOT-ANALYZER.md`), con pruebas directas contra el codigo real
   del proyecto:
   - `javalang` (pura Python, MIT, sin binarios) resuelve directamente las limitaciones de V0.1
     mas relevantes para las capacidades exigidas por V0.2 (anotaciones fully-qualified, metodos
     package-private, `RequestMapping` con multiples metodos, genericos, atributos de anotacion
     estructurados) con una superficie de codigo propio mucho menor que extender el regex a mano.
   - Se descarto reemplazar el regex por completo: `javalang` falla el archivo **completo** ante
     cualquier error de sintaxis (verificado), y no soporta sintaxis Java posterior a 2020
     (verificado con `record`; sin releases desde marzo de 2020). Un reemplazo total habria roto
     la garantia de V0.1 de tolerar codigo parcialmente malformado
     (`test_malformed_class_without_closing_brace_does_not_crash` y el nuevo
     `test_fallback_used_for_unparseable_file_recovers_valid_method`).
   - Se descarto `tree-sitter` (alternativa con recuperacion de errores nativa y mantenimiento
     activo, tambien evaluada con pruebas reales) porque su API es un arbol de sintaxis concreto
     generico, sin semantica Java de alto nivel: hubiese requerido reconstruir a mano gran parte
     de lo que `javalang` ya da (anotaciones con atributos nombrados, modificadores, genericos),
     aumentando el modulo mas de lo justificado para el alcance de V0.2 (seccion 7 de la
     directriz).
   - Consecuencia practica verificada: el motor de fallback recupera endpoints validos de
     archivos con errores de sintaxis *localizados* (p. ej. un metodo con parentesis sin cerrar
     entre otros metodos validos), pero no recupera nada si la clase controller en si no cierra
     (limitacion que ya existia en V0.1 y que el hibrido no resuelve ni empeora).

3. **`analyzer/ast_backend.py` aisla `javalang`**, pero **no** encapsula por completo la forma del
   AST: `ast_analyzer.py` y `dto_analyzer.py` recorren directamente tipos de `javalang.tree` (via
   `isinstance`/atributos). Encapsular completamente el AST detras de una capa de nodos propios
   se evaluo y se descarto por ser una abstraccion no justificada para el alcance de V0.2 (regla
   global 12 de V0.1: no introducir abstracciones innecesarias). El limite que si se mantiene es:
   la invocacion del parser, la traduccion de excepciones, y las utilidades genericas de
   extraccion de valores viven unicamente en `ast_backend.py`.

4. **Regla de evidencia sobre inferencia (V0.2, fundamental para el proyecto):** ante informacion
   que no puede determinarse con confianza suficiente (nombre de DTO ambiguo entre archivos,
   referencia ciclica entre DTOs, mapping sin metodo HTTP resoluble, atributo de anotacion en una
   forma no reconocida), el Analyzer **nunca elige un valor plausible**: el dato queda `None`/
   vacio y se registra un `Diagnostic`. Esta regla es la razon de ser de `Diagnostic`
   (`docs/09-Auditoria.md`) y aplica a todo el Analyzer, no solo al motor AST. Motivo: la
   metadata producida aqui sera consumida por un LLM en fases futuras para generar documentacion;
   presentar una inferencia como hecho contaminaria esa documentacion con informacion no
   verificable.

5. **Sin CLI hasta V0.5**: entre V0.1 y V0.4 el Analyzer/Generator/Validator se consumian
   unicamente como libreria Python, para evitar adelantar el roadmap. V0.5 implementa la CLI
   (ver punto 10 mas abajo); el roadmap original la ubicaba en V0.6 (reasignado, ver
   `docs/12-Roadmap.md`).

6. **`providers/` solo define la interfaz** (clase base abstracta), sin implementaciones
   concretas, para evitar acoplamiento a un LLM especifico y cumplir el Scope Lock. Sin cambios
   en V0.2 (seccion 15 de la directriz V0.2 lo reitera explicitamente).

7. **`validators/` (plural) se mantiene vacio/placeholder**: la directriz real de V0.4 nombro su
   paquete nuevo `validator/` (singular, ver punto 9), no `validators/`. `generators/` dejo de ser
   placeholder en V0.3 (ver punto 8).

8. **V0.3 — OpenAPI 3.0.3, sin modificar el Analyzer.** Antes de implementar, se aplico
   sistematicamente el proceso obligatorio de la seccion 6 de
   `prompts/V0.3-OPENAPI-GENERATOR.md` (identificar dato faltante -> verificar si ya existe en el
   modelo -> determinar si puede obtenerse sin modificar el Analyzer -> solo entonces proponer
   ampliacion) para cada necesidad de OpenAPI (operationId, codigo de status numerico, tags,
   mapeo de tipos). En todos los casos la informacion pudo derivarse en el Generator a partir de
   campos ya existentes (`java_method`, `controller`, `method`, `endpoint`, el texto de
   `Response.status`, el texto de `Parameter.type`/`Field.type`/`Response.body_type`) mas tablas
   de conversion propias del Generator (nombres `HttpStatus` -> codigo, tipo Java -> tipo
   OpenAPI). **No se modifico `analyzer/models.py` ni ningun otro archivo de `analyzer/`.**
   Version elegida: **OpenAPI 3.0.3** (no 3.1.x, revirtiendo la aspiracion escrita en V0.1) por
   mayor compatibilidad de herramientas y schemas mas simples de construir a mano sin una
   libreria de validacion. Dependencia nueva: `PyYAML` (MIT, solo para serializacion YAML; JSON
   usa la libreria estandar). Ver `docs/05-OpenAPI.md` para el detalle completo de las politicas
   conservadoras (responses sin status, security sin scheme concreto, tipos no resueltos).

9. **V0.4 — Validator propio y acotado, sin libreria externa, sin modificar Analyzer ni
   Generator.** Mismo proceso obligatorio de la seccion 6 aplicado a la unica necesidad de datos
   identificada (ubicacion del hallazgo dentro del documento): se resolvio reutilizando
   `Evidence.file` como JSON Pointer (RFC 6901) por convencion, sin agregar ningun campo a
   `analyzer/models.py`. Arquitectura elegida: modular (`validator/openapi_rules.py` +
   `validator/openapi_validator.py`), replicando el patron ya usado por `generators/` (orquestador
   separado de las funciones de regla). Se descarto explicitamente cualquier libreria de
   validacion OpenAPI (`openapi-spec-validator`, `jsonschema`, etc. — Scope Lock V0.4). El
   catalogo de reglas incluye ~15 extensiones propuestas mas alla de los ejemplos literales de la
   directriz (autorizadas explicitamente: `OPENAPI_PARAMETER_SCHEMA_CONTENT_CONFLICT`,
   `OPENAPI_PARAMETER_DUPLICATE`, `OPENAPI_REQUIRED_FIELD_UNDEFINED`,
   `OPENAPI_COMPONENT_NAME_INVALID`, deteccion de convenciones fijas del Generator V0.3 por
   comparacion literal de texto, entre otras), documentadas explicitamente como tales para no
   confundirlas con requisitos literales de la directriz. Ver `docs/05-OpenAPI.md` para el
   catalogo completo y las severidades.

10. **V0.5 — CLI con `argparse` (stdlib), sin dependencias nuevas, sin modificar Analyzer/
    Generator/Validator.** Evaluado formalmente en Fase 2 (`prompts/V0.5—CLI-&-DEVELOPER-
    EXPERIENCE.md`): con solo 3 subcomandos y un puñado de opciones, `click`/`typer` no se
    justifican frente a la prioridad explicita de minima dependencia; `argparse` es stdlib,
    multiplataforma y suficiente. Estructura elegida: tres subcomandos independientes
    (`analyze`/`generate`/`validate`) mas una unica variante combinada (`analyze --openapi`, que
    ejecuta Analyzer -> Generator -> Validator en una sola invocacion), en vez de un cuarto
    subcomando `pipeline`/`all` no solicitado. Decision explicita sobre semantica de opciones:
    `--format json|yaml` controla el **artefacto** OpenAPI generado; `--json` controla el
    **reporte** de la CLI sobre la operacion (conteos por severidad y, cuando aplica, la ruta del
    artefacto bajo `outputs`) — nunca el mismo concepto, y el reporte `--json` nunca incluye el
    documento OpenAPI embebido. Cuando `--json` se combina con generacion de OpenAPI sin
    `--output`, es un error de uso (exit 2): el reporte JSON y el documento no pueden compartir
    stdout. Exit codes deterministas: `0` exito, `1` diagnostics que fallan el run (`ERROR`
    siempre, `WARNING` solo bajo `--strict`), `2` error de uso, `3` error interno inesperado (sin
    traceback). `--output` crea directorios padres faltantes (`mkdir -p` implicito) en vez de
    fallar, ya que no es una operacion destructiva y evita friccion innecesaria; sigue fallando
    como error de uso si el destino no es escribible (p. ej. un directorio existente). El proceso
    obligatorio de la seccion 6 (aplicado tambien en V0.3/V0.4) confirmo que el unico dato
    "nuevo" que necesitaba la CLI (conteo de DTOs distintos para el resumen) podia derivarse
    integramente de la API publica existente (`Parameter.dto`/`Response.dto`/`Field.nested_dto`)
    sin modificar `analyzer/models.py`.

11. **V0.6 — Infraestructura de LLM Providers sin provider comercial, sin dependencias nuevas, sin
    modificar Analyzer/Generator/Validator/CLI.** Evaluado en Fase 2
    (`prompts/V0.6—LLM-PROVIDERS-&-AI-FOUNDATION.md`): se mantuvo `LLMProvider(ABC)` (V0.1) sin
    cambios en vez de migrar a `typing.Protocol` (perderia la verificacion en tiempo de ejecucion
    de la que ya dependia un test existente) o introducir un sistema de plugins (no justificado,
    la directriz exige explicitamente no asumir un patron sin justificarlo). La seleccion de
    provider por nombre se resolvio con un `dict[str, Callable]` (`providers/registry.py`) en vez
    de una clase Factory — superficie minima que cubre "seleccion del provider" sin introducir un
    framework. La forma de la respuesta se mantuvo como `str` (no una `LLMResponse` con
    metadata/usage) por ausencia de un consumidor real que lo necesite hoy; se puede ampliar mas
    adelante sin romper el contrato. Configuracion via variables de entorno
    (`SPRING_DOC_LLM_PROVIDER`/`_MODEL`/`_API_KEY`) en vez de `.env` (evita la dependencia
    `python-dotenv`) o un archivo YAML/JSON de config (sin necesidad demostrada). Se evaluo
    explicitamente implementar un `AnthropicProvider` real via `urllib` (stdlib, sin el SDK
    `anthropic`) — costo en dependencias nulo — pero se descarto por decision explicita del
    responsable del proyecto, priorizando la superficie minima justificada por la directriz
    (seccion 22: "la calidad de la abstraccion... es mas importante que la cantidad de providers
    implementados"); queda como trabajo futuro cuando exista un consumidor real. Se agrego ademas
    `skills/spring-doc/SKILL.md` (autorizado explicitamente junto con la Fase 3, fuera del alcance
    original de la directriz de V0.6, y corregido de alcance una vez implementado: la primera
    version documentaba como invocar la CLI `spring-doc`; a pedido explicito del responsable del
    proyecto se reescribio para ser un artefacto de conocimiento LLM-agnostico, agente-agnostico y
    motor-agnostico que ensena a documentar un microservicio Spring Boot leyendo su codigo fuente
    directamente, sin depender de `spring-doc` ni describir la arquitectura interna de este
    proyecto — ver seccion "Componentes" mas arriba para el detalle y la nota de nomenclatura
    frente a `skill/`, singular).

12. **V0.7 — `AnthropicProvider` real via stdlib, sin SDK, sin modificar el contrato de
    `LLMProvider` ni ningun otro componente.** La decision "sin provider real" de V0.6 (punto 11)
    se revierte explicitamente aqui, con autorizacion del responsable del proyecto: un solo
    provider real (no varios, "no se implementan multiples proveedores comerciales unicamente
    para demostrar compatibilidad" — misma prioridad que V0.6). Decisiones explicitas de Fase 2:
    - **Modelo obligatorio, sin default hardcodeado** (`InvalidModelError` si falta): un modelo
      por defecto se volveria silenciosamente obsoleto a medida que Anthropic publica modelos
      nuevos, y elegir uno no solicitado es una suposicion — mismo principio de evidencia que
      gobierna el Analyzer, aplicado ahora a la configuracion del provider. `InvalidModelError` se
      limita a la ausencia local del dato; un nombre de modelo que Anthropic rechace en tiempo
      real llega como HTTP 4xx y se traduce a `ProviderRequestError`, no a `InvalidModelError` —
      no hay forma de validar un nombre de modelo sin red ni una lista hardcodeada, igual de
      fragil que un default.
    - **Timeout con default seguro (60s) resuelto en el provider, no en `ProviderConfig`**:
      `ProviderConfig.timeout` (campo aditivo nuevo) solo transporta el valor configurado (o
      `None`); `AnthropicProvider` decide el default cuando no hay uno valido, nunca se pasa
      `timeout=None` a `urlopen` (evitaria un timeout de socket potencialmente indefinido).
    - **`max_tokens` fijo (1024), no configurable**: la API de Anthropic lo exige en cada request,
      pero la directriz no pidio exponerlo como opcion nueva — agregar esa superficie no
      solicitada violaria la regla de "no funcionalidades especulativas".
    - Todas las excepciones de `urllib` (`TimeoutError`, `HTTPError`, `URLError`) y toda respuesta
      malformada (JSON invalido, sin bloques de texto) se traducen a `providers.errors` dentro del
      propio provider — ningun detalle de `urllib` ni del formato de respuesta de Anthropic se
      propaga hacia el consumidor.
    - Ver `docs/13-Versionado.md` seccion "V0.6.0 -> V0.7.0" para el detalle completo del formato
      de request/response y la tabla de traduccion de errores.
