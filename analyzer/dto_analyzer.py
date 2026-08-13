"""Indice de clases del proyecto y resolucion de DTOs (seccion 5.4 de la directriz V0.2).

Responsabilidad distinta de ``ast_analyzer.py``: mientras ese modulo construye
Controllers/Endpoints a partir de un unico archivo ya parseado, este modulo resuelve
referencias de tipo *entre archivos* (p. ej. un ``@RequestBody CustomerRequest`` cuya
clase esta definida en otro archivo del proyecto) hacia un modelo estructurado
(``DTO``/``Field``), incluyendo campos anidados, colecciones, genericos, enums y
anotaciones de Bean Validation.

Principio de evidencia (ver seccion 2 de la directriz V0.2): si un nombre de tipo no
esta indexado (no es una clase/enum del propio proyecto) simplemente no se resuelve
como DTO -- no es un error, es lo esperado para tipos de la libreria estandar. Si un
nombre esta indexado en mas de un archivo (ambiguedad real), NO se elige uno al azar:
se registra un ``Diagnostic`` y se devuelve ``None``, para no presentar una estructura
de DTO no verificable como si fuera evidencia.
"""

from __future__ import annotations

from dataclasses import dataclass

import javalang.tree

from . import ast_backend
from .models import DTO, Diagnostic, DiagnosticSeverity, Evidence, Field, Validation

KNOWN_VALIDATIONS = frozenset(
    {
        "NotNull",
        "NotBlank",
        "NotEmpty",
        "Size",
        "Min",
        "Max",
        "Email",
        "Pattern",
        "Positive",
        "PositiveOrZero",
        "Negative",
        "NegativeOrZero",
    }
)
"""Anotaciones de Bean Validation reconocidas (seccion 5.6 de la directriz V0.2).

No es necesario soportar todas las anotaciones de Bean Validation; este conjunto es
deliberadamente ampliable (agregar un nombre aqui es suficiente para reconocer una
anotacion adicional, sin tocar la logica de extraccion)."""


class _Ambiguous:
    """Marca que un nombre de clase/enum aparece en mas de un archivo del proyecto."""

    __slots__ = ()


AMBIGUOUS = _Ambiguous()


@dataclass
class _IndexEntry:
    node: javalang.tree.ClassDeclaration | javalang.tree.EnumDeclaration
    file_label: str
    kind: str  # "class" | "enum"


ClassIndex = dict[str, "_IndexEntry | _Ambiguous"]


def build_class_index(parsed_units: dict[str, tuple[javalang.tree.CompilationUnit, str]]) -> ClassIndex:
    """Indexa todas las clases y enums de las unidades ya parseadas, por nombre simple.

    Solo incluye archivos que pudieron parsearse como AST (``parsed_units``); las
    clases definidas en archivos que cayeron al motor de fallback no quedan
    disponibles para resolucion de DTOs (limitacion documentada en docs/07-Analisis.md).
    """
    index: ClassIndex = {}
    for file_label, (unit, _text) in parsed_units.items():
        for _, node in unit.filter(javalang.tree.ClassDeclaration):
            _register(index, node.name, _IndexEntry(node=node, file_label=file_label, kind="class"))
        for _, node in unit.filter(javalang.tree.EnumDeclaration):
            _register(index, node.name, _IndexEntry(node=node, file_label=file_label, kind="enum"))
    return index


def _register(index: ClassIndex, name: str, entry: _IndexEntry) -> None:
    if name in index:
        index[name] = AMBIGUOUS
    else:
        index[name] = entry


