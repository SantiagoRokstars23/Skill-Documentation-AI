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
- `validators/` y `generators/` permanecen como paquetes placeholder hasta que su version
  correspondiente (V0.4 y V0.3) los implemente.

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
- Los tests deben ser reproducibles (`pytest`, sin dependencias externas de red o entorno).

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
