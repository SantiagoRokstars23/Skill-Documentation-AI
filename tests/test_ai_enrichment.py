"""Tests de ai/enrichment.py (V0.9): apply_documentation.

Regla central bajo prueba: solo se escriben campos de texto libre
(``summary``/``description``); nunca se agregan/quitan paths, operaciones,
parametros estructurales o schemas, y el documento de entrada nunca se muta.
"""

from __future__ import annotations

import copy
from pathlib import Path

from ai import (
    DTODocumentation,
    DocumentationContextBuilder,
    DocumentationResult,
    EndpointDocumentation,
    ParameterDocumentation,
    ResponseDocumentation,
    apply_documentation,
)
from analyzer import analyze_project
from generators import generate
from validator import validate

EXAMPLE_PROJECT = Path(__file__).resolve().parent.parent / "examples" / "customer-service"


def _example_document_and_context():
    result = analyze_project(EXAMPLE_PROJECT)
    document, _ = generate(result)
    context = DocumentationContextBuilder().build(result)
    return document, context


def test_apply_documentation_does_not_mutate_input_document():
    document, context = _example_document_and_context()
    original = copy.deepcopy(document)
    documentation = DocumentationResult(project_description="desc")

    apply_documentation(document, documentation, context)

    assert document == original


def test_apply_documentation_sets_info_description_when_absent():
    document, context = _example_document_and_context()
    assert "description" not in document.get("info", {})
    documentation = DocumentationResult(project_description="Servicio de clientes.")

    enriched, diagnostics = apply_documentation(document, documentation, context)

    assert enriched["info"]["description"] == "Servicio de clientes."


def test_apply_documentation_never_overwrites_existing_info_description():
    document, context = _example_document_and_context()
    document["info"]["description"] = "Descripcion real ya existente."
    documentation = DocumentationResult(project_description="Otra cosa distinta.")

    enriched, _ = apply_documentation(document, documentation, context)

    assert enriched["info"]["description"] == "Descripcion real ya existente."


def test_apply_documentation_sets_endpoint_summary_and_description():
    document, context = _example_document_and_context()
    endpoint = context.endpoints[0]
    documentation = DocumentationResult(
        project_description=None,
        endpoints=(
            EndpointDocumentation(
                endpoint_id=endpoint.id,
                summary="Resumen generado",
                description="Descripcion generada",
            ),
        ),
    )

    enriched, diagnostics = apply_documentation(document, documentation, context)

    operation = enriched["paths"][endpoint.path][endpoint.method.lower()]
    assert operation["summary"] == "Resumen generado"
    assert operation["description"] == "Descripcion generada"


def test_apply_documentation_never_overwrites_existing_summary():
    document, context = _example_document_and_context()
    endpoint = context.endpoints[0]
    document["paths"][endpoint.path][endpoint.method.lower()]["summary"] = "Summary real"
    documentation = DocumentationResult(
        project_description=None,
        endpoints=(
            EndpointDocumentation(endpoint_id=endpoint.id, summary="Inventado", description=""),
        ),
    )

    enriched, _ = apply_documentation(document, documentation, context)

    assert enriched["paths"][endpoint.path][endpoint.method.lower()]["summary"] == "Summary real"


def test_apply_documentation_unknown_endpoint_id_is_skipped_with_diagnostic():
    document, context = _example_document_and_context()
    documentation = DocumentationResult(
        project_description=None,
        endpoints=(
            EndpointDocumentation(endpoint_id="DOES-NOT-EXIST", summary="x", description=""),
        ),
    )

    enriched, diagnostics = apply_documentation(document, documentation, context)

    assert enriched == document
    assert any("DOES-NOT-EXIST" in message for message in diagnostics)


def test_apply_documentation_dto_description_applied_to_components_schemas():
    document, context = _example_document_and_context()
    dto_name = context.dtos[0].name
    documentation = DocumentationResult(project_description=None, dtos=(DTODocumentation(name=dto_name, description="Un DTO."),))

    enriched, _ = apply_documentation(document, documentation, context)

    assert enriched["components"]["schemas"][dto_name]["description"] == "Un DTO."


def test_apply_documentation_never_overwrites_existing_schema_description():
    document, context = _example_document_and_context()
    dto_name = context.dtos[0].name
    document["components"]["schemas"][dto_name]["description"] = "Descripcion real."
    documentation = DocumentationResult(project_description=None, dtos=(DTODocumentation(name=dto_name, description="Otra cosa."),))

    enriched, _ = apply_documentation(document, documentation, context)

    assert enriched["components"]["schemas"][dto_name]["description"] == "Descripcion real."


