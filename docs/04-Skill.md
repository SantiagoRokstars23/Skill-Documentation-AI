# 04 — Skill

> V0.2 no modifica la Skill (no estaba en su Scope Lock). Se documenta aqui unicamente que la
> evidencia que la Skill podra recibir en fases futuras es ahora considerablemente mas rica:
> ademas de `Endpoint`/`Parameter`, el Analyzer produce `Controller`, `DTO`/`Field` (con
> validaciones y anidamiento), `Response` y evidencia de seguridad (ver `docs/07-Analisis.md`).
> Las reglas de `skill/rules/01-evidencia-e-incertidumbre.md` (nunca inventar, conservar la
> incertidumbre) siguen aplicando sin cambios a esta evidencia ampliada.

## Que es la Skill

La Skill de documentacion (`skill/`) es un conjunto estructurado de instrucciones, reglas y
referencias en lenguaje natural (Markdown) que encapsula el conocimiento sobre como documentar
correctamente una API a partir de evidencia extraida del codigo. No es codigo ejecutable: es
conocimiento de dominio consumible por cualquier LLM capaz de seguir instrucciones estructuradas.

## Proposito

- Estandarizar como se interpreta la evidencia producida por el Analyzer.
- Definir el comportamiento esperado del LLM frente a informacion completa, incompleta o ausente.
- Mantener consistencia de documentacion entre distintos microservicios y distintas ejecuciones.
- Servir como contrato de comportamiento independiente del motor de IA que lo ejecute.

## Estructura

```text
skill/
├── SKILL.md          Punto de entrada: proposito, entradas, salidas, reglas generales
├── rules/             Reglas especificas (evidencia, incertidumbre, OpenAPI, Spring Boot)
├── references/        Material de referencia (anotaciones Spring, estructura OpenAPI)
└── templates/         Plantillas de salida esperada (estructura de un endpoint documentado)
```

## Responsabilidades

- Explicar el proposito del sistema y el rol de la Skill dentro del pipeline.
- Definir explicitamente las entradas que recibe (evidencia/metadata del Analyzer) y las salidas
  esperadas (contenido orientado a OpenAPI, en fases futuras).
- Establecer reglas de comportamiento ante evidencia incompleta o ambigua.
- Establecer principios de trazabilidad entre evidencia y contenido generado.

## Reglas

Las reglas de la Skill (`skill/rules/`) cubren, como minimo:

- Principios generales de documentacion (que hacer y que no hacer).
- Manejo de evidencia e incertidumbre: nunca inventar informacion ausente del codigo.
- Convenciones de Spring Boot relevantes para la interpretacion de evidencia.
- Estructura y vocabulario de OpenAPI que debe respetarse al generar contenido (fase futura).

## Relacion con el LLM

La Skill es el contrato de comportamiento que cualquier LLM Provider debe seguir al interpretar
evidencia y generar documentacion. La Skill no invoca al LLM directamente: es contenido que el
LLM Provider (o quien lo orqueste) incorpora como contexto/instrucciones. Ver `docs/06-LLM.md`.

## Relacion con el Analyzer

La Skill consume exclusivamente la metadata/evidencia estructurada que produce el Analyzer
(`docs/07-Analisis.md`). No accede al codigo fuente directamente ni redefine como se extrae la
evidencia: esa responsabilidad es exclusiva del Analyzer.

## Independencia respecto a Claude

La Skill esta escrita en lenguaje natural neutro, sin referencias a APIs, herramientas o
capacidades exclusivas de Claude. Cualquier instruccion que solo pudiera ejecutar Claude (por
ejemplo, el uso de una herramienta propietaria especifica) queda fuera de la Skill. Claude se usa
como herramienta de *ingenieria* para construir el proyecto (ver `prompts/`), pero el
**producto** — incluida la Skill — debe poder ejecutarse conceptualmente con cualquier LLM capaz
de seguir instrucciones en lenguaje natural.