def resolve_dto(
    type_name: str | None,
    class_index: ClassIndex,
    diagnostics: list[Diagnostic],
    *,
    visiting: frozenset[str] = frozenset(),
) -> DTO | None:
    """Resuelve un nombre simple de tipo hacia un ``DTO``, o ``None`` si no corresponde
    a una clase/enum del proyecto, es ambiguo, o ya se esta resolviendo (ciclo)."""
    if not type_name:
        return None
    entry = class_index.get(type_name)
    if entry is None:
        return None
    if entry is AMBIGUOUS:
        diagnostics.append(
            Diagnostic(
                severity=DiagnosticSeverity.WARNING,
                code="DTO_NAME_AMBIGUOUS",
                message=(
                    f"Existen multiples clases/enums llamadas '{type_name}' en el "
                    "proyecto; no se puede resolver como DTO sin ambiguedad."
                ),
            )
        )
        return None
    if type_name in visiting:
        diagnostics.append(
            Diagnostic(
                severity=DiagnosticSeverity.INFO,
                code="DTO_CYCLE_DETECTED",
                message=f"Referencia ciclica al resolver '{type_name}'; se detiene la expansion anidada.",
                evidence=Evidence(file=entry.file_label, symbol=type_name, type="dto"),
            )
        )
        return None

    evidence = Evidence(
        file=entry.file_label,
        line=ast_backend.line_of(entry.node),
        symbol=type_name,
        type="dto",
    )
    if entry.kind == "enum":
        constants = tuple(c.name for c in entry.node.body.constants) if entry.node.body else ()
        return DTO(name=type_name, kind="enum", enum_constants=constants, evidence=evidence)

    fields = _resolve_fields(entry.node, entry.file_label, class_index, diagnostics, visiting | {type_name})
    return DTO(name=type_name, kind="class", fields=fields, evidence=evidence)


def _resolve_fields(
    class_node: javalang.tree.ClassDeclaration,
    file_label: str,
    class_index: ClassIndex,
    diagnostics: list[Diagnostic],
    visiting: frozenset[str],
) -> tuple[Field, ...]:
    fields: list[Field] = []
    for member in class_node.body:
        if not isinstance(member, javalang.tree.FieldDeclaration):
            continue
        if "static" in member.modifiers:
            continue
        validations = extract_validations(member.annotations, file_label)
        is_collection, inner_type = ast_backend.unwrap_single_argument(member.type)
        lookup_name = ast_backend.leaf_name(inner_type if is_collection else member.type)
        nested = resolve_dto(lookup_name, class_index, diagnostics, visiting=visiting)
        type_text = ast_backend.type_to_text(member.type)
        for declarator in member.declarators:
            fields.append(
                Field(
                    name=declarator.name,
                    type=type_text,
                    is_collection=is_collection,
                    validations=validations,
                    nested_dto=nested,
                    evidence=Evidence(
                        file=file_label,
                        line=ast_backend.line_of(member),
                        symbol=declarator.name,
                        type="field",
                    ),
                )
            )
    return tuple(fields)


def extract_validations(annotations, file_label: str) -> tuple[Validation, ...]:
    """Extrae las anotaciones de ``annotations`` (lista de ``javalang.tree.Annotation``)
    que coinciden con ``KNOWN_VALIDATIONS``, como evidencia (no interpreta su semantica).

    Reutilizado tanto para campos de DTO (este modulo) como para parametros de endpoint
    (``ast_analyzer.py``), evitando duplicar la logica de reconocimiento.
    """
    validations = []
    for annotation in annotations:
        simple = ast_backend.simple_name(annotation.name)
        if simple not in KNOWN_VALIDATIONS:
            continue
        args = ast_backend.annotation_args(annotation)
        named_parts = [
            f"{key}={ast_backend.literal_text(value)}" for key, value in args.items() if key != "value"
        ]
        positional = ast_backend.literal_text(args.get("value")) if "value" in args else None
        parts = ([positional] if positional is not None else []) + named_parts
        validations.append(
            Validation(
                name=simple,
                args=", ".join(parts),
                evidence=Evidence(
                    file=file_label,
                    line=ast_backend.line_of(annotation),
                    symbol=simple,
                    type="validation",
                ),
            )
        )
    return tuple(validations)
