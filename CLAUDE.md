# CLAUDE.md — Gobierno del desarrollo

Este documento es la fuente permanente de instrucciones para el desarrollo de
**Skill-Documentation-AI**. Debe leerse antes de trabajar en cualquier version del proyecto, junto
con la directriz especifica de la version en curso (`prompts/`).

## Identidad del proyecto

Skill-Documentation-AI es un motor de documentacion inteligente para microservicios Java/Spring
Boot. Analiza codigo fuente, extrae evidencia estructurada, y utiliza una Skill especializada
junto con un LLM intercambiable para generar, validar y auditar documentacion OpenAPI. Ver
`docs/01-Modelo.md`.

## Objetivo

Ver `docs/02-Objetivos.md` para el objetivo general, los objetivos por version y las
funcionalidades explicitamente fuera de alcance en cada fase.

## Arquitectura

Ver `docs/03-Arquitectura.md`. Resumen de componentes: Analyzer, Skill, LLM Provider, OpenAPI
Generator, Validator, Auditor, CLI, Integraciones futuras. Cada componente tiene responsabilidad
unica y limites claros; ningun componente superior debe acoplarse a un proveedor de LLM concreto.

## Principios

1. El sistema es independiente del proveedor de LLM. Claude es una herramienta de ingenieria
   usada durante el desarrollo, no una dependencia arquitectonica del producto (`docs/06-LLM.md`).
2. La evidencia deterministica tiene prioridad sobre la inferencia del LLM.
3. Nunca se presenta una inferencia como un hecho; la incertidumbre se conserva explicitamente.
4. Cada componente mantiene una responsabilidad clara y el minimo acoplamiento necesario.
5. Simplicidad y mantenibilidad por encima de cobertura funcional prematura.
6. **(V0.2) El Analyzer produce evidencia, no inferencias.** Si un dato no puede determinarse de
   forma suficientemente confiable a partir del codigo analizado, debe registrarse como
   desconocido (`None`/vacio) y, cuando corresponda, generar un `Diagnostic`
   (`docs/09-Auditoria.md`) — nunca inventarse ni completarse por suposicion. Esta regla es
   fundamental para **todo** el proyecto, no solo para el Analyzer: la metadata que produce sera
   consumida por un LLM en fases futuras (V0.3+) para documentar el microservicio, y el objetivo
   es que el LLM documente lo que realmente existe en el codigo, no que "complete" lo que no
   encontro. Ejemplos ya implementados: un nombre de DTO ambiguo entre archivos no se resuelve al
   azar (`docs/07-Analisis.md`); un mapping sin metodo HTTP resoluble se omite en vez de asumir
   uno por defecto.
7. **(V0.3) La misma regla de evidencia aplica al Generator, no solo al Analyzer.** El OpenAPI
   Generator no asume `200 application/json` sin evidencia de `@ResponseStatus`, no traduce
   evidencia de seguridad (`@PreAuthorize`/`@Secured`) a un `securityScheme` concreto que no puede
   justificar, y no inventa un schema para un tipo no resuelto (`{}` + `Diagnostic` en vez de
   adivinar). Cuando una convencion propia del Generator es inevitable por requisitos
   estructurales del formato de salida (p. ej. `info.title`/`info.version`, obligatorios en
   OpenAPI, sin fuente de evidencia posible), debe quedar explicitamente documentada como
   convencion, nunca presentada como si viniera del codigo analizado. Ver `docs/05-OpenAPI.md`.

## Reglas de desarrollo

Ver seccion 16 de `prompts/V0.1-foundation.md` para el listado completo de reglas globales
(no cambiar arquitectura sin autorizacion, no dependencias innecesarias, no funcionalidades fuera
de roadmap, testear todo, documentar decisiones relevantes, no codigo especulativo, no secretos
hardcodeados, mantener configuracion separada de logica, etc.). Estas reglas aplican a **todas**
las versiones del proyecto, no solo a V0.1.

## Reglas arquitectonicas

- No introducir componentes de alto nivel no contemplados en `docs/03-Arquitectura.md` sin
  documentarlo primero.
