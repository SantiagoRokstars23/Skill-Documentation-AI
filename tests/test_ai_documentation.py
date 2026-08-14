"""Tests de ai/documentation.py (V0.8): DocumentationEngine.

``FakeProvider`` solo soporta una respuesta fija (V0.6, seccion 19 de
prompts/V0.8-...: "se puede utilizar esa capacidad sin introducir una
arquitectura de mocks compleja"). Para los casos que necesitan una respuesta
distinta por llamada (proyecto vs. cada endpoint) se usa un doble de prueba
local minimo que implementa ``LLMProvider`` -- no se amplia ``FakeProvider``.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ai import DocumentationContextBuilder, DocumentationEngine, DocumentationPromptBuilder
from ai.errors import DocumentationParseError
from analyzer import AnalysisResult, analyze_project
from providers import FakeProvider, LLMProvider, ProviderTimeoutError

EXAMPLE_PROJECT = Path(__file__).resolve().parent.parent / "examples" / "customer-service"

_EMPTY_ENDPOINT_PAYLOAD = {
    "summary": "resumen",
    "endpoint_description": "desc",
    "parameters": {},
    "request_description": None,
    "responses": {},
    "dtos": {},
}


class _ScriptedProvider(LLMProvider):
    """Devuelve una respuesta JSON valida distinta segun si el prompt es de
    proyecto o de endpoint, para poder probar el flujo completo con multiples
    endpoints (algo que FakeProvider no soporta por diseno)."""

    def __init__(self, *, endpoint_payload: dict | None = None) -> None:
        self._endpoint_payload = endpoint_payload or _EMPTY_ENDPOINT_PAYLOAD
        self.calls: list[str] = []

    def generate(self, prompt: str) -> str:
        self.calls.append(prompt)
        if "descripcion general de este proyecto" in prompt:
            return json.dumps({"project_description": "Un proyecto de ejemplo."})
        return json.dumps(self._endpoint_payload)


class _RaisingProvider(LLMProvider):
    def generate(self, prompt: str) -> str:
        raise ProviderTimeoutError("no respondio a tiempo")


class _InvalidResponseProvider(LLMProvider):
    def generate(self, prompt: str) -> str:
        return "esto no es json"


def _engine(provider: LLMProvider) -> DocumentationEngine:
    return DocumentationEngine(provider, DocumentationContextBuilder(), DocumentationPromptBuilder())


def test_fake_provider_drives_the_engine_for_an_empty_project():
    provider = FakeProvider(response=json.dumps({"project_description": "vacio"}))
    result = _engine(provider).generate(AnalysisResult())

    assert result.project_description == "vacio"
    assert result.endpoints == ()


def test_full_flow_against_example_project():
    analysis_result = analyze_project(EXAMPLE_PROJECT)
    provider = _ScriptedProvider()

    result = _engine(provider).generate(analysis_result)

    assert result.project_description == "Un proyecto de ejemplo."
    assert len(result.endpoints) == len(analysis_result.endpoints)
    # una llamada de proyecto + una por endpoint (seccion 14, estrategia hibrida)
    assert len(provider.calls) == 1 + len(analysis_result.endpoints)


def test_dtos_are_aggregated_across_endpoints_deduplicated():
    """Varios endpoints pueden referenciar el mismo DTO (p. ej. CustomerResponse
    en varias operaciones); el DocumentationResult final debe traer cada DTO
    una sola vez, sin importar cuantos endpoints lo describieron."""
    analysis_result = analyze_project(EXAMPLE_PROJECT)
    context = DocumentationContextBuilder().build(analysis_result)

    class _DtoEchoingProvider(LLMProvider):
        """Devuelve, para cada endpoint (en el mismo orden que
        context.endpoints), una descripcion de cada DTO que ese endpoint
        referencia -- exactamente lo que un LLM real devolveria si describe
        fielmente el contexto que recibe."""

        def __init__(self) -> None:
            self._endpoint_index = -1

        def generate(self, prompt: str) -> str:
            if "descripcion general de este proyecto" in prompt:
                return json.dumps({"project_description": "desc"})
            self._endpoint_index += 1
            endpoint = context.endpoints[self._endpoint_index]
            dto_names = set()
            if endpoint.request_dto_name:
                dto_names.add(endpoint.request_dto_name)
            for response in endpoint.responses:
                if response.dto_name:
                    dto_names.add(response.dto_name)
            return json.dumps(
                {
                    **_EMPTY_ENDPOINT_PAYLOAD,
                    "dtos": {name: f"descripcion de {name}" for name in dto_names},
                }
            )

    result = _engine(_DtoEchoingProvider()).generate(analysis_result)

    result_dto_names = [dto.name for dto in result.dtos]
    assert len(result_dto_names) == len(set(result_dto_names))  # sin duplicados
    assert set(result_dto_names) == {
        name
        for endpoint in context.endpoints
        for name in (
            [endpoint.request_dto_name] if endpoint.request_dto_name else []
        )
        + [r.dto_name for r in endpoint.responses if r.dto_name]
    }


def test_provider_error_propagates_unchanged_not_wrapped():
    with pytest.raises(ProviderTimeoutError):
        _engine(_RaisingProvider()).generate(AnalysisResult())


def test_invalid_llm_response_raises_documentation_parse_error():
    with pytest.raises(DocumentationParseError):
        _engine(_InvalidResponseProvider()).generate(AnalysisResult())


def test_result_diagnostics_reflect_context_diagnostics():
    analysis_result = analyze_project(EXAMPLE_PROJECT)
    provider = _ScriptedProvider()

    result = _engine(provider).generate(analysis_result)

    assert len(result.diagnostics) == len(analysis_result.diagnostics)


def test_generate_does_not_mutate_analysis_result():
    import copy

    analysis_result = analyze_project(EXAMPLE_PROJECT)
    original = copy.deepcopy(analysis_result)
    provider = _ScriptedProvider()

    _engine(provider).generate(analysis_result)

    assert analysis_result == original


def test_generate_is_deterministic_with_scripted_provider():
    analysis_result = analyze_project(EXAMPLE_PROJECT)

    first = _engine(_ScriptedProvider()).generate(analysis_result)
    second = _engine(_ScriptedProvider()).generate(analysis_result)

    assert first.to_dict() == second.to_dict()
