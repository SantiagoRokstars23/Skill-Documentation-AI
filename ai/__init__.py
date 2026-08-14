"""Capa AI (V0.8, ampliada en V0.9): consumidor real de la infraestructura de
LLM Providers (V0.6/V0.7) dentro del motor.

Analyzer -> DocumentationContextBuilder -> DocumentationPromptBuilder ->
LLMProvider -> DocumentationEngine -> DocumentationResult -> (V0.9)
apply_documentation() -> documento OpenAPI enriquecido.

Depende unicamente de la abstraccion ``providers.LLMProvider`` -- nunca de
``AnthropicProvider``, ``urllib`` ni ningun SDK concreto. No es requerido por
ningun otro paquete del proyecto: ``analyzer``/``generators``/``validator``/
``cli`` siguen funcionando sin `ai/`, y `ai/` no modifica ninguno de ellos.

``apply_documentation`` (V0.9) solo escribe en campos de texto libre
(``summary``/``description``) de un documento OpenAPI ya generado -- nunca en
``paths``/parametros/tipos/status codes/``$ref``, ver ai/enrichment.py.

No implementa RAG, agentes, memoria, chat, tool calling ni comandos de CLI
nuevos -- ver Scope Lock de V0.8/V0.9.
"""

from __future__ import annotations

from .context import DocumentationContextBuilder
from .documentation import DocumentationEngine
from .enrichment import apply_documentation
from .errors import DocumentationError, DocumentationParseError
from .models import (
    DTOContext,
    DTODocumentation,
    DTOFieldContext,
    DocumentationContext,
    DocumentationResult,
    EndpointContext,
    EndpointDocumentation,
    ParameterContext,
    ParameterDocumentation,
    ResponseContext,
    ResponseDocumentation,
)
from .prompts import PROMPT_VERSION, DocumentationPromptBuilder

__all__ = [
    "PROMPT_VERSION",
    "DTOContext",
    "DTODocumentation",
    "DTOFieldContext",
    "DocumentationContext",
    "DocumentationContextBuilder",
    "DocumentationEngine",
    "DocumentationError",
    "DocumentationParseError",
    "DocumentationPromptBuilder",
    "DocumentationResult",
    "EndpointContext",
    "EndpointDocumentation",
    "ParameterContext",
    "ParameterDocumentation",
    "ResponseContext",
    "ResponseDocumentation",
    "apply_documentation",
]
