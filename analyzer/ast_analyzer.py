"""Construye Controllers/Endpoints/Parameters a partir del AST de un archivo Java
(motor principal de V0.2, ver docs/07-Analisis.md).

Responsabilidad: dado un ``javalang.tree.CompilationUnit`` ya parseado (ver
``ast_backend.parse_file``) y el indice de clases del proyecto (ver
``dto_analyzer.build_class_index``), producir la metadata de endpoints definida en
``analyzer/models.py``. No lee ni escribe archivos, no decide cuando recurrir al motor
de fallback (eso es responsabilidad de ``analyzer/__init__.py``).

Principio de evidencia (seccion 2 de la directriz V0.2): cuando una anotacion de
mapping no permite resolver un metodo HTTP concreto, o una anotacion no reconocida
podria ser relevante, el codigo no completa el dato por suposicion: omite el elemento
y registra un ``Diagnostic``.
"""

from __future__ import annotations

import javalang.tree

from . import ast_backend, dto_analyzer
from .models import (
    Controller,
    Diagnostic,
    DiagnosticSeverity,
    Endpoint,
    Evidence,
    Parameter,
    ParameterSource,
    Response,
)
from .spring_boot_analyzer import _join_paths

_MAPPING_ANNOTATIONS = {
    "GetMapping": "GET",
    "PostMapping": "POST",
    "PutMapping": "PUT",
    "DeleteMapping": "DELETE",
    "PatchMapping": "PATCH",
}
_VALID_HTTP_METHODS = frozenset(_MAPPING_ANNOTATIONS.values())
_SECURITY_ANNOTATIONS = frozenset({"PreAuthorize", "Secured"})
_COLLECTION_WRAPPER = "ResponseEntity"

_PARAMETER_ANNOTATIONS = frozenset({"PathVariable", "RequestParam", "RequestBody", "RequestHeader"})
_PARAMETER_SOURCE_BY_ANNOTATION = {
    "PathVariable": ParameterSource.PATH,
    "RequestParam": ParameterSource.QUERY,
    "RequestHeader": ParameterSource.HEADER,
    "RequestBody": ParameterSource.BODY,
}


def analyze_compilation_unit(
    unit: javalang.tree.CompilationUnit,
    file_label: str,
    class_index: dto_analyzer.ClassIndex,
) -> tuple[list[Endpoint], list[Controller], list[Diagnostic]]:
    endpoints: list[Endpoint] = []
    controllers: list[Controller] = []
    diagnostics: list[Diagnostic] = []

    for _, class_node in unit.filter(javalang.tree.ClassDeclaration):
        annotation_names = {ast_backend.simple_name(a.name) for a in class_node.annotations}
        is_rest_controller = "RestController" in annotation_names
        is_plain_controller = "Controller" in annotation_names and _has_any_mapping(class_node)
        if not (is_rest_controller or is_plain_controller):
            continue

        base_path, class_consumes, class_produces = _class_mapping_defaults(class_node)
        class_security = _extract_security(class_node.annotations)
        controller = Controller(
            name=class_node.name,
            annotations=tuple(a.name for a in class_node.annotations),
            modifiers=tuple(sorted(class_node.modifiers)),
            base_path=base_path,
            evidence=Evidence(
                file=file_label,
                line=ast_backend.line_of(class_node),
                symbol=class_node.name,
                type="controller",
            ),
        )
        controllers.append(controller)

        for member in class_node.body:
            if not isinstance(member, javalang.tree.MethodDeclaration):
                continue
            endpoints.extend(
                _build_endpoints_for_method(
                    member,
                    controller_name=class_node.name,
                    base_path=base_path,
                    class_consumes=class_consumes,
                    class_produces=class_produces,
                    class_security=class_security,
                    file_label=file_label,
                    class_index=class_index,
                    diagnostics=diagnostics,
                )
            )

    return endpoints, controllers, diagnostics


def _has_any_mapping(class_node: javalang.tree.ClassDeclaration) -> bool:
    for member in class_node.body:
        if not isinstance(member, javalang.tree.MethodDeclaration):
            continue
        for annotation in member.annotations:
            simple = ast_backend.simple_name(annotation.name)
            if simple in _MAPPING_ANNOTATIONS or simple == "RequestMapping":
                return True
    return False


