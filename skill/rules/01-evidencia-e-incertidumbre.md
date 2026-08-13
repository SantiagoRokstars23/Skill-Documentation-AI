# Regla: Evidencia e incertidumbre

1. Toda afirmacion sobre la API debe poder respaldarse en la evidencia recibida (metadata del
   Analyzer) o marcarse explicitamente como inferencia.
2. Nunca presentar una inferencia como un hecho verificado.
3. Si un dato requerido para completar la documentacion no esta presente en la evidencia, no debe
   inventarse un valor plausible. Debe marcarse como "no determinado a partir de evidencia".
4. Ante evidencia ambigua o contradictoria, se conserva la ambiguedad en la salida (por ejemplo,
   mediante una nota), en vez de resolverla arbitrariamente.
5. La confianza (confidence, ver `docs/09-Auditoria.md`) de un elemento generado debe poder
   variar segun si proviene de evidencia directa o de inferencia; nunca se presenta como maxima
   confianza un elemento inferido sin respaldo.
