"""Reglas de validacion estructural de documentos OpenAPI 3.0.3 (V0.4).

Responsabilidad: dado un documento OpenAPI ya construido (``dict``), detectar
problemas estructurales y de calidad, usando exclusivamente la informacion presente
en el documento. Este modulo no analiza Java, no llama al Analyzer ni al Generator, y
no modifica el documento recibido (ver docs/05-OpenAPI.md y
prompts/V0.4-OPENAPI-VALIDATOR.md).

Evidence: cada ``Diagnostic`` reutiliza ``analyzer.Evidence`` sin modificar su
definicion. ``Evidence.file`` contiene un JSON Pointer (RFC 6901) que ubica el
fragmento del documento al que se refiere el hallazgo (p. ej.
``/paths/~1api~1customers/get/responses``); ``line``/``symbol`` quedan en ``None``
(sin equivalente en un documento OpenAPI); ``type`` clasifica la ubicacion
(``"document"``, ``"path"``, ``"operation"``, ``"parameter"``, ``"requestBody"``,
``"response"``, ``"schema"``, ``"ref"``, ``"components"``, ``"security"``).
"""

from __future__ import annotations

import re

from analyzer import Diagnostic, DiagnosticSeverity, Evidence

ERROR = DiagnosticSeverity.ERROR
WARNING = DiagnosticSeverity.WARNING
INFO = DiagnosticSeverity.INFO

_VALID_METHODS = ("delete", "get", "head", "options", "patch", "post", "put", "trace")
_RESERVED_PATH_ITEM_KEYS = frozenset({"parameters", "summary", "description", "servers", "$ref"})
_VALID_PARAM_LOCATIONS = frozenset({"path", "query", "header", "cookie"})
_VALID_SCHEMA_TYPES = frozenset({"string", "number", "integer", "boolean", "array", "object"})
_COMPONENT_SECTIONS = (
    "schemas",
    "parameters",
    "responses",
    "requestBodies",
    "headers",
    "securitySchemes",
)
_SECURITY_SCHEME_TYPES = frozenset({"apiKey", "http", "oauth2", "openIdConnect"})

_REF_PATTERN = re.compile(r"^#/components/(schemas|parameters|responses|requestBodies|headers|securitySchemes)/([^/]+)$")
_COMPONENT_NAME_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$")
_STATUS_CODE_PATTERN = re.compile(r"^[1-5][0-9]{2}$")
_VERSION_PATTERN = re.compile(r"^3\.0\.(\d+)$")
_PATH_PARAM_PATTERN = re.compile(r"\{([^{}]+)\}")

# Heuristicas especificas del Generator V0.3 (generators/openapi_generator.py):
# comparacion literal de texto contra sus valores fijos conocidos. NO es una
# inferencia general sobre OpenAPI -- si el Generator cambia estos textos, esta
# heuristica deja de detectar coincidencias (no se rompe, simplemente no aplica).
_GENERATOR_DEFAULT_RESPONSE_DESCRIPTION = (
    "Respuesta generada automaticamente (sin descripcion disponible en la evidencia)."
)
_GENERATOR_DEFAULT_INFO_TITLE = "Generated API"
_GENERATOR_DEFAULT_INFO_VERSION = "0.0.0"


# ---------------------------------------------------------------------------
# Utilidades: JSON Pointer y emision de diagnostics
# ---------------------------------------------------------------------------


def _ptr(base: str, *segments) -> str:
    """Extiende un JSON Pointer (RFC 6901) con segmentos adicionales, escapando
    ``~`` -> ``~0`` y ``/`` -> ``~1`` en cada segmento."""
    result = base
    for segment in segments:
        result += "/" + str(segment).replace("~", "~0").replace("/", "~1")
    return result


def _diag(diagnostics: list[Diagnostic], severity, code: str, message: str, pointer: str, type_: str) -> None:
    diagnostics.append(
        Diagnostic(severity=severity, code=code, message=message, evidence=Evidence(file=pointer, type=type_))
    )


def _is_number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


# ---------------------------------------------------------------------------
# 9.1 Documento raiz
# ---------------------------------------------------------------------------