def _class_mapping_defaults(class_node: javalang.tree.ClassDeclaration) -> tuple[str, tuple[str, ...], tuple[str, ...]]:
    base_path = ""
    consumes: tuple[str, ...] = ()
    produces: tuple[str, ...] = ()
    for annotation in class_node.annotations:
        if ast_backend.simple_name(annotation.name) != "RequestMapping":
            continue
        args = ast_backend.annotation_args(annotation)
        base_path = _extract_path(args) or base_path
        consumes = _extract_str_tuple(args.get("consumes")) or consumes
        produces = _extract_str_tuple(args.get("produces")) or produces
    return base_path, consumes, produces


def _build_endpoints_for_method(
    method: javalang.tree.MethodDeclaration,
    *,
    controller_name: str,
    base_path: str,
    class_consumes: tuple[str, ...],
    class_produces: tuple[str, ...],
    class_security: tuple[str, ...],
    file_label: str,
    class_index: dto_analyzer.ClassIndex,
    diagnostics: list[Diagnostic],
) -> list[Endpoint]:
    http_methods, path, consumes, produces, mapping_found = _resolve_mapping_annotation(method)
    if not mapping_found:
        return []

    method_evidence = Evidence(
        file=file_label,
        line=ast_backend.line_of(method),
        symbol=method.name,
        type="endpoint",
    )

    if not http_methods:
        diagnostics.append(
            Diagnostic(
                severity=DiagnosticSeverity.WARNING,
                code="AST_MAPPING_WITHOUT_HTTP_METHOD",
                message=(
                    f"El metodo '{method.name}' en '{controller_name}' tiene un mapping "
                    "sin metodo HTTP explicito; se omite."
                ),
                evidence=method_evidence,
            )
        )
        return []

    full_path = _join_paths(base_path, path or "")
    parameters = tuple(
        _build_parameter(p, file_label, class_index, diagnostics) for p in method.parameters
    )
    parameters = tuple(p for p in parameters if p is not None)
    response = _build_response(method, file_label, class_index, diagnostics)
    security = class_security + _extract_security(method.annotations)

    return [
        Endpoint(
            controller=controller_name,
            endpoint=full_path,
            method=http_method,
            parameters=parameters,
            evidence=method_evidence,
            java_method=method.name,
            consumes=consumes or class_consumes,
            produces=produces or class_produces,
            response=response,
            security=security,
        )
        for http_method in http_methods
    ]


def _resolve_mapping_annotation(
    method: javalang.tree.MethodDeclaration,
) -> tuple[list[str] | None, str | None, tuple[str, ...], tuple[str, ...], bool]:
    http_methods: list[str] | None = None
    path: str | None = None
    consumes: tuple[str, ...] = ()
    produces: tuple[str, ...] = ()
    found = False

    for annotation in method.annotations:
        simple = ast_backend.simple_name(annotation.name)
        args = ast_backend.annotation_args(annotation)
        if simple in _MAPPING_ANNOTATIONS:
            found = True
            http_methods = [_MAPPING_ANNOTATIONS[simple]]
            path = _extract_path(args) or path
            consumes = _extract_str_tuple(args.get("consumes")) or consumes
            produces = _extract_str_tuple(args.get("produces")) or produces
        elif simple == "RequestMapping":
            found = True
            path = _extract_path(args) or path
            consumes = _extract_str_tuple(args.get("consumes")) or consumes
            produces = _extract_str_tuple(args.get("produces")) or produces
            resolved = _extract_http_methods(args.get("method"))
            if resolved:
                http_methods = resolved

    return http_methods, path, consumes, produces, found


def _extract_path(args: dict[str, object]) -> str | None:
    value = args.get("value") if "value" in args else args.get("path")
    return ast_backend.literal_text(value)


def _extract_str_tuple(value_node) -> tuple[str, ...]:
    if value_node is None:
        return ()
    if isinstance(value_node, javalang.tree.ElementArrayValue):
        texts = [ast_backend.literal_text(v) for v in value_node.values]
        return tuple(t for t in texts if t is not None)
    text = ast_backend.literal_text(value_node)
    return (text,) if text is not None else ()


