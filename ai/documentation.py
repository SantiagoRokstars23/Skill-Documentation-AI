"""DocumentationEngine (V0.8): orquesta ContextBuilder -> PromptBuilder ->
LLMProvider -> DocumentationResult.

Solo conoce la abstraccion ``providers.LLMProvider`` (inyectada por
constructor, ver seccion 13 de
prompts/V0.8—AI-DOCUMENTATION-FOUNDATION.md) -- nunca ``AnthropicProvider``,
``urllib`` ni ningun SDK. No hace HTTP, no accede a API keys, no conoce la
CLI, no modifica archivos ni el documento OpenAPI original.

Estrategia de llamadas (decidida y autorizada en Fase 2): una llamada para la
descripcion del proyecto, una llamada por endpoint (nunca una unica llamada
global) -- evita depender de un ``max_tokens`` mayor al que
``AnthropicProvider`` ya fija (V0.7), sin necesidad de modificarlo.
"""

from __future__ import annotations

from analyzer import AnalysisResult
from providers import LLMProvider

from .context import DocumentationContextBuilder
from .models import DTODocumentation, DocumentationResult
from .parsing import parse_endpoint_response, parse_project_response
from .prompts import DocumentationPromptBuilder


class DocumentationEngine:
    """Orquesta la generacion de documentacion para un ``AnalysisResult``.

    El ``provider`` se inyecta explicitamente (nunca se construye
    internamente) para poder sustituirlo por ``FakeProvider`` en tests o por
    cualquier ``LLMProvider`` futuro sin modificar esta clase."""

    def __init__(
        self,
        provider: LLMProvider,
        context_builder: DocumentationContextBuilder,
        prompt_builder: DocumentationPromptBuilder,
    ) -> None:
        self._provider = provider
        self._context_builder = context_builder
        self._prompt_builder = prompt_builder

    def generate(
        self,
        analysis_result: AnalysisResult,
        openapi_document: dict | None = None,
    ) -> DocumentationResult:
        context = self._context_builder.build(analysis_result, openapi_document)

        project_prompt = self._prompt_builder.build_project_prompt(context)
        project_description = parse_project_response(self._provider.generate(project_prompt))

        endpoints = []
        dtos_by_name: dict[str, DTODocumentation] = {}
        for endpoint in context.endpoints:
            endpoint_prompt = self._prompt_builder.build_endpoint_prompt(context, endpoint.id)
            raw_response = self._provider.generate(endpoint_prompt)
            endpoint_documentation, endpoint_dtos = parse_endpoint_response(
                raw_response, context, endpoint
            )
            endpoints.append(endpoint_documentation)
            for dto in endpoint_dtos:
                dtos_by_name.setdefault(dto.name, dto)

        return DocumentationResult(
            project_description=project_description,
            endpoints=tuple(endpoints),
            dtos=tuple(dtos_by_name[name] for name in sorted(dtos_by_name)),
            diagnostics=context.diagnostics_summary,
        )