def check_root(document: dict, diagnostics: list[Diagnostic]) -> None:
    version = document.get("openapi")
    if not isinstance(version, str) or not version:
        _diag(diagnostics, ERROR, "OPENAPI_MISSING_VERSION", "El documento no declara 'openapi' como string.", _ptr(""), "document")
    else:
        match = _VERSION_PATTERN.match(version)
        if not match:
            _diag(diagnostics, ERROR, "OPENAPI_UNSUPPORTED_VERSION", f"Version '{version}' no es OpenAPI 3.0.x; V0.4 solo soporta 3.0.x.", _ptr("", "openapi"), "document")
        elif version != "3.0.3":
            _diag(diagnostics, INFO, "OPENAPI_VERSION_NOT_REFERENCE", f"Version '{version}' es 3.0.x valida, pero distinta de la version de referencia 3.0.3.", _ptr("", "openapi"), "document")

    info = document.get("info")
    if not isinstance(info, dict):
        _diag(diagnostics, ERROR, "OPENAPI_MISSING_INFO", "El documento no declara 'info' como objeto.", _ptr(""), "document")
    else:
        title = info.get("title")
        if not isinstance(title, str) or not title:
            _diag(diagnostics, ERROR, "OPENAPI_MISSING_INFO_TITLE", "'info.title' ausente o no es un string.", _ptr("", "info"), "document")
        elif title == _GENERATOR_DEFAULT_INFO_TITLE:
            _diag(diagnostics, INFO, "OPENAPI_GENERATOR_PLACEHOLDER_INFO", "'info.title' coincide con el placeholder fijo del Generator V0.3 ('Generated API').", _ptr("", "info", "title"), "document")

        version_field = info.get("version")
        if not isinstance(version_field, str) or not version_field:
            _diag(diagnostics, ERROR, "OPENAPI_MISSING_INFO_VERSION", "'info.version' ausente o no es un string.", _ptr("", "info"), "document")
        elif version_field == _GENERATOR_DEFAULT_INFO_VERSION:
            _diag(diagnostics, INFO, "OPENAPI_GENERATOR_PLACEHOLDER_INFO", "'info.version' coincide con el placeholder fijo del Generator V0.3 ('0.0.0').", _ptr("", "info", "version"), "document")

    paths = document.get("paths")
    if not isinstance(paths, dict):
        _diag(diagnostics, ERROR, "OPENAPI_MISSING_PATHS", "El documento no declara 'paths' como objeto.", _ptr(""), "document")
    elif not paths:
        _diag(diagnostics, INFO, "OPENAPI_PATHS_EMPTY", "'paths' esta presente pero vacio.", _ptr("", "paths"), "document")


# ---------------------------------------------------------------------------
# $ref
# ---------------------------------------------------------------------------


def _check_ref(ref_value, pointer: str, diagnostics: list[Diagnostic], components_index: dict, used_refs: set) -> None:
    if not isinstance(ref_value, str) or not ref_value:
        _diag(diagnostics, ERROR, "OPENAPI_REF_INVALID", "'$ref' esta vacio o no es un string.", _ptr(pointer, "$ref"), "ref")
        return
    if not ref_value.startswith("#/"):
        _diag(diagnostics, INFO, "OPENAPI_REF_EXTERNAL_SKIPPED", f"'$ref' externo detectado ('{ref_value}'); V0.4 no resuelve referencias externas.", _ptr(pointer, "$ref"), "ref")
        return
    match = _REF_PATTERN.match(ref_value)
    if not match:
        _diag(diagnostics, ERROR, "OPENAPI_REF_INVALID", f"'{ref_value}' no tiene la forma '#/components/<seccion>/<nombre>'.", _ptr(pointer, "$ref"), "ref")
        return
    section, name = match.group(1), match.group(2)
    if name not in components_index.get(section, set()):
        _diag(diagnostics, ERROR, "OPENAPI_REF_NOT_FOUND", f"'{ref_value}' no existe en components.{section}.", _ptr(pointer, "$ref"), "ref")
        return
    used_refs.add((section, name))


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


def _check_schema(schema, pointer: str, diagnostics: list[Diagnostic], components_index: dict, used_refs: set) -> None:
    if not isinstance(schema, dict):
        _diag(diagnostics, ERROR, "OPENAPI_INVALID_SCHEMA_TYPE", "El schema no es un objeto.", pointer, "schema")
        return
    if "$ref" in schema:
        _check_ref(schema["$ref"], pointer, diagnostics, components_index, used_refs)
        return

    description = schema.get("description")
    if not isinstance(description, str) or not description:
        _diag(diagnostics, WARNING, "OPENAPI_SCHEMA_MISSING_DESCRIPTION", "El schema no tiene 'description'.", pointer, "schema")

    schema_type = schema.get("type")
    if schema_type is not None and schema_type not in _VALID_SCHEMA_TYPES:
        _diag(diagnostics, ERROR, "OPENAPI_INVALID_SCHEMA_TYPE", f"'type: {schema_type}' no es un tipo OpenAPI reconocido.", pointer, "schema")
        schema_type = None

    if schema_type == "array":
        if "items" not in schema:
            _diag(diagnostics, ERROR, "OPENAPI_ARRAY_ITEMS_MISSING", "'type: array' sin 'items'.", pointer, "schema")
        else:
            _check_schema(schema["items"], _ptr(pointer, "items"), diagnostics, components_index, used_refs)

    elif schema_type == "object":
        _check_object_schema(schema, pointer, diagnostics, components_index, used_refs)

    elif schema_type == "string":
        _check_string_constraints(schema, pointer, diagnostics)

    elif schema_type in ("number", "integer"):
        _check_number_constraints(schema, pointer, diagnostics)

    enum_values = schema.get("enum")
    if enum_values is not None:
        if not isinstance(enum_values, list):
            _diag(diagnostics, ERROR, "OPENAPI_ENUM_INVALID", "'enum' no es una lista.", pointer, "schema")
        else:
            _check_enum(enum_values, schema_type, pointer, diagnostics)