def _extract_http_methods(value_node) -> list[str]:
    if value_node is None:
        return []
    nodes = value_node.values if isinstance(value_node, javalang.tree.ElementArrayValue) else [value_node]
    methods = []
    for node in nodes:
        if isinstance(node, javalang.tree.MemberReference):
            member = node.member.upper()
            if member in _VALID_HTTP_METHODS:
                methods.append(member)
    return methods


def _build_parameter(
    parameter: javalang.tree.FormalParameter,
    file_label: str,
    class_index: dto_analyzer.ClassIndex,
    diagnostics: list[Diagnostic],
) -> Parameter | None:
    matched = [a for a in parameter.annotations if ast_backend.simple_name(a.name) in _PARAMETER_ANNOTATIONS]
    if not matched:
        return None
    # Si un parametro tuviera mas de una anotacion reconocida (invalido en Java real
    # para estas anotaciones mutuamente excluyentes), se usa la primera encontrada en
    # el codigo fuente en vez de suponer cual prevalece.
    annotation = matched[0]
    simple = ast_backend.simple_name(annotation.name)
    source = _PARAMETER_SOURCE_BY_ANNOTATION[simple]
    args = ast_backend.annotation_args(annotation)

    explicit_name = ast_backend.literal_text(args.get("value")) or ast_backend.literal_text(args.get("name"))
    default_value = ast_backend.literal_text(args.get("defaultValue"))
    required_text = ast_backend.literal_text(args.get("required"))
    has_default = default_value is not None
    if source == ParameterSource.BODY:
        required = required_text != "false"
    else:
        required = required_text != "false" and not has_default

    is_collection, inner_type = ast_backend.unwrap_single_argument(parameter.type)
    lookup_name = ast_backend.leaf_name(inner_type if is_collection else parameter.type)
    dto = dto_analyzer.resolve_dto(lookup_name, class_index, diagnostics) if source == ParameterSource.BODY else None

    return Parameter(
        name=explicit_name or parameter.name,
        type=ast_backend.type_to_text(parameter.type),
        source=source,
        required=required,
        default_value=default_value,
        validations=dto_analyzer.extract_validations(parameter.annotations, file_label),
        dto=dto,
        evidence=Evidence(
            file=file_label,
            line=ast_backend.line_of(parameter),
            symbol=parameter.name,
            type="parameter",
        ),
    )


def _build_response(
    method: javalang.tree.MethodDeclaration,
    file_label: str,
    class_index: dto_analyzer.ClassIndex,
    diagnostics: list[Diagnostic],
) -> Response:
    status = None
    for annotation in method.annotations:
        if ast_backend.simple_name(annotation.name) != "ResponseStatus":
            continue
        args = ast_backend.annotation_args(annotation)
        status = ast_backend.literal_text(args.get("value") or args.get("code"))

    evidence = Evidence(
        file=file_label,
        line=ast_backend.line_of(method),
        symbol=method.name,
        type="response",
    )

    return_type = method.return_type
    if return_type is None:
        return Response(wrapper=None, body_type=None, status=status, evidence=evidence)

    wrapper = None
    body_node = return_type
    if ast_backend.leaf_name(return_type) == _COLLECTION_WRAPPER:
        arguments = getattr(return_type, "arguments", None)
        if arguments and len(arguments) == 1 and getattr(arguments[0], "type", None) is not None:
            wrapper = _COLLECTION_WRAPPER
            body_node = arguments[0].type

    is_collection, inner_node = ast_backend.unwrap_single_argument(body_node)
    dto_lookup_node = inner_node if is_collection else body_node
    dto = dto_analyzer.resolve_dto(ast_backend.leaf_name(dto_lookup_node), class_index, diagnostics)

    return Response(
        wrapper=wrapper,
        body_type=ast_backend.type_to_text(body_node),
        is_collection=is_collection,
        dto=dto,
        status=status,
        evidence=evidence,
    )


def _extract_security(annotations) -> tuple[str, ...]:
    entries = []
    for annotation in annotations:
        simple = ast_backend.simple_name(annotation.name)
        if simple not in _SECURITY_ANNOTATIONS:
            continue
        args = ast_backend.annotation_args(annotation)
        value = ast_backend.literal_text(args.get("value"))
        entries.append(f"{simple}({value})" if value is not None else simple)
    return tuple(entries)
