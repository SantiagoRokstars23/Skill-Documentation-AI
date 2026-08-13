# 14 — Glosario

- **Skill:** conjunto estructurado de instrucciones, reglas y referencias (en `skill/`) que
  encapsula el conocimiento sobre como documentar APIs correctamente, independiente del LLM que
  las ejecute. Ver `docs/04-Skill.md`.

- **LLM (Large Language Model):** modelo de lenguaje utilizado para interpretar evidencia y
  generar contenido de documentacion, invocado a traves de un `LLM Provider`.

- **Provider (LLM Provider):** interfaz que desacopla el sistema de un proveedor de LLM concreto
  (Claude, Gemini, OpenAI, etc.). Ver `docs/06-LLM.md`.

- **Analyzer:** componente que realiza analisis estatico deterministico del codigo fuente de un
  microservicio y produce evidencia/metadata estructurada. Desde V0.2, combina un motor AST
  (principal) y un motor regex heredado de V0.1 (fallback por archivo). Ver `docs/07-Analisis.md`.

- **AST (Abstract Syntax Tree):** representacion en forma de arbol de la estructura sintactica del
  codigo fuente, producida por un parser real del lenguaje. El Analyzer usa `javalang` para
  producir el AST de cada archivo Java (V0.2). Ver `docs/07-Analisis.md`.

- **Motor de fallback:** el motor de analisis de V0.1 (`analyzer/spring_boot_analyzer.py`, regex +
  balanceo de brackets), reutilizado sin modificaciones en V0.2 para analizar, archivo por
  archivo, cualquier `.java` que el motor AST no pueda parsear. Ver `docs/07-Analisis.md`.

- **Evidence (evidencia):** informacion extraida deterministicamente del codigo fuente, con
  referencia a su origen (archivo, linea, simbolo y tipo de elemento desde V0.2). Ver
  `docs/09-Auditoria.md`.

- **Diagnostic:** hallazgo estructurado del Analyzer (severidad, codigo, mensaje, evidencia),
  introducido en V0.2 como evolucion del canal de texto plano `AnalysisResult.warnings` de V0.1
  (que se mantiene por compatibilidad). Ver `docs/09-Auditoria.md`.

- **Controller:** clase Java que expone endpoints (`@RestController` o `@Controller` con mappings),
  representada como entidad propia desde V0.2 (anotaciones, modificadores, base path, evidencia).
  Ver `docs/07-Analisis.md`.

- **DTO (Data Transfer Object):** clase o enum del proyecto referenciada como cuerpo de peticion o
  de respuesta de un endpoint, resuelta por el Analyzer (V0.2) hacia una estructura de `Field`
  (campos, tipos, validaciones, anidamiento). Ver `docs/07-Analisis.md`.

- **Validation:** evidencia de una anotacion de Bean Validation reconocida (p. ej. `@NotBlank`,
  `@Size`) sobre un campo de DTO o un parametro, capturada sin interpretar su semantica (V0.2). Ver
  `docs/07-Analisis.md`.

- **Metadata:** representacion estructurada y serializable de los elementos de la API detectados
  por el Analyzer (controllers, endpoints, parametros, DTOs, respuestas — V0.2). Ver seccion 14 de
  `prompts/V0.1-foundation.md` y seccion 6 de `prompts/V0.2-ADVANCED-SPRING-BOOT-ANALYZER.md`.

- **OpenAPI:** estandar para describir APIs REST, usado como contrato de salida del sistema
  (fases futuras). Ver `docs/05-OpenAPI.md`.

- **Swagger:** nombre historico del ecosistema de herramientas alrededor de OpenAPI (Swagger UI,
  Swagger Editor). OpenAPI es el nombre de la especificacion desde la version 3.0.

- **Generator (OpenAPI Generator):** componente futuro que transforma evidencia + salida del LLM
  en una especificacion OpenAPI. Ver `docs/05-OpenAPI.md`.

- **Validator:** componente futuro que valida la especificacion OpenAPI generada, estructural y
  semanticamente. Ver `docs/08-Validacion.md`.

- **Auditor:** componente futuro que evalua trazabilidad, evidencia y confidence de la
  documentacion generada. Ver `docs/09-Auditoria.md`.

- **Confidence:** medida (futura) de cuanta confianza tiene el sistema en un elemento de
  documentacion generado, segun su origen (evidencia deterministica vs. inferencia del LLM). Ver
  `docs/09-Auditoria.md`.

- **Drift (deriva):** divergencia entre el codigo fuente real y la documentacion existente,
  detectable automaticamente en fases futuras (V3.0). Ver `docs/12-Roadmap.md`.

- **CLI:** interfaz de linea de comandos que expondra el pipeline completo (V0.6). No implementada
  en V0.1.