def _check_object_schema(schema: dict, pointer: str, diagnostics: list[Diagnostic], components_index: dict, used_refs: set) -> None:
    properties = schema.get("properties")
    required = schema.get("required")
    additional = schema.get("additionalProperties")

    if properties is not None and not isinstance(properties, dict):
        _diag(diagnostics, ERROR, "OPENAPI_OBJECT_SCHEMA_INVALID", "'properties' no es un objeto.", pointer, "schema")
        properties = None
    if required is not None and (not isinstance(required, list) or not all(isinstance(r, str) for r in required)):
        _diag(diagnostics, ERROR, "OPENAPI_OBJECT_SCHEMA_INVALID", "'required' no es una lista de strings.", pointer, "schema")
        required = None
    if additional is not None and not isinstance(additional, (bool, dict)):
        _diag(diagnostics, ERROR, "OPENAPI_OBJECT_SCHEMA_INVALID", "'additionalProperties' no es booleano ni objeto.", pointer, "schema")

    if not properties and not isinstance(additional, (bool, dict)):
        _diag(diagnostics, WARNING, "OPENAPI_OBJECT_SCHEMA_EMPTY", "'type: object' sin 'properties' ni 'additionalProperties'.", pointer, "schema")

    if properties:
        for prop_name in sorted(properties.keys(), key=str):
            _check_schema(properties[prop_name], _ptr(pointer, "properties", prop_name), diagnostics, components_index, used_refs)
        if required:
            for field_name in required:
                if field_name not in properties:
                    _diag(diagnostics, WARNING, "OPENAPI_REQUIRED_FIELD_UNDEFINED", f"'required' menciona '{field_name}' pero no esta en 'properties'.", _ptr(pointer, "required"), "schema")


def _check_string_constraints(schema: dict, pointer: str, diagnostics: list[Diagnostic]) -> None:
    min_len = schema.get("minLength")
    max_len = schema.get("maxLength")
    pattern = schema.get("pattern")
    fmt = schema.get("format")

    if min_len is not None and (not isinstance(min_len, int) or isinstance(min_len, bool) or min_len < 0):
        _diag(diagnostics, ERROR, "OPENAPI_STRING_CONSTRAINT_INVALID", "'minLength' debe ser un entero >= 0.", pointer, "schema")
        min_len = None
    if max_len is not None and (not isinstance(max_len, int) or isinstance(max_len, bool) or max_len < 0):
        _diag(diagnostics, ERROR, "OPENAPI_STRING_CONSTRAINT_INVALID", "'maxLength' debe ser un entero >= 0.", pointer, "schema")
        max_len = None
    if min_len is not None and max_len is not None and min_len > max_len:
        _diag(diagnostics, ERROR, "OPENAPI_STRING_CONSTRAINT_INVALID", f"'minLength' ({min_len}) es mayor que 'maxLength' ({max_len}).", pointer, "schema")
    if pattern is not None and not isinstance(pattern, str):
        _diag(diagnostics, ERROR, "OPENAPI_STRING_CONSTRAINT_INVALID", "'pattern' debe ser un string.", pointer, "schema")
    if fmt is not None and not isinstance(fmt, str):
        _diag(diagnostics, ERROR, "OPENAPI_STRING_CONSTRAINT_INVALID", "'format' debe ser un string.", pointer, "schema")


