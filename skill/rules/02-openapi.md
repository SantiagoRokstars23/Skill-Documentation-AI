# Regla: OpenAPI

1. Toda salida orientada a OpenAPI debe respetar la estructura y el vocabulario definidos en
   `docs/05-OpenAPI.md` (paths, operations, parameters, requestBody, responses, schemas,
   security, headers, examples).
2. Un `parameter` generado debe reflejar exactamente el `source` (`path`/`query`/`body`) y el
   `required` presentes en la evidencia; no se reclasifican ni se invierten.
3. Los `examples` generados por el LLM deben marcarse como generados, no como evidencia
   deterministica.
4. No se debe declarar un `response` con un codigo de estado especifico si no existe evidencia que
   lo respalde; en su ausencia, debe quedar marcado como pendiente de evidencia.
5. Esta regla aplica a partir de que exista un OpenAPI Generator (V0.3); en V0.1 sirve como
   referencia de diseño, no como comportamiento ejecutado.