- El Analyzer no depende de la Skill, el LLM Provider, ni de OpenAPI.
- La Skill no depende de un LLM concreto ni contiene instrucciones exclusivas de una herramienta.
- Toda interaccion con un LLM pasa por la interfaz `LLMProvider` (`providers/base.py`).
- `validators/` permanece como paquete placeholder hasta que V0.4 lo implemente. `generators/`
  dejo de ser placeholder en V0.3 (OpenAPI Generator).
- (V0.3) El Generator (`generators/`) no importa `javalang` ni ningun motor interno del Analyzer
  (`spring_boot_analyzer.py`, `ast_analyzer.py`, `dto_analyzer.py`, `scanner.py`): solo el modelo
  publico de `analyzer`. Analyzer y Generator son responsabilidades separadas (`Java -> Metadata`
  vs. `Metadata -> OpenAPI`) y no deben mezclarse (ver `docs/03-Arquitectura.md`).
- (V0.3) **Antes de modificar `analyzer/models.py` para dar soporte a un componente rio abajo**
  (Generator, Validator, Auditor), debe demostrarse que el dato faltante no puede derivarse del
  modelo existente: identificar la informacion requerida, verificar si ya existe en
  `AnalysisResult`/`Endpoint`/`Parameter`/`DTO`/`Field`/`Response`, y solo si genuinamente no
  puede obtenerse sin modificar el Analyzer, proponer la ampliacion (proceso obligatorio usado en
  V0.3, seccion 6 de `prompts/V0.3-OPENAPI-GENERATOR.md` — se mantiene como patron para futuras
  versiones). No agregar campos "por si acaso" ni entidades por simetria.
- (V0.2) Cualquier dependencia de terceros que el Analyzer necesite para parsear/interpretar
  codigo debe aislarse detras de un modulo propio (patron establecido por
  `analyzer/ast_backend.py` para `javalang`): el resto del Analyzer no debe importar el paquete
  de terceros directamente ni depender de su superficie de excepciones. Ver decision
  arquitectonica 3 en `docs/03-Arquitectura.md`.
- (V0.2) Un motor de analisis nuevo no reemplaza a uno anterior salvo autorizacion explicita y
  justificacion documentada de la perdida de comportamiento (Regla 9 de compatibilidad). El
  patron establecido es *motor principal + fallback*, no sustitucion (ver
  `analyzer/__init__.py::analyze_project`).

## Reglas de IA

Ver seccion 17 de `prompts/V0.1-foundation.md`. En resumen: nunca inventar informacion ausente
del codigo, priorizar evidencia explicita y analisis deterministico, conservar la incertidumbre en
vez de descartarla, y usar el LLM principalmente para interpretacion/generacion/razonamiento, no
como fuente unica de verdad cuando exista informacion deterministica disponible.

## Reglas de testing

- Toda funcionalidad nueva debe tener tests (regla global 6).
- El Analyzer debe tener tests para: deteccion de Controllers, mappings, metodos HTTP,
  PathVariable, RequestParam, RequestBody, casos validos, casos limite, y proyectos
  incompletos/estructuras inesperadas (seccion 20 de `prompts/V0.1-foundation.md`).
- (V0.2) Ademas: DTOs (simples, anidados, colecciones, enums, ambiguos, ciclicos), validaciones,
  headers, seguridad, consumes/produces, multiples `RequestMethod`, anotaciones fully-qualified,
  metodos package-private, y el mecanismo de fallback AST-a-regex (seccion 9 de
  `prompts/V0.2-ADVANCED-SPRING-BOOT-ANALYZER.md`).
- Los tests deben ser reproducibles (`pytest`, sin dependencias externas de red o entorno). Los
  tests que ejercitan directamente el motor de fallback importan `spring_boot_analyzer` o pasan
  codigo Java deliberadamente invalido para forzar esa ruta.