def test_apply_documentation_unknown_dto_name_is_skipped_with_diagnostic():
    document, context = _example_document_and_context()
    documentation = DocumentationResult(project_description=None, dtos=(DTODocumentation(name="NoExiste", description="x"),))

    enriched, diagnostics = apply_documentation(document, documentation, context)

    assert enriched == document
    assert any("NoExiste" in message for message in diagnostics)


def test_apply_documentation_response_description_replaces_generator_placeholder():
    document, context = _example_document_and_context()
    endpoint = next(e for e in context.endpoints if e.responses)
    response_context = endpoint.responses[0]
    status = response_context.status or "default"
    placeholder = document["paths"][endpoint.path][endpoint.method.lower()]["responses"][status][
        "description"
    ]
    assert placeholder  # el Generator siempre pone algo (description es obligatorio en OpenAPI)

    documentation = DocumentationResult(
        project_description=None,
        endpoints=(
            EndpointDocumentation(
                endpoint_id=endpoint.id,
                summary="s",
                description="",
                responses=(ResponseDocumentation(status=status, description="Respuesta real."),),
            ),
        ),
    )

    enriched, _ = apply_documentation(document, documentation, context)

    assert (
        enriched["paths"][endpoint.path][endpoint.method.lower()]["responses"][status]["description"]
        == "Respuesta real."
    )


def test_apply_documentation_response_with_unresolved_status_reconciles_with_generator_default_key():
    """ai/parsing.py::status_label() etiqueta una respuesta sin evidencia de
    @ResponseStatus como 'unknown' (UNKNOWN_STATUS_LABEL) -- es exactamente lo
    que produciria parse_endpoint_response() en un flujo real, no un valor de
    test artificial. El documento generado, en cambio, usa la clave 'default'
    para ese mismo caso (convencion del Generator, V0.3). apply_documentation
    debe reconciliar ambas convenciones en vez de perder la descripcion en
    silencio."""
    document, context = _example_document_and_context()
    endpoint = next(e for e in context.endpoints if any(r.status is None for r in e.responses))
    operation = document["paths"][endpoint.path][endpoint.method.lower()]
    assert "default" in operation["responses"]

    documentation = DocumentationResult(
        project_description=None,
        endpoints=(
            EndpointDocumentation(
                endpoint_id=endpoint.id,
                summary="s",
                description="",
                responses=(ResponseDocumentation(status="unknown", description="Respuesta real."),),
            ),
        ),
    )

    enriched, diagnostics = apply_documentation(document, documentation, context)

    assert (
        enriched["paths"][endpoint.path][endpoint.method.lower()]["responses"]["default"]["description"]
        == "Respuesta real."
    )
    assert diagnostics == []


def test_apply_documentation_response_with_status_absent_from_document_is_a_diagnostic_not_silent():
    document, context = _example_document_and_context()
    endpoint = next(e for e in context.endpoints if e.responses)
    documentation = DocumentationResult(
        project_description=None,
        endpoints=(
            EndpointDocumentation(
                endpoint_id=endpoint.id,
                summary="",
                description="",
                responses=(ResponseDocumentation(status="599", description="x"),),
            ),
        ),
    )

    enriched, diagnostics = apply_documentation(document, documentation, context)

    assert enriched == document
    assert any("599" in message for message in diagnostics)


def test_apply_documentation_response_description_never_overwrites_real_text():
    document, context = _example_document_and_context()
    endpoint = next(e for e in context.endpoints if e.responses)
    response_context = endpoint.responses[0]
    status = response_context.status or "default"
    document["paths"][endpoint.path][endpoint.method.lower()]["responses"][status][
        "description"
    ] = "Texto real, no el placeholder del Generator."

    documentation = DocumentationResult(
        project_description=None,
        endpoints=(
            EndpointDocumentation(
                endpoint_id=endpoint.id,
                summary="s",
                description="",
                responses=(ResponseDocumentation(status=status, description="Intento de sobrescribir."),),
            ),
        ),
    )

    enriched, _ = apply_documentation(document, documentation, context)

    assert (
        enriched["paths"][endpoint.path][endpoint.method.lower()]["responses"][status]["description"]
        == "Texto real, no el placeholder del Generator."
    )


