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

**Importante:** esta arquitectura es conceptual para todo el proyecto. V0.1 implementa
unicamente el **Analyzer** de forma funcional y deja el resto de componentes delimitados y
documentados, pero no implementados (ver estado por componente mas abajo).

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

### LLM Provider (interfaz definida en V0.1)

- **Responsabilidad:** exponer una interfaz uniforme para invocar un LLM, independientemente del
  proveedor concreto (Claude, Gemini, OpenAI, u otros compatibles).
- **Entrada:** prompt/contexto construido a partir de la Skill y la evidencia.
- **Salida:** contenido generado por el LLM (texto/estructura, interpretado por el Generator).
- **Dependencias:** ninguna dependencia arquitectonica de componentes superiores hacia un
  proveedor especifico. Ver `docs/06-LLM.md`.
- **Estado en V0.1:** solo la interfaz conceptual (`providers/base.py`). Sin implementaciones
  concretas (fuera de alcance, ver Scope Lock).

### OpenAPI Generator (no implementado en V0.1)

- **Responsabilidad futura:** transformar la salida del LLM Provider (guiada por la Skill) en una
  especificacion OpenAPI valida.
- Reservado para V0.3. Ver `docs/05-OpenAPI.md`.

### Validator (no implementado en V0.1)

- **Responsabilidad futura:** validar la especificacion OpenAPI generada (estructural y
  semanticamente) y clasificar hallazgos en errores/warnings/info.
- Reservado para V0.4. Ver `docs/08-Validacion.md`.
- V0.1 crea unicamente el paquete `validators/` como placeholder documentado.

### Auditor (no implementado en V0.1)

- **Responsabilidad futura:** evaluar trazabilidad, evidencia y confianza (confidence) de la
  documentacion generada.
- Reservado para V0.4. Ver `docs/09-Auditoria.md`.

### CLI (no implementado en V0.1)

- **Responsabilidad futura:** exponer el pipeline completo como herramienta de linea de comandos.
- Reservado para V0.6. En V0.1 el Analyzer se utiliza directamente como libreria Python (ver
  `README.md`).

### Integraciones futuras (no implementadas en V0.1)

- Integracion con Confluence y con el proyecto Python existente. Reservado para V0.7. Ver
  `docs/11-Integracion.md`.

## Flujo de informacion (V0.2)

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
```

El resultado del Analyzer es la unica salida funcional de V0.1/V0.2 y esta disenado para ser
consumido por el futuro OpenAPI Generator sin necesidad de romper compatibilidad (ver
`docs/07-Analisis.md` y `docs/13-Versionado.md`).

## Limites entre componentes

- El Analyzer **no** conoce la Skill, el LLM Provider, ni OpenAPI. Solo produce metadata.
- La Skill **no** depende de un LLM concreto ni contiene instrucciones exclusivas de Claude.
- El LLM Provider es una interfaz; ningun componente superior debe importar un SDK de un
  proveedor especifico directamente.
- `validators/` y `generators/` existen como paquetes reservados, sin logica de negocio.
- Dentro del Analyzer (V0.2): unicamente `analyzer/ast_backend.py` importa `javalang`. Los demas
  modulos (`ast_analyzer.py`, `dto_analyzer.py`, `__init__.py`) solo conocen el resultado de sus
  utilidades (texto, dicts, nodos ya normalizados via `annotation_args`/`literal_text`/
  `type_to_text`), salvo por el recorrido directo del arbol (`javalang.tree.*` para isinstance),
  que se acepta como acoplamiento controlado (ver decision 5 mas abajo).

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

5. **Sin CLI**: el Analyzer se consume como libreria Python. Evita adelantar el roadmap (V0.6
   CLI).

6. **`providers/` solo define la interfaz** (clase base abstracta), sin implementaciones
   concretas, para evitar acoplamiento a un LLM especifico y cumplir el Scope Lock. Sin cambios
   en V0.2 (seccion 15 de la directriz V0.2 lo reitera explicitamente).

7. **`validators/` y `generators/` se mantienen vacios/placeholder**: su logica pertenece a
   V0.3/V0.4, y V0.2 tiene explicitamente prohibido implementar OpenAPI (Scope Lock V0.2).
