# 10 — Seguridad

## API keys y credenciales

Ninguna API key ni credencial debe estar hardcodeada en el codigo fuente ni en la Skill. Las
credenciales de proveedores LLM (cuando existan implementaciones concretas en fases futuras) se
gestionan mediante configuracion externa (variables de entorno u otro mecanismo estandar),
separada del codigo (regla global 17).

## Secretos

No se deben registrar (log) secretos, tokens ni credenciales en ningun punto del pipeline. Esta
regla aplica tambien a errores/excepciones: los mensajes de log no deben incluir el contenido de
variables de entorno sensibles.

## Informacion sensible

El Analyzer procesa codigo fuente que puede contener informacion sensible del negocio (nombres de
entidades, estructuras internas). Esta informacion debe tratarse con el mismo cuidado que el
codigo fuente original: el Analyzer no debe persistir ni transmitir el codigo fuente fuera del
proceso local salvo que un componente futuro (LLM Provider) lo requiera explicitamente y el
usuario lo autorice.

## Codigo enviado a proveedores LLM

Cuando en fases futuras se invoque un LLM Provider externo, solo debe enviarse la evidencia
estrictamente necesaria para la tarea de documentacion (metadata estructurada), evitando enviar
codigo fuente completo salvo que sea imprescindible y este explicitamente decidido en el diseño
de esa fase. Esta decision debe documentarse cuando se implemente (V0.5).

## Logging

- No registrar secretos, credenciales, ni contenido sensible innecesario.
- Los warnings del Analyzer (`AnalysisResult.warnings`) contienen unicamente informacion sobre
  estructura de codigo (p. ej. "mapping sin metodo HTTP explicito"), nunca datos de negocio
  sensibles ni credenciales.

## Configuracion

La configuracion (por ejemplo, credenciales de un LLM Provider en fases futuras) debe mantenerse
separada de la logica de aplicacion, siguiendo la regla global 17. V0.1 no requiere configuracion
sensible: el Analyzer no se conecta a ningun servicio externo.

## Modelos externos

Cualquier integracion futura con modelos LLM externos debe pasar por la interfaz `LLMProvider`
(`docs/06-LLM.md`), permitiendo auditar y controlar que datos se envian externamente.

## Futuros modelos locales

La arquitectura desacoplada de LLM Provider (`docs/06-LLM.md`) permite evaluar en el futuro el uso
de modelos locales como alternativa cuando la sensibilidad del codigo lo requiera, sin cambios en
el resto del sistema.
