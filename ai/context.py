"""ContextBuilder (V0.8): transforma ``analyzer.AnalysisResult`` en un
``DocumentationContext`` inmutable, serializable y determinista para la capa
de prompts.

No llama al LLM, no genera prompts, no conoce ningun proveedor concreto (ver
prompts/V0.8—AI-DOCUMENTATION-FOUNDATION.md seccion 6). Solo importa el modelo
publico de ``analyzer`` -- nunca ``ast_analyzer``/``ast_backend``/
``dto_analyzer``/``spring_boot_analyzer``/``scanner`` ni estructuras internas.
"""

from __future__ import annotations

from analyzer import DTO, AnalysisResult, Endpoint

from .models import (
    DTOContext,
    DTOFieldContext,
    DocumentationContext,
    EndpointContext,
    ParameterContext,
    ResponseContext,
)


class DocumentationContextBuilder:
    """Construye ``DocumentationContext`` a partir de ``AnalysisResult`` (y,
    opcionalmente, un documento OpenAPI ya generado). No muta ninguno de los
    dos argumentos recibidos."""

    def build(
        self,
        analysis_result: AnalysisResult,
        openapi_document: dict | None = None,
    ) -> DocumentationContext:
        endpoint_ids = self._assign_endpoint_ids(analysis_result.endpoints)
        endpoints = tuple(
            self._build_endpoint_context(endpoint, endpoint_id)
            for endpoint, endpoint_id in zip(analysis_result.endpoints, endpoint_ids)
        )
        dtos = self._collect_dtos(analysis_result.endpoints)
        diagnostics_summary = tuple(
            f"{diagnostic.severity.value}: {diagnostic.message}"
            for diagnostic in analysis_result.diagnostics
        )
        # ``openapi_document`` se acepta para mantener la API acordada en Fase 2
        # y por si un futuro consumidor lo necesita, pero V0.8 no lo usa para
        # derivar ``project_name``: la unica clave candidata (``info.title``)
        # es una convencion fija del Generator ("Generated API", ver V0.3 /
        # docs/05-OpenAPI.md), no evidencia del proyecto real -- presentarla
        # como nombre del proyecto violaria la regla de evidencia del
        # proyecto. Sin otra fuente de evidencia, ``project_name`` queda en
        # ``None`` (mismo criterio que el Analyzer: sin evidencia, sin dato).
        del openapi_document
        project_name = None

        return DocumentationContext(
            project_name=project_name,
            endpoints=endpoints,
            dtos=dtos,
            diagnostics_summary=diagnostics_summary,
        )

    def _build_endpoint_context(self, endpoint: Endpoint, endpoint_id: str) -> EndpointContext:
        parameters = tuple(
            ParameterContext(
                name=parameter.name,
                source=parameter.source.value,
                type=parameter.type,
                required=parameter.required,
                default_value=parameter.default_value,
            )
            for parameter in endpoint.parameters
        )

        request_dto_name = None
        for parameter in endpoint.parameters:
            if parameter.source.value == "body" and parameter.dto is not None:
                request_dto_name = parameter.dto.name
                break

        responses: tuple[ResponseContext, ...] = ()
        if endpoint.response is not None:
            responses = (
                ResponseContext(
                    status=endpoint.response.status,
                    body_type=endpoint.response.body_type,
                    is_collection=endpoint.response.is_collection,
                    dto_name=endpoint.response.dto.name if endpoint.response.dto else None,
                ),
            )

        return EndpointContext(
            id=endpoint_id,
            controller=endpoint.controller,
            method=endpoint.method,
            path=endpoint.endpoint,
            parameters=parameters,
            request_dto_name=request_dto_name,
            consumes=tuple(endpoint.consumes),
            produces=tuple(endpoint.produces),
            responses=responses,
            security=tuple(endpoint.security),
        )

    @staticmethod
    def _assign_endpoint_ids(endpoints: list[Endpoint]) -> list[str]:
        # No hay un id propio en el modelo del Analyzer; se deriva de
        # metodo+path. Si colisiona (mismo path+metodo dos veces, caso raro),
        # se desambigua con un sufijo numerico determinista por orden de
        # aparicion -- mismo criterio ya usado por el Generator para
        # colisiones de operationId (V0.3), sin importar su codigo.
        counts: dict[str, int] = {}
        ids: list[str] = []
        for endpoint in endpoints:
            base_id = f"{endpoint.method} {endpoint.endpoint}"
            counts[base_id] = counts.get(base_id, 0) + 1
            occurrence = counts[base_id]
            ids.append(base_id if occurrence == 1 else f"{base_id} #{occurrence}")
        return ids

    def _collect_dtos(self, endpoints: list[Endpoint]) -> tuple[DTOContext, ...]:
        seen: dict[str, DTO] = {}

        def visit(dto: DTO) -> None:
            if dto.name in seen:
                return
            seen[dto.name] = dto
            for dto_field in dto.fields:
                if dto_field.nested_dto is not None:
                    visit(dto_field.nested_dto)

        for endpoint in endpoints:
            for parameter in endpoint.parameters:
                if parameter.dto is not None:
                    visit(parameter.dto)
            if endpoint.response is not None and endpoint.response.dto is not None:
                visit(endpoint.response.dto)

        return tuple(
            self._build_dto_context(seen[name]) for name in sorted(seen)
        )

    @staticmethod
    def _build_dto_context(dto: DTO) -> DTOContext:
        fields = tuple(
            DTOFieldContext(
                name=dto_field.name,
                type=dto_field.type,
                is_collection=dto_field.is_collection,
                validations=tuple(
                    f"{validation.name}({validation.args})" if validation.args else validation.name
                    for validation in dto_field.validations
                ),
                nested_dto_name=dto_field.nested_dto.name if dto_field.nested_dto else None,
            )
            for dto_field in dto.fields
        )
        return DTOContext(
            name=dto.name,
            kind=dto.kind,
            fields=fields,
            enum_constants=tuple(dto.enum_constants),
        )