- (V0.3) El Generator debe tener tests para: cada metodo HTTP, cada origen de parametro
  (path/query/header) con required/optional/defaultValue, request body (primitivo/DTO/coleccion/
  DTO anidado), responses (con y sin evidencia de status, DTO, primitivo, coleccion, ausencia
  total de `Response`), schemas (DTO simple/anidado/enum/coleccion/repetido con `$ref`),
  validaciones Bean Validation (una por anotacion soportada), consumes/produces (clase, metodo,
  combinacion, ausencia), security, diagnostics, colisiones de `operationId`, y serializacion
  JSON/YAML valida y deterministica (seccion 10 de `prompts/V0.3-OPENAPI-GENERATOR.md`).
- (V0.3) Golden files limitados: se permite regenerar y validar hechos estructurales sobre
  `examples/customer-service` (paths/operaciones/schemas/algunos `$ref` presentes), pero **no**
  comparar archivos generados byte a byte (fragil ante cambios de formato intencionales).

## Reglas de documentacion

- Toda decision arquitectonica relevante debe documentarse en `docs/` (regla global 7).
- La documentacion debe mantenerse sincronizada con la implementacion real; no describir
  funcionalidades no implementadas como disponibles (`README.md` seccion "Estado actual").
- Cambios que afecten a la metadata, la Skill o la interfaz de LLM Provider deben reflejarse en
  `CHANGELOG.md`.

## Reglas de versionado

Ver `docs/13-Versionado.md`. Semantic Versioning; cada `MINOR` corresponde a una fase completa del
roadmap (`docs/12-Roadmap.md`).

## Scope Lock

Cada version tiene su propio Scope Lock definido en su directriz (`prompts/`). El Scope Lock de
V0.1 esta en `prompts/V0.1-foundation.md` seccion 19. Reglas generales del Scope Lock, validas
para todas las versiones:

- No implementar funcionalidades de una version futura dentro de la version actual.
- Si durante la implementacion se identifica una necesidad relacionada con una funcionalidad fuera
  de alcance, debe documentarse como necesidad futura (en `docs/12-Roadmap.md` o el documento
  correspondiente) y **no** implementarse.
- No ampliar el alcance por iniciativa propia, incluso si tecnicamente es sencillo hacerlo.

## Comportamiento ante ambiguedad

1. Priorizar lo que diga explicitamente la directriz de la version en curso.
2. Si la directriz no resuelve la ambiguedad, elegir la opcion mas simple, mas alineada con la
   arquitectura documentada y con menor superficie de cambio.
3. Documentar la decision tomada y su justificacion en el documento de `docs/` correspondiente.
4. Ante ambiguedad arquitectonica critica (que afecte a componentes o contratos entre
   componentes), solicitar autorizacion explicita antes de implementar, en vez de asumir.

## Comportamiento ante conflictos

- Si una instruccion nueva entra en conflicto con este documento o con una directriz ya
  completada, prevalece lo ya documentado y aceptado, salvo autorizacion explicita para
  cambiarlo.
- Si una directriz de version entra en conflicto con `CLAUDE.md`, se reporta el conflicto en el
  reporte final de esa version en vez de resolverlo unilateralmente.
- No eliminar ni modificar funcionalidad existente para "hacer pasar" una auditoria o checklist
  sin justificacion tecnica documentada.

## Instrucciones para futuras versiones

1. Leer este documento y la directriz de la version correspondiente antes de empezar.
2. Inspeccionar el repositorio y el estado real del codigo antes de modificar nada.
3. Verificar el Scope Lock de la version antes de implementar cualquier funcionalidad.
4. Extender la metadata (`analyzer/models.py`) de forma retrocompatible (campos opcionales
   nuevos), nunca eliminando o resignificando campos existentes sin justificacion documentada.
5. Mantener el Analyzer libre de dependencias hacia Skill, LLM Provider, Generator, Validator o
   Auditor.
6. Al completar una version, actualizar `CHANGELOG.md`, `docs/12-Roadmap.md` (estado) y cualquier
   documento de `docs/` afectado por la nueva funcionalidad.
7. Ejecutar la Regla de Autocontrol (seccion 25 de la directriz correspondiente) antes de declarar
   la version terminada.