def _check_number_constraints(schema: dict, pointer: str, diagnostics: list[Diagnostic]) -> None:
    minimum = schema.get("minimum")
    maximum = schema.get("maximum")
    multiple_of = schema.get("multipleOf")
    exclusive_min = schema.get("exclusiveMinimum")
    exclusive_max = schema.get("exclusiveMaximum")

    if minimum is not None and not _is_number(minimum):
        _diag(diagnostics, ERROR, "OPENAPI_NUMBER_CONSTRAINT_INVALID", "'minimum' debe ser numerico.", pointer, "schema")
        minimum = None
    if maximum is not None and not _is_number(maximum):
        _diag(diagnostics, ERROR, "OPENAPI_NUMBER_CONSTRAINT_INVALID", "'maximum' debe ser numerico.", pointer, "schema")
        maximum = None
    if minimum is not None and maximum is not None and minimum > maximum:
        _diag(diagnostics, ERROR, "OPENAPI_NUMBER_CONSTRAINT_INVALID", f"'minimum' ({minimum}) es mayor que 'maximum' ({maximum}).", pointer, "schema")
    if multiple_of is not None and (not _is_number(multiple_of) or multiple_of <= 0):
        _diag(diagnostics, ERROR, "OPENAPI_NUMBER_CONSTRAINT_INVALID", "'multipleOf' debe ser numerico y mayor que 0.", pointer, "schema")
    if exclusive_min is not None and not isinstance(exclusive_min, bool):
        _diag(diagnostics, ERROR, "OPENAPI_NUMBER_CONSTRAINT_INVALID", "'exclusiveMinimum' debe ser booleano en OpenAPI 3.0.x.", pointer, "schema")
    if exclusive_max is not None and not isinstance(exclusive_max, bool):
        _diag(diagnostics, ERROR, "OPENAPI_NUMBER_CONSTRAINT_INVALID", "'exclusiveMaximum' debe ser booleano en OpenAPI 3.0.x.", pointer, "schema")


def _check_enum(values: list, schema_type, pointer: str, diagnostics: list[Diagnostic]) -> None:
    seen: list = []
    duplicates: list = []
    for value in values:
        if value in seen:
            if value not in duplicates:
                duplicates.append(value)
        else:
            seen.append(value)
    if duplicates:
        _diag(diagnostics, WARNING, "OPENAPI_ENUM_DUPLICATE_VALUES", f"'enum' contiene valores duplicados: {duplicates!r}.", _ptr(pointer, "enum"), "schema")

    type_checks = {"string": str, "boolean": bool, "integer": int, "number": (int, float)}
    expected = type_checks.get(schema_type)
    if expected is None:
        return
    for value in values:
        if schema_type in ("integer", "number") and isinstance(value, bool):
            mismatch = True
        else:
            mismatch = not isinstance(value, expected)
        if mismatch:
            _diag(diagnostics, WARNING, "OPENAPI_ENUM_TYPE_MISMATCH", f"El valor {value!r} de 'enum' no es compatible con type='{schema_type}'.", _ptr(pointer, "enum"), "schema")


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------


def _check_parameter_object(param, pointer: str, diagnostics: list[Diagnostic], components_index: dict, used_refs: set):
    if not isinstance(param, dict):
        _diag(diagnostics, ERROR, "OPENAPI_PARAMETER_MISSING_NAME", "El parametro no es un objeto.", pointer, "parameter")
        return None, None
    if "$ref" in param:
        _check_ref(param["$ref"], pointer, diagnostics, components_index, used_refs)
        return None, None

    name = param.get("name")
    location = param.get("in")
    if not isinstance(name, str) or not name:
        _diag(diagnostics, ERROR, "OPENAPI_PARAMETER_MISSING_NAME", "Falta 'name' o no es un string.", pointer, "parameter")
        name = None
    if not isinstance(location, str) or not location:
        _diag(diagnostics, ERROR, "OPENAPI_PARAMETER_MISSING_IN", "Falta 'in' o no es un string.", pointer, "parameter")
        location = None
    elif location not in _VALID_PARAM_LOCATIONS:
        _diag(diagnostics, ERROR, "OPENAPI_PARAMETER_INVALID_IN", f"'in: {location}' no es valido (path/query/header/cookie).", pointer, "parameter")
    elif location == "path" and param.get("required") is not True:
        _diag(diagnostics, ERROR, "OPENAPI_PATH_PARAMETER_NOT_REQUIRED", "Un parametro 'in: path' debe declarar required: true.", pointer, "parameter")

    has_schema = "schema" in param
    has_content = "content" in param
    if not has_schema and not has_content:
        _diag(diagnostics, ERROR, "OPENAPI_PARAMETER_MISSING_SCHEMA", "El parametro no declara 'schema' ni 'content'.", pointer, "parameter")
    elif has_schema and has_content:
        _diag(diagnostics, ERROR, "OPENAPI_PARAMETER_SCHEMA_CONTENT_CONFLICT", "El parametro declara 'schema' y 'content' a la vez.", pointer, "parameter")
    elif has_schema:
        _check_schema(param["schema"], _ptr(pointer, "schema"), diagnostics, components_index, used_refs)

    return name, location