def test_apply_documentation_parameter_description_applied_by_name():
    document, context = _example_document_and_context()
    endpoint = next(
        e for e in context.endpoints if any(p.source == "path" for p in e.parameters)
    )
    parameter_name = next(p.name for p in endpoint.parameters if p.source == "path")
    documentation = DocumentationResult(
        project_description=None,
        endpoints=(
            EndpointDocumentation(
                endpoint_id=endpoint.id,
                summary="s",
                description="",
                parameters=(ParameterDocumentation(name=parameter_name, description="El id."),),
            ),
        ),
    )

    enriched, _ = apply_documentation(document, documentation, context)

    operation_params = enriched["paths"][endpoint.path][endpoint.method.lower()]["parameters"]
    matching = next(p for p in operation_params if p["name"] == parameter_name)
    assert matching["description"] == "El id."


def test_apply_documentation_body_only_parameter_is_skipped_with_diagnostic_not_error():
    """Un parametro con source='body' no tiene equivalente en el array
    'parameters' de OpenAPI (ahi solo van path/query/header) -- debe
    registrarse como diagnostic, nunca lanzar ni corromper el documento."""
    document, context = _example_document_and_context()
    endpoint = next(e for e in context.endpoints if e.request_dto_name)
    body_param = next(p for p in endpoint.parameters if p.source == "body")
    documentation = DocumentationResult(
        project_description=None,
        endpoints=(
            EndpointDocumentation(
                endpoint_id=endpoint.id,
                summary="s",
                description="",
                parameters=(ParameterDocumentation(name=body_param.name, description="x"),),
            ),
        ),
    )

    enriched, diagnostics = apply_documentation(document, documentation, context)

    assert enriched["paths"] == document["paths"] or diagnostics  # nunca crashea; el contrato queda intacto
    original_operation = document["paths"][endpoint.path][endpoint.method.lower()]
    enriched_operation = enriched["paths"][endpoint.path][endpoint.method.lower()]
    assert enriched_operation.get("parameters") == original_operation.get("parameters")


def test_apply_documentation_never_adds_or_removes_paths():
    document, context = _example_document_and_context()
    documentation = DocumentationResult(
        project_description="x",
        endpoints=tuple(
            EndpointDocumentation(endpoint_id=e.id, summary="s", description="d")
            for e in context.endpoints
        ),
        dtos=tuple(DTODocumentation(name=d.name, description="x") for d in context.dtos),
    )

    enriched, _ = apply_documentation(document, documentation, context)

    assert set(enriched["paths"].keys()) == set(document["paths"].keys())
    for path, methods in document["paths"].items():
        assert set(enriched["paths"][path].keys()) == set(methods.keys())


def test_apply_documentation_does_not_invent_structural_keys():
    """Test de no invencion (seccion 20): incluso si se construyera un
    DocumentationResult 'malicioso', los tipos de ai/models.py no tienen forma
    de representar un path/operacion nueva -- no hay ningun campo para eso."""
    endpoint_documentation_fields = set(EndpointDocumentation.__dataclass_fields__)
    assert "path" not in endpoint_documentation_fields
    assert "method" not in endpoint_documentation_fields
    assert "operation" not in endpoint_documentation_fields


def test_apply_documentation_full_result_still_passes_validator_with_no_new_errors():
    result = analyze_project(EXAMPLE_PROJECT)
    document, _ = generate(result)
    context = DocumentationContextBuilder().build(result)
    base_errors = [d for d in validate(document) if d.severity.value == "ERROR"]

    documentation = DocumentationResult(
        project_description="Servicio de clientes.",
        endpoints=tuple(
            EndpointDocumentation(endpoint_id=e.id, summary=f"Resumen de {e.id}", description="")
            for e in context.endpoints
        ),
        dtos=tuple(DTODocumentation(name=d.name, description=f"DTO {d.name}") for d in context.dtos),
    )

    enriched, _ = apply_documentation(document, documentation, context)
    enriched_errors = [d for d in validate(enriched) if d.severity.value == "ERROR"]

    assert len(enriched_errors) == len(base_errors) == 0


def test_apply_documentation_is_deterministic():
    document, context = _example_document_and_context()
    documentation = DocumentationResult(
        project_description="x",
        endpoints=(EndpointDocumentation(endpoint_id=context.endpoints[0].id, summary="s", description="d"),),
    )

    first, first_diags = apply_documentation(document, documentation, context)
    second, second_diags = apply_documentation(document, documentation, context)

    assert first == second
    assert first_diags == second_diags


def test_apply_documentation_empty_result_produces_no_diagnostics_and_unchanged_document():
    document, context = _example_document_and_context()
    documentation = DocumentationResult(project_description=None)

    enriched, diagnostics = apply_documentation(document, documentation, context)

    assert enriched == document
    assert diagnostics == []
