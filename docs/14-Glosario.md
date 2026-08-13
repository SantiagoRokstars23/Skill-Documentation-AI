# 14 — Glosario

- **Skill:** conjunto estructurado de instrucciones, reglas y referencias (en `skill/`) que
  encapsula el conocimiento sobre como documentar APIs correctamente, independiente del LLM que
  las ejecute. Ver `docs/04-Skill.md`.

- **LLM (Large Language Model):** modelo de lenguaje utilizado para interpretar evidencia y
  generar contenido de documentacion, invocado a traves de un `LLM Provider`.

- **Provider (LLM Provider):** interfaz que desacopla el sistema de un proveedor de LLM concreto
  (Claude, Gemini, OpenAI, etc.). Ver `docs/06-LLM.md`.

- **Analyzer:** componente que realiza analisis estatico deterministico del codigo fuente de un
  microservicio y produce evidencia/metadata estructurada. Ver `docs/07-Analisis.md`.

- **Evidence (evidencia):** informacion extraida deterministicamente del codigo fuente, con
  referencia a su origen (archivo y, en el futuro, linea). Ver `docs/09-Auditoria.md`.

- **Metadata:** representacion estructurada y serializable de los elementos de la API detectados
  por el Analyzer (controllers, endpoints, parametros). Ver seccion 14 de
  `prompts/V0.1-foundation.md`.

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
