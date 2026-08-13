# Plantilla: Documentacion de un endpoint

Esta plantilla ilustra la estructura conceptual que debera producir el pipeline completo (fases
futuras) para un endpoint, a partir de la metadata del Analyzer. No es un formato ejecutable en
V0.1: sirve como referencia de diseño para la Skill y para el futuro OpenAPI Generator.

```yaml
path: <Endpoint.endpoint>
method: <Endpoint.method>
controller: <Endpoint.controller>
summary: <generado por el LLM Provider a partir de la evidencia — marcar como generado>
description: <generado por el LLM Provider a partir de la evidencia — marcar como generado>
parameters:
  - name: <Parameter.name>
    in: <Parameter.source>        # path | query
    required: <Parameter.required>
    schema:
      type: <derivado de Parameter.type — evidencia>
requestBody:
  required: <Parameter.required para source = body>
  content:
    application/json:
      schema:
        type: object              # derivado de Parameter.type — evidencia
responses:
  # Sin evidencia suficiente en V0.1 para completar codigos de respuesta.
  # No debe inventarse: debe quedar marcado como pendiente hasta contar con evidencia
  # (por ejemplo, del tipo de retorno del metodo, en una version futura del Analyzer).
  "<pendiente>": {}
_evidence:
  file: <Endpoint.evidence.file>
```