def _check_parameter_list(params: list, list_pointer: str, diagnostics: list[Diagnostic], components_index: dict, used_refs: set) -> None:
    seen: set = set()
    for index, param in enumerate(params):
        item_pointer = _ptr(list_pointer, str(index))
        name, location = _check_parameter_object(param, item_pointer, diagnostics, components_index, used_refs)
        if name is not None and location is not None:
            key = (name, location)
            if key in seen:
                _diag(diagnostics, ERROR, "OPENAPI_PARAMETER_DUPLICATE", f"Parametro duplicado (name='{name}', in='{location}') en el mismo scope.", item_pointer, "parameter")
            else:
                seen.add(key)


def _check_path_parameters_defined(declared_names: list, path_level_params: list, operation_params: list, pointer: str, diagnostics: list[Diagnostic]) -> None:
    defined: set = set()
    for param_list in (path_level_params, operation_params):
        for param in param_list:
            if isinstance(param, dict) and param.get("in") == "path" and isinstance(param.get("name"), str):
                defined.add(param["name"])
    for name in declared_names:
        if name not in defined:
            _diag(diagnostics, ERROR, "OPENAPI_PATH_PARAMETER_MISSING", f"El path referencia '{{{name}}}' pero no hay un Parameter Object 'in: path' con name='{name}'.", pointer, "path")


def _extract_path_param_names(path_key: str) -> list:
    return _PATH_PARAM_PATTERN.findall(path_key)


# ---------------------------------------------------------------------------
# Request body
# ---------------------------------------------------------------------------


def _check_request_body_object(body: dict, pointer: str, diagnostics: list[Diagnostic], components_index: dict, used_refs: set) -> None:
    required = body.get("required")
    if required is not None and not isinstance(required, bool):
        _diag(diagnostics, ERROR, "OPENAPI_REQUEST_BODY_INVALID", "'required' debe ser booleano.", pointer, "requestBody")

    content = body.get("content")
    if content is None:
        _diag(diagnostics, ERROR, "OPENAPI_REQUEST_BODY_MISSING_CONTENT", "Falta 'content'.", pointer, "requestBody")
        return
    if not isinstance(content, dict) or not content:
        _diag(diagnostics, ERROR, "OPENAPI_REQUEST_BODY_INVALID", "'content' no es un objeto o esta vacio.", _ptr(pointer, "content"), "requestBody")
        return
    for media_type in sorted(content.keys(), key=str):
        media_obj = content[media_type]
        media_pointer = _ptr(pointer, "content", media_type)
        if not isinstance(media_obj, dict):
            _diag(diagnostics, ERROR, "OPENAPI_REQUEST_BODY_INVALID", f"El Media Type Object '{media_type}' no es un objeto.", media_pointer, "requestBody")
            continue
        if "schema" in media_obj:
            _check_schema(media_obj["schema"], _ptr(media_pointer, "schema"), diagnostics, components_index, used_refs)


def _check_request_body(request_body, pointer: str, diagnostics: list[Diagnostic], components_index: dict, used_refs: set) -> None:
    if request_body is None:
        return
    if isinstance(request_body, dict) and "$ref" in request_body:
        _check_ref(request_body["$ref"], pointer, diagnostics, components_index, used_refs)
        return
    if not isinstance(request_body, dict):
        _diag(diagnostics, ERROR, "OPENAPI_REQUEST_BODY_INVALID", "'requestBody' no es un objeto.", pointer, "requestBody")
        return
    _check_request_body_object(request_body, pointer, diagnostics, components_index, used_refs)


# ---------------------------------------------------------------------------
# Responses
# ---------------------------------------------------------------------------


def _check_response_object(response_obj: dict, pointer: str, diagnostics: list[Diagnostic], components_index: dict, used_refs: set) -> None:
    description = response_obj.get("description")
    if not isinstance(description, str) or not description:
        _diag(diagnostics, WARNING, "OPENAPI_RESPONSE_MISSING_DESCRIPTION", "La respuesta no tiene 'description'.", pointer, "response")
    elif description == _GENERATOR_DEFAULT_RESPONSE_DESCRIPTION:
        _diag(diagnostics, WARNING, "OPENAPI_GENERATOR_DEFAULT_RESPONSE_DESCRIPTION", "La 'description' coincide exactamente con el texto fijo del Generator V0.3 (heuristica especifica de este proyecto, no una inferencia general de OpenAPI).", _ptr(pointer, "description"), "response")

    headers = response_obj.get("headers")
    if headers is not None:
        if not isinstance(headers, dict):
            _diag(diagnostics, ERROR, "OPENAPI_RESPONSE_HEADERS_INVALID", "'headers' no es un objeto.", _ptr(pointer, "headers"), "response")
        else:
            for header_name in sorted(headers.keys(), key=str):
                header_obj = headers[header_name]
                if isinstance(header_obj, dict) and "schema" in header_obj:
                    _check_schema(header_obj["schema"], _ptr(pointer, "headers", header_name, "schema"), diagnostics, components_index, used_refs)

    links = response_obj.get("links")
    if links is not None and not isinstance(links, dict):
        _diag(diagnostics, ERROR, "OPENAPI_RESPONSE_LINKS_INVALID", "'links' no es un objeto.", _ptr(pointer, "links"), "response")

    content = response_obj.get("content")
    if content is not None:
        if not isinstance(content, dict):
            _diag(diagnostics, ERROR, "OPENAPI_RESPONSES_INVALID", "'content' no es un objeto.", _ptr(pointer, "content"), "response")
        else:
            for media_type in sorted(content.keys(), key=str):
                media_obj = content[media_type]
                media_pointer = _ptr(pointer, "content", media_type)
                if isinstance(media_obj, dict) and "schema" in media_obj:
                    _check_schema(media_obj["schema"], _ptr(media_pointer, "schema"), diagnostics, components_index, used_refs)


