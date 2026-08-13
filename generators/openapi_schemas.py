"""Construccion de ``components.schemas`` a partir de los DTOs resueltos por el Analyzer.

Responsabilidad: dado un ``analyzer.DTO`` (ya resuelto -- campos, anidamiento, enum,
validaciones -- ver docs/07-Analisis.md), producir su fragmento de schema OpenAPI y
mantener un registro deduplicado por nombre para reutilizar ``$ref`` en vez de
duplicar schemas inline (seccion "Components / Schemas" de la directriz V0.3).

El arbol ``DTO``/``Field.nested_dto`` que entrega el Analyzer ya es aciclico: la
deteccion y el corte de ciclos ocurre en ``analyzer/dto_analyzer.py`` (evento
``DTO_CYCLE_DETECTED``) antes de que esta metadata exista. Este modulo por lo tanto
NO necesita su propia logica de deteccion de ciclos -- solo deduplicar por nombre
para que un mismo DTO referenciado varias veces produzca un unico
``components.schemas.<Nombre>`` reutilizado via ``$ref`` (seccion 14 de la
directriz).
"""

from __future__ import annotations

from analyzer import DTO, Diagnostic, Field

from .openapi_types import apply_validations, build_type_schema, is_required_by_validation

SchemaRegistry = dict[str, dict]


def schema_ref_for_dto(dto: DTO, registry: SchemaRegistry, diagnostics: list[Diagnostic]) -> dict:
    """Devuelve ``{"$ref": "#/components/schemas/<nombre>"}``, registrando el schema
    del DTO en ``registry`` la primera vez que se referencia. Llamadas posteriores con
    el mismo ``dto.name`` reutilizan el schema ya registrado (no lo reconstruyen)."""
    ref = {"$ref": f"#/components/schemas/{dto.name}"}
    if dto.name in registry:
        return ref

    if dto.kind == "enum":
        schema: dict = {"type": "string"}
        if dto.enum_constants:
            schema["enum"] = list(dto.enum_constants)
        registry[dto.name] = schema
        return ref

    # Se registra un placeholder antes de construir el cuerpo: aunque el arbol de
    # entrada ya es aciclico (ver docstring del modulo), esto evita cualquier doble
    # registro si el mismo nombre se visita dos veces durante una misma construccion.
    registry[dto.name] = {}
    properties: dict[str, dict] = {}
    required: list[str] = []
    for dto_field in dto.fields:
        properties[dto_field.name] = _schema_for_field(dto_field, registry, diagnostics)
        if is_required_by_validation(dto_field.validations):
            required.append(dto_field.name)

    schema = {"type": "object", "properties": properties}
    if required:
        schema["required"] = required
    registry[dto.name] = schema
    return ref


def _schema_for_field(dto_field: Field, registry: SchemaRegistry, diagnostics: list[Diagnostic]) -> dict:
    def resolve_ref(nested_dto: DTO) -> dict:
        return schema_ref_for_dto(nested_dto, registry, diagnostics)

    schema = build_type_schema(
        dto_field.type,
        dto_field.nested_dto,
        diagnostics,
        dto_field.evidence,
        resolve_dto_ref=resolve_ref,
    )
    return apply_validations(schema, dto_field.validations, is_collection=dto_field.is_collection)
