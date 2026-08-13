# Skill de Documentacion de APIs — Skill-Documentation-AI

## Proposito

Esta Skill encapsula el conocimiento necesario para interpretar evidencia extraida de un
microservicio Java/Spring Boot y, a partir de ella, generar, completar, actualizar y auditar
documentacion OpenAPI de forma consistente, trazable y sin inventar informacion.

Esta Skill esta escrita para ser ejecutada conceptualmente por **cualquier LLM** capaz de seguir
instrucciones estructuradas en lenguaje natural — no depende de ninguna capacidad exclusiva de
Claude ni de ningun otro proveedor especifico. Ver `docs/04-Skill.md` y `docs/06-LLM.md`.

## Entradas

- **Evidencia/metadata estructurada** producida por el Analyzer (`analyzer/models.py`):
  controllers, endpoints, metodo HTTP, path, y parametros (nombre, tipo, origen — path/query/body
  —, y si son requeridos).
- Opcionalmente, contexto adicional provisto por quien orquesta la ejecucion (p. ej. convenciones
  de la organizacion), siempre que no contradiga las reglas de esta Skill.

La Skill **no** recibe codigo fuente Java directamente: solo la metadata ya extraida por el
Analyzer. Ver `docs/07-Analisis.md`.

## Salidas

En V0.1 esta Skill no se invoca de forma automatizada (no hay LLM Provider ni Generator
implementados todavia). Su salida conceptual, para fases futuras, es contenido orientado a
completar una especificacion OpenAPI (descripciones, ejemplos, agrupaciones logicas) a partir de
la evidencia recibida, siempre distinguiendo lo que es evidencia deterministica de lo que es
contenido generado. Ver `docs/05-OpenAPI.md`.

## Principios

1. **La evidencia manda.** Si un dato existe en la metadata (p. ej. que un parametro es
   `required: true`), ese dato se usa tal cual; no se reinterpreta ni se contradice.
2. **Nunca inventar informacion ausente.** Si la evidencia no incluye un dato (p. ej. no hay
   informacion sobre codigos de respuesta), no se debe inventar un valor plausible: debe marcarse
   como desconocido/incierto.
3. **La incertidumbre se conserva, no se oculta.** Cuando exista ambiguedad, debe quedar reflejada
   en la salida (p. ej. mediante una nota o marca de baja confianza), no resuelta arbitrariamente.
4. **Toda inferencia debe ser identificable como tal.** El contenido generado por el LLM que no
   provenga directamente de la evidencia debe poder distinguirse del contenido deriva
   directamente de evidencia deterministica.
5. **Consistencia entre servicios.** Ante evidencia equivalente, la salida generada debe seguir el
   mismo criterio, independientemente del microservicio o de la ejecucion.

## Reglas

Ver `skill/rules/` para las reglas detalladas:

- `skill/rules/01-evidencia-e-incertidumbre.md`
- `skill/rules/02-openapi.md`
- `skill/rules/03-spring-boot.md`

## OpenAPI

La salida final del pipeline (fases futuras) debe ser compatible con el estandar OpenAPI descrito
en `docs/05-OpenAPI.md` y en `skill/references/openapi-reference.md`.

## Spring Boot

La evidencia que recibe esta Skill proviene de la interpretacion de anotaciones Spring MVC /
Spring Boot realizada por el Analyzer. Ver `skill/references/spring-boot-annotations.md` para el
vocabulario de anotaciones reconocido.

## Evidencia

Cada elemento de metadata recibido puede incluir informacion de origen (`evidence.file`, ver
`docs/09-Auditoria.md`). Cuando esta Skill se use para generar contenido (fases futuras), el
contenido generado deberia poder enlazarse con la evidencia que lo origino.

## Incertidumbre

Cuando la metadata no contiene informacion suficiente para completar un elemento de la
documentacion (p. ej. no hay evidencia de los posibles codigos de respuesta de un endpoint), la
Skill debe indicar explicitamente que ese elemento no pudo determinarse a partir de evidencia, en
lugar de completarlo con un valor generico no verificable.

## Restricciones

- No usar el LLM como unica fuente de verdad cuando exista informacion deterministica disponible
  en la evidencia.
- No asumir reglas de negocio no documentadas.
- No generar contenido que contradiga la evidencia recibida.

## Comportamiento esperado del LLM

Al operar bajo esta Skill, un LLM debe:

1. Priorizar siempre la evidencia recibida sobre su propio conocimiento general.
2. Senalar explicitamente cuando complete un vacio mediante inferencia, en vez de presentarlo como
   un hecho verificado.
3. Mantener el mismo criterio de interpretacion de forma consistente entre ejecuciones y entre
   microservicios distintos.
4. Rechazar (o marcar como no resuelto) un caso en el que la evidencia sea insuficiente o
   contradictoria, en vez de forzar una respuesta.
