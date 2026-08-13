"""Mapeo de tipos Java (texto producido por el Analyzer) a schemas OpenAPI 3.0.3.

Responsabilidad: interpretar el TEXTO de tipo que ya produjo el Analyzer
(``Parameter.type`` / ``Field.type`` / ``Response.body_type``, p. ej.
``"List<CustomerResponse>"`` o ``"java.util.List<String>"``) y las anotaciones de
Bean Validation ya capturadas (``Validation``), para construir un fragmento de schema
OpenAPI. Esto es interpretacion de metadata ya producida, no re-analisis de Java: este
modulo no importa ``javalang`` ni ningun motor del Analyzer (ver Scope Lock, seccion
2.1 de la directriz V0.3).

Principio de evidencia (seccion 2.2 de la directriz V0.3): un tipo que no es un
primitivo reconocido y para el cual el Analyzer no resolvio un DTO (``dto``/
``nested_dto`` es ``None``) se representa como ``{}`` (schema vacio) y genera un
``Diagnostic`` -- nunca se adivina.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Callable

from analyzer import Diagnostic, DiagnosticSeverity, Evidence, Validation

# ---------------------------------------------------------------------------
# Parseo del texto de tipo producido por analyzer.ast_backend.type_to_text
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ParsedType:
    """Representacion estructurada de un texto de tipo ya producido por el Analyzer."""

    name: str
    args: tuple["ParsedType", ...] = field(default_factory=tuple)
    array_dims: int = 0


def parse_type_text(text: str) -> ParsedType:
    """Parsea el texto de tipo (formato exacto de ``ast_backend.type_to_text``):
    nombre calificado opcional, genericos ``<A, B>`` balanceados, y sufijos ``[]``.
    """
    text = (text or "?").strip()
    array_dims = 0
    while text.endswith("[]"):
        array_dims += 1
        text = text[:-2].strip()
    args: tuple[ParsedType, ...] = ()
    if text.endswith(">") and "<" in text:
        open_idx = text.index("<")
        name_part = text[:open_idx]
        inner = text[open_idx + 1 : -1]
        args = tuple(parse_type_text(part) for part in _split_top_level(inner))
    else:
        name_part = text
    simple_name = name_part.rsplit(".", 1)[-1] if name_part else "?"
    return ParsedType(name=simple_name, args=args, array_dims=array_dims)


def _split_top_level(text: str) -> list[str]:
    parts: list[str] = []
    current: list[str] = []
    depth = 0
    for char in text:
        if char == "<":
            depth += 1
        elif char == ">":
            depth -= 1
        if char == "," and depth == 0:
            parts.append("".join(current).strip())
            current = []
            continue
        current.append(char)
    if current:
        parts.append("".join(current).strip())
    return [p for p in parts if p]


# ---------------------------------------------------------------------------
# Tabla de tipos Java -> OpenAPI (seccion 15 de la directriz V0.3)
# ---------------------------------------------------------------------------

PRIMITIVE_TYPES: dict[str, tuple[str, str | None]] = {
    "String": ("string", None),
    "char": ("string", None),
    "Character": ("string", None),
    "boolean": ("boolean", None),
    "Boolean": ("boolean", None),
    "int": ("integer", "int32"),
    "Integer": ("integer", "int32"),
    "short": ("integer", "int32"),
    "Short": ("integer", "int32"),
    "long": ("integer", "int64"),
    "Long": ("integer", "int64"),
    "float": ("number", "float"),
    "Float": ("number", "float"),
    "double": ("number", "double"),
    "Double": ("number", "double"),
    "BigDecimal": ("number", None),
    "BigInteger": ("integer", None),
    "UUID": ("string", "uuid"),
    "LocalDate": ("string", "date"),
    "LocalDateTime": ("string", "date-time"),
    "Instant": ("string", "date-time"),
    "ZonedDateTime": ("string", "date-time"),
    "OffsetDateTime": ("string", "date-time"),
}
"""Tabla explicita, ampliable. Si un tipo no esta aqui y no resuelve a un DTO del
proyecto, se trata como no reconocido (schema vacio + Diagnostic), nunca se adivina
un mapeo."""

_TRUE_COLLECTION_NAMES = frozenset({"List", "Set", "Collection", "Iterable"})
_OPTIONAL_NAME = "Optional"
_VOID_NAMES = frozenset({"void", "Void"})
_MAP_NAME = "Map"


# ---------------------------------------------------------------------------
# Tipo -> schema
# ---------------------------------------------------------------------------


def build_type_schema(
    type_text: str | None,
    dto,
    diagnostics: list[Diagnostic],
    evidence: Evidence | None,
    *,
    resolve_dto_ref: Callable[[object], dict] | None = None,
) -> dict:
    """Construye el fragmento de schema OpenAPI para un tipo Java (texto).

    ``dto`` es el ``DTO``/``nested_dto`` ya resuelto por el Analyzer para el tipo
    (unicamente para el nivel exacto que el Analyzer desenvolvio -- ver
    docs/07-Analisis.md). ``resolve_dto_ref`` registra el schema del DTO (si aun no
    existe) y devuelve su ``$ref``; si es ``None`` (uso para parametros, que nunca
    tienen DTO), cualquier ``dto`` se ignora seguro.
    """
    parsed = parse_type_text(type_text)
    return _schema_for(parsed, dto, diagnostics, evidence, resolve_dto_ref)


def _schema_for(
    parsed: ParsedType,
    dto,
    diagnostics: list[Diagnostic],
    evidence: Evidence | None,
    resolve_dto_ref: Callable[[object], dict] | None,
) -> dict:
    if parsed.array_dims > 0:
        inner = replace(parsed, array_dims=parsed.array_dims - 1)
        return {"type": "array", "items": _schema_for(inner, dto, diagnostics, evidence, resolve_dto_ref)}

    if parsed.name in _TRUE_COLLECTION_NAMES and len(parsed.args) == 1:
        return {
            "type": "array",
            "items": _schema_for(parsed.args[0], dto, diagnostics, evidence, resolve_dto_ref),
        }

    if parsed.name == _OPTIONAL_NAME and len(parsed.args) == 1:
        # Optional<T> se desenvuelve de forma transparente: no es una coleccion.
        return _schema_for(parsed.args[0], dto, diagnostics, evidence, resolve_dto_ref)

    if parsed.name == "?":
        return {}

    if parsed.name in _VOID_NAMES:
        return {}

    if parsed.name in PRIMITIVE_TYPES:
        openapi_type, fmt = PRIMITIVE_TYPES[parsed.name]
        schema: dict = {"type": openapi_type}
        if fmt is not None:
            schema["format"] = fmt
        return schema

    if parsed.name == _MAP_NAME and len(parsed.args) == 2:
        # Map<K,V>: sin evidencia suficiente para tipar additionalProperties (V0.2 no
        # desenvuelve genericos de mas de un argumento). Decision autorizada V0.3.
        return {"type": "object"}

    if dto is not None and resolve_dto_ref is not None and dto.name == parsed.name:
        return resolve_dto_ref(dto)

    diagnostics.append(
        Diagnostic(
            severity=DiagnosticSeverity.WARNING,
            code="OPENAPI_UNKNOWN_TYPE",
            message=(
                f"No se pudo determinar un schema OpenAPI para el tipo '{parsed.name}': "
                "no es un primitivo reconocido ni un DTO resuelto por el Analyzer. "
                "Se genera un schema vacio en vez de suponer su estructura."
            ),
            evidence=evidence,
        )
    )
    return {}


# ---------------------------------------------------------------------------
# Bean Validation -> keywords OpenAPI (seccion 3 "Bean Validation" de la directriz)
# ---------------------------------------------------------------------------


def apply_validations(schema: dict, validations: tuple[Validation, ...], *, is_collection: bool) -> dict:
    """Aplica, sobre ``schema`` (mutado in-place y devuelto), las keywords OpenAPI
    representables de las anotaciones de Bean Validation reconocidas. No interpreta
    ninguna anotacion fuera de la lista de la directriz."""
    for validation in validations:
        if validation.name == "NotBlank":
            schema.setdefault("minLength", 1)
        elif validation.name == "NotEmpty":
            if is_collection:
                schema.setdefault("minItems", 1)
            else:
                schema.setdefault("minLength", 1)
        elif validation.name == "Size":
            bounds = _parse_named_ints(validation.args)
            min_key, max_key = ("minItems", "maxItems") if is_collection else ("minLength", "maxLength")
            if "min" in bounds:
                schema[min_key] = bounds["min"]
            if "max" in bounds:
                schema[max_key] = bounds["max"]
        elif validation.name == "Min":
            number = _parse_number(validation.args)
            if number is not None:
                schema["minimum"] = number
        elif validation.name == "Max":
            number = _parse_number(validation.args)
            if number is not None:
                schema["maximum"] = number
        elif validation.name == "Positive":
            schema["minimum"] = 0
            schema["exclusiveMinimum"] = True
        elif validation.name == "PositiveOrZero":
            schema["minimum"] = 0
        elif validation.name == "Negative":
            schema["maximum"] = 0
            schema["exclusiveMaximum"] = True
        elif validation.name == "NegativeOrZero":
            schema["maximum"] = 0
        elif validation.name == "Email":
            schema["format"] = "email"
        elif validation.name == "Pattern":
            pattern = _parse_named_str(validation.args, "regexp")
            if pattern is not None:
                schema["pattern"] = pattern
        # NotNull no se representa aqui: implica "required" en el objeto contenedor
        # (DTO) o ya esta reflejado en Parameter.required (Spring), ver
        # generators/openapi_schemas.py.
    return schema


def is_required_by_validation(validations: tuple[Validation, ...]) -> bool:
    """True si alguna validacion reconocida implica presencia obligatoria del campo."""
    return any(v.name in ("NotNull", "NotBlank", "NotEmpty") for v in validations)


def _parse_named_ints(args_text: str) -> dict[str, int]:
    result: dict[str, int] = {}
    for part in args_text.split(","):
        part = part.strip()
        if "=" not in part:
            continue
        key, _, value = part.partition("=")
        key = key.strip()
        value = value.strip()
        if value.lstrip("-").isdigit():
            result[key] = int(value)
    return result


def _parse_number(args_text: str) -> int | float | None:
    text = args_text.strip()
    try:
        if "." in text:
            return float(text)
        return int(text)
    except ValueError:
        return None


def _parse_named_str(args_text: str, key: str) -> str | None:
    prefix = f"{key}="
    if args_text.startswith(prefix):
        return args_text[len(prefix) :]
    return None
