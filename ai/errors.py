"""Errores propios de la capa AI (V0.8).

Deliberadamente minimos (dos clases, ver Fase 2 de
prompts/V0.8—AI-DOCUMENTATION-FOUNDATION.md seccion 17): un error de provider
(``providers.errors.*``, p. ej. ``ProviderTimeoutError``) nunca se envuelve ni
se reclasifica como un error de esta capa -- solo los problemas de la propia
respuesta del LLM (JSON invalido, esquema incumplido, claves no reconocidas que
indican una posible alucinacion) son responsabilidad de ``DocumentationError``.
"""

from __future__ import annotations


class DocumentationError(Exception):
    """Base de los errores propios de ``ai/``."""


class DocumentationParseError(DocumentationError):
    """La respuesta del LLM no cumple el esquema JSON esperado: JSON invalido,
    claves obligatorias ausentes, o claves de ``parameters``/``dtos``/
    ``responses`` que no estan en el contexto entregado (indicio de que el LLM
    invento un nombre no presente en la evidencia)."""
