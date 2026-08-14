"""Capa AI (V0.8): primer consumidor real de la infraestructura de LLM
Providers (V0.6/V0.7) dentro del motor.

Analyzer -> DocumentationContextBuilder -> DocumentationPromptBuilder ->
LLMProvider -> DocumentationEngine -> DocumentationResult.

Depende unicamente de la abstraccion ``providers.LLMProvider`` -- nunca de
``AnthropicProvider``, ``urllib`` ni ningun SDK concreto (ver
prompts/V0.8—AI-DOCUMENTATION-FOUNDATION.md seccion 2). No es requerido por
ningun otro paquete del proyecto: ``analyzer``/``generators``/``validator``/
``cli`` siguen funcionando sin `ai/`, y `ai/` no modifica ninguno de ellos.

No implementa RAG, agentes, memoria, chat, tool calling ni integracion con
la CLI todavia -- ver Scope Lock de V0.8.
"""

from __future__ import annotations

from .context import DocumentationContextBuilder
from .documentation import DocumentationEngine
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
]