def _check_responses(responses, pointer: str, method: str, path_key: str, diagnostics: list[Diagnostic], components_index: dict, used_refs: set) -> None:
    if responses is None:
        _diag(diagnostics, ERROR, "OPENAPI_MISSING_RESPONSES", f"La operacion '{method.upper()} {path_key}' no declara 'responses'.", pointer, "operation")
        return
    if not isinstance(responses, dict) or not responses:
        _diag(diagnostics, ERROR, "OPENAPI_RESPONSES_INVALID", "'responses' no es un objeto o esta vacio.", _ptr(pointer, "responses"), "operation")
        return
    for status_key in sorted(responses.keys(), key=str):
        response_pointer = _ptr(pointer, "responses", status_key)
        if status_key != "default" and not _STATUS_CODE_PATTERN.match(str(status_key)):
            _diag(diagnostics, ERROR, "OPENAPI_INVALID_STATUS_CODE", f"'{status_key}' no es un codigo HTTP de 3 digitos ni 'default'.", response_pointer, "response")
            continue
        response_obj = responses[status_key]
        if isinstance(response_obj, dict) and "$ref" in response_obj:
            _check_ref(response_obj["$ref"], response_pointer, diagnostics, components_index, used_refs)
            continue
        if not isinstance(response_obj, dict):
            _diag(diagnostics, ERROR, "OPENAPI_RESPONSES_INVALID", f"La respuesta '{status_key}' no es un objeto.", response_pointer, "response")
            continue
        _check_response_object(response_obj, response_pointer, diagnostics, components_index, used_refs)


# ---------------------------------------------------------------------------
# Security
# ---------------------------------------------------------------------------


def _check_security_scheme(scheme, pointer: str, diagnostics: list[Diagnostic]) -> None:
    if not isinstance(scheme, dict):
        _diag(diagnostics, ERROR, "OPENAPI_SECURITY_INVALID", "El Security Scheme no es un objeto.", pointer, "security")
        return
    scheme_type = scheme.get("type")
    if scheme_type not in _SECURITY_SCHEME_TYPES:
        _diag(diagnostics, ERROR, "OPENAPI_SECURITY_INVALID", f"'type: {scheme_type}' no es un tipo de securityScheme reconocido.", pointer, "security")
        return
    if scheme_type == "apiKey":
        if not isinstance(scheme.get("name"), str) or not scheme.get("name"):
            _diag(diagnostics, ERROR, "OPENAPI_SECURITY_INVALID", "apiKey requiere 'name'.", pointer, "security")
        if scheme.get("in") not in ("query", "header", "cookie"):
            _diag(diagnostics, ERROR, "OPENAPI_SECURITY_INVALID", "apiKey requiere 'in' en {query,header,cookie}.", pointer, "security")
    elif scheme_type == "http":
        if not isinstance(scheme.get("scheme"), str) or not scheme.get("scheme"):
            _diag(diagnostics, ERROR, "OPENAPI_SECURITY_INVALID", "http requiere 'scheme'.", pointer, "security")
    elif scheme_type == "oauth2":
        flows = scheme.get("flows")
        if not isinstance(flows, dict) or not flows:
            _diag(diagnostics, ERROR, "OPENAPI_SECURITY_INVALID", "oauth2 requiere 'flows' como objeto no vacio.", pointer, "security")
    elif scheme_type == "openIdConnect":
        if not isinstance(scheme.get("openIdConnectUrl"), str) or not scheme.get("openIdConnectUrl"):
            _diag(diagnostics, ERROR, "OPENAPI_SECURITY_INVALID", "openIdConnect requiere 'openIdConnectUrl'.", pointer, "security")


def _check_operation_security(operation: dict, pointer: str, diagnostics: list[Diagnostic], components_index: dict) -> None:
    security = operation.get("security")
    x_evidence = operation.get("x-security-evidence")

    if x_evidence is not None:
        if not isinstance(x_evidence, list) or not all(isinstance(v, str) for v in x_evidence):
            _diag(diagnostics, WARNING, "OPENAPI_EXTENSION_MALFORMED", "'x-security-evidence' deberia ser una lista de strings.", _ptr(pointer, "x-security-evidence"), "security")
        else:
            _diag(diagnostics, WARNING, "OPENAPI_SECURITY_EXTENSION_ONLY", "La seguridad de esta operacion esta documentada solo como evidencia via 'x-security-evidence', no como un securityScheme real de OpenAPI.", _ptr(pointer, "x-security-evidence"), "security")

    if security is not None:
        if not isinstance(security, list):
            _diag(diagnostics, ERROR, "OPENAPI_SECURITY_INVALID", "'security' debe ser una lista.", _ptr(pointer, "security"), "security")
        else:
            scheme_names = components_index.get("securitySchemes", set())
            for index, requirement in enumerate(security):
                requirement_pointer = _ptr(pointer, "security", str(index))
                if not isinstance(requirement, dict):
                    _diag(diagnostics, ERROR, "OPENAPI_SECURITY_INVALID", "Cada elemento de 'security' debe ser un objeto.", requirement_pointer, "security")
                    continue
                for scheme_name in requirement:
                    if scheme_name not in scheme_names:
                        _diag(diagnostics, ERROR, "OPENAPI_SECURITY_SCHEME_NOT_FOUND", f"'security' referencia el scheme '{scheme_name}', no definido en components.securitySchemes.", _ptr(requirement_pointer, scheme_name), "security")

    if security is None and x_evidence is None:
        _diag(diagnostics, INFO, "OPENAPI_OPERATION_NO_SECURITY", "La operacion no declara 'security' ni evidencia de seguridad.", pointer, "security")


# ---------------------------------------------------------------------------
# Operation / Paths (orquestacion de nivel medio)
# ---------------------------------------------------------------------------


def _check_operation(operation: dict, pointer: str, path_key: str, method: str, path_level_params: list, declared_path_param_names: list, diagnostics: list[Diagnostic], components_index: dict, used_refs: set, operation_ids: dict) -> None:
    description = operation.get("description")
    if not isinstance(description, str) or not description:
        _diag(diagnostics, WARNING, "OPENAPI_OPERATION_MISSING_DESCRIPTION", f"La operacion '{method.upper()} {path_key}' no tiene 'description'.", pointer, "operation")

    operation_id = operation.get("operationId")
    if operation_id is not None:
        if not isinstance(operation_id, str):
            _diag(diagnostics, ERROR, "OPENAPI_OPERATION_ID_INVALID_TYPE", "'operationId' debe ser un string.", _ptr(pointer, "operationId"), "operation")
        else:
            operation_ids.setdefault(operation_id, []).append(pointer)

    raw_params = operation.get("parameters")
    operation_param_list = raw_params if isinstance(raw_params, list) else []
    _check_parameter_list(operation_param_list, _ptr(pointer, "parameters"), diagnostics, components_index, used_refs)

    _check_path_parameters_defined(declared_path_param_names, path_level_params, operation_param_list, pointer, diagnostics)

    _check_request_body(operation.get("requestBody"), _ptr(pointer, "requestBody"), diagnostics, components_index, used_refs)

    _check_responses(operation.get("responses"), pointer, method, path_key, diagnostics, components_index, used_refs)

    _check_operation_security(operation, pointer, diagnostics, components_index)


def check_paths(paths: dict, diagnostics: list[Diagnostic], components_index: dict, used_refs: set, operation_ids: dict) -> None:
    for path_key in sorted(paths.keys(), key=str):
        path_pointer = _ptr("", "paths", path_key)
        if not isinstance(path_key, str) or not path_key.startswith("/"):
            _diag(diagnostics, ERROR, "OPENAPI_INVALID_PATH", f"El path '{path_key}' esta vacio o no comienza con '/'.", path_pointer, "path")
            continue
        path_item = paths[path_key]
        if not isinstance(path_item, dict):
            _diag(diagnostics, ERROR, "OPENAPI_INVALID_PATH_ITEM", f"El valor de '{path_key}' no es un objeto.", path_pointer, "path")
            continue

        raw_path_params = path_item.get("parameters")
        path_level_params = raw_path_params if isinstance(raw_path_params, list) else []
        _check_parameter_list(path_level_params, _ptr(path_pointer, "parameters"), diagnostics, components_index, used_refs)

        declared_names = _extract_path_param_names(path_key)

        for method in sorted(path_item.keys(), key=str):
            if method in _RESERVED_PATH_ITEM_KEYS or (isinstance(method, str) and method.startswith("x-")):
                continue
            operation_pointer = _ptr(path_pointer, method)
            if method not in _VALID_METHODS:
                _diag(diagnostics, ERROR, "OPENAPI_INVALID_METHOD", f"'{method}' no es un metodo HTTP valido.", operation_pointer, "path")
                continue
            operation = path_item[method]
            if not isinstance(operation, dict):
                _diag(diagnostics, ERROR, "OPENAPI_INVALID_PATH_ITEM", f"La operacion '{method}' de '{path_key}' no es un objeto.", operation_pointer, "operation")
                continue
            _check_operation(operation, operation_pointer, path_key, method, path_level_params, declared_names, diagnostics, components_index, used_refs, operation_ids)


# ---------------------------------------------------------------------------
# Components
# ---------------------------------------------------------------------------


def build_components_index(document: dict) -> dict:
    components = document.get("components")
    index = {section: set() for section in _COMPONENT_SECTIONS}
    if isinstance(components, dict):
        for section in _COMPONENT_SECTIONS:
            section_value = components.get(section)
            if isinstance(section_value, dict):
                index[section] = set(section_value.keys())
    return index


def check_components(document: dict, diagnostics: list[Diagnostic], components_index: dict, used_refs: set) -> None:
    components = document.get("components")
    if components is None:
        return
    if not isinstance(components, dict):
        _diag(diagnostics, ERROR, "OPENAPI_COMPONENTS_INVALID", "'components' no es un objeto.", _ptr("", "components"), "components")
        return

    for section in _COMPONENT_SECTIONS:
        section_value = components.get(section)
        if section_value is None:
            continue
        section_pointer = _ptr("", "components", section)
        if not isinstance(section_value, dict):
            _diag(diagnostics, ERROR, "OPENAPI_COMPONENTS_INVALID", f"'components.{section}' no es un objeto.", section_pointer, "components")
            continue
        for name in sorted(section_value.keys(), key=str):
            item_pointer = _ptr(section_pointer, name)
            if not isinstance(name, str) or not _COMPONENT_NAME_PATTERN.match(name):
                _diag(diagnostics, WARNING, "OPENAPI_COMPONENT_NAME_INVALID", f"El nombre de componente '{name}' contiene caracteres no permitidos.", item_pointer, "components")
            item = section_value[name]
            if section == "schemas":
                _check_schema(item, item_pointer, diagnostics, components_index, used_refs)
            elif section == "parameters":
                _check_parameter_object(item, item_pointer, diagnostics, components_index, used_refs)
            elif section == "responses":
                _check_component_ref_or(item, item_pointer, diagnostics, components_index, used_refs, _check_response_object, "OPENAPI_RESPONSES_INVALID", "response")
            elif section == "requestBodies":
                _check_component_ref_or(item, item_pointer, diagnostics, components_index, used_refs, _check_request_body_object, "OPENAPI_REQUEST_BODY_INVALID", "requestBody")
            elif section == "securitySchemes":
                _check_security_scheme(item, item_pointer, diagnostics)


def _check_component_ref_or(item, pointer, diagnostics, components_index, used_refs, object_checker, invalid_code, type_) -> None:
    if isinstance(item, dict) and "$ref" in item:
        _check_ref(item["$ref"], pointer, diagnostics, components_index, used_refs)
    elif isinstance(item, dict):
        object_checker(item, pointer, diagnostics, components_index, used_refs)
    else:
        _diag(diagnostics, ERROR, invalid_code, f"El componente en '{pointer}' no es un objeto.", pointer, type_)


# ---------------------------------------------------------------------------
# Chequeos finales (posteriores al recorrido de paths/components)
# ---------------------------------------------------------------------------


def check_duplicate_operation_ids(operation_ids: dict, diagnostics: list[Diagnostic]) -> None:
    for operation_id in sorted(operation_ids.keys(), key=str):
        pointers = operation_ids[operation_id]
        if len(pointers) > 1:
            for pointer in pointers[1:]:
                _diag(diagnostics, ERROR, "OPENAPI_DUPLICATE_OPERATION_ID", f"'operationId' duplicado: '{operation_id}' ya fue usado en otra operacion.", _ptr(pointer, "operationId"), "operation")


def check_unreferenced_schemas(components_index: dict, used_refs: set, diagnostics: list[Diagnostic]) -> None:
    used_schema_names = {name for section, name in used_refs if section == "schemas"}
    for name in sorted(components_index.get("schemas", set()), key=str):
        if name not in used_schema_names:
            _diag(diagnostics, INFO, "OPENAPI_SCHEMA_UNREFERENCED", f"El schema '{name}' no es referenciado por ningun '$ref' del documento.", _ptr("", "components", "schemas", name), "schema")
